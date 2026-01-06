#!/bin/bash

# =============================================================================
# Refactor: Separación del módulo motor
# Ejecutar desde la raíz del proyecto: bash separar_motor.sh
# =============================================================================

set -e

echo "=============================================="
echo "  REFACTOR: Separación del módulo motor"
echo "=============================================="
echo ""

# -----------------------------------------------------------------------------
# 1. Crear motor/dados.py (solo tiradas genéricas)
# -----------------------------------------------------------------------------
echo "→ Creando src/motor/dados.py (tiradas genéricas)..."

cat > src/motor/dados.py << 'EOF'
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
EOF

echo "   ✓ dados.py creado"

# -----------------------------------------------------------------------------
# 2. Crear motor/reglas_basicas.py
# -----------------------------------------------------------------------------
echo "→ Creando src/motor/reglas_basicas.py..."

cat > src/motor/reglas_basicas.py << 'EOF'
"""
Reglas Básicas de D&D 5e

Este módulo contiene los cálculos fundamentales de reglas:
- Modificadores de atributos
- Bonificador de competencia
- Otros cálculos derivados

No contiene lógica de tiradas (eso está en dados.py).
"""


def calcular_modificador(puntuacion: int) -> int:
    """
    Calcula el modificador a partir de una puntuación de atributo.

    Fórmula D&D 5e: (puntuación - 10) // 2

    Args:
        puntuacion: Puntuación del atributo (1-30).

    Returns:
        Modificador correspondiente (-5 a +10).

    Examples:
        >>> calcular_modificador(10)
        0
        >>> calcular_modificador(14)
        2
        >>> calcular_modificador(8)
        -1
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


def calcular_cd_conjuros(modificador_caracteristica: int,
                         bonificador_competencia: int) -> int:
    """
    Calcula la CD (Clase de Dificultad) de conjuros.

    Fórmula D&D 5e: 8 + modificador de característica + bonificador de competencia

    Args:
        modificador_caracteristica: Modificador del atributo de lanzamiento.
        bonificador_competencia: Bonificador de competencia del personaje.

    Returns:
        CD de salvación de conjuros.
    """
    return 8 + modificador_caracteristica + bonificador_competencia


def calcular_bonificador_ataque_conjuros(modificador_caracteristica: int,
                                          bonificador_competencia: int) -> int:
    """
    Calcula el bonificador de ataque con conjuros.

    Fórmula D&D 5e: modificador de característica + bonificador de competencia

    Args:
        modificador_caracteristica: Modificador del atributo de lanzamiento.
        bonificador_competencia: Bonificador de competencia del personaje.

    Returns:
        Bonificador para tiradas de ataque con conjuros.
    """
    return modificador_caracteristica + bonificador_competencia


def calcular_ca_base(armadura: dict = None,
                     mod_destreza: int = 0,
                     escudo: bool = False) -> int:
    """
    Calcula la Clase de Armadura base.

    Args:
        armadura: Diccionario con datos de armadura o None (sin armadura).
        mod_destreza: Modificador de Destreza del personaje.
        escudo: True si lleva escudo equipado.

    Returns:
        Clase de Armadura total.

    Sin armadura: 10 + mod.DES
    Con armadura: ca_base + mod.DES (limitado) + escudo
    """
    if armadura is None:
        ca = 10 + mod_destreza
    else:
        ca_base = armadura.get("ca_base", 10)
        max_mod_des = armadura.get("max_mod_destreza", None)

        if max_mod_des is not None:
            mod_aplicable = min(mod_destreza, max_mod_des)
        else:
            mod_aplicable = mod_destreza

        ca = ca_base + mod_aplicable

    if escudo:
        ca += 2

    return ca


def calcular_carga_maxima(fuerza: int, en_libras: bool = True) -> float:
    """
    Calcula la capacidad de carga máxima.

    Fórmula D&D 5e: Fuerza × 15 (en libras)

    Args:
        fuerza: Puntuación de Fuerza.
        en_libras: Si True retorna en libras, si False en kg.

    Returns:
        Capacidad de carga máxima.
    """
    carga_lb = fuerza * 15

    if en_libras:
        return carga_lb
    else:
        return carga_lb * 0.453592
EOF

echo "   ✓ reglas_basicas.py creado"

# -----------------------------------------------------------------------------
# 3. Crear motor/combate_utils.py
# -----------------------------------------------------------------------------
echo "→ Creando src/motor/combate_utils.py..."

cat > src/motor/combate_utils.py << 'EOF'
"""
Utilidades de Combate para D&D 5e

