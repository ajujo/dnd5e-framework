"""
Calculador de Dificultad de Encuentros - D&D 5e

Implementa las reglas del DMG para calcular la dificultad de encuentros,
con ajustes especiales para grupos pequeños (1-2 PJs).
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class DificultadEncuentro(Enum):
    """Niveles de dificultad de encuentro."""
    TRIVIAL = "trivial"      # Por debajo de fácil
    FACIL = "fácil"
    MEDIO = "medio"
    DIFICIL = "difícil"
    LETAL = "letal"
    MORTAL = "mortal"        # Muy por encima de letal


# Umbrales de XP por nivel de personaje
# Fuente: DMG página 82
UMBRALES_XP = {
    1:  {"facil": 25,   "medio": 50,   "dificil": 75,   "letal": 100},
    2:  {"facil": 50,   "medio": 100,  "dificil": 150,  "letal": 200},
    3:  {"facil": 75,   "medio": 150,  "dificil": 225,  "letal": 400},
    4:  {"facil": 125,  "medio": 250,  "dificil": 375,  "letal": 500},
    5:  {"facil": 250,  "medio": 500,  "dificil": 750,  "letal": 1100},
    6:  {"facil": 300,  "medio": 600,  "dificil": 900,  "letal": 1400},
    7:  {"facil": 350,  "medio": 750,  "dificil": 1100, "letal": 1700},
    8:  {"facil": 450,  "medio": 900,  "dificil": 1400, "letal": 2100},
    9:  {"facil": 550,  "medio": 1100, "dificil": 1600, "letal": 2400},
    10: {"facil": 600,  "medio": 1200, "dificil": 1900, "letal": 2800},
    11: {"facil": 800,  "medio": 1600, "dificil": 2400, "letal": 3600},
    12: {"facil": 1000, "medio": 2000, "dificil": 3000, "letal": 4500},
    13: {"facil": 1100, "medio": 2200, "dificil": 3400, "letal": 5100},
    14: {"facil": 1250, "medio": 2500, "dificil": 3800, "letal": 5700},
    15: {"facil": 1400, "medio": 2800, "dificil": 4300, "letal": 6400},
    16: {"facil": 1600, "medio": 3200, "dificil": 4800, "letal": 7200},
    17: {"facil": 2000, "medio": 3900, "dificil": 5900, "letal": 8800},
    18: {"facil": 2100, "medio": 4200, "dificil": 6300, "letal": 9500},
    19: {"facil": 2400, "medio": 4900, "dificil": 7300, "letal": 10900},
    20: {"facil": 2800, "medio": 5700, "dificil": 8500, "letal": 12700},
}

# Multiplicadores por número de monstruos (grupo normal 3-5 PJs)
# Índice = número de monstruos, valor = multiplicador
MULTIPLICADORES_NORMAL = {
    1: 1.0,
    2: 1.5,
    3: 2.0,
    4: 2.0,
    5: 2.0,
    6: 2.0,
    7: 2.5,
    8: 2.5,
    9: 2.5,
    10: 2.5,
    11: 3.0,
    12: 3.0,
    13: 3.0,
    14: 3.0,
    15: 4.0,
}


def _obtener_multiplicador(num_monstruos: int, num_pjs: int) -> float:
    """
    Obtiene el multiplicador de XP según número de monstruos y tamaño del grupo.
    
    Ajuste DMG para grupos pequeños/grandes:
    - 1-2 PJs: subir un nivel el multiplicador
    - 3-5 PJs: normal
    - 6+ PJs: bajar un nivel el multiplicador
    """
    # Obtener multiplicador base
    if num_monstruos >= 15:
        mult_base = 4.0
    else:
        mult_base = MULTIPLICADORES_NORMAL.get(num_monstruos, 2.0)
    
    # Ajustar por tamaño de grupo
    multiplicadores_ordenados = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
    
    try:
        indice = multiplicadores_ordenados.index(mult_base)
    except ValueError:
        indice = 2  # Default a ×2
    
    if num_pjs <= 2:
        # Grupo pequeño: subir un nivel (más difícil)
        indice = min(indice + 1, len(multiplicadores_ordenados) - 1)
    elif num_pjs >= 6:
        # Grupo grande: bajar un nivel (más fácil)
        indice = max(indice - 1, 0)
    
    return multiplicadores_ordenados[indice]


def calcular_umbrales_grupo(nivel_promedio: int, num_pjs: int) -> Dict[str, int]:
    """
    Calcula los umbrales de XP para un grupo.
    
    Args:
        nivel_promedio: Nivel promedio de los PJs
        num_pjs: Número de PJs en el grupo
    
    Returns:
        Dict con umbrales {facil, medio, dificil, letal}
    """
    nivel = max(1, min(20, nivel_promedio))  # Limitar a 1-20
    umbrales_base = UMBRALES_XP[nivel]
    
    return {
        "facil": umbrales_base["facil"] * num_pjs,
        "medio": umbrales_base["medio"] * num_pjs,
        "dificil": umbrales_base["dificil"] * num_pjs,
        "letal": umbrales_base["letal"] * num_pjs,
    }


def calcular_xp_encuentro(monstruos: List[Dict[str, Any]], num_pjs: int) -> Tuple[int, int]:
    """
    Calcula el XP base y ajustado de un encuentro.
    
    Args:
        monstruos: Lista de dicts con al menos {"experiencia": int} o {"xp": int}
        num_pjs: Número de PJs
    
    Returns:
        Tuple (xp_base, xp_ajustado)
    """
    xp_base = sum(m.get("experiencia", m.get("xp", 0)) for m in monstruos)
    num_monstruos = len(monstruos)
    
    if num_monstruos == 0:
        return 0, 0
    
    multiplicador = _obtener_multiplicador(num_monstruos, num_pjs)
    xp_ajustado = int(xp_base * multiplicador)
    
    return xp_base, xp_ajustado


def determinar_dificultad(xp_ajustado: int, umbrales: Dict[str, int]) -> DificultadEncuentro:
    """
    Determina la dificultad según XP ajustado vs umbrales.
    """
    if xp_ajustado < umbrales["facil"] * 0.5:
        return DificultadEncuentro.TRIVIAL
    elif xp_ajustado < umbrales["facil"]:
        return DificultadEncuentro.TRIVIAL
    elif xp_ajustado < umbrales["medio"]:
        return DificultadEncuentro.FACIL
    elif xp_ajustado < umbrales["dificil"]:
        return DificultadEncuentro.MEDIO
    elif xp_ajustado < umbrales["letal"]:
        return DificultadEncuentro.DIFICIL
    elif xp_ajustado < umbrales["letal"] * 1.5:
        return DificultadEncuentro.LETAL
    else:
        return DificultadEncuentro.MORTAL


@dataclass
class ResultadoDificultad:
    """Resultado del cálculo de dificultad."""
    dificultad: DificultadEncuentro
    xp_base: int
    xp_ajustado: int
    multiplicador: float
    umbrales: Dict[str, int]
    num_monstruos: int
    num_pjs: int
    nivel_pj: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dificultad": self.dificultad.value,
            "xp_base": self.xp_base,
            "xp_ajustado": self.xp_ajustado,
            "multiplicador": self.multiplicador,
            "umbrales": self.umbrales,
            "num_monstruos": self.num_monstruos,
            "num_pjs": self.num_pjs,
            "nivel_pj": self.nivel_pj,
        }
    
    def descripcion(self) -> str:
        """Genera descripción legible del encuentro."""
        emoji = {
            DificultadEncuentro.TRIVIAL: "😴",
            DificultadEncuentro.FACIL: "🟢",
            DificultadEncuentro.MEDIO: "🟡",
            DificultadEncuentro.DIFICIL: "🟠",
            DificultadEncuentro.LETAL: "🔴",
            DificultadEncuentro.MORTAL: "💀",
        }
        return (
            f"{emoji.get(self.dificultad, '⚔️')} Encuentro {self.dificultad.value.upper()}\n"
            f"   XP: {self.xp_base} base × {self.multiplicador} = {self.xp_ajustado} ajustado\n"
            f"   Umbrales (nivel {self.nivel_pj}, {self.num_pjs} PJ): "
            f"Fácil {self.umbrales['facil']} | Medio {self.umbrales['medio']} | "
            f"Difícil {self.umbrales['dificil']} | Letal {self.umbrales['letal']}"
        )


def calcular_dificultad_encuentro(
    monstruos: List[Dict[str, Any]],
    nivel_pj: int = 1,
    num_pjs: int = 1
) -> ResultadoDificultad:
    """
    Calcula la dificultad completa de un encuentro.
    
    Args:
        monstruos: Lista de monstruos del encuentro.
                   Cada uno debe tener "experiencia" o "xp".
        nivel_pj: Nivel del personaje jugador (o promedio del grupo)
        num_pjs: Número de PJs (default 1 para juego en solitario)
    
    Returns:
        ResultadoDificultad con toda la información
    
    Ejemplo:
        >>> goblin = {"nombre": "Goblin", "experiencia": 50}
        >>> resultado = calcular_dificultad_encuentro([goblin], nivel_pj=1, num_pjs=1)
        >>> print(resultado.dificultad)
        DificultadEncuentro.DIFICIL
    """
    umbrales = calcular_umbrales_grupo(nivel_pj, num_pjs)
    xp_base, xp_ajustado = calcular_xp_encuentro(monstruos, num_pjs)
    multiplicador = _obtener_multiplicador(len(monstruos), num_pjs)
    dificultad = determinar_dificultad(xp_ajustado, umbrales)
    
    return ResultadoDificultad(
        dificultad=dificultad,
        xp_base=xp_base,
        xp_ajustado=xp_ajustado,
        multiplicador=multiplicador,
        umbrales=umbrales,
        num_monstruos=len(monstruos),
        num_pjs=num_pjs,
        nivel_pj=nivel_pj,
    )


def sugerir_encuentros_por_dificultad(
    nivel_pj: int,
    num_pjs: int = 1,
    dificultad_objetivo: DificultadEncuentro = DificultadEncuentro.MEDIO,
    monstruos_disponibles: List[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Sugiere composiciones de encuentros para una dificultad objetivo.
    
    Args:
        nivel_pj: Nivel del PJ
        num_pjs: Número de PJs
        dificultad_objetivo: Dificultad deseada
        monstruos_disponibles: Lista de monstruos para elegir
    
    Returns:
        Lista de sugerencias, cada una con {monstruos, dificultad_real}
    """
    umbrales = calcular_umbrales_grupo(nivel_pj, num_pjs)
    
    # Rango de XP objetivo
    rangos = {
        DificultadEncuentro.FACIL: (umbrales["facil"] * 0.5, umbrales["facil"]),
        DificultadEncuentro.MEDIO: (umbrales["facil"], umbrales["medio"]),
        DificultadEncuentro.DIFICIL: (umbrales["medio"], umbrales["dificil"]),
        DificultadEncuentro.LETAL: (umbrales["dificil"], umbrales["letal"]),
    }
    
    xp_min, xp_max = rangos.get(dificultad_objetivo, (umbrales["facil"], umbrales["medio"]))
    
    sugerencias = []
    
    if monstruos_disponibles:
        # Filtrar monstruos cuyo XP individual (con multiplicador ×1.5 para 1 PJ)
        # esté en el rango objetivo
        multiplicador_1 = _obtener_multiplicador(1, num_pjs)
        
        for m in monstruos_disponibles:
            xp = m.get("experiencia", m.get("xp", 0))
            xp_ajustado = xp * multiplicador_1
            
            if xp_min <= xp_ajustado <= xp_max:
                sugerencias.append({
                    "monstruos": [m],
                    "cantidad": 1,
                    "xp_ajustado": int(xp_ajustado),
                    "dificultad": dificultad_objetivo.value
                })
    
    return sugerencias[:10]  # Limitar a 10 sugerencias


