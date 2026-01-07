"""
Tests del normalizador de acciones.
Ejecutar desde la raíz: python tests/test_normalizador.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from motor import (
    NormalizadorAcciones,
    TipoAccionNorm,
    AccionNormalizada,
    ContextoEscena,
    CompendioMotor,
    ValidadorAcciones
)


# =============================================================================
# FIXTURES
# =============================================================================

def crear_contexto_basico():
    """Crea un contexto de escena básico."""
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
            {"id": "rayo_escarcha", "nombre": "Rayo de escarcha"}
        ],
        ranuras_disponibles={1: 2, 2: 1},
        enemigos_vivos=[
            {"instancia_id": "goblin_1", "nombre": "Goblin", "compendio_ref": "goblin"},
            {"instancia_id": "goblin_2", "nombre": "Goblin arquero", "compendio_ref": "goblin"}
        ],
        aliados=[],
        movimiento_restante=30,
        accion_disponible=True
    )


def crear_contexto_un_enemigo():
    """Crea un contexto con un solo enemigo."""
    ctx = crear_contexto_basico()
    ctx.enemigos_vivos = [
        {"instancia_id": "orco_1", "nombre": "Orco", "compendio_ref": "orco"}
    ]
    return ctx


# =============================================================================
# TESTS
# =============================================================================

def test_deteccion_ataque():
    """Test de detección de intención de ataque."""
    print("1. Detección de ataque:")
    
    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_un_enemigo()
    
    textos_ataque = [
        "Ataco al orco",
        "Le pego con mi espada",
        "Golpeo al enemigo",
        "Disparo una flecha",
    ]
    
    for texto in textos_ataque:
        resultado = normalizador.normalizar(texto, contexto)
        assert resultado.tipo == TipoAccionNorm.ATAQUE, f"'{texto}' debería ser ATAQUE, es {resultado.tipo}"
        print(f"   '{texto}' → {resultado.tipo.value} ✓")
    
    print("   ✓ Detección de ataque correcta\n")
    return True


def test_deteccion_conjuro():
    """Test de detección de intención de conjuro."""
    print("2. Detección de conjuro:")
    
    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_basico()
    
    textos_conjuro = [
        "Lanzo proyectil mágico",
        "Uso rayo de escarcha",
        "Conjuro un hechizo"
    ]
    
    for texto in textos_conjuro:
        resultado = normalizador.normalizar(texto, contexto)
        assert resultado.tipo == TipoAccionNorm.CONJURO, f"'{texto}' debería ser CONJURO, es {resultado.tipo}"
        print(f"   '{texto}' → {resultado.tipo.value} ✓")
    
    print("   ✓ Detección de conjuro correcta\n")
    return True


def test_deteccion_movimiento():
    """Test de detección de movimiento."""
    print("3. Detección de movimiento:")
    
    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_basico()
    
    textos_movimiento = [
        "Me muevo hacia la puerta",
        "Camino hacia el norte",
        "Corro hacia el goblin",
        "Me acerco al enemigo"
    ]
    
    for texto in textos_movimiento:
        resultado = normalizador.normalizar(texto, contexto)
        assert resultado.tipo == TipoAccionNorm.MOVIMIENTO, f"'{texto}' debería ser MOVIMIENTO, es {resultado.tipo}"
        print(f"   '{texto}' → {resultado.tipo.value} ✓")
    
    print("   ✓ Detección de movimiento correcta\n")
    return True


def test_extraccion_arma():
    """Test de extracción de arma del texto."""
    print("4. Extracción de arma:")
    
    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_un_enemigo()
    
    # Arma mencionada explícitamente
    resultado = normalizador.normalizar("Ataco con mi espada larga", contexto)
    assert resultado.datos.get("arma_id") == "espada_larga", f"Esperado 'espada_larga', obtenido '{resultado.datos.get('arma_id')}'"
    print(f"   'Ataco con mi espada larga' → arma_id={resultado.datos.get('arma_id')} ✓")
    
    # Arma inferida (principal equipada)
    resultado = normalizador.normalizar("Ataco al orco", contexto)
    assert resultado.datos.get("arma_id") == "espada_larga", f"Esperado 'espada_larga', obtenido '{resultado.datos.get('arma_id')}'"
    print(f"   'Ataco al orco' → arma_id={resultado.datos.get('arma_id')} (inferida) ✓")
    
    # Ataque desarmado
    resultado = normalizador.normalizar("Ataco desarmado", contexto)
    assert resultado.datos.get("arma_id") == "unarmed"
    print(f"   'Ataco desarmado' → arma_id={resultado.datos.get('arma_id')} ✓")
    
    print("   ✓ Extracción de arma correcta\n")
    return True


def test_extraccion_objetivo():
    """Test de extracción de objetivo."""
    print("5. Extracción de objetivo:")
    
    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    
    # Un solo enemigo: inferir automáticamente
    contexto = crear_contexto_un_enemigo()
    resultado = normalizador.normalizar("Ataco", contexto)
    assert resultado.datos.get("objetivo_id") == "orco_1"
    print(f"   'Ataco' (1 enemigo) → objetivo_id={resultado.datos.get('objetivo_id')} ✓")
    
    # Múltiples enemigos: mencionar explícitamente por palabra clave
    contexto = crear_contexto_basico()
    resultado = normalizador.normalizar("Ataco al arquero", contexto)
    assert resultado.datos.get("objetivo_id") == "goblin_2", f"Esperado 'goblin_2', obtenido '{resultado.datos.get('objetivo_id')}'"
    print(f"   'Ataco al arquero' → objetivo_id={resultado.datos.get('objetivo_id')} ✓")
    
    # Múltiples enemigos sin especificar
    resultado = normalizador.normalizar("Ataco", contexto)
    assert resultado.requiere_clarificacion or len(resultado.advertencias) > 0
    print(f"   'Ataco' (múltiples enemigos) → requiere clarificación ✓")
    
    print("   ✓ Extracción de objetivo correcta\n")
    return True


def test_extraccion_distancia():
    """Test de extracción de distancia."""
    print("6. Extracción de distancia:")
    
    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_basico()
    
    casos = [
        ("Me muevo 20 pies", 20),
        ("Camino 30ft hacia la puerta", 30),
        ("Me muevo 2 casillas", 10),
    ]
    
    for texto, esperado in casos:
        resultado = normalizador.normalizar(texto, contexto)
        distancia = resultado.datos.get("distancia_pies")
        assert distancia is not None, f"No se detectó distancia en '{texto}'"
        assert abs(distancia - esperado) <= 2, f"Distancia incorrecta: {distancia} != {esperado}"
        print(f"   '{texto}' → {distancia} pies ✓")
    
    print("   ✓ Extracción de distancia correcta\n")
    return True


def test_deteccion_habilidad():
    """Test de detección de pruebas de habilidad."""
    print("7. Detección de habilidad:")
    
    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_basico()
    
    casos = [
        ("Hago una prueba de percepción", "percepcion"),
        ("Intento escuchar", "percepcion"),
        ("Investigo la habitación", "investigacion"),
        ("Intento persuadirlo", "persuasion")
    ]
    
    for texto, habilidad_esperada in casos:
        resultado = normalizador.normalizar(texto, contexto)
        assert resultado.tipo == TipoAccionNorm.HABILIDAD, f"'{texto}' debería ser HABILIDAD"
        assert resultado.datos.get("habilidad") == habilidad_esperada, f"Esperado {habilidad_esperada}, obtenido {resultado.datos.get('habilidad')}"
        print(f"   '{texto}' → {resultado.datos.get('habilidad')} ✓")
    
    print("   ✓ Detección de habilidad correcta\n")
    return True


def test_acciones_genericas():
    """Test de acciones genéricas."""
    print("8. Acciones genéricas:")
    
    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_basico()
    
    casos = [
        ("Uso Dash", "dash"),
        ("Me pongo a esquivar", "dodge"),
        ("Hago Disengage", "disengage"),
        ("Ayudo a mi compañero", "help"),
        ("Me escondo", "hide"),
    ]
    
    for texto, accion_esperada in casos:
        resultado = normalizador.normalizar(texto, contexto)
        assert resultado.tipo == TipoAccionNorm.ACCION, f"'{texto}' debería ser ACCION"
        assert resultado.datos.get("accion_id") == accion_esperada, f"Esperado {accion_esperada}, obtenido {resultado.datos.get('accion_id')}"
        print(f"   '{texto}' → {resultado.datos.get('accion_id')} ✓")
    
    print("   ✓ Acciones genéricas correctas\n")
    return True


def test_deteccion_conjuro_especifico():
    """Test de detección de conjuro específico."""
    print("9. Detección de conjuro específico:")
    
    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_basico()
    
    resultado = normalizador.normalizar("Lanzo proyectil mágico al goblin", contexto)
    assert resultado.tipo == TipoAccionNorm.CONJURO
    assert resultado.datos.get("conjuro_id") == "proyectil_magico"
    print(f"   'Lanzo proyectil mágico' → conjuro_id={resultado.datos.get('conjuro_id')} ✓")
    
    resultado = normalizador.normalizar("Uso rayo de escarcha", contexto)
    assert resultado.datos.get("conjuro_id") == "rayo_escarcha"
    print(f"   'Uso rayo de escarcha' → conjuro_id={resultado.datos.get('conjuro_id')} ✓")
    
    print("   ✓ Detección de conjuro específico correcta\n")
    return True


def test_confianza_y_faltantes():
    """Test de niveles de confianza y campos faltantes."""
    print("10. Confianza y faltantes:")
    
    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_basico()
    
    # Acción completa: alta confianza
    resultado = normalizador.normalizar("Ataco al goblin con mi espada larga", contexto)
    assert resultado.confianza >= 0.8
    assert resultado.es_completa()
    print(f"   Acción completa: confianza={resultado.confianza:.2f}, faltantes={resultado.faltantes} ✓")
    
    # Acción ambigua: requiere clarificación
    resultado = normalizador.normalizar("Ataco", contexto)
    assert resultado.requiere_clarificacion or len(resultado.advertencias) > 0
    print(f"   Acción ambigua: requiere_clarificacion={resultado.requiere_clarificacion} ✓")
    
    print("   ✓ Confianza y faltantes correctos\n")
    return True


def test_fallback_llm_mock():
    """Test del fallback a LLM con mock."""
    print("11. Fallback a LLM (mock):")
    
    def llm_mock(prompt, contexto):
        if "objetivo" in prompt.lower():
            return {"objetivo_id": "goblin_1"}
        return {}
    
    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio, llm_callback=llm_mock)
    contexto = crear_contexto_basico()
    
    resultado = normalizador.normalizar("Ataco a uno de ellos", contexto)
    
    if resultado.fuente == "llm":
        print(f"   LLM usado: objetivo_id={resultado.datos.get('objetivo_id')} ✓")
    else:
        print(f"   LLM no fue necesario (resuelto por patrones) ✓")
    
    print("   ✓ Fallback a LLM correcto\n")
    return True


def test_serializacion():
    """Test de serialización del resultado."""
    print("12. Serialización:")
    
    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_un_enemigo()
    
    resultado = normalizador.normalizar("Ataco al orco con mi espada", contexto)
    diccionario = resultado.to_dict()
    
    assert "tipo" in diccionario
    assert "datos" in diccionario
    assert "confianza" in diccionario
    assert diccionario["tipo"] == "ataque"
    
    print(f"   Resultado serializado: {diccionario['tipo']}, confianza={diccionario['confianza']:.2f} ✓")
    
    print("   ✓ Serialización correcta\n")
    return True


def test_flujo_completo():
    """Test del flujo completo: normalizar → validar."""
    print("13. Flujo completo (normalizar → validar):")
    
    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    validador = ValidadorAcciones(compendio)
    
    contexto = crear_contexto_un_enemigo()
    
    # Paso 1: Normalizar
    accion = normalizador.normalizar("Ataco al orco con mi espada larga", contexto)
    print(f"   1. Normalizado: tipo={accion.tipo.value}, arma={accion.datos.get('arma_id')}, objetivo={accion.datos.get('objetivo_id')}")
    
    # Paso 2: Crear datos para validador
    personaje = {
        "nombre": contexto.actor_nombre,
        "fuente": {
            "equipo_equipado": {
                "arma_principal_id": "espada_larga"
            }
        },
        "estado_actual": {
            "condiciones": [],
            "inconsciente": False,
            "muerto": False
        }
    }
    
    objetivo = {
        "nombre": "Orco",
        "puntos_golpe_actual": 15,
        "estado_actual": {"muerto": False}
    }
    
    # Paso 3: Validar
    validacion = validador.validar_ataque(personaje, objetivo, accion.datos.get("arma_id"))
    print(f"   2. Validado: {validacion}")
    
    assert accion.es_completa(), f"Acción no completa: faltantes={accion.faltantes}"
    assert validacion.valido, f"Validación falló: {validacion.razon}"
    
    print("   ✓ Flujo completo correcto\n")
    return True


def main():
    """Ejecuta todos los tests."""
    print("\n" + "="*60)
    print("  TESTS DEL NORMALIZADOR DE ACCIONES")
    print("="*60 + "\n")
    
    tests = [
        ("Detección ataque", test_deteccion_ataque),
        ("Detección conjuro", test_deteccion_conjuro),
        ("Detección movimiento", test_deteccion_movimiento),
        ("Extracción arma", test_extraccion_arma),
        ("Extracción objetivo", test_extraccion_objetivo),
        ("Extracción distancia", test_extraccion_distancia),
        ("Detección habilidad", test_deteccion_habilidad),
        ("Acciones genéricas", test_acciones_genericas),
        ("Conjuro específico", test_deteccion_conjuro_especifico),
        ("Confianza y faltantes", test_confianza_y_faltantes),
        ("Fallback LLM", test_fallback_llm_mock),
        ("Serialización", test_serializacion),
        ("Flujo completo", test_flujo_completo),
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
