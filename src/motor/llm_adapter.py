from __future__ import annotations

"""
Adaptador para LLM local (LM Studio / Ollama / compatible OpenAI).

Proporciona una interfaz simple para conectar con LLMs locales.

USO:
    from motor.llm_adapter import crear_cliente_llm
    
    llm = crear_cliente_llm()  # Auto-detecta LM Studio/Ollama
    respuesta = llm("Narra este ataque épicamente")
"""

import json
import os
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass


@dataclass
class ConfigLLM:
    """Configuración del cliente LLM."""
    base_url: str = "http://127.0.0.1:1234/v1"  # LM Studio default
    modelo: str = ""  # Vacío = usar el modelo cargado en LM Studio
    temperatura: float = 0.7
    max_tokens: int = 500
    timeout: int = 30
    
    @property
    def url_completions(self) -> str:
        return f"{self.base_url}/chat/completions"
    
    @property
    def url_models(self) -> str:
        return f"{self.base_url}/models"


class ClienteLLM:
    """
    Cliente para LLM local compatible con API OpenAI.
    
    Soporta:
    - LM Studio (puerto 1234)
    - Ollama (puerto 11434)
    - Cualquier servidor compatible OpenAI
    """
    
    def __init__(self, config: ConfigLLM = None):
        self.config = config or ConfigLLM()
        self._disponible = None
        self._modelo_efectivo = None  # El modelo realmente usado
    
    def refrescar(self):
        """Resetea el cache de disponibilidad para re-detectar."""
        self._disponible = None
    
    def esta_disponible(self, usar_cache: bool = True) -> bool:
        """Verifica si el servidor LLM está disponible."""
        if usar_cache and self._disponible is not None:
            return self._disponible
        
        try:
            import urllib.request
            req = urllib.request.Request(
                self.config.url_models,
                method="GET"
            )
            req.add_header("Content-Type", "application/json")
            
            with urllib.request.urlopen(req, timeout=5) as response:
                self._disponible = response.status == 200
        except Exception:
            self._disponible = False
        
        return self._disponible
    
    def generar(self, prompt: str, system: str = None) -> str:
        """
        Genera texto usando el LLM.
        
        Args:
            prompt: El prompt del usuario
            system: Mensaje de sistema opcional
            
        Returns:
            Texto generado
        """
        import urllib.request
        import urllib.error
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "messages": messages,
            "temperature": self.config.temperatura,
            "max_tokens": self.config.max_tokens,
            "stream": False
        }
        
        # Usar modelo configurado si existe
        modelo_a_usar = self.config.modelo or self._modelo_efectivo
        if modelo_a_usar:
            payload["model"] = modelo_a_usar
        
        data = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(
            self.config.url_completions,
            data=data,
            method="POST"
        )
        req.add_header("Content-Type", "application/json")
        
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                # Guardar modelo efectivo de la respuesta si viene
                if "model" in result:
                    self._modelo_efectivo = result["model"]
                return result["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            # Si falla por modelo no encontrado, reintentar sin modelo específico
            if e.code == 400 and self.config.modelo:
                payload.pop("model", None)
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    self.config.url_completions,
                    data=data,
                    method="POST"
                )
                req.add_header("Content-Type", "application/json")
                with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    if "model" in result:
                        self._modelo_efectivo = result["model"]
                    return result["choices"][0]["message"]["content"].strip()
            raise ConnectionError(f"Error del LLM: {e}")
        except urllib.error.URLError as e:
            raise ConnectionError(f"No se pudo conectar al LLM: {e}")
        except (KeyError, IndexError) as e:
            raise ValueError(f"Respuesta inesperada del LLM: {e}")
    
    def __call__(self, prompt: str) -> str:
        """Permite usar el cliente como función."""
        return self.generar(prompt)
    def obtener_info(self) -> Dict[str, Any]:
        """Obtiene información del servidor LLM."""
        import urllib.request
        
        try:
            url_models = self.config.url_models
            req = urllib.request.Request(url_models, method="GET")
            req.add_header("Content-Type", "application/json")
            
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
                modelos = result.get("data", [])
                modelos_ids = [m["id"] for m in modelos]
                modelo_por_defecto = modelos_ids[0] if modelos_ids else "ninguno"
                modelo_activo = self.config.modelo or self._modelo_efectivo or modelo_por_defecto
                
                return {
                    "tipo": "LM Studio",
                    "url": self.config.base_url,
                    "modelo": modelo_activo,
                    "modelo_por_defecto": modelo_por_defecto,
                    "modelos_disponibles": modelos_ids
                }
        except Exception as e:
            return {
                "tipo": "LM Studio",
                "url": self.config.base_url,
                "modelo": self.config.modelo or "desconocido",
                "modelo_por_defecto": "desconocido",
                "error": str(e)
            }




    @property
    def modelo_efectivo(self) -> str:
        """Devuelve el modelo que se está usando realmente."""
        if self._modelo_efectivo and self._modelo_efectivo != "None":
            return self._modelo_efectivo
        if self.config.modelo:
            return self.config.modelo
        # Obtener el primero disponible
        info = self.obtener_info()
        return info.get("modelo_por_defecto") or info.get("modelo") or "desconocido"
    
    def cambiar_modelo(self, modelo_id: str) -> bool:
        """
        Cambia el modelo a usar.
        
        Returns:
            True si el modelo existe y se cambió, False si no existe
        """
        info = self.obtener_info()
        disponibles = info.get("modelos_disponibles", [])
        
        if modelo_id in disponibles:
            self.config.modelo = modelo_id
            self._modelo_efectivo = modelo_id
            return True
        return False
    
    def listar_modelos(self) -> list:
        """Lista los modelos disponibles."""
        info = self.obtener_info()
        return info.get("modelos_disponibles", [])


