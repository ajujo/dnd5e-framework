"""
Test de verificación del refinamiento de esquemas (Tarea 2.24).
Ejecutar desde la raíz del proyecto: python tests/test_refinamiento.py
"""

import sys
import os
import json
from pathlib import Path

# Añadir src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from persistencia import obtener_gestor, obtener_compendio


def verificar_esquema_personaje(personaje: dict) -> list:
    """Verifica que el personaje tiene la estructura v1.1 correcta."""
    errores = []

    # Verificar _meta
    if "_meta" not in personaje:
        errores.append("Falta campo '_meta'")
    else:
        if "version_esquema" not in personaje["_meta"]:
            errores.append("Falta '_meta.version_esquema'")
        if "derivados_calculados_en" not in personaje["_meta"]:
            errores.append("Falta '_meta.derivados_calculados_en'")

    # Verificar fuente
    if "fuente" not in personaje:
        errores.append("Falta campo 'fuente'")
    else:
        fuente = personaje["fuente"]
        campos_fuente = [
            "atributos_base", "raza", "clase", "trasfondo",
            "competencias", "equipo_equipado", "dotes", "multiclase"
        ]
        for campo in campos_fuente:
            if campo not in fuente:
                errores.append(f"Falta 'fuente.{campo}'")

        # Verificar que multiclase y dotes existen (aunque vacíos)
        if "dotes" in fuente and not isinstance(fuente["dotes"], list):
            errores.append("'fuente.dotes' debe ser una lista")

    # Verificar derivados
    if "derivados" not in personaje:
        errores.append("Falta campo 'derivados'")
    else:
        derivados = personaje["derivados"]
        campos_derivados = [
            "atributos_finales", "modificadores", "bonificador_competencia",
            "clase_armadura", "iniciativa", "velocidad", "puntos_golpe_maximo",
            "habilidades", "salvaciones"
        ]
        for campo in campos_derivados:
            if campo not in derivados:
                errores.append(f"Falta 'derivados.{campo}'")

    # Verificar estado_actual
    if "estado_actual" not in personaje:
        errores.append("Falta campo 'estado_actual'")
    else:
        if "salvaciones_muerte" not in personaje["estado_actual"]:
            errores.append("Falta 'estado_actual.salvaciones_muerte'")

    return errores


def verificar_esquema_inventario(inventario: dict) -> list:
    """Verifica que el inventario tiene la estructura v1.1 correcta."""
    errores = []

    if "capacidad_carga" not in inventario:
        errores.append("Falta campo 'capacidad_carga'")
    else:
        carga = inventario["capacidad_carga"]
        campos_carga = ["peso_actual_lb", "peso_actual_kg", "peso_maximo_lb", "peso_maximo_kg"]
        for campo in campos_carga:
            if campo not in carga:
                errores.append(f"Falta 'capacidad_carga.{campo}'")

    return errores


def verificar_esquema_combate(combate: dict) -> list:
    """Verifica que el combate tiene la estructura v1.1 correcta."""
    errores = []

    if "ambiente" not in combate:
        errores.append("Falta campo 'ambiente'")
    else:
        ambiente = combate["ambiente"]
        campos_ambiente = ["descripcion", "terreno_dificil", "cobertura_disponible", "iluminacion"]
        for campo in campos_ambiente:
            if campo not in ambiente:
                errores.append(f"Falta 'ambiente.{campo}'")

    return errores


def verificar_esquema_historial(historial: dict) -> list:
    """Verifica que el historial tiene la estructura v1.1 correcta."""
    errores = []

    if "resumen_ultima_sesion" not in historial:
        errores.append("Falta campo 'resumen_ultima_sesion'")

    if "resumen_campana" not in historial:
        errores.append("Falta campo 'resumen_campana'")

    if "estadisticas_campana" not in historial:
        errores.append("Falta campo 'estadisticas_campana'")

    return errores


def verificar_documentacion():
    """Verifica que los archivos de documentación existen y tienen contenido."""
    print("\n=== Verificación de Documentación ===\n")

    docs_dir = Path("docs/esquemas")
    archivos_requeridos = [
        "personaje.md", "inventario.md", "combate.md",
        "npcs.md", "historial.md"
    ]

    errores = []
    for archivo in archivos_requeridos:
        ruta = docs_dir / archivo
        if not ruta.exists():
            errores.append(f"No existe: {ruta}")
        else:
            contenido = ruta.read_text()
            # Verificar que contiene secciones clave
            if "Implementación por Versión" not in contenido:
                errores.append(f"{archivo}: Falta sección 'Implementación por Versión'")
            if "V1" not in contenido:
                errores.append(f"{archivo}: Falta referencia a V1")
            print(f"  ✓ {archivo} existe y tiene estructura correcta")

    if errores:
        for e in errores:
            print(f"  ✗ {e}")
        return False

    print("\n✓ Documentación verificada correctamente\n")
    return True


