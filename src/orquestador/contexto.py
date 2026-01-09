"""
Gestor de contexto para el LLM.

Mantiene el estado acumulado de la aventura y genera
el contexto estructurado para cada llamada al LLM.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Ubicacion:
    """Representa una ubicación en el mundo."""
    id: str
    nombre: str
    descripcion: str
    tipo: str = "exterior"  # exterior, interior, dungeon, ciudad
    conexiones: List[str] = field(default_factory=list)


@dataclass
class NPC:
    """Representa un NPC activo en la escena."""
    id: str
    nombre: str
    descripcion: str
    actitud: str = "neutral"  # hostil, neutral, amistoso
    hp: Optional[int] = None
    hp_max: Optional[int] = None
    ca: Optional[int] = None
    es_enemigo: bool = False
    datos_extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntradaHistorial:
    """Una entrada en el historial de la aventura."""
    turno: int
    tipo: str  # accion_jugador, respuesta_dm, resultado_mecanico, evento
    contenido: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class GestorContexto:
    """
    Gestiona todo el contexto de la aventura para el LLM.
    """
    
    def __init__(self):
        self.pj: Optional[Dict[str, Any]] = None
        self.ubicacion: Optional[Ubicacion] = None
        self.npcs_activos: List[NPC] = []
        self.historial: List[EntradaHistorial] = []
        self.turno: int = 0
        self.modo_juego: str = "exploracion"  # exploracion, social, combate
        self.estado_combate: Optional[Dict[str, Any]] = None
        self.flags: Dict[str, Any] = {}  # Flags de la aventura (misiones, eventos, etc.)
        self.notas_dm: str = ""  # Notas para el DM sobre la situación actual
    
    def cargar_pj(self, pj: Dict[str, Any]) -> None:
        """Carga el personaje jugador."""
        self.pj = pj
    
    def establecer_ubicacion(self, id: str, nombre: str, descripcion: str, 
                             tipo: str = "exterior") -> None:
        """Establece la ubicación actual."""
        self.ubicacion = Ubicacion(
            id=id,
            nombre=nombre,
            descripcion=descripcion,
            tipo=tipo
        )
    
    def añadir_npc(self, id: str, nombre: str, descripcion: str,
                   actitud: str = "neutral", es_enemigo: bool = False,
                   hp: int = None, ca: int = None) -> NPC:
        """Añade un NPC a la escena actual."""
        npc = NPC(
            id=id,
            nombre=nombre,
            descripcion=descripcion,
            actitud=actitud,
            es_enemigo=es_enemigo,
            hp=hp,
            hp_max=hp,
            ca=ca
        )
        self.npcs_activos.append(npc)
        return npc
    
    def quitar_npc(self, id: str) -> bool:
        """Quita un NPC de la escena."""
        for i, npc in enumerate(self.npcs_activos):
            if npc.id == id:
                self.npcs_activos.pop(i)
                return True
        return False
    
    def obtener_npc(self, id: str) -> Optional[NPC]:
        """Obtiene un NPC por ID."""
        for npc in self.npcs_activos:
            if npc.id == id:
                return npc
        return None
    
    def registrar_historial(self, tipo: str, contenido: str) -> None:
        """Añade una entrada al historial."""
        entrada = EntradaHistorial(
            turno=self.turno,
            tipo=tipo,
            contenido=contenido
        )
        self.historial.append(entrada)
    
    def avanzar_turno(self) -> None:
        """Avanza el contador de turnos."""
        self.turno += 1
    
    def cambiar_modo(self, nuevo_modo: str) -> None:
        """Cambia el modo de juego."""
        if nuevo_modo in ("exploracion", "social", "combate"):
            self.modo_juego = nuevo_modo
    
    def generar_contexto_llm(self) -> str:
        """
        Genera el contexto completo para el prompt del LLM.
        """
        partes = []
        
        # Información del PJ
        if self.pj:
            info = self.pj.get("info_basica", {})
            derivados = self.pj.get("derivados", {})
            partes.append("=== PERSONAJE JUGADOR ===")
            partes.append(f"Nombre: {info.get('nombre', 'Aventurero')}")
            partes.append(f"Raza: {info.get('raza', 'Desconocida')}")
            partes.append(f"Clase: {info.get('clase', 'Desconocida')} Nivel {info.get('nivel', 1)}")
            partes.append(f"HP: {derivados.get('puntos_golpe_actual', '?')}/{derivados.get('puntos_golpe_maximo', '?')}")
            partes.append(f"CA: {derivados.get('clase_armadura', 10)}")
            
            # Habilidades competentes
            habilidades = self.pj.get("competencias", {}).get("habilidades", [])
            if habilidades:
                partes.append(f"Competencias: {', '.join(habilidades)}")
            partes.append("")
        
        # Ubicación
        if self.ubicacion:
            partes.append("=== UBICACIÓN ACTUAL ===")
            partes.append(f"Lugar: {self.ubicacion.nombre}")
            partes.append(f"Tipo: {self.ubicacion.tipo}")
            partes.append(f"Descripción: {self.ubicacion.descripcion}")
            partes.append("")
        
        # NPCs en escena
        if self.npcs_activos:
            partes.append("=== NPCs EN ESCENA ===")
            for npc in self.npcs_activos:
                estado_hp = ""
                if npc.hp is not None:
                    estado_hp = f" [HP: {npc.hp}/{npc.hp_max}]"
                partes.append(f"- {npc.nombre} ({npc.actitud}){estado_hp}")
                partes.append(f"  {npc.descripcion}")
            partes.append("")
        
        # Modo de juego
        partes.append(f"=== MODO ACTUAL: {self.modo_juego.upper()} ===")
        if self.modo_juego == "combate" and self.estado_combate:
            partes.append(f"Ronda: {self.estado_combate.get('ronda', 1)}")
            partes.append(f"Turno de: {self.estado_combate.get('turno_actual', 'PJ')}")
        partes.append("")
        
        # Historial reciente (últimas 10 entradas)
        if self.historial:
            partes.append("=== HISTORIAL RECIENTE ===")
            for entrada in self.historial[-10:]:
                partes.append(f"[{entrada.tipo}] {entrada.contenido}")
            partes.append("")
        
        # Notas del DM
        if self.notas_dm:
            partes.append("=== NOTAS DEL DM ===")
            partes.append(self.notas_dm)
            partes.append("")
        
        return "\n".join(partes)
    
    def generar_diccionario_contexto(self) -> Dict[str, Any]:
        """Genera el contexto como diccionario para las herramientas."""
        return {
            "pj": self.pj,
            "ubicacion": self.ubicacion.__dict__ if self.ubicacion else None,
            "npcs": [npc.__dict__ for npc in self.npcs_activos],
            "modo": self.modo_juego,
            "turno": self.turno,
            "combate": self.estado_combate,
            "flags": self.flags
        }
    
    def serializar(self) -> Dict[str, Any]:
        """Serializa el contexto para guardado."""
        return {
            "turno": self.turno,
            "modo_juego": self.modo_juego,
            "ubicacion": self.ubicacion.__dict__ if self.ubicacion else None,
            "npcs_activos": [npc.__dict__ for npc in self.npcs_activos],
            "historial": [
                {"turno": e.turno, "tipo": e.tipo, "contenido": e.contenido, "timestamp": e.timestamp}
                for e in self.historial
            ],
            "estado_combate": self.estado_combate,
            "flags": self.flags,
            "notas_dm": self.notas_dm
        }
    
    def deserializar(self, datos: Dict[str, Any]) -> None:
        """Restaura el contexto desde datos guardados."""
        self.turno = datos.get("turno", 0)
        self.modo_juego = datos.get("modo_juego", "exploracion")
        
        if datos.get("ubicacion"):
            u = datos["ubicacion"]
            self.ubicacion = Ubicacion(**u)
        
        self.npcs_activos = []
        for npc_data in datos.get("npcs_activos", []):
            # Filtrar campos que no son del dataclass
            campos_validos = {k: v for k, v in npc_data.items() 
                           if k in NPC.__dataclass_fields__}
            self.npcs_activos.append(NPC(**campos_validos))
        
        self.historial = []
        for h in datos.get("historial", []):
            self.historial.append(EntradaHistorial(
                turno=h["turno"],
                tipo=h["tipo"],
                contenido=h["contenido"],
                timestamp=h.get("timestamp", "")
            ))
        
        self.estado_combate = datos.get("estado_combate")
        self.flags = datos.get("flags", {})
        self.notas_dm = datos.get("notas_dm", "")
