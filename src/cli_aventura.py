#!/usr/bin/env python3
"""
CLI de Aventura - Interfaz principal con el DM como cerebro.

Uso:
    python src/cli_aventura.py --cargar <ID_PERSONAJE>
    python src/cli_aventura.py --nuevo
"""

import sys
import argparse
from typing import Optional

# Imports del proyecto
from personaje import load_character, save_character, recalcular_derivados, list_characters
from llm import obtener_cliente_llm, verificar_conexion, set_perfil, get_perfil
from generador import listar_tonos, cargar_tono, listar_regiones, obtener_info_region, crear_bible_generator, obtener_bible_manager
from orquestador import DMCerebro


# Configuración
ANCHO_LINEA = 70

# Tipos de aventura disponibles
TIPOS_AVENTURA = {
    "1": {
        "nombre": "Épica Heroica",
        "descripcion": "Héroes contra el mal, batallas épicas, salvar el mundo",
        "tono": "heroico, épico, buenos vs malos claros, acción y gloria"
    },
    "2": {
        "nombre": "Fantasía Oscura", 
        "descripcion": "Mundo peligroso, moral gris, supervivencia",
        "tono": "sombrío, peligroso, decisiones difíciles, consecuencias duras"
    },
    "3": {
        "nombre": "Intriga y Misterio",
        "descripcion": "Investigación, secretos, complots políticos",
        "tono": "misterioso, detectivesco, traiciones, secretos por descubrir"
    },
    "4": {
        "nombre": "Exploración y Maravillas",
        "descripcion": "Descubrir tierras desconocidas, ruinas antiguas, tesoros",
        "tono": "aventurero, descubrimiento, maravillas, exploración"
    },
    "5": {
        "nombre": "Comedia y Caos",
        "descripcion": "Situaciones absurdas, humor, personajes excéntricos",
        "tono": "humorístico, caótico, situaciones ridículas, NPCs memorables"
    },
    "0": {
        "nombre": "Elección del DM",
        "descripcion": "El Director de Juego decide el tono según la situación",
        "tono": "variado, sorprendente, adaptativo"
    }
}


def limpiar_pantalla():
    """Limpia la pantalla."""
    print("\033[2J\033[H", end="")


def mostrar_cabecera():
    """Muestra la cabecera del juego."""
    print("═" * ANCHO_LINEA)
    print("  D&D 5e - AVENTURA")
    print("═" * ANCHO_LINEA)


def mostrar_estado_pj(dm: DMCerebro):
    """Muestra el estado resumido del PJ."""
    if not dm.contexto.pj:
        return
    
    pj = dm.contexto.pj
    info = pj.get("info_basica", {})
    derivados = pj.get("derivados", {})
    
    nombre = info.get("nombre", "Aventurero")
    hp_actual = derivados.get("puntos_golpe_actual", 0)
    hp_max = derivados.get("puntos_golpe_maximo", 0)
    ca = derivados.get("clase_armadura", 10)
    modo = dm.contexto.modo_juego.upper()
    
    # Barra de HP visual
    porcentaje_hp = hp_actual / hp_max if hp_max > 0 else 0
    bloques_llenos = int(porcentaje_hp * 10)
    barra_hp = "█" * bloques_llenos + "░" * (10 - bloques_llenos)
    
    print(f"  {nombre} | HP [{barra_hp}] {hp_actual}/{hp_max} | CA {ca} | Modo: {modo}")
    print("─" * ANCHO_LINEA)


def mostrar_narrativa(texto: str):
    """Muestra la narrativa del DM con formato."""
    print()
    # Dividir en líneas de ancho apropiado
    palabras = texto.split()
    linea_actual = "  "
    
    for palabra in palabras:
        if len(linea_actual) + len(palabra) + 1 > ANCHO_LINEA - 4:
            print(linea_actual)
            linea_actual = "  " + palabra
        else:
            linea_actual += " " + palabra if linea_actual != "  " else palabra
    
    if linea_actual.strip():
        print(linea_actual)
    
    print()


