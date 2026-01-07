"""
Gestor de Estado de Combate para D&D 5e

Mantiene el estado canónico del combate y coordina con el pipeline.

RESPONSABILIDADES:
✓ Mantener estado (HP, condiciones, posiciones)
✓ Gestionar iniciativa y turnos
✓ Aplicar cambios que devuelve el pipeline
✓ Producir ContextoEscena para el pipeline
✓ Determinar fin de combate

NO HACE:
✗ Interpretar reglas (eso es combate_utils)
✗ Normalizar texto (eso es normalizador)
✗ Narrar (eso es el LLM)

PATRÓN: Inyección de dependencias
"""

import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import copy

from .normalizador import ContextoEscena
from .pipeline_turno import PipelineTurno, ResultadoPipeline, TipoResultado, TipoResultado
from .compendio import CompendioMotor
from .dados import tirar


class TipoCombatiente(Enum):
    """Tipo de combatiente."""
    PC = "pc"           # Personaje jugador
    NPC_ALIADO = "aliado"
    NPC_ENEMIGO = "enemigo"
    NEUTRAL = "neutral"


class EstadoCombate(Enum):
    """Estado del combate."""
    NO_INICIADO = "no_iniciado"
    EN_CURSO = "en_curso"
    VICTORIA = "victoria"      # PCs ganan
    DERROTA = "derrota"        # PCs pierden
    EMPATE = "empate"          # Todos muertos o huyen
    TERMINADO = "terminado"    # Fin genérico


@dataclass
class Combatiente:
    """
    Estado de un participante en el combate.
    
    Separamos datos "fuente" (inmutables) de "estado_actual" (mutable).
    """
    # Identificación
    id: str                          # ID único en este combate
    nombre: str
    tipo: TipoCombatiente
    compendio_ref: Optional[str] = None  # Referencia al compendio (para monstruos)
    
    # Atributos base (de la ficha)
    hp_maximo: int = 10
    clase_armadura: int = 10
    velocidad: int = 30
    
    # Atributos (para bonificadores)
    fuerza: int = 10
    destreza: int = 10
    constitucion: int = 10
    inteligencia: int = 10
    sabiduria: int = 10
    carisma: int = 10
    
    # Bonificador de competencia
    bonificador_competencia: int = 2
    
    # Equipo
    arma_principal: Optional[Dict[str, Any]] = None
    arma_secundaria: Optional[Dict[str, Any]] = None
    armadura: Optional[Dict[str, Any]] = None
    
    # Conjuros (para lanzadores)
    conjuros_conocidos: List[str] = field(default_factory=list)
    ranuras_conjuro: Dict[int, int] = field(default_factory=dict)  # nivel: disponibles
    
    # Acciones de monstruo (cargadas del compendio)
    # Cada acción: {nombre, bonificador_ataque, daño, tipo_daño, alcance}
    acciones: List[Dict[str, Any]] = field(default_factory=list)
    
    # === ESTADO MUTABLE (cambia durante el combate) ===
    hp_actual: int = 0
    hp_temporal: int = 0
    condiciones: List[str] = field(default_factory=list)
    concentracion_en: Optional[str] = None  # ID del conjuro
    
    # Estado del turno actual
    iniciativa: int = 0
    accion_usada: bool = False
    accion_bonus_usada: bool = False
    reaccion_usada: bool = False
    movimiento_usado: int = 0
    
    # Flags
    inconsciente: bool = False
    muerto: bool = False
    
    def __post_init__(self):
        if self.hp_actual == 0:
            self.hp_actual = self.hp_maximo
    
    @property
    def esta_vivo(self) -> bool:
        return not self.muerto
    
    @property
    def puede_actuar(self) -> bool:
        if self.muerto or self.inconsciente:
            return False
        condiciones_bloqueantes = ["paralizado", "petrificado", "aturdido", "incapacitado"]
        return not any(c in self.condiciones for c in condiciones_bloqueantes)
    
    @property
    def movimiento_restante(self) -> int:
        return max(0, self.velocidad - self.movimiento_usado)
    
    def reiniciar_turno(self):
        """Reinicia recursos del turno."""
        self.accion_usada = False
        self.accion_bonus_usada = False
        self.movimiento_usado = 0
        # Reacción se recupera al inicio de TU turno
        self.reaccion_usada = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el combatiente."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo.value,
            "compendio_ref": self.compendio_ref,
            "hp_actual": self.hp_actual,
            "hp_maximo": self.hp_maximo,
            "hp_temporal": self.hp_temporal,
            "clase_armadura": self.clase_armadura,
            "condiciones": self.condiciones.copy(),
            "iniciativa": self.iniciativa,
            "muerto": self.muerto,
            "inconsciente": self.inconsciente,
            "puede_actuar": self.puede_actuar,
        }


