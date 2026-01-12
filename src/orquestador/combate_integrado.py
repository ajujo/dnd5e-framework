"""
Orquestador de Combate Integrado

Conecta el motor de combate táctico (GestorCombate + PipelineTurno)
con el flujo de aventura (DMCerebro).

RESPONSABILIDADES:
- Controlar loop de turnos
- Ejecutar IA para turnos de enemigos
- Obtener input del jugador para turnos del PC
- Llamar al narrador LLM para narrativa inmersiva
- Detectar condiciones de victoria/derrota
- Devolver resultado estructurado

EL LLM NO DECIDE MECÁNICA - SOLO NARRA
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

from motor import (
    GestorCombate,
    PipelineTurno,
    TipoCombatiente,
    TipoResultado,
    ResultadoPipeline,
    NarradorLLM,
    Evento,
    resolver_ataque_monstruo,
    crear_contexto_narracion,
)


class EstadoCombateIntegrado(Enum):
    """Estado del combate integrado."""
    EN_CURSO = "en_curso"
    ESPERANDO_INPUT = "esperando_input"
    VICTORIA = "victoria"
    DERROTA = "derrota"
    HUIDA = "huida"


@dataclass
class ResultadoCombate:
    """Resultado final del combate."""
    victoria: bool
    enemigos_derrotados: List[str] = field(default_factory=list)
    hp_final_pj: int = 0
    hp_max_pj: int = 0
    xp_ganada: int = 0
    botin: List[Dict[str, Any]] = field(default_factory=list)
    resumen_narrativo: str = ""
    rondas_totales: int = 0


@dataclass
class TurnoInfo:
    """Información sobre el turno actual."""
    combatiente_id: str
    combatiente_nombre: str
    es_jugador: bool
    ronda: int
    necesita_input: bool = False


class OrquestadorCombate:
    """
    Orquesta el combate táctico desde el flujo de aventura.
    
    El motor controla la mecánica, el LLM solo narra.
    """
    
    def __init__(
        self,
        gestor: GestorCombate,
        llm_callback: Optional[Callable[[str, str], str]] = None,
        input_callback: Optional[Callable[[str], str]] = None,
        output_callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Args:
            gestor: GestorCombate ya inicializado con combatientes
            llm_callback: Función para narrar eventos (system, user) -> respuesta
            input_callback: Función para obtener input del jugador (prompt) -> texto
            output_callback: Función para mostrar texto al usuario (texto) -> None
        """
        self.gestor = gestor
        self.llm_callback = llm_callback
        self.input_callback = input_callback or input
        self.output_callback = output_callback or print
        
        self.estado = EstadoCombateIntegrado.EN_CURSO
        self.log_eventos: List[Evento] = []
        self.narrativas: List[str] = []
        
        # Crear narrador si hay LLM
        # llm_callback viene como (system, user) -> str pero NarradorLLM espera (prompt) -> str
        # Creamos un wrapper que use un system prompt fijo para combate
        if llm_callback:
            def narrador_callback(prompt: str) -> str:
                system = (
                    "Eres un narrador épico de combates D&D. "
                    "Narra los eventos de forma breve pero inmersiva (1-2 frases). "
                    "Usa lenguaje evocador pero conciso."
                )
                return llm_callback(system, prompt)
            self.narrador = NarradorLLM(narrador_callback)
        else:
            self.narrador = None
        self.usar_llm_narracion = True  # Flag para toggle de narración LLM
    
    def obtener_turno_actual(self) -> Optional[TurnoInfo]:
        """Obtiene información del turno actual."""
        combatiente = self.gestor.obtener_turno_actual()
        if not combatiente:
            return None
        
        return TurnoInfo(
            combatiente_id=combatiente.id,
            combatiente_nombre=combatiente.nombre,
            es_jugador=(combatiente.tipo == TipoCombatiente.PC),
            ronda=self.gestor.ronda_actual,
            necesita_input=(combatiente.tipo == TipoCombatiente.PC),
        )
    
    def procesar_turno_jugador(self, accion_texto: str) -> Dict[str, Any]:
        """
        Procesa el turno del jugador.
        
        Args:
            accion_texto: Texto en lenguaje natural ("ataco al goblin con mi espada")
            
        Returns:
            Diccionario con resultado: narrativa, eventos, cambios, etc.
        """
        resultado = self.gestor.procesar_accion(accion_texto)
        
        # Generar narrativa
        narrativa = self._narrar_resultado(resultado)
        
        # Verificar si el combate terminó
        self._verificar_fin_combate()
        
        # Avanzar al siguiente turno si la acción fue exitosa
        if resultado.tipo == TipoResultado.ACCION_APLICADA:
            self.gestor.siguiente_turno()
        
        return {
            "tipo": resultado.tipo.value,
            "narrativa": narrativa,
            "eventos": [e.to_dict() for e in resultado.eventos],
            "necesita_clarificacion": resultado.tipo == TipoResultado.NECESITA_CLARIFICAR,
            "opciones": [{"id": o.id, "texto": o.texto} for o in resultado.opciones] if resultado.opciones else [],
            "combate_terminado": self.estado != EstadoCombateIntegrado.EN_CURSO,
        }
    
    def ejecutar_turno_enemigo(self, enemigo_id: str) -> Dict[str, Any]:
        """
        Ejecuta el turno de un enemigo (IA simple).
        
        La IA siempre ataca al PJ (único objetivo posible).
        """
        enemigo = self.gestor.obtener_combatiente(enemigo_id)
        if not enemigo or not enemigo.puede_actuar:
            return {"exito": False, "error": "Enemigo no puede actuar"}
        
        # Obtener PJ como objetivo
        pj = self.gestor.obtener_combatiente("pj")
        if not pj or not pj.esta_vivo:
            self._verificar_fin_combate()
            return {"exito": False, "error": "No hay objetivo válido"}
        
        # Usar acciones del monstruo (cargadas del compendio)
        if not enemigo.acciones:
            # Fallback: ataque básico
            return self._ataque_basico_enemigo(enemigo, pj)
        
        # Usar primera acción disponible
        accion = enemigo.acciones[0]
        from motor import tirar
        
        # Tirada de ataque - guardar d20 y bonificador por separado
        resultado_d20 = tirar("1d20")
        d20_valor = resultado_d20.total
        bonificador_ataque = accion.get("bonificador_ataque", 0)
        tirada_ataque = d20_valor + bonificador_ataque
        impacta = tirada_ataque >= pj.clase_armadura
        critico = d20_valor == 20  # Crítico es cuando el d20 natural es 20
        
        # Calcular daño si impacta - guardar desglose
        daño_total = 0
        daño_dados = 0  # Solo la parte de dados
        daño_mod = 0    # Solo el modificador
        daño_expresion = accion.get("daño", "1d6+0")
        if impacta:
            resultado_daño = tirar(daño_expresion)
            # Extraer dados y modificador por separado
            if resultado_daño.dados:
                daño_dados = sum(resultado_daño.dados)
            daño_mod = resultado_daño.total - daño_dados
            
            if critico:
                # Crítico: tirar dados de nuevo, pero mismo modificador
                resultado_critico = tirar(daño_expresion)
                if resultado_critico.dados:
                    daño_dados += sum(resultado_critico.dados)
                # No duplicamos el modificador, solo los dados
            
            daño_total = daño_dados + daño_mod
        
        # Aplicar daño si impactó
        eventos = []
        if impacta and daño_total > 0:
            pj.hp_actual = max(0, pj.hp_actual - daño_total)
            
            eventos.append(Evento(
                tipo="ataque_impacta",
                actor_id=enemigo_id,
                datos={
                    "objetivo_id": "pj",
                    "daño": daño_total,
                    "tipo_daño": accion.get("tipo_daño", "físico"),
                    "accion": accion.get("nombre", "Ataque"),
                    "tirada": tirada_ataque,
                    "critico": critico,
                }
            ))
            
            if pj.hp_actual <= 0:
                pj.inconsciente = True
                eventos.append(Evento(
                    tipo="combatiente_cae",
                    actor_id="pj",
                    datos={"causa": "daño", "atacante": enemigo.nombre}
                ))
        else:
            eventos.append(Evento(
                tipo="ataque_falla",
                actor_id=enemigo_id,
                datos={
                    "objetivo_id": "pj",
                    "tirada": tirada_ataque,
                    "ca_objetivo": pj.clase_armadura,
                    "accion": accion.get("nombre", "Ataque"),
                }
            ))
        
        # Generar narrativa
        nombre_accion = accion.get("nombre", "Ataque")
        narrativa = ""
        
        # Usar LLM si está activado
        if self.narrador and self.usar_llm_narracion:
            try:
                prompt = (
                    f"{enemigo.nombre} ataca a {pj.nombre} con {nombre_accion}. "
                    f"Tirada: {tirada_ataque} vs CA {pj.clase_armadura}. "
                )
                if impacta:
                    prompt += f"¡Impacta! Causa {daño_total} de daño."
                    if critico:
                        prompt += " (¡Crítico!)"
                else:
                    prompt += "Falla."
                prompt += " Narra esto de forma breve y épica."
                
                narrativa = self.narrador._llm(prompt) if self.narrador._llm else ""
            except Exception:
                pass
        
        # Fallback a narrativa fija si no hay LLM o falló
        if not narrativa:
            if impacta:
                narrativa = f"{enemigo.nombre} te ataca con {nombre_accion}. ¡Impacta causando {daño_total} de daño!"
            else:
                narrativa = f"{enemigo.nombre} ataca con {nombre_accion} pero falla."
        
        # Verificar fin de combate
        self._verificar_fin_combate()
        
        # Avanzar turno
        self.gestor.siguiente_turno()
        
        return {
            "exito": True,
            "enemigo": enemigo.nombre,
            "accion": nombre_accion,
            "impacta": impacta,
            "critico": critico,
            "d20_valor": d20_valor,
            "tirada_ataque": tirada_ataque,
            "bonificador_ataque": bonificador_ataque,
            "ca_objetivo": pj.clase_armadura,
            "daño": daño_total if impacta else 0,
            "daño_dados": daño_dados if impacta else 0,
            "daño_mod": daño_mod if impacta else 0,
            "daño_expresion": daño_expresion,
            "narrativa": narrativa,
            "eventos": [e.to_dict() for e in eventos],
            "combate_terminado": self.estado != EstadoCombateIntegrado.EN_CURSO,
        }
    
    def _ataque_basico_enemigo(self, enemigo, objetivo) -> Dict[str, Any]:
        """Ataque básico cuando no hay datos de monstruo."""
        from motor import tirar
        
        # Tirada de ataque simple
        tirada = tirar("1d20").total
        impacta = tirada >= objetivo.clase_armadura
        
        eventos = []
        daño = 0
        
        if impacta:
            daño = tirar("1d6").total
            objetivo.hp_actual = max(0, objetivo.hp_actual - daño)
            eventos.append(Evento(
                tipo="ataque_impacta",
                actor_id=enemigo.id,
                datos={"objetivo_id": objetivo.id, "daño": daño, "tirada": tirada}
            ))
        else:
            eventos.append(Evento(
                tipo="ataque_falla",
                actor_id=enemigo.id,
                datos={"objetivo_id": objetivo.id, "tirada": tirada, "ca_objetivo": objetivo.clase_armadura}
            ))
        
        self._verificar_fin_combate()
        self.gestor.siguiente_turno()
        
        return {
            "exito": True,
            "enemigo": enemigo.nombre,
            "impacta": impacta,
            "daño": daño,
            "narrativa": f"{enemigo.nombre} ataca. {'¡Impacta!' if impacta else 'Falla.'}",
            "eventos": [e.to_dict() for e in eventos],
        }
    
    def _narrar_resultado(self, resultado: ResultadoPipeline) -> str:
        """Genera narrativa para un resultado del pipeline."""
        # Usar LLM para narrar si está activado y disponible
        if self.narrador and self.usar_llm_narracion and resultado.eventos:
            try:
                contexto = crear_contexto_narracion(self.gestor, resultado)
                respuesta = self.narrador.narrar(contexto)
                if respuesta and respuesta.narracion:
                    return respuesta.narracion
            except Exception as e:
                pass  # Fallback a narrativa mecánica
        
        # Fallback: narrativa mecánica basada en eventos
        if resultado.tipo == TipoResultado.ACCION_APLICADA:
            partes = []
            if resultado.eventos:
                for evento in resultado.eventos:
                    tipo = evento.tipo
                    datos = evento.datos
                    
                    if tipo == "ataque_realizado":
                        tirada = datos.get("tirada", {})
                        d20 = tirada.get("dados", [0])[0] if tirada.get("dados") else "?"
                        mod = tirada.get("modificador", 0)
                        total = tirada.get("total", "?")
                        impacta = datos.get("impacta", False)
                        # Obtener nombre real del objetivo (no el ID interno)
                        objetivo_id = datos.get("objetivo_id", "objetivo")
                        objetivo = datos.get("objetivo_nombre")
                        if not objetivo:
                            # Buscar el nombre real del combatiente
                            combatiente = self.gestor.obtener_combatiente(objetivo_id)
                            objetivo = combatiente.nombre if combatiente else objetivo_id
                        arma = datos.get("arma_nombre", "arma")
                        
                        if impacta:
                            partes.append(f"🎲 Ataque con {arma}: {d20}(d20) + {mod}(mod) = {total} → ¡Impacta!")
                        else:
                            partes.append(f"🎲 Ataque con {arma}: {d20}(d20) + {mod}(mod) = {total} → Falla")
                    
                    elif tipo == "daño_aplicado" or tipo == "daño_calculado":
                        daño = datos.get("daño_total", datos.get("cantidad", 0))
                        objetivo_id = datos.get("objetivo_id", "objetivo")
                        objetivo = datos.get("objetivo_nombre")
                        if not objetivo:
                            combatiente = self.gestor.obtener_combatiente(objetivo_id)
                            objetivo = combatiente.nombre if combatiente else objetivo_id
                        
                        # Mostrar desglose si está disponible
                        tirada = datos.get("tirada", {})
                        if tirada and tirada.get("dados"):
                            dados = tirada.get("dados", [])
                            dados_total = sum(dados)
                            mod = tirada.get("modificador", 0)
                            expresion = tirada.get("expresion", "")
                            dado_exp = expresion.split("+")[0] if "+" in expresion else expresion
                            partes.append(f"💥 Daño: {dados_total}({dado_exp}) + {mod}(mod) = {daño} a {objetivo}")
                        else:
                            partes.append(f"💥 Daño: {daño} a {objetivo}")
                    
                    elif tipo == "combatiente_cae":
                        objetivo_id = datos.get("objetivo_id", "combatiente")
                        quien = datos.get("objetivo_nombre")
                        if not quien:
                            combatiente = self.gestor.obtener_combatiente(objetivo_id)
                            quien = combatiente.nombre if combatiente else objetivo_id
                        partes.append(f"💀 {quien} cae!")
            
            if partes:
                return "\n  ".join(partes)
            # Acción aplicada pero sin eventos de ataque - puede ser movimiento u otra acción
            return resultado.mensaje_dm or "Acción ejecutada."
        
        elif resultado.tipo == TipoResultado.NECESITA_CLARIFICAR:
            return resultado.pregunta or "¿Qué quieres hacer exactamente?"
        elif resultado.tipo == TipoResultado.ACCION_RECHAZADA:
            # Debug: mostrar el error real
            if resultado.error:
                return f"❌ {resultado.error}"
            return "No puedes hacer eso."
        elif resultado.tipo == TipoResultado.ERROR_INTERNO:
            return f"⚠️ Error interno: {resultado.error or 'desconocido'}"
        else:
            return f"Algo salió mal. (tipo: {resultado.tipo})"
    
    def _narrar_eventos_enemigo(self, eventos, enemigo, objetivo, resultado_ataque) -> str:
        """Genera narrativa para el turno de un enemigo."""
        if self.narrador:
            try:
                contexto = {
                    "actor": enemigo.nombre,
                    "objetivo": objetivo.nombre,
                    "accion": resultado_ataque.nombre_accion,
                }
                return self.narrador.narrar(eventos, contexto)
            except Exception:
                pass
        
        # Fallback
        if resultado_ataque.impacta:
            daño = resultado_ataque.daño_total
            return f"{enemigo.nombre} te ataca con {resultado_ataque.nombre_accion}. ¡Impacta causando {daño} de daño!"
        else:
            return f"{enemigo.nombre} ataca pero falla."
    
    def _verificar_fin_combate(self) -> None:
        """Verifica si el combate ha terminado."""
        # Verificar victoria (todos los enemigos derrotados)
        enemigos_vivos = [
            c for c in self.gestor.listar_combatientes()
            if c.tipo == TipoCombatiente.NPC_ENEMIGO and c.esta_vivo
        ]
        
        if not enemigos_vivos:
            self.estado = EstadoCombateIntegrado.VICTORIA
            return
        
        # Verificar derrota (PJ inconsciente/muerto)
        pj = self.gestor.obtener_combatiente("pj")
        if pj and (pj.hp_actual <= 0 or not pj.esta_vivo):
            self.estado = EstadoCombateIntegrado.DERROTA
            return
    
    def obtener_resultado_final(self) -> ResultadoCombate:
        """Genera el resultado final del combate."""
        pj = self.gestor.obtener_combatiente("pj")
        
        # Calcular enemigos derrotados y XP
        enemigos_derrotados = []
        xp_total = 0
        
        for c in self.gestor.listar_combatientes():
            if c.tipo == TipoCombatiente.NPC_ENEMIGO and not c.esta_vivo:
                enemigos_derrotados.append(c.nombre)
                # XP basada en compendio_ref - calculamos una XP simple basada en sus stats
                xp_total += 25  # XP simple por enemigo
        
        # Generar resumen narrativo
        resumen = ""
        if self.estado == EstadoCombateIntegrado.VICTORIA:
            resumen = f"¡Victoria! Has derrotado a {', '.join(enemigos_derrotados)}."
        elif self.estado == EstadoCombateIntegrado.DERROTA:
            resumen = "Has caído en combate..."
        
        return ResultadoCombate(
            victoria=(self.estado == EstadoCombateIntegrado.VICTORIA),
            enemigos_derrotados=enemigos_derrotados,
            hp_final_pj=pj.hp_actual if pj else 0,
            hp_max_pj=pj.hp_maximo if pj else 0,
            xp_ganada=xp_total,
            resumen_narrativo=resumen,
            rondas_totales=self.gestor.ronda_actual,
        )
    
    def ejecutar_combate_completo(self) -> ResultadoCombate:
        """
        Ejecuta el combate completo de forma interactiva.
        
        Usa input_callback para obtener acciones del jugador
        y output_callback para mostrar narrativa.
        """
        while self.estado == EstadoCombateIntegrado.EN_CURSO:
            turno = self.obtener_turno_actual()
            if not turno:
                break
            
            if turno.es_jugador:
                # Turno del jugador
                self.output_callback(f"\n═══ Tu turno (Ronda {turno.ronda}) ═══")
                
                while True:
                    accion = self.input_callback("¿Qué haces? > ")
                    
                    if accion.lower() in ("/huir", "/escapar", "/flee"):
                        self.estado = EstadoCombateIntegrado.HUIDA
                        break
                    
                    resultado = self.procesar_turno_jugador(accion)
                    self.output_callback(resultado["narrativa"])
                    
                    if resultado["necesita_clarificacion"]:
                        # Mostrar opciones
                        for i, opt in enumerate(resultado["opciones"], 1):
                            self.output_callback(f"  {i}. {opt['texto']}")
                        continue
                    
                    break
            else:
                # Turno del enemigo
                self.output_callback(f"\n--- Turno de {turno.combatiente_nombre} ---")
                resultado = self.ejecutar_turno_enemigo(turno.combatiente_id)
                self.output_callback(resultado.get("narrativa", ""))
        
        return self.obtener_resultado_final()
