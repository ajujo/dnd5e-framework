#!/bin/bash

# =============================================================================
# TAREA 2.24: Refinamiento de Esquemas
# Ejecutar desde la raíz del proyecto: bash implementar_refinamiento.sh
# =============================================================================

set -e  # Salir si hay error

echo "=============================================="
echo "  TAREA 2.24: Refinamiento de Esquemas"
echo "=============================================="
echo ""

# -----------------------------------------------------------------------------
# 1. Actualizar docs/esquemas/personaje.md
# -----------------------------------------------------------------------------
echo "→ Actualizando docs/esquemas/personaje.md..."

cat > docs/esquemas/personaje.md << 'EOF'
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
EOF

echo "   ✓ personaje.md actualizado"

# -----------------------------------------------------------------------------
# 2. Actualizar docs/esquemas/inventario.md
# -----------------------------------------------------------------------------
echo "→ Actualizando docs/esquemas/inventario.md..."

cat > docs/esquemas/inventario.md << 'EOF'
# Esquema: Inventario

Archivo: `inventario.json`

## Estructura
```json
{
  "personaje_id": "string (uuid)",

  "equipado": {
    "armadura": "string (instancia_id) | null",
    "escudo": "string (instancia_id) | null",
    "arma_principal": "string (instancia_id) | null",
    "arma_secundaria": "string (instancia_id) | null"
  },

  "objetos": [
    {
      "instancia_id": "string (uuid)",
      "compendio_ref": "string (id del compendio) | null",
      "nombre": "string",
      "cantidad": "number",
      "peso_unitario_lb": "number",
      "categoria": "string (arma|armadura|escudo|consumible|herramienta|municion|contenedor|miscelanea)",
      "is_magical": "boolean",
      "descripcion": "string",
      "propiedades": {}
    }
  ],

  "capacidad_carga": {
    "peso_actual_lb": "number",
    "peso_actual_kg": "number",
    "peso_maximo_lb": "number | null",
    "peso_maximo_kg": "number | null"
  }
}
```

## Sistema de IDs

- `instancia_id`: UUID único para este objeto en esta partida
- `compendio_ref`: Referencia al ID del compendio de origen (ej: "espada_larga")
- Si `compendio_ref` es `null`, es un objeto único/personalizado

Esto permite:
- Tener múltiples espadas largas, cada una con su propio `instancia_id`
- Rastrear el origen de cada objeto
- Personalizar objetos sin perder la referencia

## Cálculos del Motor

| Campo | Fórmula | Notas |
|-------|---------|-------|
| `peso_actual_lb` | `Σ(objeto.peso_unitario_lb × objeto.cantidad)` | Suma de todos los objetos |
| `peso_actual_kg` | `peso_actual_lb × 0.453592` | Conversión automática |
| `peso_maximo_lb` | `15 × Fuerza` | Regla estándar D&D 5e |
| `peso_maximo_kg` | `peso_maximo_lb × 0.453592` | Conversión automática |

> **Nota**: Los valores `null` en `peso_maximo_*` indican "pendiente de calcular". El motor los calcula al cargar la partida.

## Propiedades por Categoría

El campo `propiedades` varía según la categoría del objeto:

### Armas
```json
{
  "daño": "string (ej: 1d8)",
  "tipo_daño": "string (cortante|perforante|contundente)",
  "propiedades_arma": ["string"],
  "bonificador_magico": "number | null"
}
```

### Armaduras
```json
{
  "ca_base": "number",
  "max_mod_destreza": "number | null",
  "requisito_fuerza": "number | null",
  "desventaja_sigilo": "boolean",
  "bonificador_magico": "number | null"
}
```

### Consumibles
```json
{
  "efecto": "string",
  "usos_restantes": "number | null"
}
```

## Implementación por Versión

| Campo | V1 | V2+ | Notas |
|-------|:--:|:---:|-------|
| `equipado.*` | ✓ | ✓ | |
| `objetos[]` | ✓ | ✓ | |
| `capacidad_carga` | ✓ | ✓ | |
| `propiedades.bonificador_magico` | ✗ | ✓ | Siempre `null` en V1 |

