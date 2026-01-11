#!/usr/bin/env python3
"""
Convierte srd_5e_monsters.json → monstruos.json

Uso:
  python scripts/convertir_srd_monstruos.py

Genera:
  - compendio/monstruos.json (resultado final)
  - logs/conversion_report.txt (informe)
"""

import json
import re
import html
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# === RUTAS ===
RAIZ = Path(__file__).resolve().parent.parent
COMPENDIO = RAIZ / "compendio"
SRD_INPUT = COMPENDIO / "srd_5e_monsters.json"
OUTPUT = COMPENDIO / "monstruos.json"
LOGS = RAIZ / "logs"
LOGS.mkdir(exist_ok=True)
REPORT_FILE = LOGS / "conversion_report.txt"

# === MAPEOS EN → ES ===

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

TAMAÑOS = {
    "Tiny": "Diminuto",
    "Small": "Pequeño",
    "Medium": "Mediano",
    "Large": "Grande",
    "Huge": "Enorme",
    "Gargantuan": "Gargantuesco",
}

TIPOS_CRIATURA = {
    "aberration": "Aberración",
    "beast": "Bestia",
    "celestial": "Celestial",
    "construct": "Constructo",
    "dragon": "Dragón",
    "elemental": "Elemental",
    "fey": "Fata",
    "fiend": "Infernal",
    "giant": "Gigante",
    "humanoid": "Humanoide",
    "monstrosity": "Monstruosidad",
    "ooze": "Légamo",
    "plant": "Planta",
    "undead": "No-muerto",
    "swarm": "Enjambre",
}

ALINEAMIENTOS = {
    "lawful good": "Legal bueno",
    "neutral good": "Neutral bueno",
    "chaotic good": "Caótico bueno",
    "lawful neutral": "Legal neutral",
    "neutral": "Neutral",
    "true neutral": "Neutral",
    "chaotic neutral": "Caótico neutral",
    "lawful evil": "Legal malvado",
    "neutral evil": "Neutral malvado",
    "chaotic evil": "Caótico malvado",
    "unaligned": "Sin alineamiento",
    "any alignment": "Cualquier alineamiento",
    "any": "Cualquier alineamiento",
    "any evil alignment": "Cualquier alineamiento malvado",
    "any non-good alignment": "Cualquier alineamiento no bueno",
    "any non-lawful alignment": "Cualquier alineamiento no legal",
    "any chaotic alignment": "Cualquier alineamiento caótico",
}

HABILIDADES = {
    "acrobatics": "acrobacias",
    "animal handling": "trato_animales",
    "arcana": "arcanos",
    "athletics": "atletismo",
    "deception": "engaño",
    "history": "historia",
    "insight": "perspicacia",
    "intimidation": "intimidacion",
    "investigation": "investigacion",
    "medicine": "medicina",
    "nature": "naturaleza",
    "perception": "percepcion",
    "performance": "interpretacion",
    "persuasion": "persuasion",
    "religion": "religion",
    "sleight of hand": "juego_manos",
    "stealth": "sigilo",
    "survival": "supervivencia",
}

CARACTERISTICAS = {
    "STR": "fuerza",
    "DEX": "destreza", 
    "CON": "constitucion",
    "INT": "inteligencia",
    "WIS": "sabiduria",
    "CHA": "carisma",
    "Strength": "fuerza",
    "Dexterity": "destreza",
    "Constitution": "constitucion",
    "Intelligence": "inteligencia",
    "Wisdom": "sabiduria",
    "Charisma": "carisma",
}

# Nombres de monstruos que NO se traducen
NOMBRES_NO_TRADUCIR = {
    "Aboleth", "Ankheg", "Balor", "Beholder", "Chuul", "Cloaker", "Couatl",
    "Deva", "Djinni", "Doppelganger", "Dretch", "Dryad", "Efreeti", 
    "Ettercap", "Ettin", "Gargoyle", "Glabrezu", "Gnoll", "Gorgon",
    "Grick", "Griffon", "Harpy", "Hezrou", "Homunculus", "Hydra",
    "Intellect Devourer", "Kobold", "Kraken", "Lamia", "Lich", "Manticore",
    "Marilith", "Medusa", "Mephit", "Mimic", "Minotaur", "Nalfeshnee",
    "Nightmare", "Nothic", "Otyugh", "Owlbear", "Pegasus", "Peryton",
    "Pit Fiend", "Planetar", "Pseudodragon", "Rakshasa", "Remorhaz",
    "Revenant", "Roc", "Roper", "Rust Monster", "Sahuagin", "Salamander",
    "Satyr", "Shambling Mound", "Shield Guardian", "Sphinx", "Stirge",
    "Succubus", "Incubus", "Tarrasque", "Thri-kreen", "Treant", "Troglodyte",
    "Troll", "Umber Hulk", "Unicorn", "Vampire", "Vrock", "Wight", "Will-o'-Wisp",
    "Wraith", "Wyvern", "Xorn", "Zombie",
}

