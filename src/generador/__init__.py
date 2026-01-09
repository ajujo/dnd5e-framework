"""
Módulo generador de aventuras.

Incluye:
- Carga de módulos de tono
- Generación de Adventure Bible
- Gestión y actualización de biblias
"""

from .tonos import cargar_tono, listar_tonos, obtener_prompt_tono, obtener_balance_solitario
from .bible_manager import BibleManager, obtener_bible_manager

__all__ = [
    'cargar_tono', 
    'listar_tonos', 
    'obtener_prompt_tono', 
    'obtener_balance_solitario',
    'BibleManager',
    'obtener_bible_manager'
]