## Notas

- El peso en el compendio está en libras (fiel al SRD)
- El motor hace conversiones a kg automáticamente
- `equipado.*` referencia `instancia_id` de objetos en el array `objetos[]`
- Al equipar/desequipar, solo cambian las referencias, no se mueven objetos
EOF

echo "   ✓ inventario.md actualizado"

# -----------------------------------------------------------------------------
# 3. Actualizar docs/esquemas/combate.md
# -----------------------------------------------------------------------------
echo "→ Actualizando docs/esquemas/combate.md..."

cat > docs/esquemas/combate.md << 'EOF'
# Esquema: Estado de Combate

Archivo: `combate.json`

## Estructura
```json
{
  "activo": "boolean",

  "combatientes": [
    {
      "instancia_id": "string (uuid)",
      "compendio_ref": "string (id del compendio) | null",
      "nombre": "string",
      "tipo": "string (jugador|aliado|enemigo|neutral)",
      "iniciativa": "number",
      "puntos_golpe_actual": "number",
      "puntos_golpe_maximo": "number",
      "clase_armadura": "number",
      "condiciones": ["string"],
      "es_su_turno": "boolean",
      "posicion": {
        "x": "number | null",
        "y": "number | null"
      }
    }
  ],

  "orden_turnos": ["string (instancia_ids ordenados por iniciativa)"],

  "turno_actual": {
    "combatiente_id": "string (instancia_id)",
    "indice": "number",
    "acciones_disponibles": {
      "accion": "boolean",
      "accion_bonus": "boolean",
      "reaccion": "boolean",
      "movimiento_restante": "number (pies)"
    }
  },

  "ronda": "number",

  "historial_ronda": [
    {
      "combatiente_id": "string (instancia_id)",
      "combatiente_nombre": "string",
      "accion": "string",
      "objetivo_id": "string | null",
      "objetivo_nombre": "string | null",
      "resultado": "string",
      "tirada": "number | null",
      "daño": "number | null",
      "momento": "string (ISO8601)"
    }
  ],

  "ambiente": {
    "descripcion": "string",
    "terreno_dificil": "boolean",
    "cobertura_disponible": "boolean",
    "iluminacion": "string (brillante|tenue|oscuridad)"
  }
}
```

## Sistema de IDs

- `instancia_id`: UUID único para este combatiente en este combate
- `compendio_ref`: Referencia al monstruo/NPC del compendio (ej: "goblin")

### Ejemplo: 3 Goblins en combate
```json
{
  "combatientes": [
    {
      "instancia_id": "a1b2c3d4-...",
      "compendio_ref": "goblin",
      "nombre": "Goblin 1",
      "puntos_golpe_actual": 7
    },
    {
      "instancia_id": "e5f6g7h8-...",
      "compendio_ref": "goblin",
      "nombre": "Goblin 2",
      "puntos_golpe_actual": 7
    },
    {
      "instancia_id": "i9j0k1l2-...",
      "compendio_ref": "goblin",
      "nombre": "Goblin Líder",
      "puntos_golpe_actual": 10
    }
  ]
}
```

## Flujo del Combate

1. **Inicio**: `activo = true`, se generan `instancia_id` para cada combatiente
2. **Iniciativa**: El motor tira para todos, ordena `orden_turnos`
3. **Turnos**: Se ejecutan en secuencia, actualizando `turno_actual`
4. **Acciones**: Se registran en `historial_ronda`
5. **Fin de ronda**: `ronda++`, se reinician acciones disponibles
6. **Fin de combate**: `activo = false`, se limpia para el siguiente

## Condiciones Soportadas (V1)

- `asustado`
- `cegado`
- `derribado`
- `envenenado`
- `incapacitado`
- `inconsciente`
- `paralizado`
- `petrificado`
- `restringido`

## Implementación por Versión

