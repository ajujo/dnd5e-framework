"""
Motor de Progresión de Personajes.

Gestiona experiencia (XP) y subida de nivel para D&D 5e.
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class GestorProgresion:
    """Gestiona XP y subida de nivel para personajes."""
    
    def __init__(self):
        """Inicializa el gestor cargando los datos de progresión."""
        self._datos_progresion = None
        self._cargar_datos()
    
    def _cargar_datos(self):
        """Carga los datos de progresión desde el compendio."""
        # Path: src/motor/progresion.py -> src/motor -> src -> project_root -> compendio
        ruta_compendio = Path(__file__).parent.parent.parent / "compendio" / "progresion_niveles.json"
        
        if ruta_compendio.exists():
            with open(ruta_compendio, "r", encoding="utf-8") as f:
                self._datos_progresion = json.load(f)
        else:
            # Datos mínimos por defecto si no existe el archivo
            self._datos_progresion = {
                "tabla_xp": [
                    {"nivel": i, "xp_necesaria": xp, "prof_bonus": pb}
                    for i, (xp, pb) in enumerate([
                        (0, 2), (300, 2), (900, 2), (2700, 2), (6500, 3),
                        (14000, 3), (23000, 3), (34000, 3), (48000, 4), (64000, 4),
                        (85000, 4), (100000, 4), (120000, 5), (140000, 5), (165000, 5),
                        (195000, 5), (225000, 6), (265000, 6), (305000, 6), (355000, 6)
                    ], start=1)
                ],
                "clases": {}
            }
    
    def calcular_nivel(self, xp: int) -> int:
        """
        Calcula el nivel correspondiente a una cantidad de XP.
        
        Args:
            xp: Puntos de experiencia acumulados
            
        Returns:
            Nivel del personaje (1-20)
        """
        nivel = 1
        for entrada in self._datos_progresion["tabla_xp"]:
            if xp >= entrada["xp_necesaria"]:
                nivel = entrada["nivel"]
            else:
                break
        return nivel
    
    def get_xp_para_nivel(self, nivel: int) -> int:
        """Obtiene la XP necesaria para alcanzar un nivel."""
        for entrada in self._datos_progresion["tabla_xp"]:
            if entrada["nivel"] == nivel:
                return entrada["xp_necesaria"]
        return 0
    
    def get_xp_siguiente_nivel(self, nivel_actual: int) -> int:
        """Obtiene la XP necesaria para el siguiente nivel."""
        if nivel_actual >= 20:
            return 0
        return self.get_xp_para_nivel(nivel_actual + 1)
    
    def get_prof_bonus(self, nivel: int) -> int:
        """Obtiene el bonificador de competencia para un nivel."""
        for entrada in self._datos_progresion["tabla_xp"]:
            if entrada["nivel"] == nivel:
                return entrada["prof_bonus"]
        return 2
    
    def get_hit_die(self, clase: str) -> int:
        """
        Obtiene el dado de golpe de una clase.
        
        Args:
            clase: Nombre de la clase en español (pícaro, guerrero, etc.)
        """
        clase_lower = clase.lower()
        
        # Mapeo de clases a hit die (por defecto)
        hit_die_default = {
            "pícaro": 8, "picaro": 8, "rogue": 8,
            "guerrero": 10, "fighter": 10,
            "mago": 6, "wizard": 6,
            "clérigo": 8, "clerigo": 8, "cleric": 8,
            "bárbaro": 12, "barbaro": 12, "barbarian": 12,
            "bardo": 8, "bard": 8,
            "druida": 8, "druid": 8,
            "monje": 8, "monk": 8,
            "paladín": 10, "paladin": 10,
            "explorador": 10, "ranger": 10,
            "hechicero": 6, "sorcerer": 6,
            "brujo": 8, "warlock": 8,
        }
        
        # Primero intentar desde datos cargados
        clases = self._datos_progresion.get("clases", {})
        if clase_lower in clases:
            return clases[clase_lower].get("hit_die", 8)
        
        # Fallback a mapeo por defecto
        return hit_die_default.get(clase_lower, 8)
    
    def otorgar_xp(self, pj: Dict[str, Any], xp: int) -> Dict[str, Any]:
        """
        Añade XP a un personaje y verifica si puede subir de nivel.
        
        Args:
            pj: Diccionario del personaje
            xp: Cantidad de XP a añadir
            
        Returns:
            Diccionario con:
                - xp_anterior: XP antes de añadir
                - xp_nueva: XP después de añadir
                - xp_ganada: XP añadida
                - puede_subir_nivel: True si alcanzó umbral de siguiente nivel
                - nivel_actual: Nivel actual
                - nivel_posible: Nivel que podría alcanzar
        """
        xp_anterior = pj.get("experiencia", 0)
        xp_nueva = xp_anterior + xp
        pj["experiencia"] = xp_nueva
        
        nivel_actual = pj.get("info_basica", {}).get("nivel", 1)
        nivel_posible = self.calcular_nivel(xp_nueva)
        
        return {
            "xp_anterior": xp_anterior,
            "xp_nueva": xp_nueva,
            "xp_ganada": xp,
            "puede_subir_nivel": nivel_posible > nivel_actual,
            "nivel_actual": nivel_actual,
            "nivel_posible": nivel_posible
        }
    
    def subir_nivel(self, pj: Dict[str, Any], nivel_objetivo: int = None) -> Dict[str, Any]:
        """
        Sube de nivel a un personaje.
        
        Args:
            pj: Diccionario del personaje
            nivel_objetivo: Nivel al que subir (default: siguiente nivel)
            
        Returns:
            Diccionario con los cambios aplicados:
                - nivel_anterior: Nivel antes de subir
                - nivel_nuevo: Nivel después de subir
                - hp_ganados: HP añadidos
                - features_nuevos: Lista de nuevas habilidades
                - mejora_caracteristica: True si puede mejorar stats
        """
        nivel_actual = pj.get("info_basica", {}).get("nivel", 1)
        nivel_nuevo = nivel_objetivo if nivel_objetivo else nivel_actual + 1
        
        if nivel_nuevo > 20:
            nivel_nuevo = 20
        if nivel_nuevo <= nivel_actual:
            return {
                "error": f"El nivel objetivo ({nivel_nuevo}) debe ser mayor que el actual ({nivel_actual})"
            }
        
        clase = pj.get("info_basica", {}).get("clase", "guerrero")
        
        cambios = {
            "nivel_anterior": nivel_actual,
            "nivel_nuevo": nivel_nuevo,
            "hp_ganados": 0,
            "features_nuevos": [],
            "mejora_caracteristica": False,
            "sneak_attack_dice": None
        }
        
        # Aplicar cada nivel intermedio
        for nivel in range(nivel_actual + 1, nivel_nuevo + 1):
            resultado = self._aplicar_nivel(pj, clase, nivel)
            cambios["hp_ganados"] += resultado.get("hp_ganados", 0)
            cambios["features_nuevos"].extend(resultado.get("features", []))
            if resultado.get("mejora_caracteristica"):
                cambios["mejora_caracteristica"] = True
            if resultado.get("sneak_attack_dice"):
                cambios["sneak_attack_dice"] = resultado["sneak_attack_dice"]
        
        return cambios
    
    def _aplicar_nivel(self, pj: Dict[str, Any], clase: str, nivel: int) -> Dict[str, Any]:
        """
        Aplica las mejoras de un solo nivel.
        
        Args:
            pj: Diccionario del personaje
            clase: Clase del personaje
            nivel: Nivel a aplicar
        """
        resultado = {
            "hp_ganados": 0,
            "features": [],
            "mejora_caracteristica": False
        }
        
        # 1. Aumentar HP
        hit_die = self.get_hit_die(clase)
        mod_con = pj.get("caracteristicas", {}).get("CON", {}).get("modificador", 0)
        # HP por nivel = (hit_die/2 + 1) + mod CON (mínimo 1)
        hp_ganado = max(1, (hit_die // 2 + 1) + mod_con)
        resultado["hp_ganados"] = hp_ganado
        
        # Actualizar HP en el personaje
        if "derivados" not in pj:
            pj["derivados"] = {}
        pj["derivados"]["puntos_golpe_maximo"] = pj["derivados"].get("puntos_golpe_maximo", 0) + hp_ganado
        pj["derivados"]["puntos_golpe_actual"] = pj["derivados"]["puntos_golpe_maximo"]
        
        # 2. Actualizar nivel
        if "info_basica" not in pj:
            pj["info_basica"] = {}
        pj["info_basica"]["nivel"] = nivel
        
        # 3. Actualizar bonificador de competencia
        pj["derivados"]["bonificador_competencia"] = self.get_prof_bonus(nivel)
        
        # 4. Obtener features de clase para este nivel
        clase_lower = clase.lower()
        clases = self._datos_progresion.get("clases", {})
        
        if clase_lower in clases:
            datos_nivel = clases[clase_lower].get("niveles", {}).get(str(nivel), {})
            
            # Features nuevos
            for feature in datos_nivel.get("features", []):
                resultado["features"].append({
                    "id": feature.get("id"),
                    "nombre": feature.get("nombre"),
                    "descripcion": feature.get("descripcion", "")
                })
            
            # Mejora de característica
            if datos_nivel.get("mejora_caracteristica"):
                resultado["mejora_caracteristica"] = True
            
            # Datos específicos de clase (ej: sneak attack dice)
            if "sneak_attack_dice" in datos_nivel:
                resultado["sneak_attack_dice"] = datos_nivel["sneak_attack_dice"]
                # Guardar en el personaje
                if "clase_especifico" not in pj:
                    pj["clase_especifico"] = {}
                pj["clase_especifico"]["sneak_attack_dice"] = datos_nivel["sneak_attack_dice"]
        
        # 5. Guardar features en el personaje
        if "features" not in pj:
            pj["features"] = []
        for f in resultado["features"]:
            if f["id"] not in [x.get("id") for x in pj["features"]]:
                pj["features"].append(f)
        
        return resultado
    
    def get_progreso_xp(self, pj: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene información sobre el progreso de XP del personaje.
        
        Returns:
            Diccionario con:
                - xp_actual: XP acumulada
                - nivel_actual: Nivel actual
                - xp_para_siguiente: XP necesaria para siguiente nivel
                - xp_faltante: XP que falta para subir
                - porcentaje: Porcentaje hacia siguiente nivel
        """
        xp_actual = pj.get("experiencia", 0)
        nivel_actual = pj.get("info_basica", {}).get("nivel", 1)
        
        if nivel_actual >= 20:
            return {
                "xp_actual": xp_actual,
                "nivel_actual": 20,
                "xp_para_siguiente": 0,
                "xp_faltante": 0,
                "porcentaje": 100
            }
        
        xp_nivel_actual = self.get_xp_para_nivel(nivel_actual)
        xp_siguiente = self.get_xp_siguiente_nivel(nivel_actual)
        xp_faltante = max(0, xp_siguiente - xp_actual)
        
        rango = xp_siguiente - xp_nivel_actual
        progreso = xp_actual - xp_nivel_actual
        porcentaje = int((progreso / rango) * 100) if rango > 0 else 100
        
        return {
            "xp_actual": xp_actual,
            "nivel_actual": nivel_actual,
            "xp_para_siguiente": xp_siguiente,
            "xp_faltante": xp_faltante,
            "porcentaje": min(100, max(0, porcentaje))
        }


# Instancia global para uso fácil
_gestor_progresion = None

def obtener_gestor_progresion() -> GestorProgresion:
    """Obtiene la instancia global del gestor de progresión."""
    global _gestor_progresion
    if _gestor_progresion is None:
        _gestor_progresion = GestorProgresion()
    return _gestor_progresion
