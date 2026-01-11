"""
Prompts especializados para generar Adventure Bibles.

El LLM genera una biblia estructurada basándose en:
- Tipo de aventura (tono)
- Información del PJ
- Región de Faerûn
"""

PROMPT_GENERAR_BIBLE = """Eres un diseñador de aventuras de D&D 5e experto en Reinos Olvidados.

Tu tarea es crear una ADVENTURE BIBLE: un documento estructurado que define todos los elementos de una aventura ANTES de jugarla.

═══════════════════════════════════════════════════════════════════════
INFORMACIÓN DEL PERSONAJE JUGADOR
═══════════════════════════════════════════════════════════════════════
{info_pj}

═══════════════════════════════════════════════════════════════════════
TIPO DE AVENTURA: {tipo_aventura}
═══════════════════════════════════════════════════════════════════════
{descripcion_tono}

═══════════════════════════════════════════════════════════════════════
REGIÓN DE FAERÛN
═══════════════════════════════════════════════════════════════════════
{region}

═══════════════════════════════════════════════════════════════════════
INSTRUCCIONES DE GENERACIÓN
═══════════════════════════════════════════════════════════════════════

Genera una Adventure Bible en JSON con EXACTAMENTE esta estructura:

{{
  "logline": "Resumen en 1-2 frases (máx 200 caracteres)",
  
  "main_quest": {{
    "objetivo_final": "Qué debe lograr el PJ",
    "por_que_importa": "Stakes - qué pasa si falla",
    "gancho_inicial": "Cómo se presenta al PJ (NO requiere tirada)"
  }},
  
  "antagonista": {{
    "identidad_real": "Nombre real del villano",
    "fachada": "Cómo se presenta públicamente (si aplica)",
    "motivacion": "Por qué hace lo que hace",
    "objetivo": "Qué quiere lograr",
    "recursos": ["recurso1", "recurso2", "recurso3"],
    "debilidad": "Cómo puede ser derrotado",
    "pistas_foreshadowing": ["pista1", "pista2", "pista3", "pista4"]
  }},
  
  "actos": [
    {{
      "numero": 1,
      "nombre": "Nombre del acto",
      "objetivo": "Qué debe lograr el PJ en este acto",
      "escenas_semilla": [
        {{"id": "escena_1", "tipo": "social/combate/exploracion", "descripcion": "Breve descripción"}},
        {{"id": "escena_2", "tipo": "social/combate/exploracion", "descripcion": "Breve descripción"}},
        {{"id": "escena_3", "tipo": "social/combate/exploracion", "descripcion": "Breve descripción"}}
      ],
      "climax": "Cómo termina el acto"
    }},
    {{
      "numero": 2,
      "nombre": "Nombre del acto 2",
      "objetivo": "...",
      "escenas_semilla": [...],
      "climax": "..."
    }},
    {{
      "numero": 3,
      "nombre": "Nombre del acto 3",
      "objetivo": "...",
      "escenas_semilla": [...],
      "climax": "..."
    }}
  ],
  
  "revelaciones": [
    {{
      "id": "rev_1",
      "contenido": "Qué se revela",
      "importancia": "critica/importante/menor",
      "acto": 1,
      "pistas": [
        {{"id": "p1_social", "tipo": "social", "descripcion": "Pista obtenida hablando", "garantizada": false}},
        {{"id": "p1_fisica", "tipo": "fisica", "descripcion": "Pista física encontrada", "garantizada": true}},
        {{"id": "p1_documental", "tipo": "documental", "descripcion": "Pista en documentos", "garantizada": false}}
      ]
    }}
  ],
  
  "pnj_clave": [
    {{
      "nombre": "Nombre fantástico",
      "rol": "Aliado/Enemigo/Neutral/Informante",
      "descripcion_breve": "Descripción física y personalidad en 1 frase",
      "secreto": "Algo que oculta",
      "actitud_inicial": "amistoso/neutral/desconfiado/hostil",
      "ubicacion": "Dónde encontrarlo"
    }}
  ],
  
  "relojes": [
    {{
      "nombre": "Nombre del reloj",
      "descripcion": "Qué representa",
      "segmentos_total": 6,
      "que_avanza": "Qué hace que avance",
      "que_pasa_al_completar": "Consecuencia"
    }}
  ],
  
  "side_quests": [
    {{
      "id": "sq_1",
      "gancho": "Cómo se presenta",
      "que_revela": "Información útil que da",
      "como_escala": "Cómo puede volverse importante",
      "potencial_main": true/false,
      "recompensa": "Qué obtiene el PJ"
    }}
  ],
  
  "recompensas_previstas": [
    {{"que": "Objeto o cantidad de oro", "cuando": "En qué momento"}}
  ]
}}

═══════════════════════════════════════════════════════════════════════
REGLAS DE DISEÑO
═══════════════════════════════════════════════════════════════════════

1. PARTIDA EN SOLITARIO (1 PJ nivel {nivel_pj}):
   - Un solo PJ, NO un grupo
   - Los encuentros deben ser navegables por 1 personaje
   
   REGLAS DE DIFICULTAD DE ENCUENTROS:
   Para un PJ de nivel {nivel_pj}, los umbrales son:
   - Encuentro FÁCIL: CR {cr_facil} (1 enemigo) o 2 de CR {cr_facil_2}
   - Encuentro MEDIO: CR {cr_medio} (1 enemigo)
   - Encuentro DIFÍCIL: CR {nivel_pj} (1 enemigo)
   - Encuentro LETAL: CR {cr_letal} o 2+ enemigos de CR {cr_medio}
   
   ⚠️ IMPORTANTE: Para 1 PJ, 3+ enemigos SIEMPRE es encuentro MORTAL.
   
   Ejemplos de monstruos apropiados para nivel {nivel_pj}:
   - CR 0: Commoner, Rat, Goat
   - CR 1/8: Bandit, Cultist, Kobold
   - CR 1/4: Goblin, Esqueleto, Zombi
   - CR 1/2: Orc, Hobgoblin, Scout
   - CR 1: Bugbear, Ghoul, Specter
   - CR 2: Ogre, Ghast, Mimic
   - CR 3: Werewolf, Owlbear, Manticore
   
   Regla general: usa 1 enemigo de CR = nivel_pj - 1 para encuentro medio.

2. THREE CLUE RULE:
   - Cada revelación CRÍTICA tiene exactamente 3 pistas
   - Una pista es GARANTIZADA (se entrega sin tirada)
   - Las otras 2 requieren tiradas o acciones específicas

3. NUNCA BLOQUEAR:
   - El gancho inicial NO requiere tirada
   - Los fallos generan complicaciones, no bloqueos
   - Siempre hay alternativas

4. FORESHADOWING:
   - El antagonista tiene 4 pistas de foreshadowing
   - Estas pistas se siembran ANTES de revelar su identidad
   - La identidad se revela en el acto 3 normalmente

5. NOMBRES:
   - Usa nombres fantásticos de Reinos Olvidados
   - Nada de nombres modernos (Juan, María, etc.)
   - Ejemplos: Vaelindra Tormenta, Aldric Sombrafría, Grimjaw el Tuerto

6. COHERENCIA:
   - Todo debe encajar en la región de Faerûn especificada
   - Los NPCs tienen motivaciones lógicas
   - El antagonista tiene razones creíbles

7. ESTRUCTURA:
   - Exactamente 3 actos
   - 2-4 escenas semilla por acto
   - 2-4 NPCs clave
   - 1-2 relojes de tensión
   - 1-2 side quests
   - 2-4 revelaciones (al menos 1 crítica)

═══════════════════════════════════════════════════════════════════════
RESPONDE SOLO CON EL JSON
═══════════════════════════════════════════════════════════════════════
No añadas explicaciones antes ni después. Solo el JSON válido.
"""


