# Mejoras Futuras

Documento de funcionalidades a implementar en el futuro.

---

## Prioridad Crítica

### 1. Sistema de Experiencia y Niveles

**Prioridad**: Crítica  
**Complejidad**: Alta

Sin esto, el PJ nunca progresa. Es el corazón de D&D y afecta a todo lo demás:
- Umbrales de XP por nivel
- Subida de nivel automática
- Nuevos rasgos de clase por nivel
- Aumento de características (ASI)
- Nuevas ranuras de conjuros

### 2. Más Clases Base

**Prioridad**: Crítica  
**Complejidad**: Media

Actualmente solo están implementadas **4 clases**:
- ✅ Guerrero
- ✅ Pícaro  
- ✅ Mago
- ✅ Clérigo

Faltan las 8 restantes del SRD:
- ❌ Bárbaro
- ❌ Bardo
- ❌ Druida
- ❌ Monje
- ❌ Paladín
- ❌ Explorador (Ranger)
- ❌ Hechicero
- ❌ Brujo

---

## Prioridad Alta

### 3. Normalización de Input con LLM

**Prioridad**: Alta  
**Complejidad**: Media

Convertir lenguaje natural del jugador a acciones estructuradas:
- "rematar al herido" → atacar al enemigo con menos HP
- "el más cercano" → resolver referencia al contexto
- "usar mi varita" → buscar varita en inventario y activarla

Ver sección detallada más abajo.

### 4. Sistema de Magia Completo

**Prioridad**: Alta  
**Complejidad**: Alta

- Ranuras de conjuros por nivel
- Componentes (verbal, somático, material)
- Concentración
- Todos los conjuros del SRD

### 5. IA de Enemigos Mejorada

**Prioridad**: Alta  
**Complejidad**: Media

- Tácticas basadas en tipo de criatura
- Selección inteligente de objetivos
- Uso de habilidades especiales

---

## Prioridad Media

### 6. Condiciones de Estado

- Envenenado, paralizado, cegado, aturdido, etc.
- Efectos mecánicos correctos según las reglas

### 7. Movimiento Táctico

- Grid de combate (opcional)
- Ataques de oportunidad
- Terreno difícil

### 8. Descansos

- Descanso corto (dados de golpe)
- Descanso largo (recuperar todo)

---

## Prioridad Baja / Futuro

- Interfaz web
- Multijugador
- Importar personajes de D&D Beyond
- Integración con VTTs (Roll20, Foundry)

---

## Optimizaciones de Rendimiento LLM

### KV Cache para System Prompt

**Estado**: Implementado (parcialmente funcional según modelo)  
**Fecha**: 2026-01-11

#### Contexto

El framework envía ~5500 tokens de system prompt en cada turno al LLM. Esto incluye:
- Instrucciones del DM (~3000 tokens)
- Herramientas disponibles (~500 tokens)
- Adventure Bible (~800 tokens)
- Prompt de tono (~400 tokens)
- Contexto actual del PJ (~800 tokens)

#### Optimización Implementada

Se reorganizó el system prompt en `dm_cerebro.py` para poner el contenido **estático primero** y el **dinámico al final**:

```python
def _construir_system_prompt(self) -> str:
    """
    OPTIMIZACIÓN KV CACHE: Contenido ordenado de más estático a más dinámico.
    
    Orden:
    1. ESTÁTICO: Instrucciones base del DM (nunca cambia)
    2. ESTÁTICO: Herramientas disponibles (nunca cambia)
    3. SEMI-ESTÁTICO: Adventure Bible (cambia entre actos)
    4. SEMI-ESTÁTICO: Prompt de tono (cambia si cambia aventura)
    5. DINÁMICO: Contexto actual (cambia cada turno)
    """
```

#### Resultados por Modelo

