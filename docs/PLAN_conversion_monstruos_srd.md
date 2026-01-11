# Plan de Implementación: Conversión SRD Monsters → Compendio Interno

**Fecha**: 11 de Enero de 2026  
**Estado**: ✅ APROBADO

---

## Decisiones del Usuario

| Pregunta | Decisión |
|----------|----------|
| ¿Schema actual es definitivo? | ✅ Sí (copia de seguridad hecha) |
| ¿Empezar con nivel bajo o todos? | **Todos a la vez** |
| ¿Traducir nombres? | **Sí**, excepto intraducibles (Aboleth) |
| ¿Rasgos complejos? | **Híbrido**: estructura mínima + texto canónico |
| ¿Modelo de combate? | **Solo alcance, sin tablero/grid** |

---

## Modelo de Combate: Solo Alcance

**Abstracciones permitidas:**
- Distancia cualitativa: `cuerpo_a_cuerpo` / `cerca` / `media` / `lejos`
- Alcance numérico del SRD: `reach 5 ft`, `range 30/120 ft`
- Estado de engagement: "trabados cuerpo a cuerpo" o "a distancia"
- Área simple: cono/línea/esfera sin coordenadas → "afecta hasta N objetivos"

---

## Objetivo

Convertir el archivo `srd_5e_monsters.json` (SRD 5.1 en inglés, ~300 monstruos) a un compendio interno estructurado en español que el motor de combate pueda usar directamente.

---

## Fase 1: Definir Schema de Monstruo Interno

### 1.1 Schema Actual (ya existente en `monstruos.json`)

El proyecto ya tiene un schema funcional que usaremos como base:

```json
{
  "id": "goblin",
  "nombre": "Goblin",
  "tamaño": "Pequeño",
  "tipo": "Humanoide",
  "alineamiento": "Neutral malvado",
  "clase_armadura": 15,
  "puntos_golpe": 7,
  "dados_golpe": "2d6",
  "velocidad": 30,
  "atributos": {
    "fuerza": 8, "destreza": 14, "constitucion": 10,
    "inteligencia": 10, "sabiduria": 8, "carisma": 8
  },
  "habilidades": { "sigilo": 6 },
  "sentidos": { "vision_oscura": 60, "percepcion_pasiva": 9 },
  "idiomas": ["Común", "Goblin"],
  "desafio": 0.25,
  "experiencia": 50,
  "rasgos": [
    {
      "nombre": "Escape Ágil",
      "descripcion": "..."
    }
  ],
  "acciones": [
    {
      "nombre": "Cimitarra",
      "tipo": "arma_cuerpo",
      "bonificador_ataque": 4,
      "alcance": 5,
      "daño": "1d6+2",
      "tipo_daño": "cortante"
    }
  ]
}
```

### 1.2 Extensiones Necesarias para el Schema

Para soportar criaturas más complejas del SRD, necesitamos añadir:

```json
{
  "srd_ref": {
    "name": "Goblin",
    "source": "SRD 5.1"
  },
  
  "velocidades": {
    "tierra": 30,
    "vuelo": 0,
    "nado": 0,
    "trepar": 0,
    "excavar": 0
  },
  
  "tiradas_salvacion": {
    "destreza": 4,
    "constitucion": 3
  },
  
  "resistencias": ["fuego", "frío"],
  "vulnerabilidades": ["radiante"],
  "inmunidades_daño": ["veneno", "psíquico"],
  "inmunidades_condicion": ["asustado", "hechizado"],
  
  "acciones_legendarias": [
    {
      "nombre": "Detectar",
      "coste": 1,
      "descripcion": "..."
    }
  ],
  
  "acciones_guarida": [...],
  
  "lanzamiento_conjuros": {
    "nivel_lanzador": 5,
    "caracteristica": "sabiduria",
    "cd_salvacion": 14,
    "bonificador_ataque": 6,
    "conjuros": {
      "trucos": ["luz", "llama sagrada"],
      "nivel_1": { "usos": 4, "conjuros": ["curar heridas", "bendición"] }
    }
  },
  
  "multiataque": {
    "descripcion": "El dragón hace tres ataques...",
    "ataques": [
      { "accion": "Mordisco", "cantidad": 1 },
      { "accion": "Garra", "cantidad": 2 }
    ]
  }
}
```