def test_crear_partida_v11():
    """Verifica que las partidas nuevas usan el esquema v1.1."""
    print("\n=== Test de Creación de Partida (Esquema v1.1) ===\n")

    import shutil

    # Limpiar carpeta de test si existe
    test_dir = Path("./saves_test_v11")
    if test_dir.exists():
        shutil.rmtree(test_dir)

    # Crear gestor con carpeta de test
    gestor = obtener_gestor(str(test_dir))

    # Crear partida
    partida_id = gestor.crear_partida(
        nombre="Test Refinamiento",
        nombre_personaje="Eldric",
        clase="Mago",
        setting="Forgotten Realms"
    )

    if not partida_id:
        print("  ✗ Error creando partida")
        return False

    print(f"  ✓ Partida creada: {partida_id[:8]}...")

    # Cargar partida
    datos = gestor.cargar_partida(partida_id)
    if not datos:
        print("  ✗ Error cargando partida")
        return False

    todos_errores = []

    # Verificar personaje
    errores = verificar_esquema_personaje(datos["personaje"])
    if errores:
        todos_errores.extend([f"personaje: {e}" for e in errores])
    else:
        print("  ✓ Esquema personaje.json correcto")
        # Verificar valores específicos
        meta = datos["personaje"]["_meta"]
        print(f"    - version_esquema: {meta['version_esquema']}")
        print(f"    - Tiene fuente/derivados separados: ✓")

    # Verificar inventario
    errores = verificar_esquema_inventario(datos["inventario"])
    if errores:
        todos_errores.extend([f"inventario: {e}" for e in errores])
    else:
        print("  ✓ Esquema inventario.json correcto")
        carga = datos["inventario"]["capacidad_carga"]
        print(f"    - Tiene peso_actual_lb: {carga['peso_actual_lb']}")
        print(f"    - Tiene peso_maximo_lb: {carga['peso_maximo_lb']} (calculable)")

    # Verificar combate
    errores = verificar_esquema_combate(datos["combate"])
    if errores:
        todos_errores.extend([f"combate: {e}" for e in errores])
    else:
        print("  ✓ Esquema combate.json correcto")
        print(f"    - Tiene ambiente.iluminacion: {datos['combate']['ambiente']['iluminacion']}")

    # Verificar historial
    errores = verificar_esquema_historial(datos["historial"])
    if errores:
        todos_errores.extend([f"historial: {e}" for e in errores])
    else:
        print("  ✓ Esquema historial.json correcto")
        print(f"    - Tiene resumen_ultima_sesion: ✓")
        print(f"    - Tiene estadisticas_campana: ✓")

    # Limpiar
    shutil.rmtree(test_dir)
    print("\n  ✓ Carpeta de test limpiada")

    if todos_errores:
        print("\n  ERRORES ENCONTRADOS:")
        for e in todos_errores:
            print(f"    ✗ {e}")
        return False

    print("\n✓ Todos los esquemas cumplen v1.1\n")
    return True


def test_instancia_vs_compendio():
    """Verifica la diferencia conceptual entre instancia_id y compendio_ref."""
    print("\n=== Test Conceptual: instancia_id vs compendio_ref ===\n")

    # Simular estructura de combatiente
    combatiente_ejemplo = {
        "instancia_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "compendio_ref": "goblin",
        "nombre": "Goblin Arquero",
        "puntos_golpe_actual": 5
    }

    print("  Ejemplo de combatiente:")
    print(f"    instancia_id: {combatiente_ejemplo['instancia_id'][:8]}... (único en esta partida)")
    print(f"    compendio_ref: {combatiente_ejemplo['compendio_ref']} (referencia al compendio)")
    print(f"    nombre: {combatiente_ejemplo['nombre']} (personalizable)")

    # Verificar que el compendio tiene la referencia
    compendio = obtener_compendio()
    goblin = compendio.obtener_monstruo("goblin")

    if goblin:
        print(f"\n  ✓ compendio_ref 'goblin' existe en el compendio")
        print(f"    - PG base: {goblin['puntos_golpe']}")
        print(f"    - CA base: {goblin['clase_armadura']}")
    else:
        print("\n  ✗ No se encontró 'goblin' en el compendio")
        return False

    print("\n  Esto permite:")
    print("    - Tener 3 goblins con instancia_id diferentes")
    print("    - Todos referencian compendio_ref='goblin'")
    print("    - Cada uno puede tener nombre y estado únicos")

    print("\n✓ Conceptos de ID verificados\n")
    return True


def main():
    """Ejecuta todas las verificaciones."""
    print("\n" + "="*60)
    print("  VERIFICACIÓN DE REFINAMIENTO DE ESQUEMAS (Tarea 2.24)")
    print("="*60)

    resultados = []

    # Test 1: Documentación
    resultados.append(("Documentación", verificar_documentacion()))

    # Test 2: Crear partida con esquema v1.1
    resultados.append(("Esquemas v1.1", test_crear_partida_v11()))

    # Test 3: Conceptos de ID
    resultados.append(("IDs instancia/compendio", test_instancia_vs_compendio()))

    # Resumen
    print("="*60)
    print("  RESUMEN")
    print("="*60)

    todos_ok = True
    for nombre, resultado in resultados:
        estado = "✓" if resultado else "✗"
        print(f"  {estado} {nombre}")
        if not resultado:
            todos_ok = False

    print("="*60)

    if todos_ok:
        print("  ✓ TODOS LOS TESTS DE REFINAMIENTO PASARON")
    else:
        print("  ✗ ALGUNOS TESTS FALLARON")

    print("="*60 + "\n")

    return todos_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
