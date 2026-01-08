#!/usr/bin/env python3
"""
Script de verificación del sistema de creación de personajes.

Comprueba:
1. Estructura de directorios
2. Archivos JSON del compendio
3. Módulos Python
4. Integridad de datos
"""

import sys
import json
from pathlib import Path

# Colores para output
class Colors:
    OK = "\033[92m✓\033[0m"
    FAIL = "\033[91m✗\033[0m"
    WARN = "\033[93m⚠\033[0m"
    INFO = "\033[94mℹ\033[0m"
    BOLD = "\033[1m"
    END = "\033[0m"


def check_file(path: Path, descripcion: str) -> bool:
    """Verifica que un archivo existe."""
    if path.exists():
        print(f"  {Colors.OK} {descripcion}: {path}")
        return True
    else:
        print(f"  {Colors.FAIL} {descripcion}: {path} (NO EXISTE)")
        return False


def check_dir(path: Path, descripcion: str) -> bool:
    """Verifica que un directorio existe."""
    if path.is_dir():
        print(f"  {Colors.OK} {descripcion}: {path}/")
        return True
    else:
        print(f"  {Colors.FAIL} {descripcion}: {path}/ (NO EXISTE)")
        return False


def check_json(path: Path, required_keys: list = None) -> tuple[bool, dict]:
    """Verifica que un JSON es válido y tiene las claves requeridas."""
    if not path.exists():
        return False, {}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if required_keys:
            missing = [k for k in required_keys if k not in data]
            if missing:
                print(f"    {Colors.WARN} Faltan claves: {missing}")
                return False, data
        
        return True, data
    except json.JSONDecodeError as e:
        print(f"    {Colors.FAIL} Error JSON: {e}")
        return False, {}


def check_python_import(module_path: str, descripcion: str) -> bool:
    """Verifica que un módulo Python se puede importar."""
    try:
        # Añadir src al path
        src_path = Path(__file__).parent / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        __import__(module_path)
        print(f"  {Colors.OK} {descripcion}: {module_path}")
        return True
    except ImportError as e:
        print(f"  {Colors.FAIL} {descripcion}: {module_path} ({e})")
        return False
    except Exception as e:
        print(f"  {Colors.FAIL} {descripcion}: {module_path} (Error: {e})")
        return False


