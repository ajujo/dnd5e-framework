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
