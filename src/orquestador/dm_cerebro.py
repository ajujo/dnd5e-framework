"""
DM Cerebro - El orquestador principal.

Coordina el LLM con las herramientas y el contexto
para crear una experiencia de juego coherente.
"""

import json
from typing import Any, Dict, List, Optional, Callable

from .contexto import GestorContexto
from .parser_respuesta import parsear_respuesta, RespuestaLLM, validar_respuesta
from herramientas import ejecutar_herramienta, documentacion_herramientas, listar_herramientas


# System prompt base para el DM
SYSTEM_PROMPT_DM = """Eres el Dungeon Master (DM) de una partida de D&D 5e ambientada en REINOS OLVIDADOS (Faerûn).

═══════════════════════════════════════════════════════════════════════
AMBIENTACIÓN: REINOS OLVIDADOS (FORGOTTEN REALMS)
═══════════════════════════════════════════════════════════════════════

El mundo es Toril, continente de Faerûn. Conoces bien:
- COSTA DE LA ESPADA: Aguas Profundas, Neverwinter, Baldur's Gate, Puerta de Baldur
- EL NORTE: Diez Ciudades, Mithral Hall, Luskan, Valle del Viento Helado
- INTERIOR: Cormyr, Sembia, las Tierras de los Valles
- Organizaciones: Arpistas, Zentharim, Enclave Esmeralda, Orden del Guantelete, Alianza de los Señores
- Deidades: Torm, Tyr, Lathander, Selûne, Shar, Mystra, Tempus...

Usa nombres, lugares y referencias de este mundo. Los NPCs conocen la geografía, política y religiones de Faerûn.

═══════════════════════════════════════════════════════════════════════
TU ROL COMO DM
═══════════════════════════════════════════════════════════════════════

- Narras con nombres FANTÁSTICOS del estilo Reinos Olvidados
- Creas DESAFÍOS frecuentes: combates, obstáculos, pruebas
- Interpretas NPCs con personalidad y motivaciones
- Mantienes la coherencia narrativa y el ritmo de la aventura
- Gestionas los modos: EXPLORACIÓN, SOCIAL, COMBATE

═══════════════════════════════════════════════════════════════════════
REGLA DE AVENTURA ACTIVA: ¡GENERA DESAFÍOS!
═══════════════════════════════════════════════════════════════════════

Una buena aventura tiene CONFLICTO. Debes generar regularmente:

1. COMBATES (cada 3-5 escenas de exploración):
   - Emboscadas de bandidos, monstruos, criaturas
   - USA LA HERRAMIENTA "iniciar_combate" con monstruos del compendio
   - Ejemplo: emboscada de goblins en el bosque → {{"herramienta": "iniciar_combate", "parametros": {{"enemigos": ["goblin", "goblin", "goblin"]}}}}
   - Usa "listar_monstruos" para ver qué enemigos hay disponibles

2. OBSTÁCULOS CON ALTERNATIVAS:
   - Acantilados, ríos, puertas cerradas, trampas
   - Si el jugador FALLA una tirada, SIEMPRE ofrece alternativas:
     * Rodear por otro camino (más tiempo)
     * Usar otra habilidad diferente
     * Buscar ayuda o herramientas
     * Consecuencia narrativa pero avance (se hace daño pero cruza)
   - NUNCA bloquees completamente el progreso por un fallo

3. ENCUENTROS SOCIALES TENSOS:
   - NPCs con intereses propios, no todos son amigables
   - Negociaciones, intimidaciones, engaños

═══════════════════════════════════════════════════════════════════════
AVENTURA PRINCIPAL vs SECUNDARIAS
═══════════════════════════════════════════════════════════════════════

MAIN QUEST (Aventura principal):
- El gancho NUNCA requiere tirada - la información se entrega siempre
- Las tiradas modulan el CÓMO (tono, detalles extra), no el SI
- La aventura principal SIEMPRE avanza

SIDE QUESTS (Secundarias):
- Pueden descubrirse o no según tiradas
- Son opcionales y pueden cerrarse por fallos

═══════════════════════════════════════════════════════════════════════
MODOS DE JUEGO - INDICA CAMBIOS
═══════════════════════════════════════════════════════════════════════

EXPLORACIÓN: Viajes, búsqueda, investigación del entorno
- Pocas tiradas salvo peligro real
- Aquí ocurren emboscadas y encuentros aleatorios

SOCIAL: Conversaciones importantes, negociaciones
- Tiradas solo si hay resistencia Y no es main quest
- Cambia a este modo cuando hay diálogo importante

COMBATE: Enfrentamientos con enemigos
- USA "iniciar_combate" para activar combate estructurado
- El combate se resuelve por turnos con tiradas de ataque
- Cambia a este modo cuando hay hostilidades

IMPORTANTE: Indica "cambio_modo" en tu respuesta cuando la situación cambie.

═══════════════════════════════════════════════════════════════════════
INVENTARIO - USA LAS HERRAMIENTAS
═══════════════════════════════════════════════════════════════════════

Cuando el jugador OBTIENE un objeto, USA la herramienta "dar_objeto":
- Encuentra monedas → {{"herramienta": "modificar_oro", "parametros": {{"cantidad": 10, "motivo": "botín"}}}}
- Obtiene objeto → {{"herramienta": "dar_objeto", "parametros": {{"id_objeto": "pocion_curacion"}}}}
- Gasta dinero → {{"herramienta": "modificar_oro", "parametros": {{"cantidad": -5, "motivo": "compra"}}}}

NO narres que obtiene algo sin usar la herramienta. El inventario SOLO se actualiza con herramientas.

═══════════════════════════════════════════════════════════════════════
TIRADAS - CUÁNDO SÍ Y CUÁNDO NO
═══════════════════════════════════════════════════════════════════════

SÍ TIRADA:
- Acciones con riesgo real, presión de tiempo, o consecuencias
- Combate, sigilo, persuadir hostiles, trepar en peligro
- Descubrir información OPCIONAL (side quests)

NO TIRADA:
- Ganchos de main quest
- Acciones cotidianas sin presión
- Si eventualmente lo conseguiría de todas formas

═══════════════════════════════════════════════════════════════════════
HERRAMIENTAS DISPONIBLES
═══════════════════════════════════════════════════════════════════════
{herramientas}

═══════════════════════════════════════════════════════════════════════
FORMATO DE RESPUESTA (JSON estricto)
═══════════════════════════════════════════════════════════════════════
{{
    "pensamiento": "¿Main quest? ¿Necesita tirada? ¿Desafío? ¿Cambio de modo?",
    "herramienta": "nombre_herramienta o null",
    "parametros": {{"param1": "valor1"}} o {{}},
    "narrativa": "Texto inmersivo 2-3 frases",
    "cambio_modo": "exploracion/social/combate o null"
}}

═══════════════════════════════════════════════════════════════════════
EJEMPLOS
═══════════════════════════════════════════════════════════════════════

Jugador camina por bosque (generar encuentro):
{{
    "pensamiento": "Llevan varias escenas sin combate. Genero una emboscada.",
    "herramienta": "iniciar_combate",
    "parametros": {{"enemigos": ["goblin", "goblin"]}},
    "narrativa": "De entre los arbustos saltan dos figuras verdosas blandiendo cuchillos oxidados. ¡Goblins!",
    "cambio_modo": "combate"
}}

Jugador encuentra tesoro:
{{
    "pensamiento": "El jugador encuentra monedas. Uso modificar_oro para añadirlas.",
    "herramienta": "modificar_oro",
    "parametros": {{"cantidad": 15, "motivo": "cofre encontrado"}},
    "narrativa": "Dentro del cofre encuentras un puñado de monedas de oro que brillan a la luz de tu antorcha."
}}

Jugador falla trepar pero hay alternativa:
{{
    "pensamiento": "Falló Atletismo pero no debo bloquear. Ofrezco alternativas.",
    "herramienta": null,
    "parametros": {{}},
    "narrativa": "Tus dedos resbalan en la roca húmeda y caes de vuelta al suelo. Podrías intentar buscar otro camino rodeando el acantilado, o quizás haya raíces más arriba que te den mejor agarre."
}}

Conversación importante con NPC:
{{
    "pensamiento": "Empieza diálogo importante. Cambio a modo social.",
    "herramienta": null,
    "parametros": {{}},
    "narrativa": "Vaelindra Tormenta de Estrellas te observa con ojos que han visto siglos. 'Siéntate, joven. Tenemos mucho de qué hablar.'",
    "cambio_modo": "social"
}}

═══════════════════════════════════════════════════════════════════════
CONTEXTO ACTUAL
═══════════════════════════════════════════════════════════════════════
{contexto}
"""


