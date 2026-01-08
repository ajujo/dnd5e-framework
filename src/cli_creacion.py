#!/usr/bin/env python3
"""
CLI interactivo para creación de personajes D&D 5e.

Uso:
    python src/cli_creacion.py [--llm] [--continuar ID]
    
Flags:
    --llm       Usa LLM para sugerencias y explicaciones
    --continuar Continúa una creación en progreso
"""

from __future__ import annotations

import sys
import argparse
import random
from typing import Optional, Callable, List

# Añadir src al path
sys.path.insert(0, "src")

from personaje import (
    listar_razas,
    listar_clases,
    listar_trasfondos,
    obtener_raza,
    obtener_clase,
    obtener_trasfondo,
    STANDARD_ARRAY,
    CARACTERISTICAS,
    save_character,
    load_autosave,
    list_autosaves,
    recalcular_derivados,
    generar_resumen_derivados,
)
from personaje.creador import (
    CreadorPersonaje,
    PasoCreacion,
    cargar_creador_desde_autosave,
)
from personaje.compendio_pj import obtener_personalidad_trasfondo
def normalizar_texto(texto: str) -> str:
    """Normaliza texto para comparación (minúsculas, sin acentos)."""
    import unicodedata
    texto = texto.lower().strip()
    # Quitar acentos
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto


def buscar_opcion_por_texto(texto: str, opciones: List[dict]) -> Optional[int]:
    """
    Busca una opción por texto (nombre o id).
    
    Returns:
        Índice (1-based) de la opción encontrada, o None
    """
    texto_norm = normalizar_texto(texto)
    
    for i, op in enumerate(opciones, 1):
        # Comparar con id
        if normalizar_texto(op.get("id", "")) == texto_norm:
            return i
        # Comparar con nombre
        if normalizar_texto(op.get("nombre", "")) == texto_norm:
            return i
        # Comparar parcial (ej: "humano" matchea "Humano")
        nombre_norm = normalizar_texto(op.get("nombre", ""))
        if texto_norm in nombre_norm or nombre_norm.startswith(texto_norm):
            return i
    
    return None




# Prompt del LLM para creación
SYSTEM_PROMPT_CREACION = """Eres un Dungeon Master amigable ayudando a crear un personaje de D&D 5e NIVEL 1.

REGLAS CRÍTICAS (OBLIGATORIAS):
- Solo menciona razas, clases y trasfondos de las listas que te proporcione el usuario
- NO inventes opciones como "Humano Variante", "Drow", "Tiefling" u otras que no estén en la lista
- NO menciones subclases (el personaje es nivel 1, no tiene subclase aún)
- NO menciones multiclase (está fuera del alcance de este creador)
- NO sugieras combinaciones de clases como "Guerrero/Pícaro"
- NO menciones clases que no estén en la lista (como Ranger, Paladín, Bárbaro, etc.)

TU ROL:
- Explicar opciones de forma clara y breve
- Sugerir nombres y detalles narrativos
- Responder en 2-3 frases máximo, no párrafos largos
- Ayudar a imaginar el concepto del personaje

PROHIBICIONES ADICIONALES:
- NO uses formato markdown (nada de ** ni _ ni #)
- NO uses nombres en inglés (usa Semiorco, no Half-Orc)
- NO des listas numeradas de opciones narrativas
- NO escribas más de 3-4 frases por respuesta

ESTILO:
- Breve y evocador
- Texto plano sin formato
- Una idea concreta, no múltiples opciones elaboradas
"""


# Alineamientos disponibles
ALINEAMIENTOS = [
    {"id": "legal_bueno", "nombre": "Legal Bueno", "descripcion": "Actúa con compasión y honor, respetando las leyes."},
    {"id": "neutral_bueno", "nombre": "Neutral Bueno", "descripcion": "Hace el bien sin preocuparse por reglas o caos."},
    {"id": "caotico_bueno", "nombre": "Caótico Bueno", "descripcion": "Actúa según su conciencia, sin importar las normas."},
    {"id": "legal_neutral", "nombre": "Legal Neutral", "descripcion": "Sigue las leyes y tradiciones sin inclinarse al bien o mal."},
    {"id": "neutral", "nombre": "Neutral", "descripcion": "Actúa naturalmente, sin inclinarse a ningún extremo."},
    {"id": "caotico_neutral", "nombre": "Caótico Neutral", "descripcion": "Sigue sus impulsos, valorando su libertad sobre todo."},
    {"id": "legal_malvado", "nombre": "Legal Malvado", "descripcion": "Usa las leyes para conseguir lo que quiere sin piedad."},
    {"id": "neutral_malvado", "nombre": "Neutral Malvado", "descripcion": "Hace lo que sea necesario para sus propios fines."},
    {"id": "caotico_malvado", "nombre": "Caótico Malvado", "descripcion": "Actúa con violencia arbitraria, sin respeto por nada."},
]



# LLM callback global
_llm_callback: Optional[Callable[[str, str], str]] = None



def formatear_ca_detalle(pj: dict) -> str:
    """
    Formatea la CA con desglose numérico.
    
    Ejemplo: "18 (16 armadura + 2 escudo)" o "15 (11 armadura + 3 DES + 1 Defensa)"
    """
    from personaje.calculador import ARMADURAS, ESCUDO_CA
    
    derivados = pj.get("derivados", {})
    equipo = pj.get("equipo", {})
    rasgos = pj.get("rasgos", {})
    mods = derivados.get("modificadores", {})
    
    ca = derivados.get("clase_armadura", 10)
    armadura = equipo.get("armadura")
    escudo = equipo.get("escudo")
    
    ca_partes = []
    
    if armadura and armadura.get("equipada"):
        ref = armadura.get("compendio_ref", "sin_armadura")
        
        # Quitar sufijo numérico si existe (ej: "cota_mallas_pesada_1" -> "cota_mallas_pesada")
        if ref not in ARMADURAS and ref[-1].isdigit():
            ref_base = "_".join(ref.split("_")[:-1])
            if ref_base in ARMADURAS:
                ref = ref_base
        
        arm_data = ARMADURAS.get(ref, ARMADURAS.get("sin_armadura", {}))
        ca_base = arm_data.get("ca_base", 10)
        ca_partes.append(f"{ca_base} armadura")
        
        # Añadir DES si aplica
        if arm_data.get("mod_des"):
            mod_des = mods.get("destreza", 0)
            max_des = arm_data.get("max_des")
            if max_des is not None:
                mod_des = min(mod_des, max_des)
            if mod_des != 0:
                ca_partes.append(f"{mod_des:+d} DES".replace("+", ""))
    else:
        # Sin armadura
        ca_partes.append("10 base")
        mod_des = mods.get("destreza", 0)
        if mod_des != 0:
            ca_partes.append(f"{mod_des} DES")
    
    if escudo and escudo.get("equipada"):
        ca_partes.append(f"{ESCUDO_CA} escudo")
    
    # Estilo Defensa
    for r in rasgos.get("clase", []):
        if r.get("id") == "estilo_combate" and r.get("opcion") == "defensa":
            ca_partes.append("1 Defensa")
    
    if ca_partes:
        return f"{ca} ({' + '.join(ca_partes)})"
    return str(ca)


