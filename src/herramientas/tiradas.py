"""
Herramientas de tiradas: habilidades, salvaciones, ataques.
"""

from typing import Any, Dict
from .herramienta_base import Herramienta
from .registro import registrar_herramienta


# Mapeo de habilidades a características
HABILIDAD_A_CARACTERISTICA = {
    "acrobacias": "destreza",
    "arcano": "inteligencia",
    "atletismo": "fuerza",
    "engano": "carisma",
    "historia": "inteligencia",
    "interpretacion": "carisma",
    "intimidacion": "carisma",
    "investigacion": "inteligencia",
    "juego_manos": "destreza",
    "medicina": "sabiduria",
    "naturaleza": "inteligencia",
    "percepcion": "sabiduria",
    "perspicacia": "sabiduria",
    "persuasion": "carisma",
    "religion": "inteligencia",
    "sigilo": "destreza",
    "supervivencia": "sabiduria",
    "trato_animales": "sabiduria",
    # Alternativas con nombres distintos
    "averiguar_intenciones": "sabiduria",
}


class TirarHabilidad(Herramienta):
    """Realiza una tirada de habilidad."""
    
    @property
    def nombre(self) -> str:
        return "tirar_habilidad"
    
    @property
    def descripcion(self) -> str:
        return "Realiza una tirada de habilidad (1d20 + modificador) contra una CD."
    
    @property
    def parametros(self) -> Dict[str, Dict[str, Any]]:
        return {
            "habilidad": {
                "tipo": "string",
                "descripcion": "Nombre de la habilidad (ej: 'persuasion', 'atletismo', 'sigilo')",
                "requerido": True
            },
            "cd": {
                "tipo": "int",
                "descripcion": "Clase de Dificultad (5=muy fácil, 10=fácil, 15=media, 20=difícil, 25=muy difícil)",
                "requerido": True
            },
            "ventaja": {
                "tipo": "bool",
                "descripcion": "Si tiene ventaja en la tirada",
                "requerido": False
            },
            "desventaja": {
                "tipo": "bool",
                "descripcion": "Si tiene desventaja en la tirada",
                "requerido": False
            }
        }
    
    def ejecutar(self, contexto: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        from motor.dados import tirar
        
        pj = contexto.get("pj")
        if not pj:
            return {"exito": False, "error": "No hay personaje cargado"}
        
        habilidad = kwargs["habilidad"].lower().replace(" ", "_")
        cd = int(kwargs["cd"])
        ventaja = kwargs.get("ventaja", False)
        desventaja = kwargs.get("desventaja", False)
        
        # Obtener característica asociada
        caracteristica = HABILIDAD_A_CARACTERISTICA.get(habilidad)
        if not caracteristica:
            return {
                "exito": False,
                "error": f"Habilidad '{habilidad}' no reconocida",
                "habilidades_validas": list(HABILIDAD_A_CARACTERISTICA.keys())
            }
        
        # Calcular modificador
        derivados = pj.get("derivados", {})
        mods = derivados.get("modificadores", {})
        mod_car = mods.get(caracteristica, 0)
        
        # ¿Competente en la habilidad?
        habilidades_competentes = pj.get("competencias", {}).get("habilidades", [])
        es_competente = habilidad in habilidades_competentes
        
        bon_comp = derivados.get("bonificador_competencia", 2) if es_competente else 0
        modificador_total = mod_car + bon_comp
        
        # Tirar dados
        if ventaja and not desventaja:
            tirada1 = tirar("1d20")
            tirada2 = tirar("1d20")
            tirada_usada = max(tirada1.total, tirada2.total)
            tipo_tirada = "ventaja"
            detalle_tirada = f"({tirada1.total}, {tirada2.total}) → {tirada_usada}"
        elif desventaja and not ventaja:
            tirada1 = tirar("1d20")
            tirada2 = tirar("1d20")
            tirada_usada = min(tirada1.total, tirada2.total)
            tipo_tirada = "desventaja"
            detalle_tirada = f"({tirada1.total}, {tirada2.total}) → {tirada_usada}"
        else:
            tirada = tirar("1d20")
            tirada_usada = tirada.total
            tipo_tirada = "normal"
            detalle_tirada = str(tirada_usada)
        
        total = tirada_usada + modificador_total
        exito = total >= cd
        
        # Crítico natural
        critico = tirada_usada == 20
        pifia = tirada_usada == 1
        
        return {
            "exito": exito,
            "tirada": tirada_usada,
            "modificador": modificador_total,
            "total": total,
            "cd": cd,
            "margen": total - cd,
            "tipo_tirada": tipo_tirada,
            "detalle": detalle_tirada,
            "competente": es_competente,
            "critico_natural": critico,
            "pifia_natural": pifia,
            "desglose": f"{detalle_tirada} + {mod_car} ({caracteristica[:3].upper()}) + {bon_comp} (comp) = {total} vs CD {cd}"
        }


class TirarSalvacion(Herramienta):
    """Realiza una tirada de salvación."""
    
    @property
    def nombre(self) -> str:
        return "tirar_salvacion"
    
    @property
    def descripcion(self) -> str:
        return "Realiza una tirada de salvación contra una CD."
    
    @property
    def parametros(self) -> Dict[str, Dict[str, Any]]:
        return {
            "caracteristica": {
                "tipo": "string",
                "descripcion": "Característica de la salvación",
                "requerido": True,
                "opciones": ["fuerza", "destreza", "constitucion", "inteligencia", "sabiduria", "carisma"]
            },
            "cd": {
                "tipo": "int",
                "descripcion": "Clase de Dificultad",
                "requerido": True
            },
            "ventaja": {
                "tipo": "bool",
                "descripcion": "Si tiene ventaja",
                "requerido": False
            },
            "desventaja": {
                "tipo": "bool",
                "descripcion": "Si tiene desventaja",
                "requerido": False
            }
        }
    
    def ejecutar(self, contexto: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        from motor.dados import tirar
        
        pj = contexto.get("pj")
        if not pj:
            return {"exito": False, "error": "No hay personaje cargado"}
        
        caracteristica = kwargs["caracteristica"].lower()
        cd = int(kwargs["cd"])
        ventaja = kwargs.get("ventaja", False)
        desventaja = kwargs.get("desventaja", False)
        
        # Obtener modificador de salvación
        derivados = pj.get("derivados", {})
        salvaciones = derivados.get("salvaciones", {})
        mod_salvacion = salvaciones.get(caracteristica, 0)
        
        # ¿Competente?
        salvaciones_competentes = pj.get("competencias", {}).get("salvaciones", [])
        es_competente = caracteristica in salvaciones_competentes
        
        # Tirar
        if ventaja and not desventaja:
            t1, t2 = tirar("1d20").total, tirar("1d20").total
            tirada = max(t1, t2)
            detalle = f"ventaja ({t1}, {t2}) → {tirada}"
        elif desventaja and not ventaja:
            t1, t2 = tirar("1d20").total, tirar("1d20").total
            tirada = min(t1, t2)
            detalle = f"desventaja ({t1}, {t2}) → {tirada}"
        else:
            tirada = tirar("1d20").total
            detalle = str(tirada)
        
        total = tirada + mod_salvacion
        exito = total >= cd
        
        return {
            "exito": exito,
            "tirada": tirada,
            "modificador": mod_salvacion,
            "total": total,
            "cd": cd,
            "margen": total - cd,
            "competente": es_competente,
            "critico_natural": tirada == 20,
            "pifia_natural": tirada == 1,
            "desglose": f"{detalle} + {mod_salvacion} = {total} vs CD {cd}"
        }


class TirarAtaque(Herramienta):
    """Realiza una tirada de ataque."""
    
    @property
    def nombre(self) -> str:
        return "tirar_ataque"
    
    @property
    def descripcion(self) -> str:
        return "Realiza una tirada de ataque contra la CA de un objetivo."
    
    @property
    def parametros(self) -> Dict[str, Dict[str, Any]]:
        return {
            "ca_objetivo": {
                "tipo": "int",
                "descripcion": "Clase de Armadura del objetivo",
                "requerido": True
            },
            "tipo_ataque": {
                "tipo": "string",
                "descripcion": "Tipo de ataque",
                "requerido": False,
                "opciones": ["cac", "distancia"]
            },
            "ventaja": {
                "tipo": "bool",
                "descripcion": "Si tiene ventaja",
                "requerido": False
            },
            "desventaja": {
                "tipo": "bool",
                "descripcion": "Si tiene desventaja",
                "requerido": False
            }
        }
    
    def ejecutar(self, contexto: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        from motor.dados import tirar
        
        pj = contexto.get("pj")
        if not pj:
            return {"exito": False, "error": "No hay personaje cargado"}
        
        ca_objetivo = int(kwargs["ca_objetivo"])
        tipo = kwargs.get("tipo_ataque", "cac")
        ventaja = kwargs.get("ventaja", False)
        desventaja = kwargs.get("desventaja", False)
        
        # Calcular bonificador de ataque
        derivados = pj.get("derivados", {})
        mods = derivados.get("modificadores", {})
        bon_comp = derivados.get("bonificador_competencia", 2)
        
        if tipo == "distancia":
            mod_car = mods.get("destreza", 0)
            caracteristica = "DES"
        else:
            mod_car = mods.get("fuerza", 0)
            caracteristica = "FUE"
        
        modificador = mod_car + bon_comp
        
        # Tirar
        if ventaja and not desventaja:
            t1, t2 = tirar("1d20").total, tirar("1d20").total
            tirada = max(t1, t2)
            detalle = f"ventaja ({t1}, {t2}) → {tirada}"
        elif desventaja and not ventaja:
            t1, t2 = tirar("1d20").total, tirar("1d20").total
            tirada = min(t1, t2)
            detalle = f"desventaja ({t1}, {t2}) → {tirada}"
        else:
            tirada = tirar("1d20").total
            detalle = str(tirada)
        
        total = tirada + modificador
        impacta = total >= ca_objetivo
        critico = tirada == 20
        pifia = tirada == 1
        
        # Si impacta, calcular daño
        daño = None
        daño_detalle = None
        if impacta or critico:
            # Obtener arma equipada
            equipo = pj.get("equipo", {})
            arma = next((a for a in equipo.get("armas", []) if a.get("equipada")), None)
            
            # Daño base (simplificado)
            dado_daño = "1d8"  # Por defecto espada larga
            if arma:
                nombre = arma.get("nombre", "").lower()
                if "daga" in nombre:
                    dado_daño = "1d4"
                elif "corta" in nombre:
                    dado_daño = "1d6"
                elif "larga" in nombre or "bastarda" in nombre:
                    dado_daño = "1d8"
                elif "dos manos" in nombre or "mandoble" in nombre:
                    dado_daño = "2d6"
            
            # Tirar daño (doble dados si crítico)
            if critico:
                tirada_daño = tirar(dado_daño).total + tirar(dado_daño).total
            else:
                tirada_daño = tirar(dado_daño).total
            
            # Añadir modificador + estilo Duelo si aplica
            bonus_daño = mod_car
            rasgos = pj.get("rasgos", {}).get("clase", [])
            for r in rasgos:
                if r.get("id") == "estilo_combate" and r.get("opcion") == "duelo":
                    bonus_daño += 2
                    break
            
            daño = tirada_daño + bonus_daño
            daño_detalle = f"{dado_daño}={tirada_daño} + {bonus_daño} = {daño}"
            if critico:
                daño_detalle = f"¡CRÍTICO! {daño_detalle}"
        
        return {
            "impacta": impacta or critico,  # Crítico siempre impacta
            "tirada": tirada,
            "modificador": modificador,
            "total": total,
            "ca_objetivo": ca_objetivo,
            "critico": critico,
            "pifia": pifia,
            "daño": daño,
            "daño_detalle": daño_detalle,
            "desglose": f"{detalle} + {mod_car} ({caracteristica}) + {bon_comp} (comp) = {total} vs CA {ca_objetivo}"
        }


# Registrar
registrar_herramienta(TirarHabilidad())
registrar_herramienta(TirarSalvacion())
registrar_herramienta(TirarAtaque())
