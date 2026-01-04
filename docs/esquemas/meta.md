# Esquema: Metadatos de Partida

Archivo: `meta.json`

## Estructura
```json
{
  "partida_id": "string (uuid)",
  "nombre_partida": "string",
  
  "version_framework": "string (semver)",
  "version_esquemas": "string",
  
  "fecha_creacion": "string (ISO 8601)",
  "fecha_ultima_sesion": "string (ISO 8601)",
  
  "estadisticas": {
    "sesiones_jugadas": "number",
    "tiempo_total_minutos": "number",
    "combates_completados": "number",
    "nivel_maximo_alcanzado": "number"
  },
  
  "configuracion_partida": {
    "perfil_llm": "string (completo|lite)",
    "dificultad": "string (normal|dificil|mortal)",
    "modo_muerte": "string (normal|permanente)"
  },
  
  "notas_jugador": "string"
}
```

## Notas

- `version_framework`: Permite detectar si la partida fue creada con versión anterior
- `version_esquemas`: Para migraciones de estructura de datos
- `notas_jugador`: Campo libre para que el jugador apunte lo que quiera
