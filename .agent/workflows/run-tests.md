---
description: Cómo ejecutar tests del proyecto
---

# Tests

## Ejecutar todos los tests

// turbo
```bash
python -m pytest tests/ -v
```

## Ejecutar tests específicos

// turbo
```bash
# Tests del motor de combate
python -m pytest tests/test_combate.py -v

# Tests del pipeline
python -m pytest tests/test_pipeline_turno.py -v

# Tests del normalizador
python -m pytest tests/test_normalizador.py -v
```

## Verificar personajes

// turbo
```bash
python verificar_personajes.py
```