# Traducciones conocidas de nombres
NOMBRES_TRADUCCION = {
    "Acolyte": "Acólito",
    "Adult Black Dragon": "Dragón Negro Adulto",
    "Adult Blue Dragon": "Dragón Azul Adulto",
    "Adult Brass Dragon": "Dragón de Latón Adulto",
    "Adult Bronze Dragon": "Dragón de Bronce Adulto",
    "Adult Copper Dragon": "Dragón de Cobre Adulto",
    "Adult Gold Dragon": "Dragón de Oro Adulto",
    "Adult Green Dragon": "Dragón Verde Adulto",
    "Adult Red Dragon": "Dragón Rojo Adulto",
    "Adult Silver Dragon": "Dragón de Plata Adulto",
    "Adult White Dragon": "Dragón Blanco Adulto",
    "Air Elemental": "Elemental de Aire",
    "Ancient Black Dragon": "Dragón Negro Anciano",
    "Ancient Blue Dragon": "Dragón Azul Anciano",
    "Ancient Brass Dragon": "Dragón de Latón Anciano",
    "Ancient Bronze Dragon": "Dragón de Bronce Anciano",
    "Ancient Copper Dragon": "Dragón de Cobre Anciano",
    "Ancient Gold Dragon": "Dragón de Oro Anciano",
    "Ancient Green Dragon": "Dragón Verde Anciano",
    "Ancient Red Dragon": "Dragón Rojo Anciano",
    "Ancient Silver Dragon": "Dragón de Plata Anciano",
    "Ancient White Dragon": "Dragón Blanco Anciano",
    "Animated Armor": "Armadura Animada",
    "Ape": "Simio",
    "Archmage": "Archimago",
    "Assassin": "Asesino",
    "Awakened Shrub": "Arbusto Despertado",
    "Awakened Tree": "Árbol Despertado",
    "Axe Beak": "Pico Hacha",
    "Baboon": "Babuino",
    "Badger": "Tejón",
    "Bandit": "Bandido",
    "Bandit Captain": "Capitán Bandido",
    "Bat": "Murciélago",
    "Bearded Devil": "Diablo Barbudo",
    "Bear": "Oso",
    "Black Bear": "Oso Negro",
    "Black Dragon Wyrmling": "Cría de Dragón Negro",
    "Black Pudding": "Pudín Negro",
    "Blink Dog": "Perro Traslador",
    "Blood Hawk": "Halcón Sangriento",
    "Blue Dragon Wyrmling": "Cría de Dragón Azul",
    "Boar": "Jabalí",
    "Bone Devil": "Diablo de Hueso",
    "Brass Dragon Wyrmling": "Cría de Dragón de Latón",
    "Bronze Dragon Wyrmling": "Cría de Dragón de Bronce",
    "Brown Bear": "Oso Pardo",
    "Bugbear": "Osgo",
    "Camel": "Camello",
    "Cat": "Gato",
    "Centaur": "Centauro",
    "Chain Devil": "Diablo de Cadenas",
    "Chimera": "Quimera",
    "Clay Golem": "Gólem de Arcilla",
    "Cockatrice": "Cocatriz",
    "Commoner": "Plebeyo",
    "Constrictor Snake": "Serpiente Constrictora",
    "Copper Dragon Wyrmling": "Cría de Dragón de Cobre",
    "Crab": "Cangrejo",
    "Crocodile": "Cocodrilo",
    "Cult Fanatic": "Fanático del Culto",
    "Cultist": "Cultista",
    "Cyclops": "Cíclope",
    "Death Dog": "Perro de la Muerte",
    "Deer": "Ciervo",
    "Dire Wolf": "Lobo Terrible",
    "Draft Horse": "Caballo de Tiro",
    "Dragon Turtle": "Tortuga Dragón",
    "Druid": "Druida",
    "Dust Mephit": "Mefít de Polvo",
    "Eagle": "Águila",
    "Earth Elemental": "Elemental de Tierra",
    "Erinyes": "Erinia",
    "Elephant": "Elefante",
    "Elk": "Alce",
    "Fire Elemental": "Elemental de Fuego",
    "Fire Giant": "Gigante de Fuego",
    "Flesh Golem": "Gólem de Carne",
    "Flying Snake": "Serpiente Voladora",
    "Flying Sword": "Espada Voladora",
    "Frog": "Rana",
    "Frost Giant": "Gigante de Escarcha",
    "Ghost": "Fantasma",
    "Ghoul": "Necrófago",
    "Giant Ape": "Simio Gigante",
    "Giant Badger": "Tejón Gigante",
    "Giant Bat": "Murciélago Gigante",
    "Giant Boar": "Jabalí Gigante",
    "Giant Centipede": "Ciempiés Gigante",
    "Giant Constrictor Snake": "Serpiente Constrictora Gigante",
    "Giant Crab": "Cangrejo Gigante",
    "Giant Crocodile": "Cocodrilo Gigante",
    "Giant Eagle": "Águila Gigante",
    "Giant Elk": "Alce Gigante",
    "Giant Fire Beetle": "Escarabajo de Fuego Gigante",
    "Giant Frog": "Rana Gigante",
    "Giant Goat": "Cabra Gigante",
    "Giant Hyena": "Hiena Gigante",
    "Giant Lizard": "Lagarto Gigante",
    "Giant Octopus": "Pulpo Gigante",
    "Giant Owl": "Búho Gigante",
    "Giant Poisonous Snake": "Serpiente Venenosa Gigante",
    "Giant Rat": "Rata Gigante",
    "Giant Scorpion": "Escorpión Gigante",
    "Giant Sea Horse": "Caballito de Mar Gigante",
    "Giant Shark": "Tiburón Gigante",
    "Giant Spider": "Araña Gigante",
    "Giant Toad": "Sapo Gigante",
    "Giant Vulture": "Buitre Gigante",
    "Giant Wasp": "Avispa Gigante",
    "Giant Weasel": "Comadreja Gigante",
    "Giant Wolf Spider": "Araña Lobo Gigante",
    "Gibbering Mouther": "Murmurador",
    "Gladiator": "Gladiador",
    "Goat": "Cabra",
    "Goblin": "Goblin",
    "Gold Dragon Wyrmling": "Cría de Dragón de Oro",
    "Green Dragon Wyrmling": "Cría de Dragón Verde",
    "Green Hag": "Bruja Verde",
    "Grick": "Grick",
    "Guard": "Guardia",
    "Guardian Naga": "Naga Guardiana",
    "Half-Red Dragon Veteran": "Veterano Semidragón Rojo",
    "Hawk": "Halcón",
    "Hell Hound": "Perro Infernal",
    "Hill Giant": "Gigante de las Colinas",
    "Hippogriff": "Hipogrifo",
    "Hobgoblin": "Hobgoblin",
    "Horned Devil": "Diablo Cornudo",
    "Hunter Shark": "Tiburón Cazador",
    "Hyena": "Hiena",
    "Ice Devil": "Diablo de Hielo",
    "Ice Mephit": "Mefít de Hielo",
    "Imp": "Diablillo",
    "Invisible Stalker": "Acechador Invisible",
    "Iron Golem": "Gólem de Hierro",
    "Jackal": "Chacal",
    "Killer Whale": "Orca",
    "Knight": "Caballero",
    "Lemure": "Lémure",
    "Leopard": "Leopardo",
    "Lion": "León",
    "Lizard": "Lagarto",
    "Lizardfolk": "Hombre Lagarto",
    "Mage": "Mago",
    "Magma Mephit": "Mefít de Magma",
    "Magmin": "Magmin",
    "Mammoth": "Mamut",
    "Mastiff": "Mastín",
    "Mule": "Mula",
    "Mummy": "Momia",
    "Mummy Lord": "Señor Momia",
    "Night Hag": "Bruja Nocturna",
    "Noble": "Noble",
    "Ochre Jelly": "Jalea Ocre",
    "Octopus": "Pulpo",
    "Ogre": "Ogro",
    "Oni": "Oni",
    "Orc": "Orco",
    "Owl": "Búho",
    "Panther": "Pantera",
    "Phase Spider": "Araña de Fase",
    "Plesiosaurus": "Plesiosaurio",
    "Poisonous Snake": "Serpiente Venenosa",
    "Polar Bear": "Oso Polar",
    "Pony": "Poni",
    "Priest": "Sacerdote",
    "Pteranodon": "Pteranodón",
    "Purple Worm": "Gusano Púrpura",
    "Quasit": "Quasit",
    "Quipper": "Piraña",
    "Rat": "Rata",
    "Raven": "Cuervo",
    "Red Dragon Wyrmling": "Cría de Dragón Rojo",
    "Reef Shark": "Tiburón de Arrecife",
    "Rhinoceros": "Rinoceronte",
    "Riding Horse": "Caballo de Montar",
    "Rug of Smothering": "Alfombra Asfixiante",
    "Saber-Toothed Tiger": "Tigre Dientes de Sable",
    "Scorpion": "Escorpión",
    "Scout": "Explorador",
    "Sea Hag": "Bruja Marina",
    "Sea Horse": "Caballito de Mar",
    "Shadow": "Sombra",
    "Silver Dragon Wyrmling": "Cría de Dragón de Plata",
    "Skeleton": "Esqueleto",
    "Smoke Mephit": "Mefít de Humo",
    "Solar": "Solar",
    "Specter": "Espectro",
    "Spider": "Araña",
    "Spirit Naga": "Naga Espiritual",
    "Sprite": "Duendecillo",
    "Spy": "Espía",
    "Steam Mephit": "Mefít de Vapor",
    "Stone Giant": "Gigante de Piedra",
    "Stone Golem": "Gólem de Piedra",
    "Storm Giant": "Gigante de las Tormentas",
    "Swarm of Bats": "Enjambre de Murciélagos",
    "Swarm of Insects": "Enjambre de Insectos",
    "Swarm of Poisonous Snakes": "Enjambre de Serpientes Venenosas",
    "Swarm of Quippers": "Enjambre de Pirañas",
    "Swarm of Rats": "Enjambre de Ratas",
    "Swarm of Ravens": "Enjambre de Cuervos",
    "Thug": "Matón",
    "Tiger": "Tigre",
    "Tribal Warrior": "Guerrero Tribal",
    "Triceratops": "Triceratops",
    "Tyrannosaurus Rex": "Tiranosaurio Rex",
    "Vampire Spawn": "Engendro Vampírico",
    "Veteran": "Veterano",
    "Vulture": "Buitre",
    "Warhorse": "Caballo de Guerra",
    "Warhorse Skeleton": "Esqueleto de Caballo de Guerra",
    "Water Elemental": "Elemental de Agua",
    "Weasel": "Comadreja",
    "Wereboar": "Hombre Jabalí",
    "Werebear": "Hombre Oso",
    "Wererat": "Hombre Rata",
    "Weretiger": "Hombre Tigre",
    "Werewolf": "Hombre Lobo",
    "White Dragon Wyrmling": "Cría de Dragón Blanco",
    "Winter Wolf": "Lobo Invernal",
    "Wolf": "Lobo",
    "Worg": "Wargo",
    "Zombie": "Zombi",
    "Young Black Dragon": "Dragón Negro Joven",
    "Young Blue Dragon": "Dragón Azul Joven",
    "Young Brass Dragon": "Dragón de Latón Joven",
    "Young Bronze Dragon": "Dragón de Bronce Joven",
    "Young Copper Dragon": "Dragón de Cobre Joven",
    "Young Gold Dragon": "Dragón de Oro Joven",
    "Young Green Dragon": "Dragón Verde Joven",
    "Young Red Dragon": "Dragón Rojo Joven",
    "Young Silver Dragon": "Dragón de Plata Joven",
    "Young White Dragon": "Dragón Blanco Joven",
}