def main():
    print()
    print(f"{Colors.BOLD}═══════════════════════════════════════════════════════════════{Colors.END}")
    print(f"{Colors.BOLD}  VERIFICACIÓN DEL SISTEMA DE CREACIÓN DE PERSONAJES{Colors.END}")
    print(f"{Colors.BOLD}═══════════════════════════════════════════════════════════════{Colors.END}")
    print()
    
    root = Path(__file__).parent
    errores = 0
    advertencias = 0
    
    # =========================================================================
    # 1. ESTRUCTURA DE DIRECTORIOS
    # =========================================================================
    print(f"{Colors.BOLD}1. ESTRUCTURA DE DIRECTORIOS{Colors.END}")
    print()
    
    dirs_requeridos = [
        (root / "src", "Código fuente"),
        (root / "src" / "personaje", "Módulo personaje"),
        (root / "data" / "personajes", "Datos de personajes"),
        (root / "storage", "Almacenamiento"),
        (root / "storage" / "characters", "Personajes guardados"),
        (root / "storage" / "autosave", "Autosaves"),
        (root / "compendio", "Compendio general"),
    ]
    
    for path, desc in dirs_requeridos:
        if not check_dir(path, desc):
            errores += 1
    
    print()
    
    # =========================================================================
    # 2. ARCHIVOS DEL COMPENDIO GENERAL
    # =========================================================================
    print(f"{Colors.BOLD}2. COMPENDIO GENERAL (raíz/compendio/){Colors.END}")
    print()
    
    compendio_files = [
        (root / "compendio" / "armas.json", "Armas"),
        (root / "compendio" / "armaduras_escudos.json", "Armaduras y escudos"),
        (root / "compendio" / "monstruos.json", "Monstruos"),
        (root / "compendio" / "conjuros.json", "Conjuros"),
        (root / "compendio" / "miscelanea.json", "Miscelánea"),
    ]
    
    for path, desc in compendio_files:
        if check_file(path, desc):
            valid, data = check_json(path)
            if valid:
                # Contar elementos dentro de arrays (formato: {"armas": [...], "armaduras": [...]})
                total = 0
                for key, value in data.items():
                    if isinstance(value, list):
                        total += len(value)
                if total > 0:
                    print(f"    {Colors.INFO} {total} entradas")
                elif isinstance(data, dict):
                    print(f"    {Colors.INFO} {len(data)} claves")
        else:
            errores += 1
    
    print()
    
    # =========================================================================
    # 3. ARCHIVOS DE DATOS DE PERSONAJES
    # =========================================================================
    print(f"{Colors.BOLD}3. DATOS DE PERSONAJES (data/personajes/){Colors.END}")
    print()
    
    personajes_files = [
        (root / "data" / "personajes" / "razas.json", "Razas", 
         ["humano", "elfo_alto", "enano_colinas"]),
        (root / "data" / "personajes" / "clases.json", "Clases",
         ["guerrero", "mago", "picaro", "clerigo"]),
        (root / "data" / "personajes" / "trasfondos.json", "Trasfondos",
         ["noble", "soldado", "criminal", "ermitano"]),
    ]
    
    for path, desc, expected_keys in personajes_files:
        if check_file(path, desc):
            valid, data = check_json(path, expected_keys)
            if valid:
                print(f"    {Colors.INFO} {len(data)} entradas: {', '.join(list(data.keys())[:5])}...")
            else:
                errores += 1
        else:
            errores += 1
    
    print()
    
    # =========================================================================
    # 4. MÓDULOS PYTHON
    # =========================================================================
    print(f"{Colors.BOLD}4. MÓDULOS PYTHON{Colors.END}")
    print()
    
    # Añadir src al path para imports
    sys.path.insert(0, str(root / "src"))
    
    modulos = [
        ("personaje", "Módulo principal"),
        ("personaje.compendio_pj", "Compendio PJ"),
        ("personaje.calculador", "Calculador"),
        ("personaje.storage", "Storage"),
        ("personaje.mapper", "Mapper"),
        ("personaje.creador", "Creador"),
    ]
    
    for mod, desc in modulos:
        if not check_python_import(mod, desc):
            errores += 1
    
    print()
    
    # =========================================================================
    # 5. ARCHIVOS CLI
    # =========================================================================
    print(f"{Colors.BOLD}5. ARCHIVOS CLI{Colors.END}")
    print()
    
    cli_files = [
        (root / "src" / "cli_creacion.py", "CLI Creación"),
    ]
    
    for path, desc in cli_files:
        if not check_file(path, desc):
            errores += 1
    
    print()
    
    # =========================================================================
    # 6. VERIFICACIÓN DE INTEGRIDAD
    # =========================================================================
    print(f"{Colors.BOLD}6. VERIFICACIÓN DE INTEGRIDAD{Colors.END}")
    print()
    
    try:
        from personaje import compendio_pj
        
        # Verificar que se cargan los datos
        razas = compendio_pj.obtener_razas()
        clases = compendio_pj.obtener_clases()
        trasfondos = compendio_pj.obtener_trasfondos()
        
        print(f"  {Colors.OK} Razas cargadas: {len(razas)}")
        print(f"  {Colors.OK} Clases cargadas: {len(clases)}")
        print(f"  {Colors.OK} Trasfondos cargados: {len(trasfondos)}")
        
        # Verificar funciones del calculador
        from personaje import calculador
        
        mod = calculador.calcular_modificador(16)
        assert mod == 3, f"calcular_modificador(16) debería ser 3, es {mod}"
        print(f"  {Colors.OK} calcular_modificador(16) = {mod}")
        
        bon = calculador.calcular_bonificador_competencia(1)
        assert bon == 2, f"bonificador nivel 1 debería ser 2, es {bon}"
        print(f"  {Colors.OK} calcular_bonificador_competencia(1) = {bon}")
        
        # Verificar creador
        from personaje.creador import CreadorPersonaje
        
        creador = CreadorPersonaje()
        assert creador.pj.get("id") is not None
        print(f"  {Colors.OK} CreadorPersonaje inicializa correctamente")
        
        # Verificar storage
        from personaje import storage
        
        storage._asegurar_directorios()
        print(f"  {Colors.OK} Storage: directorios verificados")
        
    except Exception as e:
        print(f"  {Colors.FAIL} Error de integridad: {e}")
        errores += 1
    
    print()
    
    # =========================================================================
    # 7. VERIFICAR REFERENCIAS CRUZADAS
    # =========================================================================
    print(f"{Colors.BOLD}7. REFERENCIAS CRUZADAS (compendio ↔ personajes){Colors.END}")
    print()
    
    # Verificar que las armas del equipo inicial existen en el compendio
    try:
        armas_path = root / "compendio" / "armas.json"
        armaduras_path = root / "compendio" / "armaduras_escudos.json"
        
        if armas_path.exists() and armaduras_path.exists():
            with open(armas_path, "r", encoding="utf-8") as f:
                armas_data = json.load(f)
            with open(armaduras_path, "r", encoding="utf-8") as f:
                armaduras_data = json.load(f)
            
            # Parsear formato: {"armas": [...]} con objetos que tienen "id"
            armas_list = armas_data.get("armas", [])
            armas_keys = [a.get("id") for a in armas_list if isinstance(a, dict)]
            
            armaduras_list = armaduras_data.get("armaduras", [])
            armaduras_keys = [a.get("id") for a in armaduras_list if isinstance(a, dict)]
            
            escudos_list = armaduras_data.get("escudos", [])
            escudos_keys = [e.get("id") for e in escudos_list if isinstance(e, dict)]
            
            # Armas que usa el sistema de creación
            armas_usadas = [
                "espada_larga", "daga", "baston", "estoque", "maza",
                "arco_corto", "ballesta_ligera", "hacha_mano"
            ]
            
            # Armaduras que usa el sistema (IDs actualizados)
            armaduras_usadas = [
                "cota_mallas_pesada", "armadura_cuero", "cota_escamas"
            ]
            
            # Verificar armas
            for arma in armas_usadas:
                if arma in armas_keys:
                    print(f"  {Colors.OK} Arma '{arma}' encontrada")
                else:
                    print(f"  {Colors.WARN} Arma '{arma}' NO encontrada")
                    advertencias += 1
            
            # Verificar armaduras
            for arm in armaduras_usadas:
                if arm in armaduras_keys:
                    print(f"  {Colors.OK} Armadura '{arm}' encontrada")
                else:
                    print(f"  {Colors.WARN} Armadura '{arm}' NO encontrada")
                    advertencias += 1
            
            # Verificar escudo
            if "escudo" in escudos_keys:
                print(f"  {Colors.OK} Escudo 'escudo' encontrado")
            else:
                print(f"  {Colors.WARN} Escudo 'escudo' NO encontrado")
                advertencias += 1
        else:
            print(f"  {Colors.WARN} No se pueden verificar referencias (faltan archivos)")
            advertencias += 1
            
    except Exception as e:
        print(f"  {Colors.FAIL} Error verificando referencias: {e}")
        errores += 1
    
    print()
    
    # =========================================================================
    # RESUMEN
    # =========================================================================
    print(f"{Colors.BOLD}═══════════════════════════════════════════════════════════════{Colors.END}")
    print(f"{Colors.BOLD}  RESUMEN{Colors.END}")
    print(f"{Colors.BOLD}═══════════════════════════════════════════════════════════════{Colors.END}")
    print()
    
    if errores == 0 and advertencias == 0:
        print(f"  {Colors.OK} Todo correcto! El sistema está listo.")
    elif errores == 0:
        print(f"  {Colors.WARN} {advertencias} advertencia(s), pero el sistema debería funcionar.")
    else:
        print(f"  {Colors.FAIL} {errores} error(es) encontrado(s).")
        if advertencias > 0:
            print(f"  {Colors.WARN} {advertencias} advertencia(s) adicional(es).")
    
    print()
    
    # =========================================================================
    # INSTRUCCIONES
    # =========================================================================
    if errores > 0:
        print(f"{Colors.BOLD}PARA CORREGIR:{Colors.END}")
        print()
        print("  Si faltan directorios, créalos con:")
        print("    mkdir -p data/personajes storage/characters storage/autosave")
        print()
        print("  Si faltan archivos JSON, revisa que se hayan creado correctamente.")
        print()
    
    print(f"{Colors.BOLD}PARA PROBAR:{Colors.END}")
    print()
    print("  python src/cli_creacion.py        # Modo básico")
    print("  python src/cli_creacion.py --llm  # Con LLM")
    print()
    
    return errores


if __name__ == "__main__":
    sys.exit(main())