@dataclass 
class EstadoTurno:
    """Estado del turno actual."""
    ronda: int = 1
    indice_turno: int = 0  # Índice en la lista de iniciativa
    combatiente_actual_id: Optional[str] = None


class GestorCombate:
    """
    Gestiona el estado de un combate.
    
    Args:
        compendio: CompendioMotor inyectado
        pipeline: PipelineTurno inyectado (opcional, se crea si no)
    """
    
    def __init__(self, 
                 compendio: CompendioMotor,
                 pipeline: PipelineTurno = None):
        self._compendio = compendio
        self._pipeline = pipeline or PipelineTurno(compendio)
        
        # Estado
        self._combatientes: Dict[str, Combatiente] = {}
        self._orden_iniciativa: List[str] = []  # IDs ordenados por iniciativa
        self._turno = EstadoTurno()
        self._estado = EstadoCombate.NO_INICIADO
        
        # Historial
        self._historial_eventos: List[Dict[str, Any]] = []
        
        # Guard contra doble aplicación de cambios
        # Set de (ronda, actor_id, hash_cambios) ya aplicados
        self._cambios_aplicados: set = set()
        
        # Guard contra doble aplicación de cambios
        # Set de (ronda, actor_id, hash_cambios) ya aplicados
        self._cambios_aplicados: set = set()
    
    # =========================================================================
    # INICIALIZACIÓN
    # =========================================================================
    
    def agregar_combatiente(self, combatiente: Combatiente):
        """Añade un combatiente al combate."""
        if self._estado != EstadoCombate.NO_INICIADO:
            raise ValueError("No se pueden añadir combatientes después de iniciar el combate")
        self._combatientes[combatiente.id] = combatiente
    
    def agregar_desde_compendio(self, 
                                 monstruo_id: str, 
                                 instancia_id: str = None,
                                 nombre: str = None,
                                 tipo: TipoCombatiente = TipoCombatiente.NPC_ENEMIGO) -> Combatiente:
        """
        Crea un combatiente desde el compendio.
        
        Args:
            monstruo_id: ID en el compendio
            instancia_id: ID único para este combate (auto-generado si None)
            nombre: Nombre personalizado (usa el del compendio si None)
            tipo: Tipo de combatiente
        
        Returns:
            El Combatiente creado
        """
        datos = self._compendio.obtener_monstruo(monstruo_id)
        if not datos:
            raise ValueError(f"Monstruo '{monstruo_id}' no encontrado en compendio")
        
        if not instancia_id:
            # Generar ID único
            base = monstruo_id
            contador = 1
            while f"{base}_{contador}" in self._combatientes:
                contador += 1
            instancia_id = f"{base}_{contador}"
        
        # Cargar acciones del monstruo
        acciones_raw = datos.get("acciones", [])
        acciones = []
        for acc in acciones_raw:
            if "bonificador_ataque" in acc:  # Es un ataque
                acciones.append({
                    "nombre": acc.get("nombre", "Ataque"),
                    "bonificador_ataque": acc.get("bonificador_ataque", 0),
                    "daño": acc.get("daño", "1d4"),
                    "tipo_daño": acc.get("tipo_daño", "contundente"),
                    "alcance": acc.get("alcance", "cuerpo a cuerpo"),
                })
        
        combatiente = Combatiente(
            id=instancia_id,
            nombre=nombre or datos.get("nombre", monstruo_id),
            tipo=tipo,
            compendio_ref=monstruo_id,
            hp_maximo=datos.get("puntos_golpe", 10),
            hp_actual=datos.get("puntos_golpe", 10),
            clase_armadura=datos.get("clase_armadura", 10),
            velocidad=datos.get("velocidad", 30),
            fuerza=datos.get("atributos", {}).get("fuerza", 10),
            destreza=datos.get("atributos", {}).get("destreza", 10),
            constitucion=datos.get("atributos", {}).get("constitucion", 10),
            inteligencia=datos.get("atributos", {}).get("inteligencia", 10),
            sabiduria=datos.get("atributos", {}).get("sabiduria", 10),
            carisma=datos.get("atributos", {}).get("carisma", 10),
            acciones=acciones,
        )
        
        self.agregar_combatiente(combatiente)
        return combatiente
    
    def iniciar_combate(self, tirar_iniciativa: bool = True):
        """
        Inicia el combate.
        
        Args:
            tirar_iniciativa: Si True, tira iniciativa automáticamente.
                             Si False, usa los valores ya asignados.
        """
        if len(self._combatientes) < 2:
            raise ValueError("Se necesitan al menos 2 combatientes")
        
        if tirar_iniciativa:
            self._tirar_iniciativas()
        
        self._ordenar_por_iniciativa()
        
        self._turno = EstadoTurno(
            ronda=1,
            indice_turno=0,
            combatiente_actual_id=self._orden_iniciativa[0]
        )
        
        # Reiniciar turno del primer combatiente
        self._combatientes[self._turno.combatiente_actual_id].reiniciar_turno()
        
        self._estado = EstadoCombate.EN_CURSO
    
    def _tirar_iniciativas(self):
        """Tira iniciativa para todos los combatientes."""
        from .reglas_basicas import calcular_modificador
        
        for combatiente in self._combatientes.values():
            mod_des = calcular_modificador(combatiente.destreza)
            resultado = tirar(f"1d20+{mod_des}")
            combatiente.iniciativa = resultado.total
    
    def _ordenar_por_iniciativa(self):
        """Ordena combatientes por iniciativa (mayor primero)."""
        self._orden_iniciativa = sorted(
            self._combatientes.keys(),
            key=lambda id: (
                self._combatientes[id].iniciativa,
                self._combatientes[id].destreza  # Desempate por Destreza
            ),
            reverse=True
        )
    
    # =========================================================================
    # GESTIÓN DE TURNOS
    # =========================================================================
    
    def obtener_turno_actual(self) -> Optional[Combatiente]:
        """Retorna el combatiente cuyo turno es."""
        if self._estado != EstadoCombate.EN_CURSO:
            return None
        return self._combatientes.get(self._turno.combatiente_actual_id)
    
    def siguiente_turno(self) -> Optional[Combatiente]:
        """
        Avanza al siguiente turno.
        
        Returns:
            El nuevo combatiente activo, o None si el combate terminó.
        """
        if self._estado != EstadoCombate.EN_CURSO:
            return None
        
        # Verificar fin de combate
        if self._verificar_fin_combate():
            return None
        
        # Avanzar índice
        self._turno.indice_turno += 1
        
        # Nueva ronda si llegamos al final
        if self._turno.indice_turno >= len(self._orden_iniciativa):
            self._turno.indice_turno = 0
            self._turno.ronda += 1
        
        # Buscar siguiente combatiente que pueda actuar
        intentos = 0
        while intentos < len(self._orden_iniciativa):
            id_actual = self._orden_iniciativa[self._turno.indice_turno]
            combatiente = self._combatientes[id_actual]
            
            if combatiente.esta_vivo:
                self._turno.combatiente_actual_id = id_actual
                combatiente.reiniciar_turno()
                return combatiente
            
            # Siguiente
            self._turno.indice_turno += 1
            if self._turno.indice_turno >= len(self._orden_iniciativa):
                self._turno.indice_turno = 0
                self._turno.ronda += 1
            intentos += 1
        
        # Todos muertos
        self._estado = EstadoCombate.EMPATE
        return None
    
    # =========================================================================
    # PROCESAMIENTO DE ACCIONES
    # =========================================================================
    
    def procesar_accion(self, texto: str) -> ResultadoPipeline:
        """
        Procesa una acción del combatiente actual.
        
        Args:
            texto: Texto en lenguaje natural
            
        Returns:
            ResultadoPipeline con el resultado
        """
        if self._estado != EstadoCombate.EN_CURSO:
            return ResultadoPipeline(
                tipo=TipoResultado.ACCION_RECHAZADA,
                motivo="El combate no está en curso"
            )
        
        combatiente = self.obtener_turno_actual()
        if not combatiente:
            return ResultadoPipeline(
                tipo=TipoResultado.ACCION_RECHAZADA,
                motivo="No hay combatiente activo"
            )
        
        # Generar contexto de escena
        contexto = self.obtener_contexto_escena()
        
        # Procesar con el pipeline
        resultado = self._pipeline.procesar(texto, contexto)
        
        # Aplicar cambios si la acción fue exitosa
        if resultado.tipo == TipoResultado.ACCION_APLICADA:
            self._aplicar_cambios(resultado.cambios_estado)
            
            # Guardar eventos en historial
            for evento in resultado.eventos:
                self._historial_eventos.append({
                    "ronda": self._turno.ronda,
                    "actor_id": combatiente.id,
                    "evento": evento.to_dict()
                })
            
            # Verificar fin de combate después de la acción
            self._verificar_fin_combate()
        
        return resultado
    
    def _aplicar_cambios(self, cambios: Dict[str, Any]):
        """
        Aplica los cambios de estado que devuelve el pipeline.
        
        Este es el único lugar donde el estado del combate se modifica
        como resultado de acciones.
        
        GUARD: Evita doble aplicación por reintentos del pipeline/LLM.
        """
        combatiente = self.obtener_turno_actual()
        if not combatiente:
            return
        
        # Guard contra doble aplicación (JSON canónico para estabilidad)
        payload = json.dumps(cambios, sort_keys=True, separators=(",", ":"))
        cambios_hash = hashlib.sha256(payload.encode()).hexdigest()[:12]
        clave_cambio = (self._turno.ronda, combatiente.id, getattr(self._turno, "indice_turno", 0), cambios_hash)
        
        if clave_cambio in self._cambios_aplicados:
            # Ya se aplicó este cambio exacto en este turno
            return
        
        self._cambios_aplicados.add(clave_cambio)
        
        # Acción usada
        if cambios.get("accion_usada"):
            combatiente.accion_usada = True
        
        # Movimiento usado
        if "movimiento_usado" in cambios:
            combatiente.movimiento_usado += cambios["movimiento_usado"]
        
        # Movimiento bonus (Dash)
        if "movimiento_bonus" in cambios:
            # Dash da movimiento extra igual a tu velocidad
            # Lo implementamos como que reduce el movimiento usado
            combatiente.movimiento_usado -= cambios["movimiento_bonus"]
        
        # Condición temporal (Dodge)
        if "condicion_temporal" in cambios:
            condicion = cambios["condicion_temporal"]
            if condicion not in combatiente.condiciones:
                combatiente.condiciones.append(condicion)
        
        # Daño infligido
        if "daño_infligido" in cambios:
            info_daño = cambios["daño_infligido"]
            objetivo_id = info_daño.get("objetivo_id")
            cantidad = info_daño.get("cantidad", 0)
            
            if objetivo_id and objetivo_id in self._combatientes:
                self._aplicar_daño(objetivo_id, cantidad)
        
        # Ranura de conjuro gastada
        if "ranura_gastada" in cambios:
            nivel = cambios["ranura_gastada"].get("nivel", 1)
            if nivel in combatiente.ranuras_conjuro:
                combatiente.ranuras_conjuro[nivel] = max(0, combatiente.ranuras_conjuro[nivel] - 1)
    
    def _aplicar_daño(self, objetivo_id: str, cantidad: int):
        """Aplica daño a un combatiente."""
        objetivo = self._combatientes.get(objetivo_id)
        if not objetivo or objetivo.muerto:
            return
        
        # Primero absorbe HP temporal
        if objetivo.hp_temporal > 0:
            absorbido = min(objetivo.hp_temporal, cantidad)
            objetivo.hp_temporal -= absorbido
            cantidad -= absorbido
        
        # Luego HP normal
        objetivo.hp_actual = max(0, objetivo.hp_actual - cantidad)
        
        # Verificar muerte/inconsciencia
        if objetivo.hp_actual <= 0:
            if objetivo.tipo == TipoCombatiente.PC:
                # PCs caen inconscientes (simplificado, sin tiradas de muerte)
                objetivo.inconsciente = True
            else:
                # NPCs mueren directamente
                objetivo.muerto = True
    
    # =========================================================================
    # CONTEXTO DE ESCENA
    # =========================================================================
    
    def obtener_contexto_escena(self) -> ContextoEscena:
        """
        Genera el ContextoEscena que necesita el pipeline.
        """
        combatiente = self.obtener_turno_actual()
        if not combatiente:
            raise ValueError("No hay combatiente activo")
        
        # Separar enemigos y aliados
        enemigos = []
        aliados = []
        
        for c in self._combatientes.values():
            if c.id == combatiente.id:
                continue
            if c.muerto or c.inconsciente:
                continue
                
            info = {
                "instancia_id": c.id,
                "nombre": c.nombre,
                "compendio_ref": c.compendio_ref,
                "puntos_golpe_actual": c.hp_actual,
                "clase_armadura": c.clase_armadura,
                "estado_actual": {"muerto": c.muerto}
            }
            
            # Determinar si es enemigo o aliado
            if combatiente.tipo == TipoCombatiente.PC:
                if c.tipo == TipoCombatiente.NPC_ENEMIGO:
                    enemigos.append(info)
                else:
                    aliados.append(info)
            else:
                if c.tipo == TipoCombatiente.PC or c.tipo == TipoCombatiente.NPC_ALIADO:
                    enemigos.append(info)  # Desde perspectiva del NPC
                else:
                    aliados.append(info)
        
        # Armas disponibles
        armas = []
        if combatiente.arma_principal:
            armas.append(combatiente.arma_principal)
        if combatiente.arma_secundaria:
            armas.append(combatiente.arma_secundaria)
        
        # Conjuros
        conjuros = [{"id": c, "nombre": c} for c in combatiente.conjuros_conocidos]
        
        return ContextoEscena(
            actor_id=combatiente.id,
            actor_nombre=combatiente.nombre,
            arma_principal=combatiente.arma_principal,
            arma_secundaria=combatiente.arma_secundaria,
            armas_disponibles=armas,
            conjuros_conocidos=conjuros,
            ranuras_disponibles=combatiente.ranuras_conjuro.copy(),
            enemigos_vivos=enemigos,
            aliados=aliados,
            acciones_monstruo=combatiente.acciones.copy() if combatiente.acciones else [],
            movimiento_restante=combatiente.movimiento_restante,
            accion_disponible=not combatiente.accion_usada,
            accion_bonus_disponible=not combatiente.accion_bonus_usada,
        )
    
    # =========================================================================
    # FIN DE COMBATE
    # =========================================================================
    
    def _verificar_fin_combate(self) -> bool:
        """
        Verifica si el combate ha terminado.
        
        Returns:
            True si el combate terminó
        """
        if self._estado != EstadoCombate.EN_CURSO:
            return True
        
        pcs_vivos = 0
        enemigos_vivos = 0
        
        for c in self._combatientes.values():
            if c.muerto or c.inconsciente:
                continue
            if c.tipo == TipoCombatiente.PC:
                pcs_vivos += 1
            elif c.tipo == TipoCombatiente.NPC_ENEMIGO:
                enemigos_vivos += 1
        
        if enemigos_vivos == 0 and pcs_vivos > 0:
            self._estado = EstadoCombate.VICTORIA
            return True
        
        if pcs_vivos == 0 and enemigos_vivos > 0:
            self._estado = EstadoCombate.DERROTA
            return True
        
        if pcs_vivos == 0 and enemigos_vivos == 0:
            self._estado = EstadoCombate.EMPATE
            return True
        
        return False
    
    def combate_terminado(self) -> bool:
        """Retorna True si el combate ha terminado."""
        return self._estado not in [EstadoCombate.NO_INICIADO, EstadoCombate.EN_CURSO]
    
    # =========================================================================
    # CONSULTAS
    # =========================================================================
    
    @property
    def estado(self) -> EstadoCombate:
        """Estado actual del combate."""
        return self._estado
    
    @property
    def ronda_actual(self) -> int:
        """Ronda actual."""
        return self._turno.ronda
    
    def obtener_combatiente(self, id: str) -> Optional[Combatiente]:
        """Obtiene un combatiente por ID."""
        return self._combatientes.get(id)
    
    def listar_combatientes(self) -> List[Combatiente]:
        """Lista todos los combatientes en orden de iniciativa."""
        return [self._combatientes[id] for id in self._orden_iniciativa]
    
    def obtener_resumen(self) -> Dict[str, Any]:
        """Retorna un resumen del estado del combate."""
        return {
            "estado": self._estado.value,
            "ronda": self._turno.ronda,
            "turno_de": self._turno.combatiente_actual_id,
            "combatientes": [c.to_dict() for c in self.listar_combatientes()],
            "orden_iniciativa": self._orden_iniciativa.copy(),
        }
    
    def obtener_historial(self) -> List[Dict[str, Any]]:
        """Retorna el historial de eventos."""
        return self._historial_eventos.copy()
