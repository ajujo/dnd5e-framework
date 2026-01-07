"""
Normalizador de Acciones para D&D 5e

Convierte texto en lenguaje natural a estructuras JSON canónicas.
Usa un enfoque híbrido:
1. Patrones deterministas desde vocabulario.py (rápido, mantenible)
2. Fallback a LLM local (solo cuando hace falta)

PATRÓN: Inyección de dependencias
- Recibe CompendioMotor por constructor
- Recibe contexto de escena (enemigos, equipo, etc.)

El LLM NO decide reglas. Solo rellena campos del JSON.
La legalidad la decide ValidadorAcciones.
"""

import re
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

from .compendio import CompendioMotor
from .vocabulario import (
    TipoIntencion,
    detectar_intencion_por_verbo,
    detectar_habilidad_por_verbo,
    detectar_accion_generica,
    es_ataque_desarmado,
    buscar_sinonimo_arma,
    SINONIMOS_ACCION_GENERICA,
)


class TipoAccionNorm(Enum):
    """Tipos de acción normalizados."""
    ATAQUE = "ataque"
    CONJURO = "conjuro"
    MOVIMIENTO = "movimiento"
    HABILIDAD = "habilidad"
    ACCION = "accion"
    OBJETO = "objeto"
    DESCONOCIDO = "desconocido"


# Mapeo de TipoIntencion a TipoAccionNorm
_INTENCION_A_ACCION = {
    TipoIntencion.ATAQUE: TipoAccionNorm.ATAQUE,
    TipoIntencion.CONJURO: TipoAccionNorm.CONJURO,
    TipoIntencion.MOVIMIENTO: TipoAccionNorm.MOVIMIENTO,
    TipoIntencion.HABILIDAD: TipoAccionNorm.HABILIDAD,
    TipoIntencion.ACCION: TipoAccionNorm.ACCION,
    TipoIntencion.OBJETO: TipoAccionNorm.OBJETO,
}


@dataclass
class AccionNormalizada:
    """Resultado de normalizar una acción."""
    tipo: TipoAccionNorm
    datos: Dict[str, Any]
    confianza: float = 0.0
    faltantes: List[str] = field(default_factory=list)
    advertencias: List[str] = field(default_factory=list)
    texto_original: str = ""
    requiere_clarificacion: bool = False
    fuente: str = "patron"
    
    def es_completa(self) -> bool:
        return len(self.faltantes) == 0 and self.confianza >= 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tipo": self.tipo.value,
            "datos": self.datos,
            "confianza": self.confianza,
            "faltantes": self.faltantes,
            "advertencias": self.advertencias,
            "texto_original": self.texto_original,
            "requiere_clarificacion": self.requiere_clarificacion,
            "fuente": self.fuente
        }


@dataclass
class ContextoEscena:
    """Contexto actual de la escena para resolver ambigüedades."""
    actor_id: str
    actor_nombre: str
    
    arma_principal: Optional[Dict[str, Any]] = None
    arma_secundaria: Optional[Dict[str, Any]] = None
    armas_disponibles: List[Dict[str, Any]] = field(default_factory=list)
    
    conjuros_conocidos: List[Dict[str, Any]] = field(default_factory=list)
    ranuras_disponibles: Dict[int, int] = field(default_factory=dict)
    
    enemigos_vivos: List[Dict[str, Any]] = field(default_factory=list)
    aliados: List[Dict[str, Any]] = field(default_factory=list)
    
    movimiento_restante: int = 30
    accion_disponible: bool = True
    accion_bonus_disponible: bool = True


# Lista de habilidades válidas
HABILIDADES_VALIDAS = [
    'acrobacias', 'arcanos', 'atletismo', 'engaño', 'historia',
    'interpretacion', 'intimidacion', 'investigacion', 'juego_manos',
    'medicina', 'naturaleza', 'percepcion', 'perspicacia', 'persuasion',
    'religion', 'sigilo', 'supervivencia', 'trato_animales'
]


