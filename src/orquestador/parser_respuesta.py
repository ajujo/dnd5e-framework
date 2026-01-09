"""
Parser de respuestas del LLM.

Extrae las llamadas a herramientas y la narrativa
de las respuestas estructuradas del LLM.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RespuestaLLM:
    """Estructura de una respuesta parseada del LLM."""
    pensamiento: str = ""  # Razonamiento interno del LLM
    herramienta: Optional[str] = None  # Nombre de herramienta a ejecutar
    parametros: Dict[str, Any] = None  # Parámetros de la herramienta
    narrativa: str = ""  # Texto narrativo para el jugador
    accion_dm: Optional[str] = None  # Acción especial del DM
    cambio_modo: Optional[str] = None  # Cambio de modo: exploracion/social/combate
    error: Optional[str] = None  # Error de parsing si lo hay
    
    def __post_init__(self):
        if self.parametros is None:
            self.parametros = {}


def parsear_respuesta_json(texto: str) -> RespuestaLLM:
    """
    Parsea una respuesta en formato JSON del LLM.
    
    Formato esperado:
    {
        "pensamiento": "Mi razonamiento...",
        "herramienta": "nombre_herramienta" o null,
        "parametros": {...} o {},
        "narrativa": "Texto para el jugador...",
        "accion_dm": "iniciar_combate" o null
    }
    """
    respuesta = RespuestaLLM()
    
    # Limpiar el texto (quitar markdown code blocks si los hay)
    texto_limpio = texto.strip()
    
    # Buscar JSON en el texto
    json_match = re.search(r'\{[\s\S]*\}', texto_limpio)
    
    if not json_match:
        # Si no hay JSON, tratar todo como narrativa
        respuesta.narrativa = texto_limpio
        return respuesta
    
    try:
        datos = json.loads(json_match.group())
        
        respuesta.pensamiento = datos.get("pensamiento", "")
        respuesta.herramienta = datos.get("herramienta")
        respuesta.parametros = datos.get("parametros", {})
        respuesta.narrativa = datos.get("narrativa", "")
        respuesta.accion_dm = datos.get("accion_dm")
        respuesta.cambio_modo = datos.get("cambio_modo")
        
        # Si hay herramienta pero es null o "ninguna", limpiar
        if respuesta.herramienta in (None, "null", "ninguna", "none", ""):
            respuesta.herramienta = None
            respuesta.parametros = {}
        
    except json.JSONDecodeError as e:
        respuesta.error = f"Error parseando JSON: {e}"
        # Intentar extraer narrativa del texto
        respuesta.narrativa = texto_limpio
    
    return respuesta


def parsear_respuesta_con_marcadores(texto: str) -> RespuestaLLM:
    """
    Parser alternativo que usa marcadores de texto.
    
    Formato esperado:
    [PENSAMIENTO]
    Mi razonamiento...
    [/PENSAMIENTO]
    
    [HERRAMIENTA: nombre_herramienta]
    param1: valor1
    param2: valor2
    [/HERRAMIENTA]
    
    [NARRATIVA]
    Texto para el jugador...
    [/NARRATIVA]
    """
    respuesta = RespuestaLLM()
    
    # Extraer pensamiento
    pensamiento_match = re.search(
        r'\[PENSAMIENTO\](.*?)\[/PENSAMIENTO\]', 
        texto, 
        re.DOTALL | re.IGNORECASE
    )
    if pensamiento_match:
        respuesta.pensamiento = pensamiento_match.group(1).strip()
    
    # Extraer herramienta
    herramienta_match = re.search(
        r'\[HERRAMIENTA:\s*(\w+)\](.*?)\[/HERRAMIENTA\]',
        texto,
        re.DOTALL | re.IGNORECASE
    )
    if herramienta_match:
        respuesta.herramienta = herramienta_match.group(1).strip()
        params_texto = herramienta_match.group(2).strip()
        
        # Parsear parámetros (formato key: value)
        for linea in params_texto.split('\n'):
            if ':' in linea:
                key, value = linea.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Intentar convertir tipos
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif re.match(r'^-?\d+\.?\d*$', value):
                    value = float(value)
                
                respuesta.parametros[key] = value
    
    # Extraer narrativa
    narrativa_match = re.search(
        r'\[NARRATIVA\](.*?)\[/NARRATIVA\]',
        texto,
        re.DOTALL | re.IGNORECASE
    )
    if narrativa_match:
        respuesta.narrativa = narrativa_match.group(1).strip()
    else:
        # Si no hay marcadores de narrativa, buscar texto fuera de marcadores
        texto_sin_marcadores = re.sub(
            r'\[(?:PENSAMIENTO|HERRAMIENTA|ACCION_DM).*?\[/(?:PENSAMIENTO|HERRAMIENTA|ACCION_DM)\]',
            '',
            texto,
            flags=re.DOTALL | re.IGNORECASE
        ).strip()
        if texto_sin_marcadores:
            respuesta.narrativa = texto_sin_marcadores
    
    # Extraer acción DM
    accion_match = re.search(
        r'\[ACCION_DM:\s*(\w+)\]',
        texto,
        re.IGNORECASE
    )
    if accion_match:
        respuesta.accion_dm = accion_match.group(1).strip()
    
    return respuesta


def parsear_respuesta(texto: str, formato: str = "json") -> RespuestaLLM:
    """
    Parsea una respuesta del LLM.
    
    Args:
        texto: Texto de respuesta del LLM
        formato: "json" o "marcadores"
    """
    if formato == "json":
        return parsear_respuesta_json(texto)
    else:
        return parsear_respuesta_con_marcadores(texto)


def validar_respuesta(respuesta: RespuestaLLM) -> Tuple[bool, str]:
    """
    Valida que una respuesta tenga el contenido mínimo necesario.
    
    Returns:
        (es_valida, mensaje_error)
    """
    if respuesta.error:
        return False, respuesta.error
    
    if not respuesta.narrativa and not respuesta.herramienta:
        return False, "La respuesta no tiene ni narrativa ni herramienta"
    
    if respuesta.herramienta and not respuesta.parametros:
        # Algunas herramientas no necesitan parámetros, esto es OK
        pass
    
    return True, "OK"
