"""
Clase base para todas las herramientas del sistema.

Cada herramienta es una función que el LLM puede invocar.
Define una interfaz común para registro, documentación y ejecución.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Herramienta(ABC):
    """Clase base abstracta para herramientas."""
    
    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre único de la herramienta (usado por el LLM)."""
        pass
    
    @property
    @abstractmethod
    def descripcion(self) -> str:
        """Descripción breve de qué hace (para el prompt del LLM)."""
        pass
    
    @property
    @abstractmethod
    def parametros(self) -> Dict[str, Dict[str, Any]]:
        """
        Define los parámetros que acepta.
        
        Formato:
        {
            "nombre_param": {
                "tipo": "string|int|float|bool|list",
                "descripcion": "Para qué sirve",
                "requerido": True/False,
                "opciones": ["op1", "op2"]  # opcional, si hay valores fijos
            }
        }
        """
        pass
    
    @abstractmethod
    def ejecutar(self, contexto: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Ejecuta la herramienta.
        
        Args:
            contexto: Estado actual del juego (pj, ubicacion, npcs, etc.)
            **kwargs: Parámetros específicos de la herramienta
            
        Returns:
            Dict con el resultado (siempre incluye "exito" y "mensaje")
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la herramienta a diccionario para el prompt del LLM."""
        return {
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "parametros": self.parametros
        }
    
    def validar_parametros(self, **kwargs) -> tuple[bool, str]:
        """Valida que los parámetros requeridos estén presentes."""
        for nombre, config in self.parametros.items():
            if config.get("requerido", False) and nombre not in kwargs:
                return False, f"Parámetro requerido '{nombre}' no proporcionado"
            
            if nombre in kwargs and "opciones" in config:
                if kwargs[nombre] not in config["opciones"]:
                    return False, f"Valor '{kwargs[nombre]}' no válido para '{nombre}'. Opciones: {config['opciones']}"
        
        return True, "OK"
