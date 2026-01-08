#!/usr/bin/env python3
"""
Sesión mínima de juego - Validación end-to-end del sistema.

Una escena + una decisión + una consecuencia + guardar.
"""

import sys
import argparse
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent))

from personaje import load_character, save_character, recalcular_derivados
from motor.dados import tirar
from motor.combate_utils import tirar_ataque, resolver_ataque, tirar_daño


# ============================================================
# CONFIGURACIÓN LLM
# ============================================================
_llm_callback = None

def configurar_llm():
    """Configura conexión con LLM local."""
    global _llm_callback
    
    try:
        import requests
        
        # Intentar LM Studio
        response = requests.get("http://localhost:1234/v1/models", timeout=2)
        if response.status_code == 200:
            print("✓ LM Studio conectado")
            
            def callback(prompt: str, system: str = None) -> str:
                resp = requests.post(
                    "http://localhost:1234/v1/chat/completions",
                    json={
                        "messages": [
                            {"role": "system", "content": system or SYSTEM_PROMPT_DM},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 300,
                    },
                    timeout=30
                )
                return resp.json()["choices"][0]["message"]["content"]
            
            _llm_callback = callback
            return True
    except:
        pass
    
    print("⚠ No se encontró LLM local. Usando modo básico.")
    return False


SYSTEM_PROMPT_DM = """Eres un Dungeon Master narrando una sesión de D&D 5e.

REGLAS:
- Describe en 2-3 frases máximo
- NO expliques reglas ni mecánicas
- NO muestres números ni dados
- SÍ describe efectos narrativos
- Mantén tensión y atmósfera
- Usa segunda persona ("Ves...", "Sientes...")
- NO preguntes "¿Qué haces?" (eso lo hace la interfaz)

ESTILO:
- Conciso y evocador
- Sin formato markdown
- Prosa directa
"""


def narrar(prompt: str) -> str:
    """Genera narración con LLM o texto básico."""
    if _llm_callback:
        return _llm_callback(prompt)
    return prompt


# ============================================================
# ESCENAS PREDEFINIDAS
# ============================================================
ESCENA_INICIAL = {
    "descripcion": "El sendero del bosque se estrecha entre robles centenarios. Un hombre corpulento bloquea el camino, con una espada corta en la mano. Su mirada es fría y calculadora.",
    "npc": {
        "nombre": "Bandido",
        "hp": 11,
        "hp_max": 11,
        "ca": 12,
        "ataque": 4,
        "daño": "1d6+2",
        "hostil": True,
    }
}

# Estado narrativo para mantener coherencia con el LLM
def crear_estado_narrativo(pj: dict = None):
    estado = {
        "escena": "sendero del bosque entre robles",
        "enemigo": "bandido humano",
        "fase": "tension",  # tension | combate | desenlace
        "ultimo_evento": "El bandido bloquea el camino con su espada desenvainada",
        "arma_pj": "espada",
        "nombre_pj": "el aventurero",
    }
    
    # Extraer datos del PJ si está disponible
    if pj:
        equipo = pj.get("equipo", {})
        arma = next((a for a in equipo.get("armas", []) if a.get("equipada")), None)
        if arma:
            estado["arma_pj"] = arma.get("nombre", "espada")
        
        info = pj.get("info_basica", {})
        if info.get("nombre"):
            estado["nombre_pj"] = info["nombre"]
    
    return estado


def construir_contexto_llm(estado: dict) -> str:
    """Construye el contexto fijo para el LLM."""
    return (
        "CONTEXTO FIJO (NO MODIFICAR):\n"
        f"- Escena: {estado['escena']}\n"
        f"- Enemigo: {estado['enemigo']} (arma: espada corta)\n"
        f"- Aventurero: {estado.get('nombre_pj', 'el aventurero')} (arma: {estado.get('arma_pj', 'espada')})\n"
        f"- Fase actual: {estado['fase']}\n"
        f"- Último evento: {estado['ultimo_evento']}\n\n"
        "REGLAS ESTRICTAS:\n"
        "- No repitas el último evento\n"
        "- No cambies enemigo (siempre bandido humano, NO ogro/gigante/monstruo)\n"
        "- No cambies lugar (siempre sendero del bosque)\n"
        "- Usa el arma correcta del aventurero (NO inventes otra)\n"
        "- No inventes violencia si el jugador no ataca\n"
        "- 1-2 frases máximo\n\n"
    )


# ============================================================
# FUNCIONES DE JUEGO
# ============================================================
def mostrar_estado_pj(pj: dict):
    """Muestra estado actual del PJ."""
    info = pj.get("info_basica", {})
    derivados = pj.get("derivados", {})
    equipo = pj.get("equipo", {})
    
    print(f"\n  ═══ {info.get('nombre', 'Aventurero')} ═══")
    print(f"  {info.get('raza', '?')} {info.get('clase', '?')} Nv.{info.get('nivel', 1)}")
    print(f"  HP: {derivados.get('puntos_golpe_actual', '?')}/{derivados.get('puntos_golpe_maximo', '?')} | CA: {derivados.get('clase_armadura', '?')}")
    
    arma = next((a for a in equipo.get("armas", []) if a.get("equipada")), None)
    if arma:
        print(f"  Arma: {arma.get('nombre', '?')}")
    print()


def mostrar_escena(escena: dict, estado: dict = None):
    """Muestra la escena actual."""
    print("\n" + "─" * 60)
    
    if _llm_callback and estado:
        # Usar contexto fijo
        contexto = construir_contexto_llm(estado)
        desc = narrar(
            contexto +
            f"Describe la escena inicial: {escena['descripcion']}"
        )
        print(f"\n  {desc}")
    elif _llm_callback:
        print(f"\n  {escena['descripcion']}")
    else:
        print(f"\n  {escena['descripcion']}")
    
    print("\n" + "─" * 60)


def procesar_accion(accion: str, pj: dict, escena: dict, estado: dict) -> dict:
    """
    Procesa la acción del jugador y devuelve el resultado.
    
    Args:
        estado: Estado narrativo para contexto del LLM
    
    Returns:
        dict con: tipo, exito, descripcion, daño (si aplica)
    """
    accion_lower = accion.lower()
    npc = escena.get("npc", {})
    resultado = {"tipo": "narrar", "descripcion": ""}
    
    # Detectar tipo de acción
    if any(palabra in accion_lower for palabra in ["ataco", "atacar", "golpeo", "golpear", "disparo", "disparar"]):
        resultado["tipo"] = "ataque"
        
        # Calcular ataque del PJ
        derivados = pj.get("derivados", {})
        mods = derivados.get("modificadores", {})
        bon_comp = derivados.get("bonificador_competencia", 2)
        
        # Determinar si es CaC o distancia
        es_distancia = any(p in accion_lower for p in ["disparo", "flecha", "arco", "ballesta"])
        mod_ataque = mods.get("destreza" if es_distancia else "fuerza", 0)
        
        bonus_total = mod_ataque + bon_comp
        tirada = tirar("1d20")
        total = tirada.total + bonus_total
        
        print(f"\n  [Tirada de ataque: {tirada.total} + {bonus_total} = {total} vs CA {npc.get('ca', 10)}]")
        
        if total >= npc.get("ca", 10):
            # Impacto - calcular daño
            equipo = pj.get("equipo", {})
            arma = next((a for a in equipo.get("armas", []) if a.get("equipada")), None)
            
            # Daño base según arma (simplificado)
            if arma:
                # Usar daño básico de arma
                daño_base = "1d8"  # Por defecto
                if "daga" in arma.get("nombre", "").lower():
                    daño_base = "1d4"
                elif "espada corta" in arma.get("nombre", "").lower():
                    daño_base = "1d6"
            else:
                daño_base = "1d4"  # Desarmado
            
            tirada_daño = tirar(daño_base)
            daño_total = tirada_daño.total + mod_ataque
            bonus_estilo = 0
            nombre_estilo = ""
            
            # Verificar estilo de combate
            rasgos = pj.get("rasgos", {}).get("clase", [])
            for r in rasgos:
                if r.get("id") == "estilo_combate":
                    opcion = r.get("opcion", "")
                    if opcion == "duelo":
                        bonus_estilo = 2
                        nombre_estilo = "Duelo"
                    # Armas Grandes: repetir 1s y 2s (simplificado aquí)
                    break
            
            daño_total += bonus_estilo
            
            # Mostrar desglose
            desglose = f"{tirada_daño.total} + {mod_ataque} FUE"
            if bonus_estilo > 0:
                desglose += f" + {bonus_estilo} {nombre_estilo}"
            print(f"  [Daño: {desglose} = {daño_total}]")
            
            resultado["exito"] = True
            resultado["daño"] = daño_total
            resultado["descripcion"] = f"¡Impacto! {daño_total} de daño."
            
            # Aplicar daño al NPC
            npc["hp"] = npc.get("hp", 0) - daño_total
            
            # Actualizar estado narrativo
            estado["fase"] = "combate"
            estado["ultimo_evento"] = f"El aventurero golpeó al bandido causando {daño_total} de daño"
            
            if npc["hp"] <= 0:
                resultado["npc_derrotado"] = True
        else:
            resultado["exito"] = False
            resultado["descripcion"] = "El ataque falla."
            estado["fase"] = "combate"
            estado["ultimo_evento"] = "El aventurero falló su ataque"
    
    elif any(palabra in accion_lower for palabra in ["intimidar", "intimido", "amenazo"]):
        resultado["tipo"] = "habilidad"
        
        # Tirada de Intimidación
        mods = pj.get("derivados", {}).get("modificadores", {})
        habilidades = pj.get("competencias", {}).get("habilidades", [])
        
        mod_car = mods.get("carisma", 0)
        bonus = mod_car
        if "intimidacion" in habilidades:
            bonus += pj.get("derivados", {}).get("bonificador_competencia", 2)
        
        tirada = tirar("1d20")
        total = tirada.total + bonus
        cd = 12  # CD básica
        
        print(f"\n  [Tirada de Intimidación: {tirada.total} + {bonus} = {total} vs CD {cd}]")
        
        resultado["exito"] = total >= cd
        if resultado["exito"]:
            resultado["descripcion"] = "Tu presencia lo intimida visiblemente."
            npc["hostil"] = False
        else:
            resultado["descripcion"] = "No parece impresionado por tu amenaza."
    
    elif any(palabra in accion_lower for palabra in ["huyo", "huir", "corro", "escapo"]):
        resultado["tipo"] = "huida"
        resultado["descripcion"] = "Te das la vuelta y huyes por el sendero."
        resultado["fin_escena"] = True
    
    else:
        # Detectar si es diálogo (hablar, preguntar, decir)
        es_dialogo = any(palabra in accion_lower for palabra in [
            "digo", "pregunto", "hablo", "grito", "susurro", "respondo",
            "le digo", "qué quieres", "quién", "por qué", "cómo", "dónde"
        ]) or accion.endswith("?") or accion.endswith("!")
        
        resultado["tipo"] = "dialogo" if es_dialogo else "narrar"
        
        if _llm_callback:
            # Usar contexto fijo
            contexto_base = construir_contexto_llm(estado)
            
            if es_dialogo:
                resultado["descripcion"] = narrar(
                    contexto_base +
                    "ACCIÓN: El jugador HABLA (no ataca).\n"
                    f"Dice: '{accion}'\n"
                    "Narra SOLO la respuesta verbal del bandido (sin violencia)."
                )
                estado["ultimo_evento"] = f"El aventurero dijo: {accion[:50]}"
            else:
                resultado["descripcion"] = narrar(
                    contexto_base +
                    f"ACCIÓN: {accion}\n"
                    "Narra la reacción del bandido (sin violencia, 1-2 frases)."
                )
                estado["ultimo_evento"] = f"El aventurero: {accion[:50]}"
        else:
            if es_dialogo:
                resultado["descripcion"] = '"No es asunto tuyo", gruñe el bandido sin bajar la guardia.'
            else:
                resultado["descripcion"] = "El bandido te observa con desconfianza, sin bajar la guardia."
    
    return resultado


def turno_npc(pj: dict, npc: dict) -> dict:
    """El NPC realiza su turno."""
    if not npc.get("hostil", True):
        return {"descripcion": "El hombre retrocede, nervioso, sin atacar."}
    
    if npc.get("hp", 0) <= 0:
        return {"descripcion": ""}
    
    # El NPC ataca
    derivados = pj.get("derivados", {})
    ca_pj = derivados.get("clase_armadura", 10)
    
    tirada = tirar("1d20")
    total = tirada.total + npc.get("ataque", 3)
    
    print(f"\n  [El bandido ataca: {tirada.total} + {npc.get('ataque', 3)} = {total} vs CA {ca_pj}]")
    
    if total >= ca_pj:
        # Daño
        tirada_daño = tirar(npc.get("daño", "1d6"))
        daño = tirada_daño.total
        
        # Aplicar al PJ
        hp_actual = derivados.get("puntos_golpe_actual", 0)
        derivados["puntos_golpe_actual"] = max(0, hp_actual - daño)
        
        return {
            "exito": True,
            "daño": daño,
            "descripcion": f"¡Te golpea! Recibes {daño} de daño."
        }
    else:
        return {
            "exito": False,
            "descripcion": "Su ataque pasa rozándote sin impactar."
        }


def narrar_resultado(resultado: dict, estado: dict = None, es_npc: bool = False):
    """Narra el resultado de una acción usando el contexto fijo."""
    if _llm_callback and resultado.get("descripcion"):
        quien = "el bandido" if es_npc else "el aventurero"
        evento = f"Acción de {quien}. Resultado: {resultado['descripcion']}"
        
        if resultado.get("exito") and resultado.get("daño"):
            evento += f" Daño: {resultado['daño']}."
        
        if resultado.get("npc_derrotado"):
            evento += " El enemigo cae derrotado."
        
        # Usar contexto fijo si está disponible
        if estado:
            contexto_base = construir_contexto_llm(estado)
            narracion = narrar(
                contexto_base +
                f"EVENTO A NARRAR: {evento}\n"
                "Narra SOLO este momento en 1 frase."
            )
        else:
            narracion = narrar(
                "REGLAS: Enemigo=bandido humano. Lugar=sendero del bosque.\n"
                f"Narra en 1 frase: {evento}"
            )
        
        print(f"\n  {narracion}")
    else:
        print(f"\n  {resultado.get('descripcion', '')}")


# ============================================================
# BUCLE PRINCIPAL
# ============================================================
def jugar_sesion(pj_id: str):
    """Ejecuta una sesión mínima de juego."""
    
    print("\n" + "═" * 60)
    print("  SESIÓN MÍNIMA - D&D 5e")
    print("═" * 60)
    
    # 1. Cargar PJ
    print("\n  Cargando personaje...")
    pj = load_character(pj_id)
    
    if not pj:
        print(f"  ✗ No se encontró el personaje con ID: {pj_id}")
        return False
    
    # Recalcular derivados
    recalcular_derivados(pj)
    
    # Asegurar HP actual
    if "puntos_golpe_actual" not in pj.get("derivados", {}):
        pj["derivados"]["puntos_golpe_actual"] = pj["derivados"].get("puntos_golpe_maximo", 10)
    
    mostrar_estado_pj(pj)
    print("  ✓ Personaje listo")
    
    # 2. Configurar LLM
    configurar_llm()
    
    # 3. Escena inicial
    escena = ESCENA_INICIAL.copy()
    escena["npc"] = ESCENA_INICIAL["npc"].copy()
    
    # Estado narrativo para coherencia del LLM
    estado_narrativo = crear_estado_narrativo(pj)
    
    mostrar_escena(escena, estado_narrativo)
    
    # 4. Bucle de juego
    turno = 1
    while True:
        # Estado del NPC
        npc = escena["npc"]
        if npc["hp"] > 0:
            print(f"\n  [Bandido: HP {npc['hp']}/{npc['hp_max']}]")
        
        # Input del jugador
        print("\n  ¿Qué haces?")
        print("  (escribe tu acción, /guardar, /estado, /curar, /reset, /salir)")
        
        try:
            accion = input("  > ").strip()
        except (KeyboardInterrupt, EOFError):
            accion = "/salir"
        
        if not accion:
            continue
        
        # Comandos especiales
        if accion.lower() == "/salir":
            print("\n  Guardando y saliendo...")
            save_character(pj)
            print("  ✓ Partida guardada")
            break
        
        if accion.lower() == "/guardar":
            save_character(pj)
            print("\n  ✓ Partida guardada")
            continue
        
        if accion.lower() == "/estado":
            mostrar_estado_pj(pj)
            continue
        
        if accion.lower() == "/curar":
            hp_max = pj["derivados"].get("puntos_golpe_maximo", 10)
            pj["derivados"]["puntos_golpe_actual"] = hp_max
            print(f"\n  ✓ HP restaurado a {hp_max}/{hp_max}")
            continue
        
        if accion.lower() == "/reset":
            # Restaurar HP del PJ
            hp_max = pj["derivados"].get("puntos_golpe_maximo", 10)
            pj["derivados"]["puntos_golpe_actual"] = hp_max
            # Reiniciar el NPC
            escena["npc"] = ESCENA_INICIAL["npc"].copy()
            # Reiniciar estado narrativo
            estado_narrativo = crear_estado_narrativo(pj)
            print("\n  ✓ Encuentro reiniciado")
            print(f"  PJ: HP {hp_max}/{hp_max}")
            print(f"  Bandido: HP {escena['npc']['hp']}/{escena['npc']['hp_max']}")
            mostrar_escena(escena, estado_narrativo)
            continue
        
        # 5. Procesar acción del jugador
        resultado = procesar_accion(accion, pj, escena, estado_narrativo)
        narrar_resultado(resultado, estado_narrativo)
        
        # Fin de escena por huida
        if resultado.get("fin_escena"):
            print("\n  [Fin de la escena]")
            save_character(pj)
            break
        
        # NPC derrotado (ya se narró el impacto en narrar_resultado)
        if resultado.get("npc_derrotado"):
            print("\n  ═══ ¡VICTORIA! ═══")
            print("  El camino queda libre.")
            save_character(pj)
            break
        
        # 6. Turno del NPC (si sigue vivo y hostil)
        if npc["hp"] > 0 and npc.get("hostil") and resultado.get("tipo") in ("ataque", "habilidad", "huida"):
            resultado_npc = turno_npc(pj, npc)
            narrar_resultado(resultado_npc, estado_narrativo, es_npc=True)
            
            # Comprobar si el PJ cayó
            if pj["derivados"].get("puntos_golpe_actual", 0) <= 0:
                print("\n  ═══ HAS CAÍDO ═══")
                print("  Tu visión se nubla mientras caes al suelo...")
                save_character(pj)
                break
        
        turno += 1
        
        # Límite de seguridad
        if turno > 20:
            print("\n  [Límite de turnos alcanzado]")
            break
    
    # Mostrar estado final
    print("\n" + "─" * 60)
    mostrar_estado_pj(pj)
    print("  Sesión finalizada.")
    
    return True


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Sesión mínima de D&D 5e")
    parser.add_argument("--cargar", "-c", required=True, help="ID del personaje a cargar")
    
    args = parser.parse_args()
    
    jugar_sesion(args.cargar)


if __name__ == "__main__":
    main()
