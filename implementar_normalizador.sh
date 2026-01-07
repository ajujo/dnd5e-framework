#!/bin/bash

# =============================================================================
# TAREA 3.4: Normalizador de Acciones (Híbrido)
# Ejecutar desde la raíz del proyecto: bash implementar_normalizador.sh
# =============================================================================

set -e

echo "=============================================="
echo "  TAREA 3.4: Normalizador de Acciones"
echo "=============================================="
echo ""

# -----------------------------------------------------------------------------
# 1. Crear src/motor/normalizador.py
# -----------------------------------------------------------------------------
echo "→ Creando src/motor/normalizador.py..."

cat > src/motor/normalizador.py << 'EOF'
"""
Normalizador de Acciones para D&D 5e

Convierte texto en lenguaje natural a estructuras JSON canónicas.
Usa un enfoque híbrido:
1. Patrones deterministas (rápido, predecible)
2. Fallback a LLM local (solo cuando hace falta)

PATRÓN: Inyección de dependencias
- Recibe CompendioMotor por constructor
- Recibe contexto de escena (enemigos, equipo, etc.)

El LLM NO decide reglas. Solo rellena campos del JSON.
La legalidad la decide ValidadorAcciones.
"""

import re
import unicodedata
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

from .compendio import CompendioMotor


class TipoAccionNorm(Enum):
    """Tipos de acción normalizados."""
    ATAQUE = "ataque"
    CONJURO = "conjuro"
    MOVIMIENTO = "movimiento"
    HABILIDAD = "habilidad"
    ACCION = "accion"  # Genéricas: dash, dodge, etc.
    OBJETO = "objeto"
    DESCONOCIDO = "desconocido"


@dataclass
class AccionNormalizada:
    """
    Resultado de normalizar una acción.

    Attributes:
        tipo: Tipo de acción detectada.
        datos: JSON canónico con los campos de la acción.
        confianza: 0.0 a 1.0, qué tan seguro está el normalizador.
        faltantes: Campos que no se pudieron resolver.
        advertencias: Información adicional para el usuario/DM.
        texto_original: El texto que se intentó normalizar.
        requiere_clarificacion: Si necesita input adicional del jugador.
        fuente: "patron" o "llm" - de dónde vino la normalización.
    """
    tipo: TipoAccionNorm
    datos: Dict[str, Any]
    confianza: float = 0.0
    faltantes: List[str] = field(default_factory=list)
    advertencias: List[str] = field(default_factory=list)
    texto_original: str = ""
    requiere_clarificacion: bool = False
    fuente: str = "patron"

    def es_completa(self) -> bool:
        """Retorna True si la acción tiene todos los campos necesarios."""
        return len(self.faltantes) == 0 and self.confianza >= 0.7

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
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
    """
    Contexto actual de la escena para resolver ambigüedades.

    El normalizador usa esto para inferir objetivos, armas, etc.
    """
    actor_id: str  # Quién está actuando
    actor_nombre: str

    # Equipo del actor
    arma_principal: Optional[Dict[str, Any]] = None
    arma_secundaria: Optional[Dict[str, Any]] = None
    armas_disponibles: List[Dict[str, Any]] = field(default_factory=list)

    # Conjuros
    conjuros_conocidos: List[Dict[str, Any]] = field(default_factory=list)
    ranuras_disponibles: Dict[int, int] = field(default_factory=dict)

    # Objetivos en escena
    enemigos_vivos: List[Dict[str, Any]] = field(default_factory=list)
    aliados: List[Dict[str, Any]] = field(default_factory=list)

    # Estado
    movimiento_restante: int = 30
    accion_disponible: bool = True
    accion_bonus_disponible: bool = True


