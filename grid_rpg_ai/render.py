from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional, Set, Tuple

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
    alpha = 225
    ink = (25, 25, 35, alpha)
    figure = (255, 235, 190, alpha)
    width = max(1, size // 12)
    cx = size // 2
    head_radius = max(2, size // 9)
    head_y = size // 4
    shoulder_y = size // 2
    hip_y = size * 3 // 4
    draw.ellipse(
        (cx - head_radius, head_y - head_radius, cx + head_radius, head_y + head_radius),
        fill=figure,
        outline=ink,
        width=width,
    )
    draw.line((cx, head_y + head_radius, cx, hip_y), fill=ink, width=width)
    draw.line((size // 4, shoulder_y, size * 3 // 4, shoulder_y), fill=ink, width=width)
    draw.line((cx, hip_y, size // 3, size - 2), fill=ink, width=width)
    draw.line((cx, hip_y, size * 2 // 3, size - 2), fill=ink, width=width)
    return img


def make_goal_sprite(size: int = TILE_SIZE) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = max(3, size // 4)
    center = size // 2
    width = max(2, size // 7)
    draw.line(
        (center, margin, center, size - margin),
        fill=(30, 25, 20, 225),
        width=width + 2,
    )
    draw.line(
        (margin, center, size - margin, center),
        fill=(30, 25, 20, 225),
        width=width + 2,
    )
    draw.line(
        (center, margin, center, size - margin),
        fill=(255, 220, 70, 230),
        width=width,
    )
    draw.line(
        (margin, center, size - margin, center),
        fill=(255, 220, 70, 230),
        width=width,
    )
    return img


def compute_visibility(
    width: int,
    height: int,
    player_pos: Coord,
    discovered: Iterable[Coord],
    radius: int,
) -> list[list[str]]:
    if width <= 0 or height <= 0:
        raise ValueError("Map dimensions must be positive")
    if radius < 0:
        raise ValueError("Visibility radius must be non-negative")

    px, py = player_pos
    discovered_set: Set[Coord] = {
        (x, y)
        for x, y in discovered
        if 0 <= x < width and 0 <= y < height
    }
    visible = {
        (x, y)
        for y in range(max(0, py - radius), min(height, py + radius + 1))
        for x in range(max(0, px - radius), min(width, px + radius + 1))
    }
    discovered_set.update(visible)

    return [
        [
            "visible" if (x, y) in visible else "seen" if (x, y) in discovered_set else "unknown"
            for x in range(width)
        ]
        for y in range(height)
    ]


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
    goal_pos: Optional[Coord] = None,
    goal_sprite: Optional[Image.Image] = None,
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
    frame.alpha_composite(player_sprite.convert("RGBA"), (px * tile_size, py * tile_size))

    if goal_pos is not None:
        gx, gy = goal_pos
        if visibility[gy][gx] in {"visible", "seen"}:
            if goal_sprite is None:
                goal_sprite = make_goal_sprite(tile_size)
            frame.alpha_composite(goal_sprite.convert("RGBA"), (gx * tile_size, gy * tile_size))

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