def configurar_llm():
    """Configura el callback del LLM si está disponible."""
    global _llm_callback
    
    try:
        from motor.llm_adapter import crear_cliente_llm, crear_callback_narrador
        
        print("🔍 Buscando LLM local...")
        cliente = crear_cliente_llm()
        
        if cliente:
            info = cliente.obtener_info()
            print(f"✓ {info.get('tipo', 'LLM')} conectado")
            print(f"  Modelo: {info.get('modelo', 'desconocido')}")
            
            # Crear callback personalizado para creación
            def callback_creacion(prompt: str) -> str:
                return cliente.generar(prompt, system=SYSTEM_PROMPT_CREACION)
            
            _llm_callback = callback_creacion
            return True
        else:
            print("⚠️  No se encontró LLM. Modo básico activado.")
            return False
            
    except ImportError:
        print("⚠️  Módulo LLM no disponible. Modo básico activado.")
        return False


def limpiar_pantalla():
    """Limpia la pantalla."""
    print("\n" * 2)


def mostrar_titulo(titulo: str):
    """Muestra un título decorado."""
    print()
    print("═" * 60)
    print(f"  {titulo}")
    print("═" * 60)
    print()


def mostrar_opciones(opciones: List[dict], mostrar_desc: bool = True, mostrar_bonificadores: bool = False):
    """Muestra una lista numerada de opciones con espaciado."""
    for i, op in enumerate(opciones, 1):
        nombre = op.get("nombre", op.get("id", "?"))
        
        # Añadir bonificadores si se pide (para razas)
        extra = ""
        if mostrar_bonificadores:
            bons = op.get("bonificadores", {})
            if bons:
                partes = [f"{k.upper()[:3]}+{v}" for k, v in bons.items()]
                extra = f" [{', '.join(partes)}]"
        
        print(f"  {i}. {nombre}{extra}")
        
        if mostrar_desc and op.get("descripcion"):
            desc = op["descripcion"]
            if len(desc) <= 75:
                print(f"     {desc}")
            else:
                palabras = desc.split()
                linea = "     "
                for palabra in palabras:
                    if len(linea) + len(palabra) > 80:
                        print(linea)
                        linea = "     " + palabra + " "
                    else:
                        linea += palabra + " "
                if linea.strip():
                    print(linea)
        print()  # Línea en blanco entre opciones


def pedir_opcion(prompt: str, max_opcion: int, permitir_cero: bool = False) -> int:
    """Pide al usuario que elija una opción numérica."""
    while True:
        try:
            entrada = input(f"{prompt} ").strip()
            
            # Comandos especiales
            if entrada.lower() in ["/salir", "/exit", "/q"]:
                return -1
            if entrada.lower() in ["/atras", "/back", "/b"]:
                return -2
            
            num = int(entrada)
            min_val = 0 if permitir_cero else 1
            if min_val <= num <= max_opcion:
                return num
            print(f"  Por favor, elige entre {min_val} y {max_opcion}")
        except ValueError:
            print("  Introduce un número válido")


def pedir_texto(prompt: str, obligatorio: bool = True) -> Optional[str]:
    """Pide texto al usuario."""
    while True:
        entrada = input(f"{prompt} ").strip()
        
        if entrada.lower() in ["/salir", "/exit", "/q"]:
            return None
        if entrada.lower() in ["/atras", "/back", "/b"]:
            return "__ATRAS__"
        
        if entrada or not obligatorio:
            return entrada
        
        print("  Este campo es obligatorio")


def consultar_llm(prompt: str) -> Optional[str]:
    """Consulta al LLM si está disponible."""
    if _llm_callback:
        try:
            return _llm_callback(prompt)
        except Exception as e:
            print(f"  (Error LLM: {e})")
    return None