### 1.3 JSON Schema Formal

Crearemos `docs/esquemas/monstruo_schema.json` con validación JSON Schema para garantizar consistencia.

---

## Fase 2: Script de Conversión

### 2.1 Archivo: `scripts/convertir_srd_monstruos.py`

```python
#!/usr/bin/env python3
"""
Convierte srd_5e_monsters.json → monstruos_convertidos.json

Uso:
  python scripts/convertir_srd_monstruos.py
  
Genera:
  - compendio/monstruos_convertidos.json (resultado)
  - compendio/monstruos_revision_manual.json (casos problemáticos)
  - logs/conversion_report.txt (informe)
"""
```

### 2.2 Mapeos de Traducción

#### Campos SRD → Schema Interno

| SRD (inglés) | Interno (español) |
|--------------|-------------------|
| `name` | `nombre` (traducir) |
| `Armor Class` | `clase_armadura` (parsear número) |
| `Hit Points` | `puntos_golpe`, `dados_golpe` |
| `Speed` | `velocidades` (parsear múltiples) |
| `STR`, `DEX`, etc. | `atributos.fuerza`, etc. |
| `Saving Throws` | `tiradas_salvacion` |
| `Skills` | `habilidades` |
| `Damage Immunities` | `inmunidades_daño` |
| `Damage Resistances` | `resistencias` |
| `Damage Vulnerabilities` | `vulnerabilidades` |
| `Condition Immunities` | `inmunidades_condicion` |
| `Senses` | `sentidos` |
| `Languages` | `idiomas` |
| `Challenge` | `desafio`, `experiencia` |
| `Traits` | `rasgos` (parsear HTML) |
| `Actions` | `acciones` (parsear HTML) |
| `Legendary Actions` | `acciones_legendarias` |

#### Tipos de Daño (EN → ES)

```python
TIPOS_DAÑO = {
    "bludgeoning": "contundente",
    "piercing": "perforante",
    "slashing": "cortante",
    "acid": "ácido",
    "cold": "frío",
    "fire": "fuego",
    "force": "fuerza",
    "lightning": "relámpago",
    "necrotic": "necrótico",
    "poison": "veneno",
    "psychic": "psíquico",
    "radiant": "radiante",
    "thunder": "trueno",
}
```

#### Condiciones (EN → ES)

```python
CONDICIONES = {
    "blinded": "cegado",
    "charmed": "hechizado",
    "deafened": "ensordecido",
    "exhaustion": "agotamiento",
    "frightened": "asustado",
    "grappled": "agarrado",
    "incapacitated": "incapacitado",
    "invisible": "invisible",
    "paralyzed": "paralizado",
    "petrified": "petrificado",
    "poisoned": "envenenado",
    "prone": "derribado",
    "restrained": "apresado",
    "stunned": "aturdido",
    "unconscious": "inconsciente",
}
```

#### Tamaños (EN → ES)

```python
TAMAÑOS = {
    "Tiny": "Diminuto",
    "Small": "Pequeño",
    "Medium": "Mediano",
    "Large": "Grande",
    "Huge": "Enorme",
    "Gargantuan": "Gargantuesco",
}
```

### 2.3 Parseo de Acciones

El desafío principal es parsear texto HTML como:

```html
<p><em><strong>Bite.</strong></em> <em>Melee Weapon Attack:</em> +11 to hit, 
reach 10 ft., one target. <em>Hit:</em> 17 (2d10 + 6) piercing damage plus 
4 (1d8) acid damage.</p>
```

#### Regex para Ataques