def mostrar_resultado_mecanico(resultado: dict, herramienta: str = None):
    """Muestra el resultado mecánico si lo hay."""
    if not resultado:
        return
    
    # Mostrar de forma compacta
    if "desglose" in resultado:
        exito_txt = "✓" if resultado.get("exito") or resultado.get("impacta") else "✗"
        
        # Añadir nombre de habilidad/herramienta si está disponible
        prefijo = ""
        if herramienta == "tirar_habilidad":
            # Extraer habilidad del desglose (formato: "X + Y (HAB) + Z")
            prefijo = "Tirada de habilidad: "
        elif herramienta == "tirar_salvacion":
            prefijo = "Salvación: "
        elif herramienta == "tirar_ataque":
            prefijo = "Ataque: "
        
        print(f"  [{exito_txt}] {prefijo}{resultado['desglose']}")
    
    if resultado.get("daño"):
        print(f"  [Daño: {resultado['daño']}]")
    
    if resultado.get("daño_detalle"):
        print(f"  [Daño: {resultado['daño_detalle']}]")



def mostrar_sistema(dm: DMCerebro):
    """Muestra información del sistema actual."""
    from llm import get_perfil
    
    perfil = get_perfil()
    flags = dm.contexto.flags
    
    print("\n  ═══ ESTADO DEL SISTEMA ═══")
    
    # Perfil LLM
    print(f"\n  🤖 PERFIL LLM: {perfil['nombre'].upper()}")
    print(f"     Max tokens: {perfil['max_tokens']}")
    print(f"     Temperatura: {perfil['temperature']}")
    print(f"     Timeout: {perfil['timeout']}s")
    
    # Tipo de aventura
    tipo_av = flags.get("tipo_aventura", {})
    if tipo_av:
        print(f"\n  📖 TIPO DE AVENTURA: {tipo_av.get('nombre', 'No definido')}")
        datos = tipo_av.get('datos_completos', {})
        if datos:
            print(f"     Letalidad: {datos.get('letalidad', 'N/A')}")
            print(f"     Moral: {datos.get('moral', 'N/A')}")
            freq = datos.get('frecuencias', {})
            if freq:
                print(f"     Combate: {freq.get('combate', '?')} | Social: {freq.get('social', '?')} | Misterio: {freq.get('misterio', '?')}")
        else:
            print(f"     Tono: {tipo_av.get('tono', 'N/A')}")
    
    # Modo de juego actual
    print(f"\n  🎮 MODO ACTUAL: {dm.contexto.modo_juego.upper()}")
    
    # Estadísticas de sesión
    print(f"\n  📊 ESTADÍSTICAS:")
    print(f"     Turnos jugados: {dm.contexto.turno}")
    print(f"     NPCs en escena: {len(dm.contexto.npcs_activos)}")
    if dm.contexto.ubicacion:
        print(f"     Ubicación: {dm.contexto.ubicacion.nombre}")
    
    # Estado de combate si hay
    if dm.contexto.estado_combate and dm.contexto.estado_combate.get("activo"):
        print(f"\n  ⚔️ COMBATE ACTIVO:")
        print(f"     Ronda: {dm.contexto.estado_combate.get('ronda', 1)}")
    
    print()

def mostrar_ayuda():
    """Muestra los comandos disponibles."""
    print("""
  COMANDOS:
    /estado      - Ver estado detallado del personaje
    /inventario  - Ver inventario (alias: /inv, /i)
    /combate     - Ver estado del combate activo
    /guardar     - Guardar partida
    /debug       - Activar/desactivar modo debug
    /sistema     - Ver estado del sistema (perfil, modo, tipo aventura)
    /ayuda       - Mostrar esta ayuda
    /salir       - Guardar y salir
    
  ACCIONES:
    Escribe lo que quieras hacer en lenguaje natural.
    El DM interpretará tu acción y aplicará las reglas.
    
  MODOS DE JUEGO:
    EXPLORACIÓN - Viajar, investigar, explorar
    SOCIAL      - Conversaciones, negociaciones  
    COMBATE     - Enfrentamientos con enemigos
""")