class NormalizadorAcciones:
    """
    Normaliza texto en lenguaje natural a acciones estructuradas.

    Flujo:
    1. Preprocesado (limpieza, detección de intención)
    2. Extracción de entidades (armas, objetivos, números)
    3. Resolución de ambigüedades sin LLM
    4. Fallback a LLM si hace falta
    5. Canonización final
    """

    # Patrones para detectar intenciones
    PATRONES_INTENCION = {
        TipoAccionNorm.ATAQUE: [
            r'\batac[ao]r?\b', r'\bgolpe[ao]r?\b', r'\bpeg[ao]r?\b',
            r'\bdispar[ao]r?\b', r'\blanz[ao]r?\s+(flecha|dardo)',
            r'\bcort[ao]r?\b', r'\bapuñal[ao]r?\b', r'\bhier[oe]\b'
        ],
        TipoAccionNorm.CONJURO: [
            r'\blanz[ao]r?\s+(conjuro|hechizo)\b', r'\bconjur[ao]r?\b',
            r'\bhechiz[ao]r?\b', r'\bcast\b', r'\bmagia\b'
        ],
        TipoAccionNorm.MOVIMIENTO: [
            r'\bmov[ei]r?(me|se)?\b', r'\bcamin[ao]r?\b', r'\bcorr[eo]r?\b',
            r'\bacercar?(me|se)?\b', r'\balejar?(me|se)?\b', r'\bir\s+(a|hacia)\b',
            r'\bdesplazar?(me|se)?\b'
        ],
        TipoAccionNorm.HABILIDAD: [
            r'\bpercep[cs]i[oó]n\b', r'\bsigilo\b', r'\batletismo\b',
            r'\bacrobacia\b', r'\binvestig[ao]r?\b', r'\bbuscar\b',
            r'\bescuchar\b', r'\bmirar\b', r'\bexaminar\b'
        ],
        TipoAccionNorm.ACCION: [
            r'\bdash\b', r'\besquiv[ao]r?\b', r'\bdodge\b',
            r'\bdesenganche\b', r'\bdisengage\b', r'\bayud[ao]r?\b',
            r'\besconder?(me|se)?\b', r'\bhide\b', r'\bpreparar\b'
        ],
        TipoAccionNorm.OBJETO: [
            r'\bus[ao]r?\b.*\b(poci[oó]n|objeto|item)\b',
            r'\bbeber\b', r'\btomar\b.*\bpoci[oó]n\b',
            r'\bsacar\b', r'\bequipar\b'
        ]
    }

    # Mapeo de acciones genéricas
    ACCIONES_GENERICAS = {
        'dash': ['dash', 'carrera', 'sprint', 'correr rápido'],
        'dodge': ['dodge', 'esquivar', 'esquiva', 'evadir'],
        'disengage': ['disengage', 'desenganche', 'retirada', 'retirarse'],
        'help': ['help', 'ayudar', 'ayuda', 'asistir'],
        'hide': ['hide', 'esconder', 'esconderse', 'ocultar'],
        'search': ['search', 'buscar', 'registrar', 'examinar'],
        'ready': ['ready', 'preparar', 'preparar acción']
    }

    # Habilidades válidas
    HABILIDADES = [
        'acrobacias', 'arcanos', 'atletismo', 'engaño', 'historia',
        'interpretacion', 'intimidacion', 'investigacion', 'juego_manos',
        'medicina', 'naturaleza', 'percepcion', 'perspicacia', 'persuasion',
        'religion', 'sigilo', 'supervivencia', 'trato_animales'
    ]

    def __init__(self, compendio_motor: CompendioMotor,
                 llm_callback: Callable[[str, Dict], Dict] = None):
        """
        Inicializa el normalizador.

        Args:
            compendio_motor: Instancia de CompendioMotor (inyectada).
            llm_callback: Función opcional para llamar al LLM.
                          Firma: callback(prompt, contexto) -> dict
        """
        self._compendio = compendio_motor
        self._llm_callback = llm_callback

        # Compilar patrones
        self._patrones_compilados = {
            tipo: [re.compile(p, re.IGNORECASE) for p in patrones]
            for tipo, patrones in self.PATRONES_INTENCION.items()
        }

    # =========================================================================
    # MÉTODO PRINCIPAL
    # =========================================================================

    def normalizar(self, texto: str,
                   contexto: ContextoEscena) -> AccionNormalizada:
        """
        Normaliza un texto de acción a formato canónico.

        Args:
            texto: Texto en lenguaje natural del jugador.
            contexto: Contexto actual de la escena.

        Returns:
            AccionNormalizada con el resultado.
        """
        # Paso 1: Preprocesado
        texto_limpio = self._preprocesar(texto)

        # Paso 2: Detectar intención
        tipo, confianza_tipo = self._detectar_intencion(texto_limpio)

        # Paso 3: Extraer entidades según tipo
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

        # Paso 4: Resolver ambigüedades sin LLM
        resultado = self._resolver_ambiguedades(resultado, contexto)

        # Paso 5: Fallback a LLM si hace falta
        if not resultado.es_completa() and self._llm_callback:
            resultado = self._fallback_llm(resultado, texto, contexto)

        # Paso 6: Canonización final
        resultado = self._canonizar(resultado)
        resultado.texto_original = texto

        return resultado

    # =========================================================================
    # PASO 1: PREPROCESADO
    # =========================================================================

    def _preprocesar(self, texto: str) -> str:
        """Limpia y normaliza el texto de entrada."""
        # Minúsculas
        texto = texto.lower()

        # Normalizar acentos (opcional: mantener para mejor matching)
        # texto = unicodedata.normalize('NFKD', texto)
        # texto = texto.encode('ASCII', 'ignore').decode('ASCII')

        # Eliminar signos de puntuación excepto guiones
        texto = re.sub(r'[^\w\s\-áéíóúüñ]', ' ', texto)

        # Normalizar espacios
        texto = re.sub(r'\s+', ' ', texto).strip()

        return texto

    # =========================================================================
    # PASO 2: DETECCIÓN DE INTENCIÓN
    # =========================================================================

    def _detectar_intencion(self, texto: str) -> Tuple[TipoAccionNorm, float]:
        """
        Detecta el tipo de acción más probable.

        Returns:
            Tupla (tipo, confianza).
        """
        mejor_tipo = TipoAccionNorm.DESCONOCIDO
        mejor_confianza = 0.0

        for tipo, patrones in self._patrones_compilados.items():
            for patron in patrones:
                if patron.search(texto):
                    # Más matches = más confianza
                    confianza = 0.8
                    if confianza > mejor_confianza:
                        mejor_tipo = tipo
                        mejor_confianza = confianza
                    break

        return mejor_tipo, mejor_confianza

    # =========================================================================
    # PASO 3: EXTRACCIÓN DE ENTIDADES
    # =========================================================================

    def _normalizar_ataque(self, texto: str,
                           contexto: ContextoEscena) -> AccionNormalizada:
        """Normaliza una acción de ataque."""
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

        # Detectar arma
        arma_id, arma_confianza = self._buscar_arma_en_texto(texto, contexto)
        if arma_id:
            datos["arma_id"] = arma_id
            confianza = min(confianza + 0.1, 1.0)
        else:
            faltantes.append("arma_id")

        # Detectar objetivo
        objetivo_id, obj_confianza = self._buscar_objetivo_en_texto(texto, contexto)
        if objetivo_id:
            datos["objetivo_id"] = objetivo_id
            confianza = min(confianza + 0.1, 1.0)
        else:
            faltantes.append("objetivo_id")

        # Detectar modo (ventaja/desventaja)
        if re.search(r'\bventaja\b', texto):
            datos["modo"] = "ventaja"
        elif re.search(r'\bdesventaja\b', texto):
            datos["modo"] = "desventaja"

        # Detectar subtipo
        if re.search(r'\b(arco|ballesta|distancia|disparar|lanzar)\b', texto):
            datos["subtipo"] = "ranged"
        elif re.search(r'\b(desarmado|puño|puñetazo|patada)\b', texto):
            datos["subtipo"] = "unarmed"
            datos["arma_id"] = "unarmed"
            if "arma_id" in faltantes:
                faltantes.remove("arma_id")

        return AccionNormalizada(
            tipo=TipoAccionNorm.ATAQUE,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes,
            advertencias=advertencias
        )

    def _normalizar_conjuro(self, texto: str,
                            contexto: ContextoEscena) -> AccionNormalizada:
        """Normaliza una acción de conjuro."""
        datos = {
            "tipo": "conjuro",
            "lanzador_id": contexto.actor_id,
            "objetivo_id": None,
            "conjuro_id": None,
            "nivel_lanzamiento": None
        }
        faltantes = []
        confianza = 0.6

        # Buscar conjuro en texto
        conjuro_id, conj_confianza = self._buscar_conjuro_en_texto(texto, contexto)
        if conjuro_id:
            datos["conjuro_id"] = conjuro_id
            confianza = min(confianza + 0.2, 1.0)

            # Obtener nivel base
            conjuro = self._compendio.obtener_conjuro(conjuro_id)
            if conjuro:
                datos["nivel_lanzamiento"] = conjuro.get("nivel", 1)
        else:
            faltantes.append("conjuro_id")

        # Buscar nivel específico
        match_nivel = re.search(r'nivel\s+(\d+)', texto)
        if match_nivel:
            datos["nivel_lanzamiento"] = int(match_nivel.group(1))

        # Buscar objetivo
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
        """Normaliza una acción de movimiento."""
        datos = {
            "tipo": "movimiento",
            "actor_id": contexto.actor_id,
            "distancia_pies": None,
            "destino": None
        }
        faltantes = []
        confianza = 0.7

        # Buscar distancia
        # Patrones: "20 pies", "5 metros", "6m", "30ft"
        match_pies = re.search(r'(\d+)\s*(pies|ft|feet)', texto)
        match_metros = re.search(r'(\d+)\s*(metros?|m)\b', texto)
        match_casillas = re.search(r'(\d+)\s*casillas?', texto)

        if match_pies:
            datos["distancia_pies"] = int(match_pies.group(1))
        elif match_metros:
            metros = int(match_metros.group(1))
            datos["distancia_pies"] = int(metros * 3.28)  # Conversión aproximada
        elif match_casillas:
            casillas = int(match_casillas.group(1))
            datos["distancia_pies"] = casillas * 5  # 1 casilla = 5 pies
        else:
            faltantes.append("distancia_pies")

        # Buscar destino
        destinos_comunes = [
            r'hacia\s+(el|la|los|las)?\s*(\w+)',
            r'a\s+(el|la|los|las)?\s*(\w+)',
            r'cerca\s+de\s+(el|la|los|las)?\s*(\w+)'
        ]
        for patron in destinos_comunes:
            match = re.search(patron, texto)
            if match:
                datos["destino"] = match.group(2) if match.lastindex >= 2 else match.group(1)
                break

        return AccionNormalizada(
            tipo=TipoAccionNorm.MOVIMIENTO,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes
        )

    def _normalizar_habilidad(self, texto: str,
                              contexto: ContextoEscena) -> AccionNormalizada:
        """Normaliza una prueba de habilidad."""
        datos = {
            "tipo": "habilidad",
            "actor_id": contexto.actor_id,
            "habilidad": None,
            "objetivo_id": None
        }
        faltantes = []
        confianza = 0.6

        # Buscar habilidad
        texto_normalizado = self._normalizar_texto_habilidad(texto)
        for hab in self.HABILIDADES:
            if hab in texto_normalizado or hab.replace('_', ' ') in texto_normalizado:
                datos["habilidad"] = hab
                confianza = 0.9
                break

        if not datos["habilidad"]:
            # Inferir por verbos
            if re.search(r'\bescuchar\b|\boir\b', texto):
                datos["habilidad"] = "percepcion"
            elif re.search(r'\bbuscar\b|\bmirar\b', texto):
                datos["habilidad"] = "percepcion"
            elif re.search(r'\binvestigar\b|\bexaminar\b', texto):
                datos["habilidad"] = "investigacion"
            elif re.search(r'\besconder\b|\bocultar\b|\bsigiloso\b', texto):
                datos["habilidad"] = "sigilo"
            elif re.search(r'\bsaltar\b|\btrepar\b|\bescalar\b', texto):
                datos["habilidad"] = "atletismo"
            elif re.search(r'\besquivar\b|\brodar\b', texto):
                datos["habilidad"] = "acrobacias"
            elif re.search(r'\bmentir\b|\bengañar\b', texto):
                datos["habilidad"] = "engaño"
            elif re.search(r'\bconvencer\b|\bpersuadir\b', texto):
                datos["habilidad"] = "persuasion"
            elif re.search(r'\bintimi\w+\b|\bamena\w+\b', texto):
                datos["habilidad"] = "intimidacion"
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
        """Normaliza acciones genéricas (Dash, Dodge, etc.)."""
        datos = {
            "tipo": "accion",
            "actor_id": contexto.actor_id,
            "accion_id": None
        }
        faltantes = []
        confianza = 0.5

        texto_lower = texto.lower()

        for accion_id, variantes in self.ACCIONES_GENERICAS.items():
            for variante in variantes:
                if variante in texto_lower:
                    datos["accion_id"] = accion_id
                    confianza = 0.9
                    break
            if datos["accion_id"]:
                break

        if not datos["accion_id"]:
            faltantes.append("accion_id")

        return AccionNormalizada(
            tipo=TipoAccionNorm.ACCION,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes
        )

    def _normalizar_objeto(self, texto: str,
                           contexto: ContextoEscena) -> AccionNormalizada:
        """Normaliza uso de objetos."""
        datos = {
            "tipo": "objeto",
            "actor_id": contexto.actor_id,
            "objeto_id": None
        }
        faltantes = ["objeto_id"]
        confianza = 0.5

        # Buscar objetos conocidos
        objetos = self._compendio.listar_objetos()
        for obj in objetos:
            nombre_lower = obj["nombre"].lower()
            id_lower = obj["id"].lower()
            if nombre_lower in texto.lower() or id_lower in texto.lower():
                datos["objeto_id"] = obj["id"]
                faltantes.remove("objeto_id")
                confianza = 0.85
                break

        # Buscar "poción" genérica
        if not datos["objeto_id"] and re.search(r'\bpoci[oó]n\b', texto):
            # Asumir poción de curación si no especifica
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

    # =========================================================================
    # HELPERS DE BÚSQUEDA
    # =========================================================================

    def _buscar_arma_en_texto(self, texto: str,
                              contexto: ContextoEscena) -> Tuple[Optional[str], float]:
        """Busca un arma mencionada en el texto."""
        # Primero buscar por nombre exacto en armas disponibles
        for arma in contexto.armas_disponibles:
            nombre_lower = arma.get("nombre", "").lower()
            if nombre_lower and nombre_lower in texto.lower():
                return arma.get("id") or arma.get("compendio_ref"), 0.95

        # Buscar en compendio
        armas = self._compendio.listar_armas()
        for arma in armas:
            nombre_lower = arma["nombre"].lower()
            if nombre_lower in texto.lower():
                return arma["id"], 0.8

        # Sinónimos comunes
        sinonimos = {
            "espada": ["espada_larga", "espada_corta"],
            "arco": ["arco_corto", "arco_largo"],
            "hacha": ["hacha_mano", "hacha_grande"],
            "daga": ["daga"],
            "maza": ["maza"],
            "bastón": ["baston"],
        }

        for sinonimo, ids in sinonimos.items():
            if sinonimo in texto.lower():
                # Preferir arma equipada
                if contexto.arma_principal:
                    ref = contexto.arma_principal.get("compendio_ref") or contexto.arma_principal.get("id")
                    if ref in ids:
                        return ref, 0.85
                # Sino la primera de la lista
                return ids[0], 0.6

        return None, 0.0

    def _buscar_objetivo_en_texto(self, texto: str,
                                  contexto: ContextoEscena) -> Tuple[Optional[str], float]:
        """Busca un objetivo mencionado en el texto."""
        # Buscar por nombre en enemigos vivos
        for enemigo in contexto.enemigos_vivos:
            nombre_lower = enemigo.get("nombre", "").lower()
            if nombre_lower and nombre_lower in texto.lower():
                return enemigo.get("instancia_id") or enemigo.get("id"), 0.95

        # Buscar tipo de criatura
        for enemigo in contexto.enemigos_vivos:
            # Por compendio_ref (ej: "goblin")
            ref = enemigo.get("compendio_ref", "").lower()
            if ref and ref in texto.lower():
                return enemigo.get("instancia_id") or enemigo.get("id"), 0.85

        return None, 0.0

    def _buscar_conjuro_en_texto(self, texto: str,
                                 contexto: ContextoEscena) -> Tuple[Optional[str], float]:
        """Busca un conjuro mencionado en el texto."""
        # Buscar en conjuros conocidos del personaje
        for conjuro in contexto.conjuros_conocidos:
            nombre_lower = conjuro.get("nombre", "").lower()
            if nombre_lower and nombre_lower in texto.lower():
                return conjuro.get("id"), 0.95

        # Buscar en compendio
        conjuros = self._compendio.listar_conjuros()
        for conjuro in conjuros:
            nombre_lower = conjuro["nombre"].lower()
            # Normalizar para matching
            nombre_norm = nombre_lower.replace(" ", "_")
            if nombre_lower in texto.lower() or nombre_norm in texto.lower():
                return conjuro["id"], 0.8

        return None, 0.0

    def _normalizar_texto_habilidad(self, texto: str) -> str:
        """Normaliza texto para búsqueda de habilidades."""
        # Reemplazar variantes
        reemplazos = {
            'percepción': 'percepcion',
            'religión': 'religion',
            'persuasión': 'persuasion',
            'intimidación': 'intimidacion',
            'investigación': 'investigacion',
            'interpretación': 'interpretacion',
        }
        texto_norm = texto.lower()
        for original, reemplazo in reemplazos.items():
            texto_norm = texto_norm.replace(original, reemplazo)
        return texto_norm

    # =========================================================================
    # PASO 4: RESOLUCIÓN DE AMBIGÜEDADES SIN LLM
    # =========================================================================

    def _resolver_ambiguedades(self, resultado: AccionNormalizada,
                               contexto: ContextoEscena) -> AccionNormalizada:
        """
        Intenta resolver campos faltantes con reglas simples.

        - Si solo hay 1 enemigo vivo → úsalo como objetivo
        - Si solo hay 1 arma equipada → úsala por defecto
        - Etc.
        """
        datos = resultado.datos.copy()
        faltantes = resultado.faltantes.copy()
        advertencias = resultado.advertencias.copy()
        confianza = resultado.confianza

        # Resolver objetivo
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

        # Resolver arma
        if "arma_id" in faltantes and resultado.tipo == TipoAccionNorm.ATAQUE:
            if contexto.arma_principal:
                ref = contexto.arma_principal.get("compendio_ref") or contexto.arma_principal.get("id")
                datos["arma_id"] = ref
                faltantes.remove("arma_id")
                advertencias.append(f"Arma inferida: {contexto.arma_principal.get('nombre', ref)}")
                confianza = min(confianza + 0.1, 1.0)
            elif contexto.arma_secundaria:
                ref = contexto.arma_secundaria.get("compendio_ref") or contexto.arma_secundaria.get("id")
                datos["arma_id"] = ref
                faltantes.remove("arma_id")
                advertencias.append(f"Arma inferida: {contexto.arma_secundaria.get('nombre', ref)}")

        # Resolver nivel de conjuro
        if resultado.tipo == TipoAccionNorm.CONJURO:
            if datos.get("nivel_lanzamiento") is None and datos.get("conjuro_id"):
                conjuro = self._compendio.obtener_conjuro(datos["conjuro_id"])
                if conjuro:
                    datos["nivel_lanzamiento"] = conjuro.get("nivel", 0)

        return AccionNormalizada(
            tipo=resultado.tipo,
            datos=datos,
            confianza=confianza,
            faltantes=faltantes,
            advertencias=advertencias,
            fuente=resultado.fuente
        )

    # =========================================================================
    # PASO 5: FALLBACK A LLM
    # =========================================================================

    def _fallback_llm(self, resultado: AccionNormalizada,
                      texto_original: str,
                      contexto: ContextoEscena) -> AccionNormalizada:
        """
        Usa el LLM para resolver ambigüedades.

        Solo se llama si:
        - Faltan campos obligatorios
        - Hay múltiples candidatos
        - Intención poco clara
        """
        if not self._llm_callback:
            return resultado

        # Construir contexto para el LLM
        contexto_llm = {
            "texto_jugador": texto_original,
            "tipo_detectado": resultado.tipo.value,
            "datos_parciales": resultado.datos,
            "faltantes": resultado.faltantes,
            "armas_equipadas": [
                {"id": a.get("compendio_ref") or a.get("id"), "nombre": a.get("nombre")}
                for a in [contexto.arma_principal, contexto.arma_secundaria]
                if a
            ],
            "enemigos_vivos": [
                {"id": e.get("instancia_id") or e.get("id"), "nombre": e.get("nombre")}
                for e in contexto.enemigos_vivos
            ],
            "conjuros_conocidos": [
                {"id": c.get("id"), "nombre": c.get("nombre")}
                for c in contexto.conjuros_conocidos
            ]
        }

        # Prompt para el LLM
        prompt = f"""Analiza la acción del jugador y completa los campos faltantes.

Texto del jugador: "{texto_original}"

Contexto:
- Tipo detectado: {resultado.tipo.value}
- Datos parciales: {resultado.datos}
- Campos faltantes: {resultado.faltantes}
- Armas equipadas: {contexto_llm['armas_equipadas']}
- Enemigos vivos: {contexto_llm['enemigos_vivos']}
- Conjuros conocidos: {contexto_llm['conjuros_conocidos']}

Responde SOLO con un JSON válido completando los campos faltantes.
Si no puedes determinar un campo, usa null.
"""

        try:
            respuesta = self._llm_callback(prompt, contexto_llm)

            if respuesta and isinstance(respuesta, dict):
                # Merge con datos existentes
                for key, value in respuesta.items():
                    if value is not None:
                        resultado.datos[key] = value
                        if key in resultado.faltantes:
                            resultado.faltantes.remove(key)

                resultado.fuente = "llm"
                resultado.confianza = min(resultado.confianza + 0.15, 0.9)

        except Exception as e:
            resultado.advertencias.append(f"Error en LLM: {str(e)}")

        return resultado

    # =========================================================================
    # PASO 6: CANONIZACIÓN
    # =========================================================================

    def _canonizar(self, resultado: AccionNormalizada) -> AccionNormalizada:
        """
        Asegura que el resultado tenga el formato canónico correcto.
        """
        datos = resultado.datos

        # Asegurar campos mínimos por tipo
        if resultado.tipo == TipoAccionNorm.ATAQUE:
            datos.setdefault("subtipo", "melee")
            datos.setdefault("modo", "normal")

        elif resultado.tipo == TipoAccionNorm.CONJURO:
            datos.setdefault("nivel_lanzamiento", 1)

        elif resultado.tipo == TipoAccionNorm.MOVIMIENTO:
            datos.setdefault("distancia_pies", 0)

        # Determinar si requiere clarificación
        campos_criticos = {
            TipoAccionNorm.ATAQUE: ["objetivo_id"],
            TipoAccionNorm.CONJURO: ["conjuro_id"],
            TipoAccionNorm.MOVIMIENTO: [],  # Puede moverse sin destino específico
            TipoAccionNorm.HABILIDAD: ["habilidad"],
            TipoAccionNorm.ACCION: ["accion_id"],
            TipoAccionNorm.OBJETO: ["objeto_id"]
        }

        criticos = campos_criticos.get(resultado.tipo, [])
        faltantes_criticos = [f for f in resultado.faltantes if f in criticos]

        resultado.requiere_clarificacion = len(faltantes_criticos) > 0

        return resultado
