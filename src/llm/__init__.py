"""
Módulo de conexión con LLM local (LM Studio).
Soporta perfiles de configuración: lite, normal, completo
"""

import json
import os
import requests
from typing import Callable, Optional, Dict, Any

# Configuración por defecto
LM_STUDIO_URL = "http://localhost:1234/v1"
TIMEOUT_CONEXION = 2

# Perfil activo (se configura con set_perfil)
_perfil_activo: Dict[str, Any] = {
    "nombre": "normal",
    "max_tokens": 600,
    "temperature": 0.75,
    "timeout": 60
}


def cargar_perfiles() -> Dict[str, Any]:
    """Carga los perfiles desde el archivo de configuración."""
    ruta = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'llm_profiles.json')
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f).get("perfiles", {})
    except FileNotFoundError:
        return {}


def set_perfil(nombre: str) -> bool:
    """
    Establece el perfil activo.
    
    Args:
        nombre: "lite", "normal" o "completo"
    
    Returns:
        True si se estableció correctamente
    """
    global _perfil_activo
    
    perfiles = cargar_perfiles()
    
    if nombre not in perfiles:
        print(f"⚠ Perfil '{nombre}' no encontrado. Usando 'normal'.")
        nombre = "normal"
        if nombre not in perfiles:
            return False
    
    perfil = perfiles[nombre]
    _perfil_activo = {
        "nombre": nombre,
        "max_tokens": perfil.get("max_tokens", 600),
        "temperature": perfil.get("temperature", 0.75),
        "timeout": perfil.get("timeout", 60)
    }
    
    return True


def get_perfil() -> Dict[str, Any]:
    """Devuelve el perfil activo."""
    return _perfil_activo.copy()


def verificar_conexion() -> bool:
    """Verifica si LM Studio está disponible."""
    try:
        response = requests.get(f"{LM_STUDIO_URL}/models", timeout=TIMEOUT_CONEXION)
        return response.status_code == 200
    except:
        return False


def llamar_llm(prompt: str, system_prompt: str = "", 
               temperature: float = None, max_tokens: int = None) -> Optional[str]:
    """
    Llama al LLM y devuelve la respuesta.
    Usa los valores del perfil activo si no se especifican.
    """
    # Usar valores del perfil si no se especifican
    if temperature is None:
        temperature = _perfil_activo["temperature"]
    if max_tokens is None:
        max_tokens = _perfil_activo["max_tokens"]
    timeout = _perfil_activo["timeout"]
    
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = requests.post(
            f"{LM_STUDIO_URL}/chat/completions",
            json={
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            print(f"[LLM Error] Status: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        print("[LLM Error] Timeout esperando respuesta")
        return None
    except Exception as e:
        print(f"[LLM Error] {e}")
        return None


def obtener_cliente_llm() -> Optional[Callable[[str, str], str]]:
    """
    Obtiene un cliente LLM como función callback.
    """
    if not verificar_conexion():
        return None
    
    def callback(prompt: str, system_prompt: str = "") -> str:
        resultado = llamar_llm(prompt, system_prompt)
        return resultado if resultado else ""
    
    return callback


def configurar_llm() -> bool:
    """Verifica y configura conexión LLM."""
    return verificar_conexion()