class DMCerebro:
    """
    El cerebro del DM - coordina LLM, herramientas y contexto.
    """
    
    def __init__(self, llm_callback: Callable[[str, str], str] = None):
        """
        Args:
            llm_callback: Función que recibe (system_prompt, user_message) 
                         y devuelve la respuesta del LLM
        """
        self.contexto = GestorContexto()
        self.llm_callback = llm_callback
        self.ultimo_resultado_herramienta: Optional[Dict[str, Any]] = None
        self.debug_mode = False
    
    def cargar_personaje(self, pj: Dict[str, Any]) -> None:
        """Carga el personaje jugador."""
        self.contexto.cargar_pj(pj)
    
    def establecer_escena(self, ubicacion_id: str, nombre: str, 
                          descripcion: str, tipo: str = "exterior") -> None:
        """Establece la escena inicial."""
        self.contexto.establecer_ubicacion(ubicacion_id, nombre, descripcion, tipo)
    
    def añadir_npc(self, **kwargs) -> None:
        """Añade un NPC a la escena."""
        self.contexto.añadir_npc(**kwargs)
    
    def _construir_system_prompt(self) -> str:
        """Construye el system prompt con contexto actual."""
        return SYSTEM_PROMPT_DM.format(
            herramientas=documentacion_herramientas(),
            contexto=self.contexto.generar_contexto_llm()
        )
    
    def _llamar_llm(self, mensaje_usuario: str) -> str:
        """Llama al LLM con el mensaje del usuario."""
        if not self.llm_callback:
            return '{"pensamiento": "Sin LLM", "herramienta": null, "parametros": {}, "narrativa": "El DM no está disponible."}'
        
        system_prompt = self._construir_system_prompt()
        
        if self.debug_mode:
            print("\n[DEBUG] System prompt length:", len(system_prompt))
            print("[DEBUG] User message:", mensaje_usuario[:100])
        
        return self.llm_callback(system_prompt, mensaje_usuario)
    
    def procesar_turno(self, accion_jugador: str) -> Dict[str, Any]:
        """
        Procesa un turno completo.
        
        1. Registra la acción del jugador
        2. Llama al LLM
        3. Parsea la respuesta
        4. Ejecuta herramienta si la hay
        5. Si hay herramienta, vuelve a llamar al LLM con el resultado
        6. Devuelve la narrativa final
        
        Returns:
            {
                "narrativa": str,
                "resultado_mecanico": dict o None,
                "herramienta_usada": str o None,
                "modo": str
            }
        """
        resultado_turno = {
            "narrativa": "",
            "resultado_mecanico": None,
            "herramienta_usada": None,
            "modo": self.contexto.modo_juego
        }
        
        # Registrar acción del jugador
        self.contexto.registrar_historial("accion_jugador", accion_jugador)
        
        # Primera llamada al LLM
        respuesta_raw = self._llamar_llm(accion_jugador)
        
        if self.debug_mode:
            print(f"\n[DEBUG] LLM response: {respuesta_raw[:500]}")
        
        # Parsear respuesta
        respuesta = parsear_respuesta(respuesta_raw, formato="json")
        
        valido, error = validar_respuesta(respuesta)
        if not valido:
            resultado_turno["narrativa"] = f"[Error del DM: {error}]"
            return resultado_turno
        
        # ¿Hay herramienta que ejecutar?
        if respuesta.herramienta:
            resultado_turno["herramienta_usada"] = respuesta.herramienta
            
            # Ejecutar herramienta
            contexto_herramienta = self.contexto.generar_diccionario_contexto()
            resultado_herramienta = ejecutar_herramienta(
                respuesta.herramienta,
                contexto_herramienta,
                **respuesta.parametros
            )
            
            resultado_turno["resultado_mecanico"] = resultado_herramienta
            self.ultimo_resultado_herramienta = resultado_herramienta
            
            if self.debug_mode:
                print(f"\n[DEBUG] Tool result: {resultado_herramienta}")
            
            # Registrar resultado mecánico
            self.contexto.registrar_historial(
                "resultado_mecanico",
                f"{respuesta.herramienta}: {json.dumps(resultado_herramienta, ensure_ascii=False)}"
            )
            
            # Segunda llamada al LLM para narrar el resultado
            mensaje_resultado = f"""El jugador dijo: "{accion_jugador}"

Usaste la herramienta '{respuesta.herramienta}' y obtuviste este resultado:
{json.dumps(resultado_herramienta, indent=2, ensure_ascii=False)}

Ahora NARRA el resultado de forma inmersiva para el jugador.
Responde SOLO con JSON en este formato:
{{"pensamiento": "...", "herramienta": null, "parametros": {{}}, "narrativa": "Tu narración aquí"}}"""
            
            respuesta_narracion_raw = self._llamar_llm(mensaje_resultado)
            respuesta_narracion = parsear_respuesta(respuesta_narracion_raw, formato="json")
            
            # Usar la narrativa de la segunda respuesta si existe
            if respuesta_narracion.narrativa:
                resultado_turno["narrativa"] = respuesta_narracion.narrativa
            else:
                # Fallback: narrativa de la primera respuesta + resultado
                resultado_turno["narrativa"] = respuesta.narrativa or self._generar_narrativa_fallback(
                    respuesta.herramienta, resultado_herramienta
                )
        else:
            # Sin herramienta, usar narrativa directa
            resultado_turno["narrativa"] = respuesta.narrativa
        
        # Registrar narrativa
        self.contexto.registrar_historial("respuesta_dm", resultado_turno["narrativa"])
        
        # Avanzar turno
        self.contexto.avanzar_turno()
        
        # Manejar acciones especiales del DM
        if respuesta.accion_dm:
            self._procesar_accion_dm(respuesta.accion_dm)
        
        # Procesar cambio de modo si lo hay
        cambio_modo = getattr(respuesta, 'cambio_modo', None)
        if cambio_modo and cambio_modo in ("exploracion", "social", "combate"):
            self.contexto.cambiar_modo(cambio_modo)
            resultado_turno["modo"] = cambio_modo
        
        return resultado_turno
    
    def _generar_narrativa_fallback(self, herramienta: str, resultado: Dict[str, Any]) -> str:
        """Genera narrativa básica cuando el LLM no responde bien."""
        if herramienta == "tirar_habilidad":
            if resultado.get("exito"):
                return f"Lo consigues. ({resultado.get('desglose', '')})"
            else:
                return f"No lo logras. ({resultado.get('desglose', '')})"
        
        elif herramienta == "tirar_ataque":
            if resultado.get("impacta"):
                return f"¡Impactas! Causas {resultado.get('daño', 0)} de daño."
            else:
                return f"El ataque falla. ({resultado.get('desglose', '')})"
        
        elif herramienta == "consultar_ficha":
            return f"Información: {resultado.get('datos', resultado)}"
        
        return str(resultado)
    
    def _procesar_accion_dm(self, accion: str) -> None:
        """Procesa acciones especiales del DM."""
        if accion == "iniciar_combate":
            self.contexto.cambiar_modo("combate")
            self.contexto.estado_combate = {
                "ronda": 1,
                "turno_actual": "PJ",
                "combatientes": []
            }
        elif accion == "fin_combate":
            self.contexto.cambiar_modo("exploracion")
            self.contexto.estado_combate = None
        elif accion == "modo_social":
            self.contexto.cambiar_modo("social")
        elif accion == "modo_exploracion":
            self.contexto.cambiar_modo("exploracion")
    
    def narrar_escena_inicial(self) -> str:
        """Genera la narración inicial de la escena."""
        if not self.llm_callback:
            if self.contexto.ubicacion:
                return self.contexto.ubicacion.descripcion
            return "Te encuentras en un lugar desconocido."
        
        mensaje = "Genera una descripción inicial atmosférica de la escena actual (2-3 frases). NO hagas preguntas."
        
        respuesta_raw = self._llamar_llm(mensaje)
        respuesta = parsear_respuesta(respuesta_raw, formato="json")
        
        return respuesta.narrativa or self.contexto.ubicacion.descripcion if self.contexto.ubicacion else "Te encuentras en un lugar desconocido."
    
    def obtener_estado_juego(self) -> Dict[str, Any]:
        """Devuelve el estado actual del juego."""
        return {
            "turno": self.contexto.turno,
            "modo": self.contexto.modo_juego,
            "ubicacion": self.contexto.ubicacion.nombre if self.contexto.ubicacion else None,
            "npcs": [npc.nombre for npc in self.contexto.npcs_activos],
            "hp_pj": self.contexto.pj.get("derivados", {}).get("puntos_golpe_actual") if self.contexto.pj else None
        }
    
    def guardar_estado(self) -> Dict[str, Any]:
        """Serializa el estado completo para guardado."""
        return self.contexto.serializar()
    
    def cargar_estado(self, datos: Dict[str, Any]) -> None:
        """Restaura el estado desde datos guardados."""
        self.contexto.deserializar(datos)
