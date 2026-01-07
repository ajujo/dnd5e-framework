"""
Narrador LLM para D&D 5e

El LLM actúa SOLO como narrador, no como motor de reglas.

RESPONSABILIDADES:
✓ Recibir estado + eventos estructurados
✓ Generar narración inmersiva
✓ Reformular preguntas de clarificación (sin cambiar opciones)

NO HACE:
✗ Decidir reglas
✗ Modificar estado
✗ Cambiar opciones de clarificación
✗ Interpretar acciones (eso es el normalizador)

PATRÓN: Inyección de dependencias
- Recibe callback de LLM por constructor
- Funciona sin LLM (devuelve texto genérico)
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

from .pipeline_turno import Evento, ResultadoPipeline, TipoResultado
from .gestor_combate import Combatiente, EstadoCombate


@dataclass
class ContextoNarracion:
    """
    Contexto completo para que el LLM narre.
    
    Incluye todo lo necesario para generar texto inmersivo
    sin necesidad de conocer reglas.
    """
    # Estado general
    ronda: int
    estado_combate: str  # "en_curso", "victoria", etc.
    
    # Turno actual
    actor_nombre: str
    actor_hp: int
    actor_hp_max: int
    actor_condiciones: List[str]
    
    # Eventos ocurridos (ya resueltos)
    eventos: List[Dict[str, Any]]
    
    # Participantes
    combatientes: List[Dict[str, Any]]
    
    # Clarificación (si aplica)
    necesita_clarificacion: bool = False
    pregunta_clarificacion: str = ""
    opciones_clarificacion: List[Dict[str, str]] = field(default_factory=list)
    
    # Rechazo (si aplica)
    accion_rechazada: bool = False
    motivo_rechazo: str = ""
    sugerencia: str = ""


@dataclass
class RespuestaNarrador:
    """
    Respuesta del narrador.
    
    Separa:
    - narracion: texto de roleplay/inmersión
    - feedback_sistema: mensajes técnicos (errores, sugerencias)
    - pregunta_reformulada: solo si hay clarificación
    """
    narracion: str
    feedback_sistema: Optional[str] = None  # Errores, sugerencias técnicas
    pregunta_reformulada: Optional[str] = None  # Solo si hay clarificación
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "narracion": self.narracion,
            "feedback_sistema": self.feedback_sistema,
            "pregunta_reformulada": self.pregunta_reformulada
        }


class NarradorLLM:
    """
    Genera narración usando un LLM.
    
    Args:
        llm_callback: Función que recibe prompt y devuelve texto.
                     Si es None, usa narración genérica.
        estilo: Estilo de narración ("epico", "casual", "minimalista")
    """
    
    def __init__(self, 
                 llm_callback: Callable[[str], str] = None,
                 estilo: str = "epico"):
        self._llm = llm_callback
        self._estilo = estilo
    
    def narrar(self, contexto: ContextoNarracion) -> RespuestaNarrador:
        """
        Genera narración para el contexto dado.
        
        Args:
            contexto: ContextoNarracion con todo lo necesario
            
        Returns:
            RespuestaNarrador con texto y pregunta reformulada si aplica
        """
        if contexto.necesita_clarificacion:
            return self._narrar_clarificacion(contexto)
        
        if contexto.accion_rechazada:
            return self._narrar_rechazo(contexto)
        
        return self._narrar_eventos(contexto)
    
    def _narrar_eventos(self, contexto: ContextoNarracion) -> RespuestaNarrador:
        """Narra los eventos de una acción exitosa."""
        if self._llm:
            prompt = self._construir_prompt_eventos(contexto)
            narracion = self._llm(prompt)
            return RespuestaNarrador(narracion=narracion)
        
        # Narración genérica sin LLM
        return RespuestaNarrador(
            narracion=self._generar_narracion_generica(contexto)
        )
    
    def _narrar_clarificacion(self, contexto: ContextoNarracion) -> RespuestaNarrador:
        """Narra una solicitud de clarificación."""
        if self._llm:
            prompt = self._construir_prompt_clarificacion(contexto)
            narracion = self._llm(prompt)
        else:
            narracion = f"El DM necesita más información."
        
        # Reformular pregunta pero NUNCA cambiar opciones
        pregunta = contexto.pregunta_clarificacion
        if self._llm and pregunta:
            prompt_pregunta = f"""Reformula esta pregunta de forma más inmersiva para D&D:
