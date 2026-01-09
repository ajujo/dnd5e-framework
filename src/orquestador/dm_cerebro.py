"""
DM Cerebro - El orquestador principal.

Coordina el LLM con las herramientas y el contexto
para crear una experiencia de juego coherente.
"""

import json
from typing import Any, Dict, List, Optional, Callable
from generador import obtener_prompt_tono, obtener_balance_solitario, obtener_bible_manager

from .contexto import GestorContexto
from .parser_respuesta import parsear_respuesta, RespuestaLLM, validar_respuesta
from herramientas import ejecutar_herramienta, documentacion_herramientas, listar_herramientas


# System prompt base para el DM
SYSTEM_PROMPT_DM = """Eres el Dungeon Master (DM) de una partida de D&D 5e EN SOLITARIO, ambientada en REINOS OLVIDADOS (Faerûn).

═══════════════════════════════════════════════════════════════════════
AMBIENTACIÓN: REINOS OLVIDADOS (FORGOTTEN REALMS)
═══════════════════════════════════════════════════════════════════════

El mundo es Toril, continente de Faerûn. Conoces bien:
- COSTA DE LA ESPADA: Aguas Profundas, Neverwinter, Puerta de Baldur, Luskan
- EL NORTE: Diez Ciudades, Mithral Hall, Valle del Viento Helado
- INTERIOR: Cormyr, Sembia, Tierras de los Valles
- Organizaciones: Arpistas, Zhentarim, Enclave Esmeralda, Orden del Guantelete, Alianza de los Señores
- Deidades: Torm, Tyr, Lathander, Selûne, Shar, Mystra, Tempus, Kelemvor

Usa nombres, lugares y referencias coherentes con este mundo.
Los PNJ tienen MEMORIA, INTERESES y RELACIONES PERSISTENTES.

═══════════════════════════════════════════════════════════════════════
TU ROL COMO DM (PARTIDA EN SOLITARIO)
═══════════════════════════════════════════════════════════════════════

- Narras de forma inmersiva, concisa y evocadora (2-3 frases)
- Interpretas PNJ con personalidad, motivaciones y objetivos propios
- Creas CONFLICTO y TENSIÓN de forma regular
- Mantienes coherencia narrativa a corto y largo plazo
- Ajustas la DIFICULTAD para UN SOLO PERSONAJE (no un grupo)
- Gestionas los modos: EXPLORACIÓN, SOCIAL, COMBATE

═══════════════════════════════════════════════════════════════════════
REGLA FUNDAMENTAL: NUNCA BLOQUEAR EL PROGRESO
═══════════════════════════════════════════════════════════════════════

❗ NUNCA bloquees el progreso de la historia por una tirada fallida.

Los FALLOS generan:
- Costes (tiempo, recursos, HP)
- Complicaciones (alertar enemigos, perder confianza)
- Consecuencias narrativas (el NPC desconfía, la puerta hace ruido)

Pero la historia SIEMPRE AVANZA. Ofrece alternativas tras cada fallo.

═══════════════════════════════════════════════════════════════════════
AVENTURA PRINCIPAL vs SECUNDARIAS
═══════════════════════════════════════════════════════════════════════

MAIN QUEST (Aventura principal):
- El gancho y la información clave NUNCA requieren tirada
- Las tiradas modifican el CÓMO, no el SI
- La aventura principal SIEMPRE progresa

SIDE QUESTS (Secundarias):
- Son opcionales, pueden descubrirse o perderse
- Sus consecuencias persisten en el mundo
- Enriquecen pero no bloquean la main quest

═══════════════════════════════════════════════════════════════════════
GENERACIÓN ACTIVA DE CONFLICTO
═══════════════════════════════════════════════════════════════════════

Debes generar desafíos regularmente:

1. COMBATES (cada 3-5 escenas de exploración):
   - Emboscadas, cacerías, enfrentamientos
   
   ⚠️ REGLA OBLIGATORIA DE COMBATE:
   Cuando aparezcan enemigos hostiles, DEBES seguir este orden EXACTO:
   
   PASO 1: Usa "listar_monstruos" para ver monstruos disponibles
   PASO 2: Usa "iniciar_combate" con los IDs de monstruos del compendio
           Ejemplo: {{"herramienta": "iniciar_combate", "parametros": {{"enemigos": ["bandido", "bandido"]}}}}
   PASO 3: El sistema calculará iniciativa y gestionará turnos
   PASO 4: En cada turno de combate, usa "tirar_ataque" o "dañar_enemigo"
   
   ❌ PROHIBIDO: Narrar ataques o daño SIN haber llamado a "iniciar_combate" primero
   ❌ PROHIBIDO: Inventar monstruos que no estén en el compendio
   ❌ PROHIBIDO: Resolver combates narrativamente sin usar las herramientas
   
   - Ajusta cantidad de enemigos para UN SOLO PJ (1-3 enemigos débiles o 1 fuerte)

2. OBSTÁCULOS CON ALTERNATIVAS:
   - Puertas, ríos, trampas, acantilados
   - Un fallo SIEMPRE ofrece al menos una alternativa viable

3. ENCUENTROS SOCIALES TENSOS:
   - PNJ con intereses propios, no todos cooperan
   - Las decisiones afectan relaciones futuras
   - Recuerda interacciones previas con cada PNJ

═══════════════════════════════════════════════════════════════════════
MODOS DE JUEGO
═══════════════════════════════════════════════════════════════════════

EXPLORACIÓN: Viajes, búsqueda, investigación. Pocas tiradas salvo peligro.
SOCIAL: Diálogos importantes. Tiradas solo si hay resistencia real.
COMBATE: OBLIGATORIO llamar "iniciar_combate" ANTES de cualquier ataque.
         El sistema gestiona turnos e iniciativa automáticamente.
         NO narres ataques sin haber iniciado combate formalmente.

Indica SIEMPRE "cambio_modo" cuando la situación cambie.

═══════════════════════════════════════════════════════════════════════
INVENTARIO Y ECONOMÍA (OBLIGATORIO)
═══════════════════════════════════════════════════════════════════════

NO narres que el jugador obtiene algo sin usar la herramienta correspondiente:
- Obtiene objeto → "dar_objeto"
- Gana/gasta oro → "modificar_oro"
- Pierde objeto → "quitar_objeto"

El inventario SOLO se actualiza con herramientas.

═══════════════════════════════════════════════════════════════════════
MEMORIA NARRATIVA (CRÍTICO PARA COHERENCIA)
═══════════════════════════════════════════════════════════════════════

Debes actualizar la memoria narrativa en cada respuesta relevante:

MAIN_QUEST:
- fase_actual: dónde está la aventura principal
- objetivo_inmediato: qué debe hacer el jugador ahora
- revelaciones_clave: información importante descubierta

SIDE_QUESTS:
- Lista de misiones secundarias con estado (activa/resuelta/fallida)

PNJ_RELEVANTES:
- nombre, actitud hacia el jugador, última interacción

AMENAZAS_ACTIVAS:
- Enemigos, facciones hostiles, peligros latentes

Esta memoria influye en escenas futuras y garantiza continuidad.

═══════════════════════════════════════════════════════════════════════
HERRAMIENTAS DISPONIBLES
═══════════════════════════════════════════════════════════════════════
{herramientas}

═══════════════════════════════════════════════════════════════════════
FORMATO DE RESPUESTA (JSON ESTRICTO)
═══════════════════════════════════════════════════════════════════════
{{
    "herramienta": "nombre_herramienta o null",
    "parametros": {{}},
    "narrativa": "Narración inmersiva (2-3 frases)",
    "cambio_modo": "exploracion | social | combate | null",
    "memoria": {{
        "main_quest": {{"fase": "", "objetivo": "", "revelacion": ""}},
        "pnj": {{"nombre": "", "actitud": "", "nota": ""}},
        "amenaza": ""
    }}
}}

NOTAS sobre el JSON:
- "herramienta": null si no necesitas ejecutar ninguna
- "parametros": {{}} vacío si no hay herramienta
- "cambio_modo": null si no cambia el modo
- "memoria": incluir SOLO los campos que cambien, puede ser {{}} si nada cambia

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
    

    def _obtener_contexto_bible(self) -> str:
        """Obtiene el contexto de la Adventure Bible para el prompt."""
        pj_id = self.contexto.pj.get("id", "") if self.contexto.pj else ""
        if not pj_id:
            return ""
        
        try:
            bm = obtener_bible_manager()
            bible = bm.cargar_bible_full(pj_id)
            if not bible:
                return ""
            
            # Generar vista DM (filtrada, sin spoilers)
            vista = bm.generar_vista_dm(bible)
            
            partes = []
            partes.append("═══════════════════════════════════════════════════════════════════════")
            partes.append("ADVENTURE BIBLE (GUÍA INTERNA - NO REVELAR DIRECTAMENTE)")
            partes.append("═══════════════════════════════════════════════════════════════════════")
            partes.append("")
            
            # Situación actual
            sit = vista.get("situacion_actual", {})
            partes.append(f"OBJETIVO ACTUAL: {sit.get('objetivo_inmediato', 'Explorar')}")
            partes.append(f"TENSIÓN: {sit.get('tension_actual', 'media')}")
            partes.append("")
            
            # Acto actual
            acto = vista.get("acto_actual_info", {})
            if acto:
                partes.append(f"ACTO {acto.get('numero', 1)}: {acto.get('nombre', '')}")
                partes.append(f"Objetivo del acto: {acto.get('objetivo', '')}")
                
                escenas = acto.get("escenas_disponibles", [])
                if escenas:
                    partes.append("Escenas sugeridas:")
                    for e in escenas[:3]:
                        estado = "✓" if e.get("completada") else "○"
                        partes.append(f"  {estado} [{e.get('tipo', '?')}] {e.get('descripcion', '')[:50]}")
                partes.append("")
            
            # Antagonista (sombra)
            ant = vista.get("antagonista_sombra", {})
            if ant:
                if ant.get("revelacion_disponible"):
                    partes.append(f"ANTAGONISTA: {ant.get('identidad_real', 'Desconocido')}")
                    partes.append(f"Motivación: {ant.get('motivacion', '')}")
                    partes.append(f"Debilidad: {ant.get('debilidad', '')}")
                else:
                    partes.append(f"ANTAGONISTA (OCULTO): {ant.get('descripcion_vaga', 'Una fuerza misteriosa')}")
                    pistas = ant.get("pistas_para_sembrar", [])
                    if pistas:
                        partes.append("Pistas de foreshadowing que puedes sembrar:")
                        for p in pistas[:2]:
                            partes.append(f"  - {p}")
                partes.append("")
            
            # NPCs relevantes
            npcs = vista.get("pnj_en_escena", [])
            if npcs:
                partes.append("NPCs RELEVANTES:")
                for npc in npcs[:4]:
                    hint = f" ({npc.get('secreto_hint', '')})" if npc.get('secreto_hint') else ""
                    partes.append(f"  - {npc.get('nombre')}: {npc.get('actitud_actual', 'neutral')}{hint}")
                partes.append("")
            
            # Revelaciones pendientes
            revs = vista.get("revelaciones_pendientes", [])
            if revs:
                partes.append("REVELACIONES PENDIENTES (entregar al menos la pista garantizada):")
                for rev in revs[:2]:
                    partes.append(f"  → GARANTIZADA: {rev.get('pista_garantizada', 'N/A')}")
                partes.append("")
            
            # Relojes
            relojes = vista.get("relojes_visibles", [])
            if relojes:
                partes.append("RELOJES DE TENSIÓN:")
                for r in relojes:
                    partes.append(f"  ⏱ {r.get('nombre')}: {r.get('segmentos')} [{r.get('urgencia', 'media').upper()}]")
                    partes.append(f"    Avanza cuando: {r.get('que_avanza', '')[:50]}")
                partes.append("")
            
            # Canon
            canon = vista.get("canon_activo", [])
            if canon:
                partes.append("CANON (NO CONTRADECIR):")
                for c in canon[:4]:
                    partes.append(f"  • {c}")
                partes.append("")
            
            return "\n".join(partes)
            
        except Exception as e:
            if hasattr(self, 'debug_mode') and self.debug_mode:
                print(f"[DEBUG] Error cargando bible: {e}")
            return ""

    def _construir_system_prompt(self) -> str:
        """Construye el system prompt completo para el DM."""
        # Obtener documentación de herramientas
        doc_herramientas = documentacion_herramientas()
        
        # Obtener contexto actual
        contexto = self.contexto.generar_contexto_llm()
        
        # Construir prompt base
        prompt = SYSTEM_PROMPT_DM.format(
            herramientas=doc_herramientas,
            contexto=contexto
        )
        
        # Obtener e inyectar prompt de tono si hay tipo de aventura
        tipo_aventura = self.contexto.flags.get("tipo_aventura", {})
        if tipo_aventura and tipo_aventura.get("id"):
            prompt_tono = obtener_prompt_tono(tipo_aventura["id"])
            if prompt_tono:
                # Insertar el tono antes del contexto actual
                marcador = "═══════════════════════════════════════════════════════════════════════\nCONTEXTO ACTUAL"
                if marcador in prompt:
                    prompt = prompt.replace(marcador, prompt_tono + "\n\n" + marcador)
                else:
                    # Si no encuentra el marcador, añadir al final
                    prompt = prompt + "\n\n" + prompt_tono
        
        # Obtener e inyectar contexto de la Adventure Bible
        contexto_bible = self._obtener_contexto_bible()
        if contexto_bible:
            prompt = prompt + "\n\n" + contexto_bible
        
        return prompt


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
            
            # VALIDACIÓN: tirar_ataque y dañar_enemigo requieren combate activo
            herramientas_combate = ["tirar_ataque", "dañar_enemigo"]
            if respuesta.herramienta in herramientas_combate:
                if not self.contexto.estado_combate:
                    # No hay combate activo, forzar al LLM a iniciarlo
                    resultado_turno["resultado_mecanico"] = {
                        "error": "NO HAY COMBATE ACTIVO",
                        "mensaje": "Debes usar 'iniciar_combate' antes de atacar",
                        "accion_requerida": "Usa iniciar_combate con los enemigos apropiados"
                    }
                    resultado_turno["narrativa"] = "⚠️ [Sistema: Se requiere iniciar combate formalmente antes de atacar]"
                    return resultado_turno
            
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
        
        # Procesar actualización de memoria narrativa
        memoria_update = getattr(respuesta, 'memoria', None)
        if memoria_update:
            self.contexto.actualizar_memoria(memoria_update)
        
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
