"""
Motor de Reglas D&D 5e

Este módulo contiene toda la lógica de reglas del juego.

ESTRUCTURA ACTUAL (V1):
- dados.py: Sistema de tiradas + utilidades de reglas

TODO FUTURO (refactor):
- dados.py: Solo tiradas genéricas
- reglas_basicas.py: Modificadores, competencia
- combate_utils.py: Ataque, daño, iniciativa
"""

from .dados import (
    # Gestor de aleatoriedad
    rng,
    GestorAleatorio,

    # Tipos
    TipoTirada,
    ResultadoTirada,
    DADOS_VALIDOS,

    # Tiradas básicas
    tirar,
    tirar_dado,
    tirar_dados,
    tirar_ventaja,
    tirar_desventaja,
    parsear_expresion,

    # Tiradas específicas D&D
    tirar_ataque,
    tirar_daño,
    tirar_salvacion,
    tirar_habilidad,
    tirar_iniciativa,
    tirar_atributos,

    # Cálculos de reglas
    calcular_modificador,
    obtener_bonificador_competencia,
)

__all__ = [
    # Gestor de aleatoriedad
    'rng',
    'GestorAleatorio',

    # Tipos
    'TipoTirada',
    'ResultadoTirada',
    'DADOS_VALIDOS',

    # Tiradas básicas
    'tirar',
    'tirar_dado',
    'tirar_dados',
    'tirar_ventaja',
    'tirar_desventaja',
    'parsear_expresion',

    # Tiradas específicas D&D
    'tirar_ataque',
    'tirar_daño',
    'tirar_salvacion',
    'tirar_habilidad',
    'tirar_iniciativa',
    'tirar_atributos',

    # Cálculos de reglas
    'calcular_modificador',
    'obtener_bonificador_competencia',
]
