"""
Sistema de Tiradas de Dados para D&D 5e

Este módulo proporciona las funciones GENÉRICAS para simular tiradas de dados.
No contiene lógica específica de reglas D&D.

ALCANCE V1:
- Solo se soporta el formato NdX±M (ej: "2d6+3", "1d20-1")
- Expresiones compuestas (ej: "2d6+1d4+3") se implementarán en fases posteriores

NOTAS SOBRE CRÍTICOS/PIFIAS:
- Los flags `critico` y `pifia` se marcan SOLO para tiradas de 1d20
- El módulo NO interpreta las consecuencias (eso lo hace el motor de reglas)
"""

import random
import re
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# SISTEMA DE SEMILLA PARA REPRODUCIBILIDAD
# =============================================================================

class GestorAleatorio:
    """
    Gestor del generador de números aleatorios.

    Permite establecer una semilla para reproducibilidad en debugging/testing.

    Uso:
        from motor.dados import rng
        rng.set_seed(12345)  # Para debugging
        rng.reset()          # Volver a aleatorio
    """

    def __init__(self):
        self._seed: Optional[int] = None
        self._rng = random.Random()

    def set_seed(self, seed: int) -> None:
        """Establece una semilla fija para reproducibilidad."""
        self._seed = seed
        self._rng.seed(seed)

    def get_seed(self) -> Optional[int]:
        """Retorna la semilla actual o None si es aleatorio."""
        return self._seed

    def reset(self) -> None:
        """Vuelve al modo completamente aleatorio."""
        self._seed = None
        self._rng = random.Random()

    def randint(self, a: int, b: int) -> int:
        """Genera un entero aleatorio entre a y b (inclusive)."""
        return self._rng.randint(a, b)

    def generar_seed(self) -> int:
        """Genera una nueva semilla aleatoria y la retorna."""
        nueva_seed = random.randint(0, 2**32 - 1)
        self.set_seed(nueva_seed)
        return nueva_seed


# Instancia global del gestor de aleatoriedad
rng = GestorAleatorio()


# =============================================================================
# TIPOS Y ESTRUCTURAS
# =============================================================================

class TipoTirada(Enum):
    """Tipos de tirada según ventaja/desventaja."""
    NORMAL = "normal"
    VENTAJA = "ventaja"
    DESVENTAJA = "desventaja"


# Dados válidos en D&D 5e estándar
DADOS_VALIDOS = [4, 6, 8, 10, 12, 20, 100]


@dataclass
class ResultadoTirada:
    """
    Resultado detallado de una tirada de dados.

    Attributes:
        dados: Lista de valores individuales de cada dado tirado.
        total: Suma total incluyendo modificador.
        modificador: Valor fijo añadido/restado.
        expresion: La expresión original (ej: "2d6+3").
        tipo_tirada: Normal, ventaja o desventaja.
        dados_descartados: Dados no usados (en ventaja/desventaja).
        critico: True si es un 20 natural en d20 (solo marcador).
        pifia: True si es un 1 natural en d20 (solo marcador).
        es_d20: True si la tirada fue de 1d20.
    """
    dados: List[int]
    total: int
    modificador: int
    expresion: str
    tipo_tirada: TipoTirada = TipoTirada.NORMAL
    dados_descartados: List[int] = field(default_factory=list)
    critico: bool = False
    pifia: bool = False
    es_d20: bool = False

    def __str__(self) -> str:
        """Representación legible del resultado."""
        dados_str = "+".join(str(d) for d in self.dados)

        if self.modificador > 0:
            mod_str = f"+{self.modificador}"
        elif self.modificador < 0:
            mod_str = str(self.modificador)
        else:
            mod_str = ""

        resultado = f"[{dados_str}]{mod_str} = {self.total}"

        if self.dados_descartados:
            descartados = ",".join(str(d) for d in self.dados_descartados)
            resultado += f" (descartados: {descartados})"

        if self.critico:
            resultado += " ¡CRÍTICO!"
        elif self.pifia:
            resultado += " ¡PIFIA!"

        return resultado

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "dados": self.dados,
            "total": self.total,
            "modificador": self.modificador,
            "expresion": self.expresion,
            "tipo_tirada": self.tipo_tirada.value,
            "dados_descartados": self.dados_descartados,
            "critico": self.critico,
            "pifia": self.pifia,
            "es_d20": self.es_d20
        }


# =============================================================================
# FUNCIONES DE TIRADA BÁSICAS
# =============================================================================

