#!/bin/bash

# =============================================================================
# TAREA 3.1: Sistema de Tiradas de Dados
# Ejecutar desde la raíz del proyecto: bash implementar_dados.sh
# =============================================================================

set -e  # Salir si hay error

echo "=============================================="
echo "  TAREA 3.1: Sistema de Tiradas de Dados"
echo "=============================================="
echo ""

# -----------------------------------------------------------------------------
# 1. Crear src/motor/dados.py
# -----------------------------------------------------------------------------
echo "→ Creando src/motor/dados.py..."

cat > src/motor/dados.py << 'EOF'
"""
Sistema de Tiradas de Dados para D&D 5e

Este módulo proporciona todas las funciones necesarias para simular
tiradas de dados según las reglas de D&D 5e.
"""

import random
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class TipoTirada(Enum):
    """Tipos de tirada según ventaja/desventaja."""
    NORMAL = "normal"
    VENTAJA = "ventaja"
    DESVENTAJA = "desventaja"


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
        critico: True si es un 20 natural en d20.
        pifia: True si es un 1 natural en d20.
    """
    dados: List[int]
    total: int
    modificador: int
    expresion: str
    tipo_tirada: TipoTirada = TipoTirada.NORMAL
    dados_descartados: List[int] = field(default_factory=list)
    critico: bool = False
    pifia: bool = False

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


def tirar_dado(caras: int) -> int:
    """
    Tira un único dado.

    Args:
        caras: Número de caras del dado (4, 6, 8, 10, 12, 20, 100).

    Returns:
        Valor entre 1 y caras (inclusive).

    Raises:
        ValueError: Si el número de caras no es válido.
    """
    dados_validos = [4, 6, 8, 10, 12, 20, 100]
    if caras not in dados_validos:
        raise ValueError(f"Dado inválido: d{caras}. Válidos: {dados_validos}")

    return random.randint(1, caras)


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

    Args:
        expresion: Expresión en formato NdX+M o NdX-M.

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
        raise ValueError(f"Expresión de dados inválida: {expresion}")

    cantidad_str, caras_str, mod_str = match.groups()

    cantidad = int(cantidad_str) if cantidad_str else 1
    caras = int(caras_str)
    modificador = int(mod_str) if mod_str else 0

    return cantidad, caras, modificador


def tirar(expresion: str,
          tipo: TipoTirada = TipoTirada.NORMAL) -> ResultadoTirada:
    """
    Realiza una tirada de dados completa.

    Args:
        expresion: Expresión de dados (ej: "1d20+5", "2d6", "d8").
        tipo: Tipo de tirada (normal, ventaja, desventaja).

    Returns:
        ResultadoTirada con todos los detalles.

    Examples:
        >>> resultado = tirar("1d20+5")
        >>> print(resultado.total)  # Entre 6 y 25

        >>> resultado = tirar("2d6+3")
        >>> print(resultado.dados)  # Ej: [4, 6]
        >>> print(resultado.total)  # Ej: 13

        >>> resultado = tirar("1d20", TipoTirada.VENTAJA)
        >>> print(resultado.dados_descartados)  # El d20 menor
    """
    cantidad, caras, modificador = parsear_expresion(expresion)

    # Caso especial: ventaja/desventaja solo aplica a d20
    if tipo != TipoTirada.NORMAL and caras == 20 and cantidad == 1:
        return _tirar_con_ventaja_desventaja(modificador, expresion, tipo)

    # Tirada normal
    dados = tirar_dados(cantidad, caras)
    total = sum(dados) + modificador

    # Detectar crítico/pifia en d20
    critico = False
    pifia = False
    if caras == 20 and cantidad == 1:
        critico = dados[0] == 20
        pifia = dados[0] == 1

    return ResultadoTirada(
        dados=dados,
        total=total,
        modificador=modificador,
        expresion=expresion,
        tipo_tirada=tipo,
        critico=critico,
        pifia=pifia
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
        pifia=(elegido == 1)
    )


def tirar_ventaja(expresion: str) -> ResultadoTirada:
    """Atajo para tirar con ventaja."""
    return tirar(expresion, TipoTirada.VENTAJA)


def tirar_desventaja(expresion: str) -> ResultadoTirada:
    """Atajo para tirar con desventaja."""
    return tirar(expresion, TipoTirada.DESVENTAJA)


def tirar_atributos(metodo: str = "4d6_drop_lowest") -> Dict[str, any]:
    """
    Genera los 6 atributos de un personaje.

    Args:
        metodo: Método de generación.
            - "4d6_drop_lowest": Tira 4d6, descarta el menor (estándar).
            - "3d6": Tira 3d6 (clásico).
            - "standard_array": Usa array estándar [15,14,13,12,10,8].

    Returns:
        Diccionario con 6 valores para asignar a atributos.
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

    Args:
        bonificador_ataque: Bonificador total al ataque.
        tipo: Normal, ventaja o desventaja.

    Returns:
        ResultadoTirada indicando si es crítico/pifia.
    """
    if bonificador_ataque >= 0:
        expresion = f"1d20+{bonificador_ataque}"
    else:
        expresion = f"1d20{bonificador_ataque}"
    return tirar(expresion, tipo)


def tirar_daño(expresion_daño: str, critico: bool = False) -> ResultadoTirada:
    """
    Tira daño, duplicando dados en caso de crítico.

    Args:
        expresion_daño: Expresión de daño (ej: "2d6+3").
        critico: Si True, duplica los dados (no el modificador).

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
# FUNCIONES DE UTILIDAD
# =============================================================================

