"""
Módulo generador de aventuras.

Incluye:
- Carga de módulos de tono
- Generación de Adventure Bible
- Gestión y actualización de biblias
"""

from .tonos import cargar_tono, listar_tonos, obtener_prompt_tono, obtener_balance_solitario
from .bible_manager import BibleManager, obtener_bible_manager
from .bible_generator import BibleGenerator, crear_bible_generator
from .prompts_bible import listar_regiones, obtener_info_region

__all__ = [
    # Tonos
    'cargar_tono', 
    'listar_tonos', 
    'obtener_prompt_tono', 
    'obtener_balance_solitario',
    # Bible Manager
    'BibleManager',
    'obtener_bible_manager',
    # Bible Generator
    'BibleGenerator',
    'crear_bible_generator',
    # Regiones
    'listar_regiones',
    'obtener_info_region'
]
