"""
Interfaz del Motor con el Compendio

Este módulo proporciona acceso del motor de reglas al compendio de datos.
Actúa como adaptador de datos, NO como motor de reglas.

RESPONSABILIDADES:
✓ Delegar consultas al compendio
✓ Crear instancias con UUID único
✓ Extraer datos básicos (sin interpretarlos)

NO HACE (eso va en reglas_basicas.py o combate_utils.py):
✗ Calcular escalado de conjuros
✗ Decidir qué atributo usa un arma
✗ Interpretar efectos o reglas
"""

import uuid
from typing import Dict, List, Optional, Any

# Import normal desde src/ (no sys.path.insert)
from persistencia import obtener_compendio


class CompendioMotor:
    """
    Adaptador del motor para acceder al compendio.

    Proporciona:
    - Consultas delegadas al compendio
    - Verificación de existencia
    - Creación de instancias para combate/inventario
    """

    def __init__(self, compendio=None):
        """
        Inicializa la conexión con el compendio.

        Args:
            compendio: Instancia de Compendio opcional (para testing/mocking).
                       Si es None, usa el compendio por defecto.
        """
        self._compendio = compendio if compendio is not None else obtener_compendio()

    # =========================================================================
    # MONSTRUOS
    # =========================================================================

    def obtener_monstruo(self, monstruo_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene los datos de un monstruo del compendio."""
        return self._compendio.obtener_monstruo(monstruo_id)

    def existe_monstruo(self, monstruo_id: str) -> bool:
        """Verifica si un monstruo existe en el compendio."""
        return self.obtener_monstruo(monstruo_id) is not None

    def listar_monstruos(self) -> List[Dict[str, Any]]:
        """Lista todos los monstruos disponibles."""
        return self._compendio.listar_monstruos()

    def crear_instancia_monstruo(self, monstruo_id: str,
                                  nombre_personalizado: str = None) -> Optional[Dict[str, Any]]:
        """
        Crea una instancia de monstruo para usar en combate.

        Genera un instancia_id único y copia los datos relevantes.
        NO interpreta reglas, solo crea la estructura.
        """
        datos = self.obtener_monstruo(monstruo_id)
        if datos is None:
            return None

        return {
            "instancia_id": str(uuid.uuid4()),
            "compendio_ref": monstruo_id,
            "categoria": "monstruo",
            "nombre": nombre_personalizado or datos["nombre"],
            "tipo": "enemigo",
            "puntos_golpe_maximo": datos["puntos_golpe"],
            "puntos_golpe_actual": datos["puntos_golpe"],
            "clase_armadura": datos["clase_armadura"],
            "atributos": datos["atributos"].copy(),
            "acciones": [a.copy() for a in datos.get("acciones", [])],
            "rasgos": datos.get("rasgos", []).copy(),
            "velocidad": datos.get("velocidad", 30),
            "condiciones": [],
            "es_su_turno": False
        }

    # =========================================================================
    # ARMAS
    # =========================================================================

    def obtener_arma(self, arma_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene los datos de un arma del compendio."""
        return self._compendio.obtener_arma(arma_id)

    def existe_arma(self, arma_id: str) -> bool:
        """Verifica si un arma existe en el compendio."""
        return self.obtener_arma(arma_id) is not None

    # =========================================================================
    # OBJETOS MISCELÁNEOS
    # =========================================================================

    def obtener_objeto_misc(self, objeto_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene los datos de un objeto misceláneo del compendio."""
        # Intentar obtener de objetos si existe el método
        if hasattr(self._compendio, 'obtener_objeto'):
            return self._compendio.obtener_objeto(objeto_id)
        return None
    
    def obtener_armadura(self, armadura_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene los datos de una armadura del compendio."""
        if hasattr(self._compendio, 'obtener_armadura'):
            return self._compendio.obtener_armadura(armadura_id)
        return None

    def listar_armas(self) -> List[Dict[str, Any]]:
        """Lista todas las armas disponibles."""
        return self._compendio.listar_armas()

    def crear_instancia_arma(self, arma_id: str) -> Optional[Dict[str, Any]]:
        """Crea una instancia de arma para el inventario."""
        datos = self.obtener_arma(arma_id)
        if datos is None:
            return None

        return {
            "instancia_id": str(uuid.uuid4()),
            "compendio_ref": arma_id,
            "categoria": "arma",
            "nombre": datos["nombre"],
            "cantidad": 1,
            "peso_unitario_lb": datos.get("peso", 0),
            "is_magical": datos.get("is_magical", False),
            "descripcion": datos.get("descripcion", ""),
            "propiedades": {
                "daño": datos["daño"],
                "tipo_daño": datos["tipo_daño"],
                "propiedades_arma": datos.get("propiedades", []),
                "categoria_arma": datos.get("categoria", ""),
                "bonificador_magico": None
            }
        }

    def obtener_daño_arma(self, arma_id: str) -> Optional[Dict[str, str]]:
        """Obtiene solo daño y tipo_daño de un arma."""
        arma = self.obtener_arma(arma_id)
        if arma is None:
            return None

        return {
            "daño": arma["daño"],
            "tipo_daño": arma["tipo_daño"]
        }

    def obtener_propiedades_arma(self, arma_id: str) -> List[str]:
        """Obtiene la lista de propiedades de un arma."""
        arma = self.obtener_arma(arma_id)
        if arma is None:
            return []
        return arma.get("propiedades", [])

    # =========================================================================
    # ARMADURAS Y ESCUDOS
    # =========================================================================

    def obtener_armadura(self, armadura_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene los datos de una armadura del compendio."""
        return self._compendio.obtener_armadura(armadura_id)

    def existe_armadura(self, armadura_id: str) -> bool:
        """Verifica si una armadura existe en el compendio."""
        return self.obtener_armadura(armadura_id) is not None

    def listar_armaduras(self) -> List[Dict[str, Any]]:
        """Lista todas las armaduras disponibles."""
        return self._compendio.listar_armaduras()

    def obtener_escudo(self) -> Optional[Dict[str, Any]]:
        """Obtiene los datos del escudo."""
        return self._compendio.obtener_escudo("escudo")

    def crear_instancia_armadura(self, armadura_id: str) -> Optional[Dict[str, Any]]:
        """Crea una instancia de armadura para el inventario."""
        datos = self.obtener_armadura(armadura_id)
        if datos is None:
            return None

        return {
            "instancia_id": str(uuid.uuid4()),
            "compendio_ref": armadura_id,
            "categoria": "armadura",
            "nombre": datos["nombre"],
            "cantidad": 1,
            "peso_unitario_lb": datos.get("peso", 0),
            "is_magical": datos.get("is_magical", False),
            "descripcion": datos.get("descripcion", ""),
            "propiedades": {
                "ca_base": datos["ca_base"],
                "max_mod_destreza": datos.get("max_mod_destreza"),
                "requisito_fuerza": datos.get("requisito_fuerza"),
                "desventaja_sigilo": datos.get("desventaja_sigilo", False),
                "tipo_armadura": datos.get("tipo", ""),
                "bonificador_magico": None
            }
        }

    def obtener_ca_armadura(self, armadura_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene la información de CA de una armadura."""
        armadura = self.obtener_armadura(armadura_id)
        if armadura is None:
            return None

        return {
            "ca_base": armadura["ca_base"],
            "max_mod_destreza": armadura.get("max_mod_destreza"),
            "requisito_fuerza": armadura.get("requisito_fuerza"),
            "desventaja_sigilo": armadura.get("desventaja_sigilo", False)
        }

    # =========================================================================
    # CONJUROS
    # =========================================================================

    def obtener_conjuro(self, conjuro_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene los datos de un conjuro del compendio."""
        return self._compendio.obtener_conjuro(conjuro_id)

    def existe_conjuro(self, conjuro_id: str) -> bool:
        """Verifica si un conjuro existe en el compendio."""
        return self.obtener_conjuro(conjuro_id) is not None

    def listar_conjuros(self, nivel: int = None,
                        clase: str = None) -> List[Dict[str, Any]]:
        """Lista conjuros, opcionalmente filtrados."""
        return self._compendio.listar_conjuros(nivel=nivel, clase=clase)

    # NOTA: El escalado de daño de conjuros es LÓGICA DE REGLAS
    # y debe hacerse en combate_utils.py, no aquí.

    def obtener_daño_conjuro_base(self, conjuro_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el daño BASE de un conjuro (sin escalado).

        El escalado es lógica de reglas y se hace en combate_utils.py
        """
        conjuro = self.obtener_conjuro(conjuro_id)
        if conjuro is None or "daño" not in conjuro:
            return None

        return {
            "daño": conjuro["daño"],
            "tipo_daño": conjuro.get("tipo_daño", ""),
            "nivel_base": conjuro.get("nivel", 0),
            "escalado": conjuro.get("escalado", None)
        }

    # =========================================================================
    # OBJETOS MISCELÁNEOS
    # =========================================================================

    def obtener_objeto(self, objeto_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene los datos de un objeto del compendio."""
        return self._compendio.obtener_objeto(objeto_id)

    def existe_objeto(self, objeto_id: str) -> bool:
        """Verifica si un objeto existe en el compendio."""
        return self.obtener_objeto(objeto_id) is not None

    def listar_objetos(self, categoria: str = None) -> List[Dict[str, Any]]:
        """Lista objetos, opcionalmente por categoría."""
        return self._compendio.listar_objetos(categoria=categoria)

    def crear_instancia_objeto(self, objeto_id: str,
                                cantidad: int = 1) -> Optional[Dict[str, Any]]:
        """Crea una instancia de objeto para el inventario."""
        datos = self.obtener_objeto(objeto_id)
        if datos is None:
            return None

        return {
            "instancia_id": str(uuid.uuid4()),
            "compendio_ref": objeto_id,
            "categoria": datos.get("categoria", "miscelanea"),
            "nombre": datos["nombre"],
            "cantidad": cantidad,
            "peso_unitario_lb": datos.get("peso", 0),
            "is_magical": datos.get("is_magical", False),
            "descripcion": datos.get("descripcion", ""),
            "propiedades": datos.get("propiedades", {})
        }

    # =========================================================================
    # BÚSQUEDA GENERAL
    # =========================================================================

    def buscar(self, termino: str) -> Dict[str, List[Dict[str, Any]]]:
        """Busca en todo el compendio."""
        return self._compendio.buscar(termino)

    def existe(self, item_id: str) -> bool:
        """Verifica si un ID existe en cualquier categoría."""
        return (
            self.existe_monstruo(item_id) or
            self.existe_arma(item_id) or
            self.existe_armadura(item_id) or
            self.existe_conjuro(item_id) or
            self.existe_objeto(item_id)
        )

    def obtener_cualquiera(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un item de cualquier categoría."""
        if self.existe_monstruo(item_id):
            return {"categoria": "monstruo", "datos": self.obtener_monstruo(item_id)}
        if self.existe_arma(item_id):
            return {"categoria": "arma", "datos": self.obtener_arma(item_id)}
        if self.existe_armadura(item_id):
            return {"categoria": "armadura", "datos": self.obtener_armadura(item_id)}
        if self.existe_conjuro(item_id):
            return {"categoria": "conjuro", "datos": self.obtener_conjuro(item_id)}
        if self.existe_objeto(item_id):
            return {"categoria": "objeto", "datos": self.obtener_objeto(item_id)}
        return None


# =============================================================================
# INSTANCIA GLOBAL
# =============================================================================

_compendio_motor = None

def obtener_compendio_motor(compendio=None) -> CompendioMotor:
    """
    Obtiene o crea la instancia global del compendio del motor.

    Args:
        compendio: Compendio opcional para inyección (testing).
    """
    global _compendio_motor
    if _compendio_motor is None or compendio is not None:
        _compendio_motor = CompendioMotor(compendio)
    return _compendio_motor


def resetear_compendio_motor():
    """Resetea la instancia global (útil para tests)."""
    global _compendio_motor
    _compendio_motor = None