def calcular_modificador(puntuacion: int) -> int:
    """
    Calcula el modificador a partir de una puntuación de atributo.

    Args:
        puntuacion: Puntuación del atributo (1-30).

    Returns:
        Modificador correspondiente (-5 a +10).
    """
    return (puntuacion - 10) // 2


def obtener_bonificador_competencia(nivel: int) -> int:
    """
    Obtiene el bonificador de competencia según el nivel.

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
EOF

echo "   ✓ dados.py creado"

# -----------------------------------------------------------------------------
# 2. Crear src/motor/__init__.py
# -----------------------------------------------------------------------------
echo "→ Creando src/motor/__init__.py..."

cat > src/motor/__init__.py << 'EOF'
"""
Motor de Reglas D&D 5e

Este módulo contiene toda la lógica de reglas del juego.
"""

from .dados import (
    TipoTirada,
    ResultadoTirada,
    tirar,
    tirar_dado,
    tirar_dados,
    tirar_ventaja,
    tirar_desventaja,
    tirar_ataque,
    tirar_daño,
    tirar_salvacion,
    tirar_habilidad,
    tirar_iniciativa,
    tirar_atributos,
    calcular_modificador,
    obtener_bonificador_competencia,
    parsear_expresion,
)

__all__ = [
    'TipoTirada',
    'ResultadoTirada',
    'tirar',
    'tirar_dado',
    'tirar_dados',
    'tirar_ventaja',
    'tirar_desventaja',
    'tirar_ataque',
    'tirar_daño',
    'tirar_salvacion',
    'tirar_habilidad',
    'tirar_iniciativa',
    'tirar_atributos',
    'calcular_modificador',
    'obtener_bonificador_competencia',
    'parsear_expresion',
]
EOF

echo "   ✓ __init__.py creado"

# -----------------------------------------------------------------------------
# 3. Crear tests/test_dados.py
# -----------------------------------------------------------------------------
echo "→ Creando tests/test_dados.py..."

cat > tests/test_dados.py << 'EOF'
"""
Test del sistema de dados.
Ejecutar desde la raíz: python tests/test_dados.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from motor import (
    tirar, tirar_ventaja, tirar_desventaja, tirar_daño,
    tirar_ataque, tirar_salvacion, tirar_habilidad, tirar_iniciativa,
    tirar_atributos, calcular_modificador, obtener_bonificador_competencia,
    parsear_expresion, TipoTirada
)