def mostrar_ficha_completa(pj: dict):
    """Muestra la ficha completa de un personaje."""
    info = pj.get("info_basica", {})
    car = pj.get("caracteristicas", {})
    derivados = pj.get("derivados", {})
    competencias = pj.get("competencias", {})
    personalidad = pj.get("personalidad", {})
    historia = pj.get("historia", {})
    equipo = pj.get("equipo", {})
    rasgos = pj.get("rasgos", {})
    
    raza_data = obtener_raza(info.get("raza", ""))
    clase_data = obtener_clase(info.get("clase", ""))
    trasf_data = obtener_trasfondo(info.get("trasfondo", ""))
    
    mostrar_titulo(f"FICHA: {info.get('nombre', 'Sin nombre')}")
    
    # Info básica
    print(f"  Raza: {raza_data['nombre'] if raza_data else info.get('raza', '?')}")
    print(f"  Clase: {clase_data['nombre'] if clase_data else info.get('clase', '?')} Nivel {info.get('nivel', 1)}")
    print(f"  Trasfondo: {trasf_data['nombre'] if trasf_data else info.get('trasfondo', '?')}")
    print(f"  Alineamiento: {info.get('alineamiento', 'No definido')}")
    print()
    
    # Características
    print("  CARACTERÍSTICAS:")
    mods = derivados.get("modificadores", {})
    for c in ["fuerza", "destreza", "constitucion", "inteligencia", "sabiduria", "carisma"]:
        val = car.get(c, 10)
        mod = mods.get(c, 0)
        print(f"    {c.upper()[:3]}: {val:2d} ({mod:+d})")
    print()
    
    # Combate
    print("  COMBATE:")
    print(f"    HP: {derivados.get('puntos_golpe_actual', 0)}/{derivados.get('puntos_golpe_maximo', 0)}")
    
    # CA desglosada con números (usando helper)
    print(f"    CA: {formatear_ca_detalle(pj)}")
    
    print(f"    Velocidad: {derivados.get('velocidad', 30)} pies")
    print(f"    Iniciativa: {derivados.get('iniciativa', 0):+d}")
    print(f"    Dado de golpe: {derivados.get('dado_golpe', 'd8')}")
    
    # Bonificadores de ataque
    bon_comp = derivados.get('bonificador_competencia', 2)
    mod_fue = mods.get('fuerza', 0)
    mod_des = mods.get('destreza', 0)
    
    ataque_cac = mod_fue + bon_comp
    ataque_dist = mod_des + bon_comp
    
    print()
    print(f"    Ataque cuerpo a cuerpo: {ataque_cac:+d} (FUE {mod_fue:+d} + competencia +{bon_comp})")
    print(f"    Ataque a distancia: {ataque_dist:+d} (DES {mod_des:+d} + competencia +{bon_comp})")
    
    # Nota sobre armas sutiles
    if mod_des > mod_fue:
        print(f"    (Armas sutiles/distancia pueden usar DES: {ataque_dist:+d})")
    
    # Mostrar bonificadores de daño por estilos de combate
    for r in rasgos.get("clase", []):
        if r.get("id") == "estilo_combate":
            estilo = r.get("opcion", "")
            if estilo == "duelo":
                print(f"    Daño CaC (1 mano): +{mod_fue} FUE +2 Duelo = +{mod_fue + 2}")
            elif estilo == "armas_grandes":
                print(f"    Daño (2 manos): Repetir 1s y 2s en dados de daño")
            elif estilo == "combate_dos_armas":
                print(f"    Segundo ataque: Añade mod FUE al daño")
    print()
    
    # Salvaciones (con desglose)
    print("  TIRADAS DE SALVACIÓN:")
    salvaciones = derivados.get("salvaciones", {})
    competentes = competencias.get("salvaciones", [])
    bon_comp = derivados.get('bonificador_competencia', 2)
    
    for c in ["fuerza", "destreza", "constitucion", "inteligencia", "sabiduria", "carisma"]:
        val = salvaciones.get(c, 0)
        mod = mods.get(c, 0)
        es_competente = c in competentes
        marca = "●" if es_competente else "○"
        
        if es_competente:
            detalle = f"(mod {mod:+d} + comp +{bon_comp})"
        else:
            detalle = f"(mod {mod:+d})"
        
        print(f"    {marca} {c.upper()[:3]}: {val:+d} {detalle}")
    print()
    
    # Habilidades
    habilidades = competencias.get("habilidades", [])
    if habilidades:
        print(f"  HABILIDADES: {', '.join(h.replace('_', ' ').title() for h in habilidades)}")
        print()
    
    # Idiomas
    idiomas = competencias.get("idiomas", [])
    if idiomas:
        print(f"  IDIOMAS: {', '.join(i.title() for i in idiomas)}")
        print()
    
    # Rasgos
    rasgos_raciales = rasgos.get("raciales", [])
    rasgos_clase = rasgos.get("clase", [])
    if rasgos_raciales or rasgos_clase:
        print("  RASGOS:")
        for r in rasgos_raciales:
            print(f"    • {r.get('nombre', r.get('id', '?'))}")
        for r in rasgos_clase:
            nombre = r.get('nombre', r.get('id', '?'))
            if r.get('opcion'):
                nombre += f" ({r['opcion'].replace('_', ' ').title()})"
            print(f"    • {nombre}")
        print()
    
    # Equipo
    armas = equipo.get("armas", [])
    armadura = equipo.get("armadura")
    escudo = equipo.get("escudo")
    if armas or armadura or escudo:
        print("  EQUIPO:")
        for arma in armas:
            eq = "⚔️" if arma.get("equipada") else "  "
            print(f"    {eq} {arma.get('nombre', '?')}")
        if armadura:
            print(f"    🛡️ {armadura.get('nombre', '?')}")
        if escudo:
            print(f"    🛡️ {escudo.get('nombre', '?')}")
        print()
    
    # Personalidad
    if any(personalidad.values()):
        print("  PERSONALIDAD:")
        if personalidad.get("rasgos"):
            print(f"    Rasgo: {personalidad['rasgos'][0]}")
        if personalidad.get("ideales"):
            print(f"    Ideal: {personalidad['ideales'][0]}")
        if personalidad.get("vinculos"):
            print(f"    Vínculo: {personalidad['vinculos'][0]}")
        if personalidad.get("defectos"):
            print(f"    Defecto: {personalidad['defectos'][0]}")
        print()
    
    # Descripción física
    if any(historia.values()):
        print("  DESCRIPCIÓN:")
        if historia.get("edad"):
            print(f"    Edad: {historia['edad']}")
        if historia.get("ojos"):
            print(f"    Ojos: {historia['ojos']}")
        if historia.get("cabello"):
            print(f"    Cabello: {historia['cabello']}")
        if historia.get("piel"):
            print(f"    Piel: {historia['piel']}")
        if historia.get("altura"):
            print(f"    Altura: {historia['altura']}")
        if historia.get("peso"):
            print(f"    Peso: {historia['peso']}")
        print()
    
    # Historia
    backstory = historia.get("backstory", "")
    if backstory:
        print("  HISTORIA:")
        # Dividir en líneas de ~70 caracteres
        palabras = backstory.split()
        linea = "    "
        for palabra in palabras:
            if len(linea) + len(palabra) > 75:
                print(linea)
                linea = "    " + palabra + " "
            else:
                linea += palabra + " "
        if linea.strip():
            print(linea)
        print()





# =============================================================================
# PASOS DE CREACIÓN
# =============================================================================

def paso_concepto(creador: CreadorPersonaje) -> bool:
    """Paso 1: Concepto del personaje."""
    mostrar_titulo("PASO 1: CONCEPTO DEL PERSONAJE")
    
    if _llm_callback:
        print("🎭 DM: ¡Bienvenido, futuro héroe! Antes de empezar con los números,")
        print("   cuéntame: ¿qué tipo de aventurero imaginas?")
        print()
        print("   Puede ser algo como:")
        print("   - Un guerrero noble caído en desgracia")
        print("   - Una maga elfa obsesionada con los secretos arcanos")
        print("   - Un pícaro mediano con corazón de oro")
        print()
    else:
        print("Describe brevemente el concepto de tu personaje.")
        print("(Esto es opcional, puedes dejarlo en blanco)")
        print()
    
    concepto = pedir_texto("Tu concepto (o Enter para saltar):", obligatorio=False)
    
    if concepto == "__ATRAS__":
        return False
    if concepto is None:
        return False
    
    if concepto:
        creador.establecer_concepto(concepto)
        
        # Respuesta del LLM
        if _llm_callback and concepto:
            # Pasar listas disponibles al LLM
            razas_disponibles = ", ".join([r["nombre"] for r in listar_razas()])
            clases_disponibles = ", ".join([c["nombre"] for c in listar_clases()])
            
            respuesta = consultar_llm(
                f"El jugador quiere crear: '{concepto}'. "
                f"RAZAS DISPONIBLES: {razas_disponibles}. "
                f"CLASES DISPONIBLES: {clases_disponibles}. "
                f"En 2-3 frases, comenta qué razas y clases de estas listas podrían encajar bien con ese concepto."
            )
            if respuesta:
                print()
                print(f"🎭 DM: {respuesta}")
                print()
    
    return True


