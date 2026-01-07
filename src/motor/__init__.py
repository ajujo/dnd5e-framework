"""
Motor de Reglas D&D 5e

ESTRUCTURA:
- dados.py: Sistema de tiradas genéricas
- reglas_basicas.py: Modificadores, competencia, CA
- combate_utils.py: Ataque, daño, iniciativa, salvaciones
- compendio.py: Interfaz con el compendio de datos
- validador.py: Validación de acciones
- normalizador.py: Normalización de texto a acciones
- vocabulario.py: Sinónimos y variantes de texto

PATRÓN DE INYECCIÓN:
- Los módulos internos reciben dependencias por constructor
- obtener_compendio_motor() solo debe usarse en main.py/cli.py

FLUJO DE ACCIONES:
Texto jugador → NormalizadorAcciones → ValidadorAcciones → Resolución
"""

from .dados import (
    rng, GestorAleatorio, TipoTirada, ResultadoTirada, DADOS_VALIDOS,
    tirar, tirar_dado, tirar_dados, tirar_ventaja, tirar_desventaja, parsear_expresion,
)

from .reglas_basicas import (
    calcular_modificador, obtener_bonificador_competencia,
    calcular_cd_conjuros, calcular_bonificador_ataque_conjuros,
    calcular_ca_base, calcular_carga_maxima,
)

from .combate_utils import (
    tirar_ataque, tirar_daño, tirar_salvacion, tirar_habilidad,
    tirar_iniciativa, tirar_atributos, resolver_ataque,
    resolver_ataque_completo,
    ResultadoAtaqueCompleto,
)

from .compendio import (
    CompendioMotor, obtener_compendio_motor, resetear_compendio_motor,
)

from .validador import (
    ValidadorAcciones, TipoAccion, ResultadoValidacion,
)

from .normalizador import (
    NormalizadorAcciones, TipoAccionNorm, AccionNormalizada, ContextoEscena,
)

from .vocabulario import (
    TipoIntencion,
    detectar_intencion_por_verbo,
    detectar_habilidad_por_verbo,
    detectar_accion_generica,
    es_ataque_desarmado,
    buscar_sinonimo_arma,
    VERBOS_INTENCION,
    VERBOS_HABILIDAD,
    SINONIMOS_ACCION_GENERICA,
    SINONIMOS_ARMA,
)

__all__ = [
    # Dados
    'rng', 'GestorAleatorio', 'TipoTirada', 'ResultadoTirada', 'DADOS_VALIDOS',
    'tirar', 'tirar_dado', 'tirar_dados', 'tirar_ventaja', 'tirar_desventaja', 'parsear_expresion',
    # Reglas
    'calcular_modificador', 'obtener_bonificador_competencia',
    'calcular_cd_conjuros', 'calcular_bonificador_ataque_conjuros',
    'calcular_ca_base', 'calcular_carga_maxima',
    # Combate
    'tirar_ataque', 'tirar_daño', 'tirar_salvacion', 'tirar_habilidad',
    'tirar_iniciativa', 'tirar_atributos', 'resolver_ataque',
    # Compendio
    'CompendioMotor', 'obtener_compendio_motor', 'resetear_compendio_motor',
    # Validador
    'ValidadorAcciones', 'TipoAccion', 'ResultadoValidacion',
    # Normalizador
    'NormalizadorAcciones', 'TipoAccionNorm', 'AccionNormalizada', 'ContextoEscena',
    # Vocabulario
    'TipoIntencion', 'detectar_intencion_por_verbo', 'detectar_habilidad_por_verbo',
    'detectar_accion_generica', 'es_ataque_desarmado', 'buscar_sinonimo_arma',
    'VERBOS_INTENCION', 'VERBOS_HABILIDAD', 'SINONIMOS_ACCION_GENERICA', 'SINONIMOS_ARMA',
]

# Pipeline de turno
from .pipeline_turno import (
    PipelineTurno,
    TipoResultado,
    ResultadoPipeline,
    Evento,
    OpcionClarificacion,
)

__all__ += [
    'PipelineTurno',
    'TipoResultado',
    'ResultadoPipeline',
    'Evento',
    'OpcionClarificacion',
]

# Gestor de combate
from .gestor_combate import (
    GestorCombate,
    Combatiente,
    TipoCombatiente,
    EstadoCombate,
    EstadoTurno,
)

__all__ += [
    'GestorCombate',
    'Combatiente',
    'TipoCombatiente',
    'EstadoCombate',
    'EstadoTurno',
]

# Narrador LLM
from .narrador import (
    NarradorLLM,
    ContextoNarracion,
    RespuestaNarrador,
    crear_contexto_narracion,
)

__all__ += [
    'NarradorLLM',
    'ContextoNarracion',
    'RespuestaNarrador',
    'crear_contexto_narracion',
]

# Narrador LLM
from .narrador import (
    NarradorLLM,
    ContextoNarracion,
    RespuestaNarrador,
    crear_contexto_narracion,
)

__all__ += [
    'NarradorLLM',
    'ContextoNarracion',
    'RespuestaNarrador',
    'crear_contexto_narracion',
]

# Ataque de monstruo
from .combate_utils import (
    ResultadoAtaqueMonstruo,
    resolver_ataque_monstruo,
)

__all__ += [
    'ResultadoAtaqueMonstruo',
    'resolver_ataque_monstruo',
]

# Utilidades
from .utils import normalizar_nombre

__all__ += ['normalizar_nombre']
