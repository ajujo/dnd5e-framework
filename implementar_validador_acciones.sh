#!/bin/bash

# =============================================================================
# TAREA 3.3: Validador de Acciones
# Ejecutar desde la raíz del proyecto: bash implementar_validador_acciones.sh
# =============================================================================

set -e

echo "=============================================="
echo "  TAREA 3.3: Validador de Acciones"
echo "=============================================="
echo ""

# -----------------------------------------------------------------------------
# 1. Crear src/motor/validador.py
# -----------------------------------------------------------------------------
echo "→ Creando src/motor/validador.py..."

cat > src/motor/validador.py << 'EOF'
"""
Validador de Acciones para D&D 5e

Este módulo valida si una acción es posible dado el estado actual del juego.
NO ejecuta las acciones, solo dice si son válidas y por qué no.

PATRÓN: Inyección de dependencias
- Recibe CompendioMotor por constructor
- NUNCA llama a obtener_compendio_motor()

Responsabilidades:
✓ Validar que una acción es posible
✓ Explicar por qué no es posible
✓ Verificar requisitos (recursos, estado, equipo)

NO hace:
✗ Ejecutar acciones
✗ Modificar estado
✗ Tirar dados
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Import del tipo (no de la instancia global)
from .compendio import CompendioMotor


class TipoAccion(Enum):
    """Tipos de acción en D&D 5e."""
    ATAQUE = "ataque"
    CONJURO = "conjuro"
    HABILIDAD = "habilidad"
    MOVIMIENTO = "movimiento"
    OBJETO = "objeto"
    DASH = "dash"
    DISENGAGE = "disengage"
    DODGE = "dodge"
    HELP = "help"
    HIDE = "hide"
    READY = "ready"
    SEARCH = "search"


@dataclass
class ResultadoValidacion:
    """
    Resultado de validar una acción.

    Attributes:
        valido: True si la acción es posible.
        razon: Explicación (por qué no es válido, o confirmación).
        advertencias: Cosas que el jugador debería saber.
        datos_extra: Info adicional para el motor.
    """
    valido: bool
    razon: str
    advertencias: List[str] = None
    datos_extra: Dict[str, Any] = None

    def __post_init__(self):
        if self.advertencias is None:
            self.advertencias = []
        if self.datos_extra is None:
            self.datos_extra = {}

    def __str__(self) -> str:
        estado = "✓ Válido" if self.valido else "✗ Inválido"
        resultado = f"{estado}: {self.razon}"
        if self.advertencias:
            resultado += f"\n  Advertencias: {', '.join(self.advertencias)}"
        return resultado


class ValidadorAcciones:
    """
    Valida si las acciones son posibles.

    IMPORTANTE: Recibe CompendioMotor por inyección.
    No usa singleton ni estado global.
    """

    def __init__(self, compendio_motor: CompendioMotor):
        """
        Inicializa el validador.

        Args:
            compendio_motor: Instancia de CompendioMotor (inyectada).
        """
        self._compendio = compendio_motor

    # =========================================================================
    # VALIDACIÓN DE ATAQUES
    # =========================================================================

    def validar_ataque(self,
                       atacante: Dict[str, Any],
                       objetivo: Dict[str, Any],
                       arma_id: str = None) -> ResultadoValidacion:
        """
        Valida si un ataque es posible.

        Args:
            atacante: Datos del personaje/monstruo que ataca.
            objetivo: Datos del objetivo.
            arma_id: ID del arma a usar (None = ataque desarmado).

        Returns:
            ResultadoValidacion indicando si el ataque es válido.
        """
        advertencias = []

        # 1. Verificar que el atacante puede actuar
        validacion_estado = self._verificar_puede_actuar(atacante)
        if not validacion_estado.valido:
            return validacion_estado

        # 2. Verificar que el objetivo es válido
        if objetivo is None:
            return ResultadoValidacion(
                valido=False,
                razon="No hay objetivo seleccionado"
            )

        # Verificar que el objetivo no está muerto
        if objetivo.get("estado_actual", {}).get("muerto", False):
            return ResultadoValidacion(
                valido=False,
                razon=f"{objetivo.get('nombre', 'El objetivo')} ya está muerto"
            )

        # 3. Verificar arma si se especifica
        if arma_id:
            arma = self._compendio.obtener_arma(arma_id)
            if arma is None:
                return ResultadoValidacion(
                    valido=False,
                    razon=f"Arma '{arma_id}' no existe en el compendio"
                )

            # Verificar si tiene el arma equipada (si hay datos de equipo)
            equipo = atacante.get("fuente", {}).get("equipo_equipado", {})
            arma_principal = equipo.get("arma_principal_id")
            arma_secundaria = equipo.get("arma_secundaria_id")

            if arma_id not in [arma_principal, arma_secundaria]:
                advertencias.append(f"'{arma['nombre']}' no está equipada")

        # 4. Verificar alcance (simplificado para V1)
        # TODO: Implementar cálculo de distancia real

        return ResultadoValidacion(
            valido=True,
            razon=f"Ataque válido contra {objetivo.get('nombre', 'objetivo')}",
            advertencias=advertencias,
            datos_extra={
                "arma_id": arma_id,
                "tipo_ataque": "cuerpo a cuerpo" if arma_id is None else "con arma"
            }
        )

    # =========================================================================
    # VALIDACIÓN DE CONJUROS
    # =========================================================================

    def validar_conjuro(self,
                        lanzador: Dict[str, Any],
                        conjuro_id: str,
                        nivel_ranura: int = None,
                        objetivo: Dict[str, Any] = None) -> ResultadoValidacion:
        """
        Valida si se puede lanzar un conjuro.

        Args:
            lanzador: Datos del personaje que lanza.
            conjuro_id: ID del conjuro a lanzar.
            nivel_ranura: Nivel de ranura a usar (None = nivel base).
            objetivo: Objetivo del conjuro (si requiere).

        Returns:
            ResultadoValidacion indicando si el lanzamiento es válido.
        """
        advertencias = []

        # 1. Verificar que puede actuar
        validacion_estado = self._verificar_puede_actuar(lanzador)
        if not validacion_estado.valido:
            return validacion_estado

        # 2. Verificar que el conjuro existe
        conjuro = self._compendio.obtener_conjuro(conjuro_id)
        if conjuro is None:
            return ResultadoValidacion(
                valido=False,
                razon=f"Conjuro '{conjuro_id}' no existe en el compendio"
            )

        # 3. Verificar que conoce el conjuro
        conjuros_conocidos = lanzador.get("fuente", {}).get("conjuros_conocidos", [])
        conjuros_preparados = lanzador.get("fuente", {}).get("conjuros_preparados", [])

        if conjuro_id not in conjuros_conocidos and conjuro_id not in conjuros_preparados:
            # Advertencia, no bloqueo (el DM puede permitirlo)
            advertencias.append(f"'{conjuro['nombre']}' no está en conjuros conocidos/preparados")

        # 4. Verificar nivel de ranura
        nivel_conjuro = conjuro.get("nivel", 0)

        if nivel_conjuro == 0:
            # Truco: no gasta ranura
            pass
        else:
            # Conjuro con nivel: necesita ranura
            nivel_usar = nivel_ranura if nivel_ranura else nivel_conjuro

            if nivel_usar < nivel_conjuro:
                return ResultadoValidacion(
                    valido=False,
                    razon=f"'{conjuro['nombre']}' es nivel {nivel_conjuro}, no puede lanzarse con ranura de nivel {nivel_usar}"
                )

            # Verificar ranuras disponibles
            recursos = lanzador.get("recursos", {})
            ranuras = recursos.get("ranuras_conjuro", {})
            ranura_key = f"nivel_{nivel_usar}"
            ranura_info = ranuras.get(ranura_key, {"disponibles": 0, "maximo": 0})

            if ranura_info.get("disponibles", 0) <= 0:
                return ResultadoValidacion(
                    valido=False,
                    razon=f"No quedan ranuras de nivel {nivel_usar} disponibles"
                )

        # 5. Verificar objetivo si es necesario
        requiere_objetivo = conjuro.get("objetivo", "") not in ["", "personal", "self"]
        if requiere_objetivo and objetivo is None:
            advertencias.append(f"'{conjuro['nombre']}' podría requerir un objetivo")

        return ResultadoValidacion(
            valido=True,
            razon=f"Puede lanzar '{conjuro['nombre']}'",
            advertencias=advertencias,
            datos_extra={
                "conjuro": conjuro,
                "nivel_ranura": nivel_ranura or nivel_conjuro,
                "es_truco": nivel_conjuro == 0
            }
        )

    # =========================================================================
    # VALIDACIÓN DE USO DE OBJETOS
    # =========================================================================

    def validar_uso_objeto(self,
                           usuario: Dict[str, Any],
                           objeto_id: str,
                           instancia_id: str = None) -> ResultadoValidacion:
        """
        Valida si se puede usar un objeto.

        Args:
            usuario: Datos del personaje que usa el objeto.
            objeto_id: ID del objeto en el compendio.
            instancia_id: ID de la instancia específica en inventario.

        Returns:
            ResultadoValidacion indicando si se puede usar.
        """
        # 1. Verificar que puede actuar
        validacion_estado = self._verificar_puede_actuar(usuario)
        if not validacion_estado.valido:
            return validacion_estado

        # 2. Verificar que el objeto existe
        objeto = self._compendio.obtener_objeto(objeto_id)
        if objeto is None:
            return ResultadoValidacion(
                valido=False,
                razon=f"Objeto '{objeto_id}' no existe en el compendio"
            )

        # 3. Verificar que tiene el objeto en inventario (si se pasa instancia)
        # TODO: Integrar con sistema de inventario cuando esté listo

        return ResultadoValidacion(
            valido=True,
            razon=f"Puede usar '{objeto['nombre']}'",
            datos_extra={"objeto": objeto}
        )

    # =========================================================================
    # VALIDACIÓN DE MOVIMIENTO
    # =========================================================================

    def validar_movimiento(self,
                           personaje: Dict[str, Any],
                           distancia: int,
                           movimiento_usado: int = 0) -> ResultadoValidacion:
        """
        Valida si un movimiento es posible.

        Args:
            personaje: Datos del personaje.
            distancia: Distancia a mover (en pies).
            movimiento_usado: Movimiento ya usado este turno.

        Returns:
            ResultadoValidacion indicando si puede moverse.
        """
        # 1. Verificar condiciones que impiden movimiento
        estado = personaje.get("estado_actual", {})
        condiciones = estado.get("condiciones", [])

        condiciones_inmovil = ["paralizado", "petrificado", "aturdido", "inconsciente", "agarrado", "apresado"]
        for cond in condiciones:
            if cond.lower() in condiciones_inmovil:
                return ResultadoValidacion(
                    valido=False,
                    razon=f"No puede moverse: está {cond}"
                )

        # 2. Calcular velocidad
        velocidad = personaje.get("derivados", {}).get("velocidad", 30)
        if "fuente" in personaje:
            velocidad = personaje.get("derivados", {}).get("velocidad",
                        personaje.get("fuente", {}).get("raza", {}).get("velocidad_base", 30))

        # Para monstruos
        if "velocidad" in personaje:
            velocidad = personaje["velocidad"]

        movimiento_restante = velocidad - movimiento_usado

        if distancia > movimiento_restante:
            return ResultadoValidacion(
                valido=False,
                razon=f"No tiene suficiente movimiento: necesita {distancia} pies, le quedan {movimiento_restante} pies"
            )

        # 3. Verificar terreno difícil (TODO: implementar)

        return ResultadoValidacion(
            valido=True,
            razon=f"Puede moverse {distancia} pies (quedarán {movimiento_restante - distancia} pies)",
            datos_extra={
                "velocidad_total": velocidad,
                "movimiento_restante_despues": movimiento_restante - distancia
            }
        )

    # =========================================================================
    # VALIDACIÓN DE HABILIDADES
    # =========================================================================

    def validar_prueba_habilidad(self,
                                  personaje: Dict[str, Any],
                                  habilidad: str) -> ResultadoValidacion:
        """
        Valida si se puede hacer una prueba de habilidad.

        Args:
            personaje: Datos del personaje.
            habilidad: Nombre de la habilidad.

        Returns:
            ResultadoValidacion (casi siempre válido, pero con info).
        """
        habilidades_validas = [
            "acrobacias", "arcanos", "atletismo", "engaño", "historia",
            "interpretacion", "intimidacion", "investigacion", "juego_manos",
            "medicina", "naturaleza", "percepcion", "perspicacia", "persuasion",
            "religion", "sigilo", "supervivencia", "trato_animales"
        ]

        habilidad_lower = habilidad.lower().replace(" ", "_")

        if habilidad_lower not in habilidades_validas:
            return ResultadoValidacion(
                valido=False,
                razon=f"'{habilidad}' no es una habilidad válida",
                datos_extra={"habilidades_validas": habilidades_validas}
            )

        # Verificar condiciones que podrían afectar
        advertencias = []
        estado = personaje.get("estado_actual", {})
        condiciones = estado.get("condiciones", [])

        if "cegado" in condiciones and habilidad_lower == "percepcion":
            advertencias.append("Está cegado: desventaja en Percepción que dependa de la vista")

        if "asustado" in condiciones:
            advertencias.append("Está asustado: desventaja en pruebas mientras vea la fuente del miedo")

        return ResultadoValidacion(
            valido=True,
            razon=f"Puede hacer prueba de {habilidad}",
            advertencias=advertencias
        )

    # =========================================================================
    # HELPERS INTERNOS
    # =========================================================================

    def _verificar_puede_actuar(self, entidad: Dict[str, Any]) -> ResultadoValidacion:
        """
        Verifica si una entidad puede realizar acciones.

        Comprueba condiciones que impiden actuar:
        - Inconsciente
        - Paralizado
        - Petrificado
        - Aturdido
        - Muerto
        """
        nombre = entidad.get("nombre", "La entidad")

        # Para personajes con estructura completa
        estado = entidad.get("estado_actual", {})

        # Para monstruos/instancias de combate
        if "puntos_golpe_actual" in entidad:
            if entidad.get("puntos_golpe_actual", 1) <= 0:
                return ResultadoValidacion(
                    valido=False,
                    razon=f"{nombre} tiene 0 PG"
                )

        if estado.get("muerto", False):
            return ResultadoValidacion(
                valido=False,
                razon=f"{nombre} está muerto"
            )

        if estado.get("inconsciente", False):
            return ResultadoValidacion(
                valido=False,
                razon=f"{nombre} está inconsciente"
            )

        condiciones = entidad.get("condiciones", [])
        if not condiciones:
            condiciones = estado.get("condiciones", [])

        condiciones_incapacitantes = ["paralizado", "petrificado", "aturdido", "incapacitado"]
        for cond in condiciones:
            if cond.lower() in condiciones_incapacitantes:
                return ResultadoValidacion(
                    valido=False,
                    razon=f"{nombre} está {cond} y no puede actuar"
                )

        return ResultadoValidacion(
            valido=True,
            razon=f"{nombre} puede actuar"
        )

    def validar_accion_generica(self,
                                 tipo: TipoAccion,
                                 actor: Dict[str, Any]) -> ResultadoValidacion:
        """
        Valida acciones genéricas (Dash, Disengage, Dodge, etc.).

        Args:
            tipo: Tipo de acción.
            actor: Quien realiza la acción.

        Returns:
            ResultadoValidacion.
        """
        # Verificar que puede actuar
        validacion_estado = self._verificar_puede_actuar(actor)
        if not validacion_estado.valido:
            return validacion_estado

        nombre = actor.get("nombre", "El personaje")

        if tipo == TipoAccion.DASH:
            return ResultadoValidacion(
                valido=True,
                razon=f"{nombre} puede usar Dash (duplica movimiento este turno)"
            )

        if tipo == TipoAccion.DISENGAGE:
            return ResultadoValidacion(
                valido=True,
                razon=f"{nombre} puede usar Disengage (no provoca ataques de oportunidad)"
            )

        if tipo == TipoAccion.DODGE:
            return ResultadoValidacion(
                valido=True,
                razon=f"{nombre} puede usar Dodge (ataques contra él tienen desventaja)"
            )

        if tipo == TipoAccion.HELP:
            return ResultadoValidacion(
                valido=True,
                razon=f"{nombre} puede usar Help (da ventaja a un aliado)"
            )

        if tipo == TipoAccion.HIDE:
            return ResultadoValidacion(
                valido=True,
                razon=f"{nombre} puede intentar Hide (tirada de Sigilo)"
            )

        if tipo == TipoAccion.SEARCH:
            return ResultadoValidacion(
                valido=True,
                razon=f"{nombre} puede usar Search (tirada de Percepción/Investigación)"
            )

        if tipo == TipoAccion.READY:
            return ResultadoValidacion(
                valido=True,
                razon=f"{nombre} puede preparar una acción"
            )

        return ResultadoValidacion(
            valido=True,
            razon=f"{nombre} puede realizar la acción"
        )
EOF

echo "   ✓ validador.py creado"

# -----------------------------------------------------------------------------
# 2. Actualizar src/motor/__init__.py
# -----------------------------------------------------------------------------
echo "→ Actualizando src/motor/__init__.py..."

cat > src/motor/__init__.py << 'EOF'
"""
Motor de Reglas D&D 5e

