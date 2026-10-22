from PIL import Image
import pytest

from grid_rpg_ai.data.maps import create_default_map
from grid_rpg_ai.render import (
    build_static_map,
    compute_visibility,
    load_tiles,
    make_goal_sprite,
    make_player_sprite,
    render_frame,
)
from examples.fog_sandbox import attempt_move


def test_compute_visibility_tracks_current_and_previously_seen_tiles() -> None:
    visibility = compute_visibility(
        width=5,
        height=3,
        player_pos=(2, 1),
        discovered={(0, 0), (99, 99)},
        radius=1,
    )

    assert visibility == [
        ["seen", "unknown", "unknown", "unknown", "unknown"],
        ["visible", "visible", "visible", "unknown", "unknown"],
        ["unknown", "visible", "visible", "visible", "unknown"],
    ]


def test_compute_visibility_rejects_invalid_dimensions_and_radius() -> None:
    with pytest.raises(ValueError, match="dimensions"):
        compute_visibility(0, 2, (0, 0), set(), 1)
    with pytest.raises(ValueError, match="non-negative"):
        compute_visibility(2, 2, (0, 0), set(), -1)


@pytest.mark.parametrize("sprite_factory", [make_player_sprite, make_goal_sprite])
def test_marker_sprites_have_transparent_background_and_translucent_ink(sprite_factory) -> None:
    sprite = sprite_factory(32)

    assert sprite.mode == "RGBA"
    assert sprite.getpixel((0, 0))[3] == 0
    assert any(0 < pixel[3] < 255 for pixel in sprite.getdata())


def test_render_frame_only_draws_goal_after_discovery() -> None:
    grid = [["plains", "forest"]]
    tiles = load_tiles()
    base_map = build_static_map(grid, tiles)
    goal_sprite = Image.new("RGBA", (32, 32), (255, 0, 0, 255))
    unknown = [["visible", "unknown"]]
    discovered = [["visible", "seen"]]

    hidden_frame = render_frame(
        base_map,
        grid,
        unknown,
        (0, 0),
        tiles=tiles,
        goal_pos=(1, 0),
        goal_sprite=goal_sprite,
    )
    shown_frame = render_frame(
        base_map,
        grid,
        discovered,
        (0, 0),
        tiles=tiles,
        goal_pos=(1, 0),
        goal_sprite=goal_sprite,
    )

    assert hidden_frame.getpixel((32 + 16, 16)) == base_map.getpixel((32 + 16, 16))
    assert shown_frame.getpixel((32 + 16, 16)) == (255, 0, 0, 255)


def test_sandbox_moves_only_to_walkable_cells_inside_the_map() -> None:
    game_map = create_default_map()

    assert attempt_move(game_map, (0, 0), "Derecha") == ((1, 0), None)
    assert attempt_move(game_map, (0, 0), "Izquierda") == (
        (0, 0),
        "No puedes salirte del mapa.",
    )
    assert attempt_move(game_map, (8, 3), "Derecha") == (
        (8, 3),
        "Ese terreno bloquea el paso.",
    )


def test_sandbox_rejects_unknown_movement_direction() -> None:
    with pytest.raises(ValueError, match="Unknown movement direction"):
        attempt_move(create_default_map(), (0, 0), "Diagonal")
