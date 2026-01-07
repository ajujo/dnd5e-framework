"""
Vocabulario de Sinónimos para D&D 5e

Este módulo centraliza todos los sinónimos y variantes de texto
que el normalizador usa para detectar intenciones y entidades.

MANTENIMIENTO:
- Para añadir un nuevo sinónimo, solo hay que añadirlo al diccionario correspondiente
- Los patrones regex se generan automáticamente desde estos diccionarios
- No es necesario modificar el normalizador

ESTRUCTURA:
- SINONIMOS_INTENCION: verbo/frase → tipo de acción
- SINONIMOS_HABILIDAD: verbo/frase → habilidad específica
- SINONIMOS_ACCION: verbo/frase → acción genérica (dash, dodge, etc.)
- SINONIMOS_ARMA: término coloquial → id del compendio
"""

import re
from typing import Dict, List, Set, Optional, Tuple
from enum import Enum


# =============================================================================
# SINÓNIMOS DE INTENCIÓN (qué tipo de acción quiere hacer)
# =============================================================================

class TipoIntencion(Enum):
    ATAQUE = "ataque"
    CONJURO = "conjuro"
    MOVIMIENTO = "movimiento"
    HABILIDAD = "habilidad"
    ACCION = "accion"
    OBJETO = "objeto"


# Verbos/frases que indican cada tipo de intención
# Clave: palabra o frase, Valor: tipo de intención
VERBOS_INTENCION: Dict[str, TipoIntencion] = {
    # Ataque
    "ataco": TipoIntencion.ATAQUE,
    "atacar": TipoIntencion.ATAQUE,
    "ataque": TipoIntencion.ATAQUE,
    "golpeo": TipoIntencion.ATAQUE,
    "golpear": TipoIntencion.ATAQUE,
    "pego": TipoIntencion.ATAQUE,
    "pegar": TipoIntencion.ATAQUE,
    "disparo": TipoIntencion.ATAQUE,
    "disparar": TipoIntencion.ATAQUE,
    "corto": TipoIntencion.ATAQUE,
    "cortar": TipoIntencion.ATAQUE,
    "apuñalo": TipoIntencion.ATAQUE,
    "apuñalar": TipoIntencion.ATAQUE,
    "hiero": TipoIntencion.ATAQUE,
    "herir": TipoIntencion.ATAQUE,
    
    # Movimiento
    "muevo": TipoIntencion.MOVIMIENTO,
    "moverme": TipoIntencion.MOVIMIENTO,
    "mover": TipoIntencion.MOVIMIENTO,
    "camino": TipoIntencion.MOVIMIENTO,
    "caminar": TipoIntencion.MOVIMIENTO,
    "corro": TipoIntencion.MOVIMIENTO,
    "correr": TipoIntencion.MOVIMIENTO,
    "acerco": TipoIntencion.MOVIMIENTO,
    "acercarme": TipoIntencion.MOVIMIENTO,
    "alejo": TipoIntencion.MOVIMIENTO,
    "alejarme": TipoIntencion.MOVIMIENTO,
    "desplazo": TipoIntencion.MOVIMIENTO,
    "desplazarme": TipoIntencion.MOVIMIENTO,
    "voy": TipoIntencion.MOVIMIENTO,
    "ir": TipoIntencion.MOVIMIENTO,
    "avanzo": TipoIntencion.MOVIMIENTO,
    "avanzar": TipoIntencion.MOVIMIENTO,
    "retrocedo": TipoIntencion.MOVIMIENTO,
    "retroceder": TipoIntencion.MOVIMIENTO,
    
    # Conjuro (verbos genéricos, los específicos se detectan por nombre)
    "conjuro": TipoIntencion.CONJURO,
    "conjurar": TipoIntencion.CONJURO,
    "hechizo": TipoIntencion.CONJURO,
    "magia": TipoIntencion.CONJURO,
    
    # Habilidad (verbos que implican pruebas)
    "escucho": TipoIntencion.HABILIDAD,
    "escuchar": TipoIntencion.HABILIDAD,
    "oigo": TipoIntencion.HABILIDAD,
    "oir": TipoIntencion.HABILIDAD,
    "miro": TipoIntencion.HABILIDAD,
    "mirar": TipoIntencion.HABILIDAD,
    "busco": TipoIntencion.HABILIDAD,
    "buscar": TipoIntencion.HABILIDAD,
    "examino": TipoIntencion.HABILIDAD,
    "examinar": TipoIntencion.HABILIDAD,
    "investigo": TipoIntencion.HABILIDAD,
    "investigar": TipoIntencion.HABILIDAD,
    "persuado": TipoIntencion.HABILIDAD,
    "persuadir": TipoIntencion.HABILIDAD,
    "persuadirlo": TipoIntencion.HABILIDAD,
    "convenzo": TipoIntencion.HABILIDAD,
    "convencer": TipoIntencion.HABILIDAD,
    "intimido": TipoIntencion.HABILIDAD,
    "intimidar": TipoIntencion.HABILIDAD,
    "amenazo": TipoIntencion.HABILIDAD,
    "amenazar": TipoIntencion.HABILIDAD,
    "miento": TipoIntencion.HABILIDAD,
    "mentir": TipoIntencion.HABILIDAD,
    "engaño": TipoIntencion.HABILIDAD,
    "engañar": TipoIntencion.HABILIDAD,
    "trepo": TipoIntencion.HABILIDAD,
    "trepar": TipoIntencion.HABILIDAD,
    "escalo": TipoIntencion.HABILIDAD,
    "escalar": TipoIntencion.HABILIDAD,
    "salto": TipoIntencion.HABILIDAD,
    "saltar": TipoIntencion.HABILIDAD,
    "nado": TipoIntencion.HABILIDAD,
    "nadar": TipoIntencion.HABILIDAD,
    
    # Objeto
    "bebo": TipoIntencion.OBJETO,
    "beber": TipoIntencion.OBJETO,
    "tomo": TipoIntencion.OBJETO,
    "tomar": TipoIntencion.OBJETO,
}


