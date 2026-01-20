---
description: Cómo debuggear problemas de combate
---

# Debug Combate

## Activar modo debug

// turbo
```bash
python src/cli_aventura.py --debug --continuar
```

## Qué muestra el modo debug

Durante el combate verás información como:
```
[DEBUG] Acción: ataco al esqueleto
[DEBUG] PJ arma_principal: Espada larga
[DEBUG] Contexto arma: {'nombre': 'Espada larga', ...}
[DEBUG] Estado orq después de turno: EstadoCombateIntegrado.EN_CURSO
[DEBUG] Resultado tipo: accion_aplicada
[DEBUG] Enemigos: [('Esqueleto', 5, False)]
```

## Problemas comunes

### "No entendí esa acción"
- Prueba ser más específico: "ataco al esqueleto herido"
- Verifica que el enemigo exista con `/combate`

### Combate termina inesperadamente
- El debug mostrará `[DEBUG] ¡Combate terminando!`
- Revisa el estado y tipo de resultado

### HP de enemigos se resetea
- Esto ocurre si el combate se reinicia
- Busca por qué terminó el combate original

## Toggle narración LLM en combate

| Comando | Efecto |
|---------|--------|
| `/nollm` | Desactiva narración LLM |
| `/sillm` | Activa narración LLM |
