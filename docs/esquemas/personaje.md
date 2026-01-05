# Esquema: Ficha de Personaje

Archivo: `personaje.json`

## Principio de Diseño

Este esquema separa explícitamente:
- **Fuente (source of truth)**: Datos elegidos por el jugador o asignados por el sistema
- **Derivados**: Datos calculados por el motor a partir de la fuente
- **Estado actual**: Valores que cambian durante la partida

> **Regla del motor**: Los campos en `derivados` son calculados y pueden regenerarse en cualquier momento. La fuente de verdad son los campos en `fuente` y `estado_actual`.

## Estructura
```json
{
  "id": "string (uuid)",
  "nombre": "string",
  "jugador": "string",

  "_meta": {
    "version_esquema": "1.1",
    "derivados_calculados_en": "string (ISO8601) | null"
  },

  "fuente": {
    "atributos_base": {
      "fuerza": "number (1-20)",
      "destreza": "number (1-20)",
      "constitucion": "number (1-20)",
      "inteligencia": "number (1-20)",
      "sabiduria": "number (1-20)",
      "carisma": "number (1-20)"
    },

    "raza": {
      "id": "string",
      "nombre": "string",
      "velocidad_base": "number (pies)",
      "tamaño": "string (Pequeño|Mediano|Grande)",
      "bonificadores_atributo": {
        "fuerza": "number",
        "destreza": "number",
        "constitucion": "number",
        "inteligencia": "number",
        "sabiduria": "number",
        "carisma": "number"
      },
      "rasgos": ["string"]
    },

    "clase": {
      "id": "string",
      "nombre": "string",
      "nivel": "number (1-20)",
      "dado_golpe": "string (d6|d8|d10|d12)",
      "caracteristica_lanzamiento": "string | null"
    },

    "subclase": "object | null",

    "trasfondo": {
      "id": "string",
      "nombre": "string",
      "rasgo_personalidad": "string",
      "ideal": "string",
      "vinculo": "string",
      "defecto": "string"
    },

    "competencias": {
      "habilidades": ["string"],
      "salvaciones": ["string"],
      "armas": ["string"],
      "armaduras": ["string"],
      "herramientas": ["string"],
      "idiomas": ["string"]
    },

    "expertise": ["string"],

    "equipo_equipado": {
      "armadura_id": "string | null",
      "escudo_id": "string | null",
      "arma_principal_id": "string | null",
      "arma_secundaria_id": "string | null"
    },

    "dotes": [],
    "multiclase": "object | null",

    "conjuros_conocidos": ["string"],
    "conjuros_preparados": ["string"]
  },

  "derivados": {
    "atributos_finales": {
      "fuerza": "number",
      "destreza": "number",
      "constitucion": "number",
      "inteligencia": "number",
      "sabiduria": "number",
      "carisma": "number"
    },

    "modificadores": {
      "fuerza": "number (-5 a +10)",
      "destreza": "number",
      "constitucion": "number",
      "inteligencia": "number",
      "sabiduria": "number",
      "carisma": "number"
    },

    "bonificador_competencia": "number (2-6)",
    "clase_armadura": "number",
    "iniciativa": "number",
    "velocidad": "number (pies)",
    "puntos_golpe_maximo": "number",

    "habilidades": {
      "acrobacias": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "arcanos": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "atletismo": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "engaño": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "historia": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "interpretacion": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "intimidacion": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "investigacion": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "juego_manos": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "medicina": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "naturaleza": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "percepcion": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "perspicacia": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "persuasion": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "religion": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "sigilo": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "supervivencia": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" },
      "trato_animales": { "modificador_total": "number", "competente": "boolean", "expertise": "boolean" }
    },

    "salvaciones": {
      "fuerza": { "modificador_total": "number", "competente": "boolean" },
      "destreza": { "modificador_total": "number", "competente": "boolean" },
      "constitucion": { "modificador_total": "number", "competente": "boolean" },
      "inteligencia": { "modificador_total": "number", "competente": "boolean" },
      "sabiduria": { "modificador_total": "number", "competente": "boolean" },
      "carisma": { "modificador_total": "number", "competente": "boolean" }
    },

    "cd_conjuros": "number | null",
    "bonificador_ataque_conjuros": "number | null"
  },

  "estado_actual": {
    "puntos_golpe_actual": "number",
    "puntos_golpe_temporal": "number",
    "condiciones": ["string"],
    "inconsciente": "boolean",
    "estable": "boolean",
    "muerto": "boolean",
    "salvaciones_muerte": {
      "exitos": "number (0-3)",
      "fracasos": "number (0-3)"
    }
  },

  "recursos": {
    "dados_golpe": {
      "disponibles": "number",
      "maximo": "number"
    },
    "ranuras_conjuro": {
      "nivel_1": { "disponibles": "number", "maximo": "number" },
      "nivel_2": { "disponibles": "number", "maximo": "number" },
      "nivel_3": { "disponibles": "number", "maximo": "number" },
      "nivel_4": { "disponibles": "number", "maximo": "number" },
      "nivel_5": { "disponibles": "number", "maximo": "number" }
    },
    "experiencia": "number"
  },

  "dinero": {
    "pc": "number (piezas de cobre)",
    "pp": "number (piezas de plata)",
    "pe": "number (piezas de electro)",
    "po": "number (piezas de oro)",
    "ppt": "number (piezas de platino)"
  }
}
```

