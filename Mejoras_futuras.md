# Mejoras Futuras

Documento de funcionalidades a implementar en el futuro.

---

## 1. Normalización de Acciones de Combate con LLM

**Prioridad**: Alta  
**Complejidad**: Media

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
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 4: Display Combinado                                      │
│  🎲 Ataque: 15(d20) + 5(mod) = 20 → ¡Impacta!                   │
│  💥 Daño: 7 al Esqueleto                                        │
│                                                                 │
│  Tu espada corta el aire con la gracia de un susurro lunar...  │
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

2. **Prompt de normalización**:
   ```
   El jugador dijo: "{texto}"
   
   Contexto:
   - Enemigos: Esqueleto (HP: 2/13), Esqueleto (HP: 13/13), Goblin (HP: 7/7)
   - Arma equipada: Espada larga
   
   Convierte esto a una acción de combate:
   - Si quiere atacar, identifica el objetivo más probable
   - "el herido" = el enemigo con menos HP
   - Responde SOLO con JSON: {"tipo": "ataque", "objetivo_id": "...", "arma_id": "..."}
   ```

3. **Integración en `OrquestadorCombate.procesar_turno_jugador()`**:
   - Intentar normalización con patrones primero (rápido)
   - Si falla, usar LLM como fallback
   - Cachear normalizaciones frecuentes

### Beneficios
- Jugadores pueden expresarse naturalmente
- Mejor inmersión narrativa
- Mantiene la mecánica determinista (LLM no decide reglas)

### Consideraciones
- Latencia adicional por llamadas LLM
- Necesidad de manejar respuestas malformadas
- Posible toggle `/nollm-norm` para desactivar

---

*Última actualización: 2026-01-10*
