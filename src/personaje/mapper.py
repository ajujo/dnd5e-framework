"""
Mapper de personaje a combatiente.

Convierte una ficha de personaje al formato que usa el motor de combate.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..motor.combate import Combatiente, TipoCombatiente


def to_combatiente(pj: dict) -> "Combatiente":
    """
    Convierte una ficha de personaje a un Combatiente para el motor de combate.
    
    Esta función es defensiva: usa valores por defecto si faltan campos,
    para evitar errores cuando el schema del personaje cambia.
    
    Args:
        pj: Diccionario del personaje (ficha completa)
        
    Returns:
        Instancia de Combatiente lista para el motor de combate
    """
    # Importar aquí para evitar dependencia circular
    from ..motor.combate import Combatiente, TipoCombatiente
    
    # Extraer secciones con fallback a dict vacío
    d = pj.get("derivados") or pj.get("_derivados") or {}
    c = pj.get("caracteristicas") or {}
    info = pj.get("info_basica") or {}
    equipo = pj.get("equipo") or {}
    conjuros = pj.get("conjuros") or {}
    
    # Determinar arma principal
    # Opción 1: campo directo arma_principal
    # Opción 2: buscar en lista de armas la que está equipada
    arma_principal = equipo.get("arma_principal")
    if not arma_principal:
        armas = equipo.get("armas", [])
        arma_principal = next((a for a in armas if a.get("equipada")), None)
    
    # Arma secundaria (opcional)
    arma_secundaria = equipo.get("arma_secundaria")
    
    # Construir combatiente con valores defensivos
    return Combatiente(
        id=pj.get("id", "pj_sin_id"),
        nombre=info.get("nombre", "Aventurero"),
        tipo=TipoCombatiente.PC,
        
        # Puntos de golpe
        hp_maximo=d.get("puntos_golpe_maximo", 1),
        hp_actual=d.get("puntos_golpe_actual", d.get("puntos_golpe_maximo", 1)),
        
        # Defensa y movimiento
        clase_armadura=d.get("clase_armadura", 10),
        velocidad=d.get("velocidad", 30),
        
        # Características
        fuerza=c.get("fuerza", 10),
        destreza=c.get("destreza", 10),
        constitucion=c.get("constitucion", 10),
        inteligencia=c.get("inteligencia", 10),
        sabiduria=c.get("sabiduria", 10),
        carisma=c.get("carisma", 10),
        
        # Bonificador de competencia
        bonificador_competencia=d.get("bonificador_competencia", 2),
        
        # Equipo
        arma_principal=arma_principal,
        arma_secundaria=arma_secundaria,
        
        # Conjuros (si aplica)
        conjuros_conocidos=conjuros.get("conocidos", []),
        ranuras_conjuro=conjuros.get("ranuras", {}),
    )


def from_combatiente(combatiente: "Combatiente", pj_base: dict = None) -> dict:
    """
    Actualiza una ficha de personaje con los datos de un combatiente.
    
    Útil para sincronizar el estado después del combate (HP actual, etc.)
    
    Args:
        combatiente: Instancia de Combatiente
        pj_base: Ficha base a actualizar (opcional, crea nueva si no se provee)
        
    Returns:
        Ficha de personaje actualizada
    """
    if pj_base is None:
        pj_base = {}
    
    # Asegurar que existe la sección de derivados
    if "derivados" not in pj_base:
        pj_base["derivados"] = {}
    
    # Sincronizar HP actual (lo más común después de combate)
    pj_base["derivados"]["puntos_golpe_actual"] = combatiente.hp_actual
    
    # Sincronizar ranuras de conjuro usadas (si aplica)
    if combatiente.ranuras_conjuro:
        if "conjuros" not in pj_base:
            pj_base["conjuros"] = {}
        pj_base["conjuros"]["ranuras"] = combatiente.ranuras_conjuro
    
    return pj_base


def crear_pj_minimo_para_test(
    nombre: str = "Héroe",
    clase: str = "guerrero",
    raza: str = "humano",
    nivel: int = 1
) -> dict:
    """
    Crea un personaje mínimo para pruebas.
    
    Args:
        nombre: Nombre del personaje
        clase: Clase del personaje
        raza: Raza del personaje
        nivel: Nivel del personaje
        
    Returns:
        Diccionario del personaje con valores por defecto
    """
    from .calculador import recalcular_derivados
    from . import compendio_pj
    
    # Standard Array por defecto
    caracteristicas_base = {
        "fuerza": 15,
        "destreza": 14,
        "constitucion": 13,
        "inteligencia": 12,
        "sabiduria": 10,
        "carisma": 8,
    }
    
    # Aplicar bonificadores raciales
    bonificadores = compendio_pj.obtener_bonificadores_raza(raza)
    caracteristicas = caracteristicas_base.copy()
    for car, bonus in bonificadores.items():
        if car in caracteristicas:
            caracteristicas[car] += bonus
    
    # Obtener salvaciones de la clase
    salvaciones = compendio_pj.obtener_salvaciones_clase(clase)
    
    # Obtener rasgos raciales
    rasgos_raciales = compendio_pj.obtener_rasgos_raza(raza)
    
    pj = {
        "id": f"test_{nombre.lower()}",
        "info_basica": {
            "nombre": nombre,
            "raza": raza,
            "clase": clase,
            "nivel": nivel,
            "experiencia": 0,
        },
        "caracteristicas": caracteristicas,
        "competencias": {
            "salvaciones": salvaciones,
            "habilidades": [],
            "armaduras": [],
            "armas": [],
        },
        "rasgos": {
            "raciales": rasgos_raciales,
            "clase": [],
            "trasfondo": [],
        },
        "equipo": {
            "armas": [
                {
                    "id": "espada_larga_1",
                    "compendio_ref": "espada_larga",
                    "nombre": "Espada larga",
                    "equipada": True,
                }
            ],
            "armadura": {
                "id": "cota_malla_1",
                "compendio_ref": "cota_de_malla",
                "nombre": "Cota de malla",
                "equipada": True,
            },
            "escudo": {
                "id": "escudo_1",
                "compendio_ref": "escudo",
                "nombre": "Escudo",
                "equipada": True,
            },
        },
    }
    
    # Calcular derivados
    return recalcular_derivados(pj)
