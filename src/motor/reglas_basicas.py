"""
Reglas Básicas de D&D 5e

Este módulo contiene los cálculos fundamentales de reglas:
- Modificadores de atributos
- Bonificador de competencia
- Otros cálculos derivados

No contiene lógica de tiradas (eso está en dados.py).
"""


def calcular_modificador(puntuacion: int) -> int:
    """
    Calcula el modificador a partir de una puntuación de atributo.

    Fórmula D&D 5e: (puntuación - 10) // 2

    Args:
        puntuacion: Puntuación del atributo (1-30).

    Returns:
        Modificador correspondiente (-5 a +10).

    Examples:
        >>> calcular_modificador(10)
        0
        >>> calcular_modificador(14)
        2
        >>> calcular_modificador(8)
        -1
    """
    return (puntuacion - 10) // 2


def obtener_bonificador_competencia(nivel: int) -> int:
    """
    Obtiene el bonificador de competencia según el nivel.

    Tabla D&D 5e:
    - Niveles 1-4: +2
    - Niveles 5-8: +3
    - Niveles 9-12: +4
    - Niveles 13-16: +5
    - Niveles 17-20: +6

    Args:
        nivel: Nivel del personaje (1-20).

    Returns:
        Bonificador de competencia (2-6).
    """
    if nivel < 1:
        return 2
    elif nivel <= 4:
        return 2
    elif nivel <= 8:
        return 3
    elif nivel <= 12:
        return 4
    elif nivel <= 16:
        return 5
    else:
        return 6


def calcular_cd_conjuros(modificador_caracteristica: int,
                         bonificador_competencia: int) -> int:
    """
    Calcula la CD (Clase de Dificultad) de conjuros.

    Fórmula D&D 5e: 8 + modificador de característica + bonificador de competencia

    Args:
        modificador_caracteristica: Modificador del atributo de lanzamiento.
        bonificador_competencia: Bonificador de competencia del personaje.

    Returns:
        CD de salvación de conjuros.
    """
    return 8 + modificador_caracteristica + bonificador_competencia


def calcular_bonificador_ataque_conjuros(modificador_caracteristica: int,
                                          bonificador_competencia: int) -> int:
    """
    Calcula el bonificador de ataque con conjuros.

    Fórmula D&D 5e: modificador de característica + bonificador de competencia

    Args:
        modificador_caracteristica: Modificador del atributo de lanzamiento.
        bonificador_competencia: Bonificador de competencia del personaje.

    Returns:
        Bonificador para tiradas de ataque con conjuros.
    """
    return modificador_caracteristica + bonificador_competencia


def calcular_ca_base(armadura: dict = None,
                     mod_destreza: int = 0,
                     escudo: bool = False) -> int:
    """
    Calcula la Clase de Armadura base.

    Args:
        armadura: Diccionario con datos de armadura o None (sin armadura).
        mod_destreza: Modificador de Destreza del personaje.
        escudo: True si lleva escudo equipado.

    Returns:
        Clase de Armadura total.

    Sin armadura: 10 + mod.DES
    Con armadura: ca_base + mod.DES (limitado) + escudo
    """
    if armadura is None:
        ca = 10 + mod_destreza
    else:
        ca_base = armadura.get("ca_base", 10)
        max_mod_des = armadura.get("max_mod_destreza", None)

        if max_mod_des is not None:
            mod_aplicable = min(mod_destreza, max_mod_des)
        else:
            mod_aplicable = mod_destreza

        ca = ca_base + mod_aplicable

    if escudo:
        ca += 2

    return ca


def calcular_carga_maxima(fuerza: int, en_libras: bool = True) -> float:
    """
    Calcula la capacidad de carga máxima.

    Fórmula D&D 5e: Fuerza × 15 (en libras)

    Args:
        fuerza: Puntuación de Fuerza.
        en_libras: Si True retorna en libras, si False en kg.

    Returns:
        Capacidad de carga máxima.
    """
    carga_lb = fuerza * 15

    if en_libras:
        return carga_lb
    else:
        return carga_lb * 0.453592
