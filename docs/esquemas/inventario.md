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
