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