Este módulo contiene funciones para tiradas específicas de combate y acciones:
- Ataques
- Daño
- Salvaciones
- Habilidades
- Iniciativa
- Generación de atributos

Depende de:
- motor.dados para las tiradas genéricas
- motor.reglas_basicas para cálculos de reglas
"""

from typing import Dict, Any

from .dados import (
    tirar, tirar_dados, parsear_expresion,
    TipoTirada, ResultadoTirada
)


def tirar_ataque(bonificador_ataque: int,
                 tipo: TipoTirada = TipoTirada.NORMAL) -> ResultadoTirada:
    """
    Tira un ataque.

    NOTA: El resultado incluye flags critico/pifia.
    El motor de combate debe interpretar:
    - critico=True → doble dados de daño
    - pifia=True → fallo automático

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
            valores.append(sum(dados[1:]))
    else:
        raise ValueError(f"Método desconocido: {metodo}")

    return {
        "valores": sorted(valores, reverse=True),
        "metodo": metodo
    }


def resolver_ataque(tirada_ataque: ResultadoTirada,
                    ca_objetivo: int) -> Dict[str, Any]:
    """
    Resuelve si un ataque impacta.

    Args:
        tirada_ataque: Resultado de tirar_ataque().
        ca_objetivo: Clase de Armadura del objetivo.

    Returns:
        Diccionario con resultado del ataque.
    """
    # Pifia siempre falla
    if tirada_ataque.pifia:
        return {
            "impacta": False,
            "critico": False,
            "pifia": True,
            "razon": "Pifia (1 natural)"
        }

    # Crítico siempre impacta
    if tirada_ataque.critico:
        return {
            "impacta": True,
            "critico": True,
            "pifia": False,
            "razon": "Crítico (20 natural)"
        }

    # Comparar contra CA
    impacta = tirada_ataque.total >= ca_objetivo
    return {
        "impacta": impacta,
        "critico": False,
        "pifia": False,
        "razon": f"Total {tirada_ataque.total} vs CA {ca_objetivo}"
    }
EOF

echo "   ✓ combate_utils.py creado"

# -----------------------------------------------------------------------------
# 4. Actualizar motor/__init__.py
# -----------------------------------------------------------------------------
echo "→ Actualizando src/motor/__init__.py..."

cat > src/motor/__init__.py << 'EOF'
"""
Motor de Reglas D&D 5e

Este módulo contiene toda la lógica de reglas del juego.

ESTRUCTURA:
- dados.py: Sistema de tiradas genéricas
- reglas_basicas.py: Modificadores, competencia, CA
- combate_utils.py: Ataque, daño, iniciativa, salvaciones
"""

# Desde dados.py
from .dados import (
    rng,
    GestorAleatorio,
    TipoTirada,
    ResultadoTirada,
    DADOS_VALIDOS,
    tirar,
    tirar_dado,
    tirar_dados,
    tirar_ventaja,
    tirar_desventaja,
    parsear_expresion,
)

# Desde reglas_basicas.py
from .reglas_basicas import (
    calcular_modificador,
    obtener_bonificador_competencia,
    calcular_cd_conjuros,
    calcular_bonificador_ataque_conjuros,
    calcular_ca_base,
    calcular_carga_maxima,
)

# Desde combate_utils.py
from .combate_utils import (
    tirar_ataque,
    tirar_daño,
    tirar_salvacion,
    tirar_habilidad,
    tirar_iniciativa,
    tirar_atributos,
    resolver_ataque,
)

__all__ = [
    # Gestor de aleatoriedad
    'rng',
    'GestorAleatorio',

    # Tipos
    'TipoTirada',
    'ResultadoTirada',
    'DADOS_VALIDOS',

    # Tiradas genéricas
    'tirar',
    'tirar_dado',
    'tirar_dados',
    'tirar_ventaja',
    'tirar_desventaja',
    'parsear_expresion',

    # Reglas básicas
    'calcular_modificador',
    'obtener_bonificador_competencia',
    'calcular_cd_conjuros',
    'calcular_bonificador_ataque_conjuros',
    'calcular_ca_base',
    'calcular_carga_maxima',

    # Combate
    'tirar_ataque',
    'tirar_daño',
    'tirar_salvacion',
    'tirar_habilidad',
    'tirar_iniciativa',
    'tirar_atributos',
    'resolver_ataque',
]
EOF