def mostrar_estado_detallado(dm: DMCerebro):
    """Muestra el estado detallado del PJ."""
    if not dm.contexto.pj:
        print("  No hay personaje cargado.")
        return
    
    from herramientas import ejecutar_herramienta
    
    contexto = dm.contexto.generar_diccionario_contexto()
    resultado = ejecutar_herramienta("consultar_ficha", contexto, campo="todo")
    
    if resultado.get("exito"):
        datos = resultado["datos"]
        print(f"""
  ═══ {datos.get('nombre', 'PJ')} ═══
  {datos.get('raza', '?')} {datos.get('clase', '?')} Nv.{datos.get('nivel', 1)}
  HP: {datos.get('hp', '?')}
  CA: {datos.get('ca', '?')}
  
  Características:""")
        for car, val in datos.get("caracteristicas", {}).items():
            print(f"    {car.upper()[:3]}: {val}")
        
        print(f"\n  Competencias: {', '.join(datos.get('habilidades_competentes', []))}")
        print(f"  Arma: {datos.get('arma_equipada', 'Ninguna')}")


def mostrar_inventario(dm: DMCerebro):
    """Muestra el inventario del PJ."""
    if not dm.contexto.pj:
        print("  No hay personaje cargado.")
        return
    
    equipo = dm.contexto.pj.get("equipo", {})
    
    print("\n  ═══ INVENTARIO ═══")
    
    # Armas
    armas = equipo.get("armas", [])
    if armas:
        print("\n  ⚔ Armas:")
        for arma in armas:
            eq = " ★" if arma.get("equipada") else ""
            print(f"    • {arma.get('nombre', '?')}{eq}")
    
    # Armaduras
    armaduras = equipo.get("armaduras", [])
    if armaduras:
        print("\n  🛡 Armaduras:")
        for arm in armaduras:
            eq = " ★" if arm.get("equipada") else ""
            print(f"    • {arm.get('nombre', '?')}{eq}")
    
    # Escudo
    if equipo.get("escudo"):
        print(f"    • Escudo ★")
    
    # Objetos misceláneos
    objetos = equipo.get("objetos", [])
    if objetos:
        print("\n  🎒 Mochila:")
        for obj in objetos:
            cant = f" x{obj.get('cantidad', 1)}" if obj.get("cantidad", 1) > 1 else ""
            print(f"    • {obj.get('nombre', obj.get('id', '?'))}{cant}")
    
    # Monedas
    print("\n  💰 Monedas:")
    oro = equipo.get("oro", 0)
    plata = equipo.get("plata", 0)
    cobre = equipo.get("cobre", 0)
    
    if oro > 0:
        print(f"    • {oro} po (oro)")
    if plata > 0:
        print(f"    • {plata} pp (plata)")
    if cobre > 0:
        print(f"    • {cobre} pc (cobre)")
    if oro == 0 and plata == 0 and cobre == 0:
        print("    • Sin monedas")
    
    print()


def seleccionar_personaje() -> Optional[dict]:
    """Permite al usuario seleccionar un personaje existente."""
    personajes = list_characters()
    
    if not personajes:
        print("  No hay personajes guardados.")
        return None
    
    print("\n  PERSONAJES DISPONIBLES:")
    for i, pj in enumerate(personajes, 1):
        print(f"    {i}. {pj['nombre']} ({pj['raza']} {pj['clase']} Nv.{pj['nivel']})")
    
    while True:
        try:
            opcion = input("\n  Selecciona (número) o 0 para cancelar: ").strip()
            if opcion == "0":
                return None
            
            idx = int(opcion) - 1
            if 0 <= idx < len(personajes):
                return load_character(personajes[idx]["id"])
        except (ValueError, IndexError):
            print("  Opción no válida.")




def seleccionar_tipo_aventura() -> dict:
    """Permite al usuario seleccionar el tipo de aventura usando módulos de tono."""
    tonos = listar_tonos()
    
    print("\n  ═══ TIPO DE AVENTURA ═══\n")
    
    for i, tono in enumerate(tonos, 1):
        print(f"  {i}. {tono['nombre']}")
        print(f"     {tono['descripcion']}\n")
    
    while True:
        try:
            opcion = input("  Elige (1-{0}): ".format(len(tonos))).strip()
            idx = int(opcion) - 1
            if 0 <= idx < len(tonos):
                tono_seleccionado = tonos[idx]
                tono_completo = cargar_tono(tono_seleccionado['id'])
                
                print(f"\n  ✓ Aventura: {tono_seleccionado['nombre']}")
                
                return {
                    "id": tono_seleccionado['id'],
                    "nombre": tono_seleccionado['nombre'],
                    "tono": tono_completo.get('tono_narrativo', ''),
                    "datos_completos": tono_completo
                }
        except ValueError:
            pass
        print("  Opción no válida.")


