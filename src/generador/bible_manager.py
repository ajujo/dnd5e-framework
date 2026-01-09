"""
Gestión de Adventure Bibles.

Responsabilidades:
- Cargar/guardar biblias
- Generar vista DM (filtrada, sin spoilers)
- Aplicar patches
- Validar consistencia
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from copy import deepcopy


class BibleManager:
    """Gestor de Adventure Bibles."""
    
    def __init__(self, ruta_saves: str = None):
        """
        Args:
            ruta_saves: Ruta al directorio de saves. Si es None, usa saves/aventuras/
        """
        if ruta_saves is None:
            ruta_saves = os.path.join(
                os.path.dirname(__file__), '..', '..', 'saves', 'aventuras'
            )
        self.ruta_saves = ruta_saves
        os.makedirs(self.ruta_saves, exist_ok=True)
    
    def _ruta_aventura(self, pj_id: str) -> str:
        """Obtiene la ruta del directorio de aventura para un PJ."""
        ruta = os.path.join(self.ruta_saves, pj_id)
        os.makedirs(ruta, exist_ok=True)
        return ruta
    
    # =========================================================================
    # CARGAR / GUARDAR
    # =========================================================================
    
    def guardar_bible_full(self, pj_id: str, bible: Dict[str, Any]) -> bool:
        """Guarda la biblia completa (con spoilers)."""
        ruta = os.path.join(self._ruta_aventura(pj_id), 'adventure_bible_full.json')
        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(bible, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error guardando bible: {e}")
            return False
    
    def cargar_bible_full(self, pj_id: str) -> Optional[Dict[str, Any]]:
        """Carga la biblia completa."""
        ruta = os.path.join(self._ruta_aventura(pj_id), 'adventure_bible_full.json')
        if not os.path.exists(ruta):
            return None
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    def existe_bible(self, pj_id: str) -> bool:
        """Verifica si existe una biblia para el PJ."""
        ruta = os.path.join(self._ruta_aventura(pj_id), 'adventure_bible_full.json')
        return os.path.exists(ruta)
    
    # =========================================================================
    # GENERAR VISTA DM (SIN SPOILERS)
    # =========================================================================
    
    def generar_vista_dm(self, bible_full: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera la vista filtrada para el DM.
        
        - Sin identidad real del antagonista (hasta que corresponda)
        - Con sombras y pistas de foreshadowing
        - Solo información del acto actual
        """
        acto_actual_num = self._obtener_acto_actual(bible_full)
        
        vista = {
            "meta": {
                "acto_actual": acto_actual_num,
                "tipo_aventura": bible_full.get("meta", {}).get("tipo_aventura"),
                "pj_nombre": bible_full.get("meta", {}).get("pj_nombre"),
                "nivel_pj": bible_full.get("meta", {}).get("nivel_pj", 1)
            },
            "situacion_actual": self._generar_situacion_actual(bible_full, acto_actual_num),
            "antagonista_sombra": self._generar_sombra_antagonista(bible_full, acto_actual_num),
            "acto_actual_info": self._generar_info_acto(bible_full, acto_actual_num),
            "pnj_en_escena": self._filtrar_pnj_relevantes(bible_full, acto_actual_num),
            "revelaciones_pendientes": self._filtrar_revelaciones(bible_full, acto_actual_num),
            "relojes_visibles": self._filtrar_relojes(bible_full),
            "canon_activo": bible_full.get("contrato_consistencia", {}).get("canon", []),
            "flexible_actual": bible_full.get("contrato_consistencia", {}).get("flexible", []),
            "recordatorios_tono": self._generar_recordatorios_tono(bible_full)
        }
        
        return vista
    
    def _obtener_acto_actual(self, bible: Dict[str, Any]) -> int:
        """Determina el acto actual basándose en el estado."""
        estado_mq = bible.get("main_quest", {}).get("estado", "acto_1")
        if estado_mq.startswith("acto_"):
            try:
                return int(estado_mq.split("_")[1])
            except:
                return 1
        return 1
    
    def _generar_situacion_actual(self, bible: Dict[str, Any], acto: int) -> Dict[str, Any]:
        """Genera el resumen de situación actual."""
        actos = bible.get("actos", [])
        acto_info = next((a for a in actos if a.get("numero") == acto), None)
        
        return {
            "objetivo_inmediato": acto_info.get("objetivo", "") if acto_info else "",
            "ubicacion": bible.get("meta", {}).get("region_inicial", ""),
            "amenaza_activa": self._describir_amenaza_actual(bible),
            "tension_actual": "media"  # TODO: calcular según relojes
        }
    
    def _describir_amenaza_actual(self, bible: Dict[str, Any]) -> str:
        """Describe la amenaza sin revelar al antagonista."""
        antagonista = bible.get("antagonista", {})
        return f"Una conspiración {antagonista.get('fachada', 'misteriosa')} amenaza la ciudad"
    
    def _generar_sombra_antagonista(self, bible: Dict[str, Any], acto: int) -> Dict[str, Any]:
        """Genera la sombra del antagonista según el acto."""
        antagonista = bible.get("antagonista", {})
        revelacion_acto = antagonista.get("revelacion_prevista", "acto_3")
        
        # Determinar si ya se puede revelar
        try:
            acto_revelacion = int(revelacion_acto.split("_")[1])
        except:
            acto_revelacion = 3
        
        revelacion_disponible = acto >= acto_revelacion
        
        sombra = {
            "descripcion_vaga": f"Una figura con conexiones en {antagonista.get('fachada', 'los círculos de poder')}",
            "pistas_para_sembrar": antagonista.get("pistas_foreshadowing", [])[:2],  # Solo 2 pistas
            "recursos_visibles": [r for r in antagonista.get("recursos", [])[:2]],  # Solo 2 recursos
            "revelacion_disponible": revelacion_disponible
        }
        
        if revelacion_disponible:
            sombra["identidad_real"] = antagonista.get("identidad_real")
            sombra["motivacion"] = antagonista.get("motivacion")
            sombra["debilidad"] = antagonista.get("debilidad")
        
        return sombra
    
    def _generar_info_acto(self, bible: Dict[str, Any], acto: int) -> Dict[str, Any]:
        """Genera información del acto actual."""
        actos = bible.get("actos", [])
        acto_info = next((a for a in actos if a.get("numero") == acto), None)
        
        if not acto_info:
            return {}
        
        return {
            "numero": acto,
            "nombre": acto_info.get("nombre", ""),
            "objetivo": acto_info.get("objetivo", ""),
            "escenas_disponibles": [
                {
                    "id": e.get("id"),
                    "tipo": e.get("tipo"),
                    "descripcion": e.get("descripcion"),
                    "completada": False  # TODO: tracking de escenas
                }
                for e in acto_info.get("escenas_semilla", [])
            ],
            "climax_previsto": acto_info.get("climax", ""),
            "progreso": "inicio"  # TODO: calcular progreso
        }
    
    def _filtrar_pnj_relevantes(self, bible: Dict[str, Any], acto: int) -> List[Dict[str, Any]]:
        """Filtra NPCs relevantes para el acto actual."""
        pnjs = bible.get("pnj_clave", [])
        
        resultado = []
        for pnj in pnjs:
            if pnj.get("estado") == "muerto":
                continue
            
            # No revelar que es el antagonista
            es_antagonista = "antagonista" in pnj.get("rol", "").lower()
            
            resultado.append({
                "nombre": pnj.get("nombre"),
                "rol_visible": pnj.get("rol") if not es_antagonista else "Noble local",
                "actitud_actual": pnj.get("actitud_actual", pnj.get("actitud_inicial")),
                "ubicacion": pnj.get("ubicacion"),
                "secreto_hint": "Parece ocultar algo..." if pnj.get("secreto") else None
            })
        
        return resultado
    
    def _filtrar_revelaciones(self, bible: Dict[str, Any], acto: int) -> List[Dict[str, Any]]:
        """Filtra revelaciones pendientes para el acto actual."""
        revelaciones = bible.get("revelaciones", [])
        
        resultado = []
        for rev in revelaciones:
            if rev.get("descubierta"):
                continue
            if rev.get("acto", 1) > acto:
                continue  # No mostrar revelaciones de actos futuros
            
            pista_garantizada = next(
                (p for p in rev.get("pistas", []) if p.get("garantizada")),
                None
            )
            
            resultado.append({
                "id": rev.get("id"),
                "pista_garantizada": pista_garantizada.get("descripcion") if pista_garantizada else None,
                "pistas_opcionales": [
                    p.get("descripcion") for p in rev.get("pistas", [])
                    if not p.get("garantizada") and not p.get("encontrada")
                ][:2],  # Solo mostrar 2 opcionales
                "entregada": False
            })
        
        return resultado
    
    def _filtrar_relojes(self, bible: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtra relojes activos."""
        relojes = bible.get("relojes", [])
        
        resultado = []
        for reloj in relojes:
            if not reloj.get("activo"):
                continue
            
            actual = reloj.get("segmentos_actual", 0)
            total = reloj.get("segmentos_total", 6)
            
            # Calcular urgencia
            porcentaje = actual / total if total > 0 else 0
            if porcentaje >= 0.75:
                urgencia = "critica"
            elif porcentaje >= 0.5:
                urgencia = "alta"
            elif porcentaje >= 0.25:
                urgencia = "media"
            else:
                urgencia = "baja"
            
            resultado.append({
                "nombre": reloj.get("nombre"),
                "segmentos": f"{actual}/{total}",
                "urgencia": urgencia,
                "que_avanza": reloj.get("que_avanza")
            })
        
        return resultado
    
    def _generar_recordatorios_tono(self, bible: Dict[str, Any]) -> Dict[str, Any]:
        """Genera recordatorios del tono de aventura."""
        balance = bible.get("balance_solitario", {})
        
        return {
            "letalidad": balance.get("letalidad", "media"),
            "como_resolver_fallos": "Los fallos generan costes y complicaciones, pero la historia siempre avanza",
            "frecuencia_combate": balance.get("combate", {}).get("encuentros_por_acto", "2-3")
        }
    
    # =========================================================================
    # PATCH SYSTEM
    # =========================================================================
    
    def cargar_patches(self, pj_id: str) -> Dict[str, Any]:
        """Carga el archivo de patches."""
        ruta = os.path.join(self._ruta_aventura(pj_id), 'adventure_patch.json')
        if not os.path.exists(ruta):
            return {
                "version": 1,
                "bible_id": "",
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "patch_policy": {
                    "append_only": ["revelaciones", "pnj_clave.interacciones", "canon_activo"],
                    "replace": ["main_quest.estado", "actos.estado", "relojes.segmentos_actual"],
                    "tombstone": ["pnj_clave", "side_quests", "relojes"]
                },
                "patches": [],
                "resumen_cambios": {
                    "pnj_muertos": [],
                    "revelaciones_descubiertas": [],
                    "side_quests_completadas": [],
                    "relojes_completados": [],
                    "cambios_main_quest": []
                }
            }
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    def guardar_patches(self, pj_id: str, patches: Dict[str, Any]) -> bool:
        """Guarda el archivo de patches."""
        patches["last_updated"] = datetime.now().isoformat()
        ruta = os.path.join(self._ruta_aventura(pj_id), 'adventure_patch.json')
        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(patches, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def aplicar_patch(self, pj_id: str, turno: int, tipo: str, path: str, 
                      valor_nuevo: Any, razon: str = "") -> bool:
        """
        Aplica un patch a la biblia.
        
        Args:
            pj_id: ID del personaje
            turno: Turno de juego actual
            tipo: 'append', 'replace', 'tombstone', 'merge'
            path: Ruta al elemento (ej: 'pnj_clave.capitan_darvin')
            valor_nuevo: Nuevo valor
            razon: Razón del cambio
        """
        bible = self.cargar_bible_full(pj_id)
        patches = self.cargar_patches(pj_id)
        
        if not bible or not patches:
            return False
        
        # Obtener valor anterior para auditoría
        valor_anterior = self._obtener_valor_por_path(bible, path)
        
        # Aplicar cambio según tipo
        exito = False
        if tipo == "append":
            exito = self._aplicar_append(bible, path, valor_nuevo)
        elif tipo == "replace":
            exito = self._aplicar_replace(bible, path, valor_nuevo)
        elif tipo == "tombstone":
            exito = self._aplicar_tombstone(bible, path, valor_nuevo)
        elif tipo == "merge":
            exito = self._aplicar_merge(bible, path, valor_nuevo)
        
        if not exito:
            return False
        
        # Registrar patch
        patches["patches"].append({
            "turno": turno,
            "timestamp": datetime.now().isoformat(),
            "tipo": tipo,
            "path": path,
            "valor_anterior": valor_anterior,
            "valor_nuevo": valor_nuevo,
            "razon": razon
        })
        
        # Actualizar resumen
        self._actualizar_resumen_cambios(patches, tipo, path, valor_nuevo)
        
        # Guardar todo
        self.guardar_bible_full(pj_id, bible)
        self.guardar_patches(pj_id, patches)
        
        return True
    
    def _obtener_valor_por_path(self, data: Dict, path: str) -> Any:
        """Obtiene un valor anidado por path."""
        partes = path.split(".")
        actual = data
        for parte in partes:
            if isinstance(actual, dict) and parte in actual:
                actual = actual[parte]
            elif isinstance(actual, list):
                try:
                    idx = int(parte)
                    actual = actual[idx]
                except:
                    return None
            else:
                return None
        return deepcopy(actual)
    
    def _establecer_valor_por_path(self, data: Dict, path: str, valor: Any) -> bool:
        """Establece un valor anidado por path."""
        partes = path.split(".")
        actual = data
        for parte in partes[:-1]:
            if isinstance(actual, dict):
                if parte not in actual:
                    actual[parte] = {}
                actual = actual[parte]
            else:
                return False
        
        if isinstance(actual, dict):
            actual[partes[-1]] = valor
            return True
        return False
    
    def _aplicar_append(self, bible: Dict, path: str, valor: Any) -> bool:
        """Añade a una lista sin sobrescribir."""
        lista = self._obtener_valor_por_path(bible, path)
        if isinstance(lista, list):
            lista.append(valor)
            return True
        return False
    
    def _aplicar_replace(self, bible: Dict, path: str, valor: Any) -> bool:
        """Sobrescribe un valor."""
        return self._establecer_valor_por_path(bible, path, valor)
    
    def _aplicar_tombstone(self, bible: Dict, path: str, datos_tombstone: Dict) -> bool:
        """Marca un elemento como inactivo (no lo borra)."""
        elemento = self._obtener_valor_por_path(bible, path)
        if isinstance(elemento, dict):
            elemento["_tombstone"] = True
            elemento["_tombstone_fecha"] = datetime.now().isoformat()
            elemento.update(datos_tombstone)
            return True
        return False
    
    def _aplicar_merge(self, bible: Dict, path: str, valor: Dict) -> bool:
        """Hace merge profundo de diccionarios."""
        elemento = self._obtener_valor_por_path(bible, path)
        if isinstance(elemento, dict) and isinstance(valor, dict):
            self._deep_merge(elemento, valor)
            return True
        return False
    
    def _deep_merge(self, base: Dict, update: Dict) -> None:
        """Merge profundo de diccionarios."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _actualizar_resumen_cambios(self, patches: Dict, tipo: str, path: str, valor: Any) -> None:
        """Actualiza el resumen de cambios importantes."""
        resumen = patches.get("resumen_cambios", {})
        
        if "pnj_clave" in path and tipo == "tombstone":
            if isinstance(valor, dict) and valor.get("estado") == "muerto":
                nombre = path.split(".")[-1]
                if nombre not in resumen.get("pnj_muertos", []):
                    resumen.setdefault("pnj_muertos", []).append(nombre)
        
        if "revelaciones" in path and "descubierta" in str(valor):
            id_rev = path.split(".")[1] if len(path.split(".")) > 1 else "unknown"
            if id_rev not in resumen.get("revelaciones_descubiertas", []):
                resumen.setdefault("revelaciones_descubiertas", []).append(id_rev)
        
        if "main_quest.estado" in path:
            resumen.setdefault("cambios_main_quest", []).append(f"Cambio a {valor}")


# Instancia global
_bible_manager: Optional[BibleManager] = None


def obtener_bible_manager() -> BibleManager:
    """Obtiene la instancia global del BibleManager."""
    global _bible_manager
    if _bible_manager is None:
        _bible_manager = BibleManager()
    return _bible_manager
