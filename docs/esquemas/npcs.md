# Esquema: NPCs Conocidos

Archivo: `npcs.json`

## Estructura
```json
{
  "npcs": [
    {
      "id": "string (uuid)",
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
          "resumen": "string"
        }
      ]
    }
  ]
}
```

## Notas

- `actitud`: Refleja la relación actual con el jugador
- `estadisticas`: Solo se rellenan si el NPC ha entrado en combate o es relevante
- `interacciones`: Historial resumido para contexto del LLM
- Los NPCs se añaden cuando el jugador los conoce por primera vez
