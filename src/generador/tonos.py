"""
Gestión de módulos de tono para aventuras.
"""

import json
import os
from typing import Dict, Any, List, Optional

# Ruta a los archivos de tono
RUTA_TONOS = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'tonos')


def listar_tonos() -> List[Dict[str, str]]:
    """Lista todos los tonos disponibles con su nombre y descripción."""
    tonos = []
    
    if not os.path.exists(RUTA_TONOS):
        return tonos
    
    for archivo in os.listdir(RUTA_TONOS):
        if archivo.endswith('.json'):
            ruta = os.path.join(RUTA_TONOS, archivo)
            try:
                with open(ruta, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    tonos.append({
                        "id": datos.get("id", archivo[:-5]),
                        "nombre": datos.get("nombre", archivo[:-5]),
                        "descripcion": datos.get("descripcion_corta", "")
                    })
            except:
                pass
    
    # Ordenar: dm_elige al final
    tonos.sort(key=lambda x: (x["id"] == "dm_elige", x["nombre"]))
    return tonos


def cargar_tono(id_tono: str) -> Optional[Dict[str, Any]]:
    """Carga un módulo de tono completo."""
    ruta = os.path.join(RUTA_TONOS, f"{id_tono}.json")
    
    if not os.path.exists(ruta):
        return None
    
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def obtener_prompt_tono(id_tono: str) -> str:
    """
    Genera el fragmento de prompt específico para un tono.
    Este texto se inyecta en el system prompt del DM.
    """
    tono = cargar_tono(id_tono)
    
    if not tono:
        return ""
    
    partes = []
    
    partes.append(f"═══ TONO DE AVENTURA: {tono['nombre'].upper()} ═══")
    partes.append("")
    partes.append(f"Estilo: {tono.get('descripcion_corta', '')}")
    partes.append("")
    partes.append(f"TONO NARRATIVO: {tono.get('tono_narrativo', '')}")
    partes.append("")
    
    # Frecuencias
    freq = tono.get('frecuencias', {})
    if freq:
        partes.append("BALANCE DE CONTENIDO:")
        for tipo, nivel in freq.items():
            partes.append(f"  - {tipo.capitalize()}: {nivel}")
        partes.append("")
    
    # Cómo resolver fallos
    if tono.get('como_resolver_fallos'):
        partes.append(f"FALLOS: {tono['como_resolver_fallos']}")
        partes.append("")
    
    # Letalidad y moral
    partes.append(f"Letalidad: {tono.get('letalidad', 'media')} | Moral: {tono.get('moral', 'variable')}")
    partes.append("")
    
    # Arquetipos de NPC
    arquetipos = tono.get('arquetipos_npc', [])
    if arquetipos and arquetipos[0] != "Cualquier arquetipo según la escena":
        partes.append("ARQUETIPOS DE NPC TÍPICOS:")
        for arq in arquetipos[:4]:
            partes.append(f"  - {arq}")
        partes.append("")
    
    # Tipos de antagonista
    antagonistas = tono.get('tipos_antagonista', [])
    if antagonistas and antagonistas[0] != "Cualquier tipo según la historia":
        partes.append("TIPOS DE ANTAGONISTA:")
        for ant in antagonistas[:3]:
            partes.append(f"  - {ant}")
        partes.append("")
    
    # Reglas especiales (para misterio)
    reglas = tono.get('reglas_especiales', {})
    if reglas:
        partes.append("REGLAS ESPECIALES:")
        if reglas.get('pistas_por_revelacion'):
            partes.append(f"  - Cada revelación tiene {reglas['pistas_por_revelacion']} pistas (Regla de Tres)")
        if reglas.get('pista_garantizada'):
            partes.append("  - Siempre hay una pista garantizada por revelación")
        if reglas.get('relojes_activos'):
            partes.append("  - Usa relojes para tensión temporal")
        if reglas.get('foreshadowing_obligatorio'):
            partes.append("  - Foreshadowing OBLIGATORIO antes de revelaciones")
        partes.append("")
    
    # Prompt extra
    if tono.get('prompt_extra'):
        partes.append("INSTRUCCIONES DE TONO:")
        partes.append(tono['prompt_extra'])
        partes.append("")
    
    return "\n".join(partes)


def obtener_balance_solitario(id_tono: str, nivel_pj: int = 1) -> Dict[str, Any]:
    """
    Genera las reglas de balance para partida en solitario según el tono.
    """
    tono = cargar_tono(id_tono)
    
    # Valores base
    balance = {
        "dificultad_objetivo": "media",
        "letalidad": "media",
        "combate": {
            "encuentros_por_acto": "2-3",
            "enemigos_max_por_encuentro": 3,
            "cr_max_individual": nivel_pj + 1,
            "descansos_entre_encuentros": True
        },
        "obstaculos": {
            "cd_tipica": "10-14",
            "cd_maxima": 16,
            "siempre_alternativa": True
        }
    }
    
    if not tono:
        return balance
    
    # Ajustar según tono
    letalidad = tono.get('letalidad', 'media')
    
    if letalidad == "alta":
        balance["letalidad"] = "alta"
        balance["combate"]["enemigos_max_por_encuentro"] = 4
        balance["obstaculos"]["cd_maxima"] = 18
        balance["combate"]["descansos_entre_encuentros"] = False
        
    elif letalidad == "baja" or letalidad == "muy_baja":
        balance["letalidad"] = "baja"
        balance["combate"]["enemigos_max_por_encuentro"] = 2
        balance["obstaculos"]["cd_tipica"] = "8-12"
        balance["obstaculos"]["cd_maxima"] = 14
    
    # Ajustar frecuencia de combate
    freq_combate = tono.get('frecuencias', {}).get('combate', 'media')
    if freq_combate == "alta":
        balance["combate"]["encuentros_por_acto"] = "3-4"
    elif freq_combate == "baja":
        balance["combate"]["encuentros_por_acto"] = "1-2"
    
    return balance
