"""
Tests del Gestor de Combate.
Ejecutar desde la raíz: python tests/test_gestor_combate.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from motor import (
    GestorCombate,
    Combatiente,
    TipoCombatiente,
    EstadoCombate,
    CompendioMotor,
    TipoResultado,
)


# =============================================================================
# FIXTURES
# =============================================================================

def crear_pc_basico(id: str = "pc_1", nombre: str = "Thorin") -> Combatiente:
    """Crea un PC basico para tests."""
    return Combatiente(
        id=id,
        nombre=nombre,
        tipo=TipoCombatiente.PC,
        hp_maximo=25,
        hp_actual=25,
        clase_armadura=16,
        velocidad=30,
        fuerza=16,
        destreza=14,
        constitucion=14,
        arma_principal={
            "id": "espada_1",
            "compendio_ref": "espada_larga",
            "nombre": "Espada larga"
        }
    )


def crear_enemigo_basico(id: str = "goblin_1", nombre: str = "Goblin") -> Combatiente:
    """Crea un enemigo basico para tests."""
    return Combatiente(
        id=id,
        nombre=nombre,
        tipo=TipoCombatiente.NPC_ENEMIGO,
        compendio_ref="goblin",
        hp_maximo=7,
        hp_actual=7,
        clase_armadura=12,
        velocidad=30,
        fuerza=8,
        destreza=14,
    )


# =============================================================================
# TESTS
# =============================================================================

def test_agregar_combatientes():
    """Test de agregar combatientes."""
    print("1. Agregar combatientes:")
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    
    pc = crear_pc_basico()
    goblin = crear_enemigo_basico()
    
    gestor.agregar_combatiente(pc)
    gestor.agregar_combatiente(goblin)
    
    assert gestor.obtener_combatiente("pc_1") is not None
    assert gestor.obtener_combatiente("goblin_1") is not None
    assert gestor.estado == EstadoCombate.NO_INICIADO
    
    print(f"   PC: {pc.nombre}, HP: {pc.hp_actual}/{pc.hp_maximo}")
    print(f"   Enemigo: {goblin.nombre}, HP: {goblin.hp_actual}/{goblin.hp_maximo}")
    print("   OK Combatientes agregados\n")
    return True


def test_iniciar_combate():
    """Test de iniciar combate con iniciativa."""
    print("2. Iniciar combate:")
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    
    gestor.agregar_combatiente(crear_pc_basico())
    gestor.agregar_combatiente(crear_enemigo_basico())
    
    gestor.iniciar_combate()
    
    assert gestor.estado == EstadoCombate.EN_CURSO
    assert gestor.ronda_actual == 1
    
    turno = gestor.obtener_turno_actual()
    assert turno is not None
    
    print(f"   Estado: {gestor.estado.value}")
    print(f"   Ronda: {gestor.ronda_actual}")
    print(f"   Turno de: {turno.nombre} (iniciativa: {turno.iniciativa})")
    print("   OK Combate iniciado\n")
    return True


def test_orden_iniciativa():
    """Test de orden de iniciativa."""
    print("3. Orden de iniciativa:")
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    
    pc = crear_pc_basico()
    goblin1 = crear_enemigo_basico("goblin_1", "Goblin 1")
    goblin2 = crear_enemigo_basico("goblin_2", "Goblin 2")
    
    gestor.agregar_combatiente(pc)
    gestor.agregar_combatiente(goblin1)
    gestor.agregar_combatiente(goblin2)
    
    gestor.iniciar_combate()
    
    combatientes = gestor.listar_combatientes()
    assert len(combatientes) == 3
    
    for i in range(len(combatientes) - 1):
        assert combatientes[i].iniciativa >= combatientes[i + 1].iniciativa
    
    print("   Orden de iniciativa:")
    for c in combatientes:
        print(f"     {c.nombre}: {c.iniciativa}")
    print("   OK Orden correcto\n")
    return True


def test_siguiente_turno():
    """Test de avanzar turnos."""
    print("4. Siguiente turno:")
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    
    gestor.agregar_combatiente(crear_pc_basico())
    gestor.agregar_combatiente(crear_enemigo_basico())
    
    gestor.iniciar_combate()
    
    primer_turno = gestor.obtener_turno_actual()
    print(f"   Turno 1: {primer_turno.nombre}")
    
    segundo_turno = gestor.siguiente_turno()
    print(f"   Turno 2: {segundo_turno.nombre}")
    
    assert primer_turno.id != segundo_turno.id
    
    tercer_turno = gestor.siguiente_turno()
    print(f"   Turno 3 (ronda 2): {tercer_turno.nombre}")
    
    assert gestor.ronda_actual == 2
    
    print("   OK Turnos avanzan correctamente\n")
    return True


def test_contexto_escena():
    """Test de generacion de contexto de escena."""
    print("5. Contexto de escena:")
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    
    pc = crear_pc_basico()
    goblin = crear_enemigo_basico()
    
    gestor.agregar_combatiente(pc)
    gestor.agregar_combatiente(goblin)
    gestor.iniciar_combate()
    
    while gestor.obtener_turno_actual().tipo != TipoCombatiente.PC:
        gestor.siguiente_turno()
    
    contexto = gestor.obtener_contexto_escena()
    
    assert contexto.actor_id == "pc_1"
    assert contexto.actor_nombre == "Thorin"
    assert len(contexto.enemigos_vivos) == 1
    assert contexto.enemigos_vivos[0]["nombre"] == "Goblin"
    
    print(f"   Actor: {contexto.actor_nombre}")
    print(f"   Enemigos: {[e['nombre'] for e in contexto.enemigos_vivos]}")
    print(f"   Movimiento restante: {contexto.movimiento_restante}")
    print("   OK Contexto generado correctamente\n")
    return True


def test_procesar_accion():
    """Test de procesar una accion."""
    print("6. Procesar accion:")
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    
    pc = crear_pc_basico()
    goblin = crear_enemigo_basico()
    
    gestor.agregar_combatiente(pc)
    gestor.agregar_combatiente(goblin)
    gestor.iniciar_combate()
    
    while gestor.obtener_turno_actual().tipo != TipoCombatiente.PC:
        gestor.siguiente_turno()
    
    hp_antes = goblin.hp_actual
    
    resultado = gestor.procesar_accion("Ataco al goblin con mi espada")
    
    assert resultado.tipo == TipoResultado.ACCION_APLICADA
    
    print(f"   Resultado: {resultado.tipo.value}")
    print(f"   Eventos: {[e.tipo for e in resultado.eventos]}")
    print(f"   HP Goblin: {hp_antes} -> {goblin.hp_actual}")
    print("   OK Accion procesada\n")
    return True


def test_aplicar_dano():
    """Test de aplicar dano."""
    print("7. Aplicar dano:")
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    
    pc = crear_pc_basico()
    goblin = crear_enemigo_basico()
    
    gestor.agregar_combatiente(pc)
    gestor.agregar_combatiente(goblin)
    gestor.iniciar_combate()
    
    gestor._aplicar_daño("goblin_1", 5)
    
    assert goblin.hp_actual == 2
    assert not goblin.muerto
    
    print(f"   Dano aplicado: 5")
    print(f"   HP Goblin: 7 -> {goblin.hp_actual}")
    
    gestor._aplicar_daño("goblin_1", 10)
    
    assert goblin.hp_actual == 0
    assert goblin.muerto
    
    print(f"   Dano letal aplicado")
    print(f"   Goblin muerto: {goblin.muerto}")
    print("   OK Dano aplicado correctamente\n")
    return True


def test_fin_combate_victoria():
    """Test de fin de combate por victoria."""
    print("8. Fin de combate (victoria):")
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    
    pc = crear_pc_basico()
    goblin = crear_enemigo_basico()
    goblin.hp_actual = 1
    
    gestor.agregar_combatiente(pc)
    gestor.agregar_combatiente(goblin)
    gestor.iniciar_combate()
    
    while gestor.obtener_turno_actual().tipo != TipoCombatiente.PC:
        gestor.siguiente_turno()
    
    gestor._aplicar_daño("goblin_1", 10)
    gestor._verificar_fin_combate()
    
    assert gestor.combate_terminado()
    assert gestor.estado == EstadoCombate.VICTORIA
    
    print(f"   Estado: {gestor.estado.value}")
    print("   OK Victoria detectada\n")
    return True


def test_fin_combate_derrota():
    """Test de fin de combate por derrota."""
    print("9. Fin de combate (derrota):")
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    
    pc = crear_pc_basico()
    pc.hp_actual = 1
    goblin = crear_enemigo_basico()
    
    gestor.agregar_combatiente(pc)
    gestor.agregar_combatiente(goblin)
    gestor.iniciar_combate()
    
    gestor._aplicar_daño("pc_1", 10)
    gestor._verificar_fin_combate()
    
    assert pc.inconsciente
    assert gestor.combate_terminado()
    assert gestor.estado == EstadoCombate.DERROTA
    
    print(f"   PC inconsciente: {pc.inconsciente}")
    print(f"   Estado: {gestor.estado.value}")
    print("   OK Derrota detectada\n")
    return True


def test_resumen_combate():
    """Test de resumen del combate."""
    print("10. Resumen del combate:")
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    
    gestor.agregar_combatiente(crear_pc_basico())
    gestor.agregar_combatiente(crear_enemigo_basico())
    gestor.iniciar_combate()
    
    resumen = gestor.obtener_resumen()
    
    assert "estado" in resumen
    assert "ronda" in resumen
    assert "combatientes" in resumen
    assert len(resumen["combatientes"]) == 2
    
    print(f"   Estado: {resumen['estado']}")
    print(f"   Ronda: {resumen['ronda']}")
    print(f"   Turno de: {resumen['turno_de']}")
    print(f"   Combatientes: {len(resumen['combatientes'])}")
    print("   OK Resumen generado\n")
    return True


def test_reiniciar_turno():
    """Test de reinicio de recursos por turno."""
    print("11. Reinicio de turno:")
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    
    pc = crear_pc_basico()
    goblin = crear_enemigo_basico()
    
    gestor.agregar_combatiente(pc)
    gestor.agregar_combatiente(goblin)
    gestor.iniciar_combate()
    
    while gestor.obtener_turno_actual().tipo != TipoCombatiente.PC:
        gestor.siguiente_turno()
    
    pc.accion_usada = True
    pc.movimiento_usado = 20
    
    assert pc.accion_usada == True
    assert pc.movimiento_usado == 20
    
    gestor.siguiente_turno()
    gestor.siguiente_turno()
    
    assert pc.accion_usada == False
    assert pc.movimiento_usado == 0
    
    print(f"   Accion reiniciada: {not pc.accion_usada}")
    print(f"   Movimiento reiniciado: {pc.movimiento_usado == 0}")
    print("   OK Turno reiniciado correctamente\n")
    return True


def test_combate_completo():
    """Test de un combate completo."""
    print("12. Combate completo:")
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    
    pc = crear_pc_basico()
    goblin = crear_enemigo_basico()
    goblin.hp_actual = 3
    
    gestor.agregar_combatiente(pc)
    gestor.agregar_combatiente(goblin)
    gestor.iniciar_combate()
    
    rondas = 0
    max_rondas = 10
    
    while not gestor.combate_terminado() and rondas < max_rondas:
        turno = gestor.obtener_turno_actual()
        
        if turno.tipo == TipoCombatiente.PC:
            resultado = gestor.procesar_accion("Ataco al goblin")
        else:
            resultado = gestor.procesar_accion("Ataco a Thorin")
        
        print(f"   Ronda {gestor.ronda_actual}: {turno.nombre} actua")
        
        gestor.siguiente_turno()
        rondas += 1
    
    assert gestor.combate_terminado()
    print(f"   Resultado: {gestor.estado.value}")
    print(f"   Rondas totales: {gestor.ronda_actual}")
    print("   OK Combate completado\n")
    return True


def test_dano_aplicado_una_sola_vez():
    """
    Test CRITICO: Verifica que el dano se aplica exactamente una vez.
    
    Regla:
    - Pipeline produce cambios_estado (no muta)
    - GestorCombate es el unico que muta HP
    - dano_infligido.cantidad == cambio real en HP
    """
    print("13. Dano aplicado una sola vez:")
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    
    pc = crear_pc_basico()
    goblin = crear_enemigo_basico()
    goblin.hp_actual = 50
    goblin.clase_armadura = 5
    
    gestor.agregar_combatiente(pc)
    gestor.agregar_combatiente(goblin)
    gestor.iniciar_combate()
    
    while gestor.obtener_turno_actual().tipo != TipoCombatiente.PC:
        gestor.siguiente_turno()
    
    for intento in range(10):
        hp_antes = goblin.hp_actual
        
        resultado = gestor.procesar_accion("Ataco al goblin con mi espada")
        
        hp_despues = goblin.hp_actual
        
        assert resultado.tipo == TipoResultado.ACCION_APLICADA
        
        if "daño_infligido" in resultado.cambios_estado:
            dano_reportado = resultado.cambios_estado["daño_infligido"]["cantidad"]
            dano_real = hp_antes - hp_despues
            
            print(f"   HP antes: {hp_antes}")
            print(f"   HP despues: {hp_despues}")
            print(f"   Dano reportado: {dano_reportado}")
            print(f"   Dano real: {dano_real}")
            
            assert dano_reportado == dano_real, \
                f"INCONSISTENCIA! Reportado ({dano_reportado}) != Real ({dano_real})"
            
            print("   OK Dano aplicado exactamente una vez\n")
            return True
        else:
            assert hp_antes == hp_despues, "HP cambio sin dano_infligido!"
            print(f"   Intento {intento + 1}: Ataque fallo, reintentando...")
            pc.accion_usada = False
    
    print("   WARN: Todos los ataques fallaron")
    print("   OK Test pasado (HP no cambio sin dano)\n")
    return True


def main():
    """Ejecuta todos los tests."""
    print("\n" + "="*60)
    print("  TESTS DEL GESTOR DE COMBATE")
    print("="*60 + "\n")
    
    tests = [
        ("Agregar combatientes", test_agregar_combatientes),
        ("Iniciar combate", test_iniciar_combate),
        ("Orden iniciativa", test_orden_iniciativa),
        ("Siguiente turno", test_siguiente_turno),
        ("Contexto escena", test_contexto_escena),
        ("Procesar accion", test_procesar_accion),
        ("Aplicar dano", test_aplicar_dano),
        ("Fin victoria", test_fin_combate_victoria),
        ("Fin derrota", test_fin_combate_derrota),
        ("Resumen", test_resumen_combate),
        ("Reinicio turno", test_reiniciar_turno),
        ("Combate completo", test_combate_completo),
        ("Dano una sola vez", test_dano_aplicado_una_sola_vez),
    ]
    
    resultados = []
    for nombre, test_func in tests:
        try:
            exito = test_func()
            resultados.append((nombre, exito))
        except Exception as e:
            print(f"   EXCEPCION: {e}\n")
            import traceback
            traceback.print_exc()
            resultados.append((nombre, False))
    
    print("="*60)
    print("  RESUMEN")
    print("="*60)
    
    todos_ok = True
    for nombre, exito in resultados:
        estado = "OK" if exito else "FAIL"
        print(f"  {estado} {nombre}")
        if not exito:
            todos_ok = False
    
    print("="*60)
    if todos_ok:
        print("  TODOS LOS TESTS PASARON")
    else:
        print("  ALGUNOS TESTS FALLARON")
    print("="*60 + "\n")
    
    return todos_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