def paso_raza(creador: CreadorPersonaje) -> bool:
    """Paso 2: Elección de raza."""
    mostrar_titulo("PASO 2: ELIGE TU RAZA")
    
    razas = listar_razas()
    
    if _llm_callback:
        print("🎭 DM: La raza define tus habilidades innatas y tu herencia.")
        print("   Cada una tiene bonificadores y rasgos únicos.")
        print()
    
    # Añadir bonificadores a cada raza para mostrar
    razas_con_bonus = []
    for r in razas:
        raza_data = obtener_raza(r["id"])
        r_copia = r.copy()
        if raza_data:
            r_copia["bonificadores"] = raza_data.get("bonificadores", {})
        razas_con_bonus.append(r_copia)
    
    mostrar_opciones(razas_con_bonus, mostrar_bonificadores=True)
    
    print("  0. Más información sobre una raza")
    print()
    
    while True:
        opcion = pedir_opcion(f"Elige raza (1-{len(razas)}, 0 para info):", len(razas), permitir_cero=True)
        
        if opcion == -1:  # Salir
            return False
        if opcion == -2:  # Atrás
            return False
        
        if opcion == 0:
            # Pedir info de una raza (acepta número o nombre)
            entrada = pedir_texto("¿De cuál quieres saber más? (número o nombre):")
            if entrada is None or entrada == "__ATRAS__":
                continue
            
            # Intentar como número
            info_num = None
            if entrada.isdigit():
                num = int(entrada)
                if 1 <= num <= len(razas):
                    info_num = num
            else:
                # Buscar por texto
                info_num = buscar_opcion_por_texto(entrada, razas)
            
            if info_num:
                raza_info = razas[info_num - 1]
                raza_data = obtener_raza(raza_info["id"])
                if raza_data:
                    print()
                    print(f"  📜 {raza_data['nombre']}")
                    print(f"     {raza_data.get('descripcion', '')}")
                    print()
                    print(f"     Bonificadores: ", end="")
                    bons = raza_data.get("bonificadores", {})
                    print(", ".join(f"{k.upper()[:3]}+{v}" for k, v in bons.items()))
                    print(f"     Velocidad: {raza_data.get('velocidad', 30)} pies")
                    
                    rasgos = raza_data.get("rasgos", [])
                    if rasgos:
                        print(f"     Rasgos: {', '.join(r['nombre'] for r in rasgos)}")
                    print()
            continue
        
        # Selección válida
        raza_elegida = razas[opcion - 1]
        if creador.establecer_raza(raza_elegida["id"]):
            raza_data = obtener_raza(raza_elegida["id"])
            print(f"\n  ✓ Has elegido: {raza_data['nombre']}")
            
            if _llm_callback:
                respuesta = consultar_llm(
                    f"El jugador ha elegido la raza '{raza_data['nombre']}'. "
                    f"En 1-2 frases, comenta algo interesante sobre esta raza y qué clases le van bien."
                )
                if respuesta:
                    print(f"\n🎭 DM: {respuesta}")
            
            print()
            return True
        else:
            print("  Error al establecer la raza")


def paso_clase(creador: CreadorPersonaje) -> bool:
    """Paso 3: Elección de clase."""
    mostrar_titulo("PASO 3: ELIGE TU CLASE")
    
    clases = listar_clases()
    
    if _llm_callback:
        print("🎭 DM: La clase define tus habilidades de combate y tu rol en el grupo.")
        print()
    
    mostrar_opciones(clases)
    
    print("  0. Más información sobre una clase")
    print()
    
    while True:
        opcion = pedir_opcion(f"Elige clase (1-{len(clases)}, 0 para info):", len(clases), permitir_cero=True)
        
        if opcion == -1:
            return False
        if opcion == -2:
            return False
        
        if opcion == 0:
            info_num = pedir_opcion("¿De cuál quieres saber más?", len(clases))
            if info_num > 0:
                clase_info = clases[info_num - 1]
                clase_data = obtener_clase(clase_info["id"])
                if clase_data:
                    print()
                    print(f"  ⚔️  {clase_data['nombre']}")
                    print(f"     {clase_data.get('descripcion', '')}")
                    print()
                    print(f"     Dado de golpe: {clase_data.get('dado_golpe', 'd8')}")
                    print(f"     Salvaciones: {', '.join(s.upper()[:3] for s in clase_data.get('salvaciones', []))}")
                    
                    rasgos = clase_data.get("rasgos_nivel_1", [])
                    if rasgos:
                        print(f"     Rasgos nivel 1: {', '.join(r['nombre'] for r in rasgos)}")
                    print()
            continue
        
        clase_elegida = clases[opcion - 1]
        if creador.establecer_clase(clase_elegida["id"]):
            clase_data = obtener_clase(clase_elegida["id"])
            print(f"\n  ✓ Has elegido: {clase_data['nombre']}")
            
            if _llm_callback:
                raza = creador.pj["info_basica"].get("raza", "")
                raza_data = obtener_raza(raza)
                raza_nombre = raza_data["nombre"] if raza_data else raza
                respuesta = consultar_llm(
                    f"El jugador es un {raza_nombre} {clase_data['nombre']}. "
                    f"En 1-2 frases, comenta qué tipo de personaje podría ser."
                )
                if respuesta:
                    print(f"\n🎭 DM: {respuesta}")
            
            print()
            return True


def paso_caracteristicas(creador: CreadorPersonaje) -> bool:
    """Paso 4: Asignación de características."""
    mostrar_titulo("PASO 4: CARACTERÍSTICAS")
    
    print("  Standard Array: 15, 14, 13, 12, 10, 8")
    print("  Asigna cada valor a una característica.")
    print()
    
    id_clase = creador.pj["info_basica"].get("clase", "")
    clase_data = obtener_clase(id_clase)
    
    if clase_data:
        sugerencia = clase_data.get("sugerencia_atributos", [])
        if sugerencia:
            print(f"  💡 Sugerencia para {clase_data['nombre']}:")
            print(f"     Prioriza: {', '.join(s.upper()[:3] for s in sugerencia[:3])}")
            print()
    
    print("  1. Asignar manualmente")
    print("  2. Usar distribución sugerida para mi clase")
    print()
    
    opcion = pedir_opcion("Elige (1-2):", 2)
    
    if opcion == -1:
        return False
    if opcion == -2:
        return False
    
    if opcion == 2:
        # Distribución automática
        caracteristicas = creador.establecer_caracteristicas_sugeridas()
        print("\n  ✓ Características asignadas:")
        for car in CARACTERISTICAS:
            print(f"     {car.upper()[:3]}: {caracteristicas[car]}")
        print()
        return True
    
    # Asignación manual
    valores_disponibles = list(STANDARD_ARRAY)
    asignacion = {}
    
    for car in CARACTERISTICAS:
        print(f"\n  Valores disponibles: {valores_disponibles}")
        print(f"  Asigna valor a {car.upper()}:")
        
        while True:
            try:
                entrada = input("  > ").strip()
                valor = int(entrada)
                if valor in valores_disponibles:
                    asignacion[car] = valor
                    valores_disponibles.remove(valor)
                    break
                print(f"    Valor no disponible. Elige de: {valores_disponibles}")
            except ValueError:
                print("    Introduce un número")
    
    # Verificar si es semielfo (necesita elegir +1 a dos características)
    id_raza = creador.pj["info_basica"].get("raza", "")
    raza_data = obtener_raza(id_raza)
    bonificadores_elegidos = {}
    
    if raza_data and raza_data.get("bonificadores_elegir"):
        elegir = raza_data["bonificadores_elegir"]
        cantidad = elegir.get("cantidad", 0)
        excluir = elegir.get("excluir", [])
        
        print(f"\n  Como {raza_data['nombre']}, elige {cantidad} características para +1:")
        opciones_car = [c for c in CARACTERISTICAS if c not in excluir]
        
        for i in range(cantidad):
            print(f"  Opciones: {', '.join(c.upper()[:3] for c in opciones_car)}")
            while True:
                entrada = pedir_texto(f"  Característica {i+1}:")
                if entrada and entrada != "__ATRAS__":
                    entrada_lower = entrada.lower()
                    # Buscar coincidencia
                    match = None
                    for c in opciones_car:
                        if c.startswith(entrada_lower) or c[:3] == entrada_lower:
                            match = c
                            break
                    
                    if match:
                        bonificadores_elegidos[match] = 1
                        opciones_car.remove(match)
                        break
                    print("    Característica no válida")
    
    if creador.establecer_caracteristicas(asignacion, bonificadores_elegidos):
        print("\n  ✓ Características establecidas")
        car_final = creador.pj["caracteristicas"]
        for car in CARACTERISTICAS:
            print(f"     {car.upper()[:3]}: {car_final[car]}")
        print()
        return True
    else:
        print("  Error en la asignación")
        return False