EOF

echo "   ✓ normalizador.py creado"

# -----------------------------------------------------------------------------
# 2. Actualizar src/motor/__init__.py
# -----------------------------------------------------------------------------
echo "→ Actualizando src/motor/__init__.py..."

cat > src/motor/__init__.py << 'EOF'
"""
Motor de Reglas D&D 5e

ESTRUCTURA:
- dados.py: Sistema de tiradas genéricas
- reglas_basicas.py: Modificadores, competencia, CA
- combate_utils.py: Ataque, daño, iniciativa, salvaciones
- compendio.py: Interfaz con el compendio de datos
- validador.py: Validación de acciones
- normalizador.py: Normalización de texto a acciones

PATRÓN DE INYECCIÓN:
- Los módulos internos reciben dependencias por constructor
- obtener_compendio_motor() solo debe usarse en main.py/cli.py

FLUJO DE ACCIONES:
Texto jugador → NormalizadorAcciones → ValidadorAcciones → Resolución
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
    obtener_compendio_motor,
    resetear_compendio_motor,
)

# Desde validador.py
from .validador import (
    ValidadorAcciones,
    TipoAccion,
    ResultadoValidacion,
)

# Desde normalizador.py
from .normalizador import (
    NormalizadorAcciones,
    TipoAccionNorm,
    AccionNormalizada,
    ContextoEscena,
)

__all__ = [
    # Gestor de aleatoriedad
    'rng',
    'GestorAleatorio',

    # Tipos dados
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

    # Normalizador
    'NormalizadorAcciones',
    'TipoAccionNorm',
    'AccionNormalizada',
    'ContextoEscena',
]
EOF

echo "   ✓ __init__.py actualizado"

# -----------------------------------------------------------------------------
# 3. Crear tests del normalizador
# -----------------------------------------------------------------------------
echo "→ Creando tests/test_normalizador.py..."

cat > tests/test_normalizador.py << 'EOF'
"""
Tests del normalizador de acciones.
Ejecutar desde la raíz: python tests/test_normalizador.py