| Campo | V1 | V2+ | Notas |
|-------|:--:|:---:|-------|
| `combatientes[]` | ✓ | ✓ | |
| `orden_turnos` | ✓ | ✓ | |
| `turno_actual` | ✓ | ✓ | |
| `ronda` | ✓ | ✓ | |
| `historial_ronda` | ✓ | ✓ | |
| `ambiente` | ✓ | ✓ | Simplificado en V1 |
| `posicion` | ✗ | ✓ | `null` en V1 (sin mapa) |

## Notas

- El jugador siempre tiene `instancia_id` igual a su `personaje.id`
- `compendio_ref` es `null` para el jugador y NPCs únicos
- `historial_ronda` proporciona contexto al LLM para narrar
- Al terminar el combate, los enemigos muertos se eliminan; los NPCs aliados persisten en `npcs.json`
EOF

echo "   ✓ combate.md actualizado"

# -----------------------------------------------------------------------------
# 4. Actualizar docs/esquemas/npcs.md
# -----------------------------------------------------------------------------
echo "→ Actualizando docs/esquemas/npcs.md..."

cat > docs/esquemas/npcs.md << 'EOF'
# Esquema: NPCs Conocidos

Archivo: `npcs.json`

## Estructura
```json
{
  "npcs": [
    {
      "instancia_id": "string (uuid)",
      "compendio_ref": "string (id del compendio) | null",
      "nombre": "string",
      "descripcion": "string",
      "ubicacion_conocida": "string",
      "ocupacion": "string",
      "actitud": "string (hostil|desconfiado|neutral|amistoso|aliado)",
      "vivo": "boolean",

      "estadisticas": {
        "puntos_golpe_maximo": "number | null",
        "puntos_golpe_actual": "number | null",
        "clase_armadura": "number | null"
      },

      "notas": "string",

      "interacciones": [
        {
          "dia": "number",
          "tipo": "string (dialogo|combate|comercio|mision)",
          "resumen": "string"
        }
      ],

      "primera_aparicion": {
        "dia": "number",
        "lugar": "string"
      }
    }
  ]
}
```

## Sistema de IDs

- `instancia_id`: UUID único para este NPC en esta partida
- `compendio_ref`: Referencia opcional si el NPC está basado en una criatura del compendio

### Tipos de NPCs

| Tipo | `compendio_ref` | Ejemplo |
|------|-----------------|---------|
| NPC único | `null` | "Aldric el Tabernero" |
| NPC basado en criatura | `"bandido"` | "Jefe de los Bandidos" |
| NPC genérico | `"bandido"` | "Guardia de la puerta" |

## Escala de Actitud

| Valor | Descripción | Comportamiento típico |
|-------|-------------|----------------------|
| `hostil` | Enemigo activo | Atacará si puede |
| `desconfiado` | Receloso | No colabora fácilmente |
| `neutral` | Indiferente | Trato comercial básico |
| `amistoso` | Bien dispuesto | Ayuda si puede |
| `aliado` | Comprometido | Arriesga por el jugador |

## Flujo de Vida de un NPC

1. **Primer encuentro**: Se crea entrada con `instancia_id` y `primera_aparicion`
2. **Interacciones**: Se añaden a `interacciones[]`
3. **En combate**: Sus stats se copian a `combate.combatientes[]`
4. **Post-combate**: Se actualiza `vivo` y `puntos_golpe_actual` si sobrevive
5. **Muerte**: `vivo = false`, se mantiene en historial

## Implementación por Versión

| Campo | V1 | V2+ | Notas |
|-------|:--:|:---:|-------|
| Campos básicos | ✓ | ✓ | |
| `estadisticas` | ✓ | ✓ | |
| `interacciones[]` | ✓ | ✓ | |
| `primera_aparicion` | ✓ | ✓ | |
| Sistema de reputación | ✗ | ✓ | Futuro |
| Árbol de diálogos | ✗ | ✓ | Futuro |

## Notas

- Los NPCs se añaden cuando el jugador los conoce por primera vez
- `estadisticas` solo se rellenan si el NPC ha entrado en combate o es relevante
- `interacciones` proporciona contexto al LLM para coherencia narrativa
- Un NPC muerto permanece en el archivo para referencia histórica
EOF