Este módulo contiene toda la lógica de reglas del juego.

ESTRUCTURA:
- dados.py: Sistema de tiradas genéricas
- reglas_basicas.py: Modificadores, competencia, CA
- combate_utils.py: Ataque, daño, iniciativa, salvaciones
- compendio.py: Interfaz con el compendio de datos
- validador.py: Validación de acciones

PATRÓN DE INYECCIÓN:
- Los módulos internos reciben dependencias por constructor
- obtener_compendio_motor() solo debe usarse en main.py/cli.py
"""

# Desde dados.py
from .dados import (
    rng,
    GestorAleatorio,
    TipoTirada,
    ResultadoTirada,
    DADOS_VALIDOS,
    tirar,
    tirar_dado,
    tirar_dados,
    tirar_ventaja,
    tirar_desventaja,
    parsear_expresion,
)

# Desde reglas_basicas.py
from .reglas_basicas import (
    calcular_modificador,
    obtener_bonificador_competencia,
    calcular_cd_conjuros,
    calcular_bonificador_ataque_conjuros,
    calcular_ca_base,
    calcular_carga_maxima,
)

# Desde combate_utils.py
from .combate_utils import (
    tirar_ataque,
    tirar_daño,
    tirar_salvacion,
    tirar_habilidad,
    tirar_iniciativa,
    tirar_atributos,
    resolver_ataque,
)

# Desde compendio.py
from .compendio import (
    CompendioMotor,
    obtener_compendio_motor,  # Solo para main.py/cli.py
    resetear_compendio_motor,
)

# Desde validador.py
from .validador import (
    ValidadorAcciones,
    TipoAccion,
    ResultadoValidacion,
)

__all__ = [
    # Gestor de aleatoriedad
    'rng',
    'GestorAleatorio',

    # Tipos
    'TipoTirada',
    'ResultadoTirada',
    'DADOS_VALIDOS',

    # Tiradas genéricas
    'tirar',
    'tirar_dado',
    'tirar_dados',
    'tirar_ventaja',
    'tirar_desventaja',
    'parsear_expresion',

    # Reglas básicas
    'calcular_modificador',
    'obtener_bonificador_competencia',
    'calcular_cd_conjuros',
    'calcular_bonificador_ataque_conjuros',
    'calcular_ca_base',
    'calcular_carga_maxima',

    # Combate
    'tirar_ataque',
    'tirar_daño',
    'tirar_salvacion',
    'tirar_habilidad',
    'tirar_iniciativa',
    'tirar_atributos',
    'resolver_ataque',

    # Compendio
    'CompendioMotor',
    'obtener_compendio_motor',
    'resetear_compendio_motor',

    # Validador
    'ValidadorAcciones',
    'TipoAccion',
    'ResultadoValidacion',
]
EOF

echo "   ✓ __init__.py actualizado"

# -----------------------------------------------------------------------------
# 3. Crear tests del validador
# -----------------------------------------------------------------------------
echo "→ Creando tests/test_validador.py..."

cat > tests/test_validador.py << 'EOF'
"""
Tests del validador de acciones.
Ejecutar desde la raíz: python tests/test_validador.py