# === XP por CR ===
XP_POR_CR = {
    "0": 10, "1/8": 25, "1/4": 50, "1/2": 100,
    "1": 200, "2": 450, "3": 700, "4": 1100, "5": 1800,
    "6": 2300, "7": 2900, "8": 3900, "9": 5000, "10": 5900,
    "11": 7200, "12": 8400, "13": 10000, "14": 11500, "15": 13000,
    "16": 15000, "17": 18000, "18": 20000, "19": 22000, "20": 25000,
    "21": 33000, "22": 41000, "23": 50000, "24": 62000, "25": 75000,
    "26": 90000, "27": 105000, "28": 120000, "29": 135000, "30": 155000,
}

# === TRADUCCIONES DE NOMBRES DE ACCIONES ===
ACCIONES_TRADUCCION = {
    # Ataques básicos
    "Bite": "Mordisco",
    "Claw": "Garra",
    "Claws": "Garras",
    "Tail": "Cola",
    "Slam": "Golpe",
    "Gore": "Cornada",
    "Hooves": "Cascos",
    "Hoof": "Casco",
    "Talons": "Garras",
    "Tentacle": "Tentáculo",
    "Tentacles": "Tentáculos",
    "Beak": "Pico",
    "Sting": "Aguijón",
    "Fist": "Puño",
    "Stomp": "Pisotón",
    "Constrict": "Constricción",
    "Crush": "Aplastamiento",
    "Touch": "Toque",
    "Ram": "Embestida",
    "Tusk": "Colmillo",
    "Tusks": "Colmillos",
    "Pincer": "Pinza",
    "Pincers": "Pinzas",
    # Armas
    "Shortsword": "Espada Corta",
    "Longsword": "Espada Larga",
    "Greatsword": "Espada de Dos Manos",
    "Scimitar": "Cimitarra",
    "Dagger": "Daga",
    "Spear": "Lanza",
    "Javelin": "Jabalina",
    "Greataxe": "Hacha Grande",
    "Handaxe": "Hacha de Mano",
    "Battleaxe": "Hacha de Batalla",
    "Mace": "Maza",
    "Morningstar": "Lucero del Alba",
    "Flail": "Mangual",
    "Warhammer": "Martillo de Guerra",
    "Maul": "Mazo",
    "Quarterstaff": "Bastón",
    "Club": "Garrote",
    "Greatclub": "Garrote Grande",
    "Shortbow": "Arco Corto",
    "Longbow": "Arco Largo",
    "Light Crossbow": "Ballesta Ligera",
    "Heavy Crossbow": "Ballesta Pesada",
    "Hand Crossbow": "Ballesta de Mano",
    "Sling": "Honda",
    "Trident": "Tridente",
    "War Pick": "Pico de Guerra",
    "Glaive": "Guja",
    "Halberd": "Alabarda",
    "Pike": "Pica",
    "Lance": "Lanza de Caballería",
    "Whip": "Látigo",
    "Net": "Red",
    "Blowgun": "Cerbatana",
    # Ataques especiales
    "Multiattack": "Multiataque",
    "Frightful Presence": "Presencia Aterradora",
    "Fire Breath": "Aliento de Fuego",
    "Acid Breath": "Aliento Ácido",
    "Cold Breath": "Aliento de Frío",
    "Lightning Breath": "Aliento de Relámpago",
    "Poison Breath": "Aliento Venenoso",
    "Steam Breath": "Aliento de Vapor",
    "Frost Breath": "Aliento Gélido",
    "Breath Weapons": "Armas de Aliento",
    "Sleep Breath": "Aliento Soporífero",
    "Repulsion Breath": "Aliento de Repulsión",
    "Weakening Breath": "Aliento Debilitador",
    "Slowing Breath": "Aliento Ralentizador",
    "Paralyzing Breath": "Aliento Paralizante",
    # Habilidades
    "Invisibility": "Invisibilidad",
    "Teleport": "Teletransportación",
    "Change Shape": "Cambiar Forma",
    "Healing Touch": "Toque Sanador",
    "Life Drain": "Drenar Vida",
    "Charm": "Hechizar",
    "Etherealness": "Eteralidad",
    "Possession": "Posesión",
    "Detect": "Detectar",
    "Wing Attack": "Ataque de Alas",
    "Tail Attack": "Ataque de Cola",
    "Swallow": "Tragar",
    "Engulf": "Envolver",
    "Reel": "Atraer",
    "Web": "Telaraña",
    "Scare": "Asustar",
    "Leadership": "Liderazgo",
    "Roar": "Rugido",
    "Wail": "Lamento",
    # Otros
    "Corrupting Touch": "Toque Corruptor",
    "Draining Kiss": "Beso Drenador",
    "Horrifying Visage": "Aspecto Horripilante",
    "Dreadful Glare": "Mirada Terrible",
    "Withering Touch": "Toque Marchitador",
    "Hurl Flame": "Lanzar Llamas",
}