echo "   ✓ npcs.md actualizado"

# -----------------------------------------------------------------------------
# 5. Actualizar docs/esquemas/historial.md
# -----------------------------------------------------------------------------
echo "→ Actualizando docs/esquemas/historial.md..."

cat > docs/esquemas/historial.md << 'EOF'
# Esquema: Historial de Eventos

Archivo: `historial.json`

## Estructura
```json
{
  "eventos": [
    {
      "id": "string (uuid)",
      "dia": "number",
      "hora": "number (0-23)",
      "tipo": "string (combate|social|exploracion|descanso|nivel|muerte|logro|narrativo)",
      "resumen": "string",
      "detalles": "string | null",
      "importancia": "string (menor|normal|mayor|critico)",
      "participantes": ["string (nombres)"],
      "ubicacion": "string"
    }
  ],

  "resumen_ultima_sesion": "string",

  "resumen_campana": "string",

  "estadisticas_campana": {
    "dias_transcurridos": "number",
    "combates_totales": "number",
    "enemigos_derrotados": "number",
    "npcs_conocidos": "number",
    "muertes_personaje": "number"
  },

  "ultima_actualizacion": "string (ISO8601)"
}
```

## Campos de Resumen

### `resumen_ultima_sesion`

Texto corto (1-3 párrafos) que describe qué pasó la última vez que se jugó.

**Generación**: Al cerrar la sesión, el motor (o el LLM) genera este resumen.

**Uso**: Al abrir la sesión, el LLM lo usa para retomar:
> "La última vez, exploraste las ruinas del templo abandonado y encontraste una puerta sellada con runas. Un grupo de esqueletos te emboscó pero lograste derrotarlos. Te quedaste descansando en la entrada, preparándote para investigar las runas."

### `resumen_campana`

Texto más largo que condensa toda la historia hasta el momento.

**Generación**: Periódicamente (cada X eventos importantes) o bajo demanda.

**Uso**: Cuando el contexto del LLM se llena, se usa este resumen en lugar del historial completo.

## Niveles de Importancia

| Nivel | Cuándo usarlo | Retención |
|-------|---------------|-----------|
| `menor` | Tiradas fallidas, compras menores | Puede omitirse en resúmenes |
| `normal` | Combates, diálogos importantes | Incluir en resúmenes |
| `mayor` | Derrotar jefes, descubrimientos clave | Siempre incluir |
| `critico` | Cambios de trama, muertes, decisiones irreversibles | Nunca omitir |

## Tipos de Evento

| Tipo | Descripción |
|------|-------------|
| `combate` | Inicio/fin de combate, muertes |
| `social` | Diálogos importantes, alianzas |
| `exploracion` | Descubrimientos, nuevas ubicaciones |
| `descanso` | Descansos cortos/largos |
| `nivel` | Subida de nivel |
| `muerte` | Muerte del personaje o NPC importante |
| `logro` | Objetivos cumplidos |
| `narrativo` | Eventos de trama sin categoría específica |

## Flujo de Uso

1. **Durante la partida**: El motor añade eventos a `eventos[]`
2. **Al cerrar sesión**: Se genera `resumen_ultima_sesion`
3. **Al abrir sesión**: El LLM recibe `resumen_ultima_sesion` + últimos N eventos
4. **Periódicamente**: Se actualiza `resumen_campana`
5. **Contexto lleno**: Se usa `resumen_campana` en lugar de eventos individuales

## Implementación por Versión

| Campo | V1 | V2+ | Notas |
|-------|:--:|:---:|-------|
| `eventos[]` | ✓ | ✓ | |
| `resumen_ultima_sesion` | ✓ | ✓ | Puede ser manual en V1 |
| `resumen_campana` | ✓ | ✓ | Puede ser manual en V1 |
| `estadisticas_campana` | ✓ | ✓ | Básicas en V1 |
| Generación automática con LLM | ✗ | ✓ | Manual o básica en V1 |

## Notas