class ClienteOllama(ClienteLLM):
    """Cliente específico para Ollama."""
    
    def __init__(self, modelo: str = "llama3.2"):
        config = ConfigLLM(
            base_url="http://127.0.0.1:11434/api",
            modelo=modelo,
            temperatura=0.7,
            max_tokens=500
        )
        super().__init__(config)
    
    @property
    def _url_chat(self) -> str:
        return f"{self.config.base_url}/chat"
    
    @property 
    def _url_tags(self) -> str:
        return f"{self.config.base_url}/tags"
    
    def generar(self, prompt: str, system: str = None) -> str:
        """Genera texto usando Ollama (API diferente)."""
        import urllib.request
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.config.modelo,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperatura,
                "num_predict": self.config.max_tokens
            }
        }
        
        data = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(
            self.config.url_completions,
            data=data,
            method="POST"
        )
        req.add_header("Content-Type", "application/json")
        
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["message"]["content"].strip()
        except Exception as e:
            raise ConnectionError(f"No se pudo conectar a Ollama: {e}")



    def obtener_info(self) -> Dict[str, Any]:
        """Obtiene información del servidor Ollama."""
        import urllib.request
        
        try:
            req = urllib.request.Request(
                self._url_tags,
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
                modelos = result.get("models", [])
                return {
                    "tipo": "Ollama",
                    "url": self.config.base_url,
                    "modelo": self.config.modelo,
                    "modelos_disponibles": [m["name"] for m in modelos]
                }
        except Exception as e:
            return {
                "tipo": "Ollama",
                "url": self.config.base_url,
                "modelo": self.config.modelo,
                "error": str(e)
            }


def detectar_llm_disponible() -> Optional[ClienteLLM]:
    """
    Detecta automáticamente qué LLM está disponible.
    
    Orden de prioridad:
    1. LM Studio (puerto 1234)
    2. Ollama (puerto 11434)
    
    Returns:
        ClienteLLM si hay uno disponible, None si no
    """
    # Intentar LM Studio
    cliente_lm = ClienteLLM()
    if cliente_lm.esta_disponible(usar_cache=False):
        return cliente_lm
    
    # Intentar Ollama
    cliente_ollama = ClienteOllama()
    if cliente_ollama.esta_disponible(usar_cache=False):
        return cliente_ollama
    
    return None


def crear_cliente_llm(
    url: str = None,
    modelo: str = None,
    auto_detectar: bool = True
) -> Optional[ClienteLLM]:
    """
    Crea un cliente LLM.
    
    Args:
        url: URL del servidor (None = auto-detectar)
        modelo: Modelo a usar (None = el cargado)
        auto_detectar: Si True, detecta LM Studio/Ollama automáticamente
        
    Returns:
        Función que recibe prompt y devuelve texto, o None si no hay LLM
    """
    if url:
        config = ConfigLLM(url=url)
        if modelo:
            config.modelo = modelo
        cliente = ClienteLLM(config)
        if cliente.esta_disponible():
            return cliente
        return None
    
    if auto_detectar:
        return detectar_llm_disponible()
    
    return None


# Sistema de prompts para D&D
SYSTEM_PROMPTS = {
    "narrador": """Eres el Dungeon Master de una partida de D&D 5e.
Tu rol es narrar lo que ocurre de forma inmersiva.

REGLAS DE PERSONA (OBLIGATORIAS):
- Si el ACTOR es PC: usa 2ª persona ("Lanzas tu espada...", "Tu golpe...")
- Si el ACTOR es NPC: usa 3ª persona ("El goblin ataca...")
- Si el OBJETIVO es PC: SIEMPRE usa 2ª persona ("te roza", "esquivas"). NO uses el nombre del PC.
- Si el OBJETIVO es NPC: usa 3ª persona ("el goblin cae")

PROHIBICIONES:
- NO inventes personajes, enemigos, aliados u objetos que no aparezcan en "Participantes visibles"
- NO menciones números de dados ni mecánicas
- NO añadas escenarios ni elementos de ambiente que no estén en "Escena"
- NO uses el nombre del PC cuando es el objetivo, usa "tú/te/tu"

REGLAS GENERALES:
- Sé conciso (2-3 frases máximo)
- Solo narra lo que pasó según el Resultado
- Si FALLA: describe el fallo (esquiva, bloqueo, error)
- Si IMPACTA: describe el golpe y su efecto""",

    "clarificacion": """Eres el Dungeon Master de una partida de D&D 5e.
Necesitas aclarar qué quiere hacer el jugador.
Reglas:
- Reformula la pregunta de forma narrativa
- NO cambies las opciones disponibles
- Sé breve (1 frase)""",

    "normalizador": """Eres un parser de acciones de D&D 5e.
Dado un texto en lenguaje natural, extrae la acción estructurada.

REGLAS ESTRICTAS:
- Responde SOLO con JSON válido
- SIN markdown, SIN backticks, SIN explicaciones
- Si no puedes interpretar, devuelve: {"tipo":"desconocido","datos":{},"confianza":0.0}

Formato:
{"tipo": "ataque|conjuro|movimiento|habilidad|accion", "datos": {...}, "confianza": 0.0-1.0}

Ejemplos:
"Ataco al goblin" -> {"tipo":"ataque","datos":{"objetivo":"goblin"},"confianza":0.95}
"Lanzo bola de fuego" -> {"tipo":"conjuro","datos":{"conjuro":"bola_de_fuego"},"confianza":0.90}
"Hago algo raro" -> {"tipo":"desconocido","datos":{},"confianza":0.0}"""
}


def crear_callback_narrador(cliente: ClienteLLM) -> Callable[[str], str]:
    """Crea un callback de narrador que usa el LLM."""
    def narrar(prompt: str) -> str:
        return cliente.generar(prompt, system=SYSTEM_PROMPTS["narrador"])
    return narrar


def crear_callback_normalizador(cliente: ClienteLLM) -> Callable[[str, Any], Dict]:
    """Crea un callback de normalizador que usa el LLM."""
    def normalizar(texto: str, contexto: Any) -> Dict:
        prompt = f"""Texto del jugador: "{texto}"
Contexto: Actor={contexto.actor_nombre if contexto else 'desconocido'}

Extrae la acción como JSON:"""
        
        respuesta = cliente.generar(prompt, system=SYSTEM_PROMPTS["normalizador"])
        
        # Intentar parsear JSON
        try:
            # Limpiar posibles backticks
            respuesta = respuesta.strip()
            if respuesta.startswith("```"):
                respuesta = respuesta.split("```")[1]
                if respuesta.startswith("json"):
                    respuesta = respuesta[4:]
            resultado = json.loads(respuesta)
            # Asegurar que tiene los campos mínimos
            if "tipo" not in resultado:
                resultado["tipo"] = "desconocido"
            if "datos" not in resultado:
                resultado["datos"] = {}
            
            # Normalizar confianza a 0-1
            conf = resultado.get("confianza", 0.5)
            try:
                conf = float(conf)
                if conf > 1:
                    conf = conf / 100.0
            except Exception:
                conf = 0.5
            resultado["confianza"] = max(0.0, min(1.0, conf))
            
            return resultado
        except json.JSONDecodeError:
            return {"tipo": "desconocido", "datos": {}, "confianza": 0.0}
    
    return normalizar
