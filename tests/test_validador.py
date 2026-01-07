"""
Tests del validador de acciones.
Ejecutar desde la raíz: python tests/test_validador.py

PATRÓN: Usa inyección de dependencias (CompendioMotor inyectado).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from motor import (
    ValidadorAcciones,
    TipoAccion,
    ResultadoValidacion,
    CompendioMotor
)
from motor.compendio import resetear_compendio_motor


# =============================================================================
# FIXTURES: Datos de prueba
# =============================================================================

def crear_personaje_sano():
    """Crea un personaje en buen estado."""
    return {
        "nombre": "Thorin",
        "fuente": {
            "equipo_equipado": {
                "arma_principal_id": "espada_larga",
                "arma_secundaria_id": None
            },
            "conjuros_conocidos": ["proyectil_magico", "rayo_escarcha"],
            "conjuros_preparados": ["proyectil_magico"]
        },
        "derivados": {
            "velocidad": 30
        },
        "estado_actual": {
            "puntos_golpe_actual": 25,
            "condiciones": [],
            "inconsciente": False,
            "muerto": False
        },
        "recursos": {
            "ranuras_conjuro": {
                "nivel_1": {"disponibles": 2, "maximo": 2},
                "nivel_2": {"disponibles": 1, "maximo": 1}
            }
        }
    }


def crear_personaje_incapacitado():
    """Crea un personaje que no puede actuar."""
    return {
        "nombre": "Elara",
        "estado_actual": {
            "puntos_golpe_actual": 5,
            "condiciones": ["paralizado"],
            "inconsciente": False,
            "muerto": False
        }
    }


def crear_personaje_sin_ranuras():
    """Crea un personaje sin ranuras de conjuro."""
    return {
        "nombre": "Gandor",
        "fuente": {
            "conjuros_conocidos": ["proyectil_magico"],
            "conjuros_preparados": ["proyectil_magico"]
        },
        "estado_actual": {
            "condiciones": [],
            "inconsciente": False,
            "muerto": False
        },
        "recursos": {
            "ranuras_conjuro": {
                "nivel_1": {"disponibles": 0, "maximo": 2}
            }
        }
    }


def crear_monstruo_vivo():
    """Crea un monstruo vivo."""
    return {
        "nombre": "Goblin",
        "puntos_golpe_actual": 7,
        "clase_armadura": 15,
        "condiciones": [],
        "velocidad": 30
    }


def crear_monstruo_muerto():
    """Crea un monstruo muerto."""
    return {
        "nombre": "Goblin Caído",
        "puntos_golpe_actual": 0,
        "estado_actual": {
            "muerto": True
        }
    }


# =============================================================================
# TESTS
# =============================================================================

def test_ataque_basico():
    """Test de validación de ataque básico."""
    print("1. Validación de ataque básico:")

    # Crear validador con compendio inyectado
    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()
    objetivo = crear_monstruo_vivo()

    # Ataque con arma equipada
    resultado = validador.validar_ataque(personaje, objetivo, "espada_larga")
    assert resultado.valido == True
    print(f"   Ataque con espada equipada: {resultado}")

    # Ataque desarmado
    resultado = validador.validar_ataque(personaje, objetivo, None)
    assert resultado.valido == True
    print(f"   Ataque desarmado: {resultado}")

    # Ataque con arma no equipada
    resultado = validador.validar_ataque(personaje, objetivo, "daga")
    assert resultado.valido == True  # Válido pero con advertencia
    assert len(resultado.advertencias) > 0
    print(f"   Ataque con arma no equipada: {resultado}")

    print("   ✓ Ataque básico correcto\n")
    return True


def test_ataque_sin_objetivo():
    """Test de ataque sin objetivo."""
    print("2. Validación de ataque sin objetivo:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()

    resultado = validador.validar_ataque(personaje, None, "espada_larga")
    assert resultado.valido == False
    assert "objetivo" in resultado.razon.lower()
    print(f"   {resultado}")

    print("   ✓ Validación sin objetivo correcta\n")
    return True


def test_ataque_objetivo_muerto():
    """Test de ataque a objetivo muerto."""
    print("3. Validación de ataque a objetivo muerto:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()
    objetivo_muerto = crear_monstruo_muerto()

    resultado = validador.validar_ataque(personaje, objetivo_muerto, "espada_larga")
    assert resultado.valido == False
    assert "muerto" in resultado.razon.lower()
    print(f"   {resultado}")

    print("   ✓ Validación objetivo muerto correcta\n")
    return True


def test_atacante_incapacitado():
    """Test de ataque con atacante incapacitado."""
    print("4. Validación de atacante incapacitado:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje_paralizado = crear_personaje_incapacitado()
    objetivo = crear_monstruo_vivo()

    resultado = validador.validar_ataque(personaje_paralizado, objetivo, None)
    assert resultado.valido == False
    assert "paralizado" in resultado.razon.lower()
    print(f"   {resultado}")

    print("   ✓ Validación atacante incapacitado correcta\n")
    return True


def test_conjuro_valido():
    """Test de lanzamiento de conjuro válido."""
    print("5. Validación de conjuro válido:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()

    # Conjuro conocido con ranuras
    resultado = validador.validar_conjuro(personaje, "proyectil_magico", nivel_ranura=1)
    assert resultado.valido == True
    print(f"   Proyectil mágico (conocido, con ranura): {resultado}")

    # Truco (no gasta ranura)
    resultado = validador.validar_conjuro(personaje, "rayo_escarcha")
    assert resultado.valido == True
    print(f"   Rayo de escarcha (truco): {resultado}")

    print("   ✓ Conjuro válido correcto\n")
    return True


def test_conjuro_sin_ranuras():
    """Test de conjuro sin ranuras disponibles."""
    print("6. Validación de conjuro sin ranuras:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sin_ranuras()

    resultado = validador.validar_conjuro(personaje, "proyectil_magico", nivel_ranura=1)
    assert resultado.valido == False
    assert "ranura" in resultado.razon.lower()
    print(f"   {resultado}")

    print("   ✓ Validación sin ranuras correcta\n")
    return True


def test_conjuro_no_conocido():
    """Test de conjuro no conocido (advertencia, no bloqueo)."""
    print("7. Validación de conjuro no conocido:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()

    # Conjuro que existe pero no conoce
    resultado = validador.validar_conjuro(personaje, "curar_heridas", nivel_ranura=1)
    assert resultado.valido == True  # Válido pero con advertencia
    assert len(resultado.advertencias) > 0
    print(f"   {resultado}")

    print("   ✓ Validación conjuro no conocido correcta\n")
    return True


def test_movimiento():
    """Test de validación de movimiento."""
    print("8. Validación de movimiento:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()  # velocidad 30

    # Movimiento válido
    resultado = validador.validar_movimiento(personaje, 20, movimiento_usado=0)
    assert resultado.valido == True
    print(f"   Moverse 20 pies (30 disponibles): {resultado}")

    # Movimiento exacto
    resultado = validador.validar_movimiento(personaje, 30, movimiento_usado=0)
    assert resultado.valido == True
    print(f"   Moverse 30 pies (30 disponibles): {resultado}")

    # Movimiento excesivo
    resultado = validador.validar_movimiento(personaje, 35, movimiento_usado=0)
    assert resultado.valido == False
    print(f"   Moverse 35 pies (30 disponibles): {resultado}")

    # Movimiento parcial usado
    resultado = validador.validar_movimiento(personaje, 20, movimiento_usado=15)
    assert resultado.valido == False
    print(f"   Moverse 20 pies (15 usados, 15 quedan): {resultado}")

    print("   ✓ Validación de movimiento correcta\n")
    return True


def test_movimiento_condiciones():
    """Test de movimiento con condiciones."""
    print("9. Validación de movimiento con condiciones:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()
    personaje["estado_actual"]["condiciones"] = ["agarrado"]

    resultado = validador.validar_movimiento(personaje, 10, movimiento_usado=0)
    assert resultado.valido == False
    assert "agarrado" in resultado.razon.lower()
    print(f"   {resultado}")

    print("   ✓ Validación movimiento con condiciones correcta\n")
    return True


def test_acciones_genericas():
    """Test de acciones genéricas (Dash, Dodge, etc.)."""
    print("10. Validación de acciones genéricas:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()

    acciones = [TipoAccion.DASH, TipoAccion.DODGE, TipoAccion.DISENGAGE,
                TipoAccion.HELP, TipoAccion.HIDE, TipoAccion.SEARCH]

    for accion in acciones:
        resultado = validador.validar_accion_generica(accion, personaje)
        assert resultado.valido == True
        print(f"   {accion.value}: válido ✓")

    print("   ✓ Acciones genéricas correctas\n")
    return True


def test_prueba_habilidad():
    """Test de validación de prueba de habilidad."""
    print("11. Validación de prueba de habilidad:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()

    # Habilidad válida
    resultado = validador.validar_prueba_habilidad(personaje, "Atletismo")
    assert resultado.valido == True
    print(f"   Atletismo: {resultado}")

    # Habilidad inválida
    resultado = validador.validar_prueba_habilidad(personaje, "Volar")
    assert resultado.valido == False
    print(f"   Volar (inválida): {resultado}")

    # Con condición que afecta
    personaje["estado_actual"]["condiciones"] = ["cegado"]
    resultado = validador.validar_prueba_habilidad(personaje, "Percepcion")
    assert resultado.valido == True
    assert len(resultado.advertencias) > 0
    print(f"   Percepción (cegado): {resultado}")

    print("   ✓ Validación de habilidad correcta\n")
    return True


def test_inyeccion_mock():
    """Test que demuestra inyección de compendio mock."""
    print("12. Inyección de compendio mock:")

    # Crear mock
    class CompendioMock:
        def obtener_arma(self, id):
            if id == "super_espada":
                return {"id": "super_espada", "nombre": "Super Espada"}
            return None

        def obtener_conjuro(self, id):
            return None

        def obtener_objeto(self, id):
            return None

    # Inyectar mock
    from motor.compendio import CompendioMotor

    class CompendioMotorMock(CompendioMotor):
        def __init__(self, mock):
            self._compendio = mock

    compendio_mock = CompendioMotorMock(CompendioMock())
    validador = ValidadorAcciones(compendio_mock)

    personaje = crear_personaje_sano()
    objetivo = crear_monstruo_vivo()

    # Arma que existe en el mock
    resultado = validador.validar_ataque(personaje, objetivo, "super_espada")
    assert resultado.valido == True
    print(f"   Ataque con super_espada (del mock): válido ✓")

    # Arma que no existe en el mock
    resultado = validador.validar_ataque(personaje, objetivo, "espada_larga")
    assert resultado.valido == False  # No existe en el mock
    print(f"   Ataque con espada_larga (no en mock): {resultado}")

    print("   ✓ Inyección de mock correcta\n")
    return True



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

def main():
    """Ejecuta todos los tests."""
    print("\n" + "="*60)
    print("  TESTS DEL VALIDADOR DE ACCIONES")
    print("="*60 + "\n")

    tests = [
        ("Ataque básico", test_ataque_basico),
        ("Ataque sin objetivo", test_ataque_sin_objetivo),
        ("Ataque objetivo muerto", test_ataque_objetivo_muerto),
        ("Atacante incapacitado", test_atacante_incapacitado),
        ("Conjuro válido", test_conjuro_valido),
        ("Conjuro sin ranuras", test_conjuro_sin_ranuras),
        ("Conjuro no conocido", test_conjuro_no_conocido),
        ("Movimiento", test_movimiento),
        ("Movimiento condiciones", test_movimiento_condiciones),
        ("Acciones genéricas", test_acciones_genericas),
        ("Prueba habilidad", test_prueba_habilidad),
        ("Inyección mock", test_inyeccion_mock),
        ("Modo estricto equipamiento", test_modo_estricto_equipamiento),
    ]

    resultados = []
    for nombre, test_func in tests:
        try:
            exito = test_func()
            resultados.append((nombre, exito))
        except Exception as e:
            print(f"   ✗ EXCEPCIÓN: {e}\n")
            import traceback
            traceback.print_exc()
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

