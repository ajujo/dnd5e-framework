"""
Módulo de conexión con LLM local (LM Studio).
"""

import requests
from typing import Callable, Optional

# Configuración por defecto
LM_STUDIO_URL = "http://localhost:1234/v1"
TIMEOUT_CONEXION = 2
TIMEOUT_RESPUESTA = 60


def verificar_conexion() -> bool:
    """Verifica si LM Studio está disponible."""
    try:
        response = requests.get(f"{LM_STUDIO_URL}/models", timeout=TIMEOUT_CONEXION)
        return response.status_code == 200
    except:
        return False


def llamar_llm(prompt: str, system_prompt: str = "", 
               temperature: float = 0.7, max_tokens: int = 500) -> Optional[str]:
    """
    Llama al LLM y devuelve la respuesta.
    
    Args:
        prompt: Mensaje del usuario
        system_prompt: Prompt del sistema
        temperature: Creatividad (0-1)
        max_tokens: Máximo de tokens en respuesta
    
    Returns:
        Texto de respuesta o None si hay error
    """
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
            timeout=TIMEOUT_RESPUESTA
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
    
    Returns:
        Función callback(prompt, system_prompt) -> str
        o None si no hay conexión
    """
    if not verificar_conexion():
        return None
    
    def callback(prompt: str, system_prompt: str = "") -> str:
        resultado = llamar_llm(prompt, system_prompt)
        return resultado if resultado else ""
    
    return callback


# Alias para compatibilidad
def configurar_llm() -> bool:
    """Verifica y configura conexión LLM. Devuelve True si está disponible."""
    return verificar_conexion()