| Modelo | KV Cache | Tokens a Procesar | Tiempo Prompt |
|--------|----------|-------------------|---------------|
| **Llama-3.3-70B GGUF** | ✅ Funciona | ~700 (12%) | ~3-4s |
| **Qwen3-Next-80B-A3B GGUF** | ❌ Falla* | ~5500 (100%) | ~12s |
| **Modelos MLX** | ❌ No soportado | ~5500 (100%) | ~9s |

*El modelo detecta caché pero falla al aplicarlo: `Failed to remove tokens from cache, clearing cache instead.` Probablemente por ser MoE (Mixture of Experts).

#### Próximos Pasos

1. **Probar Qwen2.5-72B GGUF** (no es MoE, debería funcionar)
2. **Esperar actualizaciones de llama.cpp** para soporte MoE
3. **Monitorear actualizaciones de LM Studio**

#### Cómo Verificar si Funciona

En los logs de LM Studio, buscar:
```
✅ FUNCIONA:
Cache reuse summary: 5052/5749 of prompt (87%)
Prompt tokens to decode: 697  ← Solo estos nuevos

❌ NO FUNCIONA:
Failed to remove tokens from cache, clearing cache instead.
Prompt tokens to decode: 5749  ← Todos
```

---

## Streaming de Respuestas LLM

**Estado**: Parcialmente implementado  
**Fecha**: 2026-01-11

### Lo Implementado

1. **Efecto typewriter en narrativa** (`cli_aventura.py`):
   - El texto aparece letra a letra con `velocidad=0.02s` por carácter
   - Hace la lectura más amena mientras esperas

2. **Función de streaming en API** (`llm/__init__.py`):
   - `llamar_llm_streaming()` con callback `on_token`
   - Preparado para streaming real si se cambia la arquitectura

### Limitación Actual

El DM responde en JSON que necesita parsearse completo antes de mostrar la narrativa. El streaming "real" (mostrar mientras genera) requeriría:
1. Que el LLM genere la narrativa primero, herramientas después
2. O cambiar el formato de respuesta completamente

El efecto typewriter es un buen compromiso que mejora la experiencia sin cambiar la arquitectura.

---

## Detalle: Normalización de Acciones de Combate con LLM

### Estado Actual

El sistema de combate usa un normalizador basado en patrones de texto (`normalizador.py`) que solo reconoce verbos específicos:
- ✅ `ataco`, `golpeo`, `disparo`, `lanzo`
- ✅ `mover`, `muevo`, `corro`
- ❌ `rematar`, `acabar con`, `eliminar`
- ❌ Referencias como "el herido", "el más cercano"

### Flujo Propuesto

```
┌─────────────────────────────────────────────────────────────────┐
│  JUGADOR: "intento rematar al esqueleto herido"                 │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 1: LLM Normaliza                                          │
│  Input: texto natural + contexto (enemigos, HPs, etc.)          │
│  Output: JSON canónico {"accion": "ataque", "objetivo": "..."}  │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 2: Motor de Combate Resuelve                              │
│  - Tiradas de dado                                              │
│  - Cálculo de daño                                              │
│  - Aplicación de efectos                                        │
│  Output: eventos mecánicos                                      │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 3: LLM Narra                                              │
│  Input: eventos mecánicos + contexto                            │
│  Output: narración inmersiva                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Cambios Técnicos Necesarios

1. **Nuevo método en `NormalizadorAcciones`**:
   ```python
   def normalizar_con_llm(self, texto: str, contexto: ContextoEscena) -> AccionNormalizada:
       prompt = self._construir_prompt_normalizacion(texto, contexto)
       respuesta = self._llm_callback(prompt)
       return self._parsear_respuesta_llm(respuesta)
   ```

2. **Integración en `OrquestadorCombate.procesar_turno_jugador()`**:
   - Intentar normalización con patrones primero (rápido)
   - Si falla, usar LLM como fallback
   - Cachear normalizaciones frecuentes

---

*Última actualización: 2026-01-11*
