"""
Sistema de Tiradas de Dados para D&D 5e

Este módulo proporciona las funciones para simular tiradas de dados.

ALCANCE V1:
- Solo se soporta el formato NdX±M (ej: "2d6+3", "1d20-1")
- Expresiones compuestas (ej: "2d6+1d4+3") se implementarán en fases posteriores
- Los dados válidos por defecto son: d4, d6, d8, d10, d12, d20, d100

NOTAS SOBRE CRÍTICOS/PIFIAS:
- Los flags `critico` y `pifia` se marcan SOLO para tiradas de 1d20
- El módulo NO interpreta las consecuencias (eso lo hace el motor de reglas)
- En D&D 5e:
  - Ataques: 20 natural = crítico (doble dados daño), 1 natural = fallo automático
  - Salvaciones: NO hay crítico/pifia automático (depende de mesa)
  - Habilidades: NO hay crítico/pifia automático (depende de mesa)
- El motor de combate/reglas decidirá qué hacer con estos flags

TODO FUTURO:
- Separar en módulos: dados.py (tiradas), reglas_basicas.py (modificadores),
  combate_utils.py (ataque, daño, iniciativa)
- Soportar expresiones compuestas
- Soportar rerolls y exploding dice
"""

import random
import re
from typing import Dict, List, Optional, Tuple, Any
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
        # Para debugging: establecer semilla fija
        from motor.dados import rng
        rng.set_seed(12345)

        # Para obtener la semilla actual (guardar en partida)
        semilla = rng.get_seed()

        # Para volver a modo aleatorio
        rng.reset()
    """

    def __init__(self):
        self._seed: Optional[int] = None
        self._rng = random.Random()

    def set_seed(self, seed: int) -> None:
        """
        Establece una semilla fija para reproducibilidad.

        Args:
            seed: Valor entero para la semilla.
        """
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
# Nota: Se mantiene whitelist para V1. En futuro podría permitirse caras >= 2
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
        critico: True si es un 20 natural en d20 (solo marcador, no interpreta reglas).
        pifia: True si es un 1 natural en d20 (solo marcador, no interpreta reglas).
        es_d20: True si la tirada fue de 1d20 (útil para el motor).
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

    Nota V1: Solo se permiten dados en DADOS_VALIDOS.
    En futuro podría permitirse cualquier caras >= 2.
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
    - NO soporta rerolls ni exploding dice

    Args:
        expresion: Expresión en formato NdX, dX, NdX+M, o NdX-M.

    Returns:
        Tupla (cantidad, caras, modificador).

    Raises:
        ValueError: Si la expresión no es válida.
    """
    # Limpiar espacios
    expresion = expresion.replace(" ", "").lower()

    # Patrón: NdX+M, NdX-M, NdX, dX
    patron = r'^(\d*)d(\d+)([+-]\d+)?$'
    match = re.match(patron, expresion)

    if not match:
        raise ValueError(
            f"Expresión de dados inválida: '{expresion}'. "
            f"Formato esperado: NdX, dX, NdX+M, NdX-M (ej: '2d6+3', '1d20-1')"
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

    Nota sobre ventaja/desventaja:
        Solo aplica a tiradas de exactamente 1d20.
        Para otros dados se ignora el tipo y se hace tirada normal.
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
    # NOTA: Estos flags son solo marcadores. El motor decide las consecuencias.
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
    else:  # DESVENTAJA
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


# =============================================================================
# FUNCIONES ESPECÍFICAS DE D&D
# TODO: Considerar mover a motor/combate_utils.py en refactor futuro
# =============================================================================

def tirar_atributos(metodo: str = "4d6_drop_lowest") -> Dict[str, Any]:
    """
    Genera los 6 atributos de un personaje.

    Args:
        metodo: Método de generación.
            - "4d6_drop_lowest": Tira 4d6, descarta el menor (estándar PHB).
            - "3d6": Tira 3d6 (clásico).
            - "standard_array": Usa array estándar [15,14,13,12,10,8].

    Returns:
        Diccionario con valores y método usado.
    """
    if metodo == "standard_array":
        valores = [15, 14, 13, 12, 10, 8]
    elif metodo == "3d6":
        valores = [sum(tirar_dados(3, 6)) for _ in range(6)]
    elif metodo == "4d6_drop_lowest":
        valores = []
        for _ in range(6):
            dados = tirar_dados(4, 6)
            dados.sort()
            valores.append(sum(dados[1:]))  # Descartar el menor
    else:
        raise ValueError(f"Método desconocido: {metodo}")

    return {
        "valores": sorted(valores, reverse=True),
        "metodo": metodo
    }


def tirar_iniciativa(modificador_destreza: int,
                     otros_bonus: int = 0,
                     tipo: TipoTirada = TipoTirada.NORMAL) -> ResultadoTirada:
    """
    Tira iniciativa para un combatiente.

    Args:
        modificador_destreza: Modificador de Destreza del combatiente.
        otros_bonus: Otros bonificadores (rasgos, objetos, etc.).
        tipo: Normal, ventaja o desventaja.

    Returns:
        ResultadoTirada con el valor de iniciativa.
    """
    mod_total = modificador_destreza + otros_bonus
    if mod_total >= 0:
        expresion = f"1d20+{mod_total}"
    else:
        expresion = f"1d20{mod_total}"
    return tirar(expresion, tipo)


def tirar_ataque(bonificador_ataque: int,
                 tipo: TipoTirada = TipoTirada.NORMAL) -> ResultadoTirada:
    """
    Tira un ataque.

    NOTA: El resultado incluye flags critico/pifia.
    El motor de combate debe interpretar:
    - critico=True → doble dados de daño
    - pifia=True → fallo automático (ignorar total)

    Args:
        bonificador_ataque: Bonificador total al ataque.
        tipo: Normal, ventaja o desventaja.

    Returns:
        ResultadoTirada con flags de crítico/pifia.
    """
    if bonificador_ataque >= 0:
        expresion = f"1d20+{bonificador_ataque}"
    else:
        expresion = f"1d20{bonificador_ataque}"
    return tirar(expresion, tipo)


def tirar_daño(expresion_daño: str, critico: bool = False) -> ResultadoTirada:
    """
    Tira daño, duplicando dados en caso de crítico.

    Regla D&D 5e: En crítico se duplican los DADOS, no el modificador.

    Args:
        expresion_daño: Expresión de daño (ej: "2d6+3").
        critico: Si True, duplica los dados.

    Returns:
        ResultadoTirada con el daño total.
    """
    cantidad, caras, modificador = parsear_expresion(expresion_daño)

    if critico:
        cantidad *= 2

    nueva_expresion = f"{cantidad}d{caras}"
    if modificador > 0:
        nueva_expresion += f"+{modificador}"
    elif modificador < 0:
        nueva_expresion += str(modificador)

    return tirar(nueva_expresion)


def tirar_salvacion(modificador_salvacion: int,
                    tipo: TipoTirada = TipoTirada.NORMAL) -> ResultadoTirada:
    """
    Tira una tirada de salvación.

    NOTA: Los flags critico/pifia se marcan pero en RAW D&D 5e
    las salvaciones NO tienen crítico/pifia automático.
    El motor de reglas decide si aplicar reglas de casa.

    Args:
        modificador_salvacion: Modificador total a la salvación.
        tipo: Normal, ventaja o desventaja.

    Returns:
        ResultadoTirada para comparar contra CD.
    """
    if modificador_salvacion >= 0:
        expresion = f"1d20+{modificador_salvacion}"
    else:
        expresion = f"1d20{modificador_salvacion}"
    return tirar(expresion, tipo)


def tirar_habilidad(modificador_habilidad: int,
                    tipo: TipoTirada = TipoTirada.NORMAL) -> ResultadoTirada:
    """
    Tira una prueba de habilidad.

    NOTA: Los flags critico/pifia se marcan pero en RAW D&D 5e
    las pruebas de habilidad NO tienen crítico/pifia automático.
    El motor de reglas decide si aplicar reglas de casa.

    Args:
        modificador_habilidad: Modificador total a la habilidad.
        tipo: Normal, ventaja o desventaja.

    Returns:
        ResultadoTirada para comparar contra CD.
    """
    if modificador_habilidad >= 0:
        expresion = f"1d20+{modificador_habilidad}"
    else:
        expresion = f"1d20{modificador_habilidad}"
    return tirar(expresion, tipo)


# =============================================================================
# FUNCIONES DE CÁLCULO DE REGLAS
# TODO: Considerar mover a motor/reglas_basicas.py en refactor futuro
# =============================================================================

def calcular_modificador(puntuacion: int) -> int:
    """
    Calcula el modificador a partir de una puntuación de atributo.

    Fórmula D&D 5e: (puntuación - 10) // 2

    Args:
        puntuacion: Puntuación del atributo (1-30).

    Returns:
        Modificador correspondiente (-5 a +10).
    """
    return (puntuacion - 10) // 2


def obtener_bonificador_competencia(nivel: int) -> int:
    """
    Obtiene el bonificador de competencia según el nivel.

    Tabla D&D 5e:
    - Niveles 1-4: +2
    - Niveles 5-8: +3
    - Niveles 9-12: +4
    - Niveles 13-16: +5
    - Niveles 17-20: +6

    Args:
        nivel: Nivel del personaje (1-20).

    Returns:
        Bonificador de competencia (2-6).
    """
    if nivel < 1:
        return 2
    elif nivel <= 4:
        return 2
    elif nivel <= 8:
        return 3
    elif nivel <= 12:
        return 4
    elif nivel <= 16:
        return 5
    else:
        return 6
