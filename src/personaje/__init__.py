"""
Módulo de creación y gestión de personajes D&D 5e.

Componentes:
- compendio_pj: Datos de razas, clases, trasfondos
- calculador: Cálculo de valores derivados (HP, CA, mods)
- storage: Guardado y carga de personajes
- mapper: Conversión entre ficha y combatiente
- creador: Flujo de creación interactivo
"""

from .compendio_pj import (
    obtener_razas,
    obtener_clases,
    obtener_trasfondos,
    obtener_raza,
    obtener_clase,
    obtener_trasfondo,
    listar_razas,
    listar_clases,
    listar_trasfondos,
    STANDARD_ARRAY,
    CARACTERISTICAS,
    HABILIDADES,
)

from .calculador import (
    calcular_modificador,
    calcular_bonificador_competencia,
    calcular_hp_maximo,
    calcular_ca,
    calcular_salvaciones,
    aplicar_bonificadores_raza,
    recalcular_derivados,
    generar_resumen_derivados,
)

from .storage import (
    save_character,
    load_character,
    list_characters,
    delete_character,
    autosave_step,
    load_autosave,
    list_autosaves,
    generar_id,
)

from .mapper import (
    to_combatiente,
    from_combatiente,
    crear_pj_minimo_para_test,
)

__all__ = [
    # Compendio
    "obtener_razas",
    "obtener_clases",
    "obtener_trasfondos",
    "obtener_raza",
    "obtener_clase",
    "obtener_trasfondo",
    "listar_razas",
    "listar_clases",
    "listar_trasfondos",
    "STANDARD_ARRAY",
    "CARACTERISTICAS",
    "HABILIDADES",
    
    # Calculador
    "calcular_modificador",
    "calcular_bonificador_competencia",
    "calcular_hp_maximo",
    "calcular_ca",
    "calcular_salvaciones",
    "aplicar_bonificadores_raza",
    "recalcular_derivados",
    "generar_resumen_derivados",
    
    # Storage
    "save_character",
    "load_character",
    "list_characters",
    "delete_character",
    "autosave_step",
    "load_autosave",
    "list_autosaves",
    "generar_id",
    
    # Mapper
    "to_combatiente",
    "from_combatiente",
    "crear_pj_minimo_para_test",
]
