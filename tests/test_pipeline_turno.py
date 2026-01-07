"""
Tests del Pipeline de Turno.
Ejecutar desde la raíz: python tests/test_pipeline_turno.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from motor import (
    PipelineTurno,
    TipoResultado,
    ResultadoPipeline,
    Evento,
    CompendioMotor,
    ContextoEscena,
)


# =============================================================================
# FIXTURES
# =============================================================================

def crear_contexto_completo():
    """Crea un contexto con todos los datos necesarios."""
    return ContextoEscena(
        actor_id="pc_1",
        actor_nombre="Thorin",
        arma_principal={"id": "espada_1", "compendio_ref": "espada_larga", "nombre": "Espada larga"},
        arma_secundaria=None,
        armas_disponibles=[
            {"id": "espada_1", "compendio_ref": "espada_larga", "nombre": "Espada larga"},
            {"id": "daga_1", "compendio_ref": "daga", "nombre": "Daga"}
        ],
        conjuros_conocidos=[
            {"id": "proyectil_magico", "nombre": "Proyectil mágico"},
        ],
        ranuras_disponibles={1: 2, 2: 1},
        enemigos_vivos=[
            {"instancia_id": "goblin_1", "nombre": "Goblin", "compendio_ref": "goblin", "puntos_golpe_actual": 7},
        ],
        aliados=[],
        movimiento_restante=30,
        accion_disponible=True
    )


def crear_contexto_multiples_enemigos():
    """Crea un contexto con múltiples enemigos."""
    ctx = crear_contexto_completo()
    ctx.enemigos_vivos = [
        {"instancia_id": "goblin_1", "nombre": "Goblin", "compendio_ref": "goblin", "puntos_golpe_actual": 7},
        {"instancia_id": "goblin_2", "nombre": "Goblin arquero", "compendio_ref": "goblin", "puntos_golpe_actual": 7},
    ]
    return ctx


# =============================================================================
# TESTS
# =============================================================================

def test_accion_completa_ataque():
    """Test de una acción de ataque completa."""
    print("1. Acción completa (ataque):")
    
    compendio = CompendioMotor()
    pipeline = PipelineTurno(compendio)
    contexto = crear_contexto_completo()
    
    resultado = pipeline.procesar("Ataco al goblin con mi espada", contexto)
    
    assert resultado.tipo == TipoResultado.ACCION_APLICADA, f"Esperado ACCION_APLICADA, obtenido {resultado.tipo}"
    assert len(resultado.eventos) > 0, "Debería generar eventos"
    assert resultado.eventos[0].tipo == "ataque_realizado"
    
    print(f"   Tipo: {resultado.tipo.value}")
    print(f"   Eventos: {[e.tipo for e in resultado.eventos]}")
    print(f"   Cambios: {resultado.cambios_estado}")
    print("   ✓ Ataque completo procesado\n")
    return True


def test_clarificacion_objetivo():
    """Test de clarificación cuando faltan datos."""
    print("2. Clarificación (objetivo faltante):")
    
    compendio = CompendioMotor()
    pipeline = PipelineTurno(compendio)
    contexto = crear_contexto_multiples_enemigos()
    
    resultado = pipeline.procesar("Ataco", contexto)
    
    assert resultado.tipo == TipoResultado.NECESITA_CLARIFICAR
    assert "atacar" in resultado.pregunta.lower() or "quién" in resultado.pregunta.lower()
    assert len(resultado.opciones) == 2  # Dos goblins
    
    print(f"   Pregunta: {resultado.pregunta}")
    print(f"   Opciones: {[o.texto for o in resultado.opciones]}")
    print("   ✓ Clarificación generada correctamente\n")
    return True


def test_accion_rechazada():
    """Test de acción rechazada."""
    print("3. Acción rechazada:")
    
    compendio = CompendioMotor()
    pipeline = PipelineTurno(compendio, strict_equipment=True)
    contexto = crear_contexto_completo()
    
    # Intentar atacar con arma no equipada (modo estricto)
    resultado = pipeline.procesar("Ataco al goblin con la daga", contexto)
    
    assert resultado.tipo == TipoResultado.ACCION_RECHAZADA
    assert len(resultado.motivo) > 0
    
    print(f"   Motivo: {resultado.motivo}")
    print(f"   Sugerencia: {resultado.sugerencia}")
    print("   ✓ Acción rechazada correctamente\n")
    return True


def test_movimiento():
    """Test de acción de movimiento."""
    print("4. Movimiento:")
    
    compendio = CompendioMotor()
    pipeline = PipelineTurno(compendio)
    contexto = crear_contexto_completo()
    
    resultado = pipeline.procesar("Me muevo 20 pies hacia la puerta", contexto)
    
    assert resultado.tipo == TipoResultado.ACCION_APLICADA
    assert any(e.tipo == "movimiento_realizado" for e in resultado.eventos)
    assert resultado.cambios_estado.get("movimiento_usado") == 20
    
    print(f"   Eventos: {[e.tipo for e in resultado.eventos]}")
    print(f"   Cambios: {resultado.cambios_estado}")
    print("   ✓ Movimiento procesado\n")
    return True


def test_conjuro():
    """Test de lanzar un conjuro."""
    print("5. Conjuro:")
    
    compendio = CompendioMotor()
    pipeline = PipelineTurno(compendio)
    contexto = crear_contexto_completo()
    
    resultado = pipeline.procesar("Lanzo proyectil mágico al goblin", contexto)
    
    assert resultado.tipo == TipoResultado.ACCION_APLICADA
    assert any(e.tipo == "conjuro_lanzado" for e in resultado.eventos)
    
    print(f"   Eventos: {[e.tipo for e in resultado.eventos]}")
    print("   ✓ Conjuro procesado\n")
    return True


def test_habilidad():
    """Test de prueba de habilidad."""
    print("6. Prueba de habilidad:")
    
    compendio = CompendioMotor()
    pipeline = PipelineTurno(compendio)
    contexto = crear_contexto_completo()
    
    resultado = pipeline.procesar("Hago una prueba de percepción", contexto)
    
    assert resultado.tipo == TipoResultado.ACCION_APLICADA
    assert any(e.tipo == "prueba_habilidad" for e in resultado.eventos)
    
    evento = next(e for e in resultado.eventos if e.tipo == "prueba_habilidad")
    assert evento.datos.get("habilidad") == "percepcion"
    assert "tirada_d20" in evento.datos
    
    print(f"   Habilidad: {evento.datos.get('habilidad')}")
    print(f"   Tirada: {evento.datos.get('tirada_d20')} + {evento.datos.get('bonificador')} = {evento.datos.get('total')}")
    print("   ✓ Habilidad procesada\n")
    return True


def test_accion_generica_dash():
    """Test de acción genérica (Dash)."""
    print("7. Acción genérica (Dash):")
    
    compendio = CompendioMotor()
    pipeline = PipelineTurno(compendio)
    contexto = crear_contexto_completo()
    
    resultado = pipeline.procesar("Uso Dash", contexto)
    
    assert resultado.tipo == TipoResultado.ACCION_APLICADA
    assert any(e.tipo == "accion_generica" for e in resultado.eventos)
    assert resultado.cambios_estado.get("movimiento_bonus") is not None
    
    print(f"   Cambios: {resultado.cambios_estado}")
    print("   ✓ Dash procesado\n")
    return True


def test_accion_generica_dodge():
    """Test de acción genérica (Dodge)."""
    print("8. Acción genérica (Dodge):")
    
    compendio = CompendioMotor()
    pipeline = PipelineTurno(compendio)
    contexto = crear_contexto_completo()
    
    resultado = pipeline.procesar("Me pongo a esquivar", contexto)
    
    assert resultado.tipo == TipoResultado.ACCION_APLICADA
    assert resultado.cambios_estado.get("condicion_temporal") == "esquivando"
    
    print(f"   Cambios: {resultado.cambios_estado}")
    print("   ✓ Dodge procesado\n")
    return True


def test_serializacion_resultado():
    """Test de serialización del resultado."""
    print("9. Serialización:")
    
    compendio = CompendioMotor()
    pipeline = PipelineTurno(compendio)
    contexto = crear_contexto_completo()
    
    resultado = pipeline.procesar("Ataco al goblin", contexto)
    diccionario = resultado.to_dict()
    
    assert "tipo" in diccionario
    assert "eventos" in diccionario
    assert diccionario["tipo"] == "accion_aplicada"
    
    print(f"   Serializado: tipo={diccionario['tipo']}, eventos={len(diccionario['eventos'])}")
    print("   ✓ Serialización correcta\n")
    return True


def test_narrador_callback():
    """Test del callback de narrador."""
    print("10. Callback de narrador:")
    
    narrador_llamado = {"valor": False}
    
    def narrador_mock(eventos, contexto):
        narrador_llamado["valor"] = True
        return "El guerrero lanza un feroz ataque contra el goblin."
    
    compendio = CompendioMotor()
    pipeline = PipelineTurno(compendio, narrador_callback=narrador_mock)
    contexto = crear_contexto_completo()
    
    resultado = pipeline.procesar("Ataco al goblin", contexto)
    
    assert narrador_llamado["valor"] == True
    assert len(resultado.mensaje_dm) > 0
    
    print(f"   Mensaje DM: {resultado.mensaje_dm}")
    print("   ✓ Narrador callback funciona\n")
    return True


def test_flujo_completo_con_clarificacion():
    """Test de flujo completo: clarificación → respuesta."""
    print("11. Flujo completo (clarificación → respuesta):")
    
    compendio = CompendioMotor()
    pipeline = PipelineTurno(compendio)
    contexto = crear_contexto_multiples_enemigos()
    
    # Paso 1: Acción ambigua
    resultado1 = pipeline.procesar("Ataco", contexto)
    assert resultado1.tipo == TipoResultado.NECESITA_CLARIFICAR
    print(f"   1. Clarificación: {resultado1.pregunta}")
    
    # Paso 2: Respuesta con objetivo específico
    resultado2 = pipeline.procesar("Ataco al goblin arquero", contexto)
    assert resultado2.tipo == TipoResultado.ACCION_APLICADA
    print(f"   2. Acción aplicada: {[e.tipo for e in resultado2.eventos]}")
    
    print("   ✓ Flujo completo correcto\n")
    return True


def main():
    """Ejecuta todos los tests."""
    print("\n" + "="*60)
    print("  TESTS DEL PIPELINE DE TURNO")
    print("="*60 + "\n")
    
    tests = [
        ("Acción completa (ataque)", test_accion_completa_ataque),
        ("Clarificación objetivo", test_clarificacion_objetivo),
        ("Acción rechazada", test_accion_rechazada),
        ("Movimiento", test_movimiento),
        ("Conjuro", test_conjuro),
        ("Prueba de habilidad", test_habilidad),
        ("Acción genérica (Dash)", test_accion_generica_dash),
        ("Acción genérica (Dodge)", test_accion_generica_dodge),
        ("Serialización", test_serializacion_resultado),
        ("Callback narrador", test_narrador_callback),
        ("Flujo completo", test_flujo_completo_con_clarificacion),
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
