"""
Tests del Narrador LLM.
Ejecutar desde la raíz: python tests/test_narrador.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from motor import (
    NarradorLLM,
    ContextoNarracion,
    RespuestaNarrador,
    crear_contexto_narracion,
    GestorCombate,
    Combatiente,
    TipoCombatiente,
    CompendioMotor,
    TipoResultado,
    rng,
)


# =============================================================================
# FIXTURES
# =============================================================================

def crear_contexto_ataque_exitoso():
    """Crea contexto de un ataque que impacta."""
    return ContextoNarracion(
        ronda=1,
        estado_combate="en_curso",
        actor_nombre="Thorin",
        actor_hp=25,
        actor_hp_max=25,
        actor_condiciones=[],
        eventos=[
            {
                "tipo": "ataque_realizado",
                "actor_id": "pc_1",
                "datos": {
                    "objetivo_id": "goblin_1",
                    "arma_nombre": "Espada larga",
                    "tirada": {"dados": [15], "modificador": 5, "total": 20},
                    "es_critico": False,
                    "es_pifia": False,
                    "impacta": True
                }
            },
            {
                "tipo": "daño_calculado",
                "actor_id": "pc_1",
                "datos": {
                    "objetivo_id": "goblin_1",
                    "daño_total": 8,
                    "tipo_daño": "cortante"
                }
            }
        ],
        combatientes=[
            {"nombre": "Thorin", "hp_actual": 25, "hp_maximo": 25, "tipo": "pc", "muerto": False, "condiciones": []},
            {"nombre": "Goblin", "hp_actual": 0, "hp_maximo": 7, "tipo": "enemigo", "muerto": True, "condiciones": []},
        ]
    )


def crear_contexto_ataque_fallido():
    """Crea contexto de un ataque que falla."""
    return ContextoNarracion(
        ronda=1,
        estado_combate="en_curso",
        actor_nombre="Thorin",
        actor_hp=25,
        actor_hp_max=25,
        actor_condiciones=[],
        eventos=[
            {
                "tipo": "ataque_realizado",
                "actor_id": "pc_1",
                "datos": {
                    "objetivo_id": "goblin_1",
                    "arma_nombre": "Espada larga",
                    "tirada": {"dados": [5], "modificador": 5, "total": 10},
                    "es_critico": False,
                    "es_pifia": False,
                    "impacta": False
                }
            }
        ],
        combatientes=[
            {"nombre": "Thorin", "hp_actual": 25, "hp_maximo": 25, "tipo": "pc", "muerto": False, "condiciones": []},
            {"nombre": "Goblin", "hp_actual": 7, "hp_maximo": 7, "tipo": "enemigo", "muerto": False, "condiciones": []},
        ]
    )


def crear_contexto_critico():
    """Crea contexto de un crítico."""
    return ContextoNarracion(
        ronda=1,
        estado_combate="en_curso",
        actor_nombre="Thorin",
        actor_hp=25,
        actor_hp_max=25,
        actor_condiciones=[],
        eventos=[
            {
                "tipo": "ataque_realizado",
                "actor_id": "pc_1",
                "datos": {
                    "arma_nombre": "Espada larga",
                    "es_critico": True,
                    "es_pifia": False,
                    "impacta": True
                }
            },
            {
                "tipo": "daño_calculado",
                "actor_id": "pc_1",
                "datos": {"daño_total": 16, "tipo_daño": "cortante"}
            }
        ],
        combatientes=[]
    )


def crear_contexto_clarificacion():
    """Crea contexto que necesita clarificación."""
    ctx = ContextoNarracion(
        ronda=1,
        estado_combate="en_curso",
        actor_nombre="Thorin",
        actor_hp=25,
        actor_hp_max=25,
        actor_condiciones=[],
        eventos=[],
        combatientes=[],
        necesita_clarificacion=True,
        pregunta_clarificacion="¿A quién quieres atacar?",
        opciones_clarificacion=[
            {"id": "goblin_1", "texto": "Goblin"},
            {"id": "goblin_2", "texto": "Goblin arquero"}
        ]
    )
    return ctx


def crear_contexto_rechazo():
    """Crea contexto de acción rechazada."""
    return ContextoNarracion(
        ronda=1,
        estado_combate="en_curso",
        actor_nombre="Thorin",
        actor_hp=25,
        actor_hp_max=25,
        actor_condiciones=[],
        eventos=[],
        combatientes=[],
        accion_rechazada=True,
        motivo_rechazo="La daga no está equipada",
        sugerencia="Usa una interacción de objeto para equiparla primero"
    )


# =============================================================================
# TESTS
# =============================================================================

def test_narracion_sin_llm():
    """Test de narración genérica sin LLM."""
    print("1. Narración sin LLM:")
    
    narrador = NarradorLLM()  # Sin callback
    contexto = crear_contexto_ataque_exitoso()
    
    respuesta = narrador.narrar(contexto)
    
    assert isinstance(respuesta, RespuestaNarrador)
    assert len(respuesta.narracion) > 0
    assert "Thorin" in respuesta.narracion or "Ataca" in respuesta.narracion
    
    print(f"   Narración: {respuesta.narracion}")
    print("   OK Narración generada sin LLM\n")
    return True


def test_narracion_ataque_fallido():
    """Test de narración de ataque fallido."""
    print("2. Narración ataque fallido:")
    
    narrador = NarradorLLM()
    contexto = crear_contexto_ataque_fallido()
    
    respuesta = narrador.narrar(contexto)
    
    assert "falla" in respuesta.narracion.lower() or "fallo" in respuesta.narracion.lower()
    
    print(f"   Narración: {respuesta.narracion}")
    print("   OK Narración de fallo\n")
    return True


def test_narracion_critico():
    """Test de narración de crítico."""
    print("3. Narración crítico:")
    
    narrador = NarradorLLM()
    contexto = crear_contexto_critico()
    
    respuesta = narrador.narrar(contexto)
    
    assert "crítico" in respuesta.narracion.lower() or "critico" in respuesta.narracion.lower()
    
    print(f"   Narración: {respuesta.narracion}")
    print("   OK Narración de crítico\n")
    return True


def test_narracion_clarificacion():
    """Test de narración de clarificación."""
    print("4. Narración clarificación:")
    
    narrador = NarradorLLM()
    contexto = crear_contexto_clarificacion()
    
    respuesta = narrador.narrar(contexto)
    
    assert respuesta.pregunta_reformulada is not None
    
    print(f"   Narración: {respuesta.narracion}")
    print(f"   Pregunta: {respuesta.pregunta_reformulada}")
    print("   OK Clarificación narrada\n")
    return True


def test_narracion_rechazo():
    """Test de narración de rechazo."""
    print("5. Narración rechazo:")
    
    narrador = NarradorLLM()
    contexto = crear_contexto_rechazo()
    
    respuesta = narrador.narrar(contexto)
    
    assert len(respuesta.narracion) > 0
    # Debe mencionar el problema
    assert respuesta.feedback_sistema is not None
    assert "daga" in respuesta.feedback_sistema.lower() or "equipada" in respuesta.feedback_sistema.lower()
    
    print(f"   Narración: {respuesta.narracion}")
    print("   OK Rechazo narrado\n")
    return True


def test_narracion_con_llm_mock():
    """Test con un LLM mock."""
    print("6. Narración con LLM mock:")
    
    def llm_mock(prompt):
        return "¡Thorin blande su espada con furia y conecta un golpe devastador!"
    
    narrador = NarradorLLM(llm_callback=llm_mock)
    contexto = crear_contexto_ataque_exitoso()
    
    respuesta = narrador.narrar(contexto)
    
    assert "Thorin" in respuesta.narracion
    assert "espada" in respuesta.narracion
    
    print(f"   Narración: {respuesta.narracion}")
    print("   OK LLM mock funciona\n")
    return True


def test_crear_contexto_desde_gestor():
    """Test de crear contexto desde GestorCombate."""
    print("7. Crear contexto desde gestor:")
    
    rng.set_seed(42)
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    
    pc = Combatiente(
        id="pc_1", nombre="Thorin", tipo=TipoCombatiente.PC,
        hp_maximo=25, clase_armadura=16,
        arma_principal={"id": "espada_1", "compendio_ref": "espada_larga", "nombre": "Espada larga"}
    )
    goblin = Combatiente(
        id="goblin_1", nombre="Goblin", tipo=TipoCombatiente.NPC_ENEMIGO,
        hp_maximo=50, clase_armadura=5  # HP alto para que no muera
    )
    
    gestor.agregar_combatiente(pc)
    gestor.agregar_combatiente(goblin)
    gestor.iniciar_combate()
    
    while gestor.obtener_turno_actual().tipo != TipoCombatiente.PC:
        gestor.siguiente_turno()
    
    resultado = gestor.procesar_accion("Ataco al goblin")
    
    contexto = crear_contexto_narracion(gestor, resultado)
    
    assert contexto.actor_nombre == "Thorin"
    assert contexto.ronda == gestor.ronda_actual
    assert len(contexto.combatientes) == 2
    
    print(f"   Actor: {contexto.actor_nombre}")
    print(f"   Ronda: {contexto.ronda}")
    print(f"   Eventos: {len(contexto.eventos)}")
    print("   OK Contexto creado desde gestor\n")
    return True


def test_flujo_completo_con_narrador():
    """Test del flujo completo: acción -> narración."""
    print("8. Flujo completo con narrador:")
    
    rng.set_seed(100)
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    narrador = NarradorLLM()
    
    pc = Combatiente(
        id="pc_1", nombre="Thorin", tipo=TipoCombatiente.PC,
        hp_maximo=25, clase_armadura=16,
        arma_principal={"id": "espada_1", "compendio_ref": "espada_larga", "nombre": "Espada larga"}
    )
    goblin = Combatiente(
        id="goblin_1", nombre="Goblin", tipo=TipoCombatiente.NPC_ENEMIGO,
        hp_maximo=50, clase_armadura=5  # HP alto para que no muera
    )
    
    gestor.agregar_combatiente(pc)
    gestor.agregar_combatiente(goblin)
    gestor.iniciar_combate()
    
    while gestor.obtener_turno_actual().tipo != TipoCombatiente.PC:
        gestor.siguiente_turno()
    
    # 1. Procesar acción
    resultado = gestor.procesar_accion("Ataco al goblin con mi espada")
    
    # 2. Crear contexto de narración
    contexto = crear_contexto_narracion(gestor, resultado)
    
    # 3. Narrar
    respuesta = narrador.narrar(contexto)
    
    assert len(respuesta.narracion) > 0
    
    print(f"   Resultado: {resultado.tipo.value}")
    print(f"   Narración: {respuesta.narracion}")
    print("   OK Flujo completo funciona\n")
    return True


def test_guard_doble_aplicacion():
    """Test del guard contra doble aplicación de daño."""
    print("9. Guard contra doble aplicación:")
    
    rng.set_seed(150)
    
    compendio = CompendioMotor()
    gestor = GestorCombate(compendio)
    
    pc = Combatiente(
        id="pc_1", nombre="Thorin", tipo=TipoCombatiente.PC,
        hp_maximo=25,
        arma_principal={"id": "espada_1", "compendio_ref": "espada_larga", "nombre": "Espada larga"}
    )
    goblin = Combatiente(
        id="goblin_1", nombre="Goblin", tipo=TipoCombatiente.NPC_ENEMIGO,
        hp_maximo=50, clase_armadura=5  # HP alto para ver el efecto
    )
    
    gestor.agregar_combatiente(pc)
    gestor.agregar_combatiente(goblin)
    gestor.iniciar_combate()
    
    while gestor.obtener_turno_actual().tipo != TipoCombatiente.PC:
        gestor.siguiente_turno()
    
    # Procesar acción
    resultado = gestor.procesar_accion("Ataco al goblin")
    hp_despues_1 = goblin.hp_actual
    
    # Intentar aplicar los mismos cambios de nuevo (simula reintento)
    if resultado.cambios_estado:
        gestor._aplicar_cambios(resultado.cambios_estado)
    
    hp_despues_2 = goblin.hp_actual
    
    # HP no debe cambiar en el segundo intento
    assert hp_despues_1 == hp_despues_2, \
        f"Guard falló! HP cambió de {hp_despues_1} a {hp_despues_2}"
    
    print(f"   HP tras acción: {hp_despues_1}")
    print(f"   HP tras reintento: {hp_despues_2}")
    print("   OK Guard previene doble aplicación\n")
    return True


def test_estilos_narracion():
    """Test de diferentes estilos de narración."""
    print("10. Estilos de narración:")
    
    contexto = crear_contexto_ataque_exitoso()
    
    narraciones = {}
    for estilo in ["epico", "casual", "minimalista"]:
        narrador = NarradorLLM(estilo=estilo)
        respuesta = narrador.narrar(contexto)
        narraciones[estilo] = respuesta.narracion
        print(f"   [{estilo}]: {respuesta.narracion}")
    
    # Verificar que minimalista es más corto
    assert len(narraciones["minimalista"]) <= len(narraciones["casual"]),         "Minimalista debería ser más corto que casual"
    
    # Verificar que épico tiene exclamación
    assert "!" in narraciones["epico"], "Épico debería tener exclamación"
    
    print("   OK Estilos tienen diferencias\n")
    return True


def main():
    """Ejecuta todos los tests."""
    print("\n" + "="*60)
    print("  TESTS DEL NARRADOR LLM")
    print("="*60 + "\n")
    
    tests = [
        ("Narración sin LLM", test_narracion_sin_llm),
        ("Ataque fallido", test_narracion_ataque_fallido),
        ("Crítico", test_narracion_critico),
        ("Clarificación", test_narracion_clarificacion),
        ("Rechazo", test_narracion_rechazo),
        ("LLM mock", test_narracion_con_llm_mock),
        ("Contexto desde gestor", test_crear_contexto_desde_gestor),
        ("Flujo completo", test_flujo_completo_con_narrador),
        ("Guard doble aplicación", test_guard_doble_aplicacion),
        ("Estilos", test_estilos_narracion),
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
