# Informe de Desarrollo: Sistema de Combate Táctico D&D 5e

**Fecha**: 10 de Enero de 2026  
**Proyecto**: Framework D&D 5e - Integración de Combate Táctico  
**Repositorio**: `/Users/ajujo/Lab/Gemini`

---

## Resumen Ejecutivo

Este proyecto consistió en la integración completa de un sistema de combate táctico dentro de una aventura narrativa D&D 5e. El objetivo principal fue convertir un sistema de combate simplificado (basado solo en herramientas LLM) en un motor táctico completo que respeta las reglas de D&D 5e, con tiradas de dados transparentes, orden de iniciativa, y narración inmersiva generada por LLM.

---

## Índice

1. [Problema Inicial](#problema-inicial)
2. [Arquitectura Implementada](#arquitectura-implementada)
3. [Cambios por Archivo](#cambios-por-archivo)
4. [Funcionalidades Implementadas](#funcionalidades-implementadas)
5. [Bugs Corregidos](#bugs-corregidos)
6. [Comandos Disponibles](#comandos-disponibles)
7. [Formato de Display de Combate](#formato-de-display-de-combate)
8. [Mejoras Futuras Documentadas](#mejoras-futuras-documentadas)

---

## Problema Inicial

### Estado antes de las modificaciones

El sistema original tenía varios problemas:

1. **Combate narrativo sin mecánica**: El LLM decidía los resultados sin tirar dados
2. **Sin orden de iniciativa**: No había control de turnos estructurado
3. **Falta de transparencia**: El jugador no veía las tiradas ni el cálculo de daño
4. **Herramientas básicas**: `iniciar_combate` solo creaba un diccionario simple
5. **Sin integración**: Existía un motor de combate completo (`GestorCombate`, `PipelineTurno`) pero no estaba conectado al flujo de aventura

### Archivos relevantes antes de cambios

- `src/motor/gestor_combate.py` - Motor completo pero no usado
- `src/motor/pipeline_turno.py` - Pipeline de resolución pero no integrado
- `src/herramientas/combate.py` - Herramientas LLM básicas
- `src/orquestador/dm_cerebro.py` - DM principal sin combate táctico
- `src/cli_aventura.py` - CLI sin modo combate

---

## Arquitectura Implementada

### Nuevo Flujo de Combate

```
┌──────────────────────────────────────────────────────────────────┐
│                     FLUJO DE AVENTURA                            │
│                        (DMCerebro)                               │
└────────────────────────────┬─────────────────────────────────────┘
                             │ LLM decide iniciar combate
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                  INICIAR COMBATE TÁCTICO                         │
│               (herramientas/combate.py)                          │
│  - Crear GestorCombate con Combatientes reales                   │
│  - Cargar monstruos desde compendio                              │
│  - Cargar arma equipada del PJ                                   │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                 ORQUESTADOR COMBATE                              │
│            (orquestador/combate_integrado.py)                    │
│  - Control de turnos por iniciativa                              │
│  - Ejecutar turnos de NPCs automáticamente                       │
│  - Procesar input del jugador                                    │
│  - Generar narrativa LLM                                         │
└────────────────────────────┬─────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│    TURNO ENEMIGO        │   │    TURNO JUGADOR        │
│  - IA selecciona acción │   │  - Normalizar input     │
│  - Tirar ataque         │   │  - Resolver mecánica    │
│  - Calcular daño        │   │  - Mostrar tiradas      │
│  - Narrar con LLM       │   │  - Narrar con LLM       │
└─────────────────────────┘   └─────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    DISPLAY EN CLI                                │
│  🎲 Ataque: 15(d20) + 4(mod) = 19 vs CA 18 → ¡Impacta!           │
│  💥 Daño: 4(1d6) + 2(mod) = 6                                    │
│                                                                  │
│  La espada oxidada del esqueleto silba a través de las           │
│  sombras, encontrando un hueco en tu defensa...                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Cambios por Archivo

### 1. `src/persistencia/compendio.py`

**Problema**: `FileNotFoundError` al ejecutar desde diferentes directorios.

**Cambios**:
- Añadida constante `RAIZ_PROYECTO` para detectar automáticamente la raíz del proyecto
- Modificada ruta por defecto de relativa a absoluta
- Actualizado `obtener_compendio()` para usar detección automática de ruta

```python
# Antes
RUTA_DEFECTO = "compendio"

# Después
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent.parent
RUTA_DEFECTO = RAIZ_PROYECTO / "compendio"
```

---

### 2. `src/herramientas/combate.py`

**Problemas**:
- `iniciar_combate` solo creaba diccionario básico
- No cargaba armas del PJ
- `compendio_ref` tenía sufijo incorrecto (`espada_larga_1` vs `espada_larga`)

**Cambios**:
- Reescrita función `iniciar_combate` para usar `GestorCombate` real
- Creación de `Combatiente` con todos los campos correctos
- Carga de monstruos desde `CompendioMotor`
- Extracción de `compendio_ref` sin sufijo numérico

```python
# Antes
arma_principal = {
    "id": arma.get("id"),
    "compendio_ref": arma.get("id"),  # espada_larga_1 ❌
}

# Después
compendio_ref = arma_id
if "_" in arma_id:
    partes = arma_id.rsplit("_", 1)
    if partes[1].isdigit():
        compendio_ref = partes[0]  # espada_larga ✓
```

---

### 3. `src/orquestador/combate_integrado.py` (NUEVO)

**Archivo completamente nuevo** - 500+ líneas de código.

**Clases creadas**:
- `EstadoCombateIntegrado` (Enum): EN_CURSO, VICTORIA, DERROTA, HUIDA
- `ResultadoCombate`: Resultado final del combate
- `TurnoInfo`: Información del turno actual
- `OrquestadorCombate`: Clase principal de orquestación

**Funcionalidades**:
- `obtener_turno_actual()` - Info del turno activo
- `ejecutar_turno_enemigo()` - IA de enemigos con tiradas reales
- `procesar_turno_jugador()` - Procesa input natural del jugador
- `_narrar_resultado()` - Genera narrativa LLM o fallback mecánico
- `obtener_resultado_final()` - Resumen de victoria/derrota

**Características especiales**:
- Wrapper para adaptar `llm_callback(system, user)` a `(prompt)`
- Flag `usar_llm_narracion` para toggle
- Cálculo de daño crítico correcto (dados x2, mod x1)
- Registro de eventos para narrativa

---

### 4. `src/orquestador/dm_cerebro.py`

**Problema**: No tenía integración con combate táctico.

**Cambios**:
- Nuevos atributos: `orquestador_combate`, `gestor_combate`
- Nuevo método: `en_combate_tactico()` - Detecta modo combate
- Nuevo método: `_iniciar_combate_tactico()` - Activa modo táctico
- Nuevo método: `_finalizar_combate_tactico()` - Cierra combate
- Nuevo método: `procesar_turno_combate()` - Delegación a orquestador
- Modificado `procesar_turno()` para detectar `gestor_combate` en resultado
- Filtrado de objetos no serializables antes de JSON

```python
# Nuevo flujo en procesar_turno
if "gestor_combate" in resultado_herramienta:
    self._iniciar_combate_tactico(resultado_herramienta["gestor_combate"])
    return {"combate_iniciado": True}  # Early return
```

---

### 5. `src/orquestador/__init__.py`

**Cambio**: Añadidos exports para nuevos componentes.

```python
from .combate_integrado import (
    OrquestadorCombate,
    EstadoCombateIntegrado,
    ResultadoCombate,
    TurnoInfo,
)
```

---

### 6. `src/cli_aventura.py`

**Cambios masivos** - El archivo más modificado.

#### Nueva función: `mostrar_ui_combate_tactico(dm)`
Muestra estado del combate con HP bars y orden de iniciativa.

#### Nuevo bloque: Loop de combate táctico (líneas 630-900+)
```python
if dm.en_combate_tactico():
    # Loop de combate táctico
    while dm.en_combate_tactico():
        turno = gestor.obtener_turno_actual()
        
        # Si es NPC, ejecutar automáticamente
        if turno.tipo != TipoCombatiente.PC:
            resultado = orq.ejecutar_turno_enemigo(turno.id)
            # Mostrar tiradas y narrativa
        
        # Si es PC, pedir input
        else:
            accion = input("> ")
            resultado = dm.procesar_turno_combate(accion)
```

#### Nuevos comandos de combate:
- `/ayuda` - Comandos disponibles
- `/estado` - Estado del combate
- `/inv` - Inventario
- `/huir` - Huir del combate
- `/nollm` - Desactivar narración LLM
- `/sillm` - Activar narración LLM
- `/debug` - Toggle debug
- `/guardar` - Guardar partida

#### Clarificación de objetivos:
- Tracking de `pendiente_clarificacion`
- Conversión de "1" a "ataco a Esqueleto"

#### Display de tiradas:
- Ataque: `🎲 Ataque: 15(d20) + 4(mod) = 19 vs CA 18 → ¡Impacta!`
- Daño: `💥 Daño: 4(1d6) + 2(mod) = 6`
- Crítico: `💥 Daño crítico: 7(2x1d6) + 2(mod) = 9`

#### Carga de partida al morir:
Implementada funcionalidad real de cargar última partida guardada.

#### Feedback para acciones no reconocidas:
```
⚠️ No entendí esa acción. Usa comandos como:
  • ataco [al esqueleto/goblin/...]
  • ataco (te mostrará objetivos)
  • /ayuda (ver comandos)
```

---

## Funcionalidades Implementadas

### 1. Sistema de Iniciativa Real
- Al iniciar combate, se determinan iniciativas
- Los turnos se ejecutan en orden correcto
- NPCs actúan automáticamente antes del input del jugador

### 2. Tiradas de Dados Transparentes
- d20 + modificador para ataque
- Dados de daño + modificador
- Visualización clara de cada componente

### 3. Daño Crítico Correcto (D&D 5e)
- Crítico = d20 natural de 20
- Dados de daño se tiran dos veces
- Modificador se aplica una sola vez

### 4. Narración LLM
- Narrativas inmersivas para ataques
- Toggle con `/nollm` y `/sillm`
- Fallback a texto mecánico si LLM falla

### 5. UI de Combate
- HP de todos los combatientes
- Indicador de turno actual
- Estado de derrota/victoria

### 6. Persistencia
- Guardado durante combate con `/guardar`
- Carga de partida guardada al morir

### 7. Sistema de Clarificación
- "ataco" muestra lista de objetivos
- Selección por número o nombre
- No pasa turno si acción no reconocida

---

## Bugs Corregidos

| Bug | Causa | Solución |
|-----|-------|----------|
| `FileNotFoundError: compendio` | Ruta relativa | Ruta absoluta desde raíz proyecto |
| `AttributeError: hp_max` | Nombre de campo incorrecto | `hp_maximo` |
| `AttributeError: ca` | Nombre de campo incorrecto | `clase_armadura` |
| `AttributeError: esta_vivo()` | Método vs propiedad | `esta_vivo` (sin paréntesis) |
| Jugador ataca "Desarmado" | Arma no cargada en Combatiente | Pasar `arma_principal` al constructor |
| `compendio_ref: espada_larga_1` | ID con sufijo numérico | Extraer base sin `_N` |
| Turno enemigo después de input | Orden de loop incorrecto | Ejecutar NPCs antes de pedir input |
| "Algo salió mal" en clarificación | Condición `eventos` vacía | Manejar `ACCION_APLICADA` sin eventos |
| Mod crítico = 8 | Cálculo incorrecto | Separar dados y mod, solo doblar dados |
| LLM no narra | Firma incompatible | Wrapper `(prompt)` → `(system, user)` |
| Nombre "goblin_3" en display | ID en vez de nombre | Buscar nombre real del combatiente |
| Acción no reconocida pasa turno | Sin feedback | Mostrar ayuda y `continue` |

---

## Comandos Disponibles

### En Exploración
| Comando | Descripción |
|---------|-------------|
| `/ayuda` | Mostrar ayuda |
| `/estado` | Estado del personaje |
| `/inv` | Inventario |
| `/guardar` | Guardar partida |
| `/salir` | Guardar y salir |
| `/debug` | Toggle modo debug |

### En Combate
| Comando | Descripción |
|---------|-------------|
| `/ayuda` | Comandos de combate |
| `/estado` | Estado del combate |
| `/inv` | Inventario |
| `/huir` | Intentar huir |
| `/nollm` | Desactivar narración LLM |
| `/sillm` | Activar narración LLM |
| `/debug` | Toggle modo debug |
| `/guardar` | Guardar partida |
| `ataco [objetivo]` | Atacar |
| `ataco` | Seleccionar objetivo |

---

## Formato de Display de Combate

### Inicio de Combate
```
⚔️ ¡COMBATE INICIADO!
Orden: Esqueleto, Kaelen Hoja Lunar, Esqueleto, Goblin
Primer turno: Esqueleto
```

### Turno de Enemigo
```
--- Turno de Esqueleto ---
🎲 Ataque: 15(d20) + 4(mod) = 19 vs CA 18 → ¡Impacta!
💥 Daño: 4(1d6) + 2(mod) = 6

La espada oxidada del esqueleto silba a través de las sombras...
```

### Turno del Jugador
```
==================================================
🛡️ TURNO DE KAELEN HOJA LUNAR
==================================================
HP: Esqueleto:13/13 | Kaelen:8/12 | Goblin:7/7

> ataco al goblin

🎲 Ataque con Espada larga: 18(d20) + 5(mod) = 23 → ¡Impacta!
💥 Daño: 7 a Goblin

Tu espada corta el aire con la gracia de la luna creciente...
```

### Daño Crítico
```
🎲 Ataque: 20(d20) + 4(mod) = 24 vs CA 18 → ¡Impacta! ¡CRÍTICO!
💥 Daño crítico: 9(2x1d6) + 2(mod) = 11
```

### Victoria
```
============================================================
🎉 ¡VICTORIA!
============================================================
XP ganada: 150
```

### Derrota
```
============================================================
💀 HAS CAÍDO EN COMBATE
============================================================

Opciones:
  1. Cargar última partida guardada
  2. Volver al menú principal
  3. Salir
```

---

## Mejoras Futuras Documentadas

Creado archivo `/Mejoras_futuras.md` con especificación para:

### Normalización de Acciones con LLM
Permitir frases naturales como "intento rematar al esqueleto herido" que el LLM normalizaría a acciones estructuradas antes de que el motor las procese.

**Flujo propuesto**:
1. Jugador escribe texto natural
2. LLM normaliza a JSON canónico
3. Motor resuelve mecánica
4. LLM narra el resultado
5. Display muestra tiradas + narrativa

---

## Estadísticas del Proyecto

| Métrica | Valor |
|---------|-------|
| Archivos modificados | 7 |
| Archivos creados | 2 |
| Líneas añadidas (estimado) | ~1500 |
| Bugs corregidos | 12 |
| Nuevos comandos | 10 |
| Horas de desarrollo | ~4 |

---

## Archivos Finales del Proyecto

```
/Users/ajujo/Lab/Gemini/
├── compendio/
│   ├── monstruos.json
│   ├── armas.json
│   └── ...
├── src/
│   ├── cli_aventura.py          [MODIFICADO EXTENSAMENTE]
│   ├── cli_combate.py           [REFERENCIA]
│   ├── herramientas/
│   │   └── combate.py           [MODIFICADO]
│   ├── motor/
│   │   ├── gestor_combate.py    [EXISTENTE]
│   │   ├── pipeline_turno.py    [EXISTENTE]
│   │   ├── normalizador.py      [EXISTENTE]
│   │   └── narrador.py          [EXISTENTE]
│   ├── orquestador/
│   │   ├── __init__.py          [MODIFICADO]
│   │   ├── dm_cerebro.py        [MODIFICADO]
│   │   └── combate_integrado.py [NUEVO]
│   └── persistencia/
│       └── compendio.py         [MODIFICADO]
├── Mejoras_futuras.md           [NUEVO]
└── docs/
    └── ...
```

---

## Conclusión

El proyecto ha pasado de un sistema de combate narrativo simple a un motor táctico completo que:

1. ✅ Respeta las reglas de D&D 5e
2. ✅ Muestra todas las tiradas de dados
3. ✅ Mantiene narrativa inmersiva con LLM
4. ✅ Permite toggle entre modo mecánico y narrativo
5. ✅ Gestiona correctamente la iniciativa y turnos
6. ✅ Implementa persistencia y carga de partidas
7. ✅ Proporciona feedback claro al jugador

El sistema está ahora listo para uso en producción, con documentación de mejoras futuras para continuar el desarrollo.

---

*Informe generado: 10 de Enero de 2026*
