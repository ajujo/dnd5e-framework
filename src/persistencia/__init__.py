"""
Sistema de Persistencia D&D 5e

Gestión de guardado/carga de partidas y acceso al compendio.
"""

from .gestor import GestorPersistencia, obtener_gestor
from .compendio import Compendio, obtener_compendio

__all__ = [
    'GestorPersistencia',
    'obtener_gestor',
    'Compendio',
    'obtener_compendio',
]
