"""
Compendio de datos para creación de personajes D&D 5e.

Carga y proporciona acceso a razas, clases y trasfondos desde JSON.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


# Rutas a los archivos de datos
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "personajes"
RAZAS_FILE = DATA_DIR / "razas.json"
CLASES_FILE = DATA_DIR / "clases.json"
TRASFONDOS_FILE = DATA_DIR / "trasfondos.json"

# Cache de datos cargados
_razas: Optional[Dict[str, Any]] = None
_clases: Optional[Dict[str, Any]] = None
_trasfondos: Optional[Dict[str, Any]] = None


def _cargar_json(filepath: Path) -> Dict[str, Any]:
    """Carga un archivo JSON."""
    if not filepath.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def obtener_razas() -> Dict[str, Any]:
    """Obtiene el diccionario completo de razas."""
    global _razas
    if _razas is None:
        _razas = _cargar_json(RAZAS_FILE)
    return _razas


def obtener_clases() -> Dict[str, Any]:
    """Obtiene el diccionario completo de clases."""
    global _clases
    if _clases is None:
        _clases = _cargar_json(CLASES_FILE)
    return _clases


def obtener_trasfondos() -> Dict[str, Any]:
    """Obtiene el diccionario completo de trasfondos."""
    global _trasfondos
    if _trasfondos is None:
        _trasfondos = _cargar_json(TRASFONDOS_FILE)
    return _trasfondos


def obtener_raza(id_raza: str) -> Optional[Dict[str, Any]]:
    """Obtiene una raza por su ID."""
    razas = obtener_razas()
    return razas.get(id_raza)


def obtener_clase(id_clase: str) -> Optional[Dict[str, Any]]:
    """Obtiene una clase por su ID."""
    clases = obtener_clases()
    return clases.get(id_clase)


def obtener_trasfondo(id_trasfondo: str) -> Optional[Dict[str, Any]]:
    """Obtiene un trasfondo por su ID."""
    trasfondos = obtener_trasfondos()
    return trasfondos.get(id_trasfondo)


def listar_razas() -> List[Dict[str, str]]:
    """Lista todas las razas disponibles con id y nombre."""
    razas = obtener_razas()
    return [
        {"id": id_raza, "nombre": data["nombre"], "descripcion": data.get("descripcion", "")}
        for id_raza, data in razas.items()
    ]


def listar_clases() -> List[Dict[str, str]]:
    """Lista todas las clases disponibles con id y nombre."""
    clases = obtener_clases()
    return [
        {"id": id_clase, "nombre": data["nombre"], "descripcion": data.get("descripcion", "")}
        for id_clase, data in clases.items()
    ]


def listar_trasfondos() -> List[Dict[str, str]]:
    """Lista todos los trasfondos disponibles con id y nombre."""
    trasfondos = obtener_trasfondos()
    return [
        {"id": id_trasfondo, "nombre": data["nombre"], "descripcion": data.get("descripcion", "")}
        for id_trasfondo, data in trasfondos.items()
    ]


def obtener_nombres_raza(id_raza: str, genero: str = "masculino") -> List[str]:
    """
    Obtiene la lista de nombres sugeridos para una raza.
    
    Args:
        id_raza: ID de la raza
        genero: "masculino" o "femenino"
        
    Returns:
        Lista de nombres
    """
    raza = obtener_raza(id_raza)
    if not raza:
        return []
    
    if genero == "masculino":
        return raza.get("nombres_masculinos", [])
    else:
        return raza.get("nombres_femeninos", [])


def obtener_nombres_familia_raza(id_raza: str) -> List[str]:
    """Obtiene la lista de apellidos/clan para una raza."""
    raza = obtener_raza(id_raza)
    if not raza:
        return []
    
    # Diferentes razas usan diferentes campos
    return (
        raza.get("nombres_familia", []) or 
        raza.get("nombres_clan", []) or 
        []
    )


def obtener_bonificadores_raza(id_raza: str) -> Dict[str, int]:
    """Obtiene los bonificadores de característica de una raza."""
    raza = obtener_raza(id_raza)
    if not raza:
        return {}
    return raza.get("bonificadores", {})


def obtener_rasgos_raza(id_raza: str) -> List[Dict[str, Any]]:
    """Obtiene los rasgos raciales."""
    raza = obtener_raza(id_raza)
    if not raza:
        return []
    return raza.get("rasgos", [])


def obtener_competencias_clase(id_clase: str) -> Dict[str, List[str]]:
    """Obtiene las competencias otorgadas por una clase."""
    clase = obtener_clase(id_clase)
    if not clase:
        return {}
    return clase.get("competencias", {})


def obtener_salvaciones_clase(id_clase: str) -> List[str]:
    """Obtiene las salvaciones competentes de una clase."""
    clase = obtener_clase(id_clase)
    if not clase:
        return []
    return clase.get("salvaciones", [])


def obtener_dado_golpe_clase(id_clase: str) -> str:
    """Obtiene el dado de golpe de una clase."""
    clase = obtener_clase(id_clase)
    if not clase:
        return "d8"
    return clase.get("dado_golpe", "d8")


def obtener_hp_nivel_1_clase(id_clase: str) -> int:
    """Obtiene los HP base de nivel 1 de una clase."""
    clase = obtener_clase(id_clase)
    if not clase:
        return 8
    return clase.get("hp_nivel_1", 8)


def obtener_habilidades_elegir_clase(id_clase: str) -> Dict[str, Any]:
    """Obtiene las opciones de habilidades a elegir de una clase."""
    clase = obtener_clase(id_clase)
    if not clase:
        return {"cantidad": 0, "opciones": []}
    return clase.get("habilidades_elegir", {"cantidad": 0, "opciones": []})


def obtener_rasgos_nivel_1_clase(id_clase: str) -> List[Dict[str, Any]]:
    """Obtiene los rasgos de nivel 1 de una clase."""
    clase = obtener_clase(id_clase)
    if not clase:
        return []
    return clase.get("rasgos_nivel_1", [])


def obtener_sugerencia_atributos_clase(id_clase: str) -> List[str]:
    """Obtiene el orden sugerido de atributos para una clase."""
    clase = obtener_clase(id_clase)
    if not clase:
        return ["fuerza", "destreza", "constitucion", "inteligencia", "sabiduria", "carisma"]
    return clase.get("sugerencia_atributos", [])


def obtener_competencias_trasfondo(id_trasfondo: str) -> Dict[str, Any]:
    """Obtiene las competencias otorgadas por un trasfondo."""
    trasfondo = obtener_trasfondo(id_trasfondo)
    if not trasfondo:
        return {}
    
    return {
        "habilidades": trasfondo.get("competencias_habilidades", []),
        "herramientas": trasfondo.get("competencias_herramientas", []),
        "idiomas_extra": trasfondo.get("idiomas_extra", 0),
    }


def obtener_rasgo_trasfondo(id_trasfondo: str) -> Optional[Dict[str, str]]:
    """Obtiene el rasgo especial del trasfondo."""
    trasfondo = obtener_trasfondo(id_trasfondo)
    if not trasfondo:
        return None
    return trasfondo.get("rasgo")


def obtener_personalidad_trasfondo(id_trasfondo: str) -> Dict[str, List]:
    """Obtiene las opciones de personalidad del trasfondo."""
    trasfondo = obtener_trasfondo(id_trasfondo)
    if not trasfondo:
        return {}
    
    return {
        "rasgos_personalidad": trasfondo.get("rasgos_personalidad", []),
        "ideales": trasfondo.get("ideales", []),
        "vinculos": trasfondo.get("vinculos", []),
        "defectos": trasfondo.get("defectos", []),
    }


# Constantes útiles
STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

CARACTERISTICAS = [
    "fuerza", "destreza", "constitucion", 
    "inteligencia", "sabiduria", "carisma"
]

HABILIDADES = {
    "acrobacias": "destreza",
    "arcano": "inteligencia",
    "atletismo": "fuerza",
    "averiguar_intenciones": "sabiduria",
    "engano": "carisma",
    "historia": "inteligencia",
    "interpretacion": "carisma",
    "intimidacion": "carisma",
    "investigacion": "inteligencia",
    "juego_manos": "destreza",
    "medicina": "sabiduria",
    "naturaleza": "inteligencia",
    "percepcion": "sabiduria",
    "persuasion": "carisma",
    "religion": "inteligencia",
    "sigilo": "destreza",
    "supervivencia": "sabiduria",
    "trato_animales": "sabiduria",
}

IDIOMAS_COMUNES = [
    "comun", "enano", "elfico", "gigante", 
    "gnomico", "goblin", "mediano", "orco"
]

IDIOMAS_EXOTICOS = [
    "abisal", "celestial", "draconico", "habla_profunda",
    "infernal", "primordial", "silvano", "infracomun"
]


def refrescar_cache():
    """Recarga todos los datos desde los archivos JSON."""
    global _razas, _clases, _trasfondos
    _razas = None
    _clases = None
    _trasfondos = None