def generar_prompt_bible(pj: dict, tipo_aventura: dict, region: str = "Costa de la Espada") -> str:
    """
    Genera el prompt para crear una Adventure Bible.
    
    Args:
        pj: Diccionario del personaje jugador
        tipo_aventura: Diccionario del tono de aventura
        region: Región de Faerûn donde se desarrolla
    
    Returns:
        Prompt completo para el LLM
    """
    # Extraer info del PJ
    info_basica = pj.get("info_basica", {})
    nombre_pj = info_basica.get("nombre", "Aventurero")
    clase = info_basica.get("clase", "Guerrero")
    raza = info_basica.get("raza", "Humano")
    nivel = info_basica.get("nivel", 1)
    trasfondo = info_basica.get("trasfondo", "Soldado")
    
    # Construir descripción del PJ
    info_pj = f"""Nombre: {nombre_pj}
Raza: {raza}
Clase: {clase}
Nivel: {nivel}
Trasfondo: {trasfondo}"""
    
    # Añadir rasgos si existen
    personalidad = pj.get("personalidad", {})
    if personalidad:
        if personalidad.get("rasgos"):
            info_pj += f"\nRasgos: {', '.join(personalidad['rasgos'][:2])}"
        if personalidad.get("ideales"):
            info_pj += f"\nIdeales: {', '.join(personalidad['ideales'][:1])}"
        if personalidad.get("vinculos"):
            info_pj += f"\nVínculos: {', '.join(personalidad['vinculos'][:1])}"
    
    # Descripción del tono
    descripcion_tono = f"""Estilo: {tipo_aventura.get('nombre', 'Épica Heroica')}
{tipo_aventura.get('descripcion_corta', '')}

Tono narrativo: {tipo_aventura.get('tono_narrativo', 'Heroico')}

Letalidad: {tipo_aventura.get('letalidad', 'media')}
Moral: {tipo_aventura.get('moral', 'clara')}

Cómo resolver fallos: {tipo_aventura.get('como_resolver_fallos', 'Los fallos generan complicaciones pero la historia avanza.')}

Tipos de antagonista típicos:
{chr(10).join('- ' + a for a in tipo_aventura.get('tipos_antagonista', ['Villano genérico'])[:3])}

Tipos de quest típicos:
{chr(10).join('- ' + q for q in tipo_aventura.get('tipos_quest', ['Misión genérica'])[:3])}"""
    
    # Construir prompt final
    # Pre-calcular valores de CR para el template
    prompt = PROMPT_GENERAR_BIBLE.format(
        info_pj=info_pj,
        tipo_aventura=tipo_aventura.get('nombre', 'Épica Heroica'),
        descripcion_tono=descripcion_tono,
        region=region,
        nivel_pj=nivel,
        cr_facil=max(0, nivel - 2),
        cr_facil_2=max(0, nivel - 3),
        cr_medio=max(0, nivel - 1),
        cr_letal=nivel + 1,
    )
    
    return prompt


