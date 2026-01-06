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
