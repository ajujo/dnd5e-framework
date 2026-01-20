---
description: Cómo crear un nuevo personaje
---

# Crear Personaje

## Pasos

// turbo
1. Ejecutar el creador de personajes:
```bash
python src/cli_creacion.py
```

2. Seguir el asistente interactivo:
   - Elegir raza (9 opciones SRD)
   - Elegir clase (12 opciones SRD)
   - Generar stats (4d6 drop lowest o array estándar)
   - Elegir trasfondo (13 opciones)
   - Nombrar al personaje

3. El personaje se guarda automáticamente en `storage/characters/`

## Verificar personajes existentes

// turbo
```bash
ls storage/characters/
```

## Cargar personaje en aventura

```bash
python src/cli_aventura.py --cargar ID_PERSONAJE
```
