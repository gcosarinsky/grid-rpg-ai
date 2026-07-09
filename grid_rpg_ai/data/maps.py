from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .biomes import BIOMES, get_biome, is_valid_biome

Coord = Tuple[int, int]
Grid = List[List[str]]


@dataclass(frozen=True)
class MapData:
    name: str
    width: int
    height: int
    grid: Grid
    start: Coord
    goal: Coord
    description: str = ""

    def tile_at(self, x: int, y: int) -> str:
        if not in_bounds(self, x, y):
            raise IndexError(f"Coordinates out of bounds: {(x, y)}")
        return self.grid[y][x]

    def biome_at(self, x: int, y: int):
        return get_biome(self.tile_at(x, y))


DEFAULT_MAP_GRID: Grid = [
    ["plains", "plains", "plains", "forest", "forest", "forest", "hill", "hill", "mountain", "mountain"],
    ["plains", "plains", "forest", "forest", "forest", "forest", "hill", "hill", "mountain", "mountain"],
    ["plains", "swamp", "swamp", "forest", "forest", "ruins", "hill", "road", "road", "mountain"],
    ["plains", "swamp", "swamp", "forest", "ruins", "ruins", "road", "road", "lake", "lake"],
    ["desert", "desert", "swamp", "forest", "ruins", "road", "road", "lake", "lake", "lake"],
    ["desert", "desert", "desert", "road", "road", "road", "road", "lake", "hill", "hill"],
    ["desert", "desert", "road", "road", "plains", "plains", "road", "hill", "hill", "hill"],
    ["desert", "road", "road", "plains", "plains", "plains", "road", "hill", "mountain", "mountain"],
    ["road", "road", "plains", "plains", "plains", "plains", "road", "hill", "mountain", "mountain"],
    ["road", "plains", "plains", "plains", "plains", "road", "road", "hill", "mountain", "mountain"],
]


def in_bounds(map_data: MapData, x: int, y: int) -> bool:
    return 0 <= x < map_data.width and 0 <= y < map_data.height


def is_walkable(map_data: MapData, x: int, y: int) -> bool:
    if not in_bounds(map_data, x, y):
        return False
    return map_data.biome_at(x, y).walkable


def neighbors(map_data: MapData, x: int, y: int) -> List[Coord]:
    candidates = [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]
    return [coord for coord in candidates if in_bounds(map_data, *coord)]


def validate_grid(grid: Grid) -> None:
    if not grid or not grid[0]:
        raise ValueError("Grid cannot be empty")

    expected_width = len(grid[0])
    for row_index, row in enumerate(grid):
        if len(row) != expected_width:
            raise ValueError(
                f"Grid row {row_index} has width {len(row)} but expected {expected_width}"
            )
        for col_index, biome_key in enumerate(row):
            if not is_valid_biome(biome_key):
                raise ValueError(
                    f"Invalid biome {biome_key!r} at {(col_index, row_index)}"
                )


def validate_map(map_data: MapData) -> None:
    validate_grid(map_data.grid)

    if map_data.width != len(map_data.grid[0]) or map_data.height != len(map_data.grid):
        raise ValueError("Map width/height do not match grid dimensions")

    if not in_bounds(map_data, *map_data.start):
        raise ValueError(f"Start out of bounds: {map_data.start}")

    if not in_bounds(map_data, *map_data.goal):
        raise ValueError(f"Goal out of bounds: {map_data.goal}")

    if not is_walkable(map_data, *map_data.start):
        raise ValueError("Start must be on a walkable biome")

    goal_biome = map_data.biome_at(*map_data.goal)
    if not goal_biome.walkable or not goal_biome.can_host_goal:
        raise ValueError("Goal must be on a valid walkable biome")


def create_default_map() -> MapData:
    map_data = MapData(
        name="starter_map",
        width=10,
        height=10,
        grid=DEFAULT_MAP_GRID,
        start=(0, 0),
        goal=(6, 9),
        description="A broader starter region with connected roads, a central forest, ruins, water blockers, and mountain edges.",
    )
    validate_map(map_data)
    return map_data


def create_map_from_grid(
    name: str,
    grid: Grid,
    start: Coord,
    goal: Coord,
    description: str = "",
) -> MapData:
    validate_grid(grid)
    map_data = MapData(
        name=name,
        width=len(grid[0]),
        height=len(grid),
        grid=grid,
        start=start,
        goal=goal,
        description=description,
    )
    validate_map(map_data)
    return map_data


