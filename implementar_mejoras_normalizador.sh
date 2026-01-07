#!/bin/bash

# =============================================================================
# MEJORAS: Vocabulario, Contrato Canónico y Modo Estricto
# =============================================================================

set -e

echo "=============================================="
echo "  MEJORAS AL NORMALIZADOR Y VALIDADOR"
echo "=============================================="
echo ""

# -----------------------------------------------------------------------------
# 1. Crear src/motor/vocabulario.py
# -----------------------------------------------------------------------------
echo "→ Creando src/motor/vocabulario.py..."

cat > src/motor/vocabulario.py << 'EOF'
"""
Vocabulario de Sinónimos para D&D 5e

Este módulo centraliza todos los sinónimos y variantes de texto
que el normalizador usa para detectar intenciones y entidades.

MANTENIMIENTO:
- Para añadir un nuevo sinónimo, solo hay que añadirlo al diccionario correspondiente
- Los patrones regex se generan automáticamente desde estos diccionarios
- No es necesario modificar el normalizador

ESTRUCTURA:
- SINONIMOS_INTENCION: verbo/frase → tipo de acción
- SINONIMOS_HABILIDAD: verbo/frase → habilidad específica
- SINONIMOS_ACCION: verbo/frase → acción genérica (dash, dodge, etc.)
- SINONIMOS_ARMA: término coloquial → id del compendio
"""

import re
from typing import Dict, List, Set, Optional, Tuple
from enum import Enum


# =============================================================================
# SINÓNIMOS DE INTENCIÓN (qué tipo de acción quiere hacer)
# =============================================================================

class TipoIntencion(Enum):
    ATAQUE = "ataque"
    CONJURO = "conjuro"
    MOVIMIENTO = "movimiento"
    HABILIDAD = "habilidad"
    ACCION = "accion"
    OBJETO = "objeto"


# Verbos/frases que indican cada tipo de intención
# Clave: palabra o frase, Valor: tipo de intención
VERBOS_INTENCION: Dict[str, TipoIntencion] = {
    # Ataque
    "ataco": TipoIntencion.ATAQUE,
    "atacar": TipoIntencion.ATAQUE,
    "ataque": TipoIntencion.ATAQUE,
    "golpeo": TipoIntencion.ATAQUE,
    "golpear": TipoIntencion.ATAQUE,
    "pego": TipoIntencion.ATAQUE,
    "pegar": TipoIntencion.ATAQUE,
    "disparo": TipoIntencion.ATAQUE,
    "disparar": TipoIntencion.ATAQUE,
    "corto": TipoIntencion.ATAQUE,
    "cortar": TipoIntencion.ATAQUE,
    "apuñalo": TipoIntencion.ATAQUE,
    "apuñalar": TipoIntencion.ATAQUE,
    "hiero": TipoIntencion.ATAQUE,
    "herir": TipoIntencion.ATAQUE,
    
    # Movimiento
    "muevo": TipoIntencion.MOVIMIENTO,
    "moverme": TipoIntencion.MOVIMIENTO,
    "mover": TipoIntencion.MOVIMIENTO,
    "camino": TipoIntencion.MOVIMIENTO,
    "caminar": TipoIntencion.MOVIMIENTO,
    "corro": TipoIntencion.MOVIMIENTO,
    "correr": TipoIntencion.MOVIMIENTO,
    "acerco": TipoIntencion.MOVIMIENTO,
    "acercarme": TipoIntencion.MOVIMIENTO,
    "alejo": TipoIntencion.MOVIMIENTO,
    "alejarme": TipoIntencion.MOVIMIENTO,
    "desplazo": TipoIntencion.MOVIMIENTO,
    "desplazarme": TipoIntencion.MOVIMIENTO,
    "voy": TipoIntencion.MOVIMIENTO,
    "ir": TipoIntencion.MOVIMIENTO,
    "avanzo": TipoIntencion.MOVIMIENTO,
    "avanzar": TipoIntencion.MOVIMIENTO,
    "retrocedo": TipoIntencion.MOVIMIENTO,
    "retroceder": TipoIntencion.MOVIMIENTO,
    
    # Conjuro (verbos genéricos, los específicos se detectan por nombre)
    "conjuro": TipoIntencion.CONJURO,
    "conjurar": TipoIntencion.CONJURO,
    "hechizo": TipoIntencion.CONJURO,
    "magia": TipoIntencion.CONJURO,
    
    # Habilidad (verbos que implican pruebas)
    "escucho": TipoIntencion.HABILIDAD,
    "escuchar": TipoIntencion.HABILIDAD,
    "oigo": TipoIntencion.HABILIDAD,
    "oir": TipoIntencion.HABILIDAD,
    "miro": TipoIntencion.HABILIDAD,
    "mirar": TipoIntencion.HABILIDAD,
    "busco": TipoIntencion.HABILIDAD,
    "buscar": TipoIntencion.HABILIDAD,
    "examino": TipoIntencion.HABILIDAD,
    "examinar": TipoIntencion.HABILIDAD,
    "investigo": TipoIntencion.HABILIDAD,
    "investigar": TipoIntencion.HABILIDAD,
    "persuado": TipoIntencion.HABILIDAD,
    "persuadir": TipoIntencion.HABILIDAD,
    "persuadirlo": TipoIntencion.HABILIDAD,
    "convenzo": TipoIntencion.HABILIDAD,
    "convencer": TipoIntencion.HABILIDAD,
    "intimido": TipoIntencion.HABILIDAD,
    "intimidar": TipoIntencion.HABILIDAD,
    "amenazo": TipoIntencion.HABILIDAD,
    "amenazar": TipoIntencion.HABILIDAD,
    "miento": TipoIntencion.HABILIDAD,
    "mentir": TipoIntencion.HABILIDAD,
    "engaño": TipoIntencion.HABILIDAD,
    "engañar": TipoIntencion.HABILIDAD,
    "trepo": TipoIntencion.HABILIDAD,
    "trepar": TipoIntencion.HABILIDAD,
    "escalo": TipoIntencion.HABILIDAD,
    "escalar": TipoIntencion.HABILIDAD,
    "salto": TipoIntencion.HABILIDAD,
    "saltar": TipoIntencion.HABILIDAD,
    "nado": TipoIntencion.HABILIDAD,
    "nadar": TipoIntencion.HABILIDAD,
    
    # Objeto
    "bebo": TipoIntencion.OBJETO,
    "beber": TipoIntencion.OBJETO,
    "tomo": TipoIntencion.OBJETO,
    "tomar": TipoIntencion.OBJETO,
}


# =============================================================================
# SINÓNIMOS DE HABILIDAD (qué habilidad específica)
# =============================================================================