- Solo se guardan eventos relevantes, no cada acción
- El motor decide qué constituye un evento guardable
- `participantes` ayuda a filtrar eventos por NPC/enemigo
- En V1, los resúmenes pueden generarse manualmente o con prompts simples
EOF

echo "   ✓ historial.md actualizado"

# -----------------------------------------------------------------------------
# 6. Actualizar src/persistencia/gestor.py
# -----------------------------------------------------------------------------
echo "→ Actualizando src/persistencia/gestor.py..."

cat > src/persistencia/gestor.py << 'EOF'
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
EOF

echo "   ✓ gestor.py actualizado"

# -----------------------------------------------------------------------------
# 7. Crear test de refinamiento
# -----------------------------------------------------------------------------
echo "→ Creando tests/test_refinamiento.py..."

cat > tests/test_refinamiento.py << 'EOF'
"""
Test de verificación del refinamiento de esquemas (Tarea 2.24).
Ejecutar desde la raíz del proyecto: python tests/test_refinamiento.py
"""

import sys
import os
import json
from pathlib import Path

# Añadir src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from persistencia import obtener_gestor, obtener_compendio


def verificar_esquema_personaje(personaje: dict) -> list:
    """Verifica que el personaje tiene la estructura v1.1 correcta."""
    errores = []

    # Verificar _meta
    if "_meta" not in personaje:
        errores.append("Falta campo '_meta'")
    else:
        if "version_esquema" not in personaje["_meta"]:
            errores.append("Falta '_meta.version_esquema'")
        if "derivados_calculados_en" not in personaje["_meta"]:
            errores.append("Falta '_meta.derivados_calculados_en'")

    # Verificar fuente
    if "fuente" not in personaje:
        errores.append("Falta campo 'fuente'")
    else:
        fuente = personaje["fuente"]
        campos_fuente = [
            "atributos_base", "raza", "clase", "trasfondo",
            "competencias", "equipo_equipado", "dotes", "multiclase"
        ]
        for campo in campos_fuente:
            if campo not in fuente:
                errores.append(f"Falta 'fuente.{campo}'")

        # Verificar que multiclase y dotes existen (aunque vacíos)
        if "dotes" in fuente and not isinstance(fuente["dotes"], list):
            errores.append("'fuente.dotes' debe ser una lista")

    # Verificar derivados
    if "derivados" not in personaje:
        errores.append("Falta campo 'derivados'")
    else:
        derivados = personaje["derivados"]
        campos_derivados = [
            "atributos_finales", "modificadores", "bonificador_competencia",
            "clase_armadura", "iniciativa", "velocidad", "puntos_golpe_maximo",
            "habilidades", "salvaciones"
        ]
        for campo in campos_derivados:
            if campo not in derivados:
                errores.append(f"Falta 'derivados.{campo}'")

    # Verificar estado_actual
    if "estado_actual" not in personaje:
        errores.append("Falta campo 'estado_actual'")
    else:
        if "salvaciones_muerte" not in personaje["estado_actual"]:
            errores.append("Falta 'estado_actual.salvaciones_muerte'")

    return errores


def verificar_esquema_inventario(inventario: dict) -> list:
    """Verifica que el inventario tiene la estructura v1.1 correcta."""
    errores = []

    if "capacidad_carga" not in inventario:
        errores.append("Falta campo 'capacidad_carga'")
    else:
        carga = inventario["capacidad_carga"]
        campos_carga = ["peso_actual_lb", "peso_actual_kg", "peso_maximo_lb", "peso_maximo_kg"]
        for campo in campos_carga:
            if campo not in carga:
                errores.append(f"Falta 'capacidad_carga.{campo}'")

    return errores


def verificar_esquema_combate(combate: dict) -> list:
    """Verifica que el combate tiene la estructura v1.1 correcta."""
    errores = []

    if "ambiente" not in combate:
        errores.append("Falta campo 'ambiente'")
    else:
        ambiente = combate["ambiente"]
        campos_ambiente = ["descripcion", "terreno_dificil", "cobertura_disponible", "iluminacion"]
        for campo in campos_ambiente:
            if campo not in ambiente:
                errores.append(f"Falta 'ambiente.{campo}'")

    return errores


