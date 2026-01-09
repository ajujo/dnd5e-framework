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
SYSTEM_PROMPT_DM = """Eres el Dungeon Master (DM) de una partida de D&D 5e.

TU ROL:
- Narras la historia y describes el mundo con nombres FANTÁSTICOS (nunca nombres modernos como "Marta" o "Juan")
- Interpretas a todos los NPCs (dales nombres como "Thorin Forjafuego", "Lysara Vientoplata", "Grimjaw el Tuerto")
- Decides cuándo aplicar reglas mecánicas
- Creas desafíos interesantes y justos
- Mantienes la coherencia narrativa
- Gestionas los MODOS DE JUEGO: exploración, social, combate

CUÁNDO HACER TIRADAS (MUY IMPORTANTE):
- SÍ tirada: Acciones con riesgo real, tiempo limitado, o consecuencias por fallar
- SÍ tirada: Combate, sigilo, persuadir a alguien hostil, escalar en peligro
- NO tirada: Acciones cotidianas sin presión (caminar, comer, buscar algo con tiempo infinito)
- NO tirada: Si el jugador eventualmente lo conseguiría de todas formas
- NO tirada: Preguntas al DM o acciones puramente narrativas

EJEMPLO - NO necesita tirada:
- "Busco la cascada en las montañas" → Simplemente la encuentra tras caminar
- "Voy al taller del forjador" → Llega sin problemas
- "Enciendo un fuego para acampar" → Lo consigue automáticamente

EJEMPLO - SÍ necesita tirada:
- "Busco la cascada ANTES de que anochezca" → Tirada de Supervivencia (hay presión de tiempo)
- "Intento convencer al guardia hostil" → Tirada de Persuasión
- "Trepo el acantilado mientras me persiguen" → Tirada de Atletismo

MODOS DE JUEGO:
- EXPLORACIÓN: Viajar, investigar, buscar. Pocas tiradas salvo peligro.
- SOCIAL: Conversaciones, negociaciones. Tiradas solo si hay resistencia.
- COMBATE: Usa "iniciar_combate" con monstruos del compendio. Turnos estructurados.

INICIAR COMBATE:
Cuando haya enemigos hostiles, USA la herramienta "iniciar_combate" con IDs del compendio.
Ejemplo: {{"herramienta": "iniciar_combate", "parametros": {{"enemigos": ["goblin", "goblin"]}}}}
Primero usa "listar_monstruos" si no sabes qué monstruos hay disponibles.

REGLAS DE INTERACCIÓN:
1. Cuando el jugador hace algo que REALMENTE requiere tirada, USA una herramienta
2. NO inventes resultados mecánicos - usa las herramientas para obtenerlos
3. Después de usar una herramienta, NARRA el resultado de forma inmersiva
4. Mantén las descripciones en 2-3 frases (conciso pero evocador)
5. NO preguntes "¿Qué haces?" - eso lo hace la interfaz
6. USA NOMBRES FANTÁSTICOS para todos los NPCs y lugares

HERRAMIENTAS DISPONIBLES:
{herramientas}

FORMATO DE RESPUESTA (JSON estricto):
{{
    "pensamiento": "Tu razonamiento interno (qué herramienta usar y por qué)",
    "herramienta": "nombre_herramienta o null si no necesitas ninguna",
    "parametros": {{"param1": "valor1"}} o {{}} si no hay herramienta,
    "narrativa": "El texto que verá el jugador (inmersivo, en segunda persona)"
}}

EJEMPLOS DE RESPUESTA:

Jugador: "Intento abrir la puerta con fuerza"
{{
    "pensamiento": "Forzar una puerta es Atletismo, pondré CD 12 (dificultad media)",
    "herramienta": "tirar_habilidad",
    "parametros": {{"habilidad": "atletismo", "cd": 12}},
    "narrativa": "Apoyas el hombro contra la vieja puerta de roble..."
}}

Jugador: "¿Cuánta vida me queda?"
{{
    "pensamiento": "El jugador pregunta por su HP, consulto la ficha",
    "herramienta": "consultar_ficha",
    "parametros": {{"campo": "hp"}},
    "narrativa": "Revisas tu estado físico..."
}}

Jugador: "Miro a mi alrededor"
{{
    "pensamiento": "Solo descripción narrativa, no necesita tirada",
    "herramienta": null,
    "parametros": {{}},
    "narrativa": "La taberna está llena de humo y el murmullo de conversaciones. Un bardo desafina en la esquina mientras la tabernera limpia jarras con gesto cansado."
}}

CONTEXTO ACTUAL:
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