```python
PATRON_ATAQUE = re.compile(
    r'<strong>(?P<nombre>[^<]+)\.</strong></em>\s*'
    r'<em>(?P<tipo>Melee|Ranged) Weapon Attack:</em>\s*'
    r'\+(?P<bonificador>\d+) to hit,\s*'
    r'(?:reach (?P<alcance>\d+) ft\.|range (?P<rango_corto>\d+)/(?P<rango_largo>\d+) ft\.)'
    r'[^<]*<em>Hit:</em>\s*'
    r'(?P<daño_promedio>\d+)\s*\((?P<dados_daño>[^)]+)\)\s*'
    r'(?P<tipo_daño>\w+) damage'
    r'(?:\s*plus\s*(?P<daño_extra_promedio>\d+)\s*\((?P<dados_extra>[^)]+)\)\s*(?P<tipo_extra>\w+) damage)?'
)
```

### 2.4 Casos que Requieren Revisión Manual

El script marcará para revisión:

1. **Multiataques complejos**: "one with its bite and two with its claws"
2. **Ataques con efectos**: salvaciones, enfermedades, condiciones
3. **Breath Weapons**: recarga, área, salvación
4. **Spellcasting**: lista de conjuros
5. **Acciones legendarias**: parsing complejo
6. **Acciones con opciones**: "uses one of the following"

### 2.5 Estructura del Output

```
compendio/
├── monstruos.json              # Compendio actual (5 monstruos)
├── srd_5e_monsters.json        # Original SRD (no tocar)
├── monstruos_convertidos.json  # Resultado automático
└── monstruos_revision.json     # Necesitan revisión manual
```

---

## Fase 3: El Motor Solo Usa Compendio Interno

### 3.1 Modificar `src/persistencia/compendio.py`

El `CompendioMotor` ya usa `monstruos.json`. Solo necesitamos:

1. Reemplazar contenido de `monstruos.json` con los convertidos
2. Añadir validación del nuevo schema
3. Mantener retrocompatibilidad con monstruos existentes

### 3.2 Regla de Oro

```python
# ✅ CORRECTO - usar compendio interno
monstruo = compendio.obtener_monstruo("dragon_negro_adulto")

# ❌ INCORRECTO - nunca leer SRD directo
with open("srd_5e_monsters.json") as f:
    monsters = json.load(f)  # NUNCA
```

---

## Fase 4: Trazabilidad al SRD Original

### 4.1 Campo `srd_ref`

Cada monstruo convertido tendrá:

```json
{
  "id": "aboleth",
  "nombre": "Aboleth",
  "srd_ref": {
    "name": "Aboleth",
    "source": "SRD 5.1",
    "index": 0
  },
  ...
}
```

### 4.2 Script de Verificación

```python
# scripts/verificar_srd_mapping.py
# Compara compendio interno con SRD original
# Detecta discrepancias en stats, acciones, etc.
```

---

## Estimación de Trabajo

| Fase | Tarea | Tiempo Estimado | Automatizable |
|------|-------|-----------------|---------------|
| 1.1 | Revisar schema actual | 30 min | - |
| 1.2 | Definir extensiones schema | 1 hora | - |
| 1.3 | Crear JSON Schema formal | 1 hora | - |
| 2.1 | Script base de conversión | 2 horas | ✅ 100% |
| 2.2 | Mapeos de traducción | 1 hora | ✅ 100% |
| 2.3 | Parseo de ataques simples | 2 horas | ✅ 80% |
| 2.4 | Casos complejos (revisión) | 3 horas | ❌ Manual |
| 3.1 | Integrar en CompendioMotor | 1 hora | ✅ 100% |
| 4.1 | Añadir srd_ref | 30 min | ✅ 100% |
| 4.2 | Script verificación | 1 hora | ✅ 100% |

**Total estimado**: ~12-15 horas de trabajo

### Distribución 80/20

- **~80% automático**: ~250 monstruos simples (humanoides, bestias, no-muertos básicos)
- **~20% manual**: ~50 monstruos complejos (dragones, demonios, criaturas legendarias)

---

## Entregables