# =============================================================================
# SINÓNIMOS DE HABILIDAD (qué habilidad específica)
# =============================================================================

# Verbo/frase → habilidad de D&D 5e
VERBOS_HABILIDAD: Dict[str, str] = {
    # Percepción
    "escucho": "percepcion",
    "escuchar": "percepcion",
    "oigo": "percepcion",
    "oir": "percepcion",
    "miro": "percepcion",
    "mirar": "percepcion",
    "observo": "percepcion",
    "observar": "percepcion",
    "vigilo": "percepcion",
    "vigilar": "percepcion",
    "oteo": "percepcion",
    "otear": "percepcion",
    
    # Investigación
    "investigo": "investigacion",
    "investigar": "investigacion",
    "examino": "investigacion",
    "examinar": "investigacion",
    "analizo": "investigacion",
    "analizar": "investigacion",
    "estudio": "investigacion",
    "estudiar": "investigacion",
    "inspecciono": "investigacion",
    "inspeccionar": "investigacion",
    
    # Sigilo
    "escondo": "sigilo",
    "esconderme": "sigilo",
    "oculto": "sigilo",
    "ocultarme": "sigilo",
    "sigiloso": "sigilo",
    "sigilosamente": "sigilo",
    
    # Atletismo
    "trepo": "atletismo",
    "trepar": "atletismo",
    "escalo": "atletismo",
    "escalar": "atletismo",
    "salto": "atletismo",
    "saltar": "atletismo",
    "nado": "atletismo",
    "nadar": "atletismo",
    "empujo": "atletismo",
    "empujar": "atletismo",
    "forcejeo": "atletismo",
    "forcejear": "atletismo",
    
    # Acrobacias
    "ruedo": "acrobacias",
    "rodar": "acrobacias",
    "voltereta": "acrobacias",
    "equilibrio": "acrobacias",
    "equilibrarme": "acrobacias",
    "pirueta": "acrobacias",
    
    # Persuasión
    "persuado": "persuasion",
    "persuadir": "persuasion",
    "persuadirlo": "persuasion",
    "convenzo": "persuasion",
    "convencer": "persuasion",
    "negocio": "persuasion",
    "negociar": "persuasion",
    "regateo": "persuasion",
    "regatear": "persuasion",
    "halago": "persuasion",
    "halagar": "persuasion",
    
    # Engaño
    "miento": "engaño",
    "mentir": "engaño",
    "engaño": "engaño",
    "engañar": "engaño",
    "finjo": "engaño",
    "fingir": "engaño",
    "faroleo": "engaño",
    "farolear": "engaño",
    "timo": "engaño",
    "timar": "engaño",
    
    # Intimidación
    "intimido": "intimidacion",
    "intimidar": "intimidacion",
    "amenazo": "intimidacion",
    "amenazar": "intimidacion",
    "asusto": "intimidacion",
    "asustar": "intimidacion",
    "aterrorizo": "intimidacion",
    "aterrorizar": "intimidacion",
    
    # Medicina
    "curo": "medicina",
    "curar": "medicina",
    "estabilizo": "medicina",
    "estabilizar": "medicina",
    "diagnostico": "medicina",
    "diagnosticar": "medicina",
    "vendo": "medicina",
    "vendar": "medicina",
    
    # Supervivencia
    "rastro": "supervivencia",
    "rastrear": "supervivencia",
    "sigo": "supervivencia",
    "seguir": "supervivencia",
    "cazo": "supervivencia",
    "cazar": "supervivencia",
    "forrajeo": "supervivencia",
    "forrajear": "supervivencia",
    
    # Trato con animales
    "amanso": "trato_animales",
    "amansar": "trato_animales",
    "domestico": "trato_animales",
    "domesticar": "trato_animales",
    "calmo": "trato_animales",
    "calmar": "trato_animales",
}


# =============================================================================
# SINÓNIMOS DE ACCIONES GENÉRICAS (Dash, Dodge, etc.)
# =============================================================================