def test_tiradas_basicas():
    """Test de tiradas básicas."""
    print("1. Tiradas básicas:")

    # d20
    resultado = tirar("1d20")
    assert 1 <= resultado.total <= 20, "d20 fuera de rango"
    print(f"   1d20: {resultado}")

    # 2d6
    resultado = tirar("2d6")
    assert 2 <= resultado.total <= 12, "2d6 fuera de rango"
    assert len(resultado.dados) == 2, "2d6 debe tener 2 dados"
    print(f"   2d6: {resultado}")

    # 1d8+3
    resultado = tirar("1d8+3")
    assert 4 <= resultado.total <= 11, "1d8+3 fuera de rango"
    assert resultado.modificador == 3, "Modificador incorrecto"
    print(f"   1d8+3: {resultado}")

    # 1d4-1
    resultado = tirar("1d4-1")
    assert 0 <= resultado.total <= 3, "1d4-1 fuera de rango"
    assert resultado.modificador == -1, "Modificador negativo incorrecto"
    print(f"   1d4-1: {resultado}")

    # d6 (sin cantidad explícita)
    resultado = tirar("d6")
    assert 1 <= resultado.total <= 6, "d6 fuera de rango"
    print(f"   d6: {resultado}")

    print("   ✓ Tiradas básicas correctas\n")
    return True


def test_ventaja_desventaja():
    """Test de tiradas con ventaja y desventaja."""
    print("2. Ventaja y desventaja:")

    # Ventaja
    resultado = tirar_ventaja("1d20+2")
    assert resultado.tipo_tirada == TipoTirada.VENTAJA, "Tipo debe ser VENTAJA"
    assert len(resultado.dados_descartados) == 1, "Debe haber 1 dado descartado"
    assert resultado.dados[0] >= resultado.dados_descartados[0], "Ventaja debe elegir el mayor"
    print(f"   Ventaja 1d20+2: {resultado}")

    # Desventaja
    resultado = tirar_desventaja("1d20-1")
    assert resultado.tipo_tirada == TipoTirada.DESVENTAJA, "Tipo debe ser DESVENTAJA"
    assert len(resultado.dados_descartados) == 1, "Debe haber 1 dado descartado"
    assert resultado.dados[0] <= resultado.dados_descartados[0], "Desventaja debe elegir el menor"
    print(f"   Desventaja 1d20-1: {resultado}")

    print("   ✓ Ventaja/desventaja correctas\n")
    return True


def test_criticos_pifias():
    """Test de detección de críticos y pifias."""
    print("3. Detección de críticos y pifias:")

    criticos = 0
    pifias = 0
    tiradas = 1000

    for _ in range(tiradas):
        resultado = tirar("1d20")
        if resultado.critico:
            criticos += 1
            assert resultado.dados[0] == 20, "Crítico debe ser 20 natural"
        if resultado.pifia:
            pifias += 1
            assert resultado.dados[0] == 1, "Pifia debe ser 1 natural"

    # Probabilidad teórica: 5% cada uno (50 en 1000)
    print(f"   En {tiradas} tiradas: {criticos} críticos ({criticos/10:.1f}%), {pifias} pifias ({pifias/10:.1f}%)")
    print(f"   (Esperado ~5% cada uno)")

    # Verificar que no hay críticos/pifias en otros dados
    resultado = tirar("1d6")
    assert not resultado.critico, "d6 no debe tener críticos"
    assert not resultado.pifia, "d6 no debe tener pifias"

    print("   ✓ Críticos/pifias correctos\n")
    return True


def test_daño_critico():
    """Test de daño con crítico."""
    print("4. Daño crítico:")

    # Daño normal
    resultado_normal = tirar_daño("2d6+3", critico=False)
    assert len(resultado_normal.dados) == 2, "Daño normal: 2 dados"
    print(f"   Normal 2d6+3: {resultado_normal}")

    # Daño crítico (duplica dados, no modificador)
    resultado_critico = tirar_daño("2d6+3", critico=True)
    assert len(resultado_critico.dados) == 4, "Daño crítico: 4 dados"
    assert resultado_critico.modificador == 3, "Modificador no debe duplicarse"
    print(f"   Crítico 2d6+3: {resultado_critico}")

    # 1d8+5 crítico
    resultado = tirar_daño("1d8+5", critico=True)
    assert len(resultado.dados) == 2, "1d8 crítico: 2 dados"
    print(f"   Crítico 1d8+5: {resultado}")

    print("   ✓ Daño crítico correcto\n")
    return True


