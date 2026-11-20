from random import Random

import pytest

from grid_rpg_ai.data.maps import create_map_from_grid
from grid_rpg_ai.gamestate import GameState
from grid_rpg_ai.rules import intended_destination, normalize_direction, resolve_move


class FirstChoiceRandom(Random):
    def random(self):
        return 0.0

    def choice(self, sequence):
        return sequence[0]


class LastChoiceRandom(FirstChoiceRandom):
    def choice(self, sequence):
        return sequence[-1]


def make_state_and_map():
    game_map = create_map_from_grid(
        name="rules_test_map",
        grid=[
            ["plains", "road", "lake"],
            ["forest", "plains", "road"],
        ],
        start=(0, 0),
        goal=(2, 1),
    )
    state = GameState(
        rows=game_map.height,
        cols=game_map.width,
        player_pos=game_map.start,
        goal_pos=game_map.goal,
    )
    return state, game_map


@pytest.mark.parametrize(
    ("direction", "expected"),
    [("up", "up"), ("North", "up"), ("w", "up"), ("right", "right")],
)
def test_normalize_direction_accepts_commands_and_cardinal_names(direction, expected):
    assert normalize_direction(direction) == expected


def test_intended_destination_uses_xy_coordinates():
    assert intended_destination((2, 1), "left") == ("left", (1, 1))


def test_resolve_move_allows_walkable_destination_without_mutating_state():
    state, game_map = make_state_and_map()

    result = resolve_move(state, game_map, "right")

    assert result.success is True
    assert result.attempted_pos == (1, 0)
    assert result.final_pos == (1, 0)
    assert state.player_pos == (0, 0)
    assert state.turn == 0


def test_resolve_move_blocks_map_boundary_and_spends_attempted_turn():
    state, game_map = make_state_and_map()

    result = resolve_move(state, game_map, "left")
    state.apply_move_result(result)

    assert result.success is False
    assert result.event_type == "out_of_bounds"
    assert result.attempted_pos == (-1, 0)
    assert state.player_pos == (0, 0)
    assert state.turn == 1


def test_resolve_move_blocks_non_walkable_biome():
    state, game_map = make_state_and_map()
    state.player_pos = (1, 0)

    result = resolve_move(state, game_map, "right")
    state.apply_move_result(result)

    assert result.success is False
    assert result.event_type == "blocked_terrain"
    assert result.attempted_pos == (2, 0)
    assert state.player_pos == (1, 0)
    assert state.turn == 1


def test_resolve_move_rejects_unknown_direction():
    state, game_map = make_state_and_map()

    with pytest.raises(ValueError, match="Unknown movement direction"):
        resolve_move(state, game_map, "diagonal")


def test_resolve_move_rejects_state_map_dimension_mismatch():
    state, game_map = make_state_and_map()
    state.cols = 2

    with pytest.raises(ValueError, match="dimensions"):
        resolve_move(state, game_map, "right")


def test_discovery_grid_uses_xy_indices_and_rectangular_dimensions():
    state = GameState(
        rows=2,
        cols=3,
        player_pos=(2, 1),
        goal_pos=(0, 0),
    )

    assert state.discovered == [[False, False, False], [False, False, True]]


def test_invalid_discovery_grid_dimensions_are_rejected():
    with pytest.raises(ValueError, match="Discovery grid dimensions"):
        GameState(
            rows=2,
            cols=3,
            player_pos=(0, 0),
            goal_pos=(1, 1),
            discovered=[[False, False]],
        )


def test_block_move_event_cancels_valid_movement():
    state, game_map = make_state_and_map()

    result = resolve_move(
        state,
        game_map,
        "down",
        rng=FirstChoiceRandom(),
        event_chance=1,
    )

    assert result.success is False
    assert result.event_id == "forest_wolves"
    assert result.attempted_pos == (0, 1)
    assert result.final_pos == (0, 0)


def test_hint_event_records_clue_in_state():
    state, game_map = make_state_and_map()

    result = resolve_move(
        state,
        game_map,
        "right",
        rng=FirstChoiceRandom(),
        event_chance=1,
    )
    state.apply_move_result(result)

    assert result.event_id == "road_signpost"
    assert result.success is True
    assert state.status["clue_road_signpost"] is True
    assert "following the road is often safer" in state.log[-1]


def test_give_clue_event_records_reward_hint_as_status():
    state, game_map = make_state_and_map()

    result = resolve_move(
        state,
        game_map,
        "right",
        rng=LastChoiceRandom(),
        event_chance=1,
    )

    assert result.event_id == "road_traveler"
    assert result.status_updates == {"clue_road_traveler": True}
    assert result.event_text.endswith(
        "The road connects the quieter edges of the wilderness better than the rough ground does."
    )


def test_flavor_event_preserves_intended_destination():
    game_map = create_map_from_grid(
        name="flavor_test_map",
        grid=[["plains", "plains"]],
        start=(0, 0),
        goal=(1, 0),
    )
    state = GameState(1, 2, game_map.start, game_map.goal)

    result = resolve_move(
        state,
        game_map,
        "right",
        rng=FirstChoiceRandom(),
        event_chance=1,
    )

    assert result.event_id == "plains_wind"
    assert result.success is True
    assert result.final_pos == (1, 0)
    assert result.status_updates is None


def test_detour_event_moves_to_walkable_adjacent_tile():
    game_map = create_map_from_grid(
        name="detour_test_map",
        grid=[
            ["plains", "desert", "desert"],
            ["plains", "road", "plains"],
        ],
        start=(0, 0),
        goal=(2, 1),
    )
    state = GameState(2, 3, game_map.start, game_map.goal)

    result = resolve_move(
        state,
        game_map,
        "right",
        rng=FirstChoiceRandom(),
        event_chance=1,
    )

    assert result.event_id == "desert_sandstorm"
    assert result.success is True
    assert result.final_pos == (2, 0)
    assert game_map.biome_at(*result.final_pos).walkable


def test_events_can_be_disabled_for_deterministic_movement():
    state, game_map = make_state_and_map()

    result = resolve_move(state, game_map, "right", event_chance=0)

    assert result.event_id is None
    assert result.final_pos == (1, 0)


def test_resolve_move_rejects_invalid_event_chance():
    state, game_map = make_state_and_map()

    with pytest.raises(ValueError, match="event_chance"):
        resolve_move(state, game_map, "right", event_chance=1.1)