def crear_escena_demo() -> tuple:
    """Crea una escena de demostración."""
    ubicacion = {
        "ubicacion_id": "taberna_ciervo",
        "nombre": "Taberna del Ciervo Dorado",
        "descripcion": "Una taberna acogedora con vigas de roble oscurecidas por el humo. El fuego crepita en la chimenea mientras parroquianos murmuran sobre sus jarras de cerveza.",
        "tipo": "interior"
    }
    
    npcs = [
        {
            "id": "tabernera",
            "nombre": "Marta la Tabernera",
            "descripcion": "Una mujer robusta de mediana edad con delantal manchado y sonrisa fácil.",
            "actitud": "amistoso"
        }
    ]
    
    return ubicacion, npcs




def generar_resumen_sesion(dm: DMCerebro) -> dict:
    """Genera un resumen de la sesión actual para guardar."""
    resumen = {
        "ubicacion_actual": "",
        "que_estaba_haciendo": "",
        "resumen_sesion": "",
        "turnos_jugados": dm.contexto.turno
    }
    
    # Ubicación actual
    if dm.contexto.ubicacion:
        resumen["ubicacion_actual"] = dm.contexto.ubicacion.nombre
    
    # Qué estaba haciendo (últimos eventos)
    if dm.contexto.historial:
        ultimos = dm.contexto.historial[-3:]  # Últimos 3 eventos
        acciones = [h.contenido for h in ultimos if h.tipo == "accion_jugador"]
        if acciones:
            resumen["que_estaba_haciendo"] = acciones[-1][:100]
    
    # Generar resumen con LLM si está disponible
    if dm.llm_callback and dm.contexto.historial:
        try:
            # Extraer eventos importantes del historial
            eventos = [h.contenido[:80] for h in dm.contexto.historial[-10:]]
            eventos_texto = "\n".join(eventos)
            
            respuesta = dm.llm_callback(
                f"Resume en 2 frases qué ha pasado en esta sesión de D&D:\n{eventos_texto}",
                "Eres un asistente que resume partidas de rol. Sé conciso."
            )
            if respuesta:
                resumen["resumen_sesion"] = respuesta.strip()[:200]
        except:
            pass
    
    # Fallback si no hay LLM
    if not resumen["resumen_sesion"] and dm.contexto.historial:
        resumen["resumen_sesion"] = f"Sesión de {dm.contexto.turno} turnos. Último: {resumen.get('que_estaba_haciendo', 'explorando')}"
    
    return resumen



def seleccionar_region() -> dict:
    """Permite al usuario seleccionar la región de Faerûn."""
    regiones = listar_regiones()
    
    print("\n  ═══ REGIÓN DE FAERÛN ═══\n")
    
    for i, region in enumerate(regiones, 1):
        print(f"  {i}. {region['nombre']}")
        print(f"     {region['descripcion'][:60]}...\n")
    
    while True:
        try:
            opcion = input(f"  Elige (1-{len(regiones)}): ").strip()
            idx = int(opcion) - 1
            if 0 <= idx < len(regiones):
                region_sel = regiones[idx]
                region_completa = obtener_info_region(region_sel['id'])
                
                print(f"\n  ✓ Región: {region_sel['nombre']}")
                print(f"    Ciudades: {', '.join(region_completa.get('ciudades', [])[:3])}")
                
                return {
                    "id": region_sel['id'],
                    "nombre": region_sel['nombre'],
                    "datos": region_completa
                }
        except ValueError:
            pass
        print("  Opción no válida.")


def generar_aventura_bible(pj: dict, tipo_aventura: dict, region: dict, llm_callback) -> bool:
    """Genera la Adventure Bible usando el LLM."""
    print("\n  ═══ GENERANDO AVENTURA ═══")
    print("  Esto puede tardar un momento...\n")
    
    generator = crear_bible_generator(llm_callback)
    
    exito, mensaje = generator.generar_y_guardar(
        pj=pj,
        tipo_aventura_id=tipo_aventura['id'],
        region_id=region['id']
    )
    
    if exito:
        print(f"  ✓ {mensaje}")
        return True
    else:
        print(f"  ✗ Error: {mensaje}")
        print("  Se continuará sin Adventure Bible (modo improvisación)")
        return False


