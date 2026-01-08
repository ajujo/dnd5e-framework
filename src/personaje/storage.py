"""
Almacenamiento de personajes D&D 5e.

Maneja guardado, carga, listado y autosave de personajes.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid


# Directorios de almacenamiento
STORAGE_BASE = Path(__file__).parent.parent.parent / "storage"
CHARACTERS_DIR = STORAGE_BASE / "characters"
AUTOSAVE_DIR = STORAGE_BASE / "autosave"


def _asegurar_directorios():
    """Crea directorios de storage si no existen."""
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    AUTOSAVE_DIR.mkdir(parents=True, exist_ok=True)


def generar_id() -> str:
    """
    Genera un ID único para un personaje.
    
    Returns:
        ID de 8 caracteres
    """
    return str(uuid.uuid4())[:8]


def save_character(pj: dict) -> str:
    """
    Guarda un personaje completo.
    
    Args:
        pj: Diccionario del personaje
        
    Returns:
        ID del personaje guardado
    """
    _asegurar_directorios()
    
    # Asegurar que tiene ID
    if "id" not in pj:
        pj["id"] = generar_id()
    
    # Actualizar fechas
    ahora = datetime.now().isoformat()
    pj["fecha_modificacion"] = ahora
    if "fecha_creacion" not in pj:
        pj["fecha_creacion"] = ahora
    
    # Guardar archivo
    filepath = CHARACTERS_DIR / f"{pj['id']}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(pj, f, indent=2, ensure_ascii=False)
    
    # Limpiar autosave si existe
    autosave_path = AUTOSAVE_DIR / f"{pj['id']}.json"
    if autosave_path.exists():
        autosave_path.unlink()
    
    return pj["id"]


def load_character(id_personaje: str) -> Optional[dict]:
    """
    Carga un personaje por ID.
    
    Args:
        id_personaje: ID del personaje
        
    Returns:
        Diccionario del personaje o None si no existe
    """
    filepath = CHARACTERS_DIR / f"{id_personaje}.json"
    if not filepath.exists():
        return None
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def list_characters() -> List[Dict[str, Any]]:
    """
    Lista todos los personajes guardados.
    
    Returns:
        Lista de diccionarios con info resumida:
        {id, nombre, raza, clase, nivel, fecha_modificacion}
    """
    _asegurar_directorios()
    
    personajes = []
    for filepath in CHARACTERS_DIR.glob("*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                pj = json.load(f)
                info = pj.get("info_basica", {})
                personajes.append({
                    "id": pj.get("id", filepath.stem),
                    "nombre": info.get("nombre", "Sin nombre"),
                    "raza": info.get("raza", "?"),
                    "clase": info.get("clase", "?"),
                    "nivel": info.get("nivel", 1),
                    "fecha_modificacion": pj.get("fecha_modificacion", ""),
                })
        except Exception:
            continue
    
    # Ordenar por fecha de modificación (más reciente primero)
    personajes.sort(key=lambda x: x.get("fecha_modificacion", ""), reverse=True)
    
    return personajes


def delete_character(id_personaje: str) -> bool:
    """
    Elimina un personaje.
    
    Args:
        id_personaje: ID del personaje a eliminar
        
    Returns:
        True si se eliminó, False si no existía
    """
    filepath = CHARACTERS_DIR / f"{id_personaje}.json"
    if filepath.exists():
        filepath.unlink()
        return True
    return False


def autosave_step(
    pj: dict, 
    paso_actual: str, 
    pasos_completados: List[str]
) -> str:
    """
    Guarda el progreso parcial de la creación de un personaje.
    
    Permite retomar la creación desde donde se dejó.
    
    Args:
        pj: Personaje en construcción
        paso_actual: Nombre del paso actual
        pasos_completados: Lista de pasos ya completados
        
    Returns:
        ID del autosave
    """
    _asegurar_directorios()
    
    # Asegurar ID
    if "id" not in pj:
        pj["id"] = generar_id()
    
    # Estructura del autosave
    autosave = {
        "pj": pj,
        "paso_actual": paso_actual,
        "pasos_completados": pasos_completados,
        "fecha": datetime.now().isoformat(),
    }
    
    filepath = AUTOSAVE_DIR / f"{pj['id']}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(autosave, f, indent=2, ensure_ascii=False)
    
    return pj["id"]


def load_autosave(id_personaje: str) -> Optional[Dict[str, Any]]:
    """
    Carga un autosave para continuar creación.
    
    Args:
        id_personaje: ID del autosave
        
    Returns:
        Diccionario con {pj, paso_actual, pasos_completados, fecha}
        o None si no existe
    """
    filepath = AUTOSAVE_DIR / f"{id_personaje}.json"
    if not filepath.exists():
        return None
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def list_autosaves() -> List[Dict[str, Any]]:
    """
    Lista todos los autosaves pendientes.
    
    Returns:
        Lista de diccionarios con info resumida:
        {id, nombre, paso_actual, fecha}
    """
    _asegurar_directorios()
    
    autosaves = []
    for filepath in AUTOSAVE_DIR.glob("*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                pj = data.get("pj", {})
                info = pj.get("info_basica", {})
                autosaves.append({
                    "id": pj.get("id", filepath.stem),
                    "nombre": info.get("nombre", "En progreso..."),
                    "raza": info.get("raza", "?"),
                    "clase": info.get("clase", "?"),
                    "paso_actual": data.get("paso_actual", "?"),
                    "pasos_completados": data.get("pasos_completados", []),
                    "fecha": data.get("fecha", ""),
                })
        except Exception:
            continue
    
    # Ordenar por fecha (más reciente primero)
    autosaves.sort(key=lambda x: x.get("fecha", ""), reverse=True)
    
    return autosaves


def delete_autosave(id_personaje: str) -> bool:
    """
    Elimina un autosave.
    
    Args:
        id_personaje: ID del autosave a eliminar
        
    Returns:
        True si se eliminó, False si no existía
    """
    filepath = AUTOSAVE_DIR / f"{id_personaje}.json"
    if filepath.exists():
        filepath.unlink()
        return True
    return False


def exists_character(id_personaje: str) -> bool:
    """Comprueba si existe un personaje guardado."""
    filepath = CHARACTERS_DIR / f"{id_personaje}.json"
    return filepath.exists()


def exists_autosave(id_personaje: str) -> bool:
    """Comprueba si existe un autosave."""
    filepath = AUTOSAVE_DIR / f"{id_personaje}.json"
    return filepath.exists()


def get_character_filepath(id_personaje: str) -> Optional[Path]:
    """
    Obtiene la ruta al archivo de un personaje.
    
    Returns:
        Path al archivo o None si no existe
    """
    filepath = CHARACTERS_DIR / f"{id_personaje}.json"
    if filepath.exists():
        return filepath
    return None
