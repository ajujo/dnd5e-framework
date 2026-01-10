"""
Herramientas de combate: iniciar encuentros, gestionar turnos.

INTEGRACIÓN CON GESTOR DE COMBATE TÁCTICO:
- iniciar_combate → crea GestorCombate real
- Los enemigos se cargan desde CompendioMotor
- El motor controla turnos e iniciativa
"""

from typing import Any, Dict, List
from .herramienta_base import Herramienta
from .registro import registrar_herramienta


class IniciarCombate(Herramienta):
    """Inicia un encuentro de combate táctico con GestorCombate."""
    
    @property
    def nombre(self) -> str:
        return "iniciar_combate"
    
    @property
    def descripcion(self) -> str:
        return "Inicia un combate táctico. SOLO puede usar monstruos que existan en el compendio."
    
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
        from motor import (
            GestorCombate, Combatiente, TipoCombatiente, 
            CompendioMotor, PipelineTurno
        )
        
        enemigos_ids = kwargs.get("enemigos", [])
        sorpresa = kwargs.get("sorpresa", "ninguno")
        
        if not enemigos_ids:
            return {"exito": False, "error": "No se especificaron enemigos"}
        
        # Crear CompendioMotor
        compendio = CompendioMotor()
        
        # Verificar que los monstruos existen
        monstruos_disponibles = [m.get("id") for m in compendio.listar_monstruos()]
        monstruos_no_encontrados = [e for e in enemigos_ids if e not in monstruos_disponibles]
        
        if monstruos_no_encontrados:
            return {
                "exito": False,
                "error": f"Monstruos no encontrados en compendio: {monstruos_no_encontrados}",
                "monstruos_disponibles": monstruos_disponibles,
                "mensaje": "Solo puedes usar monstruos del compendio. Usa 'listar_monstruos' para ver los disponibles."
            }
        
        # Crear GestorCombate con pipeline
        pipeline = PipelineTurno(compendio)
        gestor = GestorCombate(compendio=compendio, pipeline=pipeline)
        
        # Agregar PJ como combatiente
        pj = contexto.get("pj")
        if pj:
            info = pj.get("info_basica", {})
            derivados = pj.get("derivados", {})
            caracteristicas = pj.get("caracteristicas", {})
            equipo = pj.get("equipo", {})
            
            # Obtener arma equipada
            arma_principal = None
            for arma in equipo.get("armas", []):
                if arma.get("equipada"):
                    arma_id = arma.get("id", "arma")
                    # Extraer el ID base del compendio (quitar sufijo _N si existe)
                    # espada_larga_1 -> espada_larga
                    compendio_ref = arma_id
                    if "_" in arma_id:
                        partes = arma_id.rsplit("_", 1)
                        if len(partes) == 2 and partes[1].isdigit():
                            compendio_ref = partes[0]
                    
                    arma_principal = {
                        "id": arma_id,
                        "nombre": arma.get("nombre", "Arma"),
                        "compendio_ref": compendio_ref,
                    }
                    break
            
            combatiente_pj = Combatiente(
                id="pj",
                nombre=info.get("nombre", "Aventurero"),
                tipo=TipoCombatiente.PC,
                hp_maximo=derivados.get("puntos_golpe_maximo", 10),
                hp_actual=derivados.get("puntos_golpe_actual", 10),
                clase_armadura=derivados.get("clase_armadura", 10),
                velocidad=derivados.get("velocidad", 30),
                fuerza=caracteristicas.get("fuerza", 10),
                destreza=caracteristicas.get("destreza", 10),
                constitucion=caracteristicas.get("constitucion", 10),
                inteligencia=caracteristicas.get("inteligencia", 10),
                sabiduria=caracteristicas.get("sabiduria", 10),
                carisma=caracteristicas.get("carisma", 10),
                arma_principal=arma_principal,
            )
            gestor.agregar_combatiente(combatiente_pj)
        
        # Agregar enemigos desde compendio
        for i, enemigo_id in enumerate(enemigos_ids):
            try:
                gestor.agregar_desde_compendio(
                    monstruo_id=enemigo_id,
                    instancia_id=f"{enemigo_id}_{i+1}",
                    tipo=TipoCombatiente.NPC_ENEMIGO
                )
            except ValueError as e:
                return {"exito": False, "error": str(e)}
        
        # Iniciar combate (tira iniciativas y ordena)
        gestor.iniciar_combate(tirar_iniciativa=True)
        
        # Aplicar sorpresa
        if sorpresa == "jugador":
            for c in gestor.listar_combatientes():
                if c.tipo == TipoCombatiente.NPC_ENEMIGO:
                    c.sorprendido = True
        elif sorpresa == "enemigos":
            pj_combatiente = gestor.obtener_combatiente("pj")
            if pj_combatiente:
                pj_combatiente.sorprendido = True
        
        # Obtener info para respuesta
        turno_actual = gestor.obtener_turno_actual()
        
        combatientes_info = []
        for c in gestor.listar_combatientes():
            combatientes_info.append({
                "id": c.id,
                "nombre": c.nombre,
                "tipo": c.tipo.value,
                "iniciativa": c.iniciativa,
                "hp": c.hp_actual,
                "hp_max": c.hp_maximo,
                "ca": c.clase_armadura,
            })
        
        return {
            "exito": True,
            "mensaje": "¡Combate táctico iniciado!",
            "combatientes": combatientes_info,
            "orden_iniciativa": [c.nombre for c in gestor.listar_combatientes()],
            "primer_turno": turno_actual.nombre if turno_actual else "?",
            "sorpresa": sorpresa,
            # Crítico: devolver el gestor para que DMCerebro lo guarde
            "gestor_combate": gestor,
            "modo_tactico": True,
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
        from motor import CompendioMotor
        
        compendio = CompendioMotor()
        monstruos = compendio.listar_monstruos()
        
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
    """Aplica daño a un NPC/enemigo en combate (LEGACY - para compatibilidad)."""
    
    @property
    def nombre(self) -> str:
        return "dañar_enemigo"
    
    @property
    def descripcion(self) -> str:
        return "Aplica daño a un enemigo. NOTA: En modo táctico, usar el pipeline de combate."
    
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
        # Verificar si hay gestor táctico
        gestor = contexto.get("gestor_combate")
        
        if gestor:
            # Modo táctico: delegar al gestor
            id_enemigo = kwargs["id_enemigo"]
            daño = int(kwargs["daño"])
            
            enemigo = gestor.obtener_combatiente(id_enemigo)
            if not enemigo:
                ids_disponibles = [c.id for c in gestor.listar_combatientes() 
                                   if c.tipo.value == "enemigo"]
                return {
                    "exito": False,
                    "error": f"Enemigo '{id_enemigo}' no encontrado",
                    "enemigos_disponibles": ids_disponibles
                }
            
            hp_anterior = enemigo.hp_actual
            enemigo.hp_actual = max(0, enemigo.hp_actual - daño)
            
            derrotado = enemigo.hp_actual <= 0
            if derrotado:
                enemigo.muerto = True
            
            # Verificar si combate terminó
            combate_terminado = gestor.estado == gestor.estado.VICTORIA
            
            return {
                "exito": True,
                "enemigo": enemigo.nombre,
                "daño_recibido": daño,
                "hp_anterior": hp_anterior,
                "hp_actual": enemigo.hp_actual,
                "derrotado": derrotado,
                "combate_terminado": combate_terminado,
            }
        
        # Fallback: modo legacy (dict básico)
        combate = contexto.get("combate") or contexto.get("estado_combate")
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
