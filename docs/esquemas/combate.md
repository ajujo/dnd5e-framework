# Esquema: Estado de Combate

Archivo: `combate.json`

## Estructura
```json
{
  "activo": "boolean",
  
  "combatientes": [
    {
      "id": "string (uuid)",
      "nombre": "string",
      "tipo": "string (jugador|aliado|enemigo|neutral)",
      "iniciativa": "number",
      "puntos_golpe_actual": "number",
      "puntos_golpe_maximo": "number",
      "clase_armadura": "number",
      "condiciones": ["string"],
      "es_su_turno": "boolean"
    }
  ],
  
  "orden_turnos": ["string (ids ordenados por iniciativa)"],
  
  "turno_actual": {
    "combatiente_id": "string",
    "indice": "number",
    "acciones_disponibles": {
      "accion": "boolean",
      "accion_bonus": "boolean",
      "reaccion": "boolean",
      "movimiento_restante": "number"
    }
  },
  
  "ronda": "number",
  
  "historial_ronda": [
    {
      "combatiente_id": "string",
      "accion": "string",
      "resultado": "string",
      "daño": "number | null"
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

## Notas

- `activo`: Si es `false`, no hay combate en curso
- `orden_turnos`: Lista de IDs ordenada de mayor a menor iniciativa
- `turno_actual`: Rastrea qué puede hacer el combatiente activo
- `historial_ronda`: Log de acciones para contexto del LLM
- Cuando el combate termina, se guarda como `activo: false` y se limpia al iniciar el siguiente