def test_tiradas_especificas():
    """Test de funciones de tirada específicas."""
    print("5. Tiradas específicas (ataque, salvación, etc.):")

    # Ataque
    resultado = tirar_ataque(5)
    assert 6 <= resultado.total <= 25, "Ataque +5 fuera de rango"
    print(f"   Ataque +5: {resultado}")

    resultado = tirar_ataque(-2)
    assert -1 <= resultado.total <= 18, "Ataque -2 fuera de rango"
    print(f"   Ataque -2: {resultado}")

    # Salvación
    resultado = tirar_salvacion(3)
    assert 4 <= resultado.total <= 23, "Salvación +3 fuera de rango"
    print(f"   Salvación +3: {resultado}")

    # Habilidad
    resultado = tirar_habilidad(7)
    assert 8 <= resultado.total <= 27, "Habilidad +7 fuera de rango"
    print(f"   Habilidad +7: {resultado}")

    # Iniciativa
    resultado = tirar_iniciativa(2, otros_bonus=3)
    assert 6 <= resultado.total <= 25, "Iniciativa +5 fuera de rango"
    print(f"   Iniciativa (DES+2, otros+3): {resultado}")

    print("   ✓ Tiradas específicas correctas\n")
    return True


def test_generacion_atributos():
    """Test de generación de atributos."""
    print("6. Generación de atributos:")

    # 4d6 drop lowest
    resultado = tirar_atributos("4d6_drop_lowest")
    assert len(resultado["valores"]) == 6, "Debe haber 6 valores"
    for v in resultado["valores"]:
        assert 3 <= v <= 18, f"Valor {v} fuera de rango 3-18"
    print(f"   4d6 drop lowest: {resultado['valores']}")

    # 3d6 clásico
    resultado = tirar_atributos("3d6")
    assert len(resultado["valores"]) == 6, "Debe haber 6 valores"
    for v in resultado["valores"]:
        assert 3 <= v <= 18, f"Valor {v} fuera de rango 3-18"
    print(f"   3d6 clásico: {resultado['valores']}")

    # Standard array
    resultado = tirar_atributos("standard_array")
    assert resultado["valores"] == [15, 14, 13, 12, 10, 8], "Standard array incorrecto"
    print(f"   Standard array: {resultado['valores']}")

    print("   ✓ Generación de atributos correcta\n")
    return True


def test_modificadores():
    """Test de cálculo de modificadores."""
    print("7. Cálculo de modificadores:")

    casos = [
        (1, -5), (2, -4), (3, -4), (4, -3), (5, -3),
        (6, -2), (7, -2), (8, -1), (9, -1), (10, 0),
        (11, 0), (12, 1), (13, 1), (14, 2), (15, 2),
        (16, 3), (17, 3), (18, 4), (19, 4), (20, 5),
        (21, 5), (22, 6), (24, 7), (26, 8), (28, 9), (30, 10)
    ]

    errores = []
    for puntuacion, esperado in casos:
        resultado = calcular_modificador(puntuacion)
        if resultado != esperado:
            errores.append(f"Puntuación {puntuacion}: esperado {esperado}, obtenido {resultado}")

    if errores:
        for e in errores:
            print(f"   ✗ {e}")
        return False

    # Mostrar algunos ejemplos
    ejemplos = [8, 10, 12, 14, 16, 18, 20]
    for p in ejemplos:
        print(f"   Puntuación {p:2d} → Modificador {calcular_modificador(p):+d}")

    print("   ✓ Modificadores correctos\n")
    return True


