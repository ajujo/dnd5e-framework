"""
Calculador de valores derivados para personajes D&D 5e.

Funciones para calcular HP, CA, modificadores, salvaciones, etc.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional

from . import compendio_pj


# Tabla de CA de armaduras
# IDs alineados con compendio/armaduras_escudos.json
# Convención: palabras_principales_con_guion_bajo (sin artículos/preposiciones)
ARMADURAS = {
    "sin_armadura": {"ca_base": 10, "mod_des": True, "max_des": None, "tipo": None},
    # Ligeras
    "armadura_acolchada": {"ca_base": 11, "mod_des": True, "max_des": None, "tipo": "ligera"},
    "armadura_cuero": {"ca_base": 11, "mod_des": True, "max_des": None, "tipo": "ligera"},
    "armadura_cuero_tachonado": {"ca_base": 12, "mod_des": True, "max_des": None, "tipo": "ligera"},
    # Medias
    "armadura_pieles": {"ca_base": 12, "mod_des": True, "max_des": 2, "tipo": "media"},
    "cota_mallas": {"ca_base": 13, "mod_des": True, "max_des": 2, "tipo": "media"},
    "cota_escamas": {"ca_base": 14, "mod_des": True, "max_des": 2, "tipo": "media"},
    "coraza": {"ca_base": 14, "mod_des": True, "max_des": 2, "tipo": "media"},
    "semiplacas": {"ca_base": 15, "mod_des": True, "max_des": 2, "tipo": "media"},
    # Pesadas
    "armadura_anillas": {"ca_base": 14, "mod_des": False, "max_des": 0, "tipo": "pesada"},
    "cota_mallas_pesada": {"ca_base": 16, "mod_des": False, "max_des": 0, "tipo": "pesada"},
    "cota_bandas": {"ca_base": 17, "mod_des": False, "max_des": 0, "tipo": "pesada"},
    "armadura_placas": {"ca_base": 18, "mod_des": False, "max_des": 0, "tipo": "pesada"},
}

ESCUDO_CA = 2


def calcular_modificador(valor: int) -> int:
    """
    Calcula el modificador de una característica.
    
    Formula: (valor - 10) // 2
    
    Args:
        valor: Puntuación de la característica (1-30)
        
    Returns:
        Modificador (-5 a +10)
    """
    return (valor - 10) // 2


def calcular_bonificador_competencia(nivel: int) -> int:
    """
    Calcula el bonificador de competencia según el nivel.
    
    Nivel 1-4: +2
    Nivel 5-8: +3
    Nivel 9-12: +4
    Nivel 13-16: +5
    Nivel 17-20: +6
    
    Args:
        nivel: Nivel del personaje (1-20)
        
    Returns:
        Bonificador de competencia (+2 a +6)
    """
    return 2 + (nivel - 1) // 4


def calcular_hp_maximo(
    clase: str, 
    nivel: int, 
    mod_con: int, 
    rasgos_raciales: List[Dict] = None
) -> int:
    """
    Calcula los puntos de golpe máximos.
    
    Nivel 1: Dado de golpe máximo + mod CON
    Niveles siguientes: (dado/2 + 1) + mod CON por nivel
    
    Args:
        clase: ID de la clase
        nivel: Nivel del personaje
        mod_con: Modificador de Constitución
        rasgos_raciales: Lista de rasgos raciales (para Dureza Enana)
        
    Returns:
        HP máximo
    """
    rasgos_raciales = rasgos_raciales or []
    
    # HP base de nivel 1
    hp_base = compendio_pj.obtener_hp_nivel_1_clase(clase)
    hp = hp_base + mod_con
    
    # HP por niveles adicionales
    if nivel > 1:
        dado_golpe = compendio_pj.obtener_dado_golpe_clase(clase)
        # Valor promedio redondeado arriba
        promedio = int(dado_golpe[1:]) // 2 + 1
        hp += (promedio + mod_con) * (nivel - 1)
    
    # Dureza Enana: +1 HP por nivel
    tiene_dureza = any(r.get("id") == "dureza_enana" for r in rasgos_raciales)
    if tiene_dureza:
        hp += nivel
    
    return max(1, hp)


def calcular_ca(pj: dict, mods: Dict[str, int], debug: bool = False) -> int:
    """
    Calcula la Clase de Armadura.
    
    CA = armadura_base + mod_des (limitado) + escudo + bonuses
    
    Args:
        pj: Diccionario del personaje
        mods: Diccionario de modificadores de característica
        debug: Si True, imprime detalles del cálculo
        
    Returns:
        Clase de Armadura
    """
    equipo = pj.get("equipo") or {}
    rasgos_clase = pj.get("rasgos", {}).get("clase", [])
    
    # Determinar armadura equipada
    armadura = equipo.get("armadura")
    arm_data = ARMADURAS["sin_armadura"]
    ref_usado = "sin_armadura"
    
    if armadura and armadura.get("equipada"):
        # Buscar por compendio_ref o por id
        ref = armadura.get("compendio_ref", armadura.get("id", "sin_armadura"))
        
        if debug:
            print(f"  [DEBUG CA] Armadura dict: {armadura}")
            print(f"  [DEBUG CA] Buscando ref: '{ref}'")
            print(f"  [DEBUG CA] ¿Está en ARMADURAS?: {ref in ARMADURAS}")
        
        # Buscar en ARMADURAS
        if ref in ARMADURAS:
            arm_data = ARMADURAS[ref]
            ref_usado = ref
        else:
            # Intentar sin sufijo numérico
            ref_base = "_".join(ref.split("_")[:-1]) if ref[-1].isdigit() else ref
            if debug:
                print(f"  [DEBUG CA] Intentando ref_base: '{ref_base}'")
            if ref_base in ARMADURAS:
                arm_data = ARMADURAS[ref_base]
                ref_usado = ref_base
    
    ca = arm_data["ca_base"]
    
    if debug:
        print(f"  [DEBUG CA] Usando armadura: '{ref_usado}' -> CA base {ca}")
    
    # Modificador de Destreza (si aplica)
    bonus_des = 0
    if arm_data["mod_des"]:
        mod_des = mods.get("destreza", 0)
        if arm_data["max_des"] is not None:
            mod_des = min(mod_des, arm_data["max_des"])
        bonus_des = mod_des
        ca += mod_des
        if debug:
            print(f"  [DEBUG CA] + DES: {mod_des} (max: {arm_data['max_des']})")
    
    # Escudo
    escudo = equipo.get("escudo")
    if escudo and escudo.get("equipada"):
        ca += ESCUDO_CA
        if debug:
            print(f"  [DEBUG CA] + Escudo: {ESCUDO_CA}")
    elif debug:
        print(f"  [DEBUG CA] Escudo: {escudo}")
    
    # Estilo de combate: Defensa (+1 CA con armadura)
    for rasgo in rasgos_clase:
        if rasgo.get("id") == "estilo_combate" and rasgo.get("opcion") == "defensa":
            if armadura and armadura.get("equipada"):
                ca += 1
                if debug:
                    print(f"  [DEBUG CA] + Estilo Defensa: 1")
            break
    
    if debug:
        print(f"  [DEBUG CA] CA FINAL: {ca}")
    
    return ca


def calcular_salvaciones(
    mods: Dict[str, int], 
    competencias_salvacion: List[str], 
    bonificador_competencia: int
) -> Dict[str, int]:
    """
    Calcula los bonificadores de tiradas de salvación.
    
    Args:
        mods: Modificadores de característica
        competencias_salvacion: Lista de salvaciones competentes
        bonificador_competencia: Bonificador de competencia
        
    Returns:
        Diccionario de bonificadores por característica
    """
    salvaciones = {}
    for car, mod in mods.items():
        bonus = mod
        if car in competencias_salvacion:
            bonus += bonificador_competencia
        salvaciones[car] = bonus
    return salvaciones


def calcular_iniciativa(mod_des: int, bonus_adicional: int = 0) -> int:
    """
    Calcula el bonificador de iniciativa.
    
    Args:
        mod_des: Modificador de Destreza
        bonus_adicional: Bonus de rasgos o dotes
        
    Returns:
        Bonificador de iniciativa
    """
    return mod_des + bonus_adicional


def calcular_velocidad(id_raza: str, equipo: dict = None) -> int:
    """
    Calcula la velocidad base.
    
    Args:
        id_raza: ID de la raza
        equipo: Equipo del personaje (para penalizaciones)
        
    Returns:
        Velocidad en pies
    """
    raza = compendio_pj.obtener_raza(id_raza)
    if not raza:
        return 30
    
    velocidad = raza.get("velocidad", 30)
    
    # Los enanos no pierden velocidad con armadura pesada
    # Otras razas pequeñas tampoco tienen penalización en 5e
    
    return velocidad


def aplicar_bonificadores_raza(
    caracteristicas: Dict[str, int], 
    id_raza: str,
    bonificadores_elegidos: Dict[str, int] = None
) -> Dict[str, int]:
    """
    Aplica los bonificadores raciales a las características.
    
    Args:
        caracteristicas: Diccionario de características base
        id_raza: ID de la raza
        bonificadores_elegidos: Para razas con elección (semielfo)
        
    Returns:
        Características con bonificadores aplicados
    """
    bonificadores_elegidos = bonificadores_elegidos or {}
    
    # Copiar para no modificar original
    resultado = caracteristicas.copy()
    
    # Bonificadores fijos de la raza
    bonificadores = compendio_pj.obtener_bonificadores_raza(id_raza)
    for car, bonus in bonificadores.items():
        if car in resultado:
            resultado[car] += bonus
    
    # Bonificadores elegidos (ej: semielfo)
    for car, bonus in bonificadores_elegidos.items():
        if car in resultado:
            resultado[car] += bonus
    
    return resultado


def recalcular_derivados(pj: dict) -> dict:
    """
    Recalcula todos los valores derivados de un personaje.
    
    Debe ejecutarse:
    - Al cargar un personaje
    - Después de cambios de equipo
    - Después de subir de nivel
    - Después de efectos que modifiquen características
    
    Args:
        pj: Diccionario del personaje
        
    Returns:
        El personaje con derivados actualizados
    """
    info = pj.get("info_basica") or {}
    caracteristicas = pj.get("caracteristicas") or {}
    competencias = pj.get("competencias") or {}
    rasgos_raciales = pj.get("rasgos", {}).get("raciales", [])
    
    # Modificadores de característica
    mods = {car: calcular_modificador(val) for car, val in caracteristicas.items()}
    
    # Bonificador de competencia
    nivel = info.get("nivel", 1)
    bon_comp = calcular_bonificador_competencia(nivel)
    
    # HP máximo
    clase = info.get("clase", "guerrero")
    hp_max = calcular_hp_maximo(
        clase, 
        nivel, 
        mods.get("constitucion", 0), 
        rasgos_raciales
    )
    
    # CA
    ca = calcular_ca(pj, mods)
    
    # Velocidad
    raza = info.get("raza", "humano")
    velocidad = calcular_velocidad(raza, pj.get("equipo"))
    
    # Salvaciones
    salvaciones = calcular_salvaciones(
        mods, 
        competencias.get("salvaciones", []), 
        bon_comp
    )
    
    # Iniciativa
    iniciativa = calcular_iniciativa(mods.get("destreza", 0))
    
    # Dado de golpe
    dado_golpe = compendio_pj.obtener_dado_golpe_clase(clase)
    
    # Preservar HP actual si existe (no exceder máximo)
    hp_actual = pj.get("derivados", {}).get("puntos_golpe_actual", hp_max)
    hp_actual = min(hp_actual, hp_max)
    
    # Actualizar derivados
    pj["derivados"] = {
        "bonificador_competencia": bon_comp,
        "puntos_golpe_maximo": hp_max,
        "puntos_golpe_actual": hp_actual,
        "dado_golpe": dado_golpe,
        "clase_armadura": ca,
        "velocidad": velocidad,
        "iniciativa": iniciativa,
        "modificadores": mods,
        "salvaciones": salvaciones,
    }
    
    return pj


def generar_resumen_derivados(pj: dict) -> str:
    """
    Genera un resumen legible de los valores derivados.
    
    Args:
        pj: Personaje con derivados calculados
        
    Returns:
        String formateado con el resumen
    """
    d = pj.get("derivados") or {}
    mods = d.get("modificadores", {})
    salvaciones = d.get("salvaciones", {})
    
    lineas = [
        f"HP: {d.get('puntos_golpe_actual', 0)}/{d.get('puntos_golpe_maximo', 0)}",
        f"CA: {d.get('clase_armadura', 10)}",
        f"Velocidad: {d.get('velocidad', 30)} pies",
        f"Iniciativa: {d.get('iniciativa', 0):+d}",
        f"Competencia: +{d.get('bonificador_competencia', 2)}",
        "",
        "Modificadores:",
    ]
    
    for car in ["fuerza", "destreza", "constitucion", "inteligencia", "sabiduria", "carisma"]:
        mod = mods.get(car, 0)
        lineas.append(f"  {car.upper()[:3]}: {mod:+d}")
    
    lineas.extend(["", "Salvaciones:"])
    for car in ["fuerza", "destreza", "constitucion", "inteligencia", "sabiduria", "carisma"]:
        sal = salvaciones.get(car, 0)
        lineas.append(f"  {car.upper()[:3]}: {sal:+d}")
    
    return "\n".join(lineas)