# Patrones de recarga
RECARGA_PATRONES = {
    "Recharge 5–6": {"tipo": "dado", "rango": [5, 6]},
    "Recharge 5-6": {"tipo": "dado", "rango": [5, 6]},
    "Recharge 4–6": {"tipo": "dado", "rango": [4, 6]},
    "Recharge 4-6": {"tipo": "dado", "rango": [4, 6]},
    "Recharge 6": {"tipo": "dado", "rango": [6, 6]},
    "Recharges after a Short or Long Rest": {"tipo": "descanso_corto"},
    "1/Day": {"tipo": "por_dia", "usos": 1},
    "2/Day": {"tipo": "por_dia", "usos": 2},
    "3/Day": {"tipo": "por_dia", "usos": 3},
}


def traducir_nombre_accion(nombre_en: str) -> str:
    """Traduce el nombre de una acción al español."""
    # Primero buscar coincidencia exacta
    if nombre_en in ACCIONES_TRADUCCION:
        return ACCIONES_TRADUCCION[nombre_en]
    
    # Buscar sin paréntesis (ej: "Fire Breath (Recharge 5–6)" -> "Fire Breath")
    nombre_base = re.sub(r'\s*\([^)]+\)', '', nombre_en).strip()
    if nombre_base in ACCIONES_TRADUCCION:
        # Mantener el paréntesis pero traducir
        parentesis = re.search(r'\(([^)]+)\)', nombre_en)
        if parentesis:
            return f"{ACCIONES_TRADUCCION[nombre_base]} ({parentesis.group(1)})"
        return ACCIONES_TRADUCCION[nombre_base]
    
    # No encontrado, devolver original
    return nombre_en


def extraer_recarga(nombre: str) -> Optional[Dict]:
    """Extrae información de recarga del nombre de una acción."""
    for patron, info in RECARGA_PATRONES.items():
        if patron in nombre:
            return info.copy()
    return None


# === FUNCIONES DE PARSEO ===

