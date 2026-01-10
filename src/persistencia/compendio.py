"""
Lector del Compendio
Proporciona acceso a los datos de referencia del juego.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List


def _encontrar_raiz_proyecto() -> Path:
    """
    Encuentra el directorio raíz del proyecto.
    
    Busca hacia arriba desde el directorio actual del archivo
    hasta encontrar el directorio 'compendio'.
    """
    # Empezar desde el directorio de este archivo
    directorio = Path(__file__).resolve().parent
    
    # Buscar hacia arriba hasta encontrar 'compendio' como hermano
    for _ in range(5):  # Máximo 5 niveles
        posible_compendio = directorio.parent / "compendio"
        if posible_compendio.exists():
            return directorio.parent
        directorio = directorio.parent
    
    # Fallback: asumir que estamos en el directorio correcto
    return Path.cwd()


# Calcular ruta por defecto al compendio
_PROYECTO_ROOT = _encontrar_raiz_proyecto()
_COMPENDIO_DEFAULT = _PROYECTO_ROOT / "compendio"


class Compendio:
    """Acceso a los datos de referencia del juego (solo lectura)."""

    def __init__(self, ruta_base: Path = None):
        """
        Inicializa el lector del compendio.

        Args:
            ruta_base: Directorio donde están los archivos del compendio.
                       Si es None, usa la ruta por defecto detectada automáticamente.
        """
        self.ruta_base = ruta_base if ruta_base else _COMPENDIO_DEFAULT
        self._cache: Dict[str, Any] = {}

    def _cargar_archivo(self, nombre: str) -> Optional[Dict[str, Any]]:
        """Carga un archivo del compendio (con caché)."""
        if nombre in self._cache:
            return self._cache[nombre]

        ruta = self.ruta_base / f"{nombre}.json"
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                self._cache[nombre] = datos
                return datos
        except FileNotFoundError:
            print(f"Archivo de compendio no encontrado: {ruta}")
            return None
        except Exception as e:
            print(f"Error cargando compendio {nombre}: {e}")
            return None

    def obtener_monstruo(self, id_monstruo: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos de un monstruo por su ID.

        Args:
            id_monstruo: Identificador del monstruo (ej: "goblin").

        Returns:
            Diccionario con los datos del monstruo o None.
        """
        datos = self._cargar_archivo("monstruos")
        if datos:
            for m in datos.get("monstruos", []):
                if m.get("id") == id_monstruo:
                    return m
        return None

    def listar_monstruos(self) -> List[Dict[str, Any]]:
        """Lista todos los monstruos disponibles."""
        datos = self._cargar_archivo("monstruos")
        if datos:
            return datos.get("monstruos", [])
        return []

    def obtener_arma(self, id_arma: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos de un arma por su ID.

        Args:
            id_arma: Identificador del arma (ej: "espada_larga").

        Returns:
            Diccionario con los datos del arma o None.
        """
        datos = self._cargar_archivo("armas")
        if datos:
            for a in datos.get("armas", []):
                if a.get("id") == id_arma:
                    return a
        return None

    def listar_armas(self) -> List[Dict[str, Any]]:
        """Lista todas las armas disponibles."""
        datos = self._cargar_archivo("armas")
        if datos:
            return datos.get("armas", [])
        return []

    def obtener_armadura(self, id_armadura: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos de una armadura por su ID.

        Args:
            id_armadura: Identificador de la armadura.

        Returns:
            Diccionario con los datos de la armadura o None.
        """
        datos = self._cargar_archivo("armaduras_escudos")
        if datos:
            for a in datos.get("armaduras", []):
                if a.get("id") == id_armadura:
                    return a
        return None

    def obtener_escudo(self, id_escudo: str) -> Optional[Dict[str, Any]]:
        """Obtiene los datos de un escudo por su ID."""
        datos = self._cargar_archivo("armaduras_escudos")
        if datos:
            for e in datos.get("escudos", []):
                if e.get("id") == id_escudo:
                    return e
        return None

    def listar_armaduras(self) -> List[Dict[str, Any]]:
        """Lista todas las armaduras disponibles."""
        datos = self._cargar_archivo("armaduras_escudos")
        if datos:
            return datos.get("armaduras", [])
        return []

    def obtener_conjuro(self, id_conjuro: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos de un conjuro por su ID.

        Args:
            id_conjuro: Identificador del conjuro.

        Returns:
            Diccionario con los datos del conjuro o None.
        """
        datos = self._cargar_archivo("conjuros")
        if datos:
            for c in datos.get("conjuros", []):
                if c.get("id") == id_conjuro:
                    return c
        return None

    def listar_conjuros(self, nivel: Optional[int] = None,
                        clase: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista conjuros, opcionalmente filtrados.

        Args:
            nivel: Filtrar por nivel de conjuro.
            clase: Filtrar por clase que puede usarlo.

        Returns:
            Lista de conjuros que cumplen los criterios.
        """
        datos = self._cargar_archivo("conjuros")
        if not datos:
            return []

        conjuros = datos.get("conjuros", [])

        if nivel is not None:
            conjuros = [c for c in conjuros if c.get("nivel") == nivel]

        if clase:
            conjuros = [c for c in conjuros
                       if clase in c.get("clases", [])]

        return conjuros

    def obtener_objeto(self, id_objeto: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos de un objeto misceláneo por su ID.

        Args:
            id_objeto: Identificador del objeto.

        Returns:
            Diccionario con los datos del objeto o None.
        """
        datos = self._cargar_archivo("miscelanea")
        if datos:
            for o in datos.get("objetos", []):
                if o.get("id") == id_objeto:
                    return o
        return None

    def listar_objetos(self, categoria: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista objetos misceláneos, opcionalmente filtrados por categoría.

        Args:
            categoria: Filtrar por categoría (consumible, equipo, etc.).

        Returns:
            Lista de objetos.
        """
        datos = self._cargar_archivo("miscelanea")
        if not datos:
            return []

        objetos = datos.get("objetos", [])

        if categoria:
            objetos = [o for o in objetos
                      if o.get("categoria") == categoria]

        return objetos

    def buscar(self, termino: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Busca un término en todo el compendio.

        Args:
            termino: Texto a buscar (en nombres).

        Returns:
            Diccionario con resultados por categoría.
        """
        termino = termino.lower()
        resultados = {
            "monstruos": [],
            "armas": [],
            "armaduras": [],
            "conjuros": [],
            "objetos": []
        }

        for m in self.listar_monstruos():
            if termino in m.get("nombre", "").lower():
                resultados["monstruos"].append(m)

        for a in self.listar_armas():
            if termino in a.get("nombre", "").lower():
                resultados["armas"].append(a)

        for a in self.listar_armaduras():
            if termino in a.get("nombre", "").lower():
                resultados["armaduras"].append(a)

        for c in self.listar_conjuros():
            if termino in c.get("nombre", "").lower():
                resultados["conjuros"].append(c)

        for o in self.listar_objetos():
            if termino in o.get("nombre", "").lower():
                resultados["objetos"].append(o)

        return resultados


# Instancia global para uso directo
_compendio = None

def obtener_compendio(ruta_base: Path = None) -> Compendio:
    """Obtiene o crea la instancia del compendio."""
    global _compendio
    if _compendio is None:
        _compendio = Compendio(ruta_base)
    return _compendio
