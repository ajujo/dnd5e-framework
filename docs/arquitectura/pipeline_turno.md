# Pipeline de Turno

## Visión General

El Pipeline de Turno es el **orquestador central** del sistema.
Recibe texto del jugador y devuelve un resultado estructurado.
```
Texto jugador
     ↓
┌─────────────────────────────────────────┐
│           PipelineTurno                 │
│                                         │
│  1. Normalizar (texto → estructura)     │
│  2. ¿Clarificar? → pregunta + opciones  │
│  3. Validar (¿es legal?)                │
│  4. ¿Rechazar? → motivo + sugerencia    │
│  5. Ejecutar → eventos + cambios        │
│  6. Narrar → mensaje_dm (opcional)      │
│                                         │
└─────────────────────────────────────────┘
     ↓
ResultadoPipeline
```

## Tipos de Resultado

### NECESITA_CLARIFICAR
```json
{
  "tipo": "necesita_clarificar",
  "pregunta": "¿A quién quieres atacar?",
  "opciones": [
    {"id": "goblin_1", "texto": "Goblin"},
    {"id": "goblin_2", "texto": "Goblin arquero"}
  ]
}
```

### ACCION_RECHAZADA
```json
{
  "tipo": "accion_rechazada",
  "motivo": "La daga no está equipada (modo estricto)",
  "sugerencia": "Usa una interacción de objeto para equiparla"
}
```

### ACCION_APLICADA
```json
{
  "tipo": "accion_aplicada",
  "eventos": [
    {
      "tipo": "ataque_realizado",
      "actor_id": "pc_1",
      "datos": {
        "objetivo_id": "goblin_1",
        "tirada_d20": 15,
        "total": 20,
        "es_critico": false
      }
    },
    {
      "tipo": "daño_calculado",
      "actor_id": "pc_1",
      "datos": {
        "objetivo_id": "goblin_1",
        "daño_total": 8,
        "tipo_daño": "cortante"
      }
    }
  ],
  "cambios_estado": {
    "accion_usada": true,
    "daño_infligido": {"objetivo_id": "goblin_1", "cantidad": 8}
  },
  "mensaje_dm": "¡Thorin conecta un golpe certero!"
}
```

## Uso
```python
from motor import PipelineTurno, CompendioMotor, ContextoEscena

# Crear pipeline
compendio = CompendioMotor()
pipeline = PipelineTurno(
    compendio,
    strict_equipment=False,  # True = modo estricto
    narrador_callback=mi_llm_narrador  # Opcional
)

# Procesar acción
resultado = pipeline.procesar(
    texto_jugador="Ataco al goblin con mi espada",
    contexto=mi_contexto,
    estado_combate=mi_estado
)

# Manejar resultado
if resultado.tipo == TipoResultado.NECESITA_CLARIFICAR:
    mostrar_pregunta(resultado.pregunta, resultado.opciones)
elif resultado.tipo == TipoResultado.ACCION_RECHAZADA:
    mostrar_error(resultado.motivo, resultado.sugerencia)
elif resultado.tipo == TipoResultado.ACCION_APLICADA:
    aplicar_cambios(resultado.cambios_estado)
    mostrar_narrativa(resultado.mensaje_dm)
```

## Eventos

Los eventos son la "moneda" del sistema. El LLM los recibe para narrar.

| Tipo | Descripción |
|------|-------------|
| `ataque_realizado` | Tirada de ataque completada |
| `daño_calculado` | Daño determinado (si impacta) |
| `conjuro_lanzado` | Conjuro ejecutado |
| `movimiento_realizado` | Personaje se movió |
| `prueba_habilidad` | Tirada de habilidad |
| `accion_generica` | Dash, Dodge, etc. |

## Integración con LLM

El LLM se conecta en **2 puntos únicamente**:

1. **Fallback de normalización**: Si el texto es ambiguo
2. **Generación de narrativa**: Recibe eventos, devuelve texto
```python
# Fallback de normalización
def llm_normalizar(prompt, contexto):
    # Llamar al LLM para parsear texto ambiguo
    return {"objetivo_id": "goblin_1"}

# Generación de narrativa
def llm_narrar(eventos, contexto):
    # Llamar al LLM para generar texto narrativo
    return "¡Thorin blande su espada con furia!"

pipeline = PipelineTurno(
    compendio,
    llm_callback=llm_normalizar,
    narrador_callback=llm_narrar
)
```

El LLM **NO** decide reglas. Solo rellena campos y genera texto.
