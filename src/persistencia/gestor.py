"""
Gestor de Persistencia
Maneja todas las operaciones de guardado y carga del juego.

Versión: 1.1 (con refinamientos de esquema)
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List


class GestorPersistencia:
    """Gestiona el almacenamiento y recuperación de datos del juego."""

    VERSION_ESQUEMA = "1.1"

    def __init__(self, ruta_base: str = "./saves"):
        """
        Inicializa el gestor de persistencia.

        Args:
            ruta_base: Directorio donde se guardan las partidas.
        """
        self.ruta_base = Path(ruta_base)
        self.ruta_base.mkdir(parents=True, exist_ok=True)
        self._asegurar_indice()

    def _asegurar_indice(self) -> None:
        """Crea el archivo index.json si no existe."""
        ruta_indice = self.ruta_base / "index.json"
        if not ruta_indice.exists():
            indice_inicial = {
                "partidas": [],
                "ultima_partida": None
            }
            self._guardar_json(ruta_indice, indice_inicial)

    def _guardar_json(self, ruta: Path, datos: Dict[str, Any]) -> bool:
        """
        Guarda datos en un archivo JSON.

        Args:
            ruta: Ruta del archivo.
            datos: Diccionario a guardar.

        Returns:
            True si se guardó correctamente, False en caso contrario.
        """
        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error guardando {ruta}: {e}")
            return False

    def _cargar_json(self, ruta: Path) -> Optional[Dict[str, Any]]:
        """
        Carga datos desde un archivo JSON.

        Args:
            ruta: Ruta del archivo.

        Returns:
            Diccionario con los datos o None si hay error.
        """
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error cargando {ruta}: {e}")
            return None

    def _crear_personaje_inicial(self, nombre: str, clase: str) -> Dict[str, Any]:
        """Crea la estructura inicial de un personaje (esquema v1.1)."""
        personaje_id = str(uuid.uuid4())

        return {
            "id": personaje_id,
            "nombre": nombre,
            "jugador": "",

            "_meta": {
                "version_esquema": self.VERSION_ESQUEMA,
                "derivados_calculados_en": None
            },

            "fuente": {
                "atributos_base": {
                    "fuerza": 10,
                    "destreza": 10,
                    "constitucion": 10,
                    "inteligencia": 10,
                    "sabiduria": 10,
                    "carisma": 10
                },
                "raza": {
                    "id": None,
                    "nombre": None,
                    "velocidad_base": 30,
                    "tamaño": "Mediano",
                    "bonificadores_atributo": {
                        "fuerza": 0, "destreza": 0, "constitucion": 0,
                        "inteligencia": 0, "sabiduria": 0, "carisma": 0
                    },
                    "rasgos": []
                },
                "clase": {
                    "id": clase.lower() if clase else None,
                    "nombre": clase,
                    "nivel": 1,
                    "dado_golpe": "d8",
                    "caracteristica_lanzamiento": None
                },
                "subclase": None,
                "trasfondo": {
                    "id": None,
                    "nombre": None,
                    "rasgo_personalidad": "",
                    "ideal": "",
                    "vinculo": "",
                    "defecto": ""
                },
                "competencias": {
                    "habilidades": [],
                    "salvaciones": [],
                    "armas": [],
                    "armaduras": [],
                    "herramientas": [],
                    "idiomas": ["Común"]
                },
                "expertise": [],
                "equipo_equipado": {
                    "armadura_id": None,
                    "escudo_id": None,
                    "arma_principal_id": None,
                    "arma_secundaria_id": None
                },
                "dotes": [],
                "multiclase": None,
                "conjuros_conocidos": [],
                "conjuros_preparados": []
            },

            "derivados": {
                "atributos_finales": {
                    "fuerza": 10, "destreza": 10, "constitucion": 10,
                    "inteligencia": 10, "sabiduria": 10, "carisma": 10
                },
                "modificadores": {
                    "fuerza": 0, "destreza": 0, "constitucion": 0,
                    "inteligencia": 0, "sabiduria": 0, "carisma": 0
                },
                "bonificador_competencia": 2,
                "clase_armadura": 10,
                "iniciativa": 0,
                "velocidad": 30,
                "puntos_golpe_maximo": 8,
                "habilidades": self._crear_habilidades_vacias(),
                "salvaciones": self._crear_salvaciones_vacias(),
                "cd_conjuros": None,
                "bonificador_ataque_conjuros": None
            },

            "estado_actual": {
                "puntos_golpe_actual": 8,
                "puntos_golpe_temporal": 0,
                "condiciones": [],
                "inconsciente": False,
                "estable": True,
                "muerto": False,
                "salvaciones_muerte": {
                    "exitos": 0,
                    "fracasos": 0
                }
            },

            "recursos": {
                "dados_golpe": {"disponibles": 1, "maximo": 1},
                "ranuras_conjuro": {
                    "nivel_1": {"disponibles": 0, "maximo": 0},
                    "nivel_2": {"disponibles": 0, "maximo": 0},
                    "nivel_3": {"disponibles": 0, "maximo": 0},
                    "nivel_4": {"disponibles": 0, "maximo": 0},
                    "nivel_5": {"disponibles": 0, "maximo": 0}
                },
                "experiencia": 0
            },

            "dinero": {"pc": 0, "pp": 0, "pe": 0, "po": 0, "ppt": 0}
        }

    def _crear_habilidades_vacias(self) -> Dict[str, Dict[str, Any]]:
        """Crea el diccionario de habilidades con valores por defecto."""
        habilidades = [
            "acrobacias", "arcanos", "atletismo", "engaño", "historia",
            "interpretacion", "intimidacion", "investigacion", "juego_manos",
            "medicina", "naturaleza", "percepcion", "perspicacia", "persuasion",
            "religion", "sigilo", "supervivencia", "trato_animales"
        ]
        return {
            h: {"modificador_total": 0, "competente": False, "expertise": False}
            for h in habilidades
        }

    def _crear_salvaciones_vacias(self) -> Dict[str, Dict[str, Any]]:
        """Crea el diccionario de salvaciones con valores por defecto."""
        atributos = ["fuerza", "destreza", "constitucion",
                     "inteligencia", "sabiduria", "carisma"]
        return {
            a: {"modificador_total": 0, "competente": False}
            for a in atributos
        }

    def _crear_inventario_inicial(self, personaje_id: str) -> Dict[str, Any]:
        """Crea la estructura inicial del inventario (esquema v1.1)."""
        return {
            "personaje_id": personaje_id,
            "equipado": {
                "armadura": None,
                "escudo": None,
                "arma_principal": None,
                "arma_secundaria": None
            },
            "objetos": [],
            "capacidad_carga": {
                "peso_actual_lb": 0,
                "peso_actual_kg": 0,
                "peso_maximo_lb": None,
                "peso_maximo_kg": None
            }
        }

    def _crear_mundo_inicial(self, partida_id: str, setting: str) -> Dict[str, Any]:
        """Crea la estructura inicial del mundo."""
        return {
            "partida_id": partida_id,
            "setting": {
                "nombre": setting,
                "descripcion": "",
                "tono": "heroico"
            },
            "ubicacion": {
                "region": "",
                "lugar": "",
                "interior": False,
                "descripcion_actual": ""
            },
            "tiempo": {
                "dia": 1,
                "hora": 8,
                "periodo": "mañana",
                "clima": "despejado"
            },
            "modo_juego": "exploracion",
            "aventura_actual": {
                "nombre": None,
                "descripcion": None,
                "objetivo_principal": None,
                "capitulo_actual": None
            },
            "flags": {
                "eventos_completados": [],
                "decisiones_importantes": [],
                "variables_narrativas": {}
            }
        }

    def _crear_combate_inicial(self) -> Dict[str, Any]:
        """Crea la estructura inicial de combate (esquema v1.1)."""
        return {
            "activo": False,
            "combatientes": [],
            "orden_turnos": [],
            "turno_actual": None,
            "ronda": 0,
            "historial_ronda": [],
            "ambiente": {
                "descripcion": "",
                "terreno_dificil": False,
                "cobertura_disponible": False,
                "iluminacion": "brillante"
            }
        }

    def _crear_npcs_inicial(self) -> Dict[str, Any]:
        """Crea la estructura inicial de NPCs (esquema v1.1)."""
        return {"npcs": []}

    def _crear_historial_inicial(self) -> Dict[str, Any]:
        """Crea la estructura inicial del historial (esquema v1.1)."""
        ahora = datetime.now().isoformat()
        return {
            "eventos": [],
            "resumen_ultima_sesion": "",
            "resumen_campana": "",
            "estadisticas_campana": {
                "dias_transcurridos": 1,
                "combates_totales": 0,
                "enemigos_derrotados": 0,
                "npcs_conocidos": 0,
                "muertes_personaje": 0
            },
            "ultima_actualizacion": ahora
        }

    def _crear_meta_inicial(self, partida_id: str, nombre: str) -> Dict[str, Any]:
        """Crea la estructura inicial de metadatos."""
        ahora = datetime.now().isoformat()
        return {
            "partida_id": partida_id,
            "nombre_partida": nombre,
            "version_framework": "1.0.0-alpha",
            "version_esquemas": self.VERSION_ESQUEMA,
            "fecha_creacion": ahora,
            "fecha_ultima_sesion": ahora,
            "estadisticas": {
                "sesiones_jugadas": 0,
                "tiempo_total_minutos": 0,
                "combates_completados": 0,
                "nivel_maximo_alcanzado": 1
            },
            "configuracion_partida": {
                "perfil_llm": "lite",
                "dificultad": "normal",
                "modo_muerte": "normal"
            },
            "notas_jugador": ""
        }

    def crear_partida(self, nombre: str, nombre_personaje: str,
                      clase: str, setting: str) -> Optional[str]:
        """
        Crea una nueva partida con estructura completa.

        Args:
            nombre: Nombre de la partida.
            nombre_personaje: Nombre del personaje jugador.
            clase: Clase del personaje.
            setting: Mundo de D&D elegido.

        Returns:
            ID de la partida creada o None si hay error.
        """
        partida_id = str(uuid.uuid4())
        carpeta = f"save_{partida_id[:8]}"
        ruta_partida = self.ruta_base / carpeta

        try:
            ruta_partida.mkdir(parents=True, exist_ok=True)

            # Crear personaje
            personaje = self._crear_personaje_inicial(nombre_personaje, clase)
            self._guardar_json(ruta_partida / "personaje.json", personaje)

            # Crear inventario
            inventario = self._crear_inventario_inicial(personaje["id"])
            self._guardar_json(ruta_partida / "inventario.json", inventario)

            # Crear mundo
            mundo = self._crear_mundo_inicial(partida_id, setting)
            self._guardar_json(ruta_partida / "mundo.json", mundo)

            # Crear combate
            combate = self._crear_combate_inicial()
            self._guardar_json(ruta_partida / "combate.json", combate)

            # Crear NPCs
            npcs = self._crear_npcs_inicial()
            self._guardar_json(ruta_partida / "npcs.json", npcs)

            # Crear historial
            historial = self._crear_historial_inicial()
            self._guardar_json(ruta_partida / "historial.json", historial)

            # Crear meta
            meta = self._crear_meta_inicial(partida_id, nombre)
            self._guardar_json(ruta_partida / "meta.json", meta)

            # Actualizar índice
            self._agregar_a_indice(
                partida_id, nombre, nombre_personaje,
                clase, 1, setting, carpeta
            )

            return partida_id

        except Exception as e:
            print(f"Error creando partida: {e}")
            return None

    def _agregar_a_indice(self, partida_id: str, nombre: str,
                          personaje: str, clase: str, nivel: int,
                          setting: str, carpeta: str) -> None:
        """Agrega una partida al índice."""
        ruta_indice = self.ruta_base / "index.json"
        indice = self._cargar_json(ruta_indice) or {"partidas": []}

        ahora = datetime.now().isoformat()

        entrada = {
            "id": partida_id,
            "nombre": nombre,
            "personaje": personaje,
            "clase": clase,
            "nivel": nivel,
            "setting": setting,
            "fecha_creacion": ahora,
            "fecha_ultima_sesion": ahora,
            "carpeta": carpeta
        }

        indice["partidas"].append(entrada)
        indice["ultima_partida"] = partida_id

        self._guardar_json(ruta_indice, indice)

    def listar_partidas(self) -> List[Dict[str, Any]]:
        """
        Lista todas las partidas disponibles.

        Returns:
            Lista de diccionarios con información de cada partida.
        """
        ruta_indice = self.ruta_base / "index.json"
        indice = self._cargar_json(ruta_indice)

        if indice and "partidas" in indice:
            return indice["partidas"]
        return []

    def cargar_partida(self, partida_id: str) -> Optional[Dict[str, Any]]:
        """
        Carga todos los datos de una partida.

        Args:
            partida_id: ID de la partida a cargar.

        Returns:
            Diccionario con todos los datos o None si no existe.
        """
        # Buscar carpeta de la partida
        indice = self._cargar_json(self.ruta_base / "index.json")
        if not indice:
            return None

        carpeta = None
        for p in indice.get("partidas", []):
            if p["id"] == partida_id:
                carpeta = p["carpeta"]
                break

        if not carpeta:
            return None

        ruta_partida = self.ruta_base / carpeta

        if not ruta_partida.exists():
            return None

        # Cargar todos los archivos
        datos = {
            "meta": self._cargar_json(ruta_partida / "meta.json"),
            "personaje": self._cargar_json(ruta_partida / "personaje.json"),
            "inventario": self._cargar_json(ruta_partida / "inventario.json"),
            "mundo": self._cargar_json(ruta_partida / "mundo.json"),
            "combate": self._cargar_json(ruta_partida / "combate.json"),
            "npcs": self._cargar_json(ruta_partida / "npcs.json"),
            "historial": self._cargar_json(ruta_partida / "historial.json")
        }

        # Actualizar última sesión
        self._actualizar_ultima_sesion(partida_id, carpeta)

        return datos

    def _actualizar_ultima_sesion(self, partida_id: str, carpeta: str) -> None:
        """Actualiza la fecha de última sesión."""
        ahora = datetime.now().isoformat()

        # Actualizar meta.json
        ruta_meta = self.ruta_base / carpeta / "meta.json"
        meta = self._cargar_json(ruta_meta)
        if meta:
            meta["fecha_ultima_sesion"] = ahora
            self._guardar_json(ruta_meta, meta)

        # Actualizar índice
        ruta_indice = self.ruta_base / "index.json"
        indice = self._cargar_json(ruta_indice)
        if indice:
            for p in indice.get("partidas", []):
                if p["id"] == partida_id:
                    p["fecha_ultima_sesion"] = ahora
                    break
            indice["ultima_partida"] = partida_id
            self._guardar_json(ruta_indice, indice)

    def guardar_archivo(self, partida_id: str,
                        nombre_archivo: str,
                        datos: Dict[str, Any]) -> bool:
        """
        Guarda un archivo específico de una partida.

        Args:
            partida_id: ID de la partida.
            nombre_archivo: Nombre del archivo (sin extensión).
            datos: Datos a guardar.

        Returns:
            True si se guardó correctamente.
        """
        # Buscar carpeta
        indice = self._cargar_json(self.ruta_base / "index.json")
        if not indice:
            return False

        carpeta = None
        for p in indice.get("partidas", []):
            if p["id"] == partida_id:
                carpeta = p["carpeta"]
                break

        if not carpeta:
            return False

        ruta_archivo = self.ruta_base / carpeta / f"{nombre_archivo}.json"
        return self._guardar_json(ruta_archivo, datos)

    def obtener_ultima_partida(self) -> Optional[str]:
        """
        Obtiene el ID de la última partida jugada.

        Returns:
            ID de la partida o None si no hay ninguna.
        """
        indice = self._cargar_json(self.ruta_base / "index.json")
        if indice:
            return indice.get("ultima_partida")
        return None


# Funciones de conveniencia para uso directo
_gestor = None

def obtener_gestor(ruta_base: str = "./saves") -> GestorPersistencia:
    """Obtiene o crea la instancia del gestor."""
    global _gestor
    if _gestor is None:
        _gestor = GestorPersistencia(ruta_base)
    return _gestor