PRESET_MAPS: Dict[str, MapData] = {
    "starter_map": create_default_map(),
}


def get_map(name: str = "starter_map") -> MapData:
    try:
        return PRESET_MAPS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown map preset: {name!r}") from exc


def tile_summary(map_data: MapData, x: int, y: int) -> Dict[str, object]:
    biome = map_data.biome_at(x, y)
    return {
        "x": x,
        "y": y,
        "biome": biome.key,
        "biome_name": biome.display_name,
        "walkable": biome.walkable,
        "symbol": biome.symbol,
        "color": biome.color,
        "is_goal": (x, y) == map_data.goal,
        "is_start": (x, y) == map_data.start,
    }


def find_tiles_by_biome(map_data: MapData, biome_key: str) -> List[Coord]:
    if biome_key not in BIOMES:
        raise ValueError(f"Unknown biome: {biome_key!r}")

    matches: List[Coord] = []
    for y, row in enumerate(map_data.grid):
        for x, value in enumerate(row):
            if value == biome_key:
                matches.append((x, y))
    return matches

def render_symbol_grid(
    map_data: MapData,
    show_axes: bool = True,
    player_pos: Optional[Coord] = None,
    goal_pos: Optional[Coord] = None,
) -> str:
    goal_pos = goal_pos if goal_pos is not None else map_data.goal
    lines: List[str] = []

    if show_axes:
        header = "    " + " ".join(str(x) for x in range(map_data.width))
        lines.append(header)

    for y, row in enumerate(map_data.grid):
        symbols: List[str] = []
        for x, biome_key in enumerate(row):
            if player_pos == (x, y):
                symbol = "@"
            elif goal_pos == (x, y):
                symbol = "G"
            else:
                symbol = get_biome(biome_key).symbol
            symbols.append(symbol)

        body = " ".join(symbols)
        if show_axes:
            lines.append(f"{y:>2}  {body}")
        else:
            lines.append(body)

    return "\n".join(lines)

ANSI_RESET = "\033[0m"
ANSI_PLAYER = "\033[97;41m"
ANSI_GOAL = "\033[30;43m"
ANSI_BIOME_COLORS: Dict[str, str] = {
    "plains": "\033[92m",
    "forest": "\033[32m",
    "swamp": "\033[36m",
    "desert": "\033[33m",
    "hill": "\033[93m",
    "road": "\033[37m",
    "ruins": "\033[90m",
    "lake": "\033[94m",
    "mountain": "\033[95m",
}


def render_colored_symbol_grid(
    map_data: MapData,
    show_axes: bool = True,
    player_pos: Optional[Coord] = None,
    goal_pos: Optional[Coord] = None,
) -> str:
    goal_pos = goal_pos if goal_pos is not None else map_data.goal
    lines: List[str] = []

    if show_axes:
        header = "    " + " ".join(str(x) for x in range(map_data.width))
        lines.append(header)

    for y, row in enumerate(map_data.grid):
        symbols: List[str] = []
        for x, biome_key in enumerate(row):
            if player_pos == (x, y):
                painted = f"{ANSI_PLAYER}@{ANSI_RESET}"
            elif goal_pos == (x, y):
                painted = f"{ANSI_GOAL}G{ANSI_RESET}"
            else:
                symbol = get_biome(biome_key).symbol
                color = ANSI_BIOME_COLORS.get(biome_key, "")
                painted = f"{color}{symbol}{ANSI_RESET}" if color else symbol
            symbols.append(painted)

        body = " ".join(symbols)
        if show_axes:
            lines.append(f"{y:>2}  {body}")
        else:
            lines.append(body)

    return "\n".join(lines)


def optional_goal_hint(map_data: MapData, position: Coord) -> Optional[str]:
    px, py = position
    gx, gy = map_data.goal
    dx = gx - px
    dy = gy - py

    if (dx, dy) == (0, 0):
        return "The goal is here."

    horizontal = "east" if dx > 0 else "west" if dx < 0 else ""
    vertical = "south" if dy > 0 else "north" if dy < 0 else ""
    direction = " and ".join(part for part in (vertical, horizontal) if part)
    return f"You sense the objective lies to the {direction}."
