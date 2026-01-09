"""
Herramientas de consulta: ficha del PJ, monstruos, objetos.
"""

from typing import Any, Dict
from .herramienta_base import Herramienta
from .registro import registrar_herramienta


class ConsultarFicha(Herramienta):
    """Consulta información de la ficha del personaje."""
    
    @property
    def nombre(self) -> str:
        return "consultar_ficha"
    
    @property
    def descripcion(self) -> str:
        return "Consulta datos del personaje jugador: características, habilidades, HP, equipo, etc."
    
    @property
    def parametros(self) -> Dict[str, Dict[str, Any]]:
        return {
            "campo": {
                "tipo": "string",
                "descripcion": "Qué consultar: 'todo', 'caracteristicas', 'habilidades', 'combate', 'equipo', 'hp'",
                "requerido": False,
                "opciones": ["todo", "caracteristicas", "habilidades", "combate", "equipo", "hp", "competencias"]
            }
        }
    
    def ejecutar(self, contexto: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        pj = contexto.get("pj")
        if not pj:
            return {"exito": False, "error": "No hay personaje cargado"}
        
        campo = kwargs.get("campo", "todo")
        
        if campo == "todo":
            return {"exito": True, "datos": self._resumen_completo(pj)}
        elif campo == "caracteristicas":
            return {"exito": True, "datos": pj.get("caracteristicas", {})}
        elif campo == "habilidades":
            return {"exito": True, "datos": pj.get("competencias", {}).get("habilidades", [])}
        elif campo == "combate":
            return {"exito": True, "datos": self._datos_combate(pj)}
        elif campo == "equipo":
            return {"exito": True, "datos": pj.get("equipo", {})}
        elif campo == "hp":
            derivados = pj.get("derivados", {})
            return {
                "exito": True,
                "datos": {
                    "actual": derivados.get("puntos_golpe_actual", 0),
                    "maximo": derivados.get("puntos_golpe_maximo", 0)
                }
            }
        elif campo == "competencias":
            return {"exito": True, "datos": pj.get("competencias", {})}
        
        return {"exito": False, "error": f"Campo '{campo}' no reconocido"}
    
    def _resumen_completo(self, pj: dict) -> dict:
        """Genera un resumen legible del PJ."""
        info = pj.get("info_basica", {})
        derivados = pj.get("derivados", {})
        mods = derivados.get("modificadores", {})
        
        return {
            "nombre": info.get("nombre", "Sin nombre"),
            "raza": info.get("raza", ""),
            "clase": info.get("clase", ""),
            "nivel": info.get("nivel", 1),
            "hp": f"{derivados.get('puntos_golpe_actual', 0)}/{derivados.get('puntos_golpe_maximo', 0)}",
            "ca": derivados.get("clase_armadura", 10),
            "caracteristicas": {k: f"{v} ({mods.get(k, 0):+d})" for k, v in pj.get("caracteristicas", {}).items()},
            "habilidades_competentes": pj.get("competencias", {}).get("habilidades", []),
            "arma_equipada": self._obtener_arma_equipada(pj)
        }
    
    def _datos_combate(self, pj: dict) -> dict:
        """Datos relevantes para combate."""
        derivados = pj.get("derivados", {})
        mods = derivados.get("modificadores", {})
        bon_comp = derivados.get("bonificador_competencia", 2)
        
        return {
            "hp_actual": derivados.get("puntos_golpe_actual", 0),
            "hp_max": derivados.get("puntos_golpe_maximo", 0),
            "ca": derivados.get("clase_armadura", 10),
            "iniciativa": derivados.get("iniciativa", 0),
            "velocidad": derivados.get("velocidad", 30),
            "ataque_cac": mods.get("fuerza", 0) + bon_comp,
            "ataque_distancia": mods.get("destreza", 0) + bon_comp,
            "bonificador_competencia": bon_comp
        }
    
    def _obtener_arma_equipada(self, pj: dict) -> str:
        equipo = pj.get("equipo", {})
        armas = equipo.get("armas", [])
        for arma in armas:
            if arma.get("equipada"):
                return arma.get("nombre", "Arma")
        return "Desarmado"


class ConsultarMonstruo(Herramienta):
    """Consulta información de un monstruo del compendio."""
    
    @property
    def nombre(self) -> str:
        return "consultar_monstruo"
    
    @property
    def descripcion(self) -> str:
        return "Obtiene las estadísticas de un monstruo por su ID o nombre."
    
    @property
    def parametros(self) -> Dict[str, Dict[str, Any]]:
        return {
            "id_monstruo": {
                "tipo": "string",
                "descripcion": "ID del monstruo (ej: 'goblin', 'orco', 'lobo')",
                "requerido": True
            }
        }
    
    def ejecutar(self, contexto: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        from motor.compendio import obtener_compendio_motor
        
        compendio = obtener_compendio_motor()
        
        id_monstruo = kwargs.get("id_monstruo", "").lower().replace(" ", "_")
        
        monstruo = compendio.obtener_monstruo(id_monstruo)
        
        if not monstruo:
            disponibles = compendio.listar_monstruos()
            return {
                "exito": False,
                "error": f"Monstruo '{id_monstruo}' no encontrado",
                "monstruos_disponibles": [m.get("id") for m in disponibles]
            }
        
        return {
            "exito": True,
            "datos": {
                "id": monstruo.get("id"),
                "nombre": monstruo.get("nombre"),
                "tipo": monstruo.get("tipo"),
                "hp": monstruo.get("puntos_golpe"),
                "ca": monstruo.get("clase_armadura"),
                "velocidad": monstruo.get("velocidad"),
                "caracteristicas": monstruo.get("caracteristicas"),
                "ataques": monstruo.get("ataques", []),
                "desafio": monstruo.get("desafio")
            }
        }


class ConsultarObjeto(Herramienta):
    """Consulta información de un objeto del compendio."""
    
    @property
    def nombre(self) -> str:
        return "consultar_objeto"
    
    @property
    def descripcion(self) -> str:
        return "Obtiene información de un objeto (arma, armadura, objeto misc) del compendio."
    
    @property
    def parametros(self) -> Dict[str, Dict[str, Any]]:
        return {
            "id_objeto": {
                "tipo": "string",
                "descripcion": "ID del objeto (ej: 'espada_larga', 'pocion_curacion')",
                "requerido": True
            },
            "tipo": {
                "tipo": "string",
                "descripcion": "Tipo de objeto a buscar",
                "requerido": False,
                "opciones": ["arma", "armadura", "misc", "auto"]
            }
        }
    
    def ejecutar(self, contexto: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        from motor.compendio import obtener_compendio_motor
        
        compendio = obtener_compendio_motor()
        
        id_objeto = kwargs.get("id_objeto", "").lower().replace(" ", "_")
        tipo = kwargs.get("tipo", "auto")
        
        objeto = None
        tipo_encontrado = None
        
        if tipo in ("auto", "arma"):
            objeto = compendio.obtener_arma(id_objeto)
            if objeto:
                tipo_encontrado = "arma"
        
        if not objeto and tipo in ("auto", "armadura"):
            objeto = compendio.obtener_armadura(id_objeto)
            if objeto:
                tipo_encontrado = "armadura"
        
        if not objeto and tipo in ("auto", "misc"):
            objeto = compendio.obtener_objeto_misc(id_objeto)
            if objeto:
                tipo_encontrado = "misc"
        
        if not objeto:
            return {
                "exito": False,
                "error": f"Objeto '{id_objeto}' no encontrado"
            }
        
        return {
            "exito": True,
            "tipo": tipo_encontrado,
            "datos": objeto
        }


# Registrar herramientas al importar el módulo
registrar_herramienta(ConsultarFicha())
registrar_herramienta(ConsultarMonstruo())
registrar_herramienta(ConsultarObjeto())