1. **`docs/esquemas/monstruo_schema.json`** - Schema formal
2. **`scripts/convertir_srd_monstruos.py`** - Script de conversión
3. **`scripts/verificar_srd_mapping.py`** - Verificación
4. **`compendio/monstruos_convertidos.json`** - Resultado
5. **`compendio/monstruos_revision.json`** - Para revisión manual
6. **Informe de conversión** - Estadísticas y pendientes

---

## Priorización de Monstruos

### Alta Prioridad (implementar primero)
Monstruos más usados en aventuras de nivel 1-5:
- Goblin, Orco, Bandido, Esqueleto, Zombi
- Lobo, Rata gigante, Araña gigante
- Kobold, Ogro, Troll, Gnoll
- Espectro, Fantasma, Momia

### Media Prioridad
- Dragones jóvenes y adultos
- Elementales
- Gigantes
- Aberraciones comunes

### Baja Prioridad
- Criaturas legendarias
- Dragones antiguos
- Demonios y diablos mayores

---

## Próximos Pasos

1. ✅ **Aprobar este plan**
2. ⏳ Crear JSON Schema formal
3. ⏳ Desarrollar script de conversión
4. ⏳ Ejecutar conversión automática
5. ⏳ Revisar casos manuales
6. ⏳ Integrar en CompendioMotor
7. ⏳ Testing con combates reales

## Clasificación de Rasgos: MUST PARSE vs TEXT ONLY

### Lista MUST PARSE (Versión 1)

Rasgos que el motor puede aplicar **sin tablero**:

#### 1. Resistencias / Inmunidades / Vulnerabilidades

```json
{
  "resistencias": ["fuego", "frío"],
  "inmunidades_daño": ["veneno", "psíquico"],
  "inmunidades_condicion": ["asustado", "hechizado"],
  "vulnerabilidades": ["radiante"]
}
```

#### 2. Recarga (Recharge)

```json
{
  "recarga": {
    "tipo": "dado",
    "rango": [5, 6]
  }
}
```

#### 3. Regeneración

```json
{
  "regeneracion": {
    "cantidad": 10,
    "condicion_texto": "si no recibió fuego o ácido desde su último turno"
  }
}
```

#### 4. Modificadores de Tiradas (ventaja/desventaja)

| Rasgo SRD | Representación |
|-----------|----------------|
| Magic Resistance | `{"tipo": "ventaja_ts", "contra": "magia"}` |
| Pack Tactics | `{"tipo": "ventaja_ataque", "condicion": "aliado_cerca"}` |
| Keen Senses | `{"tipo": "ventaja_habilidad", "habilidad": "percepcion", "subtipo": "olfato"}` |
| Sunlight Sensitivity | `{"tipo": "desventaja_ataque", "condicion": "luz_solar"}` |

```json
{
  "modificadores_tirada": [
    {
      "tipo": "ventaja",
      "aplica_a": "tirada_salvacion",
      "contra": ["conjuros", "magia"],
      "texto_srd": "The creature has advantage on saving throws against spells..."
    }
  ]
}
```

#### 5. Sentidos Especiales

```json
{
  "sentidos": {
    "vision_oscura": 60,
    "vision_ciega": 30,
    "sentido_temblor": 60,
    "vision_verdadera": 120,
    "percepcion_pasiva": 15
  }
}
```

---

### Lista TEXT ONLY + TAGS

Rasgos que se guardan como texto con etiquetas para futuro parseo:

```json
{
  "rasgos": [
    {
      "nombre": "Posesión Incorpórea",
      "texto_srd": "The ghost enters the body of a humanoid within 5 feet...",
      "tags": ["posesion", "incorpóreo", "ts_carisma", "humanoid_only"],
      "nivel_parseo": "texto"
    },
    {
      "nombre": "Maldición de Momia",
      "texto_srd": "If the mummy can see the target within 60 feet...",
      "tags": ["maldicion", "ts_sabiduria", "vision", "miedo"],
      "nivel_parseo": "texto"
    },
    {
      "nombre": "Cambiar Forma",
      "texto_srd": "The dragon polymorphs into a humanoid or beast...",
      "tags": ["polimorfia", "a_voluntad", "dragon"],
      "nivel_parseo": "texto"
    }
  ]
}
```

