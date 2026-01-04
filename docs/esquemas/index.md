# Esquema: Índice de Partidas

Archivo: `saves/index.json`

## Estructura
```json
{
  "partidas": [
    {
      "id": "string (uuid)",
      "nombre": "string",
      "personaje": "string (nombre del personaje)",
      "clase": "string",
      "nivel": "number",
      "setting": "string",
      "fecha_creacion": "string (ISO 8601)",
      "fecha_ultima_sesion": "string (ISO 8601)",
      "carpeta": "string (nombre de la carpeta en /saves/)"
    }
  ],
  
  "ultima_partida": "string (id) | null"
}
```

## Notas

- Se actualiza automáticamente al crear, guardar o eliminar partidas
- `ultima_partida`: Permite opción "Continuar" rápida
- `carpeta`: Referencia a la subcarpeta donde están los archivos de esa partida
```

---

### Tarea 2.11: Crear estructura de carpetas para esquemas y documentación

**Qué se va a hacer:**  
Crear las carpetas necesarias dentro de `docs/` para organizar los esquemas.

**Por qué es necesaria:**  
Mantener la documentación organizada facilita su consulta y mantenimiento.

**Conocimientos mínimos requeridos:**  
- Crear carpetas

**Resultado esperado:**  
Estructura de carpetas creada.

**Comando:**
```
mkdir -p docs/esquemas
```

**Estructura resultante:**
```
docs/
└── esquemas/
    ├── personaje.md
    ├── inventario.md
    ├── mundo.md
    ├── combate.md
    ├── npcs.md
    ├── historial.md
    ├── meta.md
    └── index.md
