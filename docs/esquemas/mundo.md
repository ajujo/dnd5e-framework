# Esquema: Estado del Mundo

Archivo: `mundo.json`

## Estructura
```json
{
  "partida_id": "string (uuid)",
  
  "setting": {
    "nombre": "string (Forgotten Realms|Dark Sun|Greyhawk|Ravenloft|Dragonlance|Eberron)",
    "descripcion": "string",
    "tono": "string (heroico|oscuro|intriga|exploración)"
  },
  
  "ubicacion": {
    "region": "string",
    "lugar": "string",
    "interior": "boolean",
    "descripcion_actual": "string"
  },
  
  "tiempo": {
    "dia": "number",
    "hora": "number (0-23)",
    "periodo": "string (amanecer|mañana|mediodia|tarde|atardecer|noche|madrugada)",
    "clima": "string"
  },
  
  "modo_juego": "string (exploracion|social|combate)",
  
  "aventura_actual": {
    "nombre": "string | null",
    "descripcion": "string | null",
    "objetivo_principal": "string | null",
    "capitulo_actual": "string | null"
  },
  
  "flags": {
    "eventos_completados": ["string"],
    "decisiones_importantes": [
      {
        "id": "string",
        "descripcion": "string",
        "consecuencia": "string"
      }
    ],
    "variables_narrativas": {}
  }
}
```

## Notas

- `setting`: Define el mundo de D&D donde transcurre la partida
- `modo_juego`: Estado actual que informa al motor y al LLM
- `flags`: Sistema flexible para rastrear progreso narrativo
- `variables_narrativas`: Objeto clave-valor para datos específicos de la aventura