PATRÓN: Usa inyección de dependencias (CompendioMotor inyectado).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from motor import (
    ValidadorAcciones,
    TipoAccion,
    ResultadoValidacion,
    CompendioMotor
)
from motor.compendio import resetear_compendio_motor


# =============================================================================
# FIXTURES: Datos de prueba
# =============================================================================

def crear_personaje_sano():
    """Crea un personaje en buen estado."""
    return {
        "nombre": "Thorin",
        "fuente": {
            "equipo_equipado": {
                "arma_principal_id": "espada_larga",
                "arma_secundaria_id": None
            },
            "conjuros_conocidos": ["proyectil_magico", "rayo_escarcha"],
            "conjuros_preparados": ["proyectil_magico"]
        },
        "derivados": {
            "velocidad": 30
        },
        "estado_actual": {
            "puntos_golpe_actual": 25,
            "condiciones": [],
            "inconsciente": False,
            "muerto": False
        },
        "recursos": {
            "ranuras_conjuro": {
                "nivel_1": {"disponibles": 2, "maximo": 2},
                "nivel_2": {"disponibles": 1, "maximo": 1}
            }
        }
    }


def crear_personaje_incapacitado():
    """Crea un personaje que no puede actuar."""
    return {
        "nombre": "Elara",
        "estado_actual": {
            "puntos_golpe_actual": 5,
            "condiciones": ["paralizado"],
            "inconsciente": False,
            "muerto": False
        }
    }