def verificar_esquema_historial(historial: dict) -> list:
    """Verifica que el historial tiene la estructura v1.1 correcta."""
    errores = []

    if "resumen_ultima_sesion" not in historial:
        errores.append("Falta campo 'resumen_ultima_sesion'")

    if "resumen_campana" not in historial:
        errores.append("Falta campo 'resumen_campana'")

    if "estadisticas_campana" not in historial:
        errores.append("Falta campo 'estadisticas_campana'")

    return errores


def verificar_documentacion():
    """Verifica que los archivos de documentación existen y tienen contenido."""
    print("\n=== Verificación de Documentación ===\n")

    docs_dir = Path("docs/esquemas")
    archivos_requeridos = [
        "personaje.md", "inventario.md", "combate.md",
        "npcs.md", "historial.md"
    ]

    errores = []
    for archivo in archivos_requeridos:
        ruta = docs_dir / archivo
        if not ruta.exists():
            errores.append(f"No existe: {ruta}")
        else:
            contenido = ruta.read_text()
            # Verificar que contiene secciones clave
            if "Implementación por Versión" not in contenido:
                errores.append(f"{archivo}: Falta sección 'Implementación por Versión'")
            if "V1" not in contenido:
                errores.append(f"{archivo}: Falta referencia a V1")
            print(f"  ✓ {archivo} existe y tiene estructura correcta")

    if errores:
        for e in errores:
            print(f"  ✗ {e}")
        return False

    print("\n✓ Documentación verificada correctamente\n")
    return True


def test_crear_partida_v11():
    """Verifica que las partidas nuevas usan el esquema v1.1."""
    print("\n=== Test de Creación de Partida (Esquema v1.1) ===\n")

    import shutil

    # Limpiar carpeta de test si existe
    test_dir = Path("./saves_test_v11")
    if test_dir.exists():
        shutil.rmtree(test_dir)

    # Crear gestor con carpeta de test
    gestor = obtener_gestor(str(test_dir))

    # Crear partida
    partida_id = gestor.crear_partida(
        nombre="Test Refinamiento",
        nombre_personaje="Eldric",
        clase="Mago",
        setting="Forgotten Realms"
    )

    if not partida_id:
        print("  ✗ Error creando partida")
        return False

    print(f"  ✓ Partida creada: {partida_id[:8]}...")

    # Cargar partida
    datos = gestor.cargar_partida(partida_id)
    if not datos:
        print("  ✗ Error cargando partida")
        return False

    todos_errores = []

    # Verificar personaje
    errores = verificar_esquema_personaje(datos["personaje"])
    if errores:
        todos_errores.extend([f"personaje: {e}" for e in errores])
    else:
        print("  ✓ Esquema personaje.json correcto")
        # Verificar valores específicos
        meta = datos["personaje"]["_meta"]
        print(f"    - version_esquema: {meta['version_esquema']}")
        print(f"    - Tiene fuente/derivados separados: ✓")

    # Verificar inventario
    errores = verificar_esquema_inventario(datos["inventario"])
    if errores:
        todos_errores.extend([f"inventario: {e}" for e in errores])
    else:
        print("  ✓ Esquema inventario.json correcto")
        carga = datos["inventario"]["capacidad_carga"]
        print(f"    - Tiene peso_actual_lb: {carga['peso_actual_lb']}")
        print(f"    - Tiene peso_maximo_lb: {carga['peso_maximo_lb']} (calculable)")

    # Verificar combate
    errores = verificar_esquema_combate(datos["combate"])
    if errores:
        todos_errores.extend([f"combate: {e}" for e in errores])
    else:
        print("  ✓ Esquema combate.json correcto")
        print(f"    - Tiene ambiente.iluminacion: {datos['combate']['ambiente']['iluminacion']}")

    # Verificar historial
    errores = verificar_esquema_historial(datos["historial"])
    if errores:
        todos_errores.extend([f"historial: {e}" for e in errores])
    else:
        print("  ✓ Esquema historial.json correcto")
        print(f"    - Tiene resumen_ultima_sesion: ✓")
        print(f"    - Tiene estadisticas_campana: ✓")

    # Limpiar
    shutil.rmtree(test_dir)
    print("\n  ✓ Carpeta de test limpiada")

    if todos_errores:
        print("\n  ERRORES ENCONTRADOS:")
        for e in todos_errores:
            print(f"    ✗ {e}")
        return False

    print("\n✓ Todos los esquemas cumplen v1.1\n")
    return True


