"""
Test de verificación del sistema de persistencia.
Ejecutar desde la raíz del proyecto.
"""

import sys
import os

# Añadir src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from persistencia import obtener_gestor, obtener_compendio


def test_compendio():
    """Verifica que el compendio carga correctamente."""
    print("\n=== Test del Compendio ===\n")

    compendio = obtener_compendio()

    # Test monstruos
    monstruos = compendio.listar_monstruos()
    print(f"✓ Monstruos cargados: {len(monstruos)}")
    assert len(monstruos) == 5, "Deberían haber 5 monstruos"

    goblin = compendio.obtener_monstruo("goblin")
    assert goblin is not None, "Goblin debería existir"
    print(f"  - Goblin: CA {goblin['clase_armadura']}, PG {goblin['puntos_golpe']}")

    # Test armas
    armas = compendio.listar_armas()
    print(f"✓ Armas cargadas: {len(armas)}")

    espada = compendio.obtener_arma("espada_larga")
    assert espada is not None, "Espada larga debería existir"
    print(f"  - Espada larga: {espada['daño']} {espada['tipo_daño']}")

    # Test armaduras
    armaduras = compendio.listar_armaduras()
    print(f"✓ Armaduras cargadas: {len(armaduras)}")

    # Test conjuros
    conjuros = compendio.listar_conjuros()
    print(f"✓ Conjuros cargados: {len(conjuros)}")
    assert len(conjuros) == 5, "Deberían haber 5 conjuros"

    # Test búsqueda
    resultados = compendio.buscar("espada")
    print(f"✓ Búsqueda 'espada': {len(resultados['armas'])} armas encontradas")

    print("\n✓ Todos los tests del compendio pasaron\n")
    return True


def test_gestor_partidas():
    """Verifica que el gestor de partidas funciona."""
    print("\n=== Test del Gestor de Partidas ===\n")

    # Usar carpeta temporal para tests
    gestor = obtener_gestor("./saves_test")

    # Crear partida
    partida_id = gestor.crear_partida(
        nombre="Partida de Prueba",
        nombre_personaje="Thorin",
        clase="Guerrero",
        setting="Forgotten Realms"
    )

    assert partida_id is not None, "Debería crear partida"
    print(f"✓ Partida creada: {partida_id[:8]}...")

    # Listar partidas
    partidas = gestor.listar_partidas()
    assert len(partidas) >= 1, "Debería haber al menos una partida"
    print(f"✓ Partidas listadas: {len(partidas)}")

    # Cargar partida
    datos = gestor.cargar_partida(partida_id)
    assert datos is not None, "Debería cargar la partida"
    assert datos["personaje"]["nombre"] == "Thorin"
    print(f"✓ Partida cargada: personaje '{datos['personaje']['nombre']}'")

    # Guardar cambio
    datos["personaje"]["estadisticas_derivadas"]["puntos_golpe_actual"] = 25
    exito = gestor.guardar_archivo(partida_id, "personaje", datos["personaje"])
    assert exito, "Debería guardar el archivo"
    print("✓ Archivo guardado correctamente")

    # Verificar última partida
    ultima = gestor.obtener_ultima_partida()
    assert ultima == partida_id, "Debería ser la última partida"
    print("✓ Última partida registrada correctamente")

    print("\n✓ Todos los tests del gestor pasaron\n")

    # Limpiar (opcional, comentar si quieres inspeccionar)
    import shutil
    shutil.rmtree("./saves_test", ignore_errors=True)
    print("✓ Carpeta de test limpiada\n")

    return True


def main():
    """Ejecuta todos los tests."""
    print("\n" + "="*50)
    print("  TEST DE SISTEMA DE PERSISTENCIA")
    print("="*50)

    try:
        test_compendio()
        test_gestor_partidas()

        print("="*50)
        print("  ✓ TODOS LOS TESTS PASARON CORRECTAMENTE")
        print("="*50 + "\n")
        return True

    except AssertionError as e:
        print(f"\n✗ TEST FALLIDO: {e}\n")
        return False
    except Exception as e:
        print(f"\n✗ ERROR INESPERADO: {e}\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
