from __future__ import annotations

from pathlib import Path
from typing import Optional

import streamlit as st

from grid_rpg_ai.data.maps import MapData, get_map, in_bounds, is_walkable
from grid_rpg_ai.render import (
    TILE_SIZE,
    build_static_map,
    compute_visibility,
    load_tiles,
    render_frame,
)


MAP = get_map()
DIRECTIONS = {
    "Arriba": (0, -1),
    "Izquierda": (-1, 0),
    "Abajo": (0, 1),
    "Derecha": (1, 0),
}


@st.cache_resource
def cached_tiles(mode: str):
    tiles_dir = Path(__file__).resolve().parents[1] / "grid_rpg_ai" / "assets" / "tiles"
    return load_tiles(
        mode=mode,
        tiles_dir=tiles_dir if mode == "folder" else None,
        fallback_to_colors=False,
    )


def attempt_move(
    game_map: MapData, position: tuple[int, int], direction: str
) -> tuple[tuple[int, int], Optional[str]]:
    if direction not in DIRECTIONS:
        raise ValueError(f"Unknown movement direction: {direction!r}")

    dx, dy = DIRECTIONS[direction]
    destination = (position[0] + dx, position[1] + dy)
    if not in_bounds(game_map, *destination):
        return position, "No puedes salirte del mapa."
    if not is_walkable(game_map, *destination):
        return position, "Ese terreno bloquea el paso."
    return destination, None


def initialize_session() -> None:
    if "player_pos" not in st.session_state:
        st.session_state.player_pos = MAP.start
        st.session_state.discovered = set()
        st.session_state.move_message = ""


def main() -> None:
    st.set_page_config(page_title="Fog of War Sandbox", page_icon="🧭")
    initialize_session()
    st.title("Fog of War Sandbox")
    st.caption("Demo de movimiento en grilla y visibilidad; no usa el engine de juego.")

    with st.sidebar:
        st.header("Configuración")
        radius = st.slider("Radio de visión", min_value=1, max_value=4, value=2)
        fog_enabled = st.checkbox("Activar fog of war", value=True)
        tile_mode = st.radio("Estilo de tiles", options=["colors", "folder"], horizontal=True)
        if st.button("Reiniciar posición", use_container_width=True):
            st.session_state.player_pos = MAP.start
            st.session_state.discovered = set()
            st.session_state.move_message = ""

    position = st.session_state.player_pos
    visibility = compute_visibility(
        MAP.width,
        MAP.height,
        position,
        st.session_state.discovered,
        radius,
    )
    st.session_state.discovered.update(
        (x, y)
        for y, row in enumerate(visibility)
        for x, state in enumerate(row)
        if state == "visible"
    )
    displayed_visibility = (
        visibility
        if fog_enabled
        else [["visible"] * MAP.width for _ in range(MAP.height)]
    )

    st.subheader("Mover")
    top = st.columns(3)
    if top[1].button("⬆️", use_container_width=True, help="Mover arriba"):
        position, message = attempt_move(MAP, position, "Arriba")
        st.session_state.player_pos = position
        st.session_state.move_message = message or ""
    middle = st.columns(3)
    if middle[0].button("⬅️", use_container_width=True, help="Mover a la izquierda"):
        position, message = attempt_move(MAP, position, "Izquierda")
        st.session_state.player_pos = position
        st.session_state.move_message = message or ""
    if middle[2].button("➡️", use_container_width=True, help="Mover a la derecha"):
        position, message = attempt_move(MAP, position, "Derecha")
        st.session_state.player_pos = position
        st.session_state.move_message = message or ""
    bottom = st.columns(3)
    if bottom[1].button("⬇️", use_container_width=True, help="Mover abajo"):
        position, message = attempt_move(MAP, position, "Abajo")
        st.session_state.player_pos = position
        st.session_state.move_message = message or ""

    position = st.session_state.player_pos
    visibility = compute_visibility(
        MAP.width,
        MAP.height,
        position,
        st.session_state.discovered,
        radius,
    )
    st.session_state.discovered.update(
        (x, y)
        for y, row in enumerate(visibility)
        for x, state in enumerate(row)
        if state == "visible"
    )
    displayed_visibility = (
        visibility
        if fog_enabled
        else [["visible"] * MAP.width for _ in range(MAP.height)]
    )

    tiles = cached_tiles(tile_mode)
    base_map = build_static_map(MAP.grid, tiles, TILE_SIZE)
    frame = render_frame(
        base_map,
        MAP.grid,
        displayed_visibility,
        player_pos=position,
        tiles=tiles,
        tile_size=TILE_SIZE,
        goal_pos=MAP.goal,
    )
    st.image(frame, use_container_width=True)

    biome = MAP.biome_at(*position)
    st.write(f"**Posición:** x={position[0]}, y={position[1]}  ·  **Bioma:** {biome.display_name}")
    if st.session_state.move_message:
        st.info(st.session_state.move_message)
    if position == MAP.goal:
        st.success("¡Llegaste al objetivo!")


if __name__ == "__main__":
    main()