def paso_habilidades(creador: CreadorPersonaje) -> bool:
    """Paso 5: Elección de habilidades."""
    mostrar_titulo("PASO 5: HABILIDADES DE CLASE")
    
    opciones = creador.obtener_opciones_habilidades()
    cantidad = opciones.get("cantidad", 0)
    lista_hab = opciones.get("opciones", [])
    
    if cantidad == 0:
        print("  Tu clase no tiene habilidades a elegir en este paso.")
        return True
    
    # Habilidades que ya tiene (de raza)
    habs_actuales = creador.pj.get("competencias", {}).get("habilidades", [])
    
    # Habilidades que dará el trasfondo (para avisar de duplicados)
    id_trasfondo = creador.pj.get("info_basica", {}).get("trasfondo", "")
    from personaje.compendio_pj import obtener_competencias_trasfondo
    habs_trasfondo = obtener_competencias_trasfondo(id_trasfondo).get("habilidades", []) if id_trasfondo else []
    
    if habs_actuales:
        print(f"  Ya tienes por tu raza: {', '.join(h.replace('_', ' ').title() for h in habs_actuales)}")
    
    # Filtrar opciones: quitar las que ya tiene
    lista_hab_filtrada = [h for h in lista_hab if h not in habs_actuales]
    
    if len(lista_hab_filtrada) < cantidad:
        print(f"  (Algunas opciones no disponibles porque ya las tienes)")
    
    print()
    print(f"  Elige {cantidad} habilidades DE TU CLASE:")
    print()
    
    for i, hab in enumerate(lista_hab_filtrada, 1):
        nota = ""
        if hab in habs_trasfondo:
            nota = " (también la da tu trasfondo - podrás elegir otra)"
        print(f"  {i}. {hab.replace('_', ' ').title()}{nota}")
    print()
    
    elegidas = []
    while len(elegidas) < cantidad:
        restantes = cantidad - len(elegidas)
        opcion = pedir_opcion(f"Elige habilidad ({restantes} restantes, 1-{len(lista_hab_filtrada)}):", len(lista_hab_filtrada))
        
        if opcion == -1:
            return False
        if opcion == -2:
            return False
        
        hab = lista_hab_filtrada[opcion - 1]
        if hab in elegidas:
            print("    Ya has elegido esa habilidad")
            continue
        
        elegidas.append(hab)
        print(f"    ✓ {hab.replace('_', ' ').title()}")
    
    if creador.establecer_habilidades(elegidas):
        print("\n  ✓ Habilidades de clase establecidas")
        return True
    return False


def paso_trasfondo(creador: CreadorPersonaje) -> bool:
    """Paso 6: Elección de trasfondo."""
    mostrar_titulo("PASO 6: TRASFONDO")
    
    trasfondos = listar_trasfondos()
    
    if _llm_callback:
        print("🎭 DM: El trasfondo cuenta de dónde vienes y qué hacías antes de")
        print("   convertirte en aventurero. Te da habilidades y un rasgo especial.")
        print()
    
    mostrar_opciones(trasfondos)
    
    opcion = pedir_opcion(f"Elige trasfondo (1-{len(trasfondos)}):", len(trasfondos))
    
    if opcion == -1:
        return False
    if opcion == -2:
        return False
    
    trasfondo_elegido = trasfondos[opcion - 1]
    if creador.establecer_trasfondo(trasfondo_elegido["id"]):
        trasf_data = obtener_trasfondo(trasfondo_elegido["id"])
        print(f"\n  ✓ Has elegido: {trasf_data['nombre']}")
        
        rasgo = trasf_data.get("rasgo", {})
        if rasgo:
            print(f"     Rasgo: {rasgo.get('nombre', '')}")
        
        if _llm_callback:
            raza = obtener_raza(creador.pj["info_basica"].get("raza", ""))
            clase = obtener_clase(creador.pj["info_basica"].get("clase", ""))
            respuesta = consultar_llm(
                f"El jugador es un {raza['nombre'] if raza else ''} {clase['nombre'] if clase else ''} "
                f"con trasfondo de {trasf_data['nombre']}. "
                f"En UNA sola frase corta, comenta qué tipo de historia podría tener."
            )
            if respuesta:
                print(f"\n🎭 DM: {respuesta}")
        
        print()
        return True
    return False




def paso_alineamiento(creador: CreadorPersonaje) -> bool:
    """Paso 6b: Elección de alineamiento."""
    mostrar_titulo("PASO 6b: ALINEAMIENTO")
    
    if _llm_callback:
        # Obtener contexto del personaje
        info = creador.pj.get("info_basica", {})
        raza = obtener_raza(info.get("raza", ""))
        clase = obtener_clase(info.get("clase", ""))
        trasfondo = obtener_trasfondo(info.get("trasfondo", ""))
        
        raza_nombre = raza["nombre"] if raza else "desconocida"
        clase_nombre = clase["nombre"] if clase else "desconocida"
        trasf_nombre = trasfondo["nombre"] if trasfondo else "desconocido"
        
        respuesta = consultar_llm(
            f"El jugador está creando un {raza_nombre} {clase_nombre} con trasfondo {trasf_nombre}. "
            f"En 1-2 frases, explica brevemente qué es el alineamiento y sugiere 2-3 opciones que encajen con este personaje."
        )
        if respuesta:
            print(f"🎭 DM: {respuesta}")
            print()
    else:
        print("  El alineamiento define la brújula moral de tu personaje.")
        print("  Combina ley/caos (cómo ve las reglas) con bien/mal (su ética).")
        print()
    
    # Mostrar opciones en formato de tabla
    print("       │ BUENO          │ NEUTRAL        │ MALVADO")
    print("  ─────┼────────────────┼────────────────┼────────────────")
    print("  LEGAL│ 1. Legal Bueno │ 4. Legal Neutr.│ 7. Legal Malvado")
    print("  NEUTR│ 2. Neutral Bue.│ 5. Neutral     │ 8. Neutral Malv.")
    print("  CAÓT.│ 3. Caótico Bue.│ 6. Caótico Neu.│ 9. Caótico Malv.")
    print()
    
    # Mostrar descripciones
    print("  Descripciones:")
    for i, al in enumerate(ALINEAMIENTOS, 1):
        print(f"    {i}. {al['nombre']}: {al['descripcion']}")
    print()
    
    opcion = pedir_opcion("Elige alineamiento (1-9):", 9)
    
    if opcion == -1 or opcion == -2:
        return False
    
    alineamiento = ALINEAMIENTOS[opcion - 1]
    creador.pj["info_basica"]["alineamiento"] = alineamiento["id"]
    
    print(f"\n  ✓ Alineamiento: {alineamiento['nombre']}")
    return True

