"""
Pipeline de Turno para D&D 5e

Orquesta el flujo completo de una acción del jugador:
1. Normaliza el texto de entrada
2. Si necesita clarificación → devuelve pregunta
3. Valida la acción
4. Si inválida → devuelve motivo + sugerencias
5. Si válida → ejecuta y genera eventos

RESPONSABILIDAD:
- Este módulo es el "pegamento" del sistema
- El LLM NO decide reglas, solo se conecta en 2 puntos:
  - Fallback de normalización (ambigüedad)
  - Generación de narrativa (post-eventos)

PATRÓN: Inyección de dependencias
- Recibe todos sus colaboradores por constructor
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .utils import normalizar_nombre
from .normalizador import NormalizadorAcciones, TipoAccionNorm, AccionNormalizada, ContextoEscena
from .validador import ValidadorAcciones, TipoAccion, ResultadoValidacion
from .compendio import CompendioMotor
from .combate_utils import resolver_ataque, tirar_daño, tirar_iniciativa, tirar_habilidad


class TipoResultado(Enum):
    """Tipos de resultado del pipeline."""
    NECESITA_CLARIFICAR = "necesita_clarificar"
    ACCION_RECHAZADA = "accion_rechazada"
    ACCION_APLICADA = "accion_aplicada"
    ERROR_INTERNO = "error_interno"


@dataclass
class OpcionClarificacion:
    """Una opción para clarificar ambigüedad."""
    id: str
    texto: str
    datos: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Evento:
    """
    Un evento generado por una acción ejecutada.
    
    Los eventos son la "moneda" del sistema: representan
    qué pasó de forma estructurada para que el LLM narre.
    """
    tipo: str  # ataque_resuelto, daño_aplicado, movimiento_realizado, etc.
    actor_id: str
    datos: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tipo": self.tipo,
            "actor_id": self.actor_id,
            "datos": self.datos,
            "timestamp": self.timestamp
        }


@dataclass
class ResultadoPipeline:
    """
    Resultado del pipeline de turno.
    
    Siempre tiene un tipo y datos específicos según ese tipo.
    """
    tipo: TipoResultado
    
    # Para NECESITA_CLARIFICAR
    pregunta: str = ""
    opciones: List[OpcionClarificacion] = field(default_factory=list)
    accion_parcial: Optional[AccionNormalizada] = None
    
    # Para ACCION_RECHAZADA
    motivo: str = ""
    sugerencia: str = ""
    
    # Para ACCION_APLICADA
    eventos: List[Evento] = field(default_factory=list)
    cambios_estado: Dict[str, Any] = field(default_factory=dict)
    mensaje_dm: str = ""  # Placeholder para narrativa del LLM
    
    # Para ERROR_INTERNO
    error: str = ""
    
    # Siempre presente
    accion_normalizada: Optional[AccionNormalizada] = None
    validacion: Optional[ResultadoValidacion] = None
    
    def to_dict(self) -> Dict[str, Any]:
        resultado = {
            "tipo": self.tipo.value,
        }
        
        if self.tipo == TipoResultado.NECESITA_CLARIFICAR:
            resultado["pregunta"] = self.pregunta
            resultado["opciones"] = [
                {"id": o.id, "texto": o.texto, "datos": o.datos}
                for o in self.opciones
            ]
        
        elif self.tipo == TipoResultado.ACCION_RECHAZADA:
            resultado["motivo"] = self.motivo
            resultado["sugerencia"] = self.sugerencia
        
        elif self.tipo == TipoResultado.ACCION_APLICADA:
            resultado["eventos"] = [e.to_dict() for e in self.eventos]
            resultado["cambios_estado"] = self.cambios_estado
            resultado["mensaje_dm"] = self.mensaje_dm
        
        elif self.tipo == TipoResultado.ERROR_INTERNO:
            resultado["error"] = self.error
        
        if self.accion_normalizada:
            resultado["accion"] = self.accion_normalizada.to_dict()
        
        return resultado



def _elegir_accion_monstruo_inteligente(acciones: List[Dict]) -> Dict:
    """
    Elige la mejor acción de monstruo por defecto.
    
    Heurística:
    - Preferir ataques cuerpo a cuerpo (más comunes)
    - Pero si solo hay distancia, usar esa
    """
    if not acciones:
        return None
    
    if len(acciones) == 1:
        return acciones[0]
    
    # Separar por tipo de alcance
    melee = []
    ranged = []
    
    for acc in acciones:
        alcance = str(acc.get("alcance", "5"))
        if "/" in alcance:  # Formato "80/320" = distancia
            ranged.append(acc)
        else:
            melee.append(acc)
    
    # Preferir melee por defecto (más común en combate)
    if melee:
        return melee[0]
    elif ranged:
        return ranged[0]
    
    return acciones[0]


class PipelineTurno:
    """
    Orquesta el flujo completo de una acción del jugador.
    
    Args:
        compendio: CompendioMotor inyectado
        normalizador: NormalizadorAcciones inyectado (opcional, se crea si no)
        validador: ValidadorAcciones inyectado (opcional, se crea si no)
        llm_callback: Función para fallback a LLM en normalización
        narrador_callback: Función para generar narrativa post-eventos
    """
    
    def __init__(self,
                 compendio: CompendioMotor,
                 normalizador: NormalizadorAcciones = None,
                 validador: ValidadorAcciones = None,
                 llm_callback: Callable[[str, Dict], Dict] = None,
                 narrador_callback: Callable[[List[Evento], Dict], str] = None,
                 strict_equipment: bool = False):
        
        self._compendio = compendio
        self._normalizador = normalizador or NormalizadorAcciones(compendio, llm_callback)
        self._validador = validador or ValidadorAcciones(compendio, strict_equipment)
        self._narrador_callback = narrador_callback
    
    def procesar(self,
                 texto_jugador: str,
                 contexto: ContextoEscena,
                 estado_combate: Dict[str, Any] = None) -> ResultadoPipeline:
        """
        Procesa una acción del jugador.
        
        Args:
            texto_jugador: Lo que dijo el jugador
            contexto: Contexto de la escena (actor, enemigos, equipo, etc.)
            estado_combate: Estado actual del combate (opcional)
            
        Returns:
            ResultadoPipeline con el resultado del procesamiento
        """
        try:
            # Paso 1: Normalizar
            accion = self._normalizador.normalizar(texto_jugador, contexto)
            
            # Paso 2: ¿Necesita clarificación?
            if accion.requiere_clarificacion:
                return self._generar_clarificacion(accion, contexto)
            
            # Paso 3: Validar
            validacion = self._validar_accion(accion, contexto, estado_combate)
            
            # Paso 4: ¿Acción rechazada?
            if not validacion.valido:
                return ResultadoPipeline(
                    tipo=TipoResultado.ACCION_RECHAZADA,
                    motivo=validacion.razon,
                    sugerencia=self._generar_sugerencia(accion, validacion, contexto),
                    accion_normalizada=accion,
                    validacion=validacion
                )
            
            # Paso 5: Ejecutar acción
            eventos, cambios = self._ejecutar_accion(accion, contexto, estado_combate)
            
            # Paso 6: Generar narrativa (si hay callback)
            mensaje_dm = ""
            if self._narrador_callback:
                mensaje_dm = self._narrador_callback(eventos, {
                    "contexto": contexto,
                    "estado_combate": estado_combate
                })
            
            return ResultadoPipeline(
                tipo=TipoResultado.ACCION_APLICADA,
                eventos=eventos,
                cambios_estado=cambios,
                mensaje_dm=mensaje_dm,
                accion_normalizada=accion,
                validacion=validacion
            )
            
        except Exception as e:
            return ResultadoPipeline(
                tipo=TipoResultado.ERROR_INTERNO,
                error=str(e)
            )
    
    def _generar_clarificacion(self,
                               accion: AccionNormalizada,
                               contexto: ContextoEscena) -> ResultadoPipeline:
        """Genera pregunta y opciones para clarificar."""
        pregunta = ""
        opciones = []
        
        if accion.tipo == TipoAccionNorm.ATAQUE:
            if "objetivo_id" in accion.faltantes:
                pregunta = "¿A quién quieres atacar?"
                for enemigo in contexto.enemigos_vivos:
                    opciones.append(OpcionClarificacion(
                        id=enemigo.get("instancia_id") or enemigo.get("id"),
                        texto=enemigo.get("nombre", "Enemigo"),
                        datos={"tipo": "objetivo", "ref": enemigo.get("compendio_ref")}
                    ))
            
            elif "arma_id" in accion.faltantes:
                pregunta = "¿Con qué arma quieres atacar?"
                for arma in contexto.armas_disponibles:
                    opciones.append(OpcionClarificacion(
                        id=arma.get("compendio_ref") or arma.get("id"),
                        texto=arma.get("nombre", "Arma"),
                        datos={"tipo": "arma"}
                    ))
                opciones.append(OpcionClarificacion(
                    id="unarmed",
                    texto="Ataque desarmado",
                    datos={"tipo": "arma"}
                ))
        
        elif accion.tipo == TipoAccionNorm.CONJURO:
            if "conjuro_id" in accion.faltantes:
                pregunta = "¿Qué conjuro quieres lanzar?"
                for conjuro in contexto.conjuros_conocidos:
                    opciones.append(OpcionClarificacion(
                        id=conjuro.get("id"),
                        texto=conjuro.get("nombre", "Conjuro"),
                        datos={"tipo": "conjuro"}
                    ))
        
        elif accion.tipo == TipoAccionNorm.HABILIDAD:
            if "habilidad" in accion.faltantes:
                pregunta = "¿Qué habilidad quieres usar?"
                habilidades = [
                    "Percepción", "Sigilo", "Atletismo", "Acrobacias",
                    "Investigación", "Persuasión", "Engaño", "Intimidación"
                ]
                for hab in habilidades:
                    opciones.append(OpcionClarificacion(
                        id=hab.lower(),
                        texto=hab,
                        datos={"tipo": "habilidad"}
                    ))
        
        elif accion.tipo == TipoAccionNorm.MOVIMIENTO:
            if "distancia_pies" in accion.faltantes:
                pregunta = "¿Cuántos pies quieres moverte?"
                for dist in [5, 10, 15, 20, 25, 30]:
                    if dist <= contexto.movimiento_restante:
                        opciones.append(OpcionClarificacion(
                            id=str(dist),
                            texto=f"{dist} pies",
                            datos={"tipo": "distancia", "valor": dist}
                        ))
        
        else:
            pregunta = "No entendí tu acción. ¿Qué quieres hacer?"
            opciones = [
                OpcionClarificacion("atacar", "Atacar a un enemigo", {"tipo": "intencion"}),
                OpcionClarificacion("conjuro", "Lanzar un conjuro", {"tipo": "intencion"}),
                OpcionClarificacion("mover", "Moverme", {"tipo": "intencion"}),
                OpcionClarificacion("habilidad", "Usar una habilidad", {"tipo": "intencion"}),
            ]
        
        return ResultadoPipeline(
            tipo=TipoResultado.NECESITA_CLARIFICAR,
            pregunta=pregunta,
            opciones=opciones,
            accion_parcial=accion,
            accion_normalizada=accion
        )
    
    def _validar_accion(self,
                        accion: AccionNormalizada,
                        contexto: ContextoEscena,
                        estado_combate: Dict[str, Any] = None) -> ResultadoValidacion:
        """Valida la acción según su tipo."""
        # Construir datos del personaje para el validador
        personaje = self._construir_personaje_para_validacion(contexto)
        
        if accion.tipo == TipoAccionNorm.ATAQUE:
            objetivo = self._buscar_objetivo(accion.datos.get("objetivo_id"), contexto)
            return self._validador.validar_ataque(
                personaje,
                objetivo,
                accion.datos.get("arma_id")
            )
        
        elif accion.tipo == TipoAccionNorm.CONJURO:
            objetivo = self._buscar_objetivo(accion.datos.get("objetivo_id"), contexto)
            return self._validador.validar_conjuro(
                personaje,
                accion.datos.get("conjuro_id"),
                accion.datos.get("nivel_lanzamiento"),
                objetivo
            )
        
        elif accion.tipo == TipoAccionNorm.MOVIMIENTO:
            movimiento_usado = 0
            if estado_combate:
                movimiento_usado = estado_combate.get("movimiento_usado", 0)
            return self._validador.validar_movimiento(
                personaje,
                accion.datos.get("distancia_pies", 0),
                movimiento_usado
            )
        
        elif accion.tipo == TipoAccionNorm.HABILIDAD:
            return self._validador.validar_prueba_habilidad(
                personaje,
                accion.datos.get("habilidad", "")
            )
        
        elif accion.tipo == TipoAccionNorm.ACCION:
            tipo_accion = self._mapear_accion_generica(accion.datos.get("accion_id"))
            return self._validador.validar_accion_generica(tipo_accion, personaje)
        
        # Default: válido
        return ResultadoValidacion(valido=True, razon="Acción permitida")
    
    def _ejecutar_accion(self,
                         accion: AccionNormalizada,
                         contexto: ContextoEscena,
                         estado_combate: Dict[str, Any] = None) -> tuple:
        """
        Ejecuta la acción y genera eventos.
        
        Returns:
            Tupla (eventos, cambios_estado)
        """
        eventos = []
        cambios = {}
        
        if accion.tipo == TipoAccionNorm.ATAQUE:
            eventos, cambios = self._ejecutar_ataque(accion, contexto)
        
        elif accion.tipo == TipoAccionNorm.CONJURO:
            eventos, cambios = self._ejecutar_conjuro(accion, contexto)
        
        elif accion.tipo == TipoAccionNorm.MOVIMIENTO:
            eventos, cambios = self._ejecutar_movimiento(accion, contexto)
        
        elif accion.tipo == TipoAccionNorm.HABILIDAD:
            eventos, cambios = self._ejecutar_habilidad(accion, contexto)
        
        elif accion.tipo == TipoAccionNorm.ACCION:
            eventos, cambios = self._ejecutar_accion_generica(accion, contexto)
        
        return eventos, cambios
    
    def _ejecutar_ataque(self, accion: AccionNormalizada, contexto: ContextoEscena) -> tuple:
        """
        Ejecuta un ataque delegando la lógica a combate_utils.
        
        El pipeline solo:
        1. Extrae datos de la acción normalizada
        2. Detecta si usar acción de monstruo o arma
        3. Llama al resolver apropiado
        4. Transforma el resultado en eventos
        """
        from .combate_utils import resolver_ataque_completo, resolver_ataque_monstruo
        
        objetivo_id = accion.datos.get("objetivo_id")
        modo = accion.datos.get("modo", "normal")
        
        # Obtener CA del objetivo real
        ca_objetivo = 10  # Default
        if objetivo_id:
            # Buscar en enemigos
            for enemigo in contexto.enemigos_vivos:
                if enemigo.get("instancia_id") == objetivo_id:
                    # Intentar obtener CA si está disponible
                    ca_objetivo = enemigo.get("clase_armadura", 10)
                    break
            # Buscar en aliados también
            for aliado in contexto.aliados:
                if aliado.get("instancia_id") == objetivo_id:
                    ca_objetivo = aliado.get("clase_armadura", 10)
                    break
        
        # Determinar si usar acción de monstruo o arma
        ataque_nombre = accion.datos.get("ataque_nombre")
        usar_accion_monstruo = False
        accion_monstruo = None
        
        if contexto.acciones_monstruo:
            # Buscar acción por nombre si se especificó
            if ataque_nombre:
                for acc in contexto.acciones_monstruo:
                    if acc["nombre"].lower() == ataque_nombre.lower():
                        accion_monstruo = acc
                        usar_accion_monstruo = True
                        break
            
            # Si no se encontró por nombre, intentar mapear arma_id a acción
            if not accion_monstruo and contexto.acciones_monstruo:
                arma_id = accion.datos.get("arma_id")
                if arma_id and arma_id != "unarmed":
                    # Mapear arma_id a nombre de acción (ej: "arco_corto" -> "Arco corto")
                    for acc in contexto.acciones_monstruo:
                        nombre_normalizado = normalizar_nombre(acc["nombre"])
                        if nombre_normalizado == arma_id:
                            accion_monstruo = acc
                            usar_accion_monstruo = True
                            break
                
                # Si aún no hay, elegir inteligentemente según contexto
                if not accion_monstruo:
                    accion_monstruo = _elegir_accion_monstruo_inteligente(
                        contexto.acciones_monstruo
                    )
                    usar_accion_monstruo = True
        
        if usar_accion_monstruo and accion_monstruo:
            # Usar resolver de monstruo
            resultado = resolver_ataque_monstruo(
                accion=accion_monstruo,
                ca_objetivo=ca_objetivo,
                modo=modo
            )
            
            # Adaptar resultado para eventos (mismo formato)
            return self._crear_eventos_ataque_monstruo(resultado, contexto, objetivo_id)
        
        # Fallback: usar arma normal
        arma_id = accion.datos.get("arma_id", "unarmed")
        
        # TODO: Obtener bonificadores reales del personaje
        bonificador_ataque = 5  # Placeholder
        modificador_daño = 3   # Placeholder
        
        resultado = resolver_ataque_completo(
            compendio=self._compendio,
            arma_id=arma_id,
            bonificador_ataque=bonificador_ataque,
            modificador_daño=modificador_daño,
            ca_objetivo=ca_objetivo,
            modo=modo
        )
        
        # Transformar resultado en eventos
        eventos = []
        cambios = {}
        
        # Evento de ataque
        evento_ataque = Evento(
            tipo="ataque_realizado",
            actor_id=contexto.actor_id,
            datos={
                "objetivo_id": objetivo_id,
                "arma_id": resultado.arma_id,
                "arma_nombre": resultado.arma_nombre,
                "tirada": {
                    "dados": resultado.tirada_ataque.dados,
                    "modificador": resultado.bonificador_ataque,
                    "total": resultado.total_ataque,
                    "tipo": resultado.modo
                },
                "es_critico": resultado.es_critico,
                "es_pifia": resultado.es_pifia,
                "impacta": resultado.impacta
            }
        )
        eventos.append(evento_ataque)
        
        # Evento de daño (solo si impacta)
        if resultado.impacta:
            evento_daño = Evento(
                tipo="daño_calculado",
                actor_id=contexto.actor_id,
                datos={
                    "objetivo_id": objetivo_id,
                    "tirada": {
                        "expresion": resultado.expresion_daño,
                        "dados": resultado.dados_daño,
                        "modificador": resultado.modificador_daño,
                        "es_critico": resultado.es_critico
                    },
                    "daño_total": resultado.daño_total,
                    "tipo_daño": resultado.tipo_daño,
                    "fuente": {
                        "tipo": "arma" if resultado.arma_id != "unarmed" else "desarmado",
                        "id": resultado.arma_id,
                        "nombre": resultado.arma_nombre
                    }
                }
            )
            eventos.append(evento_daño)
            
            cambios["daño_infligido"] = {
                "objetivo_id": objetivo_id,
                "cantidad": resultado.daño_total,
                "tipo": resultado.tipo_daño
            }
        
        cambios["accion_usada"] = True
        
        return eventos, cambios
    

    def _crear_eventos_ataque_monstruo(self, resultado, contexto, objetivo_id) -> tuple:
        """Crea eventos desde ResultadoAtaqueMonstruo."""
        eventos = []
        cambios = {}
        
        # Evento de ataque
        evento_ataque = Evento(
            tipo="ataque_realizado",
            actor_id=contexto.actor_id,
            datos={
                "objetivo_id": objetivo_id,
                "arma_id": None,
                "arma_nombre": resultado.accion_nombre,
                "tirada": {
                    "dados": resultado.tirada_ataque.dados,
                    "modificador": resultado.bonificador_ataque,
                    "total": resultado.total_ataque,
                    "tipo": resultado.modo
                },
                "es_critico": resultado.es_critico,
                "es_pifia": resultado.es_pifia,
                "impacta": resultado.impacta
            }
        )
        eventos.append(evento_ataque)
        
        # Evento de daño (solo si impacta)
        if resultado.impacta:
            evento_daño = Evento(
                tipo="daño_calculado",
                actor_id=contexto.actor_id,
                datos={
                    "objetivo_id": objetivo_id,
                    "tirada": {
                        "expresion": resultado.expresion_daño,
                        "dados": resultado.tirada_daño.dados if resultado.tirada_daño else [],
                        "modificador": 0,
                        "es_critico": resultado.es_critico
                    },
                    "daño_total": resultado.daño_total,
                    "tipo_daño": resultado.tipo_daño,
                    "fuente": {
                        "tipo": "accion_monstruo",
                        "id": resultado.accion_nombre,
                        "nombre": resultado.accion_nombre
                    }
                }
            )
            eventos.append(evento_daño)
            
            cambios["daño_infligido"] = {
                "objetivo_id": objetivo_id,
                "cantidad": resultado.daño_total,
                "tipo": resultado.tipo_daño
            }
        
        cambios["accion_usada"] = True
        
        return eventos, cambios

    def _ejecutar_conjuro(self, accion: AccionNormalizada, contexto: ContextoEscena) -> tuple:
        """Ejecuta un conjuro y genera eventos."""
        eventos = []
        cambios = {}
        
        conjuro_id = accion.datos.get("conjuro_id")
        conjuro = self._compendio.obtener_conjuro(conjuro_id)
        
        evento = Evento(
            tipo="conjuro_lanzado",
            actor_id=contexto.actor_id,
            datos={
                "conjuro_id": conjuro_id,
                "nombre": conjuro.get("nombre") if conjuro else conjuro_id,
                "nivel": accion.datos.get("nivel_lanzamiento", 0),
                "objetivo_id": accion.datos.get("objetivo_id")
            }
        )
        eventos.append(evento)
        
        nivel = accion.datos.get("nivel_lanzamiento", 0)
        if nivel > 0:
            cambios["ranura_gastada"] = {
                "nivel": nivel,
                "cantidad": 1
            }
        
        cambios["accion_usada"] = True
        
        return eventos, cambios
    
    def _ejecutar_movimiento(self, accion: AccionNormalizada, contexto: ContextoEscena) -> tuple:
        """Ejecuta un movimiento y genera eventos."""
        distancia = accion.datos.get("distancia_pies", 0)
        
        evento = Evento(
            tipo="movimiento_realizado",
            actor_id=contexto.actor_id,
            datos={
                "distancia_pies": distancia,
                "destino": accion.datos.get("destino")
            }
        )
        
        cambios = {
            "movimiento_usado": distancia
        }
        
        return [evento], cambios
    
    def _ejecutar_habilidad(self, accion: AccionNormalizada, contexto: ContextoEscena) -> tuple:
        """Ejecuta una prueba de habilidad y genera eventos."""
        habilidad = accion.datos.get("habilidad", "percepcion")
        
        from .dados import tirar_dado, TipoTirada
        tirada = tirar_dado(20)
        bonificador = 3  # Placeholder
        total = tirada + bonificador
        
        evento = Evento(
            tipo="prueba_habilidad",
            actor_id=contexto.actor_id,
            datos={
                "habilidad": habilidad,
                "tirada_d20": tirada,
                "bonificador": bonificador,
                "total": total,
                "objetivo_id": accion.datos.get("objetivo_id")
            }
        )
        
        return [evento], {}
    
    def _ejecutar_accion_generica(self, accion: AccionNormalizada, contexto: ContextoEscena) -> tuple:
        """Ejecuta una acción genérica y genera eventos."""
        accion_id = accion.datos.get("accion_id", "")
        
        evento = Evento(
            tipo="accion_generica",
            actor_id=contexto.actor_id,
            datos={
                "accion_id": accion_id
            }
        )
        
        cambios = {"accion_usada": True}
        
        # Efectos específicos
        if accion_id == "dash":
            cambios["movimiento_bonus"] = contexto.movimiento_restante
        elif accion_id == "dodge":
            cambios["condicion_temporal"] = "esquivando"
        
        return [evento], cambios
    
    def _generar_sugerencia(self,
                            accion: AccionNormalizada,
                            validacion: ResultadoValidacion,
                            contexto: ContextoEscena) -> str:
        """Genera una sugerencia basada en por qué falló la validación."""
        razon = validacion.razon.lower()
        
        if "no está equipada" in razon:
            return "Usa una interacción de objeto para equipar el arma primero, o ataca desarmado."
        
        if "muerto" in razon:
            if len(contexto.enemigos_vivos) > 0:
                nombres = [e.get("nombre", "?") for e in contexto.enemigos_vivos]
                return f"Elige otro objetivo: {', '.join(nombres)}"
            return "No hay enemigos vivos."
        
        if "ranuras" in razon:
            return "Usa un truco (nivel 0) o descansa para recuperar ranuras."
        
        if "movimiento" in razon:
            return "Usa la acción Dash para duplicar tu movimiento este turno."
        
        if "incapacitado" in razon or "paralizado" in razon:
            return "No puedes actuar mientras tengas esta condición."
        
        return ""
    
    def _construir_personaje_para_validacion(self, contexto: ContextoEscena) -> Dict[str, Any]:
        """Construye un dict de personaje compatible con el validador."""
        return {
            "nombre": contexto.actor_nombre,
            "fuente": {
                "equipo_equipado": {
                    "arma_principal_id": contexto.arma_principal.get("compendio_ref") if contexto.arma_principal else None,
                    "arma_secundaria_id": contexto.arma_secundaria.get("compendio_ref") if contexto.arma_secundaria else None,
                },
                "conjuros_conocidos": [c.get("id") for c in contexto.conjuros_conocidos],
                "conjuros_preparados": [c.get("id") for c in contexto.conjuros_conocidos],
            },
            "recursos": {
                "ranuras_conjuro": {
                    f"nivel_{k}": {"disponibles": v}
                    for k, v in contexto.ranuras_disponibles.items()
                }
            },
            "derivados": {
                "velocidad": contexto.movimiento_restante + 0  # Base
            },
            "estado_actual": {
                "condiciones": [],
                "inconsciente": False,
                "muerto": False
            },
            "velocidad": 30  # Default
        }
    
    def _buscar_objetivo(self, objetivo_id: str, contexto: ContextoEscena) -> Optional[Dict]:
        """Busca un objetivo por ID en el contexto."""
        if not objetivo_id:
            return None
        
        for enemigo in contexto.enemigos_vivos:
            if enemigo.get("instancia_id") == objetivo_id or enemigo.get("id") == objetivo_id:
                return {
                    "nombre": enemigo.get("nombre", "Enemigo"),
                    "puntos_golpe_actual": enemigo.get("puntos_golpe_actual", 10),
                    "estado_actual": enemigo.get("estado_actual", {"muerto": False})
                }
        
        return None
    
    def _mapear_accion_generica(self, accion_id: str) -> TipoAccion:
        """Mapea ID de acción a TipoAccion del validador."""
        mapeo = {
            "dash": TipoAccion.DASH,
            "dodge": TipoAccion.DODGE,
            "disengage": TipoAccion.DISENGAGE,
            "help": TipoAccion.HELP,
            "hide": TipoAccion.HIDE,
            "search": TipoAccion.SEARCH,
            "ready": TipoAccion.READY,
        }
        return mapeo.get(accion_id, TipoAccion.DASH)