# Verbo/frase → habilidad de D&D 5e
VERBOS_HABILIDAD: Dict[str, str] = {
    # Percepción
    "escucho": "percepcion",
    "escuchar": "percepcion",
    "oigo": "percepcion",
    "oir": "percepcion",
    "miro": "percepcion",
    "mirar": "percepcion",
    "observo": "percepcion",
    "observar": "percepcion",
    "vigilo": "percepcion",
    "vigilar": "percepcion",
    "oteo": "percepcion",
    "otear": "percepcion",
    
    # Investigación
    "investigo": "investigacion",
    "investigar": "investigacion",
    "examino": "investigacion",
    "examinar": "investigacion",
    "analizo": "investigacion",
    "analizar": "investigacion",
    "estudio": "investigacion",
    "estudiar": "investigacion",
    "inspecciono": "investigacion",
    "inspeccionar": "investigacion",
    
    # Sigilo
    "escondo": "sigilo",
    "esconderme": "sigilo",
    "oculto": "sigilo",
    "ocultarme": "sigilo",
    "sigiloso": "sigilo",
    "sigilosamente": "sigilo",
    
    # Atletismo
    "trepo": "atletismo",
    "trepar": "atletismo",
    "escalo": "atletismo",
    "escalar": "atletismo",
    "salto": "atletismo",
    "saltar": "atletismo",
    "nado": "atletismo",
    "nadar": "atletismo",
    "empujo": "atletismo",
    "empujar": "atletismo",
    "forcejeo": "atletismo",
    "forcejear": "atletismo",
    
    # Acrobacias
    "ruedo": "acrobacias",
    "rodar": "acrobacias",
    "voltereta": "acrobacias",
    "equilibrio": "acrobacias",
    "equilibrarme": "acrobacias",
    "pirueta": "acrobacias",
    
    # Persuasión
    "persuado": "persuasion",
    "persuadir": "persuasion",
    "persuadirlo": "persuasion",
    "convenzo": "persuasion",
    "convencer": "persuasion",
    "negocio": "persuasion",
    "negociar": "persuasion",
    "regateo": "persuasion",
    "regatear": "persuasion",
    "halago": "persuasion",
    "halagar": "persuasion",
    
    # Engaño
    "miento": "engaño",
    "mentir": "engaño",
    "engaño": "engaño",
    "engañar": "engaño",
    "finjo": "engaño",
    "fingir": "engaño",
    "faroleo": "engaño",
    "farolear": "engaño",
    "timo": "engaño",
    "timar": "engaño",
    
    # Intimidación
    "intimido": "intimidacion",
    "intimidar": "intimidacion",
    "amenazo": "intimidacion",
    "amenazar": "intimidacion",
    "asusto": "intimidacion",
    "asustar": "intimidacion",
    "aterrorizo": "intimidacion",
    "aterrorizar": "intimidacion",
    
    # Medicina
    "curo": "medicina",
    "curar": "medicina",
    "estabilizo": "medicina",
    "estabilizar": "medicina",
    "diagnostico": "medicina",
    "diagnosticar": "medicina",
    "vendo": "medicina",
    "vendar": "medicina",
    
    # Supervivencia
    "rastro": "supervivencia",
    "rastrear": "supervivencia",
    "sigo": "supervivencia",
    "seguir": "supervivencia",
    "cazo": "supervivencia",
    "cazar": "supervivencia",
    "forrajeo": "supervivencia",
    "forrajear": "supervivencia",
    
    # Trato con animales
    "amanso": "trato_animales",
    "amansar": "trato_animales",
    "domestico": "trato_animales",
    "domesticar": "trato_animales",
    "calmo": "trato_animales",
    "calmar": "trato_animales",
}


# =============================================================================
# SINÓNIMOS DE ACCIONES GENÉRICAS (Dash, Dodge, etc.)
# =============================================================================

# Término → acción genérica de D&D
SINONIMOS_ACCION_GENERICA: Dict[str, str] = {
    # Dash
    "dash": "dash",
    "carrera": "dash",
    "sprint": "dash",
    "correr rápido": "dash",
    "correr rapido": "dash",
    "corro todo lo que puedo": "dash",
    
    # Dodge
    "dodge": "dodge",
    "esquivar": "dodge",
    "esquiva": "dodge",
    "esquivo": "dodge",
    "evadir": "dodge",
    "me pongo a esquivar": "dodge",
    "preparo para esquivar": "dodge",
    
    # Disengage
    "disengage": "disengage",
    "desenganche": "disengage",
    "retirada": "disengage",
    "retirarse": "disengage",
    "retirarme": "disengage",
    "me retiro": "disengage",
    "retrocedo sin provocar": "disengage",
    
    # Help
    "help": "help",
    "ayudar": "help",
    "ayuda": "help",
    "ayudo": "help",
    "asistir": "help",
    "asisto": "help",
    "echo una mano": "help",
    
    # Hide
    "hide": "hide",
    "esconder": "hide",
    "esconderse": "hide",
    "esconderme": "hide",
    "me escondo": "hide",
    "ocultar": "hide",
    "ocultarme": "hide",
    "me oculto": "hide",
    
    # Search
    "search": "search",
    "buscar": "search",
    "registrar": "search",
    "registro": "search",
    
    # Ready
    "ready": "ready",
    "preparar": "ready",
    "preparo": "ready",
    "preparar acción": "ready",
    "preparar accion": "ready",
    "preparo una acción": "ready",
}


# =============================================================================
# SINÓNIMOS DE ARMAS
# =============================================================================

# Término coloquial → id del compendio
SINONIMOS_ARMA: Dict[str, List[str]] = {
    "espada": ["espada_larga", "espada_corta"],
    "espadón": ["espada_larga"],
    "sable": ["espada_corta"],
    "daga": ["daga"],
    "cuchillo": ["daga"],
    "puñal": ["daga"],
    "maza": ["maza"],
    "martillo": ["maza"],
    "hacha": ["hacha_mano"],
    "arco": ["arco_corto"],
    "ballesta": ["ballesta_ligera"],
    "bastón": ["baston"],
    "vara": ["baston"],
    "palo": ["baston"],
}

# Términos que indican ataque desarmado
TERMINOS_DESARMADO: Set[str] = {
    "desarmado", "puño", "puñetazo", "patada", "cabezazo",
    "golpe", "mano", "codo", "rodilla", "sin arma"
}


# =============================================================================
# FUNCIONES DE AYUDA
# =============================================================================

def generar_patron_intencion(tipo: TipoIntencion) -> str:
    """
    Genera un patrón regex para detectar una intención específica.
    
    Args:
        tipo: El tipo de intención a buscar.
        
    Returns:
        Patrón regex compilable.
    """
    verbos = [v for v, t in VERBOS_INTENCION.items() if t == tipo]
    if not verbos:
        return r"(?!)"  # Patrón que nunca matchea
    return r'\b(' + '|'.join(re.escape(v) for v in verbos) + r')\b'


def detectar_intencion_por_verbo(texto: str) -> Optional[TipoIntencion]:
    """
    Detecta la intención basándose en verbos del texto.
    
    Args:
        texto: Texto normalizado (minúsculas).
        
    Returns:
        TipoIntencion si se detecta, None si no.
    """
    texto_lower = texto.lower()
    for verbo, tipo in VERBOS_INTENCION.items():
        if re.search(r'\b' + re.escape(verbo) + r'\b', texto_lower):
            return tipo
    return None


def detectar_habilidad_por_verbo(texto: str) -> Optional[str]:
    """
    Detecta la habilidad específica basándose en verbos.
    
    Args:
        texto: Texto normalizado.
        
    Returns:
        Nombre de habilidad o None.
    """
    texto_lower = texto.lower()
    for verbo, habilidad in VERBOS_HABILIDAD.items():
        if re.search(r'\b' + re.escape(verbo) + r'\b', texto_lower):
            return habilidad
    return None


def detectar_accion_generica(texto: str) -> Optional[str]:
    """
    Detecta una acción genérica en el texto.
    
    Args:
        texto: Texto normalizado.
        
    Returns:
        ID de acción (dash, dodge, etc.) o None.
    """
    texto_lower = texto.lower()
    for termino, accion in SINONIMOS_ACCION_GENERICA.items():
        if termino in texto_lower:
            return accion
    return None


def es_ataque_desarmado(texto: str) -> bool:
    """
    Detecta si el texto indica un ataque desarmado.
    
    Args:
        texto: Texto normalizado.
        
    Returns:
        True si es ataque desarmado.
    """
    texto_lower = texto.lower()
    for termino in TERMINOS_DESARMADO:
        if termino in texto_lower:
            return True
    return False


def buscar_sinonimo_arma(texto: str) -> Optional[str]:
    """
    Busca sinónimos de armas en el texto.
    
    Args:
        texto: Texto normalizado.
        
    Returns:
        ID del arma en el compendio o None.
    """
    texto_lower = texto.lower()
    for sinonimo, ids in SINONIMOS_ARMA.items():
        if sinonimo in texto_lower:
            return ids[0]  # Retorna el primero por defecto
    return None
