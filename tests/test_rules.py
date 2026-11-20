import pytest

from grid_rpg_ai.data.maps import create_map_from_grid
from grid_rpg_ai.gamestate import GameState
from grid_rpg_ai.rules import intended_destination, normalize_direction, resolve_move


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
