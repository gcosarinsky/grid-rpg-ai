from pathlib import Path

from grid_rpg_ai.data.maps import (
    create_default_map,
    render_colored_symbol_grid,
    render_symbol_grid,
)
from grid_rpg_ai.render import build_static_map, load_tiles


def main() -> None:
    game_map = create_default_map()

    print("DEFAULT MAP (plain)\n")
    print(render_symbol_grid(game_map, player_pos=game_map.start))
    print("\nDEFAULT MAP (colored)\n")
    print(render_colored_symbol_grid(game_map, player_pos=game_map.start))

    tiles1 = load_tiles(mode="colors")
    image1 = build_static_map(game_map.grid, tiles1)
    tiles_dir = Path(__file__).parents[1] / "grid_rpg_ai" / "assets" / "tiles"
    tiles2 = load_tiles(mode="folder", tiles_dir=tiles_dir, fallback_to_colors=False)
    image2 = build_static_map(game_map.grid, tiles2)

    output_path1 = Path("default_map_colors.png")
    image1.save(output_path1)
    output_path2 = Path("default_map_tiles_folder.png")
    image2.save(output_path2)
    print(f"\nSaved default map images to: {output_path1.resolve()} and {output_path2.resolve()}")


if __name__ == "__main__":
    main()