def crear_personaje_sin_ranuras():
    """Crea un personaje sin ranuras de conjuro."""
    return {
        "nombre": "Gandor",
        "fuente": {
            "conjuros_conocidos": ["proyectil_magico"],
            "conjuros_preparados": ["proyectil_magico"]
        },
        "estado_actual": {
            "condiciones": [],
            "inconsciente": False,
            "muerto": False
        },
        "recursos": {
            "ranuras_conjuro": {
                "nivel_1": {"disponibles": 0, "maximo": 2}
            }
        }
    }


def crear_monstruo_vivo():
    """Crea un monstruo vivo."""
    return {
        "nombre": "Goblin",
        "puntos_golpe_actual": 7,
        "clase_armadura": 15,
        "condiciones": [],
        "velocidad": 30
    }


def crear_monstruo_muerto():
    """Crea un monstruo muerto."""
    return {
        "nombre": "Goblin Caído",
        "puntos_golpe_actual": 0,
        "estado_actual": {
            "muerto": True
        }
    }


# =============================================================================
# TESTS
# =============================================================================

def test_ataque_basico():
    """Test de validación de ataque básico."""
    print("1. Validación de ataque básico:")

    # Crear validador con compendio inyectado
    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()
    objetivo = crear_monstruo_vivo()

    # Ataque con arma equipada
    resultado = validador.validar_ataque(personaje, objetivo, "espada_larga")
    assert resultado.valido == True
    print(f"   Ataque con espada equipada: {resultado}")

    # Ataque desarmado
    resultado = validador.validar_ataque(personaje, objetivo, None)
    assert resultado.valido == True
    print(f"   Ataque desarmado: {resultado}")

    # Ataque con arma no equipada
    resultado = validador.validar_ataque(personaje, objetivo, "daga")
    assert resultado.valido == True  # Válido pero con advertencia
    assert len(resultado.advertencias) > 0
    print(f"   Ataque con arma no equipada: {resultado}")

    print("   ✓ Ataque básico correcto\n")
    return True