def paso_personalidad(creador: CreadorPersonaje) -> bool:
    """Paso 7: Rasgos de personalidad."""
    mostrar_titulo("PASO 7: PERSONALIDAD")
    
    id_trasfondo = creador.pj["info_basica"].get("trasfondo", "")
    opciones = obtener_personalidad_trasfondo(id_trasfondo)
    
    print("  Define la personalidad de tu personaje.")
    print("  Puedes escribir tus propios rasgos o elegir de las sugerencias.")
    print()
    
    # Rasgo de personalidad
    print("  RASGO DE PERSONALIDAD:")
    rasgos_sugeridos = opciones.get("rasgos_personalidad", [])
    if rasgos_sugeridos:
        print("  Sugerencias:")
        for i, r in enumerate(rasgos_sugeridos[:4], 1):
            print(f"    {i}. {r}")
    
    rasgo = pedir_texto("  Tu rasgo (número o texto):", obligatorio=False)
    if rasgo is None:
        return False
    if rasgo == "__ATRAS__":
        return False
    
    # Convertir número a texto
    if rasgo.isdigit() and 1 <= int(rasgo) <= len(rasgos_sugeridos):
        rasgo = rasgos_sugeridos[int(rasgo) - 1]
    
    # Ideal
    print("\n  IDEAL:")
    ideales_sugeridos = opciones.get("ideales", [])
    if ideales_sugeridos:
        print("  Sugerencias:")
        for i, ideal in enumerate(ideales_sugeridos[:4], 1):
            texto = ideal.get("texto", str(ideal)) if isinstance(ideal, dict) else ideal
            print(f"    {i}. {texto}")
    
    ideal = pedir_texto("  Tu ideal (número o texto):", obligatorio=False)
    if ideal is None:
        return False
    
    if ideal.isdigit() and 1 <= int(ideal) <= len(ideales_sugeridos):
        i = ideales_sugeridos[int(ideal) - 1]
        ideal = i.get("texto", str(i)) if isinstance(i, dict) else i
    
    # Vínculo
    print("\n  VÍNCULO:")
    vinculos_sugeridos = opciones.get("vinculos", [])
    if vinculos_sugeridos:
        print("  Sugerencias:")
        for i, v in enumerate(vinculos_sugeridos[:4], 1):
            print(f"    {i}. {v}")
    
    vinculo = pedir_texto("  Tu vínculo (número o texto):", obligatorio=False)
    if vinculo is None:
        return False
    
    if vinculo.isdigit() and 1 <= int(vinculo) <= len(vinculos_sugeridos):
        vinculo = vinculos_sugeridos[int(vinculo) - 1]
    
    # Defecto
    print("\n  DEFECTO:")
    defectos_sugeridos = opciones.get("defectos", [])
    if defectos_sugeridos:
        print("  Sugerencias:")
        for i, d in enumerate(defectos_sugeridos[:4], 1):
            print(f"    {i}. {d}")
    
    defecto = pedir_texto("  Tu defecto (número o texto):", obligatorio=False)
    if defecto is None:
        return False
    
    if defecto.isdigit() and 1 <= int(defecto) <= len(defectos_sugeridos):
        defecto = defectos_sugeridos[int(defecto) - 1]
    
    creador.establecer_personalidad(
        rasgos=[rasgo] if rasgo else [],
        ideales=[ideal] if ideal else [],
        vinculos=[vinculo] if vinculo else [],
        defectos=[defecto] if defecto else [],
    )
    
    print("\n  ✓ Personalidad establecida")
    return True


def paso_equipo(creador: CreadorPersonaje) -> bool:
    """Paso 8: Equipo inicial."""
    mostrar_titulo("PASO 8: EQUIPO")
    
    id_clase = creador.pj["info_basica"].get("clase", "")
    clase_data = obtener_clase(id_clase)
    
    print(f"  Como {clase_data['nombre'] if clase_data else id_clase}, recibes equipo inicial.")
    print()
    print("  Por ahora, asignaremos el equipo estándar de tu clase.")
    print("  (En futuras versiones podrás elegir opciones)")
    print()
    
    creador.establecer_equipo_basico(id_clase)
    
    # Mostrar equipo asignado
    equipo = creador.pj.get("equipo", {})
    print("  ✓ Equipo asignado:")
    
    armas = equipo.get("armas", [])
    for arma in armas:
        eq = "⚔️" if arma.get("equipada") else " "
        print(f"     {eq} {arma.get('nombre', '?')}")
    
    armadura = equipo.get("armadura")
    if armadura:
        print(f"     🛡️ {armadura.get('nombre', '?')}")
    
    escudo = equipo.get("escudo")
    if escudo:
        print(f"     🛡️ {escudo.get('nombre', '?')}")
    
    print()
    
    # Opciones de clase específicas
    if id_clase == "guerrero":
        print("  Elige tu Estilo de Combate:")
        estilos = creador.obtener_opciones_estilo_combate()
        for i, e in enumerate(estilos, 1):
            print(f"    {i}. {e['nombre']}: {e.get('descripcion', '')}")
        
        opcion = pedir_opcion(f"Elige (1-{len(estilos)}):", len(estilos))
        if opcion > 0:
            estilo = estilos[opcion - 1]
            creador.establecer_rasgo_clase("estilo_combate", estilo["id"])
            print(f"    ✓ {estilo['nombre']}")
    
    elif id_clase == "clerigo":
        print("  Elige tu Dominio Divino:")
        dominios = creador.obtener_opciones_dominio()
        for i, d in enumerate(dominios, 1):
            print(f"    {i}. {d['nombre']}: {d.get('descripcion', '')[:50]}...")
        
        opcion = pedir_opcion(f"Elige (1-{len(dominios)}):", len(dominios))
        if opcion > 0:
            dominio = dominios[opcion - 1]
            creador.establecer_rasgo_clase("dominio_divino", dominio["id"])
            print(f"    ✓ {dominio['nombre']}")
    
    print()
    return True