def jugar(dm: DMCerebro, es_continuacion: bool = False):
    """Bucle principal del juego."""
    limpiar_pantalla()
    mostrar_cabecera()
    
    if es_continuacion:
        # Mostrar resumen del estado actual
        print()
        if dm.contexto.ubicacion:
            print(f"  [Continuando en: {dm.contexto.ubicacion.nombre}]")
        if dm.contexto.historial:
            ultimo = dm.contexto.historial[-1]
            print(f"  [Último evento: {ultimo.contenido[:60]}...]")
        print()
    else:
        # Narrar escena inicial solo si es nueva aventura
        print()
        narrativa_inicial = dm.narrar_escena_inicial()
        mostrar_narrativa(narrativa_inicial)
    
    while True:
        # Mostrar estado
        mostrar_estado_pj(dm)
        
        # Input del jugador
        try:
            accion = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Saliendo...")
            break
        
        if not accion:
            continue
        
        # Comandos del sistema
        if accion.lower() == "/salir":
            print("  Guardando partida...")
            resumen = generar_resumen_sesion(dm)
            estado = dm.guardar_estado()
            estado["resumen"] = resumen
            dm.contexto.pj["estado_aventura"] = estado
            save_character(dm.contexto.pj)
            print("  ✓ Partida guardada")
            if resumen.get("resumen_sesion"):
                print(f"  📜 {resumen['resumen_sesion'][:80]}...")
            print("  ¡Hasta la próxima aventura!")
            break
        
        elif accion.lower() == "/ayuda":
            mostrar_ayuda()
            continue
        
        elif accion.lower() == "/estado":
            mostrar_estado_detallado(dm)
            continue
        
        elif accion.lower() in ("/inv", "/inventario", "/i"):
            mostrar_inventario(dm)
            continue
        
        elif accion.lower() in ("/combate", "/combat"):
            # Mostrar estado del combate si hay uno activo
            if dm.contexto.estado_combate and dm.contexto.estado_combate.get("activo"):
                combate = dm.contexto.estado_combate
                print("\n  ═══ COMBATE ACTIVO ═══")
                print(f"  Ronda: {combate.get('ronda', 1)}")
                for cid, c in combate.get("combatientes", {}).items():
                    estado = "💀" if c.get("estado") == "derrotado" else ""
                    hp = f"HP: {c.get('hp', '?')}/{c.get('hp_max', '?')}" if c.get("tipo") == "enemigo" else ""
                    print(f"    {c.get('nombre', cid)} {hp} {estado}")
            else:
                print("\n  No hay combate activo.")
            continue
        
        elif accion.lower() == "/guardar":
            # Generar resumen de sesión
            print("  Generando resumen...")
            resumen = generar_resumen_sesion(dm)
            
            # Guardar estado de aventura + resumen en el PJ
            estado = dm.guardar_estado()
            estado["resumen"] = resumen
            dm.contexto.pj["estado_aventura"] = estado
            save_character(dm.contexto.pj)
            
            print("  ✓ Partida guardada")
            if resumen.get("ubicacion_actual"):
                print(f"  📍 {resumen['ubicacion_actual']}")
            if resumen.get("resumen_sesion"):
                print(f"  📜 {resumen['resumen_sesion'][:80]}...")
            continue
        
        elif accion.lower() == "/debug":
            dm.debug_mode = not dm.debug_mode
            print(f"  Modo debug: {'ON' if dm.debug_mode else 'OFF'}")
            continue
        
        elif accion.lower() in ("/sistema", "/system", "/sys"):
            mostrar_sistema(dm)
            continue
        
        # Procesar acción narrativa
        resultado = dm.procesar_turno(accion)
        
        # Mostrar resultado mecánico si lo hay
        mostrar_resultado_mecanico(resultado.get("resultado_mecanico"), resultado.get("herramienta_usada"))
        
        # Mostrar narrativa
        mostrar_narrativa(resultado["narrativa"])


