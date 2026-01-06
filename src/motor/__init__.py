"""
Motor de Reglas D&D 5e

Este módulo contiene toda la lógica de reglas del juego.

ESTRUCTURA:
- dados.py: Sistema de tiradas genéricas
- reglas_basicas.py: Modificadores, competencia, CA
- combate_utils.py: Ataque, daño, iniciativa, salvaciones
"""

# Desde dados.py
from .dados import (
    rng,
    GestorAleatorio,
    TipoTirada,
    ResultadoTirada,
    DADOS_VALIDOS,
    tirar,
    tirar_dado,
    tirar_dados,
    tirar_ventaja,
    tirar_desventaja,
    parsear_expresion,
)

# Desde reglas_basicas.py
from .reglas_basicas import (
    calcular_modificador,
    obtener_bonificador_competencia,
    calcular_cd_conjuros,
    calcular_bonificador_ataque_conjuros,
    calcular_ca_base,
    calcular_carga_maxima,
)

# Desde combate_utils.py
from .combate_utils import (
    tirar_ataque,
    tirar_daño,
    tirar_salvacion,
    tirar_habilidad,
    tirar_iniciativa,
    tirar_atributos,
    resolver_ataque,
)

__all__ = [
    # Gestor de aleatoriedad
    'rng',
    'GestorAleatorio',

    # Tipos
    'TipoTirada',
    'ResultadoTirada',
    'DADOS_VALIDOS',

    # Tiradas genéricas
    'tirar',
    'tirar_dado',
    'tirar_dados',
    'tirar_ventaja',
    'tirar_desventaja',
    'parsear_expresion',

    # Reglas básicas
    'calcular_modificador',
    'obtener_bonificador_competencia',
    'calcular_cd_conjuros',
    'calcular_bonificador_ataque_conjuros',
    'calcular_ca_base',
    'calcular_carga_maxima',

    # Combate
    'tirar_ataque',
    'tirar_daño',
    'tirar_salvacion',
    'tirar_habilidad',
    'tirar_iniciativa',
    'tirar_atributos',
    'resolver_ataque',
]
