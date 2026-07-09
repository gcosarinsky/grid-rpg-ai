from PIL import Image, ImageDraw

TILE_SIZE = 32

TERRAIN_COLORS = {
    "grass": (88, 140, 78, 255),
    "forest": (44, 92, 62, 255),
    "road": (156, 128, 92, 255),
    "water": (67, 113, 190, 255),
    "goal": (212, 174, 55, 255),
}

FOG_ALPHA = {
    "unknown": 210,
    "seen": 110,
    "visible": 0,
}


def make_base_tile(color, size=TILE_SIZE):
    img = Image.new("RGBA", (size, size), color)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, size - 1, size - 1), outline=(20, 20, 20, 80), width=1)
    return img


def make_player_sprite(size=TILE_SIZE):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = size // 5
    draw.ellipse((pad, pad, size - pad, size - pad), fill=(225, 80, 72, 255))
    draw.ellipse((size // 2 - 3, size // 2 - 9, size // 2 + 3, size // 2 - 3), fill=(255, 255, 255, 220))
    return img


def load_tiles(tile_size=TILE_SIZE):
    tiles = {name: make_base_tile(color, tile_size) for name, color in TERRAIN_COLORS.items()}
    player = make_player_sprite(tile_size)
    return tiles, player


def apply_fog(tile_img, visibility_state):
    alpha = FOG_ALPHA.get(visibility_state, 210)
    if alpha <= 0:
        return tile_img
    overlay = Image.new("RGBA", tile_img.size, (0, 0, 0, alpha))
    return Image.alpha_composite(tile_img.convert("RGBA"), overlay)


def build_static_map(grid, tiles, tile_size=TILE_SIZE):
    rows = len(grid)
    cols = len(grid[0])
    canvas = Image.new("RGBA", (cols * tile_size, rows * tile_size), (10, 10, 10, 255))

    for r, row in enumerate(grid):
        for c, terrain in enumerate(row):
            tile = tiles.get(terrain, tiles["grass"])
            canvas.paste(tile, (c * tile_size, r * tile_size))

    return canvas


def render_frame(base_map, grid, visibility, player_pos, player_sprite, tiles, tile_size=TILE_SIZE):
    frame = base_map.copy()

    for r, row in enumerate(grid):
        for c, terrain in enumerate(row):
            state = visibility[r][c]
            if state != "visible":
                tile = tiles.get(terrain, tiles["grass"])
                fogged = apply_fog(tile, state)
                frame.paste(fogged, (c * tile_size, r * tile_size))

    pr, pc = player_pos
    px = pc * tile_size
    py = pr * tile_size
    frame.paste(player_sprite, (px, py), player_sprite)
    return frame


if __name__ == "__main__":
    grid = [
        ["grass", "grass", "road", "road", "forest", "forest"],
        ["grass", "water", "road", "grass", "forest", "goal"],
        ["grass", "grass", "road", "grass", "forest", "forest"],
        ["grass", "grass", "grass", "grass", "grass", "grass"],
    ]

    visibility = [
        ["seen", "seen", "visible", "visible", "unknown", "unknown"],
        ["seen", "seen", "visible", "visible", "unknown", "unknown"],
        ["seen", "seen", "visible", "visible", "unknown", "unknown"],
        ["unknown", "unknown", "seen", "seen", "unknown", "unknown"],
    ]

    player_pos = (1, 2)
    tiles, player = load_tiles()
    base_map = build_static_map(grid, tiles)
    frame = render_frame(base_map, grid, visibility, player_pos, player, tiles)
    frame.save("render_demo.png")
