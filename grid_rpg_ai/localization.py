from __future__ import annotations

from typing import Literal

Language = Literal["en", "es"]
SUPPORTED_LANGUAGES: tuple[Language, ...] = ("en", "es")
LANGUAGE_LABELS: dict[Language, str] = {"en": "English", "es": "Español"}

UI_TEXT: dict[str, dict[Language, str]] = {
    "language": {"en": "Language", "es": "Idioma"},
    "title": {"en": "Grid RPG Engine Sandbox", "es": "Sandbox del motor Grid RPG"},
    "caption": {
        "en": "Playable movement, biome events, discovery, and fog-of-war loop.",
        "es": "Movimiento, eventos de bioma, descubrimiento y niebla de guerra.",
    },
    "move": {"en": "Move", "es": "Moverse"},
    "settings": {"en": "Settings", "es": "Configuración"},
    "vision_radius": {"en": "Vision radius", "es": "Radio de visión"},
    "map_zoom": {"en": "Map zoom", "es": "Zoom del mapa"},
    "enable_fog": {"en": "Enable fog of war", "es": "Activar niebla de guerra"},
    "enable_events": {"en": "Enable biome events", "es": "Activar eventos de bioma"},
    "tile_style": {"en": "Tile style", "es": "Estilo de casillas"},
    "colors": {"en": "Colors", "es": "Colores"},
    "images": {"en": "Images", "es": "Imágenes"},
    "narration": {"en": "Narration", "es": "Narración"},
    "above_map": {"en": "Above map", "es": "Sobre el mapa"},
    "right_side": {"en": "Right side", "es": "A la derecha"},
    "reset_game": {"en": "Reset game", "es": "Reiniciar partida"},
    "narration_placeholder": {
        "en": "The adventure narration will appear here.",
        "es": "La narración de la aventura aparecerá aquí.",
    },
    "narration_label": {"en": "Narration", "es": "Narración"},
    "position": {"en": "Position", "es": "Posición"},
    "biome": {"en": "Biome", "es": "Bioma"},
    "turn": {"en": "Turn", "es": "Turno"},
    "recent_turns": {"en": "Recent turns", "es": "Turnos recientes"},
    "inventory": {"en": "Inventory", "es": "Inventario"},
    "known_clues": {"en": "Known clues", "es": "Pistas conocidas"},
    "victory": {
        "en": "You reached the objective in {turn} turns!",
        "es": "¡Has alcanzado el objetivo en {turn} turnos!",
    },
    "move_up": {"en": "Move up", "es": "Mover arriba"},
    "move_down": {"en": "Move down", "es": "Mover abajo"},
    "move_left": {"en": "Move left", "es": "Mover a la izquierda"},
    "move_right": {"en": "Move right", "es": "Mover a la derecha"},
    "moved": {
        "en": "Moved {direction} to {position}.",
        "es": "Te has movido {direction} hasta {position}.",
    },
    "stayed": {
        "en": "Tried to move {direction}, but remained at {position}.",
        "es": "Intentaste moverte {direction}, pero permaneciste en {position}.",
    },
    "out_of_bounds": {
        "en": "You cannot leave the map.",
        "es": "No puedes salir del mapa.",
    },
    "blocked_terrain": {
        "en": "That terrain blocks movement.",
        "es": "Ese terreno bloquea el movimiento.",
    },
}

BIOME_NAMES: dict[str, dict[Language, str]] = {
    "plains": {"en": "Plains", "es": "Llanuras"},
    "forest": {"en": "Forest", "es": "Bosque"},
    "swamp": {"en": "Swamp", "es": "Pantano"},
    "desert": {"en": "Desert", "es": "Desierto"},
    "hill": {"en": "Hill", "es": "Colina"},
    "road": {"en": "Road", "es": "Camino"},
    "ruins": {"en": "Ruins", "es": "Ruinas"},
    "lake": {"en": "Lake", "es": "Lago"},
    "mountain": {"en": "Mountain", "es": "Montaña"},
}

