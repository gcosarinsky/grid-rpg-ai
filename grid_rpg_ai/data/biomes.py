from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable


@dataclass(frozen=True)
class Biome:
    key: str
    display_name: str
    walkable: bool
    color: str
    symbol: str
    description: str
    movement_cost: int = 1
    danger_level: int = 1
    can_host_goal: bool = True


BIOMES: Dict[str, Biome] = {
    "plains": Biome(
        key="plains",
        display_name="Plains",
        walkable=True,
        color="#8BC34A",
        symbol="P",
        description="Open grassland with good visibility and few obstacles.",
        movement_cost=1,
        danger_level=1,
    ),
    "forest": Biome(
        key="forest",
        display_name="Forest",
        walkable=True,
        color="#2E7D32",
        symbol="F",
        description="Dense woodland with low visibility, tracks, and hidden threats.",
        movement_cost=1,
        danger_level=3,
    ),
    "swamp": Biome(
        key="swamp",
        display_name="Swamp",
        walkable=True,
        color="#4E6E58",
        symbol="S",
        description="Wet, unstable ground where movement feels heavy and strange.",
        movement_cost=2,
        danger_level=4,
    ),
    "desert": Biome(
        key="desert",
        display_name="Desert",
        walkable=True,
        color="#D9A441",
        symbol="D",
        description="Dry and exposed terrain shaped by heat, wind, and drifting sand.",
        movement_cost=1,
        danger_level=3,
    ),
    "hill": Biome(
        key="hill",
        display_name="Hill",
        walkable=True,
        color="#9E9D24",
        symbol="H",
        description="Raised ground with wider views and winding paths.",
        movement_cost=1,
        danger_level=2,
    ),
    "road": Biome(
        key="road",
        display_name="Road",
        walkable=True,
        color="#8D6E63",
        symbol="R",
        description="A safer route where signs, travelers, and clues are more common.",
        movement_cost=1,
        danger_level=1,
    ),
    "ruins": Biome(
        key="ruins",
        display_name="Ruins",
        walkable=True,
        color="#78909C",
        symbol="U",
        description="Broken stone, old structures, and remnants of a lost place.",
        movement_cost=1,
        danger_level=3,
    ),
    "lake": Biome(
        key="lake",
        display_name="Lake",
        walkable=False,
        color="#42A5F5",
        symbol="L",
        description="Deep water that blocks normal movement.",
        movement_cost=99,
        danger_level=0,
        can_host_goal=False,
    ),
    "mountain": Biome(
        key="mountain",
        display_name="Mountain",
        walkable=False,
        color="#757575",
        symbol="M",
        description="Steep stone and cliffs that cannot be crossed in the MVP.",
        movement_cost=99,
        danger_level=0,
        can_host_goal=False,
    ),
}


VALID_BIOME_KEYS = tuple(BIOMES.keys())


def get_biome(key: str) -> Biome:
    try:
        return BIOMES[key]
    except KeyError as exc:
        raise ValueError(f"Unknown biome: {key!r}") from exc


def is_valid_biome(key: str) -> bool:
    return key in BIOMES


def walkable_biomes() -> Iterable[str]:
    return (key for key, biome in BIOMES.items() if biome.walkable)
