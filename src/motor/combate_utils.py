"""
Utilidades de Combate para D&D 5e

Este módulo contiene funciones para tiradas específicas de combate y acciones:
- Ataques
- Daño
- Salvaciones
- Habilidades
- Iniciativa
- Generación de atributos

Depende de:
- motor.dados para las tiradas genéricas
- motor.reglas_basicas para cálculos de reglas
"""

from typing import Dict, Any

from .dados import (
    tirar, tirar_dados, parsear_expresion,
    TipoTirada, ResultadoTirada
)


def tirar_ataque(bonificador_ataque: int,
                 tipo: TipoTirada = TipoTirada.NORMAL) -> ResultadoTirada:
    """
    Tira un ataque.

    NOTA: El resultado incluye flags critico/pifia.
    El motor de combate debe interpretar:
    - critico=True → doble dados de daño
    - pifia=True → fallo automático

    Args:
        bonificador_ataque: Bonificador total al ataque.
        tipo: Normal, ventaja o desventaja.

    Returns:
        ResultadoTirada con flags de crítico/pifia.
    """
    if bonificador_ataque >= 0:
        expresion = f"1d20+{bonificador_ataque}"
    else:
        expresion = f"1d20{bonificador_ataque}"
    return tirar(expresion, tipo)


def tirar_daño(expresion_daño: str, critico: bool = False) -> ResultadoTirada:
    """
    Tira daño, duplicando dados en caso de crítico.

    Regla D&D 5e: En crítico se duplican los DADOS, no el modificador.

    Args:
        expresion_daño: Expresión de daño (ej: "2d6+3").
        critico: Si True, duplica los dados.

    Returns:
        ResultadoTirada con el daño total.
    """
    cantidad, caras, modificador = parsear_expresion(expresion_daño)

    if critico:
        cantidad *= 2

    nueva_expresion = f"{cantidad}d{caras}"
    if modificador > 0:
        nueva_expresion += f"+{modificador}"
    elif modificador < 0:
        nueva_expresion += str(modificador)

    return tirar(nueva_expresion)


def tirar_salvacion(modificador_salvacion: int,
                    tipo: TipoTirada = TipoTirada.NORMAL) -> ResultadoTirada:
    """
    Tira una tirada de salvación.

    NOTA: Los flags critico/pifia se marcan pero en RAW D&D 5e
    las salvaciones NO tienen crítico/pifia automático.

    Args:
        modificador_salvacion: Modificador total a la salvación.
        tipo: Normal, ventaja o desventaja.

    Returns:
        ResultadoTirada para comparar contra CD.
    """
    if modificador_salvacion >= 0:
        expresion = f"1d20+{modificador_salvacion}"
    else:
        expresion = f"1d20{modificador_salvacion}"
    return tirar(expresion, tipo)


def tirar_habilidad(modificador_habilidad: int,
                    tipo: TipoTirada = TipoTirada.NORMAL) -> ResultadoTirada:
    """
    Tira una prueba de habilidad.

    NOTA: Los flags critico/pifia se marcan pero en RAW D&D 5e
    las pruebas de habilidad NO tienen crítico/pifia automático.

    Args:
        modificador_habilidad: Modificador total a la habilidad.
        tipo: Normal, ventaja o desventaja.

    Returns:
        ResultadoTirada para comparar contra CD.
    """
    if modificador_habilidad >= 0:
        expresion = f"1d20+{modificador_habilidad}"
    else:
        expresion = f"1d20{modificador_habilidad}"
    return tirar(expresion, tipo)


def tirar_iniciativa(modificador_destreza: int,
                     otros_bonus: int = 0,
                     tipo: TipoTirada = TipoTirada.NORMAL) -> ResultadoTirada:
    """
    Tira iniciativa para un combatiente.

    Args:
        modificador_destreza: Modificador de Destreza del combatiente.
        otros_bonus: Otros bonificadores (rasgos, objetos, etc.).
        tipo: Normal, ventaja o desventaja.

    Returns:
        ResultadoTirada con el valor de iniciativa.
    """
    mod_total = modificador_destreza + otros_bonus
    if mod_total >= 0:
        expresion = f"1d20+{mod_total}"
    else:
        expresion = f"1d20{mod_total}"
    return tirar(expresion, tipo)


def tirar_atributos(metodo: str = "4d6_drop_lowest") -> Dict[str, Any]:
    """
    Genera los 6 atributos de un personaje.

    Args:
        metodo: Método de generación.
            - "4d6_drop_lowest": Tira 4d6, descarta el menor (estándar PHB).
            - "3d6": Tira 3d6 (clásico).
            - "standard_array": Usa array estándar [15,14,13,12,10,8].

    Returns:
        Diccionario con valores y método usado.
    """
    if metodo == "standard_array":
        valores = [15, 14, 13, 12, 10, 8]
    elif metodo == "3d6":
        valores = [sum(tirar_dados(3, 6)) for _ in range(6)]
    elif metodo == "4d6_drop_lowest":
        valores = []
        for _ in range(6):
            dados = tirar_dados(4, 6)
            dados.sort()
            valores.append(sum(dados[1:]))
    else:
        raise ValueError(f"Método desconocido: {metodo}")

    return {
        "valores": sorted(valores, reverse=True),
        "metodo": metodo
    }


def resolver_ataque(tirada_ataque: ResultadoTirada,
                    ca_objetivo: int) -> Dict[str, Any]:
    """
    Resuelve si un ataque impacta.

    Args:
        tirada_ataque: Resultado de tirar_ataque().
        ca_objetivo: Clase de Armadura del objetivo.

    Returns:
        Diccionario con resultado del ataque.
    """
    # Pifia siempre falla
    if tirada_ataque.pifia:
        return {
            "impacta": False,
            "critico": False,
            "pifia": True,
            "razon": "Pifia (1 natural)"
        }

    # Crítico siempre impacta
    if tirada_ataque.critico:
        return {
            "impacta": True,
            "critico": True,
            "pifia": False,
            "razon": "Crítico (20 natural)"
        }

    # Comparar contra CA
    impacta = tirada_ataque.total >= ca_objetivo
    return {
        "impacta": impacta,
        "critico": False,
        "pifia": False,
        "razon": f"Total {tirada_ataque.total} vs CA {ca_objetivo}"
    }