EVENT_TEXT: dict[str, dict[Language, tuple[str, str | None]]] = {
    "plains_wind": {
        "en": ("The grass bends in waves, and for a moment the open land feels almost watchful.", None),
        "es": ("La hierba se mece en ondas y, por un momento, la llanura parece estar observando.", None),
    },
    "plains_tracks": {
        "en": ("A set of recent footprints crosses the plain toward a safer route.", "Someone passed through here recently; routes with clearer ground may lead onward."),
        "es": ("Unas huellas recientes cruzan la llanura hacia una ruta más segura.", "Alguien pasó por aquí hace poco; los caminos despejados podrían conducir hacia adelante."),
    },
    "forest_wolves": {
        "en": ("Low growls ripple through the undergrowth and force a retreat from the deeper path.", None),
        "es": ("Gruñidos bajos recorren la maleza y te obligan a retroceder del sendero más profundo.", None),
    },
    "forest_tracks": {
        "en": ("Snapped twigs and scraped bark suggest that something important passed through not long ago.", "The disturbed trail hints that the objective lies beyond the denser woods."),
        "es": ("Las ramas rotas y la corteza arañada sugieren que algo importante pasó por aquí hace poco.", "El sendero alterado indica que el objetivo está más allá del bosque espeso."),
    },
    "forest_clearing": {
        "en": ("A pocket of silence opens between the trees, offering a rare calm moment.", None),
        "es": ("Un remanso de silencio se abre entre los árboles y ofrece un raro momento de calma.", None),
    },
    "swamp_mud": {
        "en": ("The ground gives way underfoot and refuses a clean step forward.", None),
        "es": ("El suelo cede bajo tus pies y no permite avanzar con firmeza.", None),
    },
    "swamp_lights": {
        "en": ("Pale lights drift over the water and vanish when stared at directly.", None),
        "es": ("Luces pálidas flotan sobre el agua y desaparecen cuando las miras directamente.", None),
    },
    "desert_sandstorm": {
        "en": ("A sudden wall of sand throws off the route and shoves the traveler aside.", None),
        "es": ("Una pared repentina de arena desvía la ruta y te empuja a un lado.", None),
    },
    "desert_marker": {
        "en": ("A weathered stone marker emerges from the sand with a faint directional carving.", "The worn symbol suggests the destination lies along the more stable approach."),
        "es": ("Un mojón de piedra desgastado emerge de la arena con un tenue grabado direccional.", "El símbolo desgastado sugiere que el destino está por el acceso más estable."),
    },
    "hill_vantage": {
        "en": ("From higher ground, distant shapes align more clearly than before.", "From here, the objective feels easier to place relative to the surrounding land."),
        "es": ("Desde las alturas, las formas lejanas se alinean con más claridad que antes.", "Desde aquí, resulta más fácil situar el objetivo respecto al terreno circundante."),
    },
    "hill_loose_stone": {
        "en": ("Pebbles slide underfoot, but the path remains passable.", None),
        "es": ("Las piedras sueltas resbalan bajo tus pies, pero el camino sigue siendo transitable.", None),
    },
    "road_signpost": {
        "en": ("A cracked sign leans beside the road, still useful despite age and moss.", "Travelers once marked this route for a reason; following the road is often safer."),
        "es": ("Un cartel agrietado se inclina junto al camino, aún útil pese a la edad y el musgo.", "Los viajeros marcaron esta ruta por una razón; seguir el camino suele ser más seguro."),
    },
    "road_traveler": {
        "en": ("A hurried traveler shares a fragment of useful guidance before moving on.", "The road connects the quieter edges of the wilderness better than the rough ground does."),
        "es": ("Un viajero apresurado comparte un consejo útil antes de continuar.", "El camino conecta mejor los márgenes tranquilos de la naturaleza que el terreno accidentado."),
    },
    "ruins_inscription": {
        "en": ("Faded markings on broken stone preserve a hint from an older age.", "The ruins point toward a destination once important to those who built them."),
        "es": ("Las marcas desvaídas de la piedra rota conservan una pista de tiempos antiguos.", "Las ruinas apuntan hacia un destino que fue importante para quienes las construyeron."),
    },
    "ruins_collapse": {
        "en": ("Loose stone crashes down and cuts off the intended step.", None),
        "es": ("Una piedra suelta cae y bloquea el paso que pretendías dar.", None),
    },
}


def normalize_language(language: str) -> Language:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language!r}")
    return language


def text(key: str, language: Language, **values: object) -> str:
    language = normalize_language(language)
    try:
        template = UI_TEXT[key][language]
    except KeyError as exc:
        raise KeyError(f"Unknown localization key: {key!r}") from exc
    return template.format(**values)


def biome_name(biome: str, language: Language) -> str:
    language = normalize_language(language)
    return BIOME_NAMES[biome][language]


def event_text(event_id: str, language: Language) -> tuple[str, str | None]:
    language = normalize_language(language)
    return EVENT_TEXT[event_id][language]
