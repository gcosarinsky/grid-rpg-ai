from __future__ import annotations

from random import Random
from typing import Dict, Optional, Tuple

from .data.dataevents import Event, choose_event_for_biome
from .data.maps import MapData, in_bounds, is_walkable, neighbors
from .gamestate import GameState, MoveResult, Position

DirectionDelta = Tuple[int, int]
DEFAULT_EVENT_CHANCE = 0.35

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


def resolve_event(
    state: GameState,
    game_map: MapData,
    direction: str,
    attempted_pos: Position,
    event: Event,
    rng: Optional[Random] = None,
) -> MoveResult:
    """Resolve one catalog event into a bounded mechanical move result."""
    final_pos = attempted_pos
    success = True
    event_text = event.description
    status_updates = None

    if event.effect == "block_move":
        final_pos = state.player_pos
        success = False
    elif event.effect == "push_random_adjacent":
        destinations = [
            destination
            for destination in neighbors(game_map, *attempted_pos)
            if is_walkable(game_map, *destination)
        ]
        if destinations:
            random_source = rng if rng is not None else Random()
            final_pos = random_source.choice(destinations)
    elif event.effect in {"reveal_hint", "give_clue"}:
        status_updates = {f"clue_{event.event_id}": True}
        event_text = f"{event.description} {event.clue_text}".strip()
    elif event.effect != "none":
        raise ValueError(f"Unsupported event effect: {event.effect!r}")

    return MoveResult(
        intended_direction=direction,
        attempted_pos=attempted_pos,
        final_pos=final_pos,
        success=success,
        event_type=event.event_type,
        event_id=event.event_id,
        event_text=event_text,
        status_updates=status_updates,
    )


def resolve_move(
    state: GameState,
    game_map: MapData,
    direction: str,
    rng: Optional[Random] = None,
    event_chance: float = DEFAULT_EVENT_CHANCE,
) -> MoveResult:
    """Resolve movement and, on a valid move, an optional biome event.

    This function only returns the mechanical result. Call
    :meth:`GameState.apply_move_result` to commit it to the session state.
    All resolved attempts consume one turn, whether movement succeeds or not.
    """
    if state.rows != game_map.height or state.cols != game_map.width:
        raise ValueError("GameState dimensions do not match the map")
    if not 0 <= event_chance <= 1:
        raise ValueError("event_chance must be between 0 and 1")

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

    random_source = rng if rng is not None else Random()
    destination_biome = game_map.tile_at(*attempted_pos)
    if event_chance > 0 and random_source.random() < event_chance:
        event = choose_event_for_biome(destination_biome, random_source)
        if event is not None:
            return resolve_event(
                state,
                game_map,
                normalized,
                attempted_pos,
                event,
                random_source,
            )

    return MoveResult(
        intended_direction=normalized,
        attempted_pos=attempted_pos,
        final_pos=attempted_pos,
        success=True,
    )
