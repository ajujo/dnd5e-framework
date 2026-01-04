# Esquema: Ficha de Personaje

Archivo: `personaje.json`

## Estructura
```json
{
  "id": "string (uuid)",
  "nombre": "string",
  "jugador": "string",
  
  "raza": {
    "nombre": "string",
    "velocidad": "number (pies)",
    "tamaño": "string (Pequeño|Mediano|Grande)",
    "idiomas": ["string"],
    "rasgos": ["string"]
  },
  
  "clase": {
    "nombre": "string",
    "nivel": "number (1-20)",
    "dado_golpe": "string (d6|d8|d10|d12)",
    "competencias_salvacion": ["string"],
    "competencias_habilidades": ["string"],
    "competencias_armaduras": ["string"],
    "competencias_armas": ["string"]
  },
  
  "trasfondo": {
    "nombre": "string",
    "competencias_habilidades": ["string"],
    "idiomas": ["string"],
    "equipo_inicial": ["string"],
    "rasgo_personalidad": "string",
    "ideal": "string",
    "vinculo": "string",
    "defecto": "string"
  },
  
  "atributos": {
    "fuerza": "number (1-30)",
    "destreza": "number (1-30)",
    "constitucion": "number (1-30)",
    "inteligencia": "number (1-30)",
    "sabiduria": "number (1-30)",
    "carisma": "number (1-30)"
  },
  
  "estadisticas_derivadas": {
    "puntos_golpe_maximo": "number",
    "puntos_golpe_actual": "number",
    "puntos_golpe_temporal": "number",
    "clase_armadura": "number",
    "iniciativa": "number",
    "velocidad": "number",
    "bonificador_competencia": "number"
  },
  
  "habilidades": {
    "acrobacias": { "competente": "boolean", "modificador": "number" },
    "arcanos": { "competente": "boolean", "modificador": "number" },
    "atletismo": { "competente": "boolean", "modificador": "number" },
    "engaño": { "competente": "boolean", "modificador": "number" },
    "historia": { "competente": "boolean", "modificador": "number" },
    "interpretacion": { "competente": "boolean", "modificador": "number" },
    "intimidacion": { "competente": "boolean", "modificador": "number" },
    "investigacion": { "competente": "boolean", "modificador": "number" },
    "juego_manos": { "competente": "boolean", "modificador": "number" },
    "medicina": { "competente": "boolean", "modificador": "number" },
    "naturaleza": { "competente": "boolean", "modificador": "number" },
    "percepcion": { "competente": "boolean", "modificador": "number" },
    "perspicacia": { "competente": "boolean", "modificador": "number" },
    "persuasion": { "competente": "boolean", "modificador": "number" },
    "religion": { "competente": "boolean", "modificador": "number" },
    "sigilo": { "competente": "boolean", "modificador": "number" },
    "supervivencia": { "competente": "boolean", "modificador": "number" },
    "trato_animales": { "competente": "boolean", "modificador": "number" }
  },
  
  "estados": {
    "inconsciente": "boolean",
    "estable": "boolean",
    "muerto": "boolean",
    "condiciones": ["string"]
  },
  
  "recursos": {
    "ranuras_conjuro": {
      "nivel_1": { "maximo": "number", "usadas": "number" },
      "nivel_2": { "maximo": "number", "usadas": "number" },
      "nivel_3": { "maximo": "number", "usadas": "number" },
      "nivel_4": { "maximo": "number", "usadas": "number" },
      "nivel_5": { "maximo": "number", "usadas": "number" }
    },
    "dados_golpe": { "maximo": "number", "usados": "number" },
    "experiencia": "number"
  },
  
  "dinero": {
    "pc": "number",
    "pp": "number",
    "pe": "number",
    "po": "number",
    "ppt": "number"
  }
}
```

## Notas

- `id`: Generado automáticamente al crear el personaje
- Los modificadores de habilidad se calculan automáticamente
- `condiciones`: Lista de estados especiales (envenenado, asustado, etc.)
- El dinero usa las abreviaturas oficiales: pc (cobre), pp (plata), pe (electro), po (oro), ppt (platino)
