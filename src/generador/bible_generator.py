"""
Generador de Adventure Bibles usando LLM.

Usa el LLM para generar una biblia estructurada y luego la valida
y completa con los metadatos necesarios.
"""

import json
import uuid
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from .prompts_bible import generar_prompt_bible, obtener_info_region
from .tonos import cargar_tono, obtener_balance_solitario
from .bible_manager import obtener_bible_manager


class BibleGenerator:
    """Generador de Adventure Bibles."""
    
    def __init__(self, llm_callback=None):
        """
        Args:
            llm_callback: Función para llamar al LLM. 
                          Firma: callback(prompt: str, system: str) -> str
        """
        self.llm_callback = llm_callback
        self.bible_manager = obtener_bible_manager()
    
    def generar_bible(self, pj: Dict[str, Any], tipo_aventura_id: str,
                      region_id: str = "costa_espada") -> Tuple[Optional[Dict], str]:
        """
        Genera una Adventure Bible completa.
        
        Args:
            pj: Diccionario del personaje jugador
            tipo_aventura_id: ID del tono de aventura
            region_id: ID de la región de Faerûn
        
        Returns:
            Tupla (bible_dict, mensaje_error)
            Si tiene éxito, bible_dict es la biblia y mensaje_error es ""
            Si falla, bible_dict es None y mensaje_error explica el error
        """
        if not self.llm_callback:
            return None, "No hay conexión con el LLM"
        
        # Cargar tono
        tipo_aventura = cargar_tono(tipo_aventura_id)
        if not tipo_aventura:
            return None, f"Tipo de aventura '{tipo_aventura_id}' no encontrado"
        
        # Obtener info de región
        region = obtener_info_region(region_id)
        region_texto = f"{region['nombre']}\n{region['descripcion']}\nCiudades: {', '.join(region['ciudades'])}"
        
        # Generar prompt
        prompt = generar_prompt_bible(pj, tipo_aventura, region_texto)
        
        # Llamar al LLM
        print("  Generando aventura con LLM...")
        try:
            respuesta = self.llm_callback(prompt, "")
        except Exception as e:
            return None, f"Error llamando al LLM: {e}"
        
        if not respuesta:
            return None, "El LLM no devolvió respuesta"
        
        # Parsear JSON
        bible_raw, error = self._extraer_json(respuesta)
        if error:
            return None, f"Error parseando respuesta: {error}"
        
        # Validar estructura
        valida, error = self._validar_estructura(bible_raw)
        if not valida:
            return None, f"Estructura inválida: {error}"
        
        # Completar con metadatos
        bible_completa = self._completar_bible(bible_raw, pj, tipo_aventura_id, region_id)
        
        return bible_completa, ""
    
    def _extraer_json(self, respuesta: str) -> Tuple[Optional[Dict], str]:
        """Extrae el JSON de la respuesta del LLM."""
        # Intentar parsear directamente
        try:
            return json.loads(respuesta), ""
        except:
            pass
        
        # Buscar JSON entre ```json y ```
        match = re.search(r'```json\s*(.*?)\s*```', respuesta, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1)), ""
            except json.JSONDecodeError as e:
                return None, f"JSON inválido en bloque de código: {e}"
        
        # Buscar JSON entre { y }
        match = re.search(r'\{.*\}', respuesta, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0)), ""
            except json.JSONDecodeError as e:
                return None, f"JSON inválido: {e}"
        
        return None, "No se encontró JSON en la respuesta"
    
    def _validar_estructura(self, bible: Dict) -> Tuple[bool, str]:
        """Valida que la biblia tenga la estructura mínima requerida."""
        campos_requeridos = ["logline", "main_quest", "antagonista", "actos"]
        
        for campo in campos_requeridos:
            if campo not in bible:
                return False, f"Falta campo requerido: {campo}"
        
        # Validar main_quest
        mq = bible.get("main_quest", {})
        if not mq.get("objetivo_final"):
            return False, "main_quest.objetivo_final es requerido"
        
        # Validar antagonista
        ant = bible.get("antagonista", {})
        if not ant.get("identidad_real"):
            return False, "antagonista.identidad_real es requerido"
        
        # Validar actos
        actos = bible.get("actos", [])
        if len(actos) < 2:
            return False, "Se requieren al menos 2 actos"
        
        for i, acto in enumerate(actos):
            if not acto.get("nombre"):
                return False, f"Acto {i+1} sin nombre"
            if not acto.get("objetivo"):
                return False, f"Acto {i+1} sin objetivo"
        
        return True, ""
    
    def _completar_bible(self, bible_raw: Dict, pj: Dict, 
                         tipo_aventura_id: str, region_id: str) -> Dict[str, Any]:
        """Completa la biblia con metadatos y valores por defecto."""
        info_basica = pj.get("info_basica", {})
        nivel_pj = info_basica.get("nivel", 1)
        
        bible = {
            # Metadatos
            "meta": {
                "id": f"adv_{uuid.uuid4().hex[:8]}",
                "generada": datetime.now().isoformat(),
                "tipo_aventura": tipo_aventura_id,
                "pj_nombre": info_basica.get("nombre", "Aventurero"),
                "pj_id": pj.get("id", ""),
                "nivel_pj": nivel_pj,
                "ambientacion": "Reinos Olvidados - Faerûn",
                "region_inicial": obtener_info_region(region_id)["nombre"]
            },
            
            # Balance para solitario
            "balance_solitario": obtener_balance_solitario(tipo_aventura_id, nivel_pj),
            
            # Contenido generado por LLM
            "logline": bible_raw.get("logline", "Una aventura en Faerûn"),
            
            "main_quest": {
                "objetivo_final": bible_raw.get("main_quest", {}).get("objetivo_final", ""),
                "por_que_importa": bible_raw.get("main_quest", {}).get("por_que_importa", ""),
                "estado": "acto_1",
                "gancho_inicial": bible_raw.get("main_quest", {}).get("gancho_inicial", "")
            },
            
            "antagonista": self._completar_antagonista(bible_raw.get("antagonista", {})),
            
            "actos": self._completar_actos(bible_raw.get("actos", [])),
            
            "revelaciones": self._completar_revelaciones(bible_raw.get("revelaciones", [])),
            
            "pnj_clave": self._completar_pnjs(bible_raw.get("pnj_clave", [])),
            
            "relojes": self._completar_relojes(bible_raw.get("relojes", [])),
            
            "side_quests": self._completar_side_quests(bible_raw.get("side_quests", [])),
            
            "recompensas_previstas": bible_raw.get("recompensas_previstas", []),
            
            # Contrato de consistencia por defecto
            "contrato_consistencia": {
                "canon": [
                    "Geografía y lugares de Faerûn mencionados",
                    "Identidad y motivación del antagonista",
                    "NPCs clave y su estado (vivo/muerto)",
                    "Pistas descubiertas",
                    "Eventos importantes ocurridos"
                ],
                "flexible": [
                    "Orden de escenas dentro de cada acto",
                    "Número exacto de enemigos en encuentros",
                    "NPCs secundarios y figurantes",
                    "Ubicación exacta de pistas no descubiertas"
                ],
                "impro": [
                    "Descripciones ambientales",
                    "Diálogos exactos",
                    "Clima y hora del día",
                    "Pequeños obstáculos narrativos"
                ]
            }
        }
        
        return bible
    
    def _completar_antagonista(self, ant: Dict) -> Dict:
        """Completa la información del antagonista."""
        return {
            "identidad_real": ant.get("identidad_real", "Villano Misterioso"),
            "fachada": ant.get("fachada", ""),
            "motivacion": ant.get("motivacion", "Poder"),
            "objetivo": ant.get("objetivo", "Dominar la región"),
            "recursos": ant.get("recursos", [])[:5],
            "debilidad": ant.get("debilidad", "Su arrogancia"),
            "revelacion_prevista": "acto_3",
            "pistas_foreshadowing": ant.get("pistas_foreshadowing", [])[:4]
        }
    
    def _completar_actos(self, actos: list) -> list:
        """Completa la información de los actos."""
        resultado = []
        for i, acto in enumerate(actos):
            resultado.append({
                "numero": acto.get("numero", i + 1),
                "nombre": acto.get("nombre", f"Acto {i + 1}"),
                "objetivo": acto.get("objetivo", ""),
                "estado": "activo" if i == 0 else "pendiente",
                "escenas_semilla": [
                    {
                        "id": e.get("id", f"escena_{i+1}_{j+1}"),
                        "tipo": e.get("tipo", "exploracion"),
                        "descripcion": e.get("descripcion", ""),
                        "obligatoria": e.get("obligatoria", False),
                        "flexible": e.get("flexible", True),
                        "completada": False
                    }
                    for j, e in enumerate(acto.get("escenas_semilla", []))
                ],
                "climax": acto.get("climax", ""),
                "transicion_siguiente": acto.get("transicion_siguiente", "")
            })
        return resultado
    
    def _completar_revelaciones(self, revelaciones: list) -> list:
        """Completa las revelaciones asegurando Three Clue Rule."""
        resultado = []
        for rev in revelaciones:
            pistas = rev.get("pistas", [])
            
            # Asegurar que hay al menos una pista garantizada
            tiene_garantizada = any(p.get("garantizada") for p in pistas)
            if not tiene_garantizada and pistas:
                pistas[0]["garantizada"] = True
            
            resultado.append({
                "id": rev.get("id", f"rev_{len(resultado) + 1}"),
                "contenido": rev.get("contenido", ""),
                "importancia": rev.get("importancia", "importante"),
                "acto": rev.get("acto", 1),
                "descubierta": False,
                "pistas": [
                    {
                        "id": p.get("id", f"pista_{i+1}"),
                        "tipo": p.get("tipo", "fisica"),
                        "descripcion": p.get("descripcion", ""),
                        "donde": p.get("donde", ""),
                        "cd_obtener": p.get("cd_obtener"),
                        "garantizada": p.get("garantizada", False),
                        "encontrada": False
                    }
                    for i, p in enumerate(pistas)
                ]
            })
        return resultado
    
    def _completar_pnjs(self, pnjs: list) -> list:
        """Completa la información de NPCs."""
        resultado = []
        for pnj in pnjs:
            resultado.append({
                "nombre": pnj.get("nombre", "NPC Misterioso"),
                "rol": pnj.get("rol", "Neutral"),
                "descripcion_breve": pnj.get("descripcion_breve", ""),
                "secreto": pnj.get("secreto", ""),
                "actitud_inicial": pnj.get("actitud_inicial", "neutral"),
                "actitud_actual": pnj.get("actitud_inicial", "neutral"),
                "ubicacion": pnj.get("ubicacion", ""),
                "estado": "vivo",
                "conocido_por_pj": False,
                "interacciones": []
            })
        return resultado
    
    def _completar_relojes(self, relojes: list) -> list:
        """Completa la información de relojes."""
        resultado = []
        for reloj in relojes:
            resultado.append({
                "nombre": reloj.get("nombre", "Reloj"),
                "descripcion": reloj.get("descripcion", ""),
                "segmentos_total": reloj.get("segmentos_total", 6),
                "segmentos_actual": 0,
                "que_avanza": reloj.get("que_avanza", ""),
                "que_pasa_al_completar": reloj.get("que_pasa_al_completar", ""),
                "visible_al_jugador": False,
                "activo": True
            })
        return resultado
    
    def _completar_side_quests(self, sqs: list) -> list:
        """Completa la información de side quests."""
        resultado = []
        for sq in sqs:
            resultado.append({
                "id": sq.get("id", f"sq_{len(resultado) + 1}"),
                "gancho": sq.get("gancho", ""),
                "que_revela": sq.get("que_revela", ""),
                "como_escala": sq.get("como_escala", ""),
                "potencial_main": sq.get("potencial_main", False),
                "estado": "no_descubierta",
                "recompensa": sq.get("recompensa", "")
            })
        return resultado
    
    def guardar_bible(self, pj_id: str, bible: Dict[str, Any]) -> bool:
        """Guarda la biblia generada."""
        return self.bible_manager.guardar_bible_full(pj_id, bible)
    
    def generar_y_guardar(self, pj: Dict[str, Any], tipo_aventura_id: str,
                          region_id: str = "costa_espada") -> Tuple[bool, str]:
        """
        Genera y guarda una Adventure Bible.
        
        Returns:
            Tupla (exito, mensaje)
        """
        bible, error = self.generar_bible(pj, tipo_aventura_id, region_id)
        
        if error:
            return False, error
        
        pj_id = pj.get("id", "")
        if not pj_id:
            return False, "El PJ no tiene ID"
        
        if self.guardar_bible(pj_id, bible):
            # Crear archivo de patches vacío
            self.bible_manager.cargar_patches(pj_id)
            self.bible_manager.guardar_patches(pj_id, self.bible_manager.cargar_patches(pj_id))
            return True, f"Aventura '{bible['logline'][:50]}...' creada"
        else:
            return False, "Error guardando la biblia"


def crear_bible_generator(llm_callback=None) -> BibleGenerator:
    """Crea una instancia del generador de biblias."""
    return BibleGenerator(llm_callback)
