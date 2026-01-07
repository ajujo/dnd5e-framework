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