def test_bonificador_competencia():
    """Test de bonificador de competencia por nivel."""
    print("8. Bonificador de competencia:")

    casos = [
        (1, 2), (2, 2), (3, 2), (4, 2),
        (5, 3), (6, 3), (7, 3), (8, 3),
        (9, 4), (10, 4), (11, 4), (12, 4),
        (13, 5), (14, 5), (15, 5), (16, 5),
        (17, 6), (18, 6), (19, 6), (20, 6)
    ]

    errores = []
    for nivel, esperado in casos:
        resultado = obtener_bonificador_competencia(nivel)
        if resultado != esperado:
            errores.append(f"Nivel {nivel}: esperado +{esperado}, obtenido +{resultado}")

    if errores:
        for e in errores:
            print(f"   ✗ {e}")
        return False

    # Mostrar transiciones
    transiciones = [1, 4, 5, 8, 9, 12, 13, 16, 17, 20]
    for n in transiciones:
        print(f"   Nivel {n:2d} → +{obtener_bonificador_competencia(n)}")

    print("   ✓ Bonificadores de competencia correctos\n")
    return True


def test_parseo_expresiones():
    """Test de parseo de expresiones de dados."""
    print("9. Parseo de expresiones:")

    casos = [
        ("1d20", (1, 20, 0)),
        ("2d6", (2, 6, 0)),
        ("d8", (1, 8, 0)),
        ("3d6+5", (3, 6, 5)),
        ("1d20-2", (1, 20, -2)),
        ("4d6+0", (4, 6, 0)),
        ("1d100", (1, 100, 0)),
        ("2d10+10", (2, 10, 10)),
    ]

    errores = []
    for expresion, esperado in casos:
        try:
            resultado = parsear_expresion(expresion)
            if resultado != esperado:
                errores.append(f"'{expresion}': esperado {esperado}, obtenido {resultado}")
            else:
                print(f"   '{expresion}' → cantidad={resultado[0]}, caras={resultado[1]}, mod={resultado[2]}")
        except Exception as e:
            errores.append(f"'{expresion}': excepción {e}")

    if errores:
        for e in errores:
            print(f"   ✗ {e}")
        return False

    # Test de expresiones inválidas
    expresiones_invalidas = ["abc", "1x20", "d", "2d", "1d20++5"]
    for expr in expresiones_invalidas:
        try:
            parsear_expresion(expr)
            errores.append(f"'{expr}' debería fallar pero no lo hizo")
        except ValueError:
            pass  # Correcto

    print("   ✓ Parseo de expresiones correcto\n")
    return len(errores) == 0


def main():
    """Ejecuta todos los tests."""
    print("\n" + "="*60)
    print("  TEST DEL SISTEMA DE DADOS")
    print("="*60 + "\n")

    tests = [
        ("Tiradas básicas", test_tiradas_basicas),
        ("Ventaja/Desventaja", test_ventaja_desventaja),
        ("Críticos/Pifias", test_criticos_pifias),
        ("Daño crítico", test_daño_critico),
        ("Tiradas específicas", test_tiradas_especificas),
        ("Generación atributos", test_generacion_atributos),
        ("Modificadores", test_modificadores),
        ("Bonificador competencia", test_bonificador_competencia),
        ("Parseo expresiones", test_parseo_expresiones),
    ]

    resultados = []
    for nombre, test_func in tests:
        try:
            exito = test_func()
            resultados.append((nombre, exito))
        except Exception as e:
            print(f"   ✗ EXCEPCIÓN: {e}\n")
            resultados.append((nombre, False))

    # Resumen
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

echo "   ✓ test_dados.py creado"

# -----------------------------------------------------------------------------
# 4. Resumen final
# -----------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "  IMPLEMENTACIÓN COMPLETADA"
echo "=============================================="
echo ""
echo "Archivos creados:"
echo "  - src/motor/dados.py"
echo "  - src/motor/__init__.py"
echo "  - tests/test_dados.py"
echo ""
echo "Siguiente paso:"
echo "  conda activate rpg"
echo "  python tests/test_dados.py"
echo ""