---

## Schema de Acciones (Sin Grid)

### Ataque Simple

```json
{
  "id": "mordisco",
  "nombre": "Mordisco",
  "tipo": "ataque",
  "modalidad": "cuerpo",
  "ataque": {
    "bonificador": 11,
    "alcance_pies": 10
  },
  "objetivos_max": 1,
  "impacto": [
    {"tipo": "daño", "cantidad": "2d10+6", "tipo_daño": "perforante"},
    {"tipo": "daño", "cantidad": "1d8", "tipo_daño": "ácido"}
  ],
  "texto_srd": "Melee Weapon Attack: +11 to hit, reach 10 ft., one target. Hit: 17 (2d10 + 6) piercing damage plus 4 (1d8) acid damage."
}
```

### Ataque a Distancia

```json
{
  "id": "arco_corto",
  "nombre": "Arco corto",
  "tipo": "ataque",
  "modalidad": "distancia",
  "ataque": {
    "bonificador": 4,
    "alcance_corto": 80,
    "alcance_largo": 320
  },
  "objetivos_max": 1,
  "impacto": [
    {"tipo": "daño", "cantidad": "1d6+2", "tipo_daño": "perforante"}
  ]
}
```

### Multiataque

```json
{
  "multiataque": {
    "texto_srd": "The dragon makes three attacks: one with its bite and two with its claws.",
    "ataques": [
      {"accion_id": "mordisco", "cantidad": 1},
      {"accion_id": "garra", "cantidad": 2}
    ],
    "puede_usar_antes": ["presencia_aterradora"]
  }
}
```

### Aliento de Dragón (área sin grid)

```json
{
  "id": "aliento_acido",
  "nombre": "Aliento Ácido",
  "tipo": "habilidad_especial",
  "recarga": {"tipo": "dado", "rango": [5, 6]},
  "area": {
    "forma": "linea",
    "longitud_pies": 60,
    "ancho_pies": 5,
    "seleccion": "todas_en_area"
  },
  "salvacion": {
    "caracteristica": "destreza",
    "cd": 18
  },
  "impacto": [
    {"tipo": "daño", "cantidad": "12d8", "tipo_daño": "ácido", "mitad_si_exito": true}
  ],
  "texto_srd": "The dragon exhales acid in a 60-foot line..."
}
```

### Acción Legendaria

```json
{
  "acciones_legendarias": {
    "cantidad_por_ronda": 3,
    "texto_intro": "The dragon can take 3 legendary actions...",
    "acciones": [
      {
        "id": "detectar",
        "nombre": "Detectar",
        "coste": 1,
        "efecto": "tirada_percepcion",
        "texto_srd": "The dragon makes a Wisdom (Perception) check."
      },
      {
        "id": "ataque_cola",
        "nombre": "Ataque de Cola",
        "coste": 1,
        "usa_accion": "cola"
      },
      {
        "id": "ataque_alas",
        "nombre": "Ataque de Alas",
        "coste": 2,
        "salvacion": {"caracteristica": "destreza", "cd": 19},
        "impacto": [
          {"tipo": "daño", "cantidad": "2d6+6", "tipo_daño": "contundente"},
          {"tipo": "condicion", "condicion": "derribado"}
        ],
        "efecto_adicional": "El dragón puede volar hasta la mitad de su velocidad de vuelo.",
        "texto_srd": "The dragon beats its wings..."
      }
    ]
  }
}
```

---

## Próximos Pasos

1. ✅ **Plan aprobado**
2. ⏳ Crear JSON Schema formal basado en este documento
3. ⏳ Desarrollar script de conversión `convertir_srd_monstruos.py`
4. ⏳ Ejecutar conversión automática (~300 monstruos)
5. ⏳ Revisar casos marcados para revisión manual
6. ⏳ Reemplazar `monstruos.json` con resultado final
7. ⏳ Testing con combates reales

---

*Plan aprobado: 11 de Enero de 2026*

