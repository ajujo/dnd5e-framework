"""
Herramientas de combate: iniciar encuentros, gestionar turnos.

IMPORTANTE: Solo se pueden usar monstruos que existan en el compendio.
"""

from typing import Any, Dict, List
from .herramienta_base import Herramienta
from .registro import registrar_herramienta


class IniciarCombate(Herramienta):
    """Inicia un encuentro de combate con enemigos del compendio."""
    
    @property
    def nombre(self) -> str:
        return "iniciar_combate"
    
    @property
    def descripcion(self) -> str:
        return "Inicia un combate. SOLO puede usar monstruos que existan en el compendio (consulta primero con consultar_monstruo)."
    
    @property
    def parametros(self) -> Dict[str, Dict[str, Any]]:
        return {
            "enemigos": {
                "tipo": "list",
                "descripcion": "Lista de IDs de monstruos del compendio (ej: ['goblin', 'goblin', 'lobo'])",
                "requerido": True
            },
            "sorpresa": {
                "tipo": "string",
                "descripcion": "Quién tiene sorpresa",
                "requerido": False,
                "opciones": ["ninguno", "jugador", "enemigos"]
            }
        }
    
    def ejecutar(self, contexto: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        from motor.compendio import obtener_monstruo, listar_monstruos
        from motor.dados import tirar
        
        enemigos_ids = kwargs.get("enemigos", [])
        sorpresa = kwargs.get("sorpresa", "ninguno")
        
        if not enemigos_ids:
            return {"exito": False, "error": "No se especificaron enemigos"}
        
        # Validar que todos los monstruos existen en el compendio
        combatientes_enemigos = []
        monstruos_no_encontrados = []
        monstruos_disponibles = [m.get("id") for m in listar_monstruos()]
        
        for i, enemigo_id in enumerate(enemigos_ids):
            monstruo = obtener_monstruo(enemigo_id)
            
            if not monstruo:
                monstruos_no_encontrados.append(enemigo_id)
                continue
            
            # Crear instancia única del monstruo
            combatiente = {
                "id": f"{enemigo_id}_{i+1}",
                "nombre": monstruo.get("nombre", enemigo_id),
                "tipo": "enemigo",
                "hp": monstruo.get("puntos_golpe", 10),
                "hp_max": monstruo.get("puntos_golpe", 10),
                "ca": monstruo.get("clase_armadura", 10),
                "iniciativa": 0,
                "datos_monstruo": monstruo,
                "estado": "activo"
            }
            
            # Tirar iniciativa
            mod_des = 0
            if monstruo.get("caracteristicas"):
                des = monstruo["caracteristicas"].get("destreza", 10)
                mod_des = (des - 10) // 2
            combatiente["iniciativa"] = tirar("1d20").total + mod_des
            
            combatientes_enemigos.append(combatiente)
        
        # Si hubo monstruos no encontrados, avisar
        if monstruos_no_encontrados:
            return {
                "exito": False,
                "error": f"Monstruos no encontrados en compendio: {monstruos_no_encontrados}",
                "monstruos_disponibles": monstruos_disponibles,
                "mensaje": "Solo puedes usar monstruos del compendio. Usa 'consultar_monstruo' para ver los disponibles."
            }
        
        # Tirar iniciativa del PJ
        pj = contexto.get("pj")
        iniciativa_pj = 0
        if pj:
            derivados = pj.get("derivados", {})
            mod_ini = derivados.get("iniciativa", 0)
            iniciativa_pj = tirar("1d20").total + mod_ini
        
        combatiente_pj = {
            "id": "pj",
            "nombre": pj.get("info_basica", {}).get("nombre", "Aventurero") if pj else "Aventurero",
            "tipo": "jugador",
            "iniciativa": iniciativa_pj,
            "estado": "activo"
        }
        
        # Ordenar por iniciativa
        todos_combatientes = [combatiente_pj] + combatientes_enemigos
        todos_combatientes.sort(key=lambda x: x["iniciativa"], reverse=True)
        
        # Aplicar sorpresa
        rondas_sorpresa = 0
        if sorpresa == "jugador":
            rondas_sorpresa = 1
            for c in combatientes_enemigos:
                c["sorprendido"] = True
        elif sorpresa == "enemigos":
            rondas_sorpresa = 1
            combatiente_pj["sorprendido"] = True
        
        # Construir estado de combate
        estado_combate = {
            "activo": True,
            "ronda": 1,
            "turno_idx": 0,
            "orden": [c["id"] for c in todos_combatientes],
            "combatientes": {c["id"]: c for c in todos_combatientes},
            "sorpresa": sorpresa,
            "log": []
        }
        
        # Determinar quién actúa primero
        primer_turno = todos_combatientes[0]
        
        return {
            "exito": True,
            "mensaje": "¡Combate iniciado!",
            "combatientes": [
                {"nombre": c["nombre"], "iniciativa": c["iniciativa"], "hp": c.get("hp", "?")}
                for c in todos_combatientes
            ],
            "orden_iniciativa": [c["nombre"] for c in todos_combatientes],
            "primer_turno": primer_turno["nombre"],
            "sorpresa": sorpresa,
            "estado_combate": estado_combate
        }


class ListarMonstruosDisponibles(Herramienta):
    """Lista los monstruos disponibles en el compendio."""
    
    @property
    def nombre(self) -> str:
        return "listar_monstruos"
    
    @property
    def descripcion(self) -> str:
        return "Lista todos los monstruos disponibles en el compendio para usar en combates."
    
    @property
    def parametros(self) -> Dict[str, Dict[str, Any]]:
        return {}
    
    def ejecutar(self, contexto: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        from motor.compendio import listar_monstruos
        
        monstruos = listar_monstruos()
        
        lista = []
        for m in monstruos:
            lista.append({
                "id": m.get("id"),
                "nombre": m.get("nombre"),
                "tipo": m.get("tipo"),
                "desafio": m.get("desafio"),
                "hp": m.get("puntos_golpe"),
                "ca": m.get("clase_armadura")
            })
        
        return {
            "exito": True,
            "cantidad": len(lista),
            "monstruos": lista
        }


class AplicarDañoNPC(Herramienta):
    """Aplica daño a un NPC/enemigo en combate."""
    
    @property
    def nombre(self) -> str:
        return "dañar_enemigo"
    
    @property
    def descripcion(self) -> str:
        return "Aplica daño a un enemigo en combate."
    
    @property
    def parametros(self) -> Dict[str, Dict[str, Any]]:
        return {
            "id_enemigo": {
                "tipo": "string",
                "descripcion": "ID del enemigo (ej: 'goblin_1')",
                "requerido": True
            },
            "daño": {
                "tipo": "int",
                "descripcion": "Cantidad de daño a aplicar",
                "requerido": True
            }
        }
    
    def ejecutar(self, contexto: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        combate = contexto.get("combate")
        if not combate or not combate.get("activo"):
            return {"exito": False, "error": "No hay combate activo"}
        
        id_enemigo = kwargs["id_enemigo"]
        daño = int(kwargs["daño"])
        
        combatientes = combate.get("combatientes", {})
        enemigo = combatientes.get(id_enemigo)
        
        if not enemigo:
            return {
                "exito": False,
                "error": f"Enemigo '{id_enemigo}' no encontrado",
                "enemigos_disponibles": [k for k, v in combatientes.items() if v.get("tipo") == "enemigo"]
            }
        
        hp_anterior = enemigo.get("hp", 0)
        hp_nuevo = max(0, hp_anterior - daño)
        enemigo["hp"] = hp_nuevo
        
        derrotado = hp_nuevo <= 0
        if derrotado:
            enemigo["estado"] = "derrotado"
        
        # Verificar si todos los enemigos están derrotados
        enemigos_vivos = [c for c in combatientes.values() 
                        if c.get("tipo") == "enemigo" and c.get("hp", 0) > 0]
        combate_terminado = len(enemigos_vivos) == 0
        
        if combate_terminado:
            combate["activo"] = False
        
        return {
            "exito": True,
            "enemigo": enemigo["nombre"],
            "daño_recibido": daño,
            "hp_anterior": hp_anterior,
            "hp_actual": hp_nuevo,
            "derrotado": derrotado,
            "combate_terminado": combate_terminado,
            "enemigos_restantes": len(enemigos_vivos)
        }


# Registrar herramientas
registrar_herramienta(IniciarCombate())
registrar_herramienta(ListarMonstruosDisponibles())
registrar_herramienta(AplicarDañoNPC())
