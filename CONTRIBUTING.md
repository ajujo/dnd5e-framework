# Contribuir al proyecto

## Estructura del proyecto

```
dnd5e-framework/
├── .agent/workflows/      # Workflows para desarrollo
├── compendio/             # Datos D&D (monstruos, armas, etc.)
├── config/                # Configuración de aventuras
├── docs/                  # Documentación y SRD
├── src/                   # Código fuente
│   ├── motor/             # Motor de reglas D&D 5e
│   ├── orquestador/       # Integración LLM + Motor
│   └── llm/               # Conexión con LLM
├── storage/               # Personajes y partidas guardadas
└── tests/                 # Tests unitarios
```

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                     EL LLM NO DECIDE REGLAS                     │
│                     EL LLM NARRA Y GUÍA                         │
│                     EL MOTOR DECIDE MECÁNICA                    │
└─────────────────────────────────────────────────────────────────┘
```

## Cómo contribuir

1. Fork del repositorio
2. Crear rama feature: `git checkout -b feature/mi-feature`
3. Hacer cambios y tests
4. Commit: `git commit -m "feat: descripción"`
5. Push y Pull Request

## Convenciones de commits

| Prefijo | Uso |
|---------|-----|
| `feat:` | Nueva funcionalidad |
| `fix:` | Corrección de bug |
| `docs:` | Documentación |
| `refactor:` | Refactorización |
| `test:` | Tests |

## Ejecutar tests

```bash
python -m pytest tests/ -v
```

## Configuración LLM

El proyecto usa LM Studio en `http://localhost:1234`. Ver perfiles en `src/llm/__init__.py`.