EOF

echo "   ✓ vocabulario.py creado"

# -----------------------------------------------------------------------------
# 2. Refactorizar normalizador para usar vocabulario
# -----------------------------------------------------------------------------
echo "→ Actualizando src/motor/normalizador.py para usar vocabulario..."

cat > src/motor/normalizador.py << 'EOF'
"""
Normalizador de Acciones para D&D 5e

Convierte texto en lenguaje natural a estructuras JSON canónicas.
Usa un enfoque híbrido:
1. Patrones deterministas desde vocabulario.py (rápido, mantenible)
2. Fallback a LLM local (solo cuando hace falta)

PATRÓN: Inyección de dependencias
- Recibe CompendioMotor por constructor
- Recibe contexto de escena (enemigos, equipo, etc.)

El LLM NO decide reglas. Solo rellena campos del JSON.
La legalidad la decide ValidadorAcciones.
"""

import re
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

from .compendio import CompendioMotor
from .vocabulario import (
    TipoIntencion,
    detectar_intencion_por_verbo,
    detectar_habilidad_por_verbo,
    detectar_accion_generica,
    es_ataque_desarmado,
    buscar_sinonimo_arma,
    SINONIMOS_ACCION_GENERICA,
)


class TipoAccionNorm(Enum):
    """Tipos de acción normalizados."""
    ATAQUE = "ataque"
    CONJURO = "conjuro"
    MOVIMIENTO = "movimiento"
    HABILIDAD = "habilidad"
    ACCION = "accion"
    OBJETO = "objeto"
    DESCONOCIDO = "desconocido"


# Mapeo de TipoIntencion a TipoAccionNorm
_INTENCION_A_ACCION = {
    TipoIntencion.ATAQUE: TipoAccionNorm.ATAQUE,
    TipoIntencion.CONJURO: TipoAccionNorm.CONJURO,
    TipoIntencion.MOVIMIENTO: TipoAccionNorm.MOVIMIENTO,
    TipoIntencion.HABILIDAD: TipoAccionNorm.HABILIDAD,
    TipoIntencion.ACCION: TipoAccionNorm.ACCION,
    TipoIntencion.OBJETO: TipoAccionNorm.OBJETO,
}


@dataclass
class AccionNormalizada:
    """Resultado de normalizar una acción."""
    tipo: TipoAccionNorm
    datos: Dict[str, Any]
    confianza: float = 0.0
    faltantes: List[str] = field(default_factory=list)
    advertencias: List[str] = field(default_factory=list)
    texto_original: str = ""
    requiere_clarificacion: bool = False
    fuente: str = "patron"
    
    def es_completa(self) -> bool:
        return len(self.faltantes) == 0 and self.confianza >= 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tipo": self.tipo.value,
            "datos": self.datos,
            "confianza": self.confianza,
            "faltantes": self.faltantes,
            "advertencias": self.advertencias,
            "texto_original": self.texto_original,
            "requiere_clarificacion": self.requiere_clarificacion,
            "fuente": self.fuente
        }


@dataclass
class ContextoEscena:
    """Contexto actual de la escena para resolver ambigüedades."""
    actor_id: str
    actor_nombre: str
    
    arma_principal: Optional[Dict[str, Any]] = None
    arma_secundaria: Optional[Dict[str, Any]] = None
    armas_disponibles: List[Dict[str, Any]] = field(default_factory=list)
    
    conjuros_conocidos: List[Dict[str, Any]] = field(default_factory=list)
    ranuras_disponibles: Dict[int, int] = field(default_factory=dict)
    
    enemigos_vivos: List[Dict[str, Any]] = field(default_factory=list)
    aliados: List[Dict[str, Any]] = field(default_factory=list)
    
    movimiento_restante: int = 30
    accion_disponible: bool = True
    accion_bonus_disponible: bool = True


# Lista de habilidades válidas
HABILIDADES_VALIDAS = [
    'acrobacias', 'arcanos', 'atletismo', 'engaño', 'historia',
    'interpretacion', 'intimidacion', 'investigacion', 'juego_manos',
    'medicina', 'naturaleza', 'percepcion', 'perspicacia', 'persuasion',
    'religion', 'sigilo', 'supervivencia', 'trato_animales'
]


