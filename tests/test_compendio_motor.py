"""
Tests de la interfaz del motor con el compendio.
Ejecutar desde la raíz: python tests/test_compendio_motor.py

Estos tests usan los IDs REALES del compendio.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from motor import obtener_compendio_motor
from motor.compendio import resetear_compendio_motor


def setup():
    """Resetea el compendio antes de cada grupo de tests."""
    resetear_compendio_motor()


def test_monstruos():
    """Test de consultas de monstruos."""
    print("1. Consultas de monstruos:")
    setup()
    
    compendio = obtener_compendio_motor()
    
    # Verificar que hay monstruos
    monstruos = compendio.listar_monstruos()
    assert len(monstruos) > 0, "Debe haber monstruos en el compendio"
    print(f"   Monstruos disponibles: {len(monstruos)}")
    
    # Mostrar IDs disponibles
    ids_monstruos = [m["id"] for m in monstruos]
    print(f"   IDs: {ids_monstruos}")
    
    # Usar el primer monstruo disponible
    primer_id = ids_monstruos[0]
    monstruo = compendio.obtener_monstruo(primer_id)
    assert monstruo is not None
    print(f"   {monstruo['nombre']}: PG={monstruo['puntos_golpe']}, CA={monstruo['clase_armadura']}")
    
    # Verificar existencia
    assert compendio.existe_monstruo(primer_id) == True
    assert compendio.existe_monstruo("dragon_ancestral_inexistente") == False
    print(f"   Existencia: {primer_id}=✓, dragon_ancestral_inexistente=✗")
    
    # Crear instancia para combate
    instancia = compendio.crear_instancia_monstruo(primer_id, "Enemigo Líder")
    assert instancia is not None
    assert instancia["nombre"] == "Enemigo Líder"
    assert instancia["compendio_ref"] == primer_id
    assert "instancia_id" in instancia
    assert instancia["categoria"] == "monstruo"
    print(f"   Instancia creada: {instancia['nombre']} (id: {instancia['instancia_id'][:8]}...)")
    
    print("   ✓ Monstruos correctos\n")
    return True


def test_armas():
    """Test de consultas de armas."""
    print("2. Consultas de armas:")
    setup()
    
    compendio = obtener_compendio_motor()
    
    # Verificar que hay armas
    armas = compendio.listar_armas()
    assert len(armas) > 0, "Debe haber armas en el compendio"
    print(f"   Armas disponibles: {len(armas)}")
    
    # Mostrar IDs disponibles
    ids_armas = [a["id"] for a in armas]
    print(f"   IDs: {ids_armas}")
    
    # Usar espada_larga si existe, sino la primera
    arma_id = "espada_larga" if "espada_larga" in ids_armas else ids_armas[0]
    arma = compendio.obtener_arma(arma_id)
    assert arma is not None
    print(f"   {arma['nombre']}: {arma['daño']} {arma['tipo_daño']}")
    
    # Daño
    daño = compendio.obtener_daño_arma(arma_id)
    assert "daño" in daño
    assert "tipo_daño" in daño
    print(f"   Daño: {daño}")
    
    # Propiedades
    props = compendio.obtener_propiedades_arma(arma_id)
    print(f"   Propiedades: {props}")
    
    # Crear instancia
    instancia = compendio.crear_instancia_arma(arma_id)
    assert instancia is not None
    assert instancia["categoria"] == "arma"
    print(f"   Instancia: {instancia['nombre']} (id: {instancia['instancia_id'][:8]}...)")
    
    print("   ✓ Armas correctas\n")
    return True


def test_armaduras():
    """Test de consultas de armaduras."""
    print("3. Consultas de armaduras:")
    setup()
    
    compendio = obtener_compendio_motor()
    
    # Verificar que hay armaduras
    armaduras = compendio.listar_armaduras()
    assert len(armaduras) > 0, "Debe haber armaduras en el compendio"
    print(f"   Armaduras disponibles: {len(armaduras)}")
    
    # Mostrar IDs disponibles
    ids_armaduras = [a["id"] for a in armaduras]
    print(f"   IDs: {ids_armaduras}")
    
    # Usar la primera armadura
    armadura_id = ids_armaduras[0]
    armadura = compendio.obtener_armadura(armadura_id)
    assert armadura is not None
    print(f"   {armadura['nombre']}: CA base={armadura['ca_base']}")
    
    # CA info
    ca_info = compendio.obtener_ca_armadura(armadura_id)
    assert "ca_base" in ca_info
    print(f"   Info CA: {ca_info}")
    
    # Escudo
    escudo = compendio.obtener_escudo()
    if escudo:
        print(f"   Escudo: +{escudo.get('bonificador_ca', 2)} CA")
    else:
        print("   Escudo: no encontrado en compendio")
    
    # Crear instancia
    instancia = compendio.crear_instancia_armadura(armadura_id)
    assert instancia is not None
    assert instancia["categoria"] == "armadura"
    print(f"   Instancia: {instancia['nombre']}")
    
    print("   ✓ Armaduras correctas\n")
    return True


def test_conjuros():
    """Test de consultas de conjuros."""
    print("4. Consultas de conjuros:")
    setup()
    
    compendio = obtener_compendio_motor()
    
    # Verificar que hay conjuros
    conjuros = compendio.listar_conjuros()
    assert len(conjuros) > 0, "Debe haber conjuros en el compendio"
    print(f"   Conjuros disponibles: {len(conjuros)}")
    
    # Mostrar IDs disponibles
    ids_conjuros = [c["id"] for c in conjuros]
    print(f"   IDs: {ids_conjuros}")
    
    # Usar el primer conjuro
    conjuro_id = ids_conjuros[0]
    conjuro = compendio.obtener_conjuro(conjuro_id)
    assert conjuro is not None
    print(f"   {conjuro['nombre']}: nivel {conjuro['nivel']}")
    
    # Daño base (sin escalado - eso es lógica de reglas)
    daño = compendio.obtener_daño_conjuro_base(conjuro_id)
    if daño:
        print(f"   Daño base: {daño}")
    else:
        print(f"   {conjuro['nombre']} no hace daño directo")
    
    # Listar trucos (nivel 0)
    trucos = compendio.listar_conjuros(nivel=0)
    print(f"   Trucos (nivel 0): {len(trucos)}")
    
    print("   ✓ Conjuros correctos\n")
    return True


def test_objetos():
    """Test de consultas de objetos."""
    print("5. Consultas de objetos:")
    setup()
    
    compendio = obtener_compendio_motor()
    
    # Verificar que hay objetos
    objetos = compendio.listar_objetos()
    assert len(objetos) > 0, "Debe haber objetos en el compendio"
    print(f"   Objetos disponibles: {len(objetos)}")
    
    # Mostrar IDs disponibles
    ids_objetos = [o["id"] for o in objetos]
    print(f"   IDs: {ids_objetos}")
    
    # Usar el primer objeto
    objeto_id = ids_objetos[0]
    objeto = compendio.obtener_objeto(objeto_id)
    assert objeto is not None
    print(f"   {objeto['nombre']}")
    
    # Crear instancia con cantidad
    instancia = compendio.crear_instancia_objeto(objeto_id, cantidad=3)
    assert instancia is not None
    assert instancia["cantidad"] == 3
    print(f"   Instancia: {instancia['cantidad']}x {instancia['nombre']}")
    
    print("   ✓ Objetos correctos\n")
    return True


def test_busqueda():
    """Test de búsqueda general."""
    print("6. Búsqueda general:")
    setup()
    
    compendio = obtener_compendio_motor()
    
    # Buscar término que debería existir
    resultados = compendio.buscar("espada")
    print(f"   Búsqueda 'espada': {sum(len(v) for v in resultados.values())} resultados")
    
    # Verificar existencia general con un monstruo conocido
    monstruos = compendio.listar_monstruos()
    if monstruos:
        primer_id = monstruos[0]["id"]
        assert compendio.existe(primer_id) == True
        print(f"   Existe '{primer_id}': ✓")
    
    assert compendio.existe("item_totalmente_inexistente_xyz") == False
    print("   Existe 'item_totalmente_inexistente_xyz': ✗")
    
    # Obtener cualquiera
    if monstruos:
        item = compendio.obtener_cualquiera(monstruos[0]["id"])
        assert item["categoria"] == "monstruo"
        print(f"   obtener_cualquiera: categoría={item['categoria']}")
    
    print("   ✓ Búsqueda correcta\n")
    return True


def test_instancias_unicas():
    """Test de creación de instancias con IDs únicos."""
    print("7. Instancias únicas:")
    setup()
    
    compendio = obtener_compendio_motor()
    
    # Obtener un monstruo del compendio
    monstruos = compendio.listar_monstruos()
    if not monstruos:
        print("   ⚠ No hay monstruos para probar")
        return True
    
    monstruo_id = monstruos[0]["id"]
    
    # Crear grupo de instancias
    instancias = []
    for i in range(3):
        nombre = f"Enemigo {i+1}" if i < 2 else "Enemigo Líder"
        instancia = compendio.crear_instancia_monstruo(monstruo_id, nombre)
        instancias.append(instancia)
    
    # Verificar IDs únicos
    ids = [g["instancia_id"] for g in instancias]
    assert len(ids) == len(set(ids)), "Cada instancia debe tener ID único"
    
    print(f"   Creadas 3 instancias de '{monstruo_id}':")
    for inst in instancias:
        print(f"     - {inst['nombre']}: {inst['instancia_id'][:8]}...")
    
    # Todas referencian al mismo compendio
    refs = [g["compendio_ref"] for g in instancias]
    assert all(r == monstruo_id for r in refs)
    print(f"   Todos referencian compendio_ref='{monstruo_id}' ✓")
    
    print("   ✓ Instancias únicas correctas\n")
    return True


def test_inyeccion_compendio():
    """Test de inyección de compendio para testing."""
    print("8. Inyección de compendio:")
    setup()
    
    # Mock completo que implementa todos los métodos que CompendioMotor usa
    class CompendioMock:
        """Mock completo del compendio para testing."""
        
        # --- Monstruos ---
        def obtener_monstruo(self, id):
            if id == "test_monster":
                return {
                    "id": "test_monster",
                    "nombre": "Monstruo de Prueba",
                    "puntos_golpe": 99,
                    "clase_armadura": 20,
                    "atributos": {
                        "fuerza": 10, "destreza": 10, "constitucion": 10,
                        "inteligencia": 10, "sabiduria": 10, "carisma": 10
                    },
                    "acciones": [],
                    "rasgos": [],
                    "velocidad": 30
                }
            return None
        
        def listar_monstruos(self):
            m = self.obtener_monstruo("test_monster")
            return [m] if m else []
        
        # --- Armas ---
        def obtener_arma(self, id):
            if id == "test_sword":
                return {
                    "id": "test_sword",
                    "nombre": "Espada de Prueba",
                    "daño": "1d8",
                    "tipo_daño": "cortante",
                    "propiedades": ["Versátil"],
                    "peso": 3,
                    "categoria": "arma marcial cuerpo a cuerpo"
                }
            return None
        
        def listar_armas(self):
            a = self.obtener_arma("test_sword")
            return [a] if a else []
        
        # --- Armaduras ---
        def obtener_armadura(self, id):
            if id == "test_armor":
                return {
                    "id": "test_armor",
                    "nombre": "Armadura de Prueba",
                    "ca_base": 15,
                    "tipo": "media",
                    "peso": 20
                }
            return None
        
        def listar_armaduras(self):
            a = self.obtener_armadura("test_armor")
            return [a] if a else []
        
        def obtener_escudo(self, id):
            if id == "escudo":
                return {"id": "escudo", "nombre": "Escudo", "bonificador_ca": 2}
            return None
        
        # --- Conjuros ---
        def obtener_conjuro(self, id):
            if id == "test_spell":
                return {
                    "id": "test_spell",
                    "nombre": "Conjuro de Prueba",
                    "nivel": 1,
                    "daño": "2d6",
                    "tipo_daño": "fuego"
                }
            return None
        
        def listar_conjuros(self, nivel=None, clase=None):
            c = self.obtener_conjuro("test_spell")
            if c:
                if nivel is not None and c["nivel"] != nivel:
                    return []
                return [c]
            return []
        
        # --- Objetos ---
        def obtener_objeto(self, id):
            if id == "test_item":
                return {
                    "id": "test_item",
                    "nombre": "Objeto de Prueba",
                    "categoria": "miscelanea",
                    "peso": 1
                }
            return None
        
        def listar_objetos(self, categoria=None):
            o = self.obtener_objeto("test_item")
            if o:
                if categoria and o.get("categoria") != categoria:
                    return []
                return [o]
            return []
        
        # --- Búsqueda ---
        def buscar(self, termino):
            resultados = {
                "monstruos": [],
                "armas": [],
                "armaduras": [],
                "conjuros": [],
                "objetos": []
            }
            termino_lower = termino.lower()
            
            m = self.obtener_monstruo("test_monster")
            if m and termino_lower in m["nombre"].lower():
                resultados["monstruos"].append(m)
            
            a = self.obtener_arma("test_sword")
            if a and termino_lower in a["nombre"].lower():
                resultados["armas"].append(a)
            
            return resultados
    
    # Inyectar mock
    from motor.compendio import CompendioMotor
    compendio_mock = CompendioMock()
    motor = CompendioMotor(compendio=compendio_mock)
    
    # Test monstruos
    monstruo = motor.obtener_monstruo("test_monster")
    assert monstruo is not None
    assert monstruo["puntos_golpe"] == 99
    print(f"   Mock monstruo: {monstruo['nombre']} PG={monstruo['puntos_golpe']} ✓")
    
    # Test armas
    arma = motor.obtener_arma("test_sword")
    assert arma is not None
    assert arma["daño"] == "1d8"
    print(f"   Mock arma: {arma['nombre']} {arma['daño']} ✓")
    
    # Test armaduras
    armadura = motor.obtener_armadura("test_armor")
    assert armadura is not None
    assert armadura["ca_base"] == 15
    print(f"   Mock armadura: {armadura['nombre']} CA={armadura['ca_base']} ✓")
    
    # Test conjuros
    conjuro = motor.obtener_conjuro("test_spell")
    assert conjuro is not None
    assert conjuro["nivel"] == 1
    print(f"   Mock conjuro: {conjuro['nombre']} nivel {conjuro['nivel']} ✓")
    
    # Test objetos
    objeto = motor.obtener_objeto("test_item")
    assert objeto is not None
    print(f"   Mock objeto: {objeto['nombre']} ✓")
    
    # Test búsqueda
    resultados = motor.buscar("Espada")
    assert len(resultados["armas"]) == 1
    print(f"   Mock búsqueda 'Espada': {len(resultados['armas'])} arma(s) ✓")
    
    # Test crear instancia
    instancia = motor.crear_instancia_monstruo("test_monster")
    assert instancia["puntos_golpe_maximo"] == 99
    print(f"   Mock instancia: PG={instancia['puntos_golpe_maximo']} ✓")
    
    print("   ✓ Inyección correcta\n")
    return True


def test_estructura_instancias():
    """Test de estructura consistente de instancias."""
    print("9. Estructura de instancias:")
    setup()
    
    compendio = obtener_compendio_motor()
    
    # Campos mínimos que toda instancia debe tener
    campos_requeridos = [
        "instancia_id", "compendio_ref", "categoria", "nombre"
    ]
    
    # Probar arma
    armas = compendio.listar_armas()
    if armas:
        inst = compendio.crear_instancia_arma(armas[0]["id"])
        for campo in campos_requeridos:
            assert campo in inst, f"Falta '{campo}' en instancia de arma"
        print(f"   Arma tiene campos: {campos_requeridos} ✓")
    
    # Probar armadura
    armaduras = compendio.listar_armaduras()
    if armaduras:
        inst = compendio.crear_instancia_armadura(armaduras[0]["id"])
        for campo in campos_requeridos:
            assert campo in inst, f"Falta '{campo}' en instancia de armadura"
        print(f"   Armadura tiene campos: {campos_requeridos} ✓")
    
    # Probar objeto
    objetos = compendio.listar_objetos()
    if objetos:
        inst = compendio.crear_instancia_objeto(objetos[0]["id"])
        for campo in campos_requeridos:
            assert campo in inst, f"Falta '{campo}' en instancia de objeto"
        print(f"   Objeto tiene campos: {campos_requeridos} ✓")
    
    print("   ✓ Estructura consistente\n")
    return True


def main():
    """Ejecuta todos los tests."""
    print("\n" + "="*60)
    print("  TESTS DEL COMPENDIO DEL MOTOR")
    print("="*60 + "\n")
    
    tests = [
        ("Monstruos", test_monstruos),
        ("Armas", test_armas),
        ("Armaduras", test_armaduras),
        ("Conjuros", test_conjuros),
        ("Objetos", test_objetos),
        ("Búsqueda", test_busqueda),
        ("Instancias únicas", test_instancias_unicas),
        ("Inyección compendio", test_inyeccion_compendio),
        ("Estructura instancias", test_estructura_instancias),
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
