from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from PIL import Image, ImageColor, ImageDraw

from grid_rpg_ai.data.biomes import BIOMES, VALID_BIOME_KEYS, get_biome


Coord = Tuple[int, int]

TILE_SIZE = 32
FOG_ALPHA = {
    "unknown": 255,
    "seen": 190,
    "visible": 0,
}


def _hex_to_rgba(color: str) -> Tuple[int, int, int, int]:
    return ImageColor.getcolor(color, "RGBA")


def make_color_tile(color: str, size: int = TILE_SIZE, label: Optional[str] = None) -> Image.Image:
    img = Image.new("RGBA", (size, size), _hex_to_rgba(color))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, size - 1, size - 1), outline=(20, 20, 20, 90), width=1)
    if label:
        draw.text((size // 3, size // 4), label[:1], fill=(255, 255, 255, 220))
    return img


def make_player_sprite(size: int = TILE_SIZE) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = size // 5
    draw.ellipse((pad, pad, size - pad, size - pad), fill=(225, 80, 72, 255))
    draw.ellipse((size // 2 - 3, size // 2 - 9, size // 2 + 3, size // 2 - 3), fill=(255, 255, 255, 220))
    return img


def load_tiles(
    tile_size: int = TILE_SIZE,
    mode: str = "colors",
    tiles_dir: Optional[str | Path] = None,
    fallback_to_colors: bool = True,
) -> Dict[str, Image.Image]:
    """
    Load biome tiles either from plain biome colors or from a folder of images.

    modes:
    - colors: create tiles from biomes.py colors
    - folder: try to load {biome_key}.png from tiles_dir
    """

    mode = mode.lower().strip()
    tiles: Dict[str, Image.Image] = {}

    if mode not in {"colors", "folder"}:
        raise ValueError("mode must be 'colors' or 'folder'")

    tiles_path = Path(tiles_dir) if tiles_dir is not None else None

    for biome_key in VALID_BIOME_KEYS:
        biome = get_biome(biome_key)

        if mode == "folder":
            if tiles_path is None:
                raise ValueError("tiles_dir is required when mode='folder'")
            img_path = tiles_path / f"{biome_key}.png"
            if img_path.exists():
                img = Image.open(img_path).convert("RGBA").resize((tile_size, tile_size), Image.NEAREST)
                tiles[biome_key] = img
                continue
            if not fallback_to_colors:
                raise FileNotFoundError(f"Missing tile image for biome '{biome_key}': {img_path}")

        tiles[biome_key] = make_color_tile(biome.color, tile_size, biome.symbol)

    return tiles


def apply_fog(tile_img: Image.Image, visibility_state: str) -> Image.Image:
    alpha = FOG_ALPHA.get(visibility_state, FOG_ALPHA["unknown"])
    if alpha <= 0:
        return tile_img
    overlay = Image.new("RGBA", tile_img.size, (0, 0, 0, alpha))
    return Image.alpha_composite(tile_img.convert("RGBA"), overlay)


def build_static_map(grid: Iterable[Iterable[str]], tiles: Dict[str, Image.Image], tile_size: int = TILE_SIZE) -> Image.Image:
    grid = [list(row) for row in grid]
    rows = len(grid)
    cols = len(grid[0])
    canvas = Image.new("RGBA", (cols * tile_size, rows * tile_size), (10, 10, 10, 255))

    for y, row in enumerate(grid):
        for x, biome_key in enumerate(row):
            if biome_key not in tiles:
                raise ValueError(f"No tile loaded for biome '{biome_key}'")
            canvas.paste(tiles[biome_key], (x * tile_size, y * tile_size))
    return canvas


def render_frame(
    base_map: Image.Image,
    grid: Iterable[Iterable[str]],
    visibility: Iterable[Iterable[str]],
    player_pos: Coord,
    player_sprite: Optional[Image.Image] = None,
    tiles: Optional[Dict[str, Image.Image]] = None,
    tile_size: int = TILE_SIZE,
) -> Image.Image:
    grid = [list(row) for row in grid]
    visibility = [list(row) for row in visibility]
    frame = base_map.copy()

    if tiles is None:
        raise ValueError("tiles is required for fog re-rendering")

    for y, row in enumerate(grid):
        for x, biome_key in enumerate(row):
            state = visibility[y][x]
            if state != "visible":
                fogged = apply_fog(tiles[biome_key], state)
                frame.paste(fogged, (x * tile_size, y * tile_size))

    if player_sprite is None:
        player_sprite = make_player_sprite(tile_size)

    px, py = player_pos
    frame.paste(player_sprite, (px * tile_size, py * tile_size), player_sprite)
    return frame


if __name__ == "__main__":
    grid = [
        ["plains", "plains", "forest", "forest", "hill", "mountain"],
        ["plains", "swamp", "forest", "road", "hill", "mountain"],
        ["desert", "swamp", "ruins", "road", "lake", "lake"],
        ["desert", "desert", "road", "road", "hill", "hill"],
    ]
    visibility = [
        ["seen", "visible", "visible", "unknown", "unknown", "unknown"],
        ["seen", "visible", "visible", "seen", "unknown", "unknown"],
        ["unknown", "seen", "visible", "visible", "unknown", "unknown"],
        ["unknown", "unknown", "seen", "visible", "seen", "unknown"],
    ]
    tiles = load_tiles(mode="colors")
    base = build_static_map(grid, tiles)
    image = render_frame(base, grid, visibility, player_pos=(2, 1), tiles=tiles)
    image.save("render_demo_biomes.png")