## Cálculos del Motor

El motor calcula `derivados` usando estas fórmulas:

| Campo | Fórmula |
|-------|---------|
| `atributos_finales` | `atributos_base + bonificadores_raza` |
| `modificadores.*` | `floor((atributo - 10) / 2)` |
| `bonificador_competencia` | Tabla por nivel: 1-4→+2, 5-8→+3, 9-12→+4, 13-16→+5, 17-20→+6 |
| `clase_armadura` | Depende de armadura equipada + mod.DES + escudo |
| `iniciativa` | `modificadores.destreza` |
| `velocidad` | `raza.velocidad_base` (modificable por armadura/efectos) |
| `puntos_golpe_maximo` | `(dado_golpe_max nivel 1) + (promedio × (nivel-1)) + (mod.CON × nivel)` |
| `habilidades.*.modificador_total` | `mod.atributo + (competente ? bonif_comp : 0) + (expertise ? bonif_comp : 0)` |
| `salvaciones.*.modificador_total` | `mod.atributo + (competente ? bonif_comp : 0)` |

## Implementación por Versión

| Campo | V1 | V2+ | Notas |
|-------|:--:|:---:|-------|
| `fuente.atributos_base` | ✓ | ✓ | Obligatorio |
| `fuente.raza` | ✓ | ✓ | Solo razas SRD en V1 |
| `fuente.clase` | ✓ | ✓ | Nivel máximo 5 en V1 |
| `fuente.subclase` | ✗ | ✓ | `null` en V1 |
| `fuente.trasfondo` | ✓ | ✓ | Simplificado en V1 |
| `fuente.competencias` | ✓ | ✓ | |
| `fuente.expertise` | ✗ | ✓ | `[]` en V1 |
| `fuente.dotes` | ✗ | ✓ | `[]` en V1 |
| `fuente.multiclase` | ✗ | ✓ | `null` en V1 |
| `fuente.conjuros_*` | ✓ | ✓ | Solo conjuros del micro-compendio |
| `derivados.*` | ✓ | ✓ | Todos calculados |
| `estado_actual.*` | ✓ | ✓ | |
| `recursos.ranuras_conjuro` | ✓ | ✓ | Solo niveles 1-3 relevantes en V1 |

## Notas

- `id`: Generado automáticamente (UUID) al crear el personaje
- `_meta.derivados_calculados_en`: Timestamp de último recálculo, permite invalidar caché
- Los campos marcados V2+ existen en el esquema pero se inicializan vacíos/null
- El motor debe recalcular `derivados` cuando cambie cualquier campo de `fuente`
