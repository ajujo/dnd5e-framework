# Contrato Canónico: Acciones Normalizadas

Este documento define el **esquema fijo** de las acciones normalizadas.
**No modificar campos sin incrementar versión.**

Versión: 1.0
Fecha: 2025-01-07

---

## Estructura Base

Toda acción normalizada tiene estos campos:
```json
{
  "tipo": "string",           // Obligatorio: ataque|conjuro|movimiento|habilidad|accion|objeto
  "datos": {},                // Obligatorio: campos específicos según tipo
  "confianza": 0.0-1.0,       // Qué tan seguro está el normalizador
  "faltantes": [],            // Campos que no se pudieron resolver
  "advertencias": [],         // Información para el usuario/DM
  "texto_original": "string", // El texto que se normalizó
  "requiere_clarificacion": false,  // Si necesita input adicional
  "fuente": "patron|llm"      // De dónde vino la normalización
}
```

---

## Esquemas por Tipo

### Ataque
```json
{
  "tipo": "ataque",
  "atacante_id": "string",    // ID del actor (obligatorio)
  "objetivo_id": "string",    // ID del objetivo (crítico)
  "arma_id": "string",        // ID del compendio o "unarmed"
  "subtipo": "melee|ranged|unarmed",
  "modo": "normal|ventaja|desventaja"
}
```

### Conjuro
```json
{
  "tipo": "conjuro",
  "lanzador_id": "string",    // ID del actor (obligatorio)
  "objetivo_id": "string",    // ID del objetivo (puede ser null)
  "conjuro_id": "string",     // ID del compendio (crítico)
  "nivel_lanzamiento": 0-9    // Nivel de ranura a usar
}
```

### Movimiento
```json
{
  "tipo": "movimiento",
  "actor_id": "string",       // ID del actor (obligatorio)
  "distancia_pies": 0-999,    // Distancia en pies
  "destino": "string"         // Descripción del destino (puede ser null)
}
```

### Habilidad
```json
{
  "tipo": "habilidad",
  "actor_id": "string",       // ID del actor (obligatorio)
  "habilidad": "string",      // Nombre de la habilidad (crítico)
  "objetivo_id": "string"     // ID del objetivo (puede ser null)
}
```

Habilidades válidas:
- acrobacias, arcanos, atletismo, engaño, historia
- interpretacion, intimidacion, investigacion, juego_manos
- medicina, naturaleza, percepcion, perspicacia, persuasion
- religion, sigilo, supervivencia, trato_animales

### Acción Genérica
```json
{
  "tipo": "accion",
  "actor_id": "string",       // ID del actor (obligatorio)
  "accion_id": "string"       // dash|dodge|disengage|help|hide|search|ready
}
```

### Objeto
```json
{
  "tipo": "objeto",
  "actor_id": "string",       // ID del actor (obligatorio)
  "objeto_id": "string"       // ID del compendio (crítico)
}
```

---

## Campos Críticos vs Opcionales

| Tipo | Críticos (requieren clarificación) | Opcionales |
|------|-------------------------------------|------------|
| ataque | objetivo_id | arma_id, subtipo, modo |
| conjuro | conjuro_id | objetivo_id, nivel_lanzamiento |
| movimiento | (ninguno) | distancia_pies, destino |
| habilidad | habilidad | objetivo_id |
| accion | accion_id | (ninguno) |
| objeto | objeto_id | (ninguno) |

---

## Notas de Implementación

1. **IDs**: Siempre usar `compendio_ref` para armas/armaduras, no `instancia_id`
2. **Objetivos**: Usar `instancia_id` de combatientes, no `compendio_ref`
3. **Distancias**: Siempre en pies (1 casilla = 5 pies, 1 metro ≈ 3.28 pies)
4. **Confianza**: >= 0.7 se considera "completa"
5. **Fuente**: "patron" = determinista, "llm" = fallback a LLM

---

## Contrato del Validador

### ResultadoValidacion
```json
{
  "valido": true|false,        // Obligatorio: si la acción puede ejecutarse
  "razon": "string",           // Obligatorio: explicación humana
  "advertencias": [],          // Opcional: warnings que no bloquean
  "datos_extra": {}            // Opcional: info adicional para el motor
}
```

### Niveles de Severidad

| Nivel | valido | advertencias | Significado |
|-------|--------|--------------|-------------|
| ✅ OK | true | [] | Acción completamente válida |
| ⚠️ WARNING | true | [...] | Válida pero con notas importantes |
| ❌ ERROR | false | - | No se puede ejecutar |

### Códigos de Error Comunes

| Código | Descripción |
|--------|-------------|
| `NO_OBJETIVO` | No hay objetivo seleccionado |
| `OBJETIVO_MUERTO` | El objetivo ya está muerto |
| `ARMA_NO_EXISTE` | Arma no encontrada en compendio |
| `ARMA_NO_EQUIPADA` | Arma no equipada (modo estricto) |
| `CONJURO_NO_EXISTE` | Conjuro no encontrado |
| `SIN_RANURAS` | No hay ranuras de conjuro disponibles |
| `NIVEL_INSUFICIENTE` | Ranura de nivel inferior al conjuro |
| `NO_PUEDE_ACTUAR` | Entidad incapacitada/muerta/etc |
| `SIN_MOVIMIENTO` | No queda movimiento suficiente |
| `CONDICION_BLOQUEA` | Una condición impide la acción |

### Configuración
```python
ValidadorAcciones(
    compendio_motor=CompendioMotor(),
    strict_equipment=False  # True = armas no equipadas son ERROR
)
```

### Flujo de Validación
```
AccionNormalizada
       ↓
ValidadorAcciones.validar_X()
       ↓
ResultadoValidacion
       ↓
   ¿valido?
   /     \
  Sí      No
  ↓        ↓
Ejecutar  Mostrar razon
          al jugador
```
