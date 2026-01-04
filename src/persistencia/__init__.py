"""
Módulo de Persistencia
Gestiona el almacenamiento y recuperación de datos del juego.
"""

from .gestor import GestorPersistencia, obtener_gestor
from .compendio import Compendio, obtener_compendio

__all__ = [
    'GestorPersistencia',
    'obtener_gestor',
    'Compendio',
    'obtener_compendio'
]