def main():
    parser = argparse.ArgumentParser(description="D&D 5e - Aventura con DM AI")
    parser.add_argument("--cargar", "-c", help="ID del personaje a cargar")
    parser.add_argument("--continuar", action="store_true", help="Continuar última partida")
    parser.add_argument("--debug", "-d", action="store_true", help="Modo debug")
    parser.add_argument("--lite", action="store_true", help="Usar perfil lite (modelos 7B-14B)")
    parser.add_argument("--normal", action="store_true", help="Usar perfil normal (modelos 14B-32B)")
    parser.add_argument("--completo", action="store_true", help="Usar perfil completo (modelos 32B-80B+)")
    args = parser.parse_args()
    
    # Configurar perfil LLM
    if args.lite:
        set_perfil("lite")
    elif args.completo:
        set_perfil("completo")
    else:
        set_perfil("normal")  # Por defecto
    
    # Configurar LLM
    cliente_llm = obtener_cliente_llm()
    
    if cliente_llm:
        def llm_callback(system: str, user: str) -> str:
            return cliente_llm(user, system_prompt=system)
        perfil = get_perfil()
        print(f"✓ LLM conectado [Perfil: {perfil['nombre']}]")
    else:
        llm_callback = None
        print("⚠ Sin LLM - modo narrativa limitada")
    
    # Crear DM
    dm = DMCerebro(llm_callback=llm_callback)
    dm.debug_mode = args.debug
    
    # Cargar personaje
    if args.cargar:
        pj = load_character(args.cargar)
        if not pj:
            print(f"  Error: Personaje '{args.cargar}' no encontrado.")
            sys.exit(1)
    else:
        pj = seleccionar_personaje()
        if not pj:
            print("  No se seleccionó personaje. Saliendo.")
            sys.exit(0)
    
    # Preparar personaje
    recalcular_derivados(pj)
    dm.cargar_personaje(pj)
    
    print(f"  ═══ {pj['info_basica']['nombre']} ═══")
    print(f"  {pj['info_basica']['raza']} {pj['info_basica']['clase']}")
    
    # Verificar si hay estado de aventura guardado
    estado_guardado = pj.get("estado_aventura")
    es_continuacion = False
    
    if estado_guardado:
        # Preguntar si quiere continuar o nueva aventura
        if args.continuar:
            continuar = "s"
        else:
            print("\n  Se encontró una aventura guardada.")
            continuar = input("  ¿Continuar aventura? (s/n): ").strip().lower()
        
        if continuar in ("s", "si", "sí", "y", "yes"):
            print("  ✓ Continuando aventura guardada...")
            dm.cargar_estado(estado_guardado)
            es_continuacion = True
            
            # Mostrar resumen si existe
            resumen = estado_guardado.get("resumen", {})
            if resumen:
                print()
                if resumen.get("ubicacion_actual"):
                    print(f"  📍 Ubicación: {resumen['ubicacion_actual']}")
                if resumen.get("que_estaba_haciendo"):
                    print(f"  🎯 Haciendo: {resumen['que_estaba_haciendo']}")
                if resumen.get("resumen_sesion"):
                    print(f"  📜 Resumen: {resumen['resumen_sesion']}")
                print()
    
    if not es_continuacion:
        # Nueva aventura
        tipo_aventura = seleccionar_tipo_aventura()
        region = seleccionar_region()
        
        # Guardar tipo y región en el contexto del DM
        dm.contexto.flags["tipo_aventura"] = tipo_aventura
        dm.contexto.flags["region"] = region
        dm.contexto.notas_dm = f"TONO DE LA AVENTURA: {tipo_aventura['tono']}"
        
        # Generar Adventure Bible con LLM
        bible_generada = False
        if llm_callback:
            bible_generada = generar_aventura_bible(
                pj=dm.contexto.pj,
                tipo_aventura=tipo_aventura,
                region=region,
                llm_callback=llm_callback
            )
        
        # Cargar la biblia si se generó
        if bible_generada:
            bm = obtener_bible_manager()
            bible = bm.cargar_bible_full(dm.contexto.pj.get("id", ""))
            if bible:
                dm.contexto.flags["bible_id"] = bible.get("meta", {}).get("id")
                print(f"  📖 Aventura: {bible.get('logline', '')[:60]}...")
        
        # Crear escena inicial
        ubicacion, npcs = crear_escena_demo()
        dm.establecer_escena(**ubicacion)
        for npc in npcs:
            dm.añadir_npc(**npc)
    
    # Jugar
    jugar(dm, es_continuacion)


if __name__ == "__main__":
    main()
