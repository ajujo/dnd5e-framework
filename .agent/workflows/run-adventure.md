---
description: Cómo ejecutar la aventura D&D 5e
---

# Ejecutar Aventura

## Requisitos previos
1. Python 3.11+ instalado
2. LM Studio ejecutándose en `http://localhost:1234`
3. Modelo LLM cargado (recomendado: Qwen 32B o similar)

## Pasos

// turbo
1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

// turbo
2. Ejecutar la aventura:
```bash
python src/cli_aventura.py
```

### Opciones de ejecución

| Flag | Descripción |
|------|-------------|
| `--continuar` | Continuar última partida guardada |
| `--cargar ID` | Cargar personaje específico por ID |
| `--debug` | Activar modo debug |
| `--lite` | Perfil para modelos 7B-14B |
| `--normal` | Perfil para modelos 14B-32B (default) |
| `--completo` | Perfil para modelos 32B-80B+ |

### Comandos en juego

| Comando | Descripción |
|---------|-------------|
| `/ayuda` | Mostrar ayuda |
| `/estado` | Ver estado del personaje |
| `/inventario` | Ver inventario |
| `/xp` | Ver experiencia |
| `/nivelup` | Subir de nivel |
| `/combate` | Ver estado del combate |
| `/guardar` | Guardar partida |
| `/salir` | Guardar y salir |