def test_instancia_vs_compendio():
    """Verifica la diferencia conceptual entre instancia_id y compendio_ref."""
    print("\n=== Test Conceptual: instancia_id vs compendio_ref ===\n")

    # Simular estructura de combatiente
    combatiente_ejemplo = {
        "instancia_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "compendio_ref": "goblin",
        "nombre": "Goblin Arquero",
        "puntos_golpe_actual": 5
    }

    print("  Ejemplo de combatiente:")
    print(f"    instancia_id: {combatiente_ejemplo['instancia_id'][:8]}... (único en esta partida)")
    print(f"    compendio_ref: {combatiente_ejemplo['compendio_ref']} (referencia al compendio)")
    print(f"    nombre: {combatiente_ejemplo['nombre']} (personalizable)")

    # Verificar que el compendio tiene la referencia
    compendio = obtener_compendio()
    goblin = compendio.obtener_monstruo("goblin")

    if goblin:
        print(f"\n  ✓ compendio_ref 'goblin' existe en el compendio")
        print(f"    - PG base: {goblin['puntos_golpe']}")
        print(f"    - CA base: {goblin['clase_armadura']}")
    else:
        print("\n  ✗ No se encontró 'goblin' en el compendio")
        return False

    print("\n  Esto permite:")
    print("    - Tener 3 goblins con instancia_id diferentes")
    print("    - Todos referencian compendio_ref='goblin'")
    print("    - Cada uno puede tener nombre y estado únicos")

    print("\n✓ Conceptos de ID verificados\n")
    return True


def main():
    """Ejecuta todas las verificaciones."""
    print("\n" + "="*60)
    print("  VERIFICACIÓN DE REFINAMIENTO DE ESQUEMAS (Tarea 2.24)")
    print("="*60)

    resultados = []

    # Test 1: Documentación
    resultados.append(("Documentación", verificar_documentacion()))

    # Test 2: Crear partida con esquema v1.1
    resultados.append(("Esquemas v1.1", test_crear_partida_v11()))

    # Test 3: Conceptos de ID
    resultados.append(("IDs instancia/compendio", test_instancia_vs_compendio()))

    # Resumen
    print("="*60)
    print("  RESUMEN")
    print("="*60)

    todos_ok = True
    for nombre, resultado in resultados:
        estado = "✓" if resultado else "✗"
        print(f"  {estado} {nombre}")
        if not resultado:
            todos_ok = False

    print("="*60)

    if todos_ok:
        print("  ✓ TODOS LOS TESTS DE REFINAMIENTO PASARON")
    else:
        print("  ✗ ALGUNOS TESTS FALLARON")

    print("="*60 + "\n")

    return todos_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF

echo "   ✓ test_refinamiento.py creado"

# -----------------------------------------------------------------------------
# 8. Resumen final
# -----------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "  IMPLEMENTACIÓN COMPLETADA"
echo "=============================================="
echo ""
echo "Archivos actualizados:"
echo "  - docs/esquemas/personaje.md"
echo "  - docs/esquemas/inventario.md"
echo "  - docs/esquemas/combate.md"
echo "  - docs/esquemas/npcs.md"
echo "  - docs/esquemas/historial.md"
echo "  - src/persistencia/gestor.py"
echo ""
echo "Archivos creados:"
echo "  - tests/test_refinamiento.py"
echo ""
echo "Siguiente paso:"
echo "  python tests/test_refinamiento.py"
echo ""