def tirar_dado(caras: int) -> int:
    """
    Tira un único dado.

    Args:
        caras: Número de caras del dado.

    Returns:
        Valor entre 1 y caras (inclusive).

    Raises:
        ValueError: Si el número de caras no es válido.
    """
    if caras not in DADOS_VALIDOS:
        raise ValueError(
            f"Dado inválido: d{caras}. "
            f"Válidos en V1: {DADOS_VALIDOS}"
        )

    return rng.randint(1, caras)


def tirar_dados(cantidad: int, caras: int) -> List[int]:
    """
    Tira múltiples dados del mismo tipo.

    Args:
        cantidad: Número de dados a tirar.
        caras: Número de caras de cada dado.

    Returns:
        Lista con el resultado de cada dado.
    """
    if cantidad < 1:
        raise ValueError("La cantidad de dados debe ser al menos 1")

    return [tirar_dado(caras) for _ in range(cantidad)]


def parsear_expresion(expresion: str) -> Tuple[int, int, int]:
    """
    Parsea una expresión de dados tipo "2d6+3" o "1d20-2".

    LIMITACIONES V1:
    - Solo soporta formato NdX±M
    - NO soporta expresiones compuestas como "2d6+1d4+3"

    Args:
        expresion: Expresión en formato NdX, dX, NdX+M, o NdX-M.

    Returns:
        Tupla (cantidad, caras, modificador).

    Raises:
        ValueError: Si la expresión no es válida.
    """
    expresion = expresion.replace(" ", "").lower()

    patron = r'^(\d*)d(\d+)([+-]\d+)?$'
    match = re.match(patron, expresion)

    if not match:
        raise ValueError(
            f"Expresión de dados inválida: '{expresion}'. "
            f"Formato esperado: NdX, dX, NdX+M, NdX-M"
        )

    cantidad_str, caras_str, mod_str = match.groups()

    cantidad = int(cantidad_str) if cantidad_str else 1
    caras = int(caras_str)
    modificador = int(mod_str) if mod_str else 0

    return cantidad, caras, modificador


# =============================================================================
# FUNCIÓN DE TIRADA PRINCIPAL
# =============================================================================

def tirar(expresion: str,
          tipo: TipoTirada = TipoTirada.NORMAL) -> ResultadoTirada:
    """
    Realiza una tirada de dados completa.

    Args:
        expresion: Expresión de dados (ej: "1d20+5", "2d6", "d8").
        tipo: Tipo de tirada (normal, ventaja, desventaja).

    Returns:
        ResultadoTirada con todos los detalles.
    """
    cantidad, caras, modificador = parsear_expresion(expresion)

    es_d20 = (caras == 20 and cantidad == 1)

    # Ventaja/desventaja solo aplica a 1d20
    if tipo != TipoTirada.NORMAL and es_d20:
        return _tirar_con_ventaja_desventaja(modificador, expresion, tipo)

    # Tirada normal
    dados = tirar_dados(cantidad, caras)
    total = sum(dados) + modificador

    # Detectar crítico/pifia SOLO en 1d20
    critico = False
    pifia = False
    if es_d20:
        critico = dados[0] == 20
        pifia = dados[0] == 1

    return ResultadoTirada(
        dados=dados,
        total=total,
        modificador=modificador,
        expresion=expresion,
        tipo_tirada=tipo if es_d20 else TipoTirada.NORMAL,
        critico=critico,
        pifia=pifia,
        es_d20=es_d20
    )


def _tirar_con_ventaja_desventaja(modificador: int,
                                   expresion: str,
                                   tipo: TipoTirada) -> ResultadoTirada:
    """Maneja tiradas de d20 con ventaja o desventaja."""
    dado1 = tirar_dado(20)
    dado2 = tirar_dado(20)

    if tipo == TipoTirada.VENTAJA:
        elegido = max(dado1, dado2)
        descartado = min(dado1, dado2)
    else:
        elegido = min(dado1, dado2)
        descartado = max(dado1, dado2)

    total = elegido + modificador

    return ResultadoTirada(
        dados=[elegido],
        total=total,
        modificador=modificador,
        expresion=expresion,
        tipo_tirada=tipo,
        dados_descartados=[descartado],
        critico=(elegido == 20),
        pifia=(elegido == 1),
        es_d20=True
    )


# =============================================================================
# FUNCIONES DE CONVENIENCIA
# =============================================================================

def tirar_ventaja(expresion: str) -> ResultadoTirada:
    """Atajo para tirar con ventaja."""
    return tirar(expresion, TipoTirada.VENTAJA)


def tirar_desventaja(expresion: str) -> ResultadoTirada:
    """Atajo para tirar con desventaja."""
    return tirar(expresion, TipoTirada.DESVENTAJA)
