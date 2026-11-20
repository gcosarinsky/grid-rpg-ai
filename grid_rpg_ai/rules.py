from __future__ import annotations

from typing import Dict, Tuple

from .data.maps import MapData, in_bounds, is_walkable
from .gamestate import GameState, MoveResult, Position

DirectionDelta = Tuple[int, int]

DIRECTION_DELTAS: Dict[str, DirectionDelta] = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}
DIRECTION_ALIASES = {
    "north": "up",
    "south": "down",
    "west": "left",
    "east": "right",
    "w": "up",
    "s": "down",
    "a": "left",
    "d": "right",
}


def normalize_direction(direction: str) -> str:
    """Return a canonical movement direction or reject invalid input."""
    if not isinstance(direction, str):
        raise TypeError("Movement direction must be a string")

    normalized = direction.strip().lower()
    normalized = DIRECTION_ALIASES.get(normalized, normalized)
    if normalized not in DIRECTION_DELTAS:
        raise ValueError(f"Unknown movement direction: {direction!r}")
    return normalized


def intended_destination(position: Position, direction: str) -> Tuple[str, Position]:
    """Calculate an intended ``(x, y)`` destination without mutating state."""
    normalized = normalize_direction(direction)
    dx, dy = DIRECTION_DELTAS[normalized]
    return normalized, (position[0] + dx, position[1] + dy)


def resolve_move(state: GameState, game_map: MapData, direction: str) -> MoveResult:
    """Resolve movement against map bounds and biome walkability.

    This function only returns the mechanical result. Call
    :meth:`GameState.apply_move_result` to commit it to the session state.
    Valid attempts, including blocked attempts, consume one turn.
    """
    if state.rows != game_map.height or state.cols != game_map.width:
        raise ValueError("GameState dimensions do not match the map")

    normalized, attempted_pos = intended_destination(state.player_pos, direction)
    final_pos = state.player_pos

    if not in_bounds(game_map, *attempted_pos):
        return MoveResult(
            intended_direction=normalized,
            attempted_pos=attempted_pos,
            final_pos=final_pos,
            success=False,
            event_type="out_of_bounds",
            event_text="You cannot leave the map.",
        )

    if not is_walkable(game_map, *attempted_pos):
        return MoveResult(
            intended_direction=normalized,
            attempted_pos=attempted_pos,
            final_pos=final_pos,
            success=False,
            event_type="blocked_terrain",
            event_text="That terrain blocks movement.",
        )

    return MoveResult(
        intended_direction=normalized,
        attempted_pos=attempted_pos,
        final_pos=attempted_pos,
        success=True,
    )