class NormalizadorAcciones:
    """Normaliza texto en lenguaje natural a acciones estructuradas."""
    
    def __init__(self, compendio_motor: CompendioMotor, 
                 llm_callback: Callable[[str, Dict], Dict] = None):
        self._compendio = compendio_motor
        self._llm_callback = llm_callback
    
    def normalizar(self, texto: str, 
                   contexto: ContextoEscena) -> AccionNormalizada:
        """Normaliza un texto de acción a formato canónico."""
        texto_limpio = self._preprocesar(texto)
        tipo, confianza_tipo = self._detectar_intencion(texto_limpio, contexto)
        
        if tipo == TipoAccionNorm.ATAQUE:
            resultado = self._normalizar_ataque(texto_limpio, contexto)
        elif tipo == TipoAccionNorm.CONJURO:
            resultado = self._normalizar_conjuro(texto_limpio, contexto)
        elif tipo == TipoAccionNorm.MOVIMIENTO:
            resultado = self._normalizar_movimiento(texto_limpio, contexto)
        elif tipo == TipoAccionNorm.HABILIDAD:
            resultado = self._normalizar_habilidad(texto_limpio, contexto)
        elif tipo == TipoAccionNorm.ACCION:
            resultado = self._normalizar_accion_generica(texto_limpio, contexto)
        elif tipo == TipoAccionNorm.OBJETO:
            resultado = self._normalizar_objeto(texto_limpio, contexto)
        else:
            resultado = AccionNormalizada(
                tipo=TipoAccionNorm.DESCONOCIDO,
                datos={"actor_id": contexto.actor_id},
                confianza=0.0,
                faltantes=["tipo"],
                texto_original=texto
            )
        
        resultado = self._resolver_ambiguedades(resultado, contexto)
        
        if not resultado.es_completa() and self._llm_callback:
            resultado = self._fallback_llm(resultado, texto, contexto)
        
        resultado = self._canonizar(resultado)
        resultado.texto_original = texto
        
        return resultado
    
    def _preprocesar(self, texto: str) -> str:
        texto = texto.lower()
        texto = re.sub(r'[^\w\s\-áéíóúüñ]', ' ', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto
    
    def _detectar_intencion(self, texto: str, contexto: ContextoEscena) -> Tuple[TipoAccionNorm, float]:
        """Detecta el tipo de acción usando el vocabulario centralizado."""
        
        # 1. Acciones genéricas (muy específicas)
        accion = detectar_accion_generica(texto)
        if accion:
            return TipoAccionNorm.ACCION, 0.9
        
        # 2. Conjuros conocidos por nombre
        for conjuro in contexto.conjuros_conocidos:
            nombre_lower = conjuro.get("nombre", "").lower()
            if nombre_lower and nombre_lower in texto:
                return TipoAccionNorm.CONJURO, 0.95
        
        # También en compendio
        conjuros = self._compendio.listar_conjuros()
        for conjuro in conjuros:
            if conjuro["nombre"].lower() in texto:
                return TipoAccionNorm.CONJURO, 0.9
        
        # 3. Habilidades por nombre directo
        texto_norm = self._normalizar_texto_habilidad(texto)
        for hab in HABILIDADES_VALIDAS:
            if hab in texto_norm:
                return TipoAccionNorm.HABILIDAD, 0.9
        
        # 4. Detectar por verbos usando vocabulario
        intencion = detectar_intencion_por_verbo(texto)
        if intencion:
            tipo_accion = _INTENCION_A_ACCION.get(intencion, TipoAccionNorm.DESCONOCIDO)
            return tipo_accion, 0.85
        
        # 5. Objetos (poción)
        if re.search(r'\bpoci[oó]n\b', texto):
            return TipoAccionNorm.OBJETO, 0.8
        
        return TipoAccionNorm.DESCONOCIDO, 0.0
    
    def _normalizar_ataque(self, texto: str, 
                           contexto: ContextoEscena) -> AccionNormalizada:
        datos = {
            "tipo": "ataque",
            "atacante_id": contexto.actor_id,
            "objetivo_id": None,
            "arma_id": None,
            "subtipo": "melee",
            "modo": "normal"
        }
        faltantes = []
        advertencias = []
        confianza = 0.7
        
        # Detectar ataque desarmado
        if es_ataque_desarmado(texto):
            datos["arma_id"] = "unarmed"
            datos["subtipo"] = "unarmed"
        else:
            arma_id, arma_confianza = self._buscar_arma_en_texto(texto, contexto)
            if arma_id:
                datos["arma_id"] = arma_id
                confianza = min(confianza + 0.1, 1.0)
            else:
                faltantes.append("arma_id")
        
        objetivo_id, obj_confianza = self._buscar_objetivo_en_texto(texto, contexto)
        if objetivo_id:
            datos["objetivo_id"] = objetivo_id
            confianza = min(confianza + 0.1, 1.0)
        else:
            faltantes.append("objetivo_id")
        
        if re.search(r'\bventaja\b', texto):
            datos["modo"] = "ventaja"
        elif re.search(r'\bdesventaja\b', texto):
            datos["modo"] = "desventaja"
        
        if re.search(r'\b(arco|ballesta|distancia|disparar|disparo)\b', texto):
            datos["subtipo"] = "ranged"
        
        return AccionNormalizada(
            tipo=TipoAccionNorm.ATAQUE,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes,
            advertencias=advertencias
        )
    
    def _normalizar_conjuro(self, texto: str,
                            contexto: ContextoEscena) -> AccionNormalizada:
        datos = {
            "tipo": "conjuro",
            "lanzador_id": contexto.actor_id,
            "objetivo_id": None,
            "conjuro_id": None,
            "nivel_lanzamiento": None
        }
        faltantes = []
        confianza = 0.6
        
        conjuro_id, conj_confianza = self._buscar_conjuro_en_texto(texto, contexto)
        if conjuro_id:
            datos["conjuro_id"] = conjuro_id
            confianza = min(confianza + 0.2, 1.0)
            conjuro = self._compendio.obtener_conjuro(conjuro_id)
            if conjuro:
                datos["nivel_lanzamiento"] = conjuro.get("nivel", 1)
        else:
            faltantes.append("conjuro_id")
        
        match_nivel = re.search(r'nivel\s+(\d+)', texto)
        if match_nivel:
            datos["nivel_lanzamiento"] = int(match_nivel.group(1))
        
        objetivo_id, _ = self._buscar_objetivo_en_texto(texto, contexto)
        datos["objetivo_id"] = objetivo_id
        
        return AccionNormalizada(
            tipo=TipoAccionNorm.CONJURO,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes
        )
    
    def _normalizar_movimiento(self, texto: str,
                               contexto: ContextoEscena) -> AccionNormalizada:
        datos = {
            "tipo": "movimiento",
            "actor_id": contexto.actor_id,
            "distancia_pies": None,
            "destino": None
        }
        faltantes = []
        confianza = 0.7
        
        match_pies = re.search(r'(\d+)\s*(pies|ft|feet|pie)', texto)
        match_metros = re.search(r'(\d+)\s*(metros?|m)\b', texto)
        match_casillas = re.search(r'(\d+)\s*casillas?', texto)
        
        if match_pies:
            datos["distancia_pies"] = int(match_pies.group(1))
        elif match_metros:
            datos["distancia_pies"] = int(int(match_metros.group(1)) * 3.28)
        elif match_casillas:
            datos["distancia_pies"] = int(match_casillas.group(1)) * 5
        else:
            faltantes.append("distancia_pies")
        
        for patron in [r'hacia\s+(?:el|la|los|las)?\s*(\w+)', r'a\s+(?:el|la|los|las)?\s*(\w+)']:
            match = re.search(patron, texto)
            if match:
                datos["destino"] = match.group(1)
                break
        
        return AccionNormalizada(
            tipo=TipoAccionNorm.MOVIMIENTO,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes
        )
    
    def _normalizar_habilidad(self, texto: str,
                              contexto: ContextoEscena) -> AccionNormalizada:
        datos = {
            "tipo": "habilidad",
            "actor_id": contexto.actor_id,
            "habilidad": None,
            "objetivo_id": None
        }
        faltantes = []
        confianza = 0.6
        
        # Buscar por nombre de habilidad
        texto_norm = self._normalizar_texto_habilidad(texto)
        for hab in HABILIDADES_VALIDAS:
            if hab in texto_norm:
                datos["habilidad"] = hab
                confianza = 0.9
                break
        
        # Si no, usar vocabulario
        if not datos["habilidad"]:
            habilidad = detectar_habilidad_por_verbo(texto)
            if habilidad:
                datos["habilidad"] = habilidad
                confianza = 0.85
            else:
                faltantes.append("habilidad")
                confianza = 0.4
        
        return AccionNormalizada(
            tipo=TipoAccionNorm.HABILIDAD,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes
        )
    
    def _normalizar_accion_generica(self, texto: str,
                                     contexto: ContextoEscena) -> AccionNormalizada:
        datos = {
            "tipo": "accion",
            "actor_id": contexto.actor_id,
            "accion_id": None
        }
        faltantes = []
        confianza = 0.5
        
        accion = detectar_accion_generica(texto)
        if accion:
            datos["accion_id"] = accion
            confianza = 0.9
        else:
            faltantes.append("accion_id")
        
        return AccionNormalizada(
            tipo=TipoAccionNorm.ACCION,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes
        )
    
    def _normalizar_objeto(self, texto: str,
                           contexto: ContextoEscena) -> AccionNormalizada:
        datos = {
            "tipo": "objeto",
            "actor_id": contexto.actor_id,
            "objeto_id": None
        }
        faltantes = ["objeto_id"]
        confianza = 0.5
        
        objetos = self._compendio.listar_objetos()
        for obj in objetos:
            if obj["nombre"].lower() in texto or obj["id"].lower() in texto:
                datos["objeto_id"] = obj["id"]
                faltantes.remove("objeto_id")
                confianza = 0.85
                break
        
        if not datos["objeto_id"] and re.search(r'\bpoci[oó]n\b', texto):
            if self._compendio.existe_objeto("pocion_curacion"):
                datos["objeto_id"] = "pocion_curacion"
                if "objeto_id" in faltantes:
                    faltantes.remove("objeto_id")
                confianza = 0.6
        
        return AccionNormalizada(
            tipo=TipoAccionNorm.OBJETO,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes
        )
    
    def _buscar_arma_en_texto(self, texto: str,
                              contexto: ContextoEscena) -> Tuple[Optional[str], float]:
        # Armas disponibles del personaje
        for arma in contexto.armas_disponibles:
            nombre_lower = arma.get("nombre", "").lower()
            if nombre_lower and nombre_lower in texto:
                return arma.get("compendio_ref") or arma.get("id"), 0.95
        
        # Compendio
        armas = self._compendio.listar_armas()
        for arma in armas:
            if arma["nombre"].lower() in texto:
                return arma["id"], 0.8
        
        # Sinónimos del vocabulario
        arma_sinonimo = buscar_sinonimo_arma(texto)
        if arma_sinonimo:
            return arma_sinonimo, 0.7
        
        return None, 0.0
    
    def _buscar_objetivo_en_texto(self, texto: str,
                                  contexto: ContextoEscena) -> Tuple[Optional[str], float]:
        for enemigo in contexto.enemigos_vivos:
            nombre_lower = enemigo.get("nombre", "").lower()
            if nombre_lower and nombre_lower in texto:
                return enemigo.get("instancia_id") or enemigo.get("id"), 0.95
        
        for enemigo in contexto.enemigos_vivos:
            nombre = enemigo.get("nombre", "").lower()
            for palabra in nombre.split():
                if len(palabra) > 3 and palabra in texto:
                    return enemigo.get("instancia_id") or enemigo.get("id"), 0.85
        
        for enemigo in contexto.enemigos_vivos:
            ref = enemigo.get("compendio_ref", "").lower()
            if ref and ref in texto:
                return enemigo.get("instancia_id") or enemigo.get("id"), 0.8
        
        return None, 0.0
    
    def _buscar_conjuro_en_texto(self, texto: str,
                                 contexto: ContextoEscena) -> Tuple[Optional[str], float]:
        for conjuro in contexto.conjuros_conocidos:
            nombre_lower = conjuro.get("nombre", "").lower()
            if nombre_lower and nombre_lower in texto:
                return conjuro.get("id"), 0.95
        
        conjuros = self._compendio.listar_conjuros()
        for conjuro in conjuros:
            nombre_lower = conjuro["nombre"].lower()
            if nombre_lower in texto or nombre_lower.replace(" ", "_") in texto:
                return conjuro["id"], 0.8
        
        return None, 0.0
    
    def _normalizar_texto_habilidad(self, texto: str) -> str:
        reemplazos = {
            'percepción': 'percepcion', 'religión': 'religion',
            'persuasión': 'persuasion', 'intimidación': 'intimidacion',
            'investigación': 'investigacion', 'interpretación': 'interpretacion',
        }
        texto_norm = texto.lower()
        for original, reemplazo in reemplazos.items():
            texto_norm = texto_norm.replace(original, reemplazo)
        return texto_norm
    
    def _resolver_ambiguedades(self, resultado: AccionNormalizada,
                               contexto: ContextoEscena) -> AccionNormalizada:
        datos = resultado.datos.copy()
        faltantes = resultado.faltantes.copy()
        advertencias = resultado.advertencias.copy()
        confianza = resultado.confianza
        
        if "objetivo_id" in faltantes:
            if len(contexto.enemigos_vivos) == 1:
                objetivo = contexto.enemigos_vivos[0]
                datos["objetivo_id"] = objetivo.get("instancia_id") or objetivo.get("id")
                faltantes.remove("objetivo_id")
                advertencias.append(f"Objetivo inferido: {objetivo.get('nombre', 'enemigo')}")
                confianza = min(confianza + 0.1, 1.0)
            elif len(contexto.enemigos_vivos) > 1:
                nombres = [e.get("nombre", "?") for e in contexto.enemigos_vivos]
                advertencias.append(f"Múltiples objetivos: {', '.join(nombres)}")
        
        if "arma_id" in faltantes and resultado.tipo == TipoAccionNorm.ATAQUE:
            if contexto.arma_principal:
                ref = contexto.arma_principal.get("compendio_ref") or contexto.arma_principal.get("id")
                datos["arma_id"] = ref
                faltantes.remove("arma_id")
                advertencias.append(f"Arma inferida: {contexto.arma_principal.get('nombre', ref)}")
                confianza = min(confianza + 0.1, 1.0)
        
        if resultado.tipo == TipoAccionNorm.CONJURO:
            if datos.get("nivel_lanzamiento") is None and datos.get("conjuro_id"):
                conjuro = self._compendio.obtener_conjuro(datos["conjuro_id"])
                if conjuro:
                    datos["nivel_lanzamiento"] = conjuro.get("nivel", 0)
        
        return AccionNormalizada(
            tipo=resultado.tipo, datos=datos, confianza=confianza,
            faltantes=faltantes, advertencias=advertencias, fuente=resultado.fuente
        )
    
    def _fallback_llm(self, resultado: AccionNormalizada,
                      texto_original: str, contexto: ContextoEscena) -> AccionNormalizada:
        if not self._llm_callback:
            return resultado
        
        contexto_llm = {
            "texto_jugador": texto_original,
            "tipo_detectado": resultado.tipo.value,
            "datos_parciales": resultado.datos,
            "faltantes": resultado.faltantes,
            "armas_equipadas": [
                {"id": a.get("compendio_ref") or a.get("id"), "nombre": a.get("nombre")}
                for a in [contexto.arma_principal, contexto.arma_secundaria] if a
            ],
            "enemigos_vivos": [
                {"id": e.get("instancia_id") or e.get("id"), "nombre": e.get("nombre")}
                for e in contexto.enemigos_vivos
            ],
        }
        
        prompt = f"""Completa los campos faltantes de esta acción:
Texto: "{texto_original}"
Tipo: {resultado.tipo.value}
Faltantes: {resultado.faltantes}
Contexto: {contexto_llm}
Responde SOLO con JSON."""
        
        try:
            respuesta = self._llm_callback(prompt, contexto_llm)
            if respuesta and isinstance(respuesta, dict):
                for key, value in respuesta.items():
                    if value is not None:
                        resultado.datos[key] = value
                        if key in resultado.faltantes:
                            resultado.faltantes.remove(key)
                resultado.fuente = "llm"
                resultado.confianza = min(resultado.confianza + 0.15, 0.9)
        except Exception as e:
            resultado.advertencias.append(f"Error LLM: {str(e)}")
        
        return resultado
    
    def _canonizar(self, resultado: AccionNormalizada) -> AccionNormalizada:
        datos = resultado.datos
        
        if resultado.tipo == TipoAccionNorm.ATAQUE:
            datos.setdefault("subtipo", "melee")
            datos.setdefault("modo", "normal")
        elif resultado.tipo == TipoAccionNorm.CONJURO:
            datos.setdefault("nivel_lanzamiento", 1)
        elif resultado.tipo == TipoAccionNorm.MOVIMIENTO:
            datos.setdefault("distancia_pies", 0)
        
        campos_criticos = {
            TipoAccionNorm.ATAQUE: ["objetivo_id"],
            TipoAccionNorm.CONJURO: ["conjuro_id"],
            TipoAccionNorm.MOVIMIENTO: [],
            TipoAccionNorm.HABILIDAD: ["habilidad"],
            TipoAccionNorm.ACCION: ["accion_id"],
            TipoAccionNorm.OBJETO: ["objeto_id"]
        }
        
        criticos = campos_criticos.get(resultado.tipo, [])
        faltantes_criticos = [f for f in resultado.faltantes if f in criticos]
        resultado.requiere_clarificacion = len(faltantes_criticos) > 0
        
        return resultado
EOF

echo "   ✓ normalizador.py actualizado"

# -----------------------------------------------------------------------------
# 3. Crear documentación del contrato canónico
# -----------------------------------------------------------------------------
echo "→ Creando docs/esquemas/acciones_normalizadas.md..."

mkdir -p docs/esquemas

cat > docs/esquemas/acciones_normalizadas.md << 'EOF'
# Contrato Canónico: Acciones Normalizadas

Este documento define el **esquema fijo** de las acciones normalizadas.
**No modificar campos sin incrementar versión.**

Versión: 1.0
Fecha: 2025-01-07

---

## Estructura Base

Toda acción normalizada tiene estos campos:
```json
{
  "tipo": "string",           // Obligatorio: ataque|conjuro|movimiento|habilidad|accion|objeto
  "datos": {},                // Obligatorio: campos específicos según tipo
  "confianza": 0.0-1.0,       // Qué tan seguro está el normalizador
  "faltantes": [],            // Campos que no se pudieron resolver
  "advertencias": [],         // Información para el usuario/DM
  "texto_original": "string", // El texto que se normalizó
  "requiere_clarificacion": false,  // Si necesita input adicional
  "fuente": "patron|llm"      // De dónde vino la normalización
}
```

---

## Esquemas por Tipo

### Ataque
```json
{
  "tipo": "ataque",
  "atacante_id": "string",    // ID del actor (obligatorio)
  "objetivo_id": "string",    // ID del objetivo (crítico)
  "arma_id": "string",        // ID del compendio o "unarmed"
  "subtipo": "melee|ranged|unarmed",
  "modo": "normal|ventaja|desventaja"
}
```

### Conjuro
```json
{
  "tipo": "conjuro",
  "lanzador_id": "string",    // ID del actor (obligatorio)
  "objetivo_id": "string",    // ID del objetivo (puede ser null)
  "conjuro_id": "string",     // ID del compendio (crítico)
  "nivel_lanzamiento": 0-9    // Nivel de ranura a usar
}
```

### Movimiento
```json
{
  "tipo": "movimiento",
  "actor_id": "string",       // ID del actor (obligatorio)
  "distancia_pies": 0-999,    // Distancia en pies
  "destino": "string"         // Descripción del destino (puede ser null)
}
```

### Habilidad
```json
{
  "tipo": "habilidad",
  "actor_id": "string",       // ID del actor (obligatorio)
  "habilidad": "string",      // Nombre de la habilidad (crítico)
  "objetivo_id": "string"     // ID del objetivo (puede ser null)
}
```

Habilidades válidas:
- acrobacias, arcanos, atletismo, engaño, historia
- interpretacion, intimidacion, investigacion, juego_manos
- medicina, naturaleza, percepcion, perspicacia, persuasion
- religion, sigilo, supervivencia, trato_animales

### Acción Genérica
```json
{
  "tipo": "accion",
  "actor_id": "string",       // ID del actor (obligatorio)
  "accion_id": "string"       // dash|dodge|disengage|help|hide|search|ready
}
```

### Objeto
```json
{
  "tipo": "objeto",
  "actor_id": "string",       // ID del actor (obligatorio)
  "objeto_id": "string"       // ID del compendio (crítico)
}
```

---

## Campos Críticos vs Opcionales

| Tipo | Críticos (requieren clarificación) | Opcionales |
|------|-------------------------------------|------------|
| ataque | objetivo_id | arma_id, subtipo, modo |
| conjuro | conjuro_id | objetivo_id, nivel_lanzamiento |
| movimiento | (ninguno) | distancia_pies, destino |
| habilidad | habilidad | objetivo_id |
| accion | accion_id | (ninguno) |
| objeto | objeto_id | (ninguno) |

---

## Notas de Implementación

1. **IDs**: Siempre usar `compendio_ref` para armas/armaduras, no `instancia_id`
2. **Objetivos**: Usar `instancia_id` de combatientes, no `compendio_ref`
3. **Distancias**: Siempre en pies (1 casilla = 5 pies, 1 metro ≈ 3.28 pies)
4. **Confianza**: >= 0.7 se considera "completa"
5. **Fuente**: "patron" = determinista, "llm" = fallback a LLM
EOF

echo "   ✓ acciones_normalizadas.md creado"

# -----------------------------------------------------------------------------
# 4. Actualizar validador con modo estricto
# -----------------------------------------------------------------------------
echo "→ Actualizando src/motor/validador.py con modo estricto..."

cat > src/motor/validador.py << 'EOF'
"""
Validador de Acciones para D&D 5e

Este módulo valida si una acción es posible dado el estado actual del juego.
NO ejecuta las acciones, solo dice si son válidas y por qué no.

CONFIGURACIÓN:
- strict_equipment: Si True, invalida ataques con armas no equipadas
                    Si False (default), solo genera warning

PATRÓN: Inyección de dependencias
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .compendio import CompendioMotor


class TipoAccion(Enum):
    """Tipos de acción en D&D 5e."""
    ATAQUE = "ataque"
    CONJURO = "conjuro"
    HABILIDAD = "habilidad"
    MOVIMIENTO = "movimiento"
    OBJETO = "objeto"
    DASH = "dash"
    DISENGAGE = "disengage"
    DODGE = "dodge"
    HELP = "help"
    HIDE = "hide"
    READY = "ready"
    SEARCH = "search"


@dataclass
class ResultadoValidacion:
    """Resultado de validar una acción."""
    valido: bool
    razon: str
    advertencias: List[str] = None
    datos_extra: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.advertencias is None:
            self.advertencias = []
        if self.datos_extra is None:
            self.datos_extra = {}
    
    def __str__(self) -> str:
        estado = "✓ Válido" if self.valido else "✗ Inválido"
        resultado = f"{estado}: {self.razon}"
        if self.advertencias:
            resultado += f"\n  Advertencias: {', '.join(self.advertencias)}"
        return resultado


class ValidadorAcciones:
    """
    Valida si las acciones son posibles.
    
    Args:
        compendio_motor: Instancia de CompendioMotor (inyectada).
        strict_equipment: Si True, invalida ataques con armas no equipadas.
                         Si False (default), solo genera warning.
    """
    
    def __init__(self, compendio_motor: CompendioMotor, strict_equipment: bool = False):
        self._compendio = compendio_motor
        self._strict_equipment = strict_equipment
    
    # =========================================================================
    # VALIDACIÓN DE ATAQUES
    # =========================================================================
    
    def validar_ataque(self, 
                       atacante: Dict[str, Any],
                       objetivo: Dict[str, Any],
                       arma_id: str = None) -> ResultadoValidacion:
        """Valida si un ataque es posible."""
        advertencias = []
        
        # 1. Verificar que el atacante puede actuar
        validacion_estado = self._verificar_puede_actuar(atacante)
        if not validacion_estado.valido:
            return validacion_estado
        
        # 2. Verificar objetivo
        if objetivo is None:
            return ResultadoValidacion(
                valido=False,
                razon="No hay objetivo seleccionado"
            )
        
        if objetivo.get("estado_actual", {}).get("muerto", False):
            return ResultadoValidacion(
                valido=False,
                razon=f"{objetivo.get('nombre', 'El objetivo')} ya está muerto"
            )
        
        # 3. Verificar arma
        if arma_id and arma_id != "unarmed":
            arma = self._compendio.obtener_arma(arma_id)
            if arma is None:
                return ResultadoValidacion(
                    valido=False,
                    razon=f"Arma '{arma_id}' no existe en el compendio"
                )
            
            # Verificar si está equipada
            equipo = atacante.get("fuente", {}).get("equipo_equipado", {})
            arma_principal = equipo.get("arma_principal_id")
            arma_secundaria = equipo.get("arma_secundaria_id")
            
            if arma_id not in [arma_principal, arma_secundaria]:
                if self._strict_equipment:
                    # Modo estricto: invalidar
                    return ResultadoValidacion(
                        valido=False,
                        razon=f"'{arma['nombre']}' no está equipada (modo estricto activado)",
                        advertencias=["Usar interacción de objeto para equipar primero"]
                    )
                else:
                    # Modo permisivo: solo warning
                    advertencias.append(f"'{arma['nombre']}' no está equipada")
        
        return ResultadoValidacion(
            valido=True,
            razon=f"Ataque válido contra {objetivo.get('nombre', 'objetivo')}",
            advertencias=advertencias,
            datos_extra={
                "arma_id": arma_id,
                "tipo_ataque": "cuerpo a cuerpo" if arma_id is None else "con arma"
            }
        )
    
    # =========================================================================
    # VALIDACIÓN DE CONJUROS
    # =========================================================================
    
    def validar_conjuro(self,
                        lanzador: Dict[str, Any],
                        conjuro_id: str,
                        nivel_ranura: int = None,
                        objetivo: Dict[str, Any] = None) -> ResultadoValidacion:
        """Valida si se puede lanzar un conjuro."""
        advertencias = []
        
        validacion_estado = self._verificar_puede_actuar(lanzador)
        if not validacion_estado.valido:
            return validacion_estado
        
        conjuro = self._compendio.obtener_conjuro(conjuro_id)
        if conjuro is None:
            return ResultadoValidacion(
                valido=False,
                razon=f"Conjuro '{conjuro_id}' no existe en el compendio"
            )
        
        conjuros_conocidos = lanzador.get("fuente", {}).get("conjuros_conocidos", [])
        conjuros_preparados = lanzador.get("fuente", {}).get("conjuros_preparados", [])
        
        if conjuro_id not in conjuros_conocidos and conjuro_id not in conjuros_preparados:
            advertencias.append(f"'{conjuro['nombre']}' no está en conjuros conocidos/preparados")
        
        nivel_conjuro = conjuro.get("nivel", 0)
        
        if nivel_conjuro > 0:
            nivel_usar = nivel_ranura if nivel_ranura else nivel_conjuro
            
            if nivel_usar < nivel_conjuro:
                return ResultadoValidacion(
                    valido=False,
                    razon=f"'{conjuro['nombre']}' es nivel {nivel_conjuro}, no puede lanzarse con ranura de nivel {nivel_usar}"
                )
            
            recursos = lanzador.get("recursos", {})
            ranuras = recursos.get("ranuras_conjuro", {})
            ranura_key = f"nivel_{nivel_usar}"
            ranura_info = ranuras.get(ranura_key, {"disponibles": 0})
            
            if ranura_info.get("disponibles", 0) <= 0:
                return ResultadoValidacion(
                    valido=False,
                    razon=f"No quedan ranuras de nivel {nivel_usar} disponibles"
                )
        
        requiere_objetivo = conjuro.get("objetivo", "") not in ["", "personal", "self"]
        if requiere_objetivo and objetivo is None:
            advertencias.append(f"'{conjuro['nombre']}' podría requerir un objetivo")
        
        return ResultadoValidacion(
            valido=True,
            razon=f"Puede lanzar '{conjuro['nombre']}'",
            advertencias=advertencias,
            datos_extra={
                "conjuro": conjuro,
                "nivel_ranura": nivel_ranura or nivel_conjuro,
                "es_truco": nivel_conjuro == 0
            }
        )
    
    # =========================================================================
    # VALIDACIÓN DE OBJETOS
    # =========================================================================
    
    def validar_uso_objeto(self,
                           usuario: Dict[str, Any],
                           objeto_id: str,
                           instancia_id: str = None) -> ResultadoValidacion:
        """Valida si se puede usar un objeto."""
        validacion_estado = self._verificar_puede_actuar(usuario)
        if not validacion_estado.valido:
            return validacion_estado
        
        objeto = self._compendio.obtener_objeto(objeto_id)
        if objeto is None:
            return ResultadoValidacion(
                valido=False,
                razon=f"Objeto '{objeto_id}' no existe en el compendio"
            )
        
        return ResultadoValidacion(
            valido=True,
            razon=f"Puede usar '{objeto['nombre']}'",
            datos_extra={"objeto": objeto}
        )
    
    # =========================================================================
    # VALIDACIÓN DE MOVIMIENTO
    # =========================================================================
    
    def validar_movimiento(self,
                           personaje: Dict[str, Any],
                           distancia: int,
                           movimiento_usado: int = 0) -> ResultadoValidacion:
        """Valida si un movimiento es posible."""
        estado = personaje.get("estado_actual", {})
        condiciones = estado.get("condiciones", [])
        
        condiciones_inmovil = ["paralizado", "petrificado", "aturdido", "inconsciente", "agarrado", "apresado"]
        for cond in condiciones:
            if cond.lower() in condiciones_inmovil:
                return ResultadoValidacion(
                    valido=False,
                    razon=f"No puede moverse: está {cond}"
                )
        
        velocidad = personaje.get("derivados", {}).get("velocidad", 30)
        if "fuente" in personaje:
            velocidad = personaje.get("derivados", {}).get("velocidad", 
                        personaje.get("fuente", {}).get("raza", {}).get("velocidad_base", 30))
        if "velocidad" in personaje:
            velocidad = personaje["velocidad"]
        
        movimiento_restante = velocidad - movimiento_usado
        
        if distancia > movimiento_restante:
            return ResultadoValidacion(
                valido=False,
                razon=f"No tiene suficiente movimiento: necesita {distancia} pies, le quedan {movimiento_restante} pies"
            )
        
        return ResultadoValidacion(
            valido=True,
            razon=f"Puede moverse {distancia} pies (quedarán {movimiento_restante - distancia} pies)",
            datos_extra={
                "velocidad_total": velocidad,
                "movimiento_restante_despues": movimiento_restante - distancia
            }
        )
    
    # =========================================================================
    # VALIDACIÓN DE HABILIDADES
    # =========================================================================
    
    def validar_prueba_habilidad(self,
                                  personaje: Dict[str, Any],
                                  habilidad: str) -> ResultadoValidacion:
        """Valida si se puede hacer una prueba de habilidad."""
        habilidades_validas = [
            "acrobacias", "arcanos", "atletismo", "engaño", "historia",
            "interpretacion", "intimidacion", "investigacion", "juego_manos",
            "medicina", "naturaleza", "percepcion", "perspicacia", "persuasion",
            "religion", "sigilo", "supervivencia", "trato_animales"
        ]
        
        habilidad_lower = habilidad.lower().replace(" ", "_")
        
        if habilidad_lower not in habilidades_validas:
            return ResultadoValidacion(
                valido=False,
                razon=f"'{habilidad}' no es una habilidad válida",
                datos_extra={"habilidades_validas": habilidades_validas}
            )
        
        advertencias = []
        estado = personaje.get("estado_actual", {})
        condiciones = estado.get("condiciones", [])
        
        if "cegado" in condiciones and habilidad_lower == "percepcion":
            advertencias.append("Está cegado: desventaja en Percepción que dependa de la vista")
        
        if "asustado" in condiciones:
            advertencias.append("Está asustado: desventaja en pruebas mientras vea la fuente del miedo")
        
        return ResultadoValidacion(
            valido=True,
            razon=f"Puede hacer prueba de {habilidad}",
            advertencias=advertencias
        )
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _verificar_puede_actuar(self, entidad: Dict[str, Any]) -> ResultadoValidacion:
        """Verifica si una entidad puede realizar acciones."""
        nombre = entidad.get("nombre", "La entidad")
        estado = entidad.get("estado_actual", {})
        
        if "puntos_golpe_actual" in entidad:
            if entidad.get("puntos_golpe_actual", 1) <= 0:
                return ResultadoValidacion(valido=False, razon=f"{nombre} tiene 0 PG")
        
        if estado.get("muerto", False):
            return ResultadoValidacion(valido=False, razon=f"{nombre} está muerto")
        
        if estado.get("inconsciente", False):
            return ResultadoValidacion(valido=False, razon=f"{nombre} está inconsciente")
        
        condiciones = entidad.get("condiciones", [])
        if not condiciones:
            condiciones = estado.get("condiciones", [])
        
        for cond in condiciones:
            if cond.lower() in ["paralizado", "petrificado", "aturdido", "incapacitado"]:
                return ResultadoValidacion(
                    valido=False,
                    razon=f"{nombre} está {cond} y no puede actuar"
                )
        
        return ResultadoValidacion(valido=True, razon=f"{nombre} puede actuar")
    
    def validar_accion_generica(self, 
                                 tipo: TipoAccion,
                                 actor: Dict[str, Any]) -> ResultadoValidacion:
        """Valida acciones genéricas (Dash, Disengage, Dodge, etc.)."""
        validacion_estado = self._verificar_puede_actuar(actor)
        if not validacion_estado.valido:
            return validacion_estado
        
        nombre = actor.get("nombre", "El personaje")
        
        mensajes = {
            TipoAccion.DASH: f"{nombre} puede usar Dash (duplica movimiento este turno)",
            TipoAccion.DISENGAGE: f"{nombre} puede usar Disengage (no provoca ataques de oportunidad)",
            TipoAccion.DODGE: f"{nombre} puede usar Dodge (ataques contra él tienen desventaja)",
            TipoAccion.HELP: f"{nombre} puede usar Help (da ventaja a un aliado)",
            TipoAccion.HIDE: f"{nombre} puede intentar Hide (tirada de Sigilo)",
            TipoAccion.SEARCH: f"{nombre} puede usar Search (tirada de Percepción/Investigación)",
            TipoAccion.READY: f"{nombre} puede preparar una acción",
        }
        
        return ResultadoValidacion(
            valido=True,
            razon=mensajes.get(tipo, f"{nombre} puede realizar la acción")
        )
EOF

echo "   ✓ validador.py actualizado con modo estricto"

# -----------------------------------------------------------------------------
# 5. Actualizar __init__.py
# -----------------------------------------------------------------------------
echo "→ Actualizando src/motor/__init__.py..."

cat > src/motor/__init__.py << 'EOF'
"""
Motor de Reglas D&D 5e

ESTRUCTURA:
- dados.py: Sistema de tiradas genéricas
- reglas_basicas.py: Modificadores, competencia, CA
- combate_utils.py: Ataque, daño, iniciativa, salvaciones
- compendio.py: Interfaz con el compendio de datos
- validador.py: Validación de acciones
- normalizador.py: Normalización de texto a acciones
- vocabulario.py: Sinónimos y variantes de texto

PATRÓN DE INYECCIÓN:
- Los módulos internos reciben dependencias por constructor
- obtener_compendio_motor() solo debe usarse en main.py/cli.py

FLUJO DE ACCIONES:
Texto jugador → NormalizadorAcciones → ValidadorAcciones → Resolución
"""

from .dados import (
    rng, GestorAleatorio, TipoTirada, ResultadoTirada, DADOS_VALIDOS,
    tirar, tirar_dado, tirar_dados, tirar_ventaja, tirar_desventaja, parsear_expresion,
)

from .reglas_basicas import (
    calcular_modificador, obtener_bonificador_competencia,
    calcular_cd_conjuros, calcular_bonificador_ataque_conjuros,
    calcular_ca_base, calcular_carga_maxima,
)

from .combate_utils import (
    tirar_ataque, tirar_daño, tirar_salvacion, tirar_habilidad,
    tirar_iniciativa, tirar_atributos, resolver_ataque,
)

from .compendio import (
    CompendioMotor, obtener_compendio_motor, resetear_compendio_motor,
)

from .validador import (
    ValidadorAcciones, TipoAccion, ResultadoValidacion,
)

from .normalizador import (
    NormalizadorAcciones, TipoAccionNorm, AccionNormalizada, ContextoEscena,
)

from .vocabulario import (
    TipoIntencion,
    detectar_intencion_por_verbo,
    detectar_habilidad_por_verbo,
    detectar_accion_generica,
    es_ataque_desarmado,
    buscar_sinonimo_arma,
    VERBOS_INTENCION,
    VERBOS_HABILIDAD,
    SINONIMOS_ACCION_GENERICA,
    SINONIMOS_ARMA,
)

__all__ = [
    # Dados
    'rng', 'GestorAleatorio', 'TipoTirada', 'ResultadoTirada', 'DADOS_VALIDOS',
    'tirar', 'tirar_dado', 'tirar_dados', 'tirar_ventaja', 'tirar_desventaja', 'parsear_expresion',
    # Reglas
    'calcular_modificador', 'obtener_bonificador_competencia',
    'calcular_cd_conjuros', 'calcular_bonificador_ataque_conjuros',
    'calcular_ca_base', 'calcular_carga_maxima',
    # Combate
    'tirar_ataque', 'tirar_daño', 'tirar_salvacion', 'tirar_habilidad',
    'tirar_iniciativa', 'tirar_atributos', 'resolver_ataque',
    # Compendio
    'CompendioMotor', 'obtener_compendio_motor', 'resetear_compendio_motor',
    # Validador
    'ValidadorAcciones', 'TipoAccion', 'ResultadoValidacion',
    # Normalizador
    'NormalizadorAcciones', 'TipoAccionNorm', 'AccionNormalizada', 'ContextoEscena',
    # Vocabulario
    'TipoIntencion', 'detectar_intencion_por_verbo', 'detectar_habilidad_por_verbo',
    'detectar_accion_generica', 'es_ataque_desarmado', 'buscar_sinonimo_arma',
    'VERBOS_INTENCION', 'VERBOS_HABILIDAD', 'SINONIMOS_ACCION_GENERICA', 'SINONIMOS_ARMA',
]
EOF

echo "   ✓ __init__.py actualizado"

# -----------------------------------------------------------------------------
# 6. Actualizar tests para modo estricto
# -----------------------------------------------------------------------------
echo "→ Añadiendo test de modo estricto..."

cat >> tests/test_validador.py << 'EOF'


def test_modo_estricto_equipamiento():
    """Test del modo estricto de equipamiento."""
    print("13. Modo estricto de equipamiento:")
    
    compendio = CompendioMotor()
    
    personaje = {
        "nombre": "Thorin",
        "fuente": {
            "equipo_equipado": {
                "arma_principal_id": "espada_larga",
                "arma_secundaria_id": None
            }
        },
        "estado_actual": {
            "condiciones": [],
            "inconsciente": False,
            "muerto": False
        }
    }
    
    objetivo = {
        "nombre": "Goblin",
        "puntos_golpe_actual": 7,
        "estado_actual": {"muerto": False}
    }
    
    # Modo permisivo (default): arma no equipada = warning
    validador_permisivo = ValidadorAcciones(compendio, strict_equipment=False)
    resultado = validador_permisivo.validar_ataque(personaje, objetivo, "daga")
    assert resultado.valido == True
    assert len(resultado.advertencias) > 0
    print(f"   Modo permisivo (daga no equipada): válido con warning ✓")
    
    # Modo estricto: arma no equipada = inválido
    validador_estricto = ValidadorAcciones(compendio, strict_equipment=True)
    resultado = validador_estricto.validar_ataque(personaje, objetivo, "daga")
    assert resultado.valido == False
    assert "estricto" in resultado.razon.lower()
    print(f"   Modo estricto (daga no equipada): inválido ✓")
    
    # Arma equipada funciona en ambos modos
    resultado = validador_estricto.validar_ataque(personaje, objetivo, "espada_larga")
    assert resultado.valido == True
    print(f"   Modo estricto (espada equipada): válido ✓")
    
    print("   ✓ Modo estricto correcto\n")
    return True
EOF

echo "   ✓ Test de modo estricto añadido"

# -----------------------------------------------------------------------------
# 7. Verificar
# -----------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "  VERIFICACIÓN"
echo "=============================================="
echo ""

python tests/test_normalizador.py
python tests/test_validador.py

echo ""
echo "=============================================="
echo "  MEJORAS COMPLETADAS"
echo "=============================================="
echo ""
echo "1. ✓ vocabulario.py: Diccionarios centralizados de sinónimos"
echo "2. ✓ normalizador.py: Refactorizado para usar vocabulario"
echo "3. ✓ acciones_normalizadas.md: Contrato canónico documentado"
echo "4. ✓ validador.py: Modo estricto de equipamiento"
echo ""
