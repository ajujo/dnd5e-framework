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
   
   ⛔ REGLA CRÍTICA DE COMBATE - FALLO = ERROR GRAVE:
   
   Cuando un enemigo vaya a atacar o un jugador quiera atacar, DEBES:
   
   PASO 1: Llamar "iniciar_combate" ANTES de cualquier narración de ataque
           Ejemplo: {{"herramienta": "iniciar_combate", "parametros": {{"enemigos": ["bandido"]}}}}
   PASO 2: El sistema creará el combate táctico con iniciativa
   PASO 3: A partir de ahí, el SISTEMA gestiona los turnos, no tú
   
   ❌ NUNCA narres que un enemigo ataca, hiere o daña al jugador SIN iniciar_combate
   ❌ NUNCA narres que el jugador ataca a un enemigo SIN iniciar_combate
   ❌ NUNCA cambies a modo COMBATE sin llamar a la herramienta iniciar_combate
   ❌ NUNCA inventes monstruos - usa SOLO IDs del compendio
   
   Si el jugador dice "ataco" y NO hay combate activo, llama iniciar_combate primero.
   
   📊 LÍMITES DE DIFICULTAD PARA 1 PJ:
   
   | Nivel PJ | Máximo Enemigos | Ejemplos Válidos |
   |----------|-----------------|------------------|
   | 1        | 1-2 CR 1/4 o inferior | 1 goblin, 2 ratas gigantes |
   | 2        | 1-2 CR 1/2 o inferior | 1 orco, 2 goblins |
   | 3        | 1-2 CR 1 o inferior | 1 bugbear, 2 esqueletos |
   | 4-5      | 1-2 CR 2 o inferior | 1 ogro, 2 orcos |
   
   ⚠️ NUNCA uses 3+ enemigos contra 1 PJ (casi siempre LETAL)
   ⚠️ Prefiere 1 enemigo fuerte a varios débiles

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
COMBATE: ⛔ SOLO entrar con "iniciar_combate". El sistema gestiona turnos.
         Si narras un ataque sin haber llamado iniciar_combate, HAS FALLADO.

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
    
    Modos de operación:
    - NARRATIVO (exploración/social): El LLM controla el flujo
    - TÁCTICO (combate): OrquestadorCombate controla, LLM solo narra
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
        
        # Combate táctico
        self.orquestador_combate: Optional['OrquestadorCombate'] = None
        self.gestor_combate = None  # GestorCombate activo
    
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
    
    def en_combate_tactico(self) -> bool:
        """Verifica si hay un combate táctico activo."""
        return self.orquestador_combate is not None and self.gestor_combate is not None
    
    def _iniciar_combate_tactico(self, gestor) -> None:
        """Inicia el modo de combate táctico."""
        from .combate_integrado import OrquestadorCombate
        
        self.gestor_combate = gestor
        self.orquestador_combate = OrquestadorCombate(
            gestor=gestor,
            llm_callback=self.llm_callback,
        )
        self.contexto.cambiar_modo("combate")
        
        if self.debug_mode:
            print("[DEBUG] Combate táctico iniciado")
    
    def _finalizar_combate_tactico(self, resultado) -> Dict[str, Any]:
        """Finaliza el combate táctico y vuelve al modo narrativo."""
        # Actualizar HP del PJ
        if self.contexto.pj and resultado:
            self.contexto.pj["derivados"]["puntos_golpe_actual"] = resultado.hp_final_pj
            
            # Añadir XP si hubo victoria
            if resultado.victoria and resultado.xp_ganada > 0:
                xp_actual = self.contexto.pj.get("progresion", {}).get("experiencia", 0)
                if "progresion" not in self.contexto.pj:
                    self.contexto.pj["progresion"] = {}
                self.contexto.pj["progresion"]["experiencia"] = xp_actual + resultado.xp_ganada
        
        # Limpiar estado de combate
        self.gestor_combate = None
        self.orquestador_combate = None
        self.contexto.estado_combate = None
        self.contexto.cambiar_modo("exploracion")
        
        if self.debug_mode:
            print(f"[DEBUG] Combate finalizado: {'VICTORIA' if resultado.victoria else 'DERROTA'}")
        
        return {
            "narrativa": resultado.resumen_narrativo,
            "resultado_mecanico": {
                "victoria": resultado.victoria,
                "xp": resultado.xp_ganada,
                "enemigos_derrotados": resultado.enemigos_derrotados,
            },
            "herramienta_usada": "fin_combate",
            "modo": "exploracion"
        }
    
    def procesar_turno_combate(self, accion_jugador: str) -> Dict[str, Any]:
        """
        Procesa un turno durante combate táctico.
        
        El motor controla, el LLM solo narra.
        """
        if not self.en_combate_tactico():
            return {"error": "No hay combate táctico activo"}
        
        orq = self.orquestador_combate
        turno = orq.obtener_turno_actual()
        
        if not turno:
            # Combate terminó
            resultado = orq.obtener_resultado_final()
            return self._finalizar_combate_tactico(resultado)
        
        resultado_turno = {
            "narrativa": "",
            "resultado_mecanico": None,
            "herramienta_usada": None,
            "modo": "combate",
            "turno_info": {
                "combatiente": turno.combatiente_nombre,
                "ronda": turno.ronda,
                "es_jugador": turno.es_jugador,
            }
        }
        
        if turno.es_jugador:
            # Turno del jugador - procesar via pipeline
            resultado = orq.procesar_turno_jugador(accion_jugador)
            resultado_turno["narrativa"] = resultado.get("narrativa", "")
            resultado_turno["resultado_mecanico"] = resultado
            resultado_turno["necesita_clarificacion"] = resultado.get("necesita_clarificacion", False)
            resultado_turno["opciones"] = resultado.get("opciones", [])
        
        # DEBUG: Ver estado antes de verificar fin
        from .combate_integrado import EstadoCombateIntegrado
        if self.debug_mode:
            print(f"[DEBUG] Estado orq después de turno: {orq.estado}")
            print(f"[DEBUG] Resultado tipo: {resultado.get('tipo', 'N/A')}")
            enemigos_info = [(c.nombre, c.hp_actual, c.muerto) 
                            for c in self.gestor_combate.listar_combatientes() 
                            if c.tipo.value == "npc_enemigo"]
            print(f"[DEBUG] Enemigos: {enemigos_info}")
        
        # Verificar si combate terminó
        if orq.estado != EstadoCombateIntegrado.EN_CURSO:
            if self.debug_mode:
                print(f"[DEBUG] ¡Combate terminando! Estado: {orq.estado}")
            resultado_final = orq.obtener_resultado_final()
            return self._finalizar_combate_tactico(resultado_final)
        
        return resultado_turno
    
    def ejecutar_turnos_enemigos(self) -> List[Dict[str, Any]]:
        """
        Ejecuta todos los turnos de enemigos pendientes.
        
        Returns:
            Lista de resultados de turnos de enemigos
        """
        resultados = []
        
        if not self.en_combate_tactico():
            return resultados
        
        from .combate_integrado import EstadoCombateIntegrado
        orq = self.orquestador_combate
        
        while orq.estado == EstadoCombateIntegrado.EN_CURSO:
            turno = orq.obtener_turno_actual()
            if not turno or turno.es_jugador:
                break
            
            resultado = orq.ejecutar_turno_enemigo(turno.combatiente_id)
            resultados.append(resultado)
            
            if orq.estado != EstadoCombateIntegrado.EN_CURSO:
                break
        
        return resultados

    def _inferir_enemigos_de_contexto(self) -> list:
        """Infiere qué enemigos usar basándose en el historial reciente."""
        # Buscar menciones de enemigos en el historial
        historial = self.contexto.historial[-10:] if self.contexto.historial else []
        texto_historial = " ".join(str(h) for h in historial).lower()
        
        # Mapeo de palabras clave a monstruos del compendio
        mapeo_enemigos = {
            "esqueleto": "esqueleto",
            "skeleton": "esqueleto",
            "hueso": "esqueleto",
            "muerto": "esqueleto",
            "no-muerto": "esqueleto",
            "goblin": "goblin",
            "trasgo": "goblin",
            "lobo": "lobo",
            "wolf": "lobo",
            "bandido": "bandido",
            "ladrón": "bandido",
            "asaltante": "bandido",
            "orco": "orco",
            "orc": "orco",
            "sombra": "esqueleto",  # Las sombras se representan como esqueletos
        }
        
        enemigos_encontrados = []
        for palabra, monstruo in mapeo_enemigos.items():
            if palabra in texto_historial:
                if monstruo not in enemigos_encontrados:
                    enemigos_encontrados.append(monstruo)
        
        # Si encontramos enemigos, usar esos
        if enemigos_encontrados:
            # Limitar a 2-3 enemigos para un PJ solitario
            return enemigos_encontrados[:2] * 1  # Al menos 1 de cada tipo
        
        # Por defecto, usar bandidos (enemigos genéricos)
        return ["bandido", "bandido"]

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
        """
        Construye el system prompt completo para el DM.
        
        OPTIMIZACIÓN KV CACHE: El contenido está ordenado de más estático a más dinámico.
        Esto permite que LM Studio reutilice el caché de la parte estática entre turnos.
        
        Orden:
        1. ESTÁTICO: Instrucciones base del DM (nunca cambia)
        2. ESTÁTICO: Herramientas disponibles (nunca cambia)
        3. SEMI-ESTÁTICO: Adventure Bible (cambia entre actos)
        4. SEMI-ESTÁTICO: Prompt de tono (cambia si cambia aventura)
        5. DINÁMICO: Contexto actual (cambia cada turno)
        """
        partes = []
        
        # 1. ESTÁTICO: Instrucciones base del DM + Herramientas
        # Usamos un template sin {contexto} para añadirlo al final
        doc_herramientas = documentacion_herramientas()
        prompt_base = SYSTEM_PROMPT_DM.replace(
            "═══════════════════════════════════════════════════════════════════════\nCONTEXTO ACTUAL\n═══════════════════════════════════════════════════════════════════════\n{contexto}",
            ""  # Quitamos el placeholder de contexto
        ).format(herramientas=doc_herramientas)
        partes.append(prompt_base.rstrip())
        
        # 2. SEMI-ESTÁTICO: Adventure Bible (solo cambia entre actos)
        contexto_bible = self._obtener_contexto_bible()
        if contexto_bible:
            partes.append(contexto_bible)
        
        # 3. SEMI-ESTÁTICO: Prompt de tono (solo cambia si cambia el tipo de aventura)
        tipo_aventura = self.contexto.flags.get("tipo_aventura", {})
        if tipo_aventura and tipo_aventura.get("id"):
            prompt_tono = obtener_prompt_tono(tipo_aventura["id"])
            if prompt_tono:
                partes.append(prompt_tono)
        
        # 4. DINÁMICO: Contexto actual (cambia cada turno - va AL FINAL)
        contexto = self.contexto.generar_contexto_llm()
        partes.append(
            "═══════════════════════════════════════════════════════════════════════\n"
            "CONTEXTO ACTUAL (ESTADO DEL TURNO)\n"
            "═══════════════════════════════════════════════════════════════════════\n"
            f"{contexto}"
        )
        
        return "\n\n".join(partes)


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
                # Verificar si hay combate táctico o legacy activo
                if not self.en_combate_tactico() and not self.contexto.estado_combate:
                    # No hay combate activo - INICIAR AUTOMÁTICAMENTE EN MODO TÁCTICO
                    enemigos_auto = self._inferir_enemigos_de_contexto()
                    
                    if self.debug_mode:
                        print(f"[DEBUG] Auto-iniciando combate TÁCTICO con: {enemigos_auto}")
                    
                    # Ejecutar iniciar_combate
                    contexto_herramienta = self.contexto.generar_diccionario_contexto()
                    resultado_inicio = ejecutar_herramienta(
                        "iniciar_combate",
                        contexto_herramienta,
                        enemigos=enemigos_auto
                    )
                    
                    # CRÍTICO: Usar gestor_combate para modo táctico
                    if resultado_inicio.get("gestor_combate"):
                        self._iniciar_combate_tactico(resultado_inicio["gestor_combate"])
                        
                        # Mostrar info de inicio
                        orden = resultado_inicio.get("orden_iniciativa", [])
                        print(f"\n  ⚔️ ¡COMBATE TÁCTICO INICIADO!")
                        print(f"  Orden: {', '.join(orden)}")
                        print(f"  Primer turno: {resultado_inicio.get('primer_turno', '?')}")
                        print()
                        
                        # IMPORTANTE: Retornar ahora - el siguiente turno irá por el sistema táctico
                        resultado_turno["narrativa"] = "¡El combate comienza!"
                        resultado_turno["resultado_mecanico"] = {
                            k: v for k, v in resultado_inicio.items() if k != "gestor_combate"
                        }
                        resultado_turno["modo"] = "combate"
                        return resultado_turno
                    
                    # Fallback: modo legacy
                    elif resultado_inicio.get("estado_combate"):
                        self.contexto.estado_combate = resultado_inicio["estado_combate"]
                        self.contexto.cambiar_modo("combate")
                        if self.debug_mode:
                            print("[DEBUG] Usando modo combate legacy")
                    
                    # Mostrar info
                    orden = resultado_inicio.get("orden_iniciativa", [])
                    print(f"\n  ⚔️ ¡COMBATE INICIADO!")
                    print(f"  Orden: {', '.join(orden)}")
                    print()
            
            # Ejecutar herramienta
            contexto_herramienta = self.contexto.generar_diccionario_contexto()
            resultado_herramienta = ejecutar_herramienta(
                respuesta.herramienta,
                contexto_herramienta,
                **respuesta.parametros
            )
            
            resultado_turno["resultado_mecanico"] = resultado_herramienta
            self.ultimo_resultado_herramienta = resultado_herramienta
            
            # NUEVO: Si es iniciar_combate con gestor_combate, iniciar modo táctico
            if respuesta.herramienta == "iniciar_combate":
                if resultado_herramienta.get("gestor_combate"):
                    # Modo táctico con GestorCombate real
                    self._iniciar_combate_tactico(resultado_herramienta["gestor_combate"])
                    if self.debug_mode:
                        print("[DEBUG] Modo táctico activado con GestorCombate")
                    
                    # Retornar inmediatamente - siguiente input irá por sistema táctico
                    resultado_turno["narrativa"] = respuesta.narrativa or "¡El combate comienza!"
                    resultado_turno["resultado_mecanico"] = {
                        k: v for k, v in resultado_herramienta.items() if k != "gestor_combate"
                    }
                    resultado_turno["modo"] = "combate"
                    return resultado_turno
                    
                elif resultado_herramienta.get("estado_combate"):
                    # Fallback: modo legacy con dict básico
                    self.contexto.estado_combate = resultado_herramienta["estado_combate"]
                    if self.debug_mode:
                        print("[DEBUG] estado_combate guardado (modo legacy)")
            
            if self.debug_mode:
                print(f"\n[DEBUG] Tool result: {resultado_herramienta}")
            
            # Filtrar objetos no serializables para el log y el LLM
            resultado_serializable = {
                k: v for k, v in resultado_herramienta.items()
                if k not in ("gestor_combate",)  # Excluir objetos no serializables
            }
            
            # Registrar resultado mecánico
            self.contexto.registrar_historial(
                "resultado_mecanico",
                f"{respuesta.herramienta}: {json.dumps(resultado_serializable, ensure_ascii=False)}"
            )
            
            # Segunda llamada al LLM para narrar el resultado
            mensaje_resultado = f"""El jugador dijo: "{accion_jugador}"

Usaste la herramienta '{respuesta.herramienta}' y obtuviste este resultado:
{json.dumps(resultado_serializable, indent=2, ensure_ascii=False)}

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