REGIONES_FAERUN = {
    "costa_espada": {
        "nombre": "Costa de la Espada",
        "descripcion": "La región más cosmopolita de Faerûn. Incluye Aguas Profundas, Neverwinter, Puerta de Baldur y Luskan.",
        "ciudades": ["Aguas Profundas", "Neverwinter", "Puerta de Baldur", "Luskan", "Mirabar"],
        "facciones": ["Lords de Aguas Profundas", "Arpistas", "Zhentarim", "Enclave Esmeralda"],
        "amenazas_tipicas": ["Piratas", "Zhentarim", "Cultos demoníacos", "Dragones"]
    },
    "el_norte": {
        "nombre": "El Norte Salvaje",
        "descripcion": "Tierras heladas y peligrosas. Diez Ciudades, Valle del Viento Helado, Mithral Hall.",
        "ciudades": ["Diez Ciudades", "Mithral Hall", "Lonelywood", "Bryn Shander"],
        "facciones": ["Bárbaros Uthgardt", "Enanos de Mithral Hall", "Reghed"],
        "amenazas_tipicas": ["Gigantes de escarcha", "Orcos", "Dragones blancos", "El frío"]
    },
    "cormyr": {
        "nombre": "Cormyr",
        "descripcion": "El reino del Dragón Púrpura. Tierra de caballeros, nobles y política.",
        "ciudades": ["Suzail", "Marsember", "Arabel", "Tilverton"],
        "facciones": ["Corona de Cormyr", "Caballeros Púrpura", "Magos de Guerra"],
        "amenazas_tipicas": ["Intrigas nobles", "Shadovar", "Monstruos del Bosque Hullack"]
    },
    "tierras_valles": {
        "nombre": "Tierras de los Valles",
        "descripcion": "Valles semi-independientes entre grandes poderes. Tierra de aventureros.",
        "ciudades": ["Arroyo de la Sombra", "Valle de la Daga", "Tantras"],
        "facciones": ["Arpistas", "Zhentarim", "Culto del Dragón"],
        "amenazas_tipicas": ["Zhentarim", "Drow", "Culto del Dragón", "Bandidos"]
    },
    "calimshan": {
        "nombre": "Calimshan",
        "descripcion": "Tierras del sur, influencia árabe/persa. Genios, mercaderes, intrigas.",
        "ciudades": ["Calimport", "Memnon", "Almraiven"],
        "facciones": ["Pashas mercantes", "Gremios de ladrones", "Vinculadores de genios"],
        "amenazas_tipicas": ["Genios malignos", "Esclavistas", "Asesinos", "Política de pashas"]
    }
}


def obtener_info_region(region_id: str) -> dict:
    """Obtiene información de una región de Faerûn."""
    return REGIONES_FAERUN.get(region_id, REGIONES_FAERUN["costa_espada"])


def listar_regiones() -> list:
    """Lista todas las regiones disponibles."""
    return [
        {"id": k, "nombre": v["nombre"], "descripcion": v["descripcion"]}
        for k, v in REGIONES_FAERUN.items()
    ]