# === UTILIDADES PARA EL LLM ===

def generar_prompt_encuentro(nivel_pj: int, num_pjs: int = 1) -> str:
    """
    Genera un prompt con las reglas de dificultad para que el LLM
    elija enemigos apropiados.
    """
    umbrales = calcular_umbrales_grupo(nivel_pj, num_pjs)
    mult_1 = _obtener_multiplicador(1, num_pjs)
    mult_2 = _obtener_multiplicador(2, num_pjs)
    mult_3 = _obtener_multiplicador(3, num_pjs)
    
    return f"""## Reglas de Dificultad de Encuentros (D&D 5e)

**Grupo**: {num_pjs} PJ(s) de nivel {nivel_pj}

### Umbrales de XP:
- Trivial: < {umbrales['facil']} XP
- Fácil: {umbrales['facil']} XP
- Medio: {umbrales['medio']} XP
- Difícil: {umbrales['dificil']} XP
- Letal: {umbrales['letal']} XP

### Multiplicadores por número de enemigos:
- 1 enemigo: ×{mult_1}
- 2 enemigos: ×{mult_2}
- 3+ enemigos: ×{mult_3}

### Ejemplos de CR apropiados para {num_pjs} PJ nivel {nivel_pj}:
- Encuentro Fácil: 1 monstruo de CR {max(0, nivel_pj - 2)} o menor
- Encuentro Medio: 1 monstruo de CR {max(0, nivel_pj - 1)}
- Encuentro Difícil: 1 monstruo de CR {nivel_pj}
- Encuentro Letal: 1 monstruo de CR {nivel_pj + 1} o 2 de CR {max(0, nivel_pj - 1)}

### IMPORTANTE:
- Para 1 PJ, evitar encuentros con 3+ enemigos (casi siempre letales)
- Preferir 1-2 enemigos para encuentros equilibrados
"""