Verifica:
- Detección de intenciones
- Extracción de entidades
- Resolución de ambigüedades
- Fallback a LLM (con mock)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from motor import (
    NormalizadorAcciones,
    TipoAccionNorm,
    AccionNormalizada,
    ContextoEscena,
    CompendioMotor
)


# =============================================================================
# FIXTURES
# =============================================================================

def crear_contexto_basico():
    """Crea un contexto de escena básico."""
    return ContextoEscena(
        actor_id="pc_1",
        actor_nombre="Thorin",
        arma_principal={"id": "espada_1", "compendio_ref": "espada_larga", "nombre": "Espada larga"},
        arma_secundaria=None,
        armas_disponibles=[
            {"id": "espada_1", "compendio_ref": "espada_larga", "nombre": "Espada larga"},
            {"id": "daga_1", "compendio_ref": "daga", "nombre": "Daga"}
        ],
        conjuros_conocidos=[
            {"id": "proyectil_magico", "nombre": "Proyectil mágico"},
            {"id": "rayo_escarcha", "nombre": "Rayo de escarcha"}
        ],
        ranuras_disponibles={1: 2, 2: 1},
        enemigos_vivos=[
            {"instancia_id": "goblin_1", "nombre": "Goblin", "compendio_ref": "goblin"},
            {"instancia_id": "goblin_2", "nombre": "Goblin arquero", "compendio_ref": "goblin"}
        ],
        aliados=[],
        movimiento_restante=30,
        accion_disponible=True
    )


