from typing import Optional, List
from dataclasses import dataclass, field
"""
Utilidades de Combate para D&D 5e

Este módulo contiene funciones para tiradas específicas de combate y acciones:
- Ataques
- Daño
- Salvaciones
- Habilidades
- Iniciativa
- Generación de atributos

Depende de:
- motor.dados para las tiradas genéricas
- motor.reglas_basicas para cálculos de reglas
"""

from typing import Dict, Any

from .dados import (
    tirar, tirar_dados, parsear_expresion,
    TipoTirada, ResultadoTirada
)


def tirar_ataque(bonificador_ataque: int,
                 tipo: TipoTirada = TipoTirada.NORMAL) -> ResultadoTirada:
    """
    Tira un ataque.

    NOTA: El resultado incluye flags critico/pifia.
    El motor de combate debe interpretar:
    - critico=True → doble dados de daño
    - pifia=True → fallo automático

    Args:
        bonificador_ataque: Bonificador total al ataque.
        tipo: Normal, ventaja o desventaja.

    Returns:
        ResultadoTirada con flags de crítico/pifia.
    """
    if bonificador_ataque >= 0:
        expresion = f"1d20+{bonificador_ataque}"
    else:
        expresion = f"1d20{bonificador_ataque}"
    return tirar(expresion, tipo)


def tirar_daño(expresion_daño: str, critico: bool = False) -> ResultadoTirada:
    """
    Tira daño, duplicando dados en caso de crítico.

    Regla D&D 5e: En crítico se duplican los DADOS, no el modificador.

    Args:
        expresion_daño: Expresión de daño (ej: "2d6+3").
        critico: Si True, duplica los dados.

    Returns:
        ResultadoTirada con el daño total.
    """
    cantidad, caras, modificador = parsear_expresion(expresion_daño)

    if critico:
        cantidad *= 2

    nueva_expresion = f"{cantidad}d{caras}"
    if modificador > 0:
        nueva_expresion += f"+{modificador}"
    elif modificador < 0:
        nueva_expresion += str(modificador)

    return tirar(nueva_expresion)


def tirar_salvacion(modificador_salvacion: int,
                    tipo: TipoTirada = TipoTirada.NORMAL) -> ResultadoTirada:
    """
    Tira una tirada de salvación.

    NOTA: Los flags critico/pifia se marcan pero en RAW D&D 5e
    las salvaciones NO tienen crítico/pifia automático.

    Args:
        modificador_salvacion: Modificador total a la salvación.
        tipo: Normal, ventaja o desventaja.

    Returns:
        ResultadoTirada para comparar contra CD.
    """
    if modificador_salvacion >= 0:
        expresion = f"1d20+{modificador_salvacion}"
    else:
        expresion = f"1d20{modificador_salvacion}"
    return tirar(expresion, tipo)


def tirar_habilidad(modificador_habilidad: int,
                    tipo: TipoTirada = TipoTirada.NORMAL) -> ResultadoTirada:
    """
    Tira una prueba de habilidad.

    NOTA: Los flags critico/pifia se marcan pero en RAW D&D 5e
    las pruebas de habilidad NO tienen crítico/pifia automático.

    Args:
        modificador_habilidad: Modificador total a la habilidad.
        tipo: Normal, ventaja o desventaja.

    Returns:
        ResultadoTirada para comparar contra CD.
    """
    if modificador_habilidad >= 0:
        expresion = f"1d20+{modificador_habilidad}"
    else:
        expresion = f"1d20{modificador_habilidad}"
    return tirar(expresion, tipo)


def tirar_iniciativa(modificador_destreza: int,
                     otros_bonus: int = 0,
                     tipo: TipoTirada = TipoTirada.NORMAL) -> ResultadoTirada:
    """
    Tira iniciativa para un combatiente.

    Args:
        modificador_destreza: Modificador de Destreza del combatiente.
        otros_bonus: Otros bonificadores (rasgos, objetos, etc.).
        tipo: Normal, ventaja o desventaja.

    Returns:
        ResultadoTirada con el valor de iniciativa.
    """
    mod_total = modificador_destreza + otros_bonus
    if mod_total >= 0:
        expresion = f"1d20+{mod_total}"
    else:
        expresion = f"1d20{mod_total}"
    return tirar(expresion, tipo)


def tirar_atributos(metodo: str = "4d6_drop_lowest") -> Dict[str, Any]:
    """
    Genera los 6 atributos de un personaje.

    Args:
        metodo: Método de generación.
            - "4d6_drop_lowest": Tira 4d6, descarta el menor (estándar PHB).
            - "3d6": Tira 3d6 (clásico).
            - "standard_array": Usa array estándar [15,14,13,12,10,8].

    Returns:
        Diccionario con valores y método usado.
    """
    if metodo == "standard_array":
        valores = [15, 14, 13, 12, 10, 8]
    elif metodo == "3d6":
        valores = [sum(tirar_dados(3, 6)) for _ in range(6)]
    elif metodo == "4d6_drop_lowest":
        valores = []
        for _ in range(6):
            dados = tirar_dados(4, 6)
            dados.sort()
            valores.append(sum(dados[1:]))
    else:
        raise ValueError(f"Método desconocido: {metodo}")

    return {
        "valores": sorted(valores, reverse=True),
        "metodo": metodo
    }


