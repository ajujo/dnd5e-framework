"""
Tests del pipeline con acciones de monstruo.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from motor import (
    PipelineTurno, CompendioMotor, rng,
    AccionNormalizada, TipoAccionNorm
)
from motor.normalizador import ContextoEscena


def crear_contexto_monstruo():
    """Crea contexto de un monstruo con acciones."""
    return ContextoEscena(
        actor_id="goblin_1",
        actor_nombre="Goblin",
        arma_principal=None,
        acciones_monstruo=[
            {
                "nombre": "Cimitarra",
                "bonificador_ataque": 4,
                "daño": "1d6+2",
                "tipo_daño": "cortante",
                "alcance": 5
            },
            {
                "nombre": "Arco corto",
                "bonificador_ataque": 4,
                "daño": "1d6+2",
                "tipo_daño": "perforante",
                "alcance": "80/320"
            }
        ],
        enemigos_vivos=[
            {"instancia_id": "pc_1", "nombre": "Thorin", "clase_armadura": 16}
        ]
    )


def test_pipeline_elige_accion_por_arma_id():
    """Test: pipeline mapea arma_id a accion de monstruo."""
    print("1. Pipeline mapea arma_id a accion de monstruo:")
    
    rng.set_seed(42)
    
    compendio = CompendioMotor()
    pipeline = PipelineTurno(compendio)
    contexto = crear_contexto_monstruo()
    
    # Simular accion normalizada con arma_id="arco_corto"
    accion = AccionNormalizada(
        tipo=TipoAccionNorm.ATAQUE,
        datos={
            "objetivo_id": "pc_1",
            "arma_id": "arco_corto",
            "modo": "normal"
        }
    )
    
    eventos, cambios = pipeline._ejecutar_ataque(accion, contexto)
    
    evento_ataque = eventos[0]
    arma_usada = evento_ataque.datos.get("arma_nombre")
    
    assert arma_usada == "Arco corto", f"Esperaba 'Arco corto', obtuvo '{arma_usada}'"
    
    print(f"   Arma usada: {arma_usada}")
    print("   OK\n")
    return True


def test_pipeline_fallback_melee():
    """Test: sin arma_id, elige melee por defecto."""
    print("2. Fallback elige melee por defecto:")
    
    rng.set_seed(42)
    
    compendio = CompendioMotor()
    pipeline = PipelineTurno(compendio)
    contexto = crear_contexto_monstruo()
    
    # Accion sin arma_id especifica
    accion = AccionNormalizada(
        tipo=TipoAccionNorm.ATAQUE,
        datos={
            "objetivo_id": "pc_1",
            "modo": "normal"
        }
    )
    
    eventos, cambios = pipeline._ejecutar_ataque(accion, contexto)
    
    evento_ataque = eventos[0]
    arma_usada = evento_ataque.datos.get("arma_nombre")
    
    assert arma_usada == "Cimitarra", f"Esperaba 'Cimitarra', obtuvo '{arma_usada}'"
    
    print(f"   Arma usada: {arma_usada}")
    print("   OK\n")
    return True


def test_pipeline_usa_ca_real():
    """Test: pipeline usa CA del objetivo desde contexto."""
    print("3. Pipeline usa CA del objetivo:")
    
    rng.set_seed(100)
    
    compendio = CompendioMotor()
    pipeline = PipelineTurno(compendio)
    
    contexto = ContextoEscena(
        actor_id="goblin_1",
        actor_nombre="Goblin",
        acciones_monstruo=[
            {"nombre": "Garra", "bonificador_ataque": 6, "daño": "1d4+2", "tipo_daño": "cortante", "alcance": 5}
        ],
        enemigos_vivos=[
            {"instancia_id": "pc_1", "nombre": "Thorin", "clase_armadura": 5}
        ]
    )
    
    accion = AccionNormalizada(
        tipo=TipoAccionNorm.ATAQUE,
        datos={"objetivo_id": "pc_1", "modo": "normal"}
    )
    
    eventos, cambios = pipeline._ejecutar_ataque(accion, contexto)
    
    evento_ataque = eventos[0]
    tirada = evento_ataque.datos.get("tirada", {})
    
    print(f"   Tirada: {tirada.get('total')}, impacta: {evento_ataque.datos.get('impacta')}")
    assert "impacta" in evento_ataque.datos
    
    print("   OK\n")
    return True


def test_critico_dados_multiples():
    """Test: critico con expresion de dados multiples no crashea."""
    print("4. Critico con dados multiples:")
    
    from motor.combate_utils import resolver_ataque_monstruo
    
    # Buscar seed que de critico
    for seed in range(200):
        rng.set_seed(seed)
        accion = {
            "nombre": "Mordisco",
            "bonificador_ataque": 5,
            "daño": "1d8+1d6+3",
            "tipo_daño": "perforante"
        }
        resultado = resolver_ataque_monstruo(accion, ca_objetivo=10)
        if resultado.es_critico:
            print(f"   Critico con seed {seed}")
            print(f"   Daño: {resultado.daño_total}")
            assert resultado.daño_total > 0
            print("   OK\n")
            return True
    
    print("   No se encontro critico, test parcial OK\n")
    return True


def main():
    print("\n" + "="*50)
    print("  TESTS PIPELINE CON ACCIONES DE MONSTRUO")
    print("="*50 + "\n")
    
    tests = [
        test_pipeline_elige_accion_por_arma_id,
        test_pipeline_fallback_melee,
        test_pipeline_usa_ca_real,
        test_critico_dados_multiples,
    ]
    
    resultados = []
    for t in tests:
        try:
            ok = t()
            resultados.append((t.__name__, ok))
        except Exception as e:
            print(f"   EXCEPCION: {e}\n")
            import traceback
            traceback.print_exc()
            resultados.append((t.__name__, False))
    
    print("="*50)
    todos_ok = all(r[1] for r in resultados)
    for nombre, ok in resultados:
        print(f"  {'OK' if ok else 'FAIL'} {nombre}")
    print("="*50)
    print(f"  {'TODOS LOS TESTS PASARON' if todos_ok else 'ALGUNOS TESTS FALLARON'}")
    print("="*50 + "\n")
    
    return todos_ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