echo "   ✓ __init__.py actualizado"

# -----------------------------------------------------------------------------
# 5. Actualizar tests
# -----------------------------------------------------------------------------
echo "→ Actualizando tests/test_dados.py..."

cat > tests/test_dados.py << 'EOF'
"""
Tests del motor de reglas.
Ejecutar desde la raíz: python tests/test_dados.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from motor import (
    # Gestor aleatoriedad
    rng,
    # Tiradas genéricas
    tirar, tirar_ventaja, tirar_desventaja,
    tirar_dado, tirar_dados, parsear_expresion,
    # Combate
    tirar_daño, tirar_ataque, tirar_salvacion,
    tirar_habilidad, tirar_iniciativa, tirar_atributos,
    resolver_ataque,
    # Reglas
    calcular_modificador, obtener_bonificador_competencia,
    calcular_cd_conjuros, calcular_ca_base, calcular_carga_maxima,
    # Tipos
    TipoTirada, DADOS_VALIDOS
)


def test_reproducibilidad_semilla():
    """Test de reproducibilidad con semilla fija."""
    print("1. Reproducibilidad con semilla:")

    rng.set_seed(12345)
    tiradas_1 = [tirar("1d20").total for _ in range(5)]

    rng.set_seed(12345)
    tiradas_2 = [tirar("1d20").total for _ in range(5)]

    assert tiradas_1 == tiradas_2, "Las tiradas con misma semilla deben ser idénticas"
    print(f"   Semilla 12345: {tiradas_1}")

    rng.reset()
    print("   ✓ Reproducibilidad correcta\n")
    return True


def test_tiradas_basicas():
    """Test de tiradas básicas."""
    print("2. Tiradas básicas:")

    resultado = tirar("1d20")
    assert 1 <= resultado.total <= 20
    assert resultado.es_d20 == True
    print(f"   1d20: {resultado}")

    resultado = tirar("2d6")
    assert 2 <= resultado.total <= 12
    assert len(resultado.dados) == 2
    print(f"   2d6: {resultado}")

    resultado = tirar("1d8+3")
    assert resultado.modificador == 3
    print(f"   1d8+3: {resultado}")

    print("   ✓ Tiradas básicas correctas\n")
    return True


def test_ventaja_desventaja():
    """Test de ventaja y desventaja."""
    print("3. Ventaja y desventaja:")

    resultado = tirar_ventaja("1d20+2")
    assert resultado.tipo_tirada == TipoTirada.VENTAJA
    assert len(resultado.dados_descartados) == 1
    print(f"   Ventaja: {resultado}")

    resultado = tirar_desventaja("1d20-1")
    assert resultado.tipo_tirada == TipoTirada.DESVENTAJA
    print(f"   Desventaja: {resultado}")

    # No aplica a otros dados
    resultado = tirar("2d6", TipoTirada.VENTAJA)
    assert resultado.tipo_tirada == TipoTirada.NORMAL
    print(f"   2d6 con ventaja (ignorada): {resultado}")

    print("   ✓ Ventaja/desventaja correctas\n")
    return True


def test_daño_critico():
    """Test de daño crítico."""
    print("4. Daño crítico:")

    resultado = tirar_daño("2d6+3", critico=False)
    assert len(resultado.dados) == 2
    print(f"   Normal: {resultado}")

    resultado = tirar_daño("2d6+3", critico=True)
    assert len(resultado.dados) == 4
    assert resultado.modificador == 3
    print(f"   Crítico: {resultado}")

    print("   ✓ Daño crítico correcto\n")
    return True


def test_resolver_ataque():
    """Test de resolución de ataque."""
    print("5. Resolución de ataque:")

    # Simular crítico
    rng.set_seed(42)
    # Buscar una semilla que dé 20
    for seed in range(1000):
        rng.set_seed(seed)
        r = tirar_ataque(5)
        if r.critico:
            resultado = resolver_ataque(r, ca_objetivo=25)
            assert resultado["impacta"] == True
            assert resultado["critico"] == True
            print(f"   Crítico impacta siempre: {resultado}")
            break

    # Ataque normal
    rng.set_seed(100)
    r = tirar_ataque(5)
    resultado = resolver_ataque(r, ca_objetivo=10)
    print(f"   Normal vs CA 10: {resultado}")

    rng.reset()
    print("   ✓ Resolución de ataque correcta\n")
    return True


def test_reglas_basicas():
    """Test de reglas básicas."""
    print("6. Reglas básicas:")

    # Modificadores
    assert calcular_modificador(10) == 0
    assert calcular_modificador(14) == 2
    assert calcular_modificador(8) == -1
    print("   Modificadores: 10→0, 14→+2, 8→-1 ✓")

    # Competencia
    assert obtener_bonificador_competencia(1) == 2
    assert obtener_bonificador_competencia(5) == 3
    assert obtener_bonificador_competencia(17) == 6
    print("   Competencia: N1→+2, N5→+3, N17→+6 ✓")

    # CD conjuros
    cd = calcular_cd_conjuros(modificador_caracteristica=3, bonificador_competencia=2)
    assert cd == 13
    print(f"   CD conjuros (mod+3, comp+2): {cd} ✓")

    # CA
    ca = calcular_ca_base(None, mod_destreza=2, escudo=False)
    assert ca == 12
    print(f"   CA sin armadura (DES+2): {ca} ✓")

    ca = calcular_ca_base({"ca_base": 14, "max_mod_destreza": 2}, mod_destreza=4, escudo=True)
    assert ca == 18  # 14 + 2 (limitado) + 2 (escudo)
    print(f"   CA cota de malla + escudo: {ca} ✓")

    # Carga
    carga = calcular_carga_maxima(15)
    assert carga == 225
    print(f"   Carga máxima (FUE 15): {carga} lb ✓")

    print("   ✓ Reglas básicas correctas\n")
    return True


def test_generacion_atributos():
    """Test de generación de atributos."""
    print("7. Generación de atributos:")

    resultado = tirar_atributos("standard_array")
    assert resultado["valores"] == [15, 14, 13, 12, 10, 8]
    print(f"   Standard array: {resultado['valores']}")

    resultado = tirar_atributos("4d6_drop_lowest")
    assert len(resultado["valores"]) == 6
    print(f"   4d6 drop lowest: {resultado['valores']}")

    print("   ✓ Generación de atributos correcta\n")
    return True


def test_serializacion():
    """Test de serialización."""
    print("8. Serialización:")

    resultado = tirar("1d20+5")
    diccionario = resultado.to_dict()

    assert "dados" in diccionario
    assert "total" in diccionario
    assert "es_d20" in diccionario
    print(f"   {resultado} → dict OK")

    print("   ✓ Serialización correcta\n")
    return True


def main():
    """Ejecuta todos los tests."""
    print("\n" + "="*60)
    print("  TESTS DEL MOTOR DE REGLAS")
    print("="*60 + "\n")

    tests = [
        ("Reproducibilidad", test_reproducibilidad_semilla),
        ("Tiradas básicas", test_tiradas_basicas),
        ("Ventaja/Desventaja", test_ventaja_desventaja),
        ("Daño crítico", test_daño_critico),
        ("Resolver ataque", test_resolver_ataque),
        ("Reglas básicas", test_reglas_basicas),
        ("Generación atributos", test_generacion_atributos),
        ("Serialización", test_serializacion),
    ]

    resultados = []
    for nombre, test_func in tests:
        try:
            exito = test_func()
            resultados.append((nombre, exito))
        except Exception as e:
            print(f"   ✗ EXCEPCIÓN: {e}\n")
            resultados.append((nombre, False))

    print("="*60)
    print("  RESUMEN")
    print("="*60)

    todos_ok = True
    for nombre, exito in resultados:
        estado = "✓" if exito else "✗"
        print(f"  {estado} {nombre}")
        if not exito:
            todos_ok = False

    print("="*60)
    if todos_ok:
        print("  ✓ TODOS LOS TESTS PASARON")
    else:
        print("  ✗ ALGUNOS TESTS FALLARON")
    print("="*60 + "\n")

    return todos_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF

echo "   ✓ test_dados.py actualizado"

# -----------------------------------------------------------------------------
# 6. Resumen
# -----------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "  REFACTOR COMPLETADO"
echo "=============================================="
echo ""
echo "Estructura del motor:"
echo "  src/motor/"
echo "  ├── __init__.py      (exporta todo)"
echo "  ├── dados.py         (tiradas genéricas)"
echo "  ├── reglas_basicas.py (modificadores, CA, carga)"
echo "  └── combate_utils.py  (ataque, daño, iniciativa)"
echo ""
echo "Siguiente paso:"
echo "  python tests/test_dados.py"
echo ""
