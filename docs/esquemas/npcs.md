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