def paso_detalles(creador: CreadorPersonaje) -> bool:
    """Paso 9: Detalles del personaje."""
    mostrar_titulo("PASO 9: DETALLES FINALES")
    
    # Nombre
    print("  NOMBRE DEL PERSONAJE:")
    
    id_raza = creador.pj["info_basica"].get("raza", "")
    nombres = creador.obtener_sugerencias_nombre("masculino")
    apellidos = creador.obtener_sugerencias_apellido()
    
    if nombres:
        sugeridos = random.sample(nombres, min(3, len(nombres)))
        if apellidos:
            sugeridos = [f"{n} {random.choice(apellidos)}" for n in sugeridos]
        print(f"  Sugerencias: {', '.join(sugeridos)}")
    
    if _llm_callback:
        raza_data = obtener_raza(id_raza)
        clase_data = obtener_clase(creador.pj["info_basica"].get("clase", ""))
        respuesta = consultar_llm(
            f"Sugiere 2-3 nombres épicos para un {raza_data['nombre'] if raza_data else ''} "
            f"{clase_data['nombre'] if clase_data else ''}. Solo los nombres, separados por coma."
        )
        if respuesta:
            print(f"  🎭 DM sugiere: {respuesta}")
    
    nombre = pedir_texto("  Nombre:")
    if nombre is None:
        return False
    if nombre == "__ATRAS__":
        return False
    
    # Descripción física (opcional)
    print("\n  DESCRIPCIÓN FÍSICA (opcional, Enter para saltar):")
    
    edad = pedir_texto("  Edad:", obligatorio=False)
    if edad is None:
        return False
    edad_num = int(edad) if edad and edad.isdigit() else None
    
    ojos = pedir_texto("  Color de ojos:", obligatorio=False) or ""
    cabello = pedir_texto("  Cabello:", obligatorio=False) or ""
    
    # Backstory
    print("\n  HISTORIA (opcional):")
    if _llm_callback:
        print("  Escribe una breve historia, o escribe 'ayuda' para que el DM sugiera.")
    
    backstory = pedir_texto("  Historia:", obligatorio=False) or ""
    
    if backstory.lower() == "ayuda" and _llm_callback:
        raza_data = obtener_raza(id_raza)
        clase_data = obtener_clase(creador.pj["info_basica"].get("clase", ""))
        trasf_data = obtener_trasfondo(creador.pj["info_basica"].get("trasfondo", ""))
        
        respuesta = consultar_llm(
            f"Crea una historia de fondo breve (3-4 frases) para {nombre}, "
            f"un {raza_data['nombre'] if raza_data else ''} {clase_data['nombre'] if clase_data else ''} "
            f"con trasfondo de {trasf_data['nombre'] if trasf_data else ''}."
        )
        if respuesta:
            print(f"\n🎭 DM: {respuesta}")
            usar = pedir_texto("  ¿Usar esta historia? (s/n):", obligatorio=False)
            if usar and usar.lower() in ["s", "si", "sí", "yes", "y"]:
                backstory = respuesta
    
    creador.establecer_detalles(
        nombre=nombre,
        edad=edad_num,
        ojos=ojos if ojos != "__ATRAS__" else "",
        cabello=cabello if cabello != "__ATRAS__" else "",
        backstory=backstory if backstory != "__ATRAS__" else "",
    )
    
    print("\n  ✓ Detalles establecidos")
    return True


def paso_resumen(creador: CreadorPersonaje) -> bool:
    """Paso 10: Resumen y confirmación."""
    mostrar_titulo("RESUMEN DEL PERSONAJE")
    
    # Finalizar y recalcular
    pj = creador.finalizar()
    
    # Mostrar resumen
    info = pj.get("info_basica", {})
    car = pj.get("caracteristicas", {})
    derivados = pj.get("derivados", {})
    
    raza_data = obtener_raza(info.get("raza", ""))
    clase_data = obtener_clase(info.get("clase", ""))
    trasf_data = obtener_trasfondo(info.get("trasfondo", ""))
    
    print(f"  Nombre: {info.get('nombre', 'Sin nombre')}")
    print(f"  Raza: {raza_data['nombre'] if raza_data else info.get('raza', '?')}")
    print(f"  Clase: {clase_data['nombre'] if clase_data else info.get('clase', '?')} Nivel {info.get('nivel', 1)}")
    print(f"  Trasfondo: {trasf_data['nombre'] if trasf_data else info.get('trasfondo', '?')}")
    
    # Alineamiento
    alineamiento_id = info.get('alineamiento', '')
    alineamiento_nombre = alineamiento_id.replace('_', ' ').title() if alineamiento_id else "No definido"
    print(f"  Alineamiento: {alineamiento_nombre}")
    print()
    
    print("  CARACTERÍSTICAS:")
    for c in CARACTERISTICAS:
        val = car.get(c, 10)
        mod = derivados.get("modificadores", {}).get(c, 0)
        print(f"    {c.upper()[:3]}: {val:2d} ({mod:+d})")
    print()
    
    print("  COMBATE:")
    print(f"    HP: {derivados.get('puntos_golpe_maximo', 0)}")
    
    # CA con detalle numérico (usando helper)
    print(f"    CA: {formatear_ca_detalle(pj)}")
    
    print(f"    Velocidad: {derivados.get('velocidad', 30)} pies")
    print(f"    Iniciativa: {derivados.get('iniciativa', 0):+d}")
    
    # Bonificadores de ataque
    bon_comp = derivados.get('bonificador_competencia', 2)
    mods = derivados.get('modificadores', {})
    mod_fue = mods.get('fuerza', 0)
    mod_des = mods.get('destreza', 0)
    
    print(f"    Ataque CaC: {mod_fue + bon_comp:+d} | Distancia: {mod_des + bon_comp:+d}")
    print()
    
    # Salvaciones resumidas
    salvaciones = derivados.get('salvaciones', {})
    competentes = pj.get('competencias', {}).get('salvaciones', [])
    print("  SALVACIONES:", end=" ")
    partes_salv = []
    for c in ["fuerza", "destreza", "constitucion", "inteligencia", "sabiduria", "carisma"]:
        val = salvaciones.get(c, 0)
        marca = "●" if c in competentes else ""
        partes_salv.append(f"{c.upper()[:3]} {val:+d}{marca}")
    print(" | ".join(partes_salv))
    print()
    
    # Mostrar habilidades separadas por origen (usando el campo guardado)
    competencias = pj.get("competencias", {})
    habilidades = competencias.get("habilidades", [])
    origenes = competencias.get("habilidades_origen", {})
    
    if habilidades:
        # Agrupar por origen
        por_origen = {"raza": [], "clase": [], "trasfondo": []}
        for h in habilidades:
            origen = origenes.get(h, "otro")
            if origen in por_origen:
                por_origen[origen].append(h)
            else:
                por_origen.setdefault("otro", []).append(h)
        
        for origen, lista in por_origen.items():
            if lista:
                print(f"  HABILIDADES ({origen}): {', '.join(h.replace('_', ' ').title() for h in lista)}")
        print()
    
    # Confirmar
    print("  ¿Guardar este personaje?")
    print("    1. Sí, guardar")
    print("    2. No, volver a editar")
    print()
    
    opcion = pedir_opcion("Elige (1-2):", 2)
    
    if opcion == 1:
        id_guardado = save_character(pj)
        print(f"\n  ✓ Personaje guardado con ID: {id_guardado}")
        print(f"    Archivo: storage/characters/{id_guardado}.json")
        
        if _llm_callback:
            print(f"\n🎭 DM: ¡{info.get('nombre', 'Aventurero')} está listo para la aventura!")
            print("   Que los dados te sean favorables. ⚔️")
        
        return True
    
    return False


