"""
Test del sistema de dados.
Ejecutar desde la raíz: python tests/test_dados.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from motor import (
    # Gestor aleatoriedad
    rng,
    # Tiradas
    tirar, tirar_ventaja, tirar_desventaja, tirar_daño,
    tirar_ataque, tirar_salvacion, tirar_habilidad, tirar_iniciativa,
    tirar_atributos, tirar_dado, tirar_dados,
    # Utilidades
    calcular_modificador, obtener_bonificador_competencia,
    parsear_expresion,
    # Tipos
    TipoTirada, DADOS_VALIDOS
)


def test_reproducibilidad_semilla():
    """Test de reproducibilidad con semilla fija."""
    print("1. Reproducibilidad con semilla:")

    # Establecer semilla
    rng.set_seed(12345)

    # Hacer tiradas
    tiradas_1 = [tirar("1d20").total for _ in range(5)]

    # Restablecer misma semilla
    rng.set_seed(12345)

    # Hacer las mismas tiradas
    tiradas_2 = [tirar("1d20").total for _ in range(5)]

    # Deben ser idénticas
    assert tiradas_1 == tiradas_2, "Las tiradas con misma semilla deben ser idénticas"
    print(f"   Semilla 12345, tiradas: {tiradas_1}")
    print(f"   Misma semilla, tiradas: {tiradas_2}")

    # Verificar get_seed
    assert rng.get_seed() == 12345, "get_seed debe retornar la semilla actual"

    # Reset y verificar que cambia
    rng.reset()
    assert rng.get_seed() is None, "Después de reset, get_seed debe ser None"

    tiradas_3 = [tirar("1d20").total for _ in range(5)]
    # Es muy improbable que sean iguales (pero no imposible)
    print(f"   Después de reset: {tiradas_3}")

    # Generar nueva semilla
    nueva_seed = rng.generar_seed()
    assert rng.get_seed() == nueva_seed, "generar_seed debe establecer la semilla"
    print(f"   Nueva semilla generada: {nueva_seed}")

    # Limpiar para otros tests
    rng.reset()

    print("   ✓ Reproducibilidad correcta\n")
    return True


def test_tiradas_basicas():
    """Test de tiradas básicas."""
    print("2. Tiradas básicas:")

    # d20
    resultado = tirar("1d20")
    assert 1 <= resultado.total <= 20, "d20 fuera de rango"
    assert resultado.es_d20 == True, "Debe marcar es_d20"
    print(f"   1d20: {resultado}")

    # 2d6
    resultado = tirar("2d6")
    assert 2 <= resultado.total <= 12, "2d6 fuera de rango"
    assert len(resultado.dados) == 2, "2d6 debe tener 2 dados"
    assert resultado.es_d20 == False, "No debe marcar es_d20"
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

    # d100
    resultado = tirar("1d100")
    assert 1 <= resultado.total <= 100, "d100 fuera de rango"
    print(f"   1d100: {resultado}")

    print("   ✓ Tiradas básicas correctas\n")
    return True


def test_dados_validos():
    """Test de validación de dados."""
    print("3. Validación de dados:")

    # Dados válidos
    for caras in DADOS_VALIDOS:
        try:
            resultado = tirar_dado(caras)
            assert 1 <= resultado <= caras
            print(f"   d{caras}: {resultado} ✓")
        except Exception as e:
            print(f"   d{caras}: ERROR - {e}")
            return False

    # Dados inválidos
    dados_invalidos = [2, 3, 5, 7, 15, 50]
    for caras in dados_invalidos:
        try:
            tirar_dado(caras)
            print(f"   d{caras}: debería fallar pero no lo hizo")
            return False
        except ValueError:
            pass  # Correcto

    print(f"   Dados inválidos rechazados: {dados_invalidos}")

    print("   ✓ Validación de dados correcta\n")
    return True


def test_ventaja_desventaja():
    """Test de tiradas con ventaja y desventaja."""
    print("4. Ventaja y desventaja:")

    # Ventaja
    resultado = tirar_ventaja("1d20+2")
    assert resultado.tipo_tirada == TipoTirada.VENTAJA, "Tipo debe ser VENTAJA"
    assert len(resultado.dados_descartados) == 1, "Debe haber 1 dado descartado"
    assert resultado.dados[0] >= resultado.dados_descartados[0], "Ventaja debe elegir el mayor"
    assert resultado.es_d20 == True
    print(f"   Ventaja 1d20+2: {resultado}")

    # Desventaja
    resultado = tirar_desventaja("1d20-1")
    assert resultado.tipo_tirada == TipoTirada.DESVENTAJA, "Tipo debe ser DESVENTAJA"
    assert len(resultado.dados_descartados) == 1, "Debe haber 1 dado descartado"
    assert resultado.dados[0] <= resultado.dados_descartados[0], "Desventaja debe elegir el menor"
    print(f"   Desventaja 1d20-1: {resultado}")

    # Ventaja/desventaja NO aplica a otros dados
    resultado = tirar("2d6", TipoTirada.VENTAJA)
    assert resultado.tipo_tirada == TipoTirada.NORMAL, "Ventaja no debe aplicar a 2d6"
    assert len(resultado.dados_descartados) == 0, "No debe haber dados descartados"
    print(f"   2d6 con ventaja (ignorada): {resultado}")

    print("   ✓ Ventaja/desventaja correctas\n")
    return True


def test_criticos_pifias():
    """Test de detección de críticos y pifias."""
    print("5. Detección de críticos y pifias:")

    # Usar semilla para tener control
    rng.set_seed(42)

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

        # No puede ser ambos
        assert not (resultado.critico and resultado.pifia), "No puede ser crítico Y pifia"

    print(f"   En {tiradas} tiradas: {criticos} críticos ({criticos/10:.1f}%), {pifias} pifias ({pifias/10:.1f}%)")
    print(f"   (Esperado ~5% cada uno)")

    # Verificar que NO hay críticos/pifias en otros dados
    resultado = tirar("1d6")
    assert not resultado.critico, "d6 no debe tener críticos"
    assert not resultado.pifia, "d6 no debe tener pifias"
    assert not resultado.es_d20, "d6 no debe marcar es_d20"

    # Limpiar
    rng.reset()

    print("   ✓ Críticos/pifias correctos\n")
    return True


def test_daño_critico():
    """Test de daño con crítico."""
    print("6. Daño crítico:")

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
    print("7. Tiradas específicas (ataque, salvación, etc.):")

    # Ataque
    resultado = tirar_ataque(5)
    assert 6 <= resultado.total <= 25, "Ataque +5 fuera de rango"
    assert resultado.es_d20 == True
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
    print("8. Generación de atributos:")

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
    print("9. Cálculo de modificadores:")

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
    print("10. Bonificador de competencia:")

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
    print("11. Parseo de expresiones:")

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
    expresiones_invalidas = ["abc", "1x20", "d", "2d", "1d20++5", "2d6+1d4"]
    for expr in expresiones_invalidas:
        try:
            parsear_expresion(expr)
            errores.append(f"'{expr}' debería fallar pero no lo hizo")
        except ValueError:
            pass  # Correcto

    print(f"   Expresiones inválidas rechazadas: {expresiones_invalidas}")

    print("   ✓ Parseo de expresiones correcto\n")
    return len(errores) == 0


def test_serializacion():
    """Test de serialización de resultados."""
    print("12. Serialización de resultados:")

    resultado = tirar("1d20+5")
    diccionario = resultado.to_dict()

    assert "dados" in diccionario
    assert "total" in diccionario
    assert "modificador" in diccionario
    assert "expresion" in diccionario
    assert "tipo_tirada" in diccionario
    assert "critico" in diccionario
    assert "pifia" in diccionario
    assert "es_d20" in diccionario

    print(f"   Resultado: {resultado}")
    print(f"   Como dict: {diccionario}")

    print("   ✓ Serialización correcta\n")
    return True


def main():
    """Ejecuta todos los tests."""
    print("\n" + "="*60)
    print("  TEST DEL SISTEMA DE DADOS (V1)")
    print("="*60 + "\n")

    tests = [
        ("Reproducibilidad semilla", test_reproducibilidad_semilla),
        ("Tiradas básicas", test_tiradas_basicas),
        ("Validación dados", test_dados_validos),
        ("Ventaja/Desventaja", test_ventaja_desventaja),
        ("Críticos/Pifias", test_criticos_pifias),
        ("Daño crítico", test_daño_critico),
        ("Tiradas específicas", test_tiradas_especificas),
        ("Generación atributos", test_generacion_atributos),
        ("Modificadores", test_modificadores),
        ("Bonificador competencia", test_bonificador_competencia),
        ("Parseo expresiones", test_parseo_expresiones),
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
