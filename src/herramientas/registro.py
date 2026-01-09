"""
Registro central de herramientas disponibles para el LLM.

Permite registrar, listar y ejecutar herramientas de forma centralizada.
"""

from typing import Any, Dict, List, Optional
from .herramienta_base import Herramienta


class RegistroHerramientas:
    """Gestiona todas las herramientas disponibles."""
    
    def __init__(self):
        self._herramientas: Dict[str, Herramienta] = {}
    
    def registrar(self, herramienta: Herramienta) -> None:
        """Registra una herramienta en el sistema."""
        self._herramientas[herramienta.nombre] = herramienta
    
    def obtener(self, nombre: str) -> Optional[Herramienta]:
        """Obtiene una herramienta por nombre."""
        return self._herramientas.get(nombre)
    
    def listar(self) -> List[str]:
        """Lista nombres de todas las herramientas registradas."""
        return list(self._herramientas.keys())
    
    def ejecutar(self, nombre: str, contexto: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Ejecuta una herramienta por nombre.
        
        Returns:
            Resultado de la herramienta o error si no existe.
        """
        herramienta = self.obtener(nombre)
        
        if not herramienta:
            return {
                "exito": False,
                "error": f"Herramienta '{nombre}' no encontrada",
                "herramientas_disponibles": self.listar()
            }
        
        # Validar parámetros
        valido, mensaje = herramienta.validar_parametros(**kwargs)
        if not valido:
            return {
                "exito": False,
                "error": mensaje
            }
        
        # Ejecutar
        try:
            return herramienta.ejecutar(contexto, **kwargs)
        except Exception as e:
            return {
                "exito": False,
                "error": f"Error ejecutando '{nombre}': {str(e)}"
            }
    
    def generar_documentacion_llm(self) -> str:
        """
        Genera la documentación de herramientas para incluir en el prompt del LLM.
        """
        lineas = ["HERRAMIENTAS DISPONIBLES:", ""]
        
        for nombre, herr in self._herramientas.items():
            lineas.append(f"## {nombre}")
            lineas.append(f"   {herr.descripcion}")
            lineas.append("   Parámetros:")
            
            for param, config in herr.parametros.items():
                req = "(requerido)" if config.get("requerido") else "(opcional)"
                tipo = config.get("tipo", "any")
                desc = config.get("descripcion", "")
                lineas.append(f"   - {param} [{tipo}] {req}: {desc}")
                
                if "opciones" in config:
                    lineas.append(f"     Valores válidos: {config['opciones']}")
            
            lineas.append("")
        
        return "\n".join(lineas)
    
    def generar_schema_json(self) -> List[Dict[str, Any]]:
        """Genera el schema JSON de herramientas para modelos con function calling."""
        return [h.to_dict() for h in self._herramientas.values()]


# Instancia global del registro
registro_global = RegistroHerramientas()


def registrar_herramienta(herramienta: Herramienta) -> None:
    """Función helper para registrar en el registro global."""
    registro_global.registrar(herramienta)


def obtener_registro() -> RegistroHerramientas:
    """Obtiene el registro global."""
    return registro_global