def resolver_ataque(tirada_ataque: ResultadoTirada,
                    ca_objetivo: int) -> Dict[str, Any]:
    """
    Resuelve si un ataque impacta.

    Args:
        tirada_ataque: Resultado de tirar_ataque().
        ca_objetivo: Clase de Armadura del objetivo.

    Returns:
        Diccionario con resultado del ataque.
    """
    # Pifia siempre falla
    if tirada_ataque.pifia:
        return {
            "impacta": False,
            "critico": False,
            "pifia": True,
            "razon": "Pifia (1 natural)"
        }

    # Crítico siempre impacta
    if tirada_ataque.critico:
        return {
            "impacta": True,
            "critico": True,
            "pifia": False,
            "razon": "Crítico (20 natural)"
        }

    # Comparar contra CA
    impacta = tirada_ataque.total >= ca_objetivo
    return {
        "impacta": impacta,
        "critico": False,
        "pifia": False,
        "razon": f"Total {tirada_ataque.total} vs CA {ca_objetivo}"
    }


# =============================================================================
# RESOLUCIÓN DE ATAQUE COMPLETO (para pipeline)
# =============================================================================

@dataclass
class ResultadoAtaqueCompleto:
    """
    Resultado completo de resolver un ataque.
    
    Diseñado para que el pipeline solo transforme esto en eventos,
    sin tener que conocer reglas de combate.
    """
    # Tirada de ataque
    tirada_ataque: ResultadoTirada
    bonificador_ataque: int
    total_ataque: int
    
    # Estado
    es_critico: bool
    es_pifia: bool
    impacta: bool  # True si total >= CA objetivo (o crítico)
    
    # Daño (None si pifia o fallo)
    tirada_daño: Optional[ResultadoTirada] = None
    dados_daño: List[int] = field(default_factory=list)
    modificador_daño: int = 0
    daño_total: int = 0
    tipo_daño: str = "contundente"
    
    # Metadata
    arma_id: str = "unarmed"
    arma_nombre: str = "Desarmado"
    expresion_daño: str = "1d4"
    modo: str = "normal"  # normal, ventaja, desventaja


def resolver_ataque_completo(
    compendio,
    arma_id: str = "unarmed",
    bonificador_ataque: int = 0,
    modificador_daño: int = 0,
    ca_objetivo: int = 10,
    modo: str = "normal"
) -> ResultadoAtaqueCompleto:
    """
    Resuelve un ataque completo: tirada, impacto, daño.
    
    Esta función encapsula TODA la lógica de reglas de ataque.
    El pipeline solo debe llamarla y transformar el resultado en eventos.
    
    Args:
        compendio: CompendioMotor para obtener datos del arma
        arma_id: ID del arma o "unarmed"
        bonificador_ataque: Bonificador total a la tirada (Fuerza/Destreza + competencia)
        modificador_daño: Modificador al daño (Fuerza/Destreza normalmente)
        ca_objetivo: Clase de Armadura del objetivo
        modo: "normal", "ventaja", "desventaja"
    
    Returns:
        ResultadoAtaqueCompleto con toda la información
    """
    # Obtener datos del arma
    arma = None
    expresion_daño = "1d4"
    tipo_daño = "contundente"
    arma_nombre = "Desarmado"
    
    if arma_id and arma_id != "unarmed":
        arma = compendio.obtener_arma(arma_id)
        if arma:
            expresion_daño = arma.get("daño", "1d6")
            tipo_daño = arma.get("tipo_daño", "cortante")
            arma_nombre = arma.get("nombre", arma_id)
    
    # Determinar tipo de tirada
    tipo_tirada = TipoTirada.NORMAL
    if modo == "ventaja":
        tipo_tirada = TipoTirada.VENTAJA
    elif modo == "desventaja":
        tipo_tirada = TipoTirada.DESVENTAJA
    
    # Tirada de ataque
    tirada_ataque = tirar(f"1d20+{bonificador_ataque}", tipo_tirada)
    
    es_critico = tirada_ataque.critico
    es_pifia = tirada_ataque.pifia
    
    # Determinar si impacta
    # Crítico siempre impacta, pifia siempre falla
    if es_critico:
        impacta = True
    elif es_pifia:
        impacta = False
    else:
        impacta = tirada_ataque.total >= ca_objetivo
    
    # Inicializar resultado
    resultado = ResultadoAtaqueCompleto(
        tirada_ataque=tirada_ataque,
        bonificador_ataque=bonificador_ataque,
        total_ataque=tirada_ataque.total,
        es_critico=es_critico,
        es_pifia=es_pifia,
        impacta=impacta,
        arma_id=arma_id,
        arma_nombre=arma_nombre,
        expresion_daño=expresion_daño,
        tipo_daño=tipo_daño,
        modo=modo
    )
    
    # Calcular daño solo si impacta
    if impacta:
        tirada_daño = tirar(expresion_daño)
        dados = tirada_daño.dados.copy()
        daño_base = tirada_daño.total
        
        # Crítico: tirar dados extra (no duplicar modificador)
        if es_critico:
            tirada_extra = tirar(expresion_daño)
            dados.extend(tirada_extra.dados)
            daño_base += tirada_extra.total
        
        daño_total = daño_base + modificador_daño
        
        resultado.tirada_daño = tirada_daño
        resultado.dados_daño = dados
        resultado.modificador_daño = modificador_daño
        resultado.daño_total = max(0, daño_total)  # Mínimo 0
    
    return resultado