# Término → acción genérica de D&D
SINONIMOS_ACCION_GENERICA: Dict[str, str] = {
    # Dash
    "dash": "dash",
    "carrera": "dash",
    "sprint": "dash",
    "correr rápido": "dash",
    "correr rapido": "dash",
    "corro todo lo que puedo": "dash",
    
    # Dodge
    "dodge": "dodge",
    "esquivar": "dodge",
    "esquiva": "dodge",
    "esquivo": "dodge",
    "evadir": "dodge",
    "me pongo a esquivar": "dodge",
    "preparo para esquivar": "dodge",
    
    # Disengage
    "disengage": "disengage",
    "desenganche": "disengage",
    "retirada": "disengage",
    "retirarse": "disengage",
    "retirarme": "disengage",
    "me retiro": "disengage",
    "retrocedo sin provocar": "disengage",
    
    # Help
    "help": "help",
    "ayudar": "help",
    "ayuda": "help",
    "ayudo": "help",
    "asistir": "help",
    "asisto": "help",
    "echo una mano": "help",
    
    # Hide
    "hide": "hide",
    "esconder": "hide",
    "esconderse": "hide",
    "esconderme": "hide",
    "me escondo": "hide",
    "ocultar": "hide",
    "ocultarme": "hide",
    "me oculto": "hide",
    
    # Search
    "search": "search",
    "buscar": "search",
    "registrar": "search",
    "registro": "search",
    
    # Ready
    "ready": "ready",
    "preparar": "ready",
    "preparo": "ready",
    "preparar acción": "ready",
    "preparar accion": "ready",
    "preparo una acción": "ready",
}


# =============================================================================
# SINÓNIMOS DE ARMAS
# =============================================================================

# Término coloquial → id del compendio
SINONIMOS_ARMA: Dict[str, List[str]] = {
    "espada": ["espada_larga", "espada_corta"],
    "espadón": ["espada_larga"],
    "sable": ["espada_corta"],
    "daga": ["daga"],
    "cuchillo": ["daga"],
    "puñal": ["daga"],
    "maza": ["maza"],
    "martillo": ["maza"],
    "hacha": ["hacha_mano"],
    "arco": ["arco_corto"],
    "ballesta": ["ballesta_ligera"],
    "bastón": ["baston"],
    "vara": ["baston"],
    "palo": ["baston"],
}

# Términos que indican ataque desarmado
TERMINOS_DESARMADO: Set[str] = {
    "desarmado", "puño", "puñetazo", "patada", "cabezazo",
    "golpe", "mano", "codo", "rodilla", "sin arma"
}


# =============================================================================
# FUNCIONES DE AYUDA
# =============================================================================

def generar_patron_intencion(tipo: TipoIntencion) -> str:
    """
    Genera un patrón regex para detectar una intención específica.
    
    Args:
        tipo: El tipo de intención a buscar.
        
    Returns:
        Patrón regex compilable.
    """
    verbos = [v for v, t in VERBOS_INTENCION.items() if t == tipo]
    if not verbos:
        return r"(?!)"  # Patrón que nunca matchea
    return r'\b(' + '|'.join(re.escape(v) for v in verbos) + r')\b'


def detectar_intencion_por_verbo(texto: str) -> Optional[TipoIntencion]:
    """
    Detecta la intención basándose en verbos del texto.
    
    Args:
        texto: Texto normalizado (minúsculas).
        
    Returns:
        TipoIntencion si se detecta, None si no.
    """
    texto_lower = texto.lower()
    for verbo, tipo in VERBOS_INTENCION.items():
        if re.search(r'\b' + re.escape(verbo) + r'\b', texto_lower):
            return tipo
    return None


def detectar_habilidad_por_verbo(texto: str) -> Optional[str]:
    """
    Detecta la habilidad específica basándose en verbos.
    
    Args:
        texto: Texto normalizado.
        
    Returns:
        Nombre de habilidad o None.
    """
    texto_lower = texto.lower()
    for verbo, habilidad in VERBOS_HABILIDAD.items():
        if re.search(r'\b' + re.escape(verbo) + r'\b', texto_lower):
            return habilidad
    return None


def detectar_accion_generica(texto: str) -> Optional[str]:
    """
    Detecta una acción genérica en el texto.
    
    Args:
        texto: Texto normalizado.
        
    Returns:
        ID de acción (dash, dodge, etc.) o None.
    """
    texto_lower = texto.lower()
    for termino, accion in SINONIMOS_ACCION_GENERICA.items():
        if termino in texto_lower:
            return accion
    return None


def es_ataque_desarmado(texto: str) -> bool:
    """
    Detecta si el texto indica un ataque desarmado.
    
    Args:
        texto: Texto normalizado.
        
    Returns:
        True si es ataque desarmado.
    """
    texto_lower = texto.lower()
    for termino in TERMINOS_DESARMADO:
        if termino in texto_lower:
            return True
    return False


def buscar_sinonimo_arma(texto: str) -> Optional[str]:
    """
    Busca sinónimos de armas en el texto.
    
    Args:
        texto: Texto normalizado.
        
    Returns:
        ID del arma en el compendio o None.
    """
    texto_lower = texto.lower()
    for sinonimo, ids in SINONIMOS_ARMA.items():
        if sinonimo in texto_lower:
            return ids[0]  # Retorna el primero por defecto
    return None
