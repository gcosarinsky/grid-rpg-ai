from grid_rpg_ai.data.maps import (
    create_default_map,
    render_colored_symbol_grid,
    render_symbol_grid,
)


def main() -> None:
    game_map = create_default_map()

    print("DEFAULT MAP (plain)\n")
    print(render_symbol_grid(game_map, player_pos=game_map.start))
    print("\nDEFAULT MAP (colored)\n")
    print(render_colored_symbol_grid(game_map, player_pos=game_map.start))


if __name__ == "__main__":
    main()
