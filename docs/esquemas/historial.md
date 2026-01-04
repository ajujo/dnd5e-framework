# Esquema: Historial de Eventos

Archivo: `historial.json`

## Estructura
```json
{
  "eventos": [
    {
      "id": "string (uuid)",
      "dia": "number",
      "hora": "number",
      "tipo": "string (combate|social|exploracion|descanso|nivel|muerte|logro)",
      "resumen": "string",
      "detalles": "string | null",
      "importancia": "string (menor|normal|mayor|critico)"
    }
  ],
  
  "resumen_campana": "string",
  
  "ultima_actualizacion": "string (ISO 8601)"
}
```

## Notas

- `importancia`: Permite filtrar qué enviar al LLM según límite de contexto
- `resumen_campana`: Texto generado periódicamente que condensa la historia
- Solo se guardan eventos relevantes, no cada acción
- El motor decide qué constituye un evento guardable
