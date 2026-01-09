"""
Sistema de herramientas para el LLM.

Las herramientas se registran automáticamente al importar sus módulos.
"""

# Importar todos los módulos de herramientas para que se registren
from . import consultas
from . import tiradas
from . import estado
from . import combate  # Añadido

# Exponer el registro y funciones útiles
from .registro import obtener_registro, registrar_herramienta, RegistroHerramientas
from .herramienta_base import Herramienta


def listar_herramientas():
    """Lista todas las herramientas registradas."""
    return obtener_registro().listar()


def ejecutar_herramienta(nombre: str, contexto: dict, **kwargs):
    """Ejecuta una herramienta por nombre."""
    return obtener_registro().ejecutar(nombre, contexto, **kwargs)


def documentacion_herramientas():
    """Genera documentación para el prompt del LLM."""
    return obtener_registro().generar_documentacion_llm()