"{pregunta}"
Opciones disponibles: {[o['texto'] for o in contexto.opciones_clarificacion]}
IMPORTANTE: No cambies el significado ni añadas/quites opciones.
Solo reformula la pregunta de forma más narrativa."""
            pregunta = self._llm(prompt_pregunta)
        
        return RespuestaNarrador(
            narracion=narracion,
            pregunta_reformulada=pregunta
        )
    
    def _narrar_rechazo(self, contexto: ContextoNarracion) -> RespuestaNarrador:
        """Narra el rechazo de una acción."""
        # Feedback técnico (siempre presente)
        feedback = contexto.motivo_rechazo
        if contexto.sugerencia:
            feedback += f" Sugerencia: {contexto.sugerencia}"
        
        # Narración inmersiva
        if self._llm:
            prompt = f"""Eres el DM de una partida de D&D 5e.
{contexto.actor_nombre} intentó hacer algo que no es posible.
Explica brevemente por qué no puede hacerlo de forma narrativa (1 frase).
NO incluyas sugerencias técnicas, solo narración."""
            narracion = self._llm(prompt)
        else:
            narracion = f"{contexto.actor_nombre} no puede hacer eso."
        
        return RespuestaNarrador(
            narracion=narracion,
            feedback_sistema=feedback
        )
    
    def _construir_prompt_eventos(self, contexto: ContextoNarracion) -> str:
        """Construye el prompt para narrar eventos."""
        # Describir eventos
        eventos_texto = []
        for evento in contexto.eventos:
            eventos_texto.append(self._describir_evento(evento))
        
        # Describir estado de combatientes
        estado_texto = []
        for c in contexto.combatientes:
            hp_pct = int(100 * c.get("hp_actual", 0) / max(1, c.get("hp_maximo", 1)))
            estado = "ileso" if hp_pct > 75 else "herido" if hp_pct > 25 else "malherido"
            estado_texto.append(f"- {c['nombre']}: {estado}")
        
        estilo_instruccion = {
            "epico": "Usa un tono épico y dramático.",
            "casual": "Usa un tono casual y ligero.",
            "minimalista": "Sé muy breve y directo."
        }.get(self._estilo, "")
        
        return f"""Eres el DM de una partida de D&D 5e. Narra lo que acaba de ocurrir.

RONDA: {contexto.ronda}
TURNO DE: {contexto.actor_nombre}

EVENTOS (en orden):
{chr(10).join(eventos_texto)}

ESTADO DE LOS COMBATIENTES:
{chr(10).join(estado_texto)}

INSTRUCCIONES:
- {estilo_instruccion}
- Narra en segunda persona si es un PC ("Lanzas tu espada...")
- Narra en tercera persona si es un NPC ("El goblin ataca...")
- Sé conciso (2-4 frases máximo)
- NO inventes reglas ni resultados, solo narra lo que pasó
- NO menciones números de dados ni mecánicas"""
    
    def _construir_prompt_clarificacion(self, contexto: ContextoNarracion) -> str:
        """Construye prompt para narrar necesidad de clarificación."""
        return f"""Eres el DM de una partida de D&D 5e.
{contexto.actor_nombre} quiere hacer algo pero necesitas más información.
Pregunta original: {contexto.pregunta_clarificacion}
Opciones: {[o['texto'] for o in contexto.opciones_clarificacion]}

