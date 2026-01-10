# 🎲 D&D 5e Framework - Aventuras Narrativas con IA

> **Framework de código abierto para jugar partidas de D&D 5e en solitario guiadas por IA, con un motor de combate táctico real y narrativa inmersiva generada por LLM.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![D&D 5e](https://img.shields.io/badge/D%26D-5e%20SRD-red.svg)](https://dnd.wizards.com/resources/systems-reference-document)

---

## 📖 Índice

1. [¿Qué es este proyecto?](#qué-es-este-proyecto)
2. [Estado Actual del Desarrollo](#estado-actual-del-desarrollo)
3. [Características Implementadas](#características-implementadas)
4. [Arquitectura del Sistema](#arquitectura-del-sistema)
5. [Cómo Probarlo](#cómo-probarlo)
6. [Estructura del Proyecto](#estructura-del-proyecto)
7. [Compendio de Datos D&D](#compendio-de-datos-dd)
8. [Mejoras Futuras](#mejoras-futuras)
9. [Cómo Contribuir](#cómo-contribuir)
10. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## ¿Qué es este proyecto?

Este framework permite jugar aventuras de **Dungeons & Dragons 5ª Edición** en solitario, donde una **IA (LLM) actúa como Dungeon Master**, mientras un **motor de reglas mecánicas** se encarga de hacer cumplir las reglas del juego.

### 🎯 Filosofía de diseño

```
┌─────────────────────────────────────────────────────────────────┐
│                     EL LLM NO DECIDE REGLAS                     │
│                     EL LLM NARRA Y GUÍA                         │
│                     EL MOTOR DECIDE MECÁNICA                    │
└─────────────────────────────────────────────────────────────────┘
```

- **El LLM**: Describe escenas, genera diálogos de NPCs, decide narrativamente qué pasa en la historia
- **El Motor**: Tira dados, calcula daño, valida acciones según las reglas D&D 5e
- **El Resultado**: Combates tácticos justos + Narrativa inmersiva

### Ejemplo de juego

```
DM: Bajas las escaleras hacia la cripta. El olor a muerte 
    impregna el aire. Tres figuras se alzan de las sombras...

  ⚔️ ¡COMBATE INICIADO!
  Orden: Esqueleto, Kaelen, Esqueleto, Goblin

  --- Turno de Esqueleto ---
  🎲 Ataque: 15(d20) + 4(mod) = 19 vs CA 18 → ¡Impacta!
  💥 Daño: 4(1d6) + 2(mod) = 6

  La espada oxidada del esqueleto silba a través de las sombras,
  encontrando un hueco en tu defensa con un crujido siniestro.

  ==================================================
  🛡️ TURNO DE KAELEN HOJA LUNAR
  ==================================================
  HP: Esqueleto:13/13 | Kaelen:6/12 | Goblin:7/7

  > ataco al esqueleto

  🎲 Ataque con Espada larga: 18(d20) + 5(mod) = 23 → ¡Impacta!
  💥 Daño: 7(1d8) + 3(mod) = 10

  Tu espada corta el aire con la gracia de la luna creciente, 
  desgarrando huesos con un crujido definitivo...

  💀 ¡Esqueleto cae!
```

---

## Estado Actual del Desarrollo

### ✅ Funcional y probado

| Módulo | Estado | Descripción |
|--------|--------|-------------|
| Creación de personajes | ✅ Completo | Wizard interactivo con todas las razas, clases y trasfondos del SRD |
| Sistema de combate táctico | ✅ Funcional | Iniciativa, ataques, daño, críticos, condiciones |
| Narración LLM | ✅ Funcional | Genera descripciones inmersivas de combates y escenas |
| Persistencia | ✅ Funcional | Guardar/cargar partidas, estado de aventura |
| Adventure Bible | ✅ Estructura | Sistema de aventuras procedurales con actos, revelaciones, NPCs |

### 🔧 En desarrollo activo

| Módulo | Estado | Notas |
|--------|--------|-------|
| Normalización de input con LLM | 📋 Planificado | Entender "rematar al herido" → "ataco al esqueleto con menos HP" |
| Sistema de magia completo | 🔧 Parcial | Estructura presente, falta implementar todos los conjuros |
| Habilidades y tiradas | 🔧 Parcial | Percepción, sigilo, etc. funcionan básicamente |
| IA de enemigos avanzada | 📋 Planificado | Actualmente atacan al azar |

### 📋 Próximamente

- Multijugador (varios PCs)
- Interfaz web
- Generación procedural de dungeons
- Integración con Roll20/Foundry

---

## Características Implementadas

### 1. 🎭 Creación de Personajes Completa

```
$ python src/cli_creacion.py

═══════════════════════════════════════════════════
      CREADOR DE PERSONAJES - D&D 5e
═══════════════════════════════════════════════════

[1] Humano          [4] Elfo del Bosque    [7] Gnomo de Bosque
[2] Elfo Alto       [5] Semielfo           [8] Semiorco
[3] Enano de Montaña [6] Gnomo de Roca     [9] Mediano Piesligeros
...
```

- **9 razas** del SRD con todos sus rasgos
- **12 clases** con características de nivel 1
- **13 trasfondos** con equipo y habilidades
- Generación de stats con 4d6-drop-lowest o array estándar
- Guardado en JSON estructurado

### 2. ⚔️ Sistema de Combate Táctico D&D 5e

El combate respeta las reglas oficiales:

- **Iniciativa real**: Tirada de d20 + modificador de Destreza
- **Orden de turnos**: NPCs y jugador actúan en orden
- **Tiradas de ataque**: d20 + proficiencia + modificador vs CA
- **Daño real**: Dados de arma + modificador
- **Críticos correctos**: d20 natural de 20 = dados x2 (mod x1)
- **Condiciones**: Muerto, inconsciente (más por implementar)

### 3. 🎙️ Narración con LLM

Cada evento de combate o exploración puede ser narrado por el LLM:

- `/sillm` - Activa narración inmersiva
- `/nollm` - Desactiva (solo mecánica)

```
Sin LLM:  "Esqueleto ataca con Espada corta. Falla."

Con LLM:  "La espada oxidada del esqueleto silba como una 
          serpiente enfadada, pero Kaelen esquiva con un 
          susurro de luna plateada—el filo apenas roza el 
          aire donde su sombra aún se alzaba."
```

### 4. 📜 Sistema de Aventuras (Adventure Bible)

Cada aventura se define en un JSON estructurado que incluye:

- **Meta-información**: Tipo de aventura, ambientación
- **Actos**: Con escenas obligatorias y flexibles
- **Revelaciones**: Pistas con múltiples formas de descubrirlas
- **NPCs clave**: Con secretos, actitudes, ubicaciones
- **Relojes**: Timers ocultos que avanzan eventos
- **Side quests**: Misiones secundarias que pueden escalar
- **Contrato de consistencia**: Qué es canon, flexible o impro

### 5. 💾 Persistencia

- Guardar partida con `/guardar`
- Cargar última partida al morir
- Estado de aventura (ubicación, NPCs conocidos, pistas)
- Estado de combate (HP, inventario, condiciones)

---

## Arquitectura del Sistema

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLI AVENTURA                             │
│                     (src/cli_aventura.py)                        │
│  Interfaz de texto · Input del jugador · Display de resultados  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                         DM CEREBRO                               │
│                  (src/orquestador/dm_cerebro.py)                 │
│  Orquesta LLM + Motor · Interpreta input · Gestiona estado       │
└────────────────────────────┬─────────────────────────────────────┘
                             │
          ┌──────────────────┴──────────────────┐
          ▼                                     ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│          LLM                │   │     MOTOR DE COMBATE        │
│   (Gemini / OpenAI / etc)   │   │    (src/motor/...)          │
│                             │   │                             │
│  • Narra escenas            │   │  • GestorCombate            │
│  • Genera diálogos          │   │  • PipelineTurno            │
│  • Interpreta intenciones   │   │  • NormalizadorAcciones     │
│  • Crea Adventure Bible     │   │  • ValidadorAcciones        │
└─────────────────────────────┘   └─────────────────────────────┘
                                             │
                                             ▼
                              ┌─────────────────────────────┐
                              │      COMPENDIO D&D          │
                              │   (compendio/*.json)        │
                              │                             │
                              │  • Armas y armaduras        │
                              │  • Monstruos                │
                              │  • Conjuros                 │
                              │  • Objetos                  │
                              └─────────────────────────────┘
```

---

## Cómo Probarlo

### Requisitos

- Python 3.11 o superior
- Conexión a internet (para el LLM)
- API key de Google AI (Gemini) u otro LLM compatible

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/ajujo/dnd5e-framework.git
cd dnd5e-framework

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o: venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar API key
export GEMINI_API_KEY="tu-api-key"
# o crear archivo .env con: GEMINI_API_KEY=tu-api-key
```

### Ejecutar

```bash
# Crear un personaje nuevo
python src/cli_creacion.py

# Jugar una aventura
python src/cli_aventura.py

# Solo combate (testing)
python src/cli_combate.py
```

### Comandos en partida

| Comando | Descripción |
|---------|-------------|
| `/ayuda` | Muestra todos los comandos |
| `/estado` | Estado del personaje/combate |
| `/inv` | Inventario |
| `/guardar` | Guardar partida |
| `/salir` | Guardar y salir |
| `/debug` | Modo debug (ver tiradas internas) |
| `/sillm` | Activar narración LLM |
| `/nollm` | Desactivar narración LLM |

---

## Estructura del Proyecto

```
dnd5e-framework/
├── 📁 compendio/              # Datos D&D 5e en JSON
│   ├── armas.json
│   ├── armaduras_escudos.json
│   ├── conjuros.json
│   ├── monstruos.json
│   └── miscelanea.json
│
├── 📁 config/                 # Configuración
│   ├── prompts/               # Prompts para el LLM
│   └── *.json                 # Config de clases, razas, etc.
│
├── 📁 docs/                   # Documentación
│   ├── arquitectura.md
│   ├── esquemas/              # JSON Schemas
│   └── ejemplo_adventure_bible.json
│
├── 📁 saves/                  # Partidas guardadas
│   └── aventuras/
│
├── 📁 src/                    # Código fuente
│   ├── cli_aventura.py        # CLI principal de aventura
│   ├── cli_combate.py         # CLI solo combate
│   ├── cli_creacion.py        # CLI creación de personajes
│   │
│   ├── 📁 motor/              # Motor de reglas D&D
│   │   ├── gestor_combate.py  # Gestión de combate
│   │   ├── pipeline_turno.py  # Resolución de turnos
│   │   ├── normalizador.py    # Parseo de input
│   │   ├── validador.py       # Validación de reglas
│   │   └── narrador.py        # Narración con LLM
│   │
│   ├── 📁 orquestador/        # Coordinación
│   │   ├── dm_cerebro.py      # DM principal
│   │   ├── combate_integrado.py # Combate táctico
│   │   └── contexto.py        # Estado del juego
│   │
│   ├── 📁 herramientas/       # Tools para el LLM
│   │   ├── combate.py         # iniciar_combate, atacar...
│   │   ├── exploracion.py     # moverse, examinar...
│   │   └── social.py          # hablar, persuadir...
│   │
│   ├── 📁 persistencia/       # Guardar/cargar
│   │   ├── personajes.py
│   │   └── compendio.py
│   │
│   └── 📁 personaje/          # Creación de PJ
│       └── ...
│
├── 📁 tests/                  # Tests unitarios
│
├── Informe_desarrollo_combate.md  # Informe técnico detallado
├── Mejoras_futuras.md         # Roadmap de desarrollo
└── requirements.txt
```

---

## Compendio de Datos D&D

Todos los datos de D&D 5e están en JSON estructurado en `/compendio/`:

### Ejemplo: Monstruo

```json
{
  "id": "esqueleto",
  "nombre": "Esqueleto",
  "tipo": "No-muerto",
  "cr": "1/4",
  "hp": { "formula": "2d8+4", "promedio": 13 },
  "ca": 13,
  "velocidad": { "tierra": 30 },
  "stats": { "FUE": 10, "DES": 14, "CON": 15, "INT": 6, "SAB": 8, "CAR": 5 },
  "acciones": [
    {
      "nombre": "Espada corta",
      "tipo": "ataque_melee",
      "bonificador_ataque": 4,
      "daño": "1d6+2",
      "tipo_daño": "perforante"
    }
  ]
}
```

### Ejemplo: Arma

```json
{
  "id": "espada_larga",
  "nombre": "Espada larga",
  "categoria": "arma_marcial",
  "daño": "1d8",
  "tipo_daño": "cortante",
  "propiedades": ["versatil"],
  "daño_versatil": "1d10",
  "peso": 3,
  "precio": { "cantidad": 15, "moneda": "po" }
}
```

---

## Mejoras Futuras

Ver [Mejoras_futuras.md](./Mejoras_futuras.md) para el roadmap completo.

### Prioridad Alta

1. **Normalización de input con LLM**
   - Convertir "rematar al herido" → acción estructurada
   - Entender referencias como "el más cercano"

2. **Sistema de magia completo**
   - Ranuras de conjuros
   - Componentes y concentración
   - Todos los conjuros del SRD

3. **IA de enemigos mejorada**
   - Tácticas basadas en tipo de criatura
   - Selección inteligente de objetivos

### Prioridad Media

4. **Condiciones de estado**
   - Envenenado, paralizado, cegado, etc.
   - Efectos mecánicos correctos

5. **Movimiento táctico**
   - Grid de combate
   - Ataques de oportunidad
   - Terreno difícil

6. **Descansos**
   - Descanso corto (dados de golpe)
   - Descanso largo (recuperar todo)

### Prioridad Baja / Futuro

7. **Interfaz web**
8. **Multijugador**
9. **Importar personajes de D&D Beyond**
10. **Integración con VTTs** (Roll20, Foundry)

---

## Cómo Contribuir

¡Las contribuciones son bienvenidas! Aquí hay formas de ayudar:

### 🐛 Reportar Bugs

- Abre un Issue describiendo el problema
- Incluye pasos para reproducir
- Incluye log de error si hay

### 💡 Sugerir Mejoras

- Abre un Issue con la etiqueta "enhancement"
- Describe el caso de uso
- Si es posible, propón una implementación

### 🔧 Contribuir Código

1. Fork del repositorio
2. Crear rama: `git checkout -b feature/tu-mejora`
3. Hacer cambios y tests
4. Commit: `git commit -m "feat: descripción"`
5. Push: `git push origin feature/tu-mejora`
6. Abrir Pull Request

### 📚 Añadir Contenido al Compendio

- Monstruos, conjuros, objetos en formato JSON
- Seguir el schema existente
- Datos del SRD (contenido libre)

---

## Preguntas Frecuentes

### ¿Qué LLM necesito?

Actualmente está probado con **Google Gemini** (API gratuita con límites). También debería funcionar con OpenAI GPT-4 con modificaciones menores.

### ¿Es gratis?

El código es gratuito y open source. Los LLMs tienen sus propios costes (Gemini tiene tier gratuito).

### ¿Puedo usar contenido no-SRD?

El proyecto usa solo contenido del **System Reference Document 5.1** que Wizards ha liberado. Si añades contenido adicional para uso personal, es tu responsabilidad.

### ¿Funciona offline?

El motor de combate funciona offline. La narración LLM necesita conexión.

### ¿Puedo jugar con más de un personaje?

Actualmente está diseñado para **1 jugador con 1 personaje**. Multijugador está en el roadmap.

---

## Licencia

MIT License - Ver [LICENSE](./LICENSE)

El contenido de D&D (reglas, monstruos, etc.) está bajo la [SRD 5.1 License](https://dnd.wizards.com/resources/systems-reference-document).

---

## Créditos

- **Desarrollador**: @ajujo
- **Motor de reglas**: Basado en D&D 5e SRD
- **IA**: Google Gemini / OpenAI

---

> *"El verdadero tesoro eran las tiradas de dados que hicimos por el camino."*
> — Anónimo, probablemente

---

**¿Preguntas? ¿Sugerencias?** Abre un Issue o contacta directamente.

⭐ Si te gusta el proyecto, ¡dale una estrella en GitHub!
