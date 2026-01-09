"""
Herramientas para modificar el estado del juego: HP, inventario, tiempo.
"""

from typing import Any, Dict
from .herramienta_base import Herramienta
from .registro import registrar_herramienta


class ModificarHP(Herramienta):
    """Modifica los puntos de golpe del personaje."""
    
    @property
    def nombre(self) -> str:
        return "modificar_hp"
    
    @property
    def descripcion(self) -> str:
        return "Añade o quita puntos de golpe al personaje (daño negativo, curación positivo)."
    
    @property
    def parametros(self) -> Dict[str, Dict[str, Any]]:
        return {
            "cantidad": {
                "tipo": "int",
                "descripcion": "Cantidad a modificar (positivo=curar, negativo=dañar)",
                "requerido": True
            },
            "motivo": {
                "tipo": "string",
                "descripcion": "Razón del cambio (para el log)",
                "requerido": False
            }
        }
    
    def ejecutar(self, contexto: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        pj = contexto.get("pj")
        if not pj:
            return {"exito": False, "error": "No hay personaje cargado"}
        
        cantidad = int(kwargs["cantidad"])
        motivo = kwargs.get("motivo", "")
        
        derivados = pj.get("derivados", {})
        hp_actual = derivados.get("puntos_golpe_actual", 0)
        hp_max = derivados.get("puntos_golpe_maximo", 1)
        
        nuevo_hp = max(0, min(hp_max, hp_actual + cantidad))
        derivados["puntos_golpe_actual"] = nuevo_hp
        
        # Determinar estado
        if nuevo_hp == 0:
            estado = "inconsciente"
        elif nuevo_hp <= hp_max // 4:
            estado = "gravemente herido"
        elif nuevo_hp <= hp_max // 2:
            estado = "herido"
        else:
            estado = "sano"
        
        return {
            "exito": True,
            "hp_anterior": hp_actual,
            "hp_nuevo": nuevo_hp,
            "hp_maximo": hp_max,
            "cambio": cantidad,
            "motivo": motivo,
            "estado": estado
        }


class DarObjeto(Herramienta):
    """Añade un objeto al inventario del personaje."""
    
    @property
    def nombre(self) -> str:
        return "dar_objeto"
    
    @property
    def descripcion(self) -> str:
        return "Añade un objeto al inventario del personaje."
    
    @property
    def parametros(self) -> Dict[str, Dict[str, Any]]:
        return {
            "id_objeto": {
                "tipo": "string",
                "descripcion": "ID del objeto a dar",
                "requerido": True
            },
            "cantidad": {
                "tipo": "int",
                "descripcion": "Cantidad (por defecto 1)",
                "requerido": False
            }
        }
    
    def ejecutar(self, contexto: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        from motor.compendio import obtener_arma, obtener_armadura, obtener_objeto_misc
        
        pj = contexto.get("pj")
        if not pj:
            return {"exito": False, "error": "No hay personaje cargado"}
        
        id_objeto = kwargs["id_objeto"]
        cantidad = int(kwargs.get("cantidad", 1))
        
        # Buscar objeto en compendio
        objeto = obtener_arma(id_objeto) or obtener_armadura(id_objeto) or obtener_objeto_misc(id_objeto)
        
        if not objeto:
            return {"exito": False, "error": f"Objeto '{id_objeto}' no encontrado en compendio"}
        
        # Añadir al inventario
        equipo = pj.setdefault("equipo", {})
        objetos = equipo.setdefault("objetos", [])
        
        # Verificar si ya existe
        for obj in objetos:
            if obj.get("id") == id_objeto:
                obj["cantidad"] = obj.get("cantidad", 1) + cantidad
                return {
                    "exito": True,
                    "objeto": objeto.get("nombre", id_objeto),
                    "cantidad_total": obj["cantidad"],
                    "mensaje": f"Añadido {cantidad}x {objeto.get('nombre', id_objeto)} (total: {obj['cantidad']})"
                }
        
        # Nuevo objeto
        nuevo = {
            "id": id_objeto,
            "nombre": objeto.get("nombre", id_objeto),
            "cantidad": cantidad
        }
        objetos.append(nuevo)
        
        return {
            "exito": True,
            "objeto": objeto.get("nombre", id_objeto),
            "cantidad_total": cantidad,
            "mensaje": f"Obtenido: {cantidad}x {objeto.get('nombre', id_objeto)}"
        }


class QuitarObjeto(Herramienta):
    """Quita un objeto del inventario."""
    
    @property
    def nombre(self) -> str:
        return "quitar_objeto"
    
    @property
    def descripcion(self) -> str:
        return "Quita un objeto del inventario del personaje."
    
    @property
    def parametros(self) -> Dict[str, Dict[str, Any]]:
        return {
            "id_objeto": {
                "tipo": "string",
                "descripcion": "ID del objeto a quitar",
                "requerido": True
            },
            "cantidad": {
                "tipo": "int",
                "descripcion": "Cantidad a quitar (por defecto 1)",
                "requerido": False
            }
        }
    
    def ejecutar(self, contexto: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        pj = contexto.get("pj")
        if not pj:
            return {"exito": False, "error": "No hay personaje cargado"}
        
        id_objeto = kwargs["id_objeto"]
        cantidad = int(kwargs.get("cantidad", 1))
        
        equipo = pj.get("equipo", {})
        objetos = equipo.get("objetos", [])
        
        for i, obj in enumerate(objetos):
            if obj.get("id") == id_objeto:
                actual = obj.get("cantidad", 1)
                if actual <= cantidad:
                    objetos.pop(i)
                    return {
                        "exito": True,
                        "objeto": obj.get("nombre", id_objeto),
                        "cantidad_quitada": actual,
                        "restante": 0,
                        "mensaje": f"Eliminado: {obj.get('nombre', id_objeto)}"
                    }
                else:
                    obj["cantidad"] = actual - cantidad
                    return {
                        "exito": True,
                        "objeto": obj.get("nombre", id_objeto),
                        "cantidad_quitada": cantidad,
                        "restante": obj["cantidad"],
                        "mensaje": f"Usado {cantidad}x {obj.get('nombre', id_objeto)} (quedan: {obj['cantidad']})"
                    }
        
        return {"exito": False, "error": f"No tienes '{id_objeto}' en el inventario"}


# Registrar
registrar_herramienta(ModificarHP())
registrar_herramienta(DarObjeto())
registrar_herramienta(QuitarObjeto())


class ModificarOro(Herramienta):
    """Modifica el oro del personaje."""
    
    @property
    def nombre(self) -> str:
        return "modificar_oro"
    
    @property
    def descripcion(self) -> str:
        return "Añade o quita oro al personaje (positivo=ganar, negativo=gastar)."
    
    @property
    def parametros(self) -> Dict[str, Dict[str, Any]]:
        return {
            "cantidad": {
                "tipo": "int",
                "descripcion": "Cantidad de oro (positivo=ganar, negativo=gastar)",
                "requerido": True
            },
            "motivo": {
                "tipo": "string",
                "descripcion": "Razón del cambio (trabajo, compra, recompensa, etc.)",
                "requerido": False
            }
        }
    
    def ejecutar(self, contexto: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        pj = contexto.get("pj")
        if not pj:
            return {"exito": False, "error": "No hay personaje cargado"}
        
        cantidad = int(kwargs["cantidad"])
        motivo = kwargs.get("motivo", "")
        
        equipo = pj.setdefault("equipo", {})
        oro_actual = equipo.get("oro", 0)
        
        nuevo_oro = oro_actual + cantidad
        
        if nuevo_oro < 0:
            return {
                "exito": False,
                "error": f"No tienes suficiente oro. Tienes {oro_actual} po, necesitas {abs(cantidad)} po."
            }
        
        equipo["oro"] = nuevo_oro
        
        return {
            "exito": True,
            "oro_anterior": oro_actual,
            "cambio": cantidad,
            "oro_actual": nuevo_oro,
            "motivo": motivo,
            "mensaje": f"{'Ganaste' if cantidad > 0 else 'Gastaste'} {abs(cantidad)} po. Total: {nuevo_oro} po"
        }


# Registrar
registrar_herramienta(ModificarOro())