# =============================================================================
# FLUJO PRINCIPAL
# =============================================================================

def mostrar_menu_inicial():
    """Muestra el menú inicial."""
    mostrar_titulo("CREACIÓN DE PERSONAJE - D&D 5e")
    
    print("  1. Crear nuevo personaje")
    print("  2. Continuar creación en progreso")
    print("  3. Ver personajes guardados")
    print("  0. Salir")
    print()


def ejecutar_flujo(creador: CreadorPersonaje):
    """Ejecuta el flujo de creación completo."""
    
    pasos = {
        PasoCreacion.CONCEPTO: paso_concepto,
        PasoCreacion.RAZA: paso_raza,
        PasoCreacion.CLASE: paso_clase,
        PasoCreacion.CARACTERISTICAS: paso_caracteristicas,
        PasoCreacion.HABILIDADES: paso_habilidades,
        PasoCreacion.TRASFONDO: paso_trasfondo,
        "alineamiento": paso_alineamiento,  # Paso adicional
        PasoCreacion.PERSONALIDAD: paso_personalidad,
        PasoCreacion.EQUIPO: paso_equipo,
        PasoCreacion.DETALLES: paso_detalles,
        PasoCreacion.RESUMEN: paso_resumen,
    }
    
    while True:
        paso_actual = creador.obtener_paso_actual()
        funcion_paso = pasos.get(paso_actual)
        
        if not funcion_paso:
            print(f"  Error: paso desconocido {paso_actual}")
            break
        
        resultado = funcion_paso(creador)
        
        if not resultado:
            # Usuario canceló o pidió volver
            if paso_actual == PasoCreacion.CONCEPTO:
                # En el primer paso, salir
                print("\n  Creación cancelada.")
                break
            else:
                # Volver al paso anterior
                creador.retroceder_paso()
        else:
            # Avanzar
            if paso_actual == PasoCreacion.RESUMEN:
                # Terminado
                break
            
            # Insertar paso de alineamiento después de trasfondo
            if paso_actual == PasoCreacion.TRASFONDO:
                resultado_al = paso_alineamiento(creador)
                if not resultado_al:
                    continue  # Quedarse en trasfondo si cancela
            
            creador.avanzar_paso()


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(description="Creador de personajes D&D 5e")
    parser.add_argument("--llm", action="store_true", help="Usar LLM para sugerencias")
    parser.add_argument("--continuar", type=str, help="ID de autosave a continuar")
    args = parser.parse_args()
    
    # Configurar LLM si se solicita
    if args.llm:
        configurar_llm()
    
    print()
    print("  🐉 CREADOR DE PERSONAJES D&D 5e")
    print("  ════════════════════════════════")
    print()
    print("  Comandos disponibles en cualquier momento:")
    print("    /salir - Salir (se guarda progreso)")
    print("    /atras - Volver al paso anterior")
    print()
    
    if args.continuar:
        # Continuar desde autosave
        autosave = load_autosave(args.continuar)
        if autosave:
            creador = cargar_creador_desde_autosave(autosave)
            print(f"  ✓ Continuando creación de: {creador.pj.get('info_basica', {}).get('nombre', 'Sin nombre')}")
            print(f"    Paso actual: {creador.paso_actual.value}")
            ejecutar_flujo(creador)
        else:
            print(f"  Error: No se encontró autosave con ID {args.continuar}")
        return
    
    # Menú inicial
    while True:
        mostrar_menu_inicial()
        opcion = pedir_opcion("Elige (0-3):", 3, permitir_cero=True)
        
        if opcion == 0 or opcion == -1:
            print("\n  ¡Hasta pronto!")
            break
        
        elif opcion == 1:
            # Nuevo personaje
            creador = CreadorPersonaje()
            ejecutar_flujo(creador)
        
        elif opcion == 2:
            # Continuar
            autosaves = list_autosaves()
            if not autosaves:
                print("\n  No hay creaciones en progreso.")
                continue
            
            print("\n  Creaciones en progreso:")
            for i, a in enumerate(autosaves, 1):
                print(f"    {i}. {a['nombre']} ({a['raza']} {a['clase']}) - Paso: {a['paso_actual']}")
            
            idx = pedir_opcion(f"Elige (1-{len(autosaves)}):", len(autosaves))
            if idx > 0:
                autosave = load_autosave(autosaves[idx - 1]["id"])
                if autosave:
                    creador = cargar_creador_desde_autosave(autosave)
                    ejecutar_flujo(creador)
        
        elif opcion == 3:
            # Ver guardados
            from personaje import list_characters, load_character, delete_character, recalcular_derivados
            personajes = list_characters()
            if not personajes:
                print("\n  No hay personajes guardados.")
                continue
            
            while True:
                print("\n  Personajes guardados:")
                for i, p in enumerate(personajes, 1):
                    print(f"    {i}. {p['nombre']} ({p['raza']} {p['clase']} Nv.{p['nivel']})")
                print(f"    0. Volver al menú")
                print()
                
                idx = pedir_opcion(f"Ver personaje (1-{len(personajes)}, 0 para volver):", len(personajes), permitir_cero=True)
                
                if idx == 0 or idx == -1 or idx == -2:
                    break
                
                # Cargar y mostrar ficha completa
                pj_seleccionado = personajes[idx - 1]
                pj = load_character(pj_seleccionado['id'])
                if not pj:
                    print("  Error al cargar personaje")
                    continue
                
                # Recalcular derivados
                recalcular_derivados(pj)
                
                # Mostrar ficha completa
                mostrar_ficha_completa(pj)
                
                # Opciones
                print("\n  ¿Qué deseas hacer?")
                print("    1. Volver a la lista")
                print("    2. Borrar este personaje")
                print()
                
                accion = pedir_opcion("Elige (1-2):", 2)
                
                if accion == 2:
                    # Confirmar borrado
                    print(f"\n  ⚠️  ¿Seguro que quieres BORRAR a {pj_seleccionado['nombre']}?")
                    print("    Esta acción NO se puede deshacer.")
                    print()
                    confirmar = pedir_texto("  Escribe 'BORRAR' para confirmar:", obligatorio=False)
                    
                    if confirmar == "BORRAR":
                        if delete_character(pj_seleccionado['id']):
                            print(f"\n  ✓ {pj_seleccionado['nombre']} ha sido eliminado.")
                            # Actualizar lista
                            personajes = list_characters()
                            if not personajes:
                                print("  No quedan personajes guardados.")
                                break
                        else:
                            print("  Error al borrar")
                    else:
                        print("  Borrado cancelado.")


if __name__ == "__main__":
    main()