def test_ataque_sin_objetivo():
    """Test de ataque sin objetivo."""
    print("2. Validación de ataque sin objetivo:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()

    resultado = validador.validar_ataque(personaje, None, "espada_larga")
    assert resultado.valido == False
    assert "objetivo" in resultado.razon.lower()
    print(f"   {resultado}")

    print("   ✓ Validación sin objetivo correcta\n")
    return True


def test_ataque_objetivo_muerto():
    """Test de ataque a objetivo muerto."""
    print("3. Validación de ataque a objetivo muerto:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()
    objetivo_muerto = crear_monstruo_muerto()

    resultado = validador.validar_ataque(personaje, objetivo_muerto, "espada_larga")
    assert resultado.valido == False
    assert "muerto" in resultado.razon.lower()
    print(f"   {resultado}")

    print("   ✓ Validación objetivo muerto correcta\n")
    return True


def test_atacante_incapacitado():
    """Test de ataque con atacante incapacitado."""
    print("4. Validación de atacante incapacitado:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje_paralizado = crear_personaje_incapacitado()
    objetivo = crear_monstruo_vivo()

    resultado = validador.validar_ataque(personaje_paralizado, objetivo, None)
    assert resultado.valido == False
    assert "paralizado" in resultado.razon.lower()
    print(f"   {resultado}")

    print("   ✓ Validación atacante incapacitado correcta\n")
    return True


def test_conjuro_valido():
    """Test de lanzamiento de conjuro válido."""
    print("5. Validación de conjuro válido:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()

    # Conjuro conocido con ranuras
    resultado = validador.validar_conjuro(personaje, "proyectil_magico", nivel_ranura=1)
    assert resultado.valido == True
    print(f"   Proyectil mágico (conocido, con ranura): {resultado}")

    # Truco (no gasta ranura)
    resultado = validador.validar_conjuro(personaje, "rayo_escarcha")
    assert resultado.valido == True
    print(f"   Rayo de escarcha (truco): {resultado}")

    print("   ✓ Conjuro válido correcto\n")
    return True


def test_conjuro_sin_ranuras():
    """Test de conjuro sin ranuras disponibles."""
    print("6. Validación de conjuro sin ranuras:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sin_ranuras()

    resultado = validador.validar_conjuro(personaje, "proyectil_magico", nivel_ranura=1)
    assert resultado.valido == False
    assert "ranura" in resultado.razon.lower()
    print(f"   {resultado}")

    print("   ✓ Validación sin ranuras correcta\n")
    return True


def test_conjuro_no_conocido():
    """Test de conjuro no conocido (advertencia, no bloqueo)."""
    print("7. Validación de conjuro no conocido:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()

    # Conjuro que existe pero no conoce
    resultado = validador.validar_conjuro(personaje, "curar_heridas", nivel_ranura=1)
    assert resultado.valido == True  # Válido pero con advertencia
    assert len(resultado.advertencias) > 0
    print(f"   {resultado}")

    print("   ✓ Validación conjuro no conocido correcta\n")
    return True


def test_movimiento():
    """Test de validación de movimiento."""
    print("8. Validación de movimiento:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()  # velocidad 30

    # Movimiento válido
    resultado = validador.validar_movimiento(personaje, 20, movimiento_usado=0)
    assert resultado.valido == True
    print(f"   Moverse 20 pies (30 disponibles): {resultado}")

    # Movimiento exacto
    resultado = validador.validar_movimiento(personaje, 30, movimiento_usado=0)
    assert resultado.valido == True
    print(f"   Moverse 30 pies (30 disponibles): {resultado}")

    # Movimiento excesivo
    resultado = validador.validar_movimiento(personaje, 35, movimiento_usado=0)
    assert resultado.valido == False
    print(f"   Moverse 35 pies (30 disponibles): {resultado}")

    # Movimiento parcial usado
    resultado = validador.validar_movimiento(personaje, 20, movimiento_usado=15)
    assert resultado.valido == False
    print(f"   Moverse 20 pies (15 usados, 15 quedan): {resultado}")

    print("   ✓ Validación de movimiento correcta\n")
    return True


def test_movimiento_condiciones():
    """Test de movimiento con condiciones."""
    print("9. Validación de movimiento con condiciones:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()
    personaje["estado_actual"]["condiciones"] = ["agarrado"]

    resultado = validador.validar_movimiento(personaje, 10, movimiento_usado=0)
    assert resultado.valido == False
    assert "agarrado" in resultado.razon.lower()
    print(f"   {resultado}")

    print("   ✓ Validación movimiento con condiciones correcta\n")
    return True


def test_acciones_genericas():
    """Test de acciones genéricas (Dash, Dodge, etc.)."""
    print("10. Validación de acciones genéricas:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()

    acciones = [TipoAccion.DASH, TipoAccion.DODGE, TipoAccion.DISENGAGE,
                TipoAccion.HELP, TipoAccion.HIDE, TipoAccion.SEARCH]

    for accion in acciones:
        resultado = validador.validar_accion_generica(accion, personaje)
        assert resultado.valido == True
        print(f"   {accion.value}: válido ✓")

    print("   ✓ Acciones genéricas correctas\n")
    return True


def test_prueba_habilidad():
    """Test de validación de prueba de habilidad."""
    print("11. Validación de prueba de habilidad:")

    compendio = CompendioMotor()
    validador = ValidadorAcciones(compendio)

    personaje = crear_personaje_sano()

    # Habilidad válida
    resultado = validador.validar_prueba_habilidad(personaje, "Atletismo")
    assert resultado.valido == True
    print(f"   Atletismo: {resultado}")

    # Habilidad inválida
    resultado = validador.validar_prueba_habilidad(personaje, "Volar")
    assert resultado.valido == False
    print(f"   Volar (inválida): {resultado}")

    # Con condición que afecta
    personaje["estado_actual"]["condiciones"] = ["cegado"]
    resultado = validador.validar_prueba_habilidad(personaje, "Percepcion")
    assert resultado.valido == True
    assert len(resultado.advertencias) > 0
    print(f"   Percepción (cegado): {resultado}")

    print("   ✓ Validación de habilidad correcta\n")
    return True


def test_inyeccion_mock():
    """Test que demuestra inyección de compendio mock."""
    print("12. Inyección de compendio mock:")

    # Crear mock
    class CompendioMock:
        def obtener_arma(self, id):
            if id == "super_espada":
                return {"id": "super_espada", "nombre": "Super Espada"}
            return None

        def obtener_conjuro(self, id):
            return None

        def obtener_objeto(self, id):
            return None

    # Inyectar mock
    from motor.compendio import CompendioMotor

    class CompendioMotorMock(CompendioMotor):
        def __init__(self, mock):
            self._compendio = mock

    compendio_mock = CompendioMotorMock(CompendioMock())
    validador = ValidadorAcciones(compendio_mock)

    personaje = crear_personaje_sano()
    objetivo = crear_monstruo_vivo()

    # Arma que existe en el mock
    resultado = validador.validar_ataque(personaje, objetivo, "super_espada")
    assert resultado.valido == True
    print(f"   Ataque con super_espada (del mock): válido ✓")

    # Arma que no existe en el mock
    resultado = validador.validar_ataque(personaje, objetivo, "espada_larga")
    assert resultado.valido == False  # No existe en el mock
    print(f"   Ataque con espada_larga (no en mock): {resultado}")

    print("   ✓ Inyección de mock correcta\n")
    return True


def main():
    """Ejecuta todos los tests."""
    print("\n" + "="*60)
    print("  TESTS DEL VALIDADOR DE ACCIONES")
    print("="*60 + "\n")

    tests = [
        ("Ataque básico", test_ataque_basico),
        ("Ataque sin objetivo", test_ataque_sin_objetivo),
        ("Ataque objetivo muerto", test_ataque_objetivo_muerto),
        ("Atacante incapacitado", test_atacante_incapacitado),
        ("Conjuro válido", test_conjuro_valido),
        ("Conjuro sin ranuras", test_conjuro_sin_ranuras),
        ("Conjuro no conocido", test_conjuro_no_conocido),
        ("Movimiento", test_movimiento),
        ("Movimiento condiciones", test_movimiento_condiciones),
        ("Acciones genéricas", test_acciones_genericas),
        ("Prueba habilidad", test_prueba_habilidad),
        ("Inyección mock", test_inyeccion_mock),
    ]

    resultados = []
    for nombre, test_func in tests:
        try:
            exito = test_func()
            resultados.append((nombre, exito))
        except Exception as e:
            print(f"   ✗ EXCEPCIÓN: {e}\n")
            import traceback
            traceback.print_exc()
            resultados.append((nombre, False))

    print("="*60)
    print("  RESUMEN")
    print("="*60)

    todos_ok = True
    for nombre, exito in resultados:
        estado = "✓" if exito else "✗"
        print(f"  {estado} {nombre}")
        if not exito:
            todos_ok = False

    print("="*60)
    if todos_ok:
        print("  ✓ TODOS LOS TESTS PASARON")
    else:
        print("  ✗ ALGUNOS TESTS FALLARON")
    print("="*60 + "\n")

    return todos_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF

echo "   ✓ test_validador.py creado"

# -----------------------------------------------------------------------------
# 4. Resumen
# -----------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "  IMPLEMENTACIÓN COMPLETADA"
echo "=============================================="
echo ""
echo "Archivos creados:"
echo "  - src/motor/validador.py"
echo "  - tests/test_validador.py"
echo ""
echo "Validaciones implementadas:"
echo "  - Ataques (con arma, desarmado, objetivo válido)"
echo "  - Conjuros (ranuras, nivel, conocidos)"
echo "  - Movimiento (velocidad, condiciones)"
echo "  - Acciones genéricas (Dash, Dodge, etc.)"
echo "  - Pruebas de habilidad"
echo ""
echo "PATRÓN APLICADO:"
echo "  ✓ ValidadorAcciones recibe CompendioMotor por inyección"
echo "  ✓ No usa obtener_compendio_motor() internamente"
echo ""
echo "Siguiente paso:"
echo "  python tests/test_validador.py"
echo ""