Introduce la pregunta de forma narrativa, breve (1 frase).
NO cambies las opciones."""
    
    def _describir_evento(self, evento: Dict[str, Any]) -> str:
        """Describe un evento en texto para el prompt."""
        tipo = evento.get("tipo", "desconocido")
        datos = evento.get("datos", {})
        
        if tipo == "ataque_realizado":
            tirada = datos.get("tirada", {})
            resultado = "IMPACTA" if datos.get("impacta") else "FALLA"
            critico = " (¡CRÍTICO!)" if datos.get("es_critico") else ""
            pifia = " (¡PIFIA!)" if datos.get("es_pifia") else ""
            return f"Ataque con {datos.get('arma_nombre', 'arma')}: {resultado}{critico}{pifia}"
        
        elif tipo == "daño_calculado":
            return f"Daño: {datos.get('daño_total', 0)} de tipo {datos.get('tipo_daño', 'desconocido')}"
        
        elif tipo == "conjuro_lanzado":
            return f"Conjuro: {datos.get('nombre', 'desconocido')} lanzado"
        
        elif tipo == "movimiento_realizado":
            return f"Movimiento: {datos.get('distancia_pies', 0)} pies"
        
        elif tipo == "prueba_habilidad":
            return f"Prueba de {datos.get('habilidad', '?')}: total {datos.get('total', 0)}"
        
        elif tipo == "accion_generica":
            return f"Acción: {datos.get('accion_id', 'desconocida')}"
        
        return f"Evento: {tipo}"
    
    def _generar_narracion_generica(self, contexto: ContextoNarracion) -> str:
        """Genera narración sin LLM, respetando estilo."""
        # Intro según estilo
        if self._estilo == "minimalista":
            partes = []
        elif self._estilo == "epico":
            partes = [f"¡Es el turno de {contexto.actor_nombre}!"]
        else:  # casual
            partes = [f"Turno de {contexto.actor_nombre}."]
        
        for evento in contexto.eventos:
            tipo = evento.get("tipo", "")
            datos = evento.get("datos", {})
            
            if tipo == "ataque_realizado":
                if datos.get("es_critico"):
                    partes.append(f"¡Golpe crítico con {datos.get('arma_nombre', 'su arma')}!")
                elif datos.get("es_pifia"):
                    partes.append(f"¡Falla estrepitosamente!")
                elif datos.get("impacta"):
                    partes.append(f"Ataca con {datos.get('arma_nombre', 'su arma')} y acierta.")
                else:
                    partes.append(f"Ataca con {datos.get('arma_nombre', 'su arma')} pero falla.")
            
            elif tipo == "daño_calculado":
                partes.append(f"Causa {datos.get('daño_total', 0)} de daño.")
            
            elif tipo == "conjuro_lanzado":
                partes.append(f"Lanza {datos.get('nombre', 'un conjuro')}.")
            
            elif tipo == "movimiento_realizado":
                partes.append(f"Se mueve {datos.get('distancia_pies', 0)} pies.")
            
            elif tipo == "prueba_habilidad":
                partes.append(f"Hace una prueba de {datos.get('habilidad', 'habilidad')}.")
            
            elif tipo == "accion_generica":
                accion = datos.get('accion_id', '')
                if accion == "dodge":
                    partes.append("Se prepara para esquivar.")
                elif accion == "dash":
                    partes.append("Corre a toda velocidad.")
                elif accion == "disengage":
                    partes.append("Se retira con cuidado.")
                else:
                    partes.append(f"Realiza {accion}.")
        
        texto = " ".join(partes)
        
        # Estilo minimalista: máximo 1 frase
        if self._estilo == "minimalista" and ". " in texto:
            texto = texto.split(". ")[0] + "."
        
        return texto


def crear_contexto_narracion(
    gestor,  # GestorCombate
    resultado: ResultadoPipeline
) -> ContextoNarracion:
    """
    Crea un ContextoNarracion desde el estado del gestor y resultado del pipeline.
    
    Esta función es el "puente" entre el motor de reglas y el narrador.
    """
    combatiente = gestor.obtener_turno_actual()
    
    # Obtener combatientes para contexto
    combatientes_info = []
    for c in gestor.listar_combatientes():
        combatientes_info.append({
            "nombre": c.nombre,
            "hp_actual": c.hp_actual,
            "hp_maximo": c.hp_maximo,
            "tipo": c.tipo.value,
            "muerto": c.muerto,
            "condiciones": c.condiciones.copy()
        })
    
    # Eventos como dicts
    eventos_dict = [e.to_dict() for e in resultado.eventos] if resultado.eventos else []
    
    contexto = ContextoNarracion(
        ronda=gestor.ronda_actual,
        estado_combate=gestor.estado.value,
        actor_nombre=combatiente.nombre if combatiente else "Desconocido",
        actor_hp=combatiente.hp_actual if combatiente else 0,
        actor_hp_max=combatiente.hp_maximo if combatiente else 1,
        actor_condiciones=combatiente.condiciones.copy() if combatiente else [],
        eventos=eventos_dict,
        combatientes=combatientes_info,
    )
    
    # Manejar clarificación
    if resultado.tipo == TipoResultado.NECESITA_CLARIFICAR:
        contexto.necesita_clarificacion = True
        contexto.pregunta_clarificacion = resultado.pregunta
        contexto.opciones_clarificacion = [
            {"id": o.id, "texto": o.texto}
            for o in resultado.opciones
        ]
    
    # Manejar rechazo
    if resultado.tipo == TipoResultado.ACCION_RECHAZADA:
        contexto.accion_rechazada = True
        contexto.motivo_rechazo = resultado.motivo
        contexto.sugerencia = resultado.sugerencia
    
    return contexto
