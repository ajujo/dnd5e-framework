#!/usr/bin/env python3
"""
CLI de Combate para D&D 5e

Loop interactivo de combate que integra:
- GestorCombate (estado)
- Pipeline (normalización + validación)
- Narrador (texto inmersivo)

USO:
    python src/cli_combate.py [--llm]

COMANDOS ESPECIALES:
    /estado     - Ver estado completo
    /hp         - Ver solo HPs
    /turno      - Ver de quién es el turno
    /pasar      - Pasar turno sin acción
    /salir      - Terminar combate
    /ayuda      - Ver comandos
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Variables globales
_cliente_llm = None
_modo_reglas = False  # Mostrar tiradas detalladas

from motor import (
    GestorCombate,
    Combatiente,
    TipoCombatiente,
    EstadoCombate,
    CompendioMotor,
    TipoResultado,
    NarradorLLM,
    crear_contexto_narracion,
    rng,
    crear_cliente_llm,
    crear_callback_narrador,
)


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

COLORES = {
    "reset": "\033[0m",
    "rojo": "\033[91m",
    "verde": "\033[92m",
    "amarillo": "\033[93m",
    "azul": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "gris": "\033[90m",
    "negrita": "\033[1m",
}

def color(texto: str, nombre: str) -> str:
    """Aplica color al texto si el terminal lo soporta."""
    if sys.stdout.isatty():
        return f"{COLORES.get(nombre, '')}{texto}{COLORES['reset']}"
    return texto


# =============================================================================
# HELPERS DE IMPRESIÓN
# =============================================================================

def imprimir_banner():
    """Imprime el banner inicial."""
    print()
    print(color("=" * 60, "cyan"))
    print(color("  ⚔️  COMBATE D&D 5e - CLI INTERACTIVO  ⚔️", "negrita"))
    print(color("=" * 60, "cyan"))
    print()


def imprimir_separador():
    """Imprime un separador."""
    print(color("-" * 60, "gris"))


def imprimir_hp_bar(nombre: str, hp: int, hp_max: int, es_pc: bool = True):
    """Imprime una barra de HP visual."""
    pct = hp / max(1, hp_max)
    barras = int(pct * 20)
    barra = "█" * barras + "░" * (20 - barras)
    
    if pct > 0.5:
        color_hp = "verde"
    elif pct > 0.25:
        color_hp = "amarillo"
    else:
        color_hp = "rojo"
    
    tipo_color = "cyan" if es_pc else "magenta"
    
    nombre_fmt = f"{nombre[:15]:15}"
    print(f"  {color(nombre_fmt, tipo_color)} [{color(barra, color_hp)}] {hp}/{hp_max}")


def imprimir_estado_combate(gestor: GestorCombate):
    """Imprime el estado actual del combate."""
    print()
    print(color("📊 ESTADO DEL COMBATE", "negrita"))
    imprimir_separador()
    print(f"  Ronda: {gestor.ronda_actual}")
    turno = gestor.obtener_turno_actual()
    if turno:
        print(f"  Turno: {color(turno.nombre, 'amarillo')}")
    print()
    
    print(color("  COMBATIENTES:", "gris"))
    for c in gestor.listar_combatientes():
        if c.muerto:
            print(f"  {color('💀 ' + c.nombre, 'rojo')} - MUERTO")
        elif c.inconsciente:
            print(f"  {color('😵 ' + c.nombre, 'amarillo')} - INCONSCIENTE")
        else:
            es_pc = c.tipo == TipoCombatiente.PC
            imprimir_hp_bar(c.nombre, c.hp_actual, c.hp_maximo, es_pc)
    print()


def imprimir_hps_corto(gestor: GestorCombate):
    """Imprime solo los HPs de forma compacta."""
    partes = []
    for c in gestor.listar_combatientes():
        if c.muerto:
            partes.append(f"{c.nombre}:💀")
        elif c.inconsciente:
            partes.append(f"{c.nombre}:😵")
        else:
            partes.append(f"{c.nombre}:{c.hp_actual}/{c.hp_maximo}")
    
    print(color(f"  HP: {' | '.join(partes)}", "gris"))


def imprimir_narracion(respuesta):
    """Imprime la narración y feedback."""
    if respuesta.narracion:
        print()
        print(color("🎭 ", "amarillo") + respuesta.narracion)
    
    if respuesta.feedback_sistema:
        print(color(f"  ℹ️  {respuesta.feedback_sistema}", "gris"))




def imprimir_tiradas(resultado):
    """Imprime las tiradas detalladas si el modo reglas está activo."""
    global _modo_reglas
    if not _modo_reglas:
        return
    
    print(color("  ┌─ TIRADAS ─────────────────────────────", "gris"))
    
    for evento in resultado.eventos:
        tipo = evento.tipo
        datos = evento.datos
        
        if tipo == "ataque_realizado":
            tirada = datos.get("tirada", {})
            dados = tirada.get("dados", [])
            mod = tirada.get("modificador", 0)
            total = tirada.get("total", 0)
            
            dado_str = f"d20={dados[0]}" if dados else "d20=?"
            impacta = "✓ IMPACTA" if datos.get("impacta") else "✗ FALLA"
            
            if datos.get("es_critico"):
                impacta = "💥 CRÍTICO"
            elif datos.get("es_pifia"):
                impacta = "💀 PIFIA"
            
            objetivo = datos.get("objetivo_id", "?")
            arma = datos.get("arma_nombre", "?")
            
            print(color(f"  │ Ataque con {arma} vs {objetivo}", "gris"))
            print(color(f"  │   {dado_str} + {mod} = {total} → {impacta}", "gris"))
        
        elif tipo == "daño_calculado":
            tirada = datos.get("tirada", {})
            expresion = tirada.get("expresion", "?")
            dados = tirada.get("dados", [])
            total = datos.get("daño_total", 0)
            tipo_daño = datos.get("tipo_daño", "?")
            
            dados_str = "+".join(str(d) for d in dados) if dados else "?"
            
            print(color(f"  │ Daño: {expresion} = [{dados_str}] = {total} ({tipo_daño})", "gris"))
    
    print(color("  └────────────────────────────────────────", "gris"))

def imprimir_clarificacion(resultado, respuesta):
    """Imprime opciones de clarificación."""
    print()
    pregunta = respuesta.pregunta_reformulada or resultado.pregunta
    print(color(f"❓ {pregunta}", "amarillo"))
    print()
    
    for i, opcion in enumerate(resultado.opciones, 1):
        print(f"  {color(str(i), 'cyan')}) {opcion.texto}")
    
    print()


def imprimir_turno_header(gestor: GestorCombate):
    """Imprime el header del turno."""
    turno = gestor.obtener_turno_actual()
    if not turno:
        return
    
    print()
    imprimir_separador()
    tipo = "🛡️" if turno.tipo == TipoCombatiente.PC else "👹"
    print(color(f"  {tipo} TURNO DE {turno.nombre.upper()}", "negrita"))
    imprimir_separador()
    imprimir_hps_corto(gestor)


def imprimir_fin_combate(gestor: GestorCombate):
    """Imprime el resultado final del combate."""
    print()
    print(color("=" * 60, "cyan"))
    
    if gestor.estado == EstadoCombate.VICTORIA:
        print(color("  🎉 ¡VICTORIA! Los héroes han triunfado.", "verde"))
    elif gestor.estado == EstadoCombate.DERROTA:
        print(color("  💀 DERROTA. Los héroes han caído.", "rojo"))
    elif gestor.estado == EstadoCombate.EMPATE:
        print(color("  ⚖️  EMPATE. Nadie queda en pie.", "amarillo"))
    else:
        print(color("  🏁 Combate terminado.", "gris"))
    
    print(color("=" * 60, "cyan"))
    print(f"  Rondas totales: {gestor.ronda_actual}")
    print()


def imprimir_ayuda():
    """Imprime la ayuda de comandos."""
    print()
    print(color("📖 COMANDOS DISPONIBLES", "negrita"))
    imprimir_separador()
    print("  /estado  - Ver estado completo del combate")
    print("  /hp      - Ver HPs de todos")
    print("  /turno   - Ver de quién es el turno")
    print("  /pasar   - Pasar turno sin hacer nada")
    print("  /salir   - Terminar combate")
    print("  /ayuda   - Ver esta ayuda")
    print()
    print(color("  DEBUG:", "gris"))
    print("  /rules   - Mostrar tiradas detalladas")
    print("  /no_rules - Ocultar tiradas")
    print()
    print(color("  COMANDOS LLM:", "gris"))
    print("  /modelo  - Ver modelo actual")
    print("  /modelo <id> - Cambiar modelo")
    print("  /modelos - Listar modelos disponibles")
    print()
    print(color("  ACCIONES DE EJEMPLO:", "gris"))
    print("  'Ataco al goblin con mi espada'")
    print("  'Lanzo proyectil mágico al orco'")
    print("  'Me muevo 20 pies hacia la puerta'")
    print("  'Uso Dash'")
    print("  'Hago una prueba de percepción'")
    print()


# =============================================================================
# CONFIGURACIÓN DEL COMBATE
# =============================================================================

def crear_combate_ejemplo(compendio: CompendioMotor) -> GestorCombate:
    """Crea un combate de ejemplo para probar."""
    gestor = GestorCombate(compendio)
    
    # PC: Guerrero
    pc = Combatiente(
        id="pc_1",
        nombre="Thorin",
        tipo=TipoCombatiente.PC,
        hp_maximo=28,
        clase_armadura=16,
        velocidad=30,
        fuerza=16,
        destreza=14,
        constitucion=14,
        inteligencia=10,
        sabiduria=12,
        carisma=8,
        bonificador_competencia=2,
        arma_principal={
            "id": "espada_1",
            "compendio_ref": "espada_larga",
            "nombre": "Espada larga"
        },
        conjuros_conocidos=[],
        ranuras_conjuro={},
    )
    
    # Enemigos: 2 Goblins (cargados del compendio con sus acciones)
    goblin1 = gestor.agregar_desde_compendio(
        monstruo_id="goblin",
        instancia_id="goblin_1",
        nombre="Goblin"
    )
    
    goblin2 = gestor.agregar_desde_compendio(
        monstruo_id="goblin",
        instancia_id="goblin_2",
        nombre="Goblin arquero"
    )
    
    gestor.agregar_combatiente(pc)
    
    # Mostrar acciones cargadas (debug)
    if goblin1.acciones:
        print(f"  Goblin tiene {len(goblin1.acciones)} acciones: {[a['nombre'] for a in goblin1.acciones]}")
    if goblin2.acciones:
        print(f"  Goblin arquero tiene {len(goblin2.acciones)} acciones: {[a['nombre'] for a in goblin2.acciones]}")
    
    return gestor


# =============================================================================
# LOOP PRINCIPAL
# =============================================================================

def procesar_input_clarificacion(texto: str, opciones: list) -> str:
    """
    Procesa el input del usuario para clarificación.
    Acepta número (1, 2, 3...) o texto.
    
    Devuelve el TEXTO de la opción (no el id) para que el normalizador
    lo procese como lenguaje natural.
    """
    texto = texto.strip()
    
    # Intentar como número
    try:
        indice = int(texto) - 1
        if 0 <= indice < len(opciones):
            return opciones[indice].texto
    except ValueError:
        pass
    
    # Buscar por texto parcial (case insensitive)
    texto_lower = texto.lower()
    for opcion in opciones:
        if texto_lower in opcion.texto.lower():
            return opcion.texto
    
    # Devolver como está
    return texto


def turno_npc(gestor: GestorCombate, narrador: NarradorLLM):
    """
    Ejecuta el turno de un NPC (IA simple).
    
    Siempre consume el turno (el loop debe llamar siguiente_turno después).
    """
    turno = gestor.obtener_turno_actual()
    if not turno or turno.tipo == TipoCombatiente.PC:
        return True
    
    # IA simple: seleccionar objetivo EXPLÍCITAMENTE
    # NPC enemigo ataca a PCs vivos
    # NPC aliado atacaría a enemigos (si lo hubiera)
    
    if turno.tipo == TipoCombatiente.NPC_ENEMIGO:
        # Buscar PCs vivos
        objetivos = [
            c for c in gestor.listar_combatientes()
            if c.tipo == TipoCombatiente.PC and not c.muerto and not c.inconsciente
        ]
    else:
        # NPC aliado/neutral: atacar enemigos
        objetivos = [
            c for c in gestor.listar_combatientes()
            if c.tipo == TipoCombatiente.NPC_ENEMIGO and not c.muerto
        ]
    
    if objetivos:
        objetivo = objetivos[0]
        
        # Elegir acción del monstruo si tiene
        if turno.acciones:
            # Elegir acción según tipo de NPC
            accion_elegida = turno.acciones[0]  # Default: primera
            
            # Si tiene "arquero" en el nombre, preferir ataque a distancia
            if "arquero" in turno.nombre.lower():
                for acc in turno.acciones:
                    alcance = str(acc.get("alcance", ""))
                    if "/" in alcance:  # Formato "80/320" = distancia
                        accion_elegida = acc
                        break
            
            accion = f"Ataco a {objetivo.nombre} con {accion_elegida['nombre']}"
        else:
            accion = f"Ataco a {objetivo.nombre}"
    else:
        accion = "Paso turno"
    
    print(color(f"\n  🤖 {turno.nombre} decide: '{accion}'", "gris"))
    
    resultado = gestor.procesar_accion(accion)
    
    # Narrar
    ctx_narracion = crear_contexto_narracion(gestor, resultado)
    respuesta = narrador.narrar(ctx_narracion)
    imprimir_tiradas(resultado)
    imprimir_narracion(respuesta)
    
    # NPC siempre consume su turno (IA simple no maneja clarificaciones)
    if resultado.tipo != TipoResultado.ACCION_APLICADA:
        print(color("  (NPC pasa turno)", "gris"))


def loop_combate(gestor: GestorCombate, narrador: NarradorLLM):
    """Loop principal del combate."""
    imprimir_banner()
    print("Escribe '/ayuda' para ver comandos disponibles.")
    
    # Iniciar combate
    gestor.iniciar_combate()
    
    print(color("\n🎲 ¡El combate comienza!", "verde"))
    imprimir_estado_combate(gestor)
    
    pendiente_clarificacion = None
    
    while not gestor.combate_terminado():
        turno = gestor.obtener_turno_actual()
        
        if not turno:
            break
        
        # Turno de NPC
        if turno.tipo != TipoCombatiente.PC:
            turno_npc(gestor, narrador)
            gestor.siguiente_turno()
            continue
        
        # Turno de PC
        imprimir_turno_header(gestor)
        
        # Si hay clarificación pendiente
        if pendiente_clarificacion:
            imprimir_clarificacion(
                pendiente_clarificacion["resultado"],
                pendiente_clarificacion["respuesta"]
            )
        
        # Pedir input
        try:
            texto = input(color("\n  > ", "verde")).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            break
        
        if not texto:
            continue
        
        # Comandos especiales
        if texto.startswith("/"):
            cmd = texto.lower()
            if cmd == "/salir":
                print(color("\n  Combate abandonado.", "amarillo"))
                break
            elif cmd == "/estado":
                imprimir_estado_combate(gestor)
                continue
            elif cmd == "/hp":
                imprimir_hps_corto(gestor)
                continue
            elif cmd == "/turno":
                print(f"\n  Turno de: {turno.nombre}")
                continue
            elif cmd == "/pasar":
                print(color("  (Pasas tu turno)", "gris"))
                gestor.siguiente_turno()
                continue
            elif cmd == "/ayuda":
                imprimir_ayuda()
                continue
            elif cmd in ["/rules", "/reglas"]:
                global _modo_reglas
                _modo_reglas = True
                print(color("  ✓ Modo reglas activado (verás tiradas detalladas)", "verde"))
                continue
            elif cmd in ["/no_rules", "/no_reglas"]:
                _modo_reglas = False
                print(color("  ✓ Modo reglas desactivado", "amarillo"))
                continue
            elif cmd == "/modelos":
                if _cliente_llm:
                    modelos = _cliente_llm.listar_modelos()
                    print(color("\n📋 MODELOS DISPONIBLES:", "cyan"))
                    for i, m in enumerate(modelos[:15]):  # Mostrar max 15
                        marcador = "→" if m == _cliente_llm.modelo_efectivo else " "
                        print(f"  {marcador} {m}")
                    if len(modelos) > 15:
                        print(f"  ... y {len(modelos) - 15} más")
                else:
                    print(color("  No hay LLM conectado", "amarillo"))
                continue
            elif cmd.startswith("/modelo"):
                partes = texto.split(maxsplit=1)
                if len(partes) == 1:
                    # Solo /modelo: mostrar actual
                    if _cliente_llm:
                        print(f"  Modelo actual: {color(_cliente_llm.modelo_efectivo, 'cyan')}")
                    else:
                        print(color("  No hay LLM conectado", "amarillo"))
                else:
                    # /modelo <id>: cambiar
                    nuevo_modelo = partes[1].strip()
                    if _cliente_llm:
                        if _cliente_llm.cambiar_modelo(nuevo_modelo):
                            print(color(f"  ✓ Modelo cambiado a: {nuevo_modelo}", "verde"))
                        else:
                            print(color(f"  ✗ Modelo no encontrado: {nuevo_modelo}", "rojo"))
                            print("  Usa /modelos para ver disponibles")
                    else:
                        print(color("  No hay LLM conectado", "amarillo"))
                continue
            else:
                print(color(f"  Comando desconocido: {texto}", "rojo"))
                continue
        
        # Si había clarificación pendiente, procesar
        if pendiente_clarificacion:
            texto = procesar_input_clarificacion(
                texto,
                pendiente_clarificacion["resultado"].opciones
            )
            pendiente_clarificacion = None
        
        # Procesar acción
        resultado = gestor.procesar_accion(texto)
        
        # Crear contexto y narrar
        ctx_narracion = crear_contexto_narracion(gestor, resultado)
        respuesta = narrador.narrar(ctx_narracion)
        
        # Manejar resultado
        if resultado.tipo == TipoResultado.NECESITA_CLARIFICAR:
            pendiente_clarificacion = {
                "resultado": resultado,
                "respuesta": respuesta
            }
            continue
        
        imprimir_tiradas(resultado)
        imprimir_narracion(respuesta)
        
        if resultado.tipo == TipoResultado.ACCION_RECHAZADA:
            continue
        
        # Acción aplicada: siguiente turno si usó acción
        if resultado.cambios_estado.get("accion_usada"):
            gestor.siguiente_turno()
    
    # Fin del combate
    imprimir_fin_combate(gestor)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Punto de entrada."""
    # Parsear argumentos
    usar_llm = "--llm" in sys.argv
    seed = None
    modelo_preferido = None
    
    for arg in sys.argv[1:]:
        if arg.startswith("--seed="):
            seed = int(arg.split("=")[1])
        elif arg.startswith("--model="):
            modelo_preferido = arg.split("=")[1]
            usar_llm = True  # --model implica --llm
    
    # Configurar seed si se especificó
    if seed is not None:
        rng.set_seed(seed)
        print(f"Seed: {seed}")
    
    # Crear componentes
    compendio = CompendioMotor()
    gestor = crear_combate_ejemplo(compendio)
    
    # Narrador (con o sin LLM)
    llm_callback = None
    if usar_llm:
        print(color("🔍 Buscando LLM local...", "cyan"))
        cliente = crear_cliente_llm()
        
        # Aplicar modelo preferido si se especificó
        if cliente and modelo_preferido:
            if cliente.cambiar_modelo(modelo_preferido):
                print(color(f"  Usando modelo preferido: {modelo_preferido}", "gris"))
            else:
                print(color(f"  ⚠️  Modelo '{modelo_preferido}' no disponible, usando: {cliente.modelo_efectivo}", "amarillo"))
        if cliente:
            info = cliente.obtener_info()
            print(color(f"✓ {info['tipo']} conectado", "verde"))
            print(color(f"  Modelo: {info['modelo']}", "gris"))
            global _cliente_llm
            _cliente_llm = cliente
            llm_callback = crear_callback_narrador(cliente)
        else:
            print(color("⚠️  No se encontró LLM (LM Studio/Ollama). Usando narrador genérico.", "amarillo"))
            print(color("   Inicia LM Studio o Ollama para narración con IA.", "gris"))
    
    narrador = NarradorLLM(llm_callback=llm_callback, estilo="epico")
    
    # Ejecutar loop
    try:
        loop_combate(gestor, narrador)
    except Exception as e:
        print(color(f"\n❌ Error: {e}", "rojo"))
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