def limpiar_html(texto: str) -> str:
    """Elimina tags HTML y decodifica entidades."""
    if not texto:
        return ""
    texto = html.unescape(texto)
    texto = re.sub(r'<[^>]+>', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def generar_id(nombre: str) -> str:
    """Genera ID en snake_case desde nombre."""
    nombre_limpio = nombre.lower()
    nombre_limpio = re.sub(r'[^a-z0-9áéíóúñü\s]', '', nombre_limpio)
    nombre_limpio = nombre_limpio.replace('á', 'a').replace('é', 'e').replace('í', 'i')
    nombre_limpio = nombre_limpio.replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
    nombre_limpio = nombre_limpio.replace('ü', 'u')
    return re.sub(r'\s+', '_', nombre_limpio.strip())


def traducir_nombre(nombre_en: str) -> str:
    """Traduce nombre de monstruo al español si es posible."""
    if nombre_en in NOMBRES_TRADUCCION:
        return NOMBRES_TRADUCCION[nombre_en]
    # Si no hay traducción, devolver original
    return nombre_en


def parsear_meta(meta: str) -> Tuple[str, str, Optional[str], str]:
    """Parsea la línea meta: 'Large dragon, chaotic evil' -> (tamaño, tipo, subtipo, alineamiento)"""
    # Formato: "Size type (subtype), alignment"
    match = re.match(r'(\w+)\s+(\w+)(?:\s*\(([^)]+)\))?,?\s*(.*)', meta, re.IGNORECASE)
    if not match:
        return "Mediano", "Monstruosidad", None, "Neutral"
    
    size_en = match.group(1)
    type_en = match.group(2).lower()
    subtype = match.group(3)
    alignment_en = match.group(4).lower().strip() if match.group(4) else "neutral"
    
    tamaño = TAMAÑOS.get(size_en, "Mediano")
    tipo = TIPOS_CRIATURA.get(type_en, "Monstruosidad")
    alineamiento = ALINEAMIENTOS.get(alignment_en, "Neutral")
    
    return tamaño, tipo, subtype, alineamiento


def parsear_ca(ca_str: str) -> Tuple[int, Optional[str]]:
    """Parsea 'Armor Class': '17 (Natural Armor)' -> (17, 'armadura natural')"""
    match = re.match(r'(\d+)\s*(?:\(([^)]+)\))?', ca_str)
    if not match:
        return 10, None
    
    ca = int(match.group(1))
    fuente = match.group(2)
    
    # Traducir fuente de CA
    if fuente:
        fuente = fuente.lower()
        traducciones = {
            "natural armor": "armadura natural",
            "leather armor": "armadura de cuero",
            "studded leather": "cuero tachonado",
            "hide armor": "armadura de pieles",
            "chain shirt": "cota de mallas",
            "chain mail": "cota de mallas",
            "scale mail": "cota de escamas",
            "plate": "armadura de placas",
            "shield": "escudo",
        }
        for en, es in traducciones.items():
            if en in fuente:
                fuente = fuente.replace(en, es)
    
    return ca, fuente


def parsear_hp(hp_str: str) -> Tuple[int, str]:
    """Parsea 'Hit Points': '135 (18d10 + 36)' -> (135, '18d10+36')"""
    match = re.match(r'(\d+)\s*\(([^)]+)\)', hp_str)
    if not match:
        # Intentar solo el número
        num_match = re.match(r'(\d+)', hp_str)
        if num_match:
            return int(num_match.group(1)), "1d8"
        return 10, "1d8"
    
    hp = int(match.group(1))
    formula = match.group(2).replace(' ', '')
    return hp, formula


def parsear_velocidades(speed_str: str) -> Dict[str, int]:
    """Parsea 'Speed': '40 ft., fly 80 ft., swim 40 ft.' -> dict"""
    velocidades = {"tierra": 0, "vuelo": 0, "nado": 0, "trepar": 0, "excavar": 0}
    
    # Velocidad base (tierra)
    base_match = re.match(r'(\d+)\s*ft\.', speed_str)
    if base_match:
        velocidades["tierra"] = int(base_match.group(1))
    
    # Otras velocidades
    patrones = {
        r'fly\s+(\d+)\s*ft': "vuelo",
        r'swim\s+(\d+)\s*ft': "nado",
        r'climb\s+(\d+)\s*ft': "trepar",
        r'burrow\s+(\d+)\s*ft': "excavar",
    }
    
    for patron, clave in patrones.items():
        match = re.search(patron, speed_str, re.IGNORECASE)
        if match:
            velocidades[clave] = int(match.group(1))
    
    return velocidades


def parsear_tiradas_salvacion(saves_str: str) -> Dict[str, int]:
    """Parsea 'Saving Throws': 'DEX +7, CON +10, WIS +6' -> dict"""
    resultado = {}
    if not saves_str:
        return resultado
    
    patron = r'(STR|DEX|CON|INT|WIS|CHA)\s*\+(\d+)'
    for match in re.finditer(patron, saves_str, re.IGNORECASE):
        stat_en = match.group(1).upper()
        valor = int(match.group(2))
        stat_es = CARACTERISTICAS.get(stat_en, stat_en.lower())
        resultado[stat_es] = valor
    
    return resultado


def parsear_habilidades(skills_str: str) -> Dict[str, int]:
    """Parsea 'Skills': 'Perception +11, Stealth +7' -> dict"""
    resultado = {}
    if not skills_str:
        return resultado
    
    patron = r'(\w+(?:\s+\w+)?)\s*\+(\d+)'
    for match in re.finditer(patron, skills_str):
        skill_en = match.group(1).lower()
        valor = int(match.group(2))
        skill_es = HABILIDADES.get(skill_en, skill_en)
        resultado[skill_es] = valor
    
    return resultado


def parsear_sentidos(senses_str: str) -> Dict[str, int]:
    """Parsea 'Senses': 'Darkvision 120 ft., Passive Perception 20' -> dict"""
    resultado = {}
    if not senses_str:
        return resultado
    
    patrones = {
        r'darkvision\s+(\d+)': "vision_oscura",
        r'blindsight\s+(\d+)': "vision_ciega",
        r'tremorsense\s+(\d+)': "sentido_temblor",
        r'truesight\s+(\d+)': "vision_verdadera",
        r'passive\s+perception\s+(\d+)': "percepcion_pasiva",
    }
    
    for patron, clave in patrones.items():
        match = re.search(patron, senses_str, re.IGNORECASE)
        if match:
            resultado[clave] = int(match.group(1))
    
    return resultado


def parsear_cr(challenge_str: str) -> Tuple[float, int]:
    """Parsea 'Challenge': '10 (5,900 XP)' -> (10.0, 5900)"""
    # Extraer CR
    cr_match = re.match(r'([\d/]+)', challenge_str)
    if not cr_match:
        return 0, 10
    
    cr_str = cr_match.group(1)
    if '/' in cr_str:
        num, den = cr_str.split('/')
        cr = int(num) / int(den)
    else:
        cr = float(cr_str)
    
    # XP de la tabla
    xp = XP_POR_CR.get(cr_str, 0)
    
    return cr, xp


def traducir_tipos_daño(lista: List[str]) -> List[str]:
    """Traduce lista de tipos de daño EN -> ES"""
    resultado = []
    for item in lista:
        item_lower = item.lower().strip()
        traducido = TIPOS_DAÑO.get(item_lower, item_lower)
        resultado.append(traducido)
    return resultado


def parsear_inmunidades_daño(dmg_str: str) -> List[str]:
    """Parsea 'Damage Immunities': 'Fire, Poison' -> ['fuego', 'veneno']"""
    if not dmg_str:
        return []
    
    # Separar por comas, pero cuidado con frases como "from Nonmagical Attacks"
    partes = re.split(r',\s*(?![^()]*\))', dmg_str)
    resultado = []
    
    for parte in partes:
        parte = parte.strip().lower()
        # Ignorar modificadores como "from nonmagical attacks"
        parte = re.sub(r'\s*from\s+.*', '', parte)
        parte = re.sub(r'\s*that\s+.*', '', parte)
        
        if parte in TIPOS_DAÑO:
            resultado.append(TIPOS_DAÑO[parte])
        elif parte:
            resultado.append(parte)
    
    return resultado


def parsear_inmunidades_condicion(cond_str: str) -> List[str]:
    """Parsea 'Condition Immunities' -> lista traducida"""
    if not cond_str:
        return []
    
    partes = [p.strip().lower() for p in cond_str.split(',')]
    resultado = []
    
    for parte in partes:
        if parte in CONDICIONES:
            resultado.append(CONDICIONES[parte])
        elif parte:
            resultado.append(parte)
    
    return resultado


def parsear_idiomas(lang_str: str) -> List[str]:
    """Parsea 'Languages' -> lista"""
    if not lang_str or lang_str.strip() == '--' or lang_str.strip() == '—':
        return []
    
    traducciones = {
        "common": "Común",
        "draconic": "Dracónico",
        "elvish": "Élfico",
        "dwarvish": "Enano",
        "giant": "Gigante",
        "goblin": "Goblin",
        "orc": "Orco",
        "abyssal": "Abisal",
        "infernal": "Infernal",
        "celestial": "Celestial",
        "primordial": "Primordial",
        "sylvan": "Silvano",
        "undercommon": "Infracomún",
        "deep speech": "Habla Profunda",
        "telepathy": "Telepatía",
    }
    
    partes = [p.strip() for p in lang_str.split(',')]
    resultado = []
    
    for parte in partes:
        parte_lower = parte.lower()
        # Buscar traducción
        traducido = None
        for en, es in traducciones.items():
            if en in parte_lower:
                traducido = parte.replace(en, es)
                break
        resultado.append(traducido if traducido else parte)
    
    return resultado


def parsear_accion_ataque(texto: str) -> Optional[Dict[str, Any]]:
    """Intenta parsear un ataque de arma del texto HTML."""
    texto_limpio = limpiar_html(texto)
    
    # Patrón para ataques
    patron = re.compile(
        r'(?P<nombre>[^.]+)\.\s*'
        r'(?P<tipo>Melee|Ranged)\s+Weapon\s+Attack:\s*'
        r'\+(?P<bonus>\d+)\s+to\s+hit,\s*'
        r'(?:reach\s+(?P<alcance>\d+)\s*ft\.|'
        r'range\s+(?P<corto>\d+)/(?P<largo>\d+)\s*ft\.)[^.]*\.\s*'
        r'Hit:\s*(?P<avg>\d+)\s*\((?P<dados>[^)]+)\)\s*'
        r'(?P<tipo_daño>\w+)\s+damage',
        re.IGNORECASE
    )
    
    match = patron.search(texto_limpio)
    if not match:
        return None
    
    nombre = match.group('nombre').strip()
    es_melee = match.group('tipo').lower() == 'melee'
    
    accion = {
        "id": generar_id(nombre),
        "nombre": nombre,
        "tipo": "ataque",
        "modalidad": "cuerpo" if es_melee else "distancia",
        "ataque": {
            "bonificador": int(match.group('bonus')),
        },
        "objetivos_max": 1,
        "impacto": [{
            "tipo": "daño",
            "cantidad": match.group('dados').replace(' ', ''),
            "tipo_daño": TIPOS_DAÑO.get(match.group('tipo_daño').lower(), match.group('tipo_daño').lower())
        }],
        "texto_srd": texto_limpio
    }
    
    if es_melee:
        accion["ataque"]["alcance_pies"] = int(match.group('alcance') or 5)
    else:
        accion["ataque"]["alcance_corto"] = int(match.group('corto'))
        accion["ataque"]["alcance_largo"] = int(match.group('largo'))
    
    # Buscar daño adicional "plus X (dice) type damage"
    extra_match = re.search(
        r'plus\s+(\d+)\s*\(([^)]+)\)\s*(\w+)\s+damage', 
        texto_limpio, 
        re.IGNORECASE
    )
    if extra_match:
        accion["impacto"].append({
            "tipo": "daño",
            "cantidad": extra_match.group(2).replace(' ', ''),
            "tipo_daño": TIPOS_DAÑO.get(extra_match.group(3).lower(), extra_match.group(3).lower())
        })
    
    return accion


def parsear_breath_weapon(texto: str) -> Optional[Dict[str, Any]]:
    """Parsea un aliento de dragón u otra habilidad de área similar."""
    texto_limpio = limpiar_html(texto)
    
    # Patrón para breath weapons
    # Ejemplo: "Fire Breath (Recharge 5–6). The dragon exhales fire in a 60-foot cone. 
    # Each creature in that line must make a DC 18 Dexterity saving throw, 
    # taking 54 (12d8) acid damage on a failed save, or half as much damage on a successful one."
    
    patron_breath = re.compile(
        r'(?P<nombre>[^.]+)\.\s*'
        r'(?:The \w+ )?exhales?\s+(?P<tipo_elemento>\w+)\s+'
        r'in\s+(?:a|an)\s+(?P<longitud>\d+)[- ]?(?:foot|ft\.?)\s+'
        r'(?P<forma>line|cone)\s*'
        r'(?:that is (?P<ancho>\d+)\s*(?:feet|ft\.?)?\s*wide)?',
        re.IGNORECASE
    )
    
    match = patron_breath.search(texto_limpio)
    if not match:
        return None
    
    nombre_en = match.group('nombre').strip()
    nombre_es = traducir_nombre_accion(nombre_en)
    
    # Buscar salvación y daño
    save_match = re.search(
        r'DC\s+(?P<cd>\d+)\s+(?P<stat>Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)',
        texto_limpio,
        re.IGNORECASE
    )
    
    damage_match = re.search(
        r'(?P<avg>\d+)\s*\((?P<dados>[^)]+)\)\s*(?P<tipo>\w+)\s+damage',
        texto_limpio,
        re.IGNORECASE
    )
    
    accion = {
        "id": generar_id(nombre_es),
        "nombre": nombre_es,
        "tipo": "habilidad_especial",
        "area": {
            "forma": "cono" if match.group('forma').lower() == 'cone' else "linea",
            "longitud_pies": int(match.group('longitud')),
            "seleccion": "todas_en_area"
        },
        "texto_srd": texto_limpio,
        "nivel_parseo": "completo"
    }
    
    # Añadir ancho si es línea
    if match.group('ancho'):
        accion["area"]["ancho_pies"] = int(match.group('ancho'))
    
    # Añadir recarga
    recarga = extraer_recarga(nombre_en)
    if recarga:
        accion["recarga"] = recarga
    
    # Añadir salvación
    if save_match:
        stat_en = save_match.group('stat')
        accion["salvacion"] = {
            "caracteristica": CARACTERISTICAS.get(stat_en, stat_en.lower()),
            "cd": int(save_match.group('cd'))
        }
    
    # Añadir daño
    if damage_match:
        tipo_daño_en = damage_match.group('tipo').lower()
        accion["impacto"] = [{
            "tipo": "daño",
            "cantidad": damage_match.group('dados').replace(' ', ''),
            "tipo_daño": TIPOS_DAÑO.get(tipo_daño_en, tipo_daño_en),
            "mitad_si_exito": True
        }]
    
    return accion


def parsear_acciones(actions_html: str) -> Tuple[List[Dict], Optional[Dict], List[str]]:
    """
    Parsea el HTML de acciones.
    Retorna: (lista_acciones, multiataque, advertencias)
    """
    if not actions_html:
        return [], None, []
    
    acciones = []
    multiataque = None
    advertencias = []
    
    # Dividir por <p> tags
    bloques = re.findall(r'<p>(.*?)</p>', actions_html, re.DOTALL | re.IGNORECASE)
    
    for bloque in bloques:
        bloque_limpio = limpiar_html(bloque)
        
        # Detectar Multiattack
        if bloque_limpio.lower().startswith('multiattack'):
            multiataque = {
                "nombre": "Multiataque",
                "texto_srd": bloque_limpio,
                "ataques": []
            }
            continue
        
        # Intentar parsear como Breath Weapon primero
        accion = parsear_breath_weapon(bloque)
        if accion:
            acciones.append(accion)
            continue
        
        # Intentar parsear como ataque de arma
        accion = parsear_accion_ataque(bloque)
        if accion:
            # Traducir nombre de la acción
            nombre_traducido = traducir_nombre_accion(accion["nombre"])
            accion["nombre"] = nombre_traducido
            accion["id"] = generar_id(nombre_traducido)
            acciones.append(accion)
        else:
            # Es una acción no parseable - guardar como texto con traducción
            nombre_match = re.match(r'([^.]+)\.', bloque_limpio)
            if nombre_match:
                nombre_en = nombre_match.group(1).strip()
                nombre_es = traducir_nombre_accion(nombre_en)
                
                accion_texto = {
                    "id": generar_id(nombre_es),
                    "nombre": nombre_es,
                    "tipo": "habilidad_especial",
                    "texto_srd": bloque_limpio,
                    "nivel_parseo": "texto"
                }
                
                # Extraer recarga si existe
                recarga = extraer_recarga(nombre_en)
                if recarga:
                    accion_texto["recarga"] = recarga
                
                acciones.append(accion_texto)
                
                # Solo advertir si NO es un breath weapon (ya parseado) o si no se pudo parsear
                if "breath" not in nombre_en.lower():
                    advertencias.append(f"Acción no parseada: {nombre_en}")
    
    return acciones, multiataque, advertencias


def parsear_rasgos(traits_html: str) -> Tuple[List[Dict], List[str]]:
    """
    Parsea rasgos del HTML.
    Retorna: (lista_rasgos, advertencias)
    """
    if not traits_html:
        return [], []
    
    rasgos = []
    advertencias = []
    
    bloques = re.findall(r'<p>(.*?)</p>', traits_html, re.DOTALL | re.IGNORECASE)
    
    for bloque in bloques:
        bloque_limpio = limpiar_html(bloque)
        
        # Extraer nombre del rasgo
        nombre_match = re.match(r'([^.]+)\.', bloque_limpio)
        if not nombre_match:
            continue
        
        nombre = nombre_match.group(1).strip()
        descripcion = bloque_limpio[len(nombre)+1:].strip()
        
        rasgo = {
            "nombre": nombre,
            "texto_srd": bloque_limpio,
            "tags": [],
            "nivel_parseo": "texto"
        }
        
        # Detectar rasgos parseables
        nombre_lower = nombre.lower()
        
        # Magic Resistance
        if "magic resistance" in nombre_lower:
            rasgo["tags"] = ["ventaja_ts", "magia"]
            rasgo["nivel_parseo"] = "parcial"
        
        # Pack Tactics
        elif "pack tactics" in nombre_lower:
            rasgo["tags"] = ["ventaja_ataque", "aliado_cerca"]
            rasgo["nivel_parseo"] = "parcial"
        
        # Keen Senses
        elif "keen" in nombre_lower:
            rasgo["tags"] = ["ventaja_percepcion"]
            rasgo["nivel_parseo"] = "parcial"
        
        # Sunlight Sensitivity
        elif "sunlight" in nombre_lower and "sensitivity" in nombre_lower:
            rasgo["tags"] = ["desventaja_ataque", "luz_solar"]
            rasgo["nivel_parseo"] = "parcial"
        
        # Legendary Resistance
        elif "legendary resistance" in nombre_lower:
            usos_match = re.search(r'\((\d+)/day\)', nombre_lower)
            rasgo["tags"] = ["legendario", "resistencia"]
            if usos_match:
                rasgo["usos_por_dia"] = int(usos_match.group(1))
            rasgo["nivel_parseo"] = "parcial"
        
        # Regeneration
        elif "regeneration" in nombre_lower:
            cant_match = re.search(r'regains\s+(\d+)', descripcion.lower())
            rasgo["tags"] = ["regeneracion"]
            if cant_match:
                rasgo["regeneracion_cantidad"] = int(cant_match.group(1))
            rasgo["nivel_parseo"] = "parcial"
        
        # Amphibious
        elif "amphibious" in nombre_lower:
            rasgo["tags"] = ["anfibio", "agua", "aire"]
            rasgo["nivel_parseo"] = "completo"
        
        rasgos.append(rasgo)
    
    return rasgos, advertencias


def parsear_acciones_legendarias(leg_html: str) -> Optional[Dict]:
    """Parsea acciones legendarias."""
    if not leg_html:
        return None
    
    resultado = {
        "cantidad_por_ronda": 3,
        "texto_intro": "",
        "acciones": []
    }
    
    bloques = re.findall(r'<p>(.*?)</p>', leg_html, re.DOTALL | re.IGNORECASE)
    
    for i, bloque in enumerate(bloques):
        bloque_limpio = limpiar_html(bloque)
        
        # El primer bloque suele ser la introducción
        if i == 0 and "can take" in bloque_limpio.lower():
            resultado["texto_intro"] = bloque_limpio
            # Extraer cantidad
            cant_match = re.search(r'can take (\d+)', bloque_limpio)
            if cant_match:
                resultado["cantidad_por_ronda"] = int(cant_match.group(1))
            continue
        
        # Parsear acción legendaria
        nombre_match = re.match(r'([^.]+)\.', bloque_limpio)
        if not nombre_match:
            continue
        
        nombre = nombre_match.group(1).strip()
        
        # Detectar coste
        coste = 1
        coste_match = re.search(r'\(costs?\s*(\d+)', nombre.lower())
        if coste_match:
            coste = int(coste_match.group(1))
            nombre = re.sub(r'\s*\(costs?\s*\d+\s*actions?\)', '', nombre, flags=re.IGNORECASE).strip()
        
        resultado["acciones"].append({
            "id": generar_id(nombre),
            "nombre": nombre,
            "coste": coste,
            "texto_srd": bloque_limpio
        })
    
    return resultado if resultado["acciones"] else None


def convertir_monstruo(srd_monster: Dict, index: int) -> Tuple[Dict, List[str]]:
    """Convierte un monstruo del SRD al formato interno."""
    advertencias = []
    
    nombre_en = srd_monster.get("name", "Unknown")
    nombre_es = traducir_nombre(nombre_en)
    
    # Parsear meta
    tamaño, tipo, subtipo, alineamiento = parsear_meta(srd_monster.get("meta", ""))
    
    # Parsear CA
    ca, fuente_ca = parsear_ca(srd_monster.get("Armor Class", "10"))
    
    # Parsear HP
    hp, dados_hp = parsear_hp(srd_monster.get("Hit Points", "10 (1d8)"))
    
    # Parsear velocidades
    velocidades = parsear_velocidades(srd_monster.get("Speed", "30 ft."))
    
    # Atributos
    atributos = {
        "fuerza": int(srd_monster.get("STR", 10)),
        "destreza": int(srd_monster.get("DEX", 10)),
        "constitucion": int(srd_monster.get("CON", 10)),
        "inteligencia": int(srd_monster.get("INT", 10)),
        "sabiduria": int(srd_monster.get("WIS", 10)),
        "carisma": int(srd_monster.get("CHA", 10)),
    }
    
    # Tiradas de salvación
    tiradas_salv = parsear_tiradas_salvacion(srd_monster.get("Saving Throws", ""))
    
    # Habilidades
    habilidades = parsear_habilidades(srd_monster.get("Skills", ""))
    
    # Resistencias e inmunidades
    resistencias = parsear_inmunidades_daño(srd_monster.get("Damage Resistances", ""))
    inmunidades_daño = parsear_inmunidades_daño(srd_monster.get("Damage Immunities", ""))
    vulnerabilidades = parsear_inmunidades_daño(srd_monster.get("Damage Vulnerabilities", ""))
    inmunidades_cond = parsear_inmunidades_condicion(srd_monster.get("Condition Immunities", ""))
    
    # Sentidos
    sentidos = parsear_sentidos(srd_monster.get("Senses", ""))
    
    # Idiomas
    idiomas = parsear_idiomas(srd_monster.get("Languages", ""))
    
    # CR y XP
    desafio, xp = parsear_cr(srd_monster.get("Challenge", "0"))
    
    # Rasgos
    rasgos, rasgos_adv = parsear_rasgos(srd_monster.get("Traits", ""))
    advertencias.extend(rasgos_adv)
    
    # Acciones
    acciones, multiataque, acciones_adv = parsear_acciones(srd_monster.get("Actions", ""))
    advertencias.extend(acciones_adv)
    
    # Acciones legendarias
    acc_legendarias = parsear_acciones_legendarias(srd_monster.get("Legendary Actions", ""))
    
    # Construir resultado
    resultado = {
        "id": generar_id(nombre_es),
        "nombre": nombre_es,
        "srd_ref": {
            "name": nombre_en,
            "source": "SRD 5.1",
            "index": index
        },
        "tamaño": tamaño,
        "tipo": tipo,
        "alineamiento": alineamiento,
        "clase_armadura": ca,
        "puntos_golpe": hp,
        "dados_golpe": dados_hp,
        "velocidades": velocidades,
        "atributos": atributos,
        "sentidos": sentidos,
        "idiomas": idiomas,
        "desafio": desafio,
        "experiencia": xp,
        "rasgos": rasgos,
        "acciones": acciones,
    }
    
    # Campos opcionales
    if subtipo:
        resultado["subtipo"] = subtipo
    if fuente_ca:
        resultado["fuente_ca"] = fuente_ca
    if tiradas_salv:
        resultado["tiradas_salvacion"] = tiradas_salv
    if habilidades:
        resultado["habilidades"] = habilidades
    if resistencias:
        resultado["resistencias"] = resistencias
    if inmunidades_daño:
        resultado["inmunidades_daño"] = inmunidades_daño
    if vulnerabilidades:
        resultado["vulnerabilidades"] = vulnerabilidades
    if inmunidades_cond:
        resultado["inmunidades_condicion"] = inmunidades_cond
    if multiataque:
        resultado["multiataque"] = multiataque
    if acc_legendarias:
        resultado["acciones_legendarias"] = acc_legendarias
    
    return resultado, advertencias


def main():
    print("=" * 60)
    print("  Conversión SRD Monsters → Compendio Interno")
    print("=" * 60)
    print()
    
    # Cargar SRD
    print(f"Cargando {SRD_INPUT}...")
    with open(SRD_INPUT, 'r', encoding='utf-8') as f:
        srd_monsters = json.load(f)
    
    print(f"Encontrados {len(srd_monsters)} monstruos en SRD")
    print()
    
    # Convertir
    monstruos_convertidos = []
    todas_advertencias = []
    
    for i, monster in enumerate(srd_monsters):
        nombre = monster.get("name", "?")
        try:
            convertido, advertencias = convertir_monstruo(monster, i)
            monstruos_convertidos.append(convertido)
            
            if advertencias:
                todas_advertencias.append((nombre, advertencias))
            
            if (i + 1) % 50 == 0:
                print(f"  Procesados {i + 1}/{len(srd_monsters)}...")
        
        except Exception as e:
            print(f"  ❌ Error en {nombre}: {e}")
            todas_advertencias.append((nombre, [f"ERROR: {e}"]))
    
    print()
    print(f"✓ Convertidos {len(monstruos_convertidos)} monstruos")
    
    # Guardar resultado
    resultado = {
        "version": "2.0.0",
        "fuente": "SRD 5.1",
        "generado": datetime.now().isoformat(),
        "total_monstruos": len(monstruos_convertidos),
        "monstruos": monstruos_convertidos
    }
    
    print(f"Guardando en {OUTPUT}...")
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    
    # Generar informe
    print(f"Generando informe en {REPORT_FILE}...")
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("  INFORME DE CONVERSIÓN SRD → COMPENDIO\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Monstruos procesados: {len(srd_monsters)}\n")
        f.write(f"Monstruos convertidos: {len(monstruos_convertidos)}\n")
        f.write(f"Monstruos con advertencias: {len(todas_advertencias)}\n\n")
        
        if todas_advertencias:
            f.write("-" * 60 + "\n")
            f.write("  ADVERTENCIAS\n")
            f.write("-" * 60 + "\n\n")
            
            for nombre, advs in todas_advertencias:
                f.write(f"{nombre}:\n")
                for adv in advs:
                    f.write(f"  - {adv}\n")
                f.write("\n")
    
    print()
    print("=" * 60)
    print("  ¡CONVERSIÓN COMPLETADA!")
    print("=" * 60)
    print(f"  Archivo: {OUTPUT}")
    print(f"  Monstruos: {len(monstruos_convertidos)}")
    print(f"  Advertencias: {len(todas_advertencias)}")
    print()


if __name__ == "__main__":
    main()
