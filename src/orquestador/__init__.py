"""
Orquestador del DM - Conecta el LLM con las herramientas.
"""

from .dm_cerebro import DMCerebro, SYSTEM_PROMPT_DM
from .contexto import GestorContexto, Ubicacion, NPC
from .parser_respuesta import parsear_respuesta, RespuestaLLM
from .combate_integrado import (
    OrquestadorCombate,
    EstadoCombateIntegrado,
    ResultadoCombate,
    TurnoInfo,
)

__all__ = [
    'DMCerebro',
    'GestorContexto',
    'Ubicacion',
    'NPC',
    'parsear_respuesta',
    'RespuestaLLM',
    'SYSTEM_PROMPT_DM',
    # Combate integrado
    'OrquestadorCombate',
    'EstadoCombateIntegrado',
    'ResultadoCombate',
    'TurnoInfo',
]