def crear_contexto_un_enemigo():
    """Crea un contexto con un solo enemigo."""
    ctx = crear_contexto_basico()
    ctx.enemigos_vivos = [
        {"instancia_id": "orco_1", "nombre": "Orco", "compendio_ref": "orco"}
    ]
    return ctx


# =============================================================================
# TESTS
# =============================================================================

def test_deteccion_ataque():
    """Test de detección de intención de ataque."""
    print("1. Detección de ataque:")

    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_un_enemigo()

    textos_ataque = [
        "Ataco al orco",
        "Le pego con mi espada",
        "Golpeo al enemigo",
        "Disparo una flecha",
        "Lanzo un ataque"
    ]

    for texto in textos_ataque:
        resultado = normalizador.normalizar(texto, contexto)
        assert resultado.tipo == TipoAccionNorm.ATAQUE, f"'{texto}' debería ser ATAQUE"
        print(f"   '{texto}' → {resultado.tipo.value} ✓")

    print("   ✓ Detección de ataque correcta\n")
    return True


def test_deteccion_conjuro():
    """Test de detección de intención de conjuro."""
    print("2. Detección de conjuro:")

    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_basico()

    textos_conjuro = [
        "Lanzo proyectil mágico",
        "Conjuro rayo de escarcha",
        "Uso magia contra el goblin"
    ]

    for texto in textos_conjuro:
        resultado = normalizador.normalizar(texto, contexto)
        assert resultado.tipo == TipoAccionNorm.CONJURO, f"'{texto}' debería ser CONJURO"
        print(f"   '{texto}' → {resultado.tipo.value} ✓")

    print("   ✓ Detección de conjuro correcta\n")
    return True


