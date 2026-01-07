"""
Utilidades comunes para el motor de reglas.
"""

import re
import unicodedata


def normalizar_nombre(s: str) -> str:
    """
    Normaliza un nombre para comparación (slugify).
    
    Ejemplos:
        "Arco corto" -> "arco_corto"
        "Aliento ígneo" -> "aliento_igneo"
        "Mordisco (lobo)" -> "mordisco_lobo"
        "Espada larga +1" -> "espada_larga_1"
    """
    # Normalizar unicode (quitar tildes)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    # Minúsculas
    s = s.lower()
    # Reemplazar todo lo que no sea alfanumérico por _
    s = re.sub(r"[^a-z0-9]+", "_", s)
    # Quitar _ al inicio/final
    return s.strip("_")
