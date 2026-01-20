# Arquitectura del Motor de Combate

## Resumen

El sistema de combate separa responsabilidades:

- **Motor** (`src/motor/`): Reglas D&D 5e puras
- **Orquestador** (`src/orquestador/`): Integra motor + LLM
- **CLI** (`src/cli_aventura.py`): Interfaz de usuario

## Flujo de un turno de combate

```
Usuario: "ataco al esqueleto"
         │
         ▼
┌────────────────────┐
│   NormalizadorAcciones   │  Interpreta texto → AccionNormalizada
└──────────┬─────────┘
           ▼
┌────────────────────┐
│   ValidadorAcciones   │  Verifica si la acción es válida
└──────────┬─────────┘
           ▼
┌────────────────────┐
│   PipelineTurno    │  Ejecuta la acción, genera eventos
└──────────┬─────────┘
           ▼
┌────────────────────┐
│   GestorCombate    │  Aplica cambios (daño, condiciones)
└──────────┬─────────┘
           ▼
┌────────────────────┐
│   NarradorLLM      │  Genera narrativa inmersiva
└──────────────────────┘
```

## Componentes clave

### GestorCombate (`src/motor/gestor_combate.py`)
- Maneja combatientes (PCs, NPCs)
- Control de turnos e iniciativa
- Aplicación de daño y condiciones

### PipelineTurno (`src/motor/pipeline_turno.py`)
- Orquesta el flujo de una acción
- Genera eventos estructurados
- Nunca modifica estado directamente

### OrquestadorCombate (`src/orquestador/combate_integrado.py`)
- Conecta motor con LLM
- Ejecuta turnos de enemigos (IA)
- Detecta victoria/derrota

### DMCerebro (`src/orquestador/dm_cerebro.py`)
- Punto de entrada principal
- Gestiona modos (exploración, combate)
- Procesa herramientas del LLM