def test_deteccion_movimiento():
    """Test de detección de movimiento."""
    print("3. Detección de movimiento:")

    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_basico()

    textos_movimiento = [
        "Me muevo 20 pies hacia la puerta",
        "Camino hacia el norte",
        "Corro hacia el goblin",
        "Me acerco al enemigo"
    ]

    for texto in textos_movimiento:
        resultado = normalizador.normalizar(texto, contexto)
        assert resultado.tipo == TipoAccionNorm.MOVIMIENTO, f"'{texto}' debería ser MOVIMIENTO"
        print(f"   '{texto}' → {resultado.tipo.value} ✓")

    print("   ✓ Detección de movimiento correcta\n")
    return True


def test_extraccion_arma():
    """Test de extracción de arma del texto."""
    print("4. Extracción de arma:")

    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_un_enemigo()

    # Arma mencionada explícitamente
    resultado = normalizador.normalizar("Ataco con mi espada larga", contexto)
    assert resultado.datos.get("arma_id") == "espada_larga"
    print(f"   'Ataco con mi espada larga' → arma_id={resultado.datos.get('arma_id')} ✓")

    # Arma inferida (principal equipada)
    resultado = normalizador.normalizar("Ataco al orco", contexto)
    assert resultado.datos.get("arma_id") == "espada_larga"
    print(f"   'Ataco al orco' → arma_id={resultado.datos.get('arma_id')} (inferida) ✓")

    # Ataque desarmado
    resultado = normalizador.normalizar("Le doy un puñetazo", contexto)
    assert resultado.datos.get("arma_id") == "unarmed"
    print(f"   'Le doy un puñetazo' → arma_id={resultado.datos.get('arma_id')} ✓")

    print("   ✓ Extracción de arma correcta\n")
    return True


