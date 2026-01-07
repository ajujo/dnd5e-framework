## Nota de Arquitectura — Uso de CompendioMotor

### Principio
El acceso al compendio **no debe depender de estado global** dentro de la lógica del juego.

### Regla general
- **Módulos y clases internas** (combate, validación, reglas):
  - Reciben `CompendioMotor` **por inyección** en el constructor.
  - ❌ No llaman a `obtener_compendio_motor()` internamente.

- **Punto de entrada** (CLI, `main.py`, scripts):
  - Crea la instancia de `CompendioMotor`.
  - La pasa explícitamente a los módulos que la necesitan.

### Patrón recomendado (híbrido)
```text
main.py / cli.py
   └── crea CompendioMotor()
         ├── MotorCombate(compendio)
         ├── ValidadorAcciones(compendio)
         └── otros módulos