class NormalizadorAcciones:
    """Normaliza texto en lenguaje natural a acciones estructuradas."""
    
    def __init__(self, compendio_motor: CompendioMotor, 
                 llm_callback: Callable[[str, Dict], Dict] = None):
        self._compendio = compendio_motor
        self._llm_callback = llm_callback
    
    def normalizar(self, texto: str, 
                   contexto: ContextoEscena) -> AccionNormalizada:
        """Normaliza un texto de acción a formato canónico."""
        texto_limpio = self._preprocesar(texto)
        tipo, confianza_tipo = self._detectar_intencion(texto_limpio, contexto)
        
        if tipo == TipoAccionNorm.ATAQUE:
            resultado = self._normalizar_ataque(texto_limpio, contexto)
        elif tipo == TipoAccionNorm.CONJURO:
            resultado = self._normalizar_conjuro(texto_limpio, contexto)
        elif tipo == TipoAccionNorm.MOVIMIENTO:
            resultado = self._normalizar_movimiento(texto_limpio, contexto)
        elif tipo == TipoAccionNorm.HABILIDAD:
            resultado = self._normalizar_habilidad(texto_limpio, contexto)
        elif tipo == TipoAccionNorm.ACCION:
            resultado = self._normalizar_accion_generica(texto_limpio, contexto)
        elif tipo == TipoAccionNorm.OBJETO:
            resultado = self._normalizar_objeto(texto_limpio, contexto)
        else:
            resultado = AccionNormalizada(
                tipo=TipoAccionNorm.DESCONOCIDO,
                datos={"actor_id": contexto.actor_id},
                confianza=0.0,
                faltantes=["tipo"],
                texto_original=texto
            )
        
        resultado = self._resolver_ambiguedades(resultado, contexto)
        
        if not resultado.es_completa() and self._llm_callback:
            resultado = self._fallback_llm(resultado, texto, contexto)
        
        resultado = self._canonizar(resultado)
        resultado.texto_original = texto
        
        return resultado
    
    def _preprocesar(self, texto: str) -> str:
        texto = texto.lower()
        texto = re.sub(r'[^\w\s\-áéíóúüñ]', ' ', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto
    
    def _detectar_intencion(self, texto: str, contexto: ContextoEscena) -> Tuple[TipoAccionNorm, float]:
        """Detecta el tipo de acción usando el vocabulario centralizado."""
        
        # 1. Acciones genéricas (muy específicas)
        accion = detectar_accion_generica(texto)
        if accion:
            return TipoAccionNorm.ACCION, 0.9
        
        # 2. Conjuros conocidos por nombre
        for conjuro in contexto.conjuros_conocidos:
            nombre_lower = conjuro.get("nombre", "").lower()
            if nombre_lower and nombre_lower in texto:
                return TipoAccionNorm.CONJURO, 0.95
        
        # También en compendio
        conjuros = self._compendio.listar_conjuros()
        for conjuro in conjuros:
            if conjuro["nombre"].lower() in texto:
                return TipoAccionNorm.CONJURO, 0.9
        
        # 3. Habilidades por nombre directo
        texto_norm = self._normalizar_texto_habilidad(texto)
        for hab in HABILIDADES_VALIDAS:
            if hab in texto_norm:
                return TipoAccionNorm.HABILIDAD, 0.9
        
        # 4. Detectar por verbos usando vocabulario
        intencion = detectar_intencion_por_verbo(texto)
        if intencion:
            tipo_accion = _INTENCION_A_ACCION.get(intencion, TipoAccionNorm.DESCONOCIDO)
            return tipo_accion, 0.85
        
        # 5. Objetos (poción)
        if re.search(r'\bpoci[oó]n\b', texto):
            return TipoAccionNorm.OBJETO, 0.8
        
        return TipoAccionNorm.DESCONOCIDO, 0.0
    
    def _normalizar_ataque(self, texto: str, 
                           contexto: ContextoEscena) -> AccionNormalizada:
        datos = {
            "tipo": "ataque",
            "atacante_id": contexto.actor_id,
            "objetivo_id": None,
            "arma_id": None,
            "subtipo": "melee",
            "modo": "normal"
        }
        faltantes = []
        advertencias = []
        confianza = 0.7
        
        # Detectar ataque desarmado
        if es_ataque_desarmado(texto):
            datos["arma_id"] = "unarmed"
            datos["subtipo"] = "unarmed"
        else:
            arma_id, arma_confianza = self._buscar_arma_en_texto(texto, contexto)
            if arma_id:
                datos["arma_id"] = arma_id
                confianza = min(confianza + 0.1, 1.0)
            else:
                faltantes.append("arma_id")
        
        objetivo_id, obj_confianza = self._buscar_objetivo_en_texto(texto, contexto)
        if objetivo_id:
            datos["objetivo_id"] = objetivo_id
            confianza = min(confianza + 0.1, 1.0)
        else:
            faltantes.append("objetivo_id")
        
        if re.search(r'\bventaja\b', texto):
            datos["modo"] = "ventaja"
        elif re.search(r'\bdesventaja\b', texto):
            datos["modo"] = "desventaja"
        
        if re.search(r'\b(arco|ballesta|distancia|disparar|disparo)\b', texto):
            datos["subtipo"] = "ranged"
        
        return AccionNormalizada(
            tipo=TipoAccionNorm.ATAQUE,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes,
            advertencias=advertencias
        )
    
    def _normalizar_conjuro(self, texto: str,
                            contexto: ContextoEscena) -> AccionNormalizada:
        datos = {
            "tipo": "conjuro",
            "lanzador_id": contexto.actor_id,
            "objetivo_id": None,
            "conjuro_id": None,
            "nivel_lanzamiento": None
        }
        faltantes = []
        confianza = 0.6
        
        conjuro_id, conj_confianza = self._buscar_conjuro_en_texto(texto, contexto)
        if conjuro_id:
            datos["conjuro_id"] = conjuro_id
            confianza = min(confianza + 0.2, 1.0)
            conjuro = self._compendio.obtener_conjuro(conjuro_id)
            if conjuro:
                datos["nivel_lanzamiento"] = conjuro.get("nivel", 1)
        else:
            faltantes.append("conjuro_id")
        
        match_nivel = re.search(r'nivel\s+(\d+)', texto)
        if match_nivel:
            datos["nivel_lanzamiento"] = int(match_nivel.group(1))
        
        objetivo_id, _ = self._buscar_objetivo_en_texto(texto, contexto)
        datos["objetivo_id"] = objetivo_id
        
        return AccionNormalizada(
            tipo=TipoAccionNorm.CONJURO,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes
        )
    
    def _normalizar_movimiento(self, texto: str,
                               contexto: ContextoEscena) -> AccionNormalizada:
        datos = {
            "tipo": "movimiento",
            "actor_id": contexto.actor_id,
            "distancia_pies": None,
            "destino": None
        }
        faltantes = []
        confianza = 0.7
        
        match_pies = re.search(r'(\d+)\s*(pies|ft|feet|pie)', texto)
        match_metros = re.search(r'(\d+)\s*(metros?|m)\b', texto)
        match_casillas = re.search(r'(\d+)\s*casillas?', texto)
        
        if match_pies:
            datos["distancia_pies"] = int(match_pies.group(1))
        elif match_metros:
            datos["distancia_pies"] = int(int(match_metros.group(1)) * 3.28)
        elif match_casillas:
            datos["distancia_pies"] = int(match_casillas.group(1)) * 5
        else:
            faltantes.append("distancia_pies")
        
        for patron in [r'hacia\s+(?:el|la|los|las)?\s*(\w+)', r'a\s+(?:el|la|los|las)?\s*(\w+)']:
            match = re.search(patron, texto)
            if match:
                datos["destino"] = match.group(1)
                break
        
        return AccionNormalizada(
            tipo=TipoAccionNorm.MOVIMIENTO,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes
        )
    
    def _normalizar_habilidad(self, texto: str,
                              contexto: ContextoEscena) -> AccionNormalizada:
        datos = {
            "tipo": "habilidad",
            "actor_id": contexto.actor_id,
            "habilidad": None,
            "objetivo_id": None
        }
        faltantes = []
        confianza = 0.6
        
        # Buscar por nombre de habilidad
        texto_norm = self._normalizar_texto_habilidad(texto)
        for hab in HABILIDADES_VALIDAS:
            if hab in texto_norm:
                datos["habilidad"] = hab
                confianza = 0.9
                break
        
        # Si no, usar vocabulario
        if not datos["habilidad"]:
            habilidad = detectar_habilidad_por_verbo(texto)
            if habilidad:
                datos["habilidad"] = habilidad
                confianza = 0.85
            else:
                faltantes.append("habilidad")
                confianza = 0.4
        
        return AccionNormalizada(
            tipo=TipoAccionNorm.HABILIDAD,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes
        )
    
    def _normalizar_accion_generica(self, texto: str,
                                     contexto: ContextoEscena) -> AccionNormalizada:
        datos = {
            "tipo": "accion",
            "actor_id": contexto.actor_id,
            "accion_id": None
        }
        faltantes = []
        confianza = 0.5
        
        accion = detectar_accion_generica(texto)
        if accion:
            datos["accion_id"] = accion
            confianza = 0.9
        else:
            faltantes.append("accion_id")
        
        return AccionNormalizada(
            tipo=TipoAccionNorm.ACCION,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes
        )
    
    def _normalizar_objeto(self, texto: str,
                           contexto: ContextoEscena) -> AccionNormalizada:
        datos = {
            "tipo": "objeto",
            "actor_id": contexto.actor_id,
            "objeto_id": None
        }
        faltantes = ["objeto_id"]
        confianza = 0.5
        
        objetos = self._compendio.listar_objetos()
        for obj in objetos:
            if obj["nombre"].lower() in texto or obj["id"].lower() in texto:
                datos["objeto_id"] = obj["id"]
                faltantes.remove("objeto_id")
                confianza = 0.85
                break
        
        if not datos["objeto_id"] and re.search(r'\bpoci[oó]n\b', texto):
            if self._compendio.existe_objeto("pocion_curacion"):
                datos["objeto_id"] = "pocion_curacion"
                if "objeto_id" in faltantes:
                    faltantes.remove("objeto_id")
                confianza = 0.6
        
        return AccionNormalizada(
            tipo=TipoAccionNorm.OBJETO,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes
        )
    
    def _buscar_arma_en_texto(self, texto: str,
                              contexto: ContextoEscena) -> Tuple[Optional[str], float]:
        # Armas disponibles del personaje
        for arma in contexto.armas_disponibles:
            nombre_lower = arma.get("nombre", "").lower()
            if nombre_lower and nombre_lower in texto:
                return arma.get("compendio_ref") or arma.get("id"), 0.95
        
        # Compendio
        armas = self._compendio.listar_armas()
        for arma in armas:
            if arma["nombre"].lower() in texto:
                return arma["id"], 0.8
        
        # Sinónimos del vocabulario
        arma_sinonimo = buscar_sinonimo_arma(texto)
        if arma_sinonimo:
            return arma_sinonimo, 0.7
        
        return None, 0.0
    
    def _buscar_objetivo_en_texto(self, texto: str,
                                  contexto: ContextoEscena) -> Tuple[Optional[str], float]:
        for enemigo in contexto.enemigos_vivos:
            nombre_lower = enemigo.get("nombre", "").lower()
            if nombre_lower and nombre_lower in texto:
                return enemigo.get("instancia_id") or enemigo.get("id"), 0.95
        
        for enemigo in contexto.enemigos_vivos:
            nombre = enemigo.get("nombre", "").lower()
            for palabra in nombre.split():
                if len(palabra) > 3 and palabra in texto:
                    return enemigo.get("instancia_id") or enemigo.get("id"), 0.85
        
        for enemigo in contexto.enemigos_vivos:
            ref = enemigo.get("compendio_ref", "").lower()
            if ref and ref in texto:
                return enemigo.get("instancia_id") or enemigo.get("id"), 0.8
        
        return None, 0.0
    
    def _buscar_conjuro_en_texto(self, texto: str,
                                 contexto: ContextoEscena) -> Tuple[Optional[str], float]:
        for conjuro in contexto.conjuros_conocidos:
            nombre_lower = conjuro.get("nombre", "").lower()
            if nombre_lower and nombre_lower in texto:
                return conjuro.get("id"), 0.95
        
        conjuros = self._compendio.listar_conjuros()
        for conjuro in conjuros:
            nombre_lower = conjuro["nombre"].lower()
            if nombre_lower in texto or nombre_lower.replace(" ", "_") in texto:
                return conjuro["id"], 0.8
        
        return None, 0.0
    
    def _normalizar_texto_habilidad(self, texto: str) -> str:
        reemplazos = {
            'percepción': 'percepcion', 'religión': 'religion',
            'persuasión': 'persuasion', 'intimidación': 'intimidacion',
            'investigación': 'investigacion', 'interpretación': 'interpretacion',
        }
        texto_norm = texto.lower()
        for original, reemplazo in reemplazos.items():
            texto_norm = texto_norm.replace(original, reemplazo)
        return texto_norm
    
    def _resolver_ambiguedades(self, resultado: AccionNormalizada,
                               contexto: ContextoEscena) -> AccionNormalizada:
        datos = resultado.datos.copy()
        faltantes = resultado.faltantes.copy()
        advertencias = resultado.advertencias.copy()
        confianza = resultado.confianza
        
        if "objetivo_id" in faltantes:
            if len(contexto.enemigos_vivos) == 1:
                objetivo = contexto.enemigos_vivos[0]
                datos["objetivo_id"] = objetivo.get("instancia_id") or objetivo.get("id")
                faltantes.remove("objetivo_id")
                advertencias.append(f"Objetivo inferido: {objetivo.get('nombre', 'enemigo')}")
                confianza = min(confianza + 0.1, 1.0)
            elif len(contexto.enemigos_vivos) > 1:
                nombres = [e.get("nombre", "?") for e in contexto.enemigos_vivos]
                advertencias.append(f"Múltiples objetivos: {', '.join(nombres)}")
        
        if "arma_id" in faltantes and resultado.tipo == TipoAccionNorm.ATAQUE:
            if contexto.arma_principal:
                ref = contexto.arma_principal.get("compendio_ref") or contexto.arma_principal.get("id")
                datos["arma_id"] = ref
                faltantes.remove("arma_id")
                advertencias.append(f"Arma inferida: {contexto.arma_principal.get('nombre', ref)}")
                confianza = min(confianza + 0.1, 1.0)
        
        if resultado.tipo == TipoAccionNorm.CONJURO:
            if datos.get("nivel_lanzamiento") is None and datos.get("conjuro_id"):
                conjuro = self._compendio.obtener_conjuro(datos["conjuro_id"])
                if conjuro:
                    datos["nivel_lanzamiento"] = conjuro.get("nivel", 0)
        
        return AccionNormalizada(
            tipo=resultado.tipo, datos=datos, confianza=confianza,
            faltantes=faltantes, advertencias=advertencias, fuente=resultado.fuente
        )
    
    def _fallback_llm(self, resultado: AccionNormalizada,
                      texto_original: str, contexto: ContextoEscena) -> AccionNormalizada:
        if not self._llm_callback:
            return resultado
        
        contexto_llm = {
            "texto_jugador": texto_original,
            "tipo_detectado": resultado.tipo.value,
            "datos_parciales": resultado.datos,
            "faltantes": resultado.faltantes,
            "armas_equipadas": [
                {"id": a.get("compendio_ref") or a.get("id"), "nombre": a.get("nombre")}
                for a in [contexto.arma_principal, contexto.arma_secundaria] if a
            ],
            "enemigos_vivos": [
                {"id": e.get("instancia_id") or e.get("id"), "nombre": e.get("nombre")}
                for e in contexto.enemigos_vivos
            ],
        }
        
        prompt = f"""Completa los campos faltantes de esta acción:
Texto: "{texto_original}"
Tipo: {resultado.tipo.value}
Faltantes: {resultado.faltantes}
Contexto: {contexto_llm}
Responde SOLO con JSON."""
        
        try:
            respuesta = self._llm_callback(prompt, contexto_llm)
            if respuesta and isinstance(respuesta, dict):
                for key, value in respuesta.items():
                    if value is not None:
                        resultado.datos[key] = value
                        if key in resultado.faltantes:
                            resultado.faltantes.remove(key)
                resultado.fuente = "llm"
                resultado.confianza = min(resultado.confianza + 0.15, 0.9)
        except Exception as e:
            resultado.advertencias.append(f"Error LLM: {str(e)}")
        
        return resultado
    
    def _canonizar(self, resultado: AccionNormalizada) -> AccionNormalizada:
        datos = resultado.datos
        
        if resultado.tipo == TipoAccionNorm.ATAQUE:
            datos.setdefault("subtipo", "melee")
            datos.setdefault("modo", "normal")
        elif resultado.tipo == TipoAccionNorm.CONJURO:
            datos.setdefault("nivel_lanzamiento", 1)
        elif resultado.tipo == TipoAccionNorm.MOVIMIENTO:
            datos.setdefault("distancia_pies", 0)
        
        campos_criticos = {
            TipoAccionNorm.ATAQUE: ["objetivo_id"],
            TipoAccionNorm.CONJURO: ["conjuro_id"],
            TipoAccionNorm.MOVIMIENTO: [],
            TipoAccionNorm.HABILIDAD: ["habilidad"],
            TipoAccionNorm.ACCION: ["accion_id"],
            TipoAccionNorm.OBJETO: ["objeto_id"]
        }
        
        criticos = campos_criticos.get(resultado.tipo, [])
        faltantes_criticos = [f for f in resultado.faltantes if f in criticos]
        resultado.requiere_clarificacion = len(faltantes_criticos) > 0
        
        return resultado
