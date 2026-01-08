"""
Creador de personajes D&D 5e.

Gestiona el flujo de creación paso a paso con soporte para:
- Pasos secuenciales validados
- Integración con LLM para sugerencias
- Autosave automático
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum

from . import compendio_pj
from .calculador import (
    aplicar_bonificadores_raza,
    recalcular_derivados,
    calcular_modificador,
)
from .storage import autosave_step, generar_id


class PasoCreacion(Enum):
    """Pasos del flujo de creación."""
    CONCEPTO = "concepto"
    RAZA = "raza"
    CLASE = "clase"
    CARACTERISTICAS = "caracteristicas"
    HABILIDADES = "habilidades"
    TRASFONDO = "trasfondo"
    PERSONALIDAD = "personalidad"
    EQUIPO = "equipo"
    DETALLES = "detalles"
    RESUMEN = "resumen"


# Orden de pasos
ORDEN_PASOS = [
    PasoCreacion.CONCEPTO,
    PasoCreacion.RAZA,
    PasoCreacion.CLASE,
    PasoCreacion.CARACTERISTICAS,
    PasoCreacion.HABILIDADES,
    PasoCreacion.TRASFONDO,
    PasoCreacion.PERSONALIDAD,
    PasoCreacion.EQUIPO,
    PasoCreacion.DETALLES,
    PasoCreacion.RESUMEN,
]


@dataclass
class CreadorPersonaje:
    """
    Gestiona el flujo de creación de un personaje.
    
    Attributes:
        pj: Diccionario del personaje en construcción
        paso_actual: Paso actual del flujo
        pasos_completados: Lista de pasos ya completados
        llm_callback: Función para obtener respuestas del LLM
        auto_save: Si debe guardar automáticamente después de cada paso
    """
    
    pj: Dict[str, Any] = field(default_factory=dict)
    paso_actual: PasoCreacion = PasoCreacion.CONCEPTO
    pasos_completados: List[str] = field(default_factory=list)
    llm_callback: Optional[Callable[[str, str], str]] = None
    auto_save: bool = True
    
    def __post_init__(self):
        """Inicializa el personaje si está vacío."""
        if not self.pj:
            self.pj = self._crear_pj_vacio()
    
    def _crear_pj_vacio(self) -> dict:
        """Crea la estructura base de un personaje vacío."""
        return {
            "id": generar_id(),
            "version": "1.0",
            "info_basica": {
                "nombre": "",
                "raza": "",
                "subraza": None,
                "clase": "",
                "nivel": 1,
                "experiencia": 0,
                "trasfondo": "",
                "alineamiento": "",
            },
            "caracteristicas": {
                "fuerza": 10,
                "destreza": 10,
                "constitucion": 10,
                "inteligencia": 10,
                "sabiduria": 10,
                "carisma": 10,
            },
            "competencias": {
                "salvaciones": [],
                "habilidades": [],
                "habilidades_origen": {},  # {"percepcion": "raza", "atletismo": "clase", ...}
                "armaduras": [],
                "armas": [],
                "herramientas": [],
                "idiomas": [],
            },
            "rasgos": {
                "raciales": [],
                "clase": [],
                "trasfondo": [],
            },
            "equipo": {
                "armas": [],
                "armadura": None,
                "escudo": None,
                "objetos": [],
                "dinero": {"po": 0, "pp": 0, "pe": 0, "pc": 0},
            },
            "personalidad": {
                "rasgos": [],
                "ideales": [],
                "vinculos": [],
                "defectos": [],
            },
            "reglas": {
                "sistema": "dnd5e",
                "version": "PHB",
                "nivel_max_creador": 1,
            },
            "historia": {
                "edad": None,
                "altura": "",
                "peso": "",
                "ojos": "",
                "cabello": "",
                "piel": "",
                "backstory": "",
            },
            "conjuros": None,
            "derivados": {},
        }
    
    def _guardar_progreso(self):
        """Guarda el progreso actual si auto_save está activo."""
        if self.auto_save:
            autosave_step(
                self.pj,
                self.paso_actual.value,
                self.pasos_completados
            )
    
    def obtener_paso_actual(self) -> PasoCreacion:
        """Obtiene el paso actual."""
        return self.paso_actual
    
    def obtener_progreso(self) -> Dict[str, Any]:
        """Obtiene información del progreso."""
        total = len(ORDEN_PASOS)
        completados = len(self.pasos_completados)
        return {
            "paso_actual": self.paso_actual.value,
            "pasos_completados": self.pasos_completados,
            "total_pasos": total,
            "porcentaje": int(completados / total * 100),
        }
    
    def avanzar_paso(self) -> Optional[PasoCreacion]:
        """
        Avanza al siguiente paso.
        
        Returns:
            Siguiente paso o None si ya terminó
        """
        # Marcar paso actual como completado
        if self.paso_actual.value not in self.pasos_completados:
            self.pasos_completados.append(self.paso_actual.value)
        
        # Buscar siguiente paso
        idx_actual = ORDEN_PASOS.index(self.paso_actual)
        if idx_actual < len(ORDEN_PASOS) - 1:
            self.paso_actual = ORDEN_PASOS[idx_actual + 1]
            self._guardar_progreso()
            return self.paso_actual
        
        return None
    
    def retroceder_paso(self) -> Optional[PasoCreacion]:
        """
        Retrocede al paso anterior.
        
        Returns:
            Paso anterior o None si ya está al inicio
        """
        idx_actual = ORDEN_PASOS.index(self.paso_actual)
        if idx_actual > 0:
            self.paso_actual = ORDEN_PASOS[idx_actual - 1]
            return self.paso_actual
        return None
    
    def ir_a_paso(self, paso: PasoCreacion) -> bool:
        """
        Va directamente a un paso específico.
        
        Solo permite ir a pasos anteriores o al siguiente inmediato.
        
        Returns:
            True si se pudo ir al paso
        """
        idx_destino = ORDEN_PASOS.index(paso)
        idx_actual = ORDEN_PASOS.index(self.paso_actual)
        
        # Permitir ir atrás o al siguiente
        if idx_destino <= idx_actual + 1:
            self.paso_actual = paso
            return True
        return False
    
    # =========================================================================
    # MÉTODOS POR PASO
    # =========================================================================
    
    def establecer_concepto(self, concepto: str):
        """
        Establece el concepto general del personaje.
        
        El concepto es texto libre que describe la idea del personaje.
        """
        if "meta" not in self.pj:
            self.pj["meta"] = {}
        self.pj["meta"]["concepto"] = concepto
    
    def establecer_raza(self, id_raza: str) -> bool:
        """
        Establece la raza del personaje.
        
        Args:
            id_raza: ID de la raza (ej: "enano_montanas", "elfo_alto")
            
        Returns:
            True si la raza es válida
        """
        raza = compendio_pj.obtener_raza(id_raza)
        if not raza:
            return False
        
        self.pj["info_basica"]["raza"] = id_raza
        
        # Determinar si tiene subraza
        raza_base = raza.get("raza_base")
        if raza_base and raza_base != id_raza:
            self.pj["info_basica"]["subraza"] = id_raza
        
        # Copiar rasgos raciales
        self.pj["rasgos"]["raciales"] = raza.get("rasgos", []).copy()
        
        # Establecer idiomas
        self.pj["competencias"]["idiomas"] = raza.get("idiomas", ["comun"]).copy()
        
        # Competencias de armas raciales
        comp_armas = raza.get("competencias_armas", [])
        if comp_armas:
            self.pj["competencias"]["armas"].extend(comp_armas)
        
        # Competencias de armaduras raciales
        comp_arm = raza.get("competencias_armaduras", [])
        if comp_arm:
            self.pj["competencias"]["armaduras"].extend(comp_arm)
        
        # Competencias de habilidades raciales
        comp_hab = raza.get("competencias_habilidades", [])
        if comp_hab:
            for h in comp_hab:
                if h not in self.pj["competencias"]["habilidades"]:
                    self.pj["competencias"]["habilidades"].append(h)
                    self.pj["competencias"]["habilidades_origen"][h] = "raza"
        
        self._guardar_progreso()
        return True
    
    def establecer_clase(self, id_clase: str) -> bool:
        """
        Establece la clase del personaje.
        
        Args:
            id_clase: ID de la clase (ej: "guerrero", "mago")
            
        Returns:
            True si la clase es válida
        """
        clase = compendio_pj.obtener_clase(id_clase)
        if not clase:
            return False
        
        self.pj["info_basica"]["clase"] = id_clase
        
        # Competencias de salvación
        self.pj["competencias"]["salvaciones"] = clase.get("salvaciones", []).copy()
        
        # Competencias de armaduras
        comp_arm = clase.get("competencias", {}).get("armaduras", [])
        for arm in comp_arm:
            if arm not in self.pj["competencias"]["armaduras"]:
                self.pj["competencias"]["armaduras"].append(arm)
        
        # Competencias de armas
        comp_armas = clase.get("competencias", {}).get("armas", [])
        for arma in comp_armas:
            if arma not in self.pj["competencias"]["armas"]:
                self.pj["competencias"]["armas"].append(arma)
        
        # Competencias de herramientas
        comp_herr = clase.get("competencias", {}).get("herramientas", [])
        self.pj["competencias"]["herramientas"].extend(comp_herr)
        
        self._guardar_progreso()
        return True
    
    def establecer_caracteristicas(
        self, 
        asignacion: Dict[str, int],
        bonificadores_elegidos: Dict[str, int] = None
    ) -> bool:
        """
        Establece las características del personaje.
        
        Args:
            asignacion: Diccionario {caracteristica: valor} con Standard Array
            bonificadores_elegidos: Para razas con elección (semielfo)
            
        Returns:
            True si la asignación es válida
        """
        bonificadores_elegidos = bonificadores_elegidos or {}
        
        # Validar que usa Standard Array
        valores = sorted(asignacion.values(), reverse=True)
        if valores != sorted(compendio_pj.STANDARD_ARRAY, reverse=True):
            return False
        
        # Aplicar bonificadores raciales
        id_raza = self.pj["info_basica"].get("raza", "")
        caracteristicas = aplicar_bonificadores_raza(
            asignacion, 
            id_raza,
            bonificadores_elegidos
        )
        
        self.pj["caracteristicas"] = caracteristicas
        self._guardar_progreso()
        return True
    
    def establecer_caracteristicas_sugeridas(self) -> Dict[str, int]:
        """
        Establece características usando la distribución sugerida para la clase.
        
        Returns:
            Las características asignadas
        """
        id_clase = self.pj["info_basica"].get("clase", "guerrero")
        orden = compendio_pj.obtener_sugerencia_atributos_clase(id_clase)
        
        # Si no hay orden, usar por defecto
        if not orden:
            orden = compendio_pj.CARACTERISTICAS
        
        # Asignar Standard Array en orden sugerido
        asignacion = {}
        for i, car in enumerate(orden):
            if i < len(compendio_pj.STANDARD_ARRAY):
                asignacion[car] = compendio_pj.STANDARD_ARRAY[i]
            else:
                asignacion[car] = 8
        
        self.establecer_caracteristicas(asignacion)
        return self.pj["caracteristicas"]
    
    def establecer_habilidades(self, habilidades: List[str]) -> bool:
        """
        Establece las habilidades elegidas.
        
        Args:
            habilidades: Lista de IDs de habilidades elegidas
            
        Returns:
            True si las habilidades son válidas
        """
        id_clase = self.pj["info_basica"].get("clase", "")
        opciones = compendio_pj.obtener_habilidades_elegir_clase(id_clase)
        
        cantidad_requerida = opciones.get("cantidad", 0)
        opciones_validas = opciones.get("opciones", [])
        
        # Validar cantidad
        if len(habilidades) != cantidad_requerida:
            return False
        
        # Validar que todas son válidas
        for hab in habilidades:
            if hab not in opciones_validas:
                return False
        
        # Añadir a competencias (sin duplicar) con origen
        for hab in habilidades:
            if hab not in self.pj["competencias"]["habilidades"]:
                self.pj["competencias"]["habilidades"].append(hab)
                self.pj["competencias"]["habilidades_origen"][hab] = "clase"
        
        self._guardar_progreso()
        return True
    
    def establecer_trasfondo(self, id_trasfondo: str) -> bool:
        """
        Establece el trasfondo del personaje.
        
        Args:
            id_trasfondo: ID del trasfondo
            
        Returns:
            True si el trasfondo es válido
        """
        trasfondo = compendio_pj.obtener_trasfondo(id_trasfondo)
        if not trasfondo:
            return False
        
        self.pj["info_basica"]["trasfondo"] = id_trasfondo
        
        # Competencias del trasfondo
        comp = compendio_pj.obtener_competencias_trasfondo(id_trasfondo)
        
        for hab in comp.get("habilidades", []):
            if hab not in self.pj["competencias"]["habilidades"]:
                self.pj["competencias"]["habilidades"].append(hab)
                self.pj["competencias"]["habilidades_origen"][hab] = "trasfondo"
        
        for herr in comp.get("herramientas", []):
            if herr not in self.pj["competencias"]["herramientas"]:
                self.pj["competencias"]["herramientas"].append(herr)
        
        # Rasgo del trasfondo
        rasgo = compendio_pj.obtener_rasgo_trasfondo(id_trasfondo)
        if rasgo:
            self.pj["rasgos"]["trasfondo"] = [rasgo]
        
        self._guardar_progreso()
        return True
    
    def establecer_personalidad(
        self,
        rasgos: List[str],
        ideales: List[str],
        vinculos: List[str],
        defectos: List[str]
    ):
        """Establece los rasgos de personalidad."""
        self.pj["personalidad"] = {
            "rasgos": rasgos,
            "ideales": ideales,
            "vinculos": vinculos,
            "defectos": defectos,
        }
        self._guardar_progreso()
    
    def establecer_rasgo_clase(self, id_rasgo: str, opcion: str = None) -> bool:
        """
        Establece una opción de rasgo de clase (ej: estilo de combate, dominio).
        
        Args:
            id_rasgo: ID del rasgo (ej: "estilo_combate")
            opcion: Opción elegida (ej: "defensa")
            
        Returns:
            True si se estableció correctamente
        """
        rasgo_entry = {"id": id_rasgo}
        if opcion:
            rasgo_entry["opcion"] = opcion
        
        # Buscar si ya existe y reemplazar
        rasgos_clase = self.pj["rasgos"]["clase"]
        for i, r in enumerate(rasgos_clase):
            if r.get("id") == id_rasgo:
                rasgos_clase[i] = rasgo_entry
                self._guardar_progreso()
                return True
        
        # No existe, añadir
        rasgos_clase.append(rasgo_entry)
        self._guardar_progreso()
        return True
    
    def establecer_equipo_basico(self, id_clase: str):
        """
        Establece el equipo inicial básico según la clase.
        
        Usa opciones por defecto del equipo inicial.
        """
        # Equipo básico por clase
        equipo_por_clase = {
            "guerrero": {
                "armas": [
                    {"id": "espada_larga_1", "compendio_ref": "espada_larga", "nombre": "Espada larga", "equipada": True},
                ],
                "armadura": {"id": "cota_mallas_pesada_1", "compendio_ref": "cota_mallas_pesada", "nombre": "Cota de mallas", "equipada": True},
                "escudo": {"id": "escudo_1", "compendio_ref": "escudo", "nombre": "Escudo", "equipada": True},
            },
            "mago": {
                "armas": [
                    {"id": "baston_1", "compendio_ref": "baston", "nombre": "Bastón", "equipada": True},
                    {"id": "daga_1", "compendio_ref": "daga", "nombre": "Daga", "equipada": False},
                ],
                "armadura": None,
                "escudo": None,
            },
            "picaro": {
                "armas": [
                    {"id": "estoque_1", "compendio_ref": "estoque", "nombre": "Estoque", "equipada": True},
                    {"id": "daga_1", "compendio_ref": "daga", "nombre": "Daga", "equipada": False},
                    {"id": "daga_2", "compendio_ref": "daga", "nombre": "Daga", "equipada": False},
                ],
                "armadura": {"id": "cuero_1", "compendio_ref": "armadura_cuero", "nombre": "Armadura de cuero", "equipada": True},
                "escudo": None,
            },
            "clerigo": {
                "armas": [
                    {"id": "maza_1", "compendio_ref": "maza", "nombre": "Maza", "equipada": True},
                ],
                "armadura": {"id": "escamas_1", "compendio_ref": "cota_escamas", "nombre": "Cota de escamas", "equipada": True},
                "escudo": {"id": "escudo_1", "compendio_ref": "escudo", "nombre": "Escudo", "equipada": True},
            },
        }
        
        equipo = equipo_por_clase.get(id_clase, equipo_por_clase["guerrero"])
        self.pj["equipo"]["armas"] = equipo["armas"]
        self.pj["equipo"]["armadura"] = equipo["armadura"]
        self.pj["equipo"]["escudo"] = equipo["escudo"]
        
        self._guardar_progreso()
    
    def establecer_detalles(
        self,
        nombre: str,
        edad: int = None,
        altura: str = "",
        peso: str = "",
        ojos: str = "",
        cabello: str = "",
        piel: str = "",
        backstory: str = ""
    ):
        """Establece los detalles descriptivos del personaje."""
        self.pj["info_basica"]["nombre"] = nombre
        self.pj["historia"] = {
            "edad": edad,
            "altura": altura,
            "peso": peso,
            "ojos": ojos,
            "cabello": cabello,
            "piel": piel,
            "backstory": backstory,
        }
        self._guardar_progreso()
    
    def finalizar(self) -> dict:
        """
        Finaliza la creación y devuelve el personaje completo.
        
        Recalcula todos los derivados antes de devolver.
        
        Returns:
            Personaje completo con derivados calculados
        """
        # Recalcular derivados
        recalcular_derivados(self.pj)
        
        # Marcar como completado
        if PasoCreacion.RESUMEN.value not in self.pasos_completados:
            self.pasos_completados.append(PasoCreacion.RESUMEN.value)
        
        return self.pj
    
    # =========================================================================
    # MÉTODOS DE CONSULTA
    # =========================================================================
    
    def obtener_opciones_raza(self) -> List[Dict[str, str]]:
        """Obtiene las opciones de raza disponibles."""
        return compendio_pj.listar_razas()
    
    def obtener_opciones_clase(self) -> List[Dict[str, str]]:
        """Obtiene las opciones de clase disponibles."""
        return compendio_pj.listar_clases()
    
    def obtener_opciones_trasfondo(self) -> List[Dict[str, str]]:
        """Obtiene las opciones de trasfondo disponibles."""
        return compendio_pj.listar_trasfondos()
    
    def obtener_opciones_habilidades(self) -> Dict[str, Any]:
        """Obtiene las opciones de habilidades para la clase elegida."""
        id_clase = self.pj["info_basica"].get("clase", "")
        return compendio_pj.obtener_habilidades_elegir_clase(id_clase)
    
    def obtener_opciones_estilo_combate(self) -> List[Dict[str, str]]:
        """Obtiene las opciones de estilo de combate (guerrero)."""
        if self.pj["info_basica"].get("clase") != "guerrero":
            return []
        
        clase = compendio_pj.obtener_clase("guerrero")
        if not clase:
            return []
        
        for rasgo in clase.get("rasgos_nivel_1", []):
            if rasgo.get("id") == "estilo_combate":
                return rasgo.get("opciones", [])
        
        return []
    
    def obtener_opciones_dominio(self) -> List[Dict[str, str]]:
        """Obtiene las opciones de dominio divino (clérigo)."""
        if self.pj["info_basica"].get("clase") != "clerigo":
            return []
        
        clase = compendio_pj.obtener_clase("clerigo")
        if not clase:
            return []
        
        for rasgo in clase.get("rasgos_nivel_1", []):
            if rasgo.get("id") == "dominio_divino":
                return rasgo.get("opciones", [])
        
        return []
    
    def obtener_sugerencias_nombre(self, genero: str = "masculino") -> List[str]:
        """Obtiene nombres sugeridos según la raza."""
        id_raza = self.pj["info_basica"].get("raza", "")
        return compendio_pj.obtener_nombres_raza(id_raza, genero)
    
    def obtener_sugerencias_apellido(self) -> List[str]:
        """Obtiene apellidos/clan sugeridos según la raza."""
        id_raza = self.pj["info_basica"].get("raza", "")
        return compendio_pj.obtener_nombres_familia_raza(id_raza)
    
    def obtener_resumen_parcial(self) -> str:
        """Genera un resumen del personaje en construcción."""
        info = self.pj.get("info_basica", {})
        car = self.pj.get("caracteristicas", {})
        
        lineas = []
        
        if info.get("nombre"):
            lineas.append(f"Nombre: {info['nombre']}")
        
        if info.get("raza"):
            raza = compendio_pj.obtener_raza(info["raza"])
            nombre_raza = raza.get("nombre", info["raza"]) if raza else info["raza"]
            lineas.append(f"Raza: {nombre_raza}")
        
        if info.get("clase"):
            clase = compendio_pj.obtener_clase(info["clase"])
            nombre_clase = clase.get("nombre", info["clase"]) if clase else info["clase"]
            lineas.append(f"Clase: {nombre_clase}")
        
        if info.get("trasfondo"):
            trasfondo = compendio_pj.obtener_trasfondo(info["trasfondo"])
            nombre_trasf = trasfondo.get("nombre", info["trasfondo"]) if trasfondo else info["trasfondo"]
            lineas.append(f"Trasfondo: {nombre_trasf}")
        
        if any(v != 10 for v in car.values()):
            lineas.append("")
            lineas.append("Características:")
            for c in compendio_pj.CARACTERISTICAS:
                val = car.get(c, 10)
                mod = calcular_modificador(val)
                lineas.append(f"  {c.upper()[:3]}: {val} ({mod:+d})")
        
        return "\n".join(lineas) if lineas else "Personaje vacío"


def cargar_creador_desde_autosave(autosave_data: dict) -> CreadorPersonaje:
    """
    Crea un CreadorPersonaje desde datos de autosave.
    
    Args:
        autosave_data: Datos cargados con load_autosave()
        
    Returns:
        Instancia de CreadorPersonaje con el progreso restaurado
    """
    pj = autosave_data.get("pj", {})
    paso_str = autosave_data.get("paso_actual", "concepto")
    pasos_completados = autosave_data.get("pasos_completados", [])
    
    # Convertir string a enum
    try:
        paso = PasoCreacion(paso_str)
    except ValueError:
        paso = PasoCreacion.CONCEPTO
    
    return CreadorPersonaje(
        pj=pj,
        paso_actual=paso,
        pasos_completados=pasos_completados,
    )