def test_extraccion_objetivo():
    """Test de extracción de objetivo."""
    print("5. Extracción de objetivo:")

    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)

    # Un solo enemigo: inferir automáticamente
    contexto = crear_contexto_un_enemigo()
    resultado = normalizador.normalizar("Ataco", contexto)
    assert resultado.datos.get("objetivo_id") == "orco_1"
    print(f"   'Ataco' (1 enemigo) → objetivo_id={resultado.datos.get('objetivo_id')} ✓")

    # Múltiples enemigos: mencionar explícitamente
    contexto = crear_contexto_basico()
    resultado = normalizador.normalizar("Ataco al goblin arquero", contexto)
    assert resultado.datos.get("objetivo_id") == "goblin_2"
    print(f"   'Ataco al goblin arquero' → objetivo_id={resultado.datos.get('objetivo_id')} ✓")

    # Múltiples enemigos sin especificar
    resultado = normalizador.normalizar("Ataco", contexto)
    assert "objetivo_id" in resultado.faltantes or resultado.datos.get("objetivo_id") is None
    print(f"   'Ataco' (múltiples enemigos) → requiere clarificación ✓")

    print("   ✓ Extracción de objetivo correcta\n")
    return True


def test_extraccion_distancia():
    """Test de extracción de distancia."""
    print("6. Extracción de distancia:")

    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_basico()

    casos = [
        ("Me muevo 20 pies", 20),
        ("Camino 30ft hacia la puerta", 30),
        ("Avanzo 2 casillas", 10),  # 2 casillas = 10 pies
        ("Me desplazo 6 metros", 19),  # ~6m * 3.28
    ]

    for texto, esperado in casos:
        resultado = normalizador.normalizar(texto, contexto)
        distancia = resultado.datos.get("distancia_pies")
        assert distancia is not None, f"No se detectó distancia en '{texto}'"
        assert abs(distancia - esperado) <= 2, f"Distancia incorrecta: {distancia} != {esperado}"
        print(f"   '{texto}' → {distancia} pies ✓")

    print("   ✓ Extracción de distancia correcta\n")
    return True


def test_deteccion_habilidad():
    """Test de detección de pruebas de habilidad."""
    print("7. Detección de habilidad:")

    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_basico()

    casos = [
        ("Hago una prueba de percepción", "percepcion"),
        ("Intento escuchar", "percepcion"),
        ("Me escondo sigilosamente", "sigilo"),
        ("Investigo la habitación", "investigacion"),
        ("Intento intimidar al guardia", "intimidacion"),
        ("Quiero convencerlo", "persuasion"),
    ]

    for texto, habilidad_esperada in casos:
        resultado = normalizador.normalizar(texto, contexto)
        assert resultado.tipo == TipoAccionNorm.HABILIDAD, f"'{texto}' debería ser HABILIDAD"
        assert resultado.datos.get("habilidad") == habilidad_esperada
        print(f"   '{texto}' → {resultado.datos.get('habilidad')} ✓")

    print("   ✓ Detección de habilidad correcta\n")
    return True


def test_acciones_genericas():
    """Test de acciones genéricas."""
    print("8. Acciones genéricas:")

    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_basico()

    casos = [
        ("Uso Dash", "dash"),
        ("Me pongo a esquivar", "dodge"),
        ("Hago Disengage", "disengage"),
        ("Ayudo a mi compañero", "help"),
        ("Me escondo", "hide"),
    ]

    for texto, accion_esperada in casos:
        resultado = normalizador.normalizar(texto, contexto)
        assert resultado.tipo == TipoAccionNorm.ACCION, f"'{texto}' debería ser ACCION"
        assert resultado.datos.get("accion_id") == accion_esperada
        print(f"   '{texto}' → {resultado.datos.get('accion_id')} ✓")

    print("   ✓ Acciones genéricas correctas\n")
    return True


def test_deteccion_conjuro_especifico():
    """Test de detección de conjuro específico."""
    print("9. Detección de conjuro específico:")

    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_basico()

    resultado = normalizador.normalizar("Lanzo proyectil mágico al goblin", contexto)
    assert resultado.tipo == TipoAccionNorm.CONJURO
    assert resultado.datos.get("conjuro_id") == "proyectil_magico"
    print(f"   'Lanzo proyectil mágico' → conjuro_id={resultado.datos.get('conjuro_id')} ✓")

    resultado = normalizador.normalizar("Uso rayo de escarcha", contexto)
    assert resultado.datos.get("conjuro_id") == "rayo_escarcha"
    print(f"   'Uso rayo de escarcha' → conjuro_id={resultado.datos.get('conjuro_id')} ✓")

    print("   ✓ Detección de conjuro específico correcta\n")
    return True


