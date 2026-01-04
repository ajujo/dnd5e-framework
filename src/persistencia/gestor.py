"""
Gestor de Persistencia
Maneja todas las operaciones de guardado y carga del juego.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List


class GestorPersistencia:
    """Gestiona el almacenamiento y recuperación de datos del juego."""

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

    def crear_partida(self, nombre: str, nombre_personaje: str,
                      clase: str, setting: str) -> Optional[str]:
        """
        Crea una nueva partida con estructura vacía.

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

            ahora = datetime.now().isoformat()

            # Crear meta.json
            meta = {
                "partida_id": partida_id,
                "nombre_partida": nombre,
                "version_framework": "1.0.0-alpha",
                "version_esquemas": "1.0",
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
            self._guardar_json(ruta_partida / "meta.json", meta)

            # Crear personaje.json (esqueleto)
            personaje = {
                "id": str(uuid.uuid4()),
                "nombre": nombre_personaje,
                "jugador": "",
                "raza": {},
                "clase": {"nombre": clase, "nivel": 1},
                "trasfondo": {},
                "atributos": {},
                "estadisticas_derivadas": {},
                "habilidades": {},
                "estados": {
                    "inconsciente": False,
                    "estable": True,
                    "muerto": False,
                    "condiciones": []
                },
                "recursos": {},
                "dinero": {"pc": 0, "pp": 0, "pe": 0, "po": 0, "ppt": 0}
            }
            self._guardar_json(ruta_partida / "personaje.json", personaje)

            # Crear inventario.json
            inventario = {
                "personaje_id": personaje["id"],
                "equipado": {
                    "armadura": None,
                    "escudo": None,
                    "arma_principal": None,
                    "arma_secundaria": None
                },
                "objetos": [],
                "capacidad_carga": {"peso_actual": 0, "peso_maximo": 150}
            }
            self._guardar_json(ruta_partida / "inventario.json", inventario)

            # Crear mundo.json
            mundo = {
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
            self._guardar_json(ruta_partida / "mundo.json", mundo)

            # Crear combate.json
            combate = {
                "activo": False,
                "combatientes": [],
                "orden_turnos": [],
                "turno_actual": None,
                "ronda": 0,
                "historial_ronda": [],
                "ambiente": {}
            }
            self._guardar_json(ruta_partida / "combate.json", combate)

            # Crear npcs.json
            npcs = {"npcs": []}
            self._guardar_json(ruta_partida / "npcs.json", npcs)

            # Crear historial.json
            historial = {
                "eventos": [],
                "resumen_campana": "",
                "ultima_actualizacion": ahora
            }
            self._guardar_json(ruta_partida / "historial.json", historial)

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