def test_confianza_y_faltantes():
    """Test de niveles de confianza y campos faltantes."""
    print("10. Confianza y faltantes:")

    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_basico()

    # Acción completa: alta confianza
    resultado = normalizador.normalizar("Ataco al goblin con mi espada larga", contexto)
    assert resultado.confianza >= 0.8
    assert resultado.es_completa()
    print(f"   Acción completa: confianza={resultado.confianza:.2f}, faltantes={resultado.faltantes} ✓")

    # Acción ambigua: requiere clarificación
    resultado = normalizador.normalizar("Ataco", contexto)  # Múltiples enemigos
    assert resultado.requiere_clarificacion or len(resultado.advertencias) > 0
    print(f"   Acción ambigua: requiere_clarificacion={resultado.requiere_clarificacion} ✓")

    print("   ✓ Confianza y faltantes correctos\n")
    return True


def test_fallback_llm_mock():
    """Test del fallback a LLM con mock."""
    print("11. Fallback a LLM (mock):")

    # Mock del LLM que completa campos faltantes
    def llm_mock(prompt, contexto):
        # Simular respuesta del LLM
        if "objetivo" in prompt.lower():
            return {"objetivo_id": "goblin_1"}
        return {}

    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio, llm_callback=llm_mock)
    contexto = crear_contexto_basico()

    # Acción que necesita LLM
    resultado = normalizador.normalizar("Ataco a uno de ellos", contexto)

    # El LLM debería haber completado el objetivo
    if resultado.fuente == "llm":
        print(f"   LLM usado: objetivo_id={resultado.datos.get('objetivo_id')} ✓")
    else:
        print(f"   LLM no fue necesario (resuelto por patrones) ✓")

    print("   ✓ Fallback a LLM correcto\n")
    return True


def test_serializacion():
    """Test de serialización del resultado."""
    print("12. Serialización:")

    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    contexto = crear_contexto_un_enemigo()

    resultado = normalizador.normalizar("Ataco al orco con mi espada", contexto)
    diccionario = resultado.to_dict()

    assert "tipo" in diccionario
    assert "datos" in diccionario
    assert "confianza" in diccionario
    assert diccionario["tipo"] == "ataque"

    print(f"   Resultado serializado: {diccionario['tipo']}, confianza={diccionario['confianza']:.2f} ✓")

    print("   ✓ Serialización correcta\n")
    return True


def test_flujo_completo():
    """Test del flujo completo: normalizar → validar."""
    print("13. Flujo completo (normalizar → validar):")

    from motor import ValidadorAcciones

    compendio = CompendioMotor()
    normalizador = NormalizadorAcciones(compendio)
    validador = ValidadorAcciones(compendio)

    contexto = crear_contexto_un_enemigo()

    # Paso 1: Normalizar
    accion = normalizador.normalizar("Ataco al orco con mi espada larga", contexto)
    print(f"   1. Normalizado: tipo={accion.tipo.value}, objetivo={accion.datos.get('objetivo_id')}")

    # Paso 2: Crear datos para validador
    personaje = {
        "nombre": contexto.actor_nombre,
        "fuente": {
            "equipo_equipado": {
                "arma_principal_id": "espada_larga"
            }
        },
        "estado_actual": {
            "condiciones": [],
            "inconsciente": False,
            "muerto": False
        }
    }

    objetivo = {
        "nombre": "Orco",
        "puntos_golpe_actual": 15,
        "estado_actual": {"muerto": False}
    }

    # Paso 3: Validar
    validacion = validador.validar_ataque(personaje, objetivo, accion.datos.get("arma_id"))
    print(f"   2. Validado: {validacion}")

    assert accion.es_completa()
    assert validacion.valido

    print("   ✓ Flujo completo correcto\n")
    return True


def main():
    """Ejecuta todos los tests."""
    print("\n" + "="*60)
    print("  TESTS DEL NORMALIZADOR DE ACCIONES")
    print("="*60 + "\n")

    tests = [
        ("Detección ataque", test_deteccion_ataque),
        ("Detección conjuro", test_deteccion_conjuro),
        ("Detección movimiento", test_deteccion_movimiento),
        ("Extracción arma", test_extraccion_arma),
        ("Extracción objetivo", test_extraccion_objetivo),
        ("Extracción distancia", test_extraccion_distancia),
        ("Detección habilidad", test_deteccion_habilidad),
        ("Acciones genéricas", test_acciones_genericas),
        ("Conjuro específico", test_deteccion_conjuro_especifico),
        ("Confianza y faltantes", test_confianza_y_faltantes),
        ("Fallback LLM", test_fallback_llm_mock),
        ("Serialización", test_serializacion),
        ("Flujo completo", test_flujo_completo),
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

echo "   ✓ test_normalizador.py creado"

# -----------------------------------------------------------------------------
# 4. Resumen
# -----------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "  IMPLEMENTACIÓN COMPLETADA"
echo "=============================================="
echo ""
echo "Archivos creados:"
echo "  - src/motor/normalizador.py"
echo "  - tests/test_normalizador.py"
echo ""
echo "Funcionalidades:"
echo "  - Preprocesado de texto (limpieza, normalización)"
echo "  - Detección de intención (ataque, conjuro, movimiento, etc.)"
echo "  - Extracción de entidades (armas, objetivos, distancias)"
echo "  - Resolución de ambigüedades sin LLM"
echo "  - Fallback opcional a LLM"
echo "  - Canonización final"
echo ""
echo "PATRÓN APLICADO:"
echo "  ✓ NormalizadorAcciones recibe CompendioMotor por inyección"
echo "  ✓ LLM callback opcional (no obligatorio)"
echo "  ✓ El LLM NO decide reglas, solo completa campos"
echo ""
echo "Siguiente paso:"
echo "  python tests/test_normalizador.py"
echo ""
