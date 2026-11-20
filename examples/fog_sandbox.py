from __future__ import annotations

from pathlib import Path
from random import Random

import streamlit as st

from grid_rpg_ai.data.maps import get_map
from grid_rpg_ai.gamestate import GameState
from grid_rpg_ai.render import (
    TILE_SIZE,
    build_static_map,
    compute_visibility,
    load_tiles,
    render_frame,
)
from grid_rpg_ai.rules import DEFAULT_EVENT_CHANCE, resolve_move


MAP = get_map()


@st.cache_resource
def cached_tiles(mode: str):
    tiles_dir = Path(__file__).resolve().parents[1] / "grid_rpg_ai" / "assets" / "tiles"
    return load_tiles(
        mode=mode,
        tiles_dir=tiles_dir if mode == "folder" else None,
        fallback_to_colors=False,
    )


def new_game_state() -> GameState:
    return GameState(
        rows=MAP.height,
        cols=MAP.width,
        player_pos=MAP.start,
        goal_pos=MAP.goal,
    )


def initialize_session() -> None:
    if "game_state" not in st.session_state:
        st.session_state.game_state = new_game_state()
    if "event_rng" not in st.session_state:
        st.session_state.event_rng = Random()


def move_player(direction: str, event_chance: float) -> None:
    state: GameState = st.session_state.game_state
    result = resolve_move(
        state,
        MAP,
        direction,
        rng=st.session_state.event_rng,
        event_chance=event_chance,
    )
    state.apply_move_result(result)


def main() -> None:
    st.set_page_config(
        page_title="Grid RPG Engine Sandbox",
        page_icon="🧭",
        layout="wide",
    )
    st.markdown(
        """
        <style>
            .block-container {
                max-width: 100%;
                padding-left: 1.5rem;
                padding-right: 1.5rem;
                padding-top: 1.5rem;
            }
            [data-testid="stSidebar"] .stButton > button {
                min-height: 2.25rem;
                padding: 0.25rem 0.5rem;
            }
            [data-testid="stVerticalBlockBorderWrapper"] {
                margin-bottom: 0.25rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    initialize_session()
    state: GameState = st.session_state.game_state
    st.title("Grid RPG Engine Sandbox")
    st.caption("Playable movement, biome events, discovery, and fog-of-war loop.")

    with st.sidebar:
        st.header("Settings")
        radius = st.slider("Vision radius", min_value=1, max_value=4, value=2)
        map_zoom = st.slider(
            "Map zoom",
            min_value=50,
            max_value=200,
            value=100,
            step=10,
            format="%d%%",
        )
        fog_enabled = st.checkbox("Enable fog of war", value=True)
        events_enabled = st.checkbox("Enable biome events", value=True)
        event_chance = DEFAULT_EVENT_CHANCE if events_enabled else 0.0
        tile_mode = st.radio("Tile style", options=["Colors", "Images"], horizontal=True)
        tile_mode = "colors" if tile_mode == "Colors" else "folder"
        if st.button("Reset game", use_container_width=True):
            st.session_state.game_state = new_game_state()
            st.session_state.event_rng = Random()
            state = st.session_state.game_state

        st.divider()
        st.subheader("Move")
        controls_disabled = state.is_victory()
        top = st.columns(3)
        if top[1].button(
            "⬆️", use_container_width=True, help="Move up", disabled=controls_disabled
        ):
            move_player("up", event_chance)
        middle = st.columns(3)
        if middle[0].button(
            "⬅️", use_container_width=True, help="Move left", disabled=controls_disabled
        ):
            move_player("left", event_chance)
        if middle[2].button(
            "➡️", use_container_width=True, help="Move right", disabled=controls_disabled
        ):
            move_player("right", event_chance)
        bottom = st.columns(3)
        if bottom[1].button(
            "⬇️", use_container_width=True, help="Move down", disabled=controls_disabled
        ):
            move_player("down", event_chance)

    position = state.player_pos
    discovered_coords = {
        (x, y)
        for y, row in enumerate(state.discovered)
        for x, discovered in enumerate(row)
        if discovered
    }
    visibility = compute_visibility(
        MAP.width,
        MAP.height,
        position,
        discovered_coords,
        radius,
    )
    for y, row in enumerate(visibility):
        for x, visibility_state in enumerate(row):
            if visibility_state == "visible":
                state.discover((x, y))
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
    display_width = round(frame.width * 2.5 * map_zoom / 100)
    st.image(frame, width=display_width)

    biome = MAP.biome_at(*position)
    st.write(
        f"**Position:** x={position[0]}, y={position[1]}  ·  "
        f"**Biome:** {biome.display_name}  ·  **Turn:** {state.turn}"
    )

    if state.log:
        st.subheader("Recent turns")
        for entry in reversed(state.log[-5:]):
            st.write(f"- {entry}")

    if state.inventory:
        st.write("**Inventory:** " + ", ".join(state.inventory))
    active_clues = [key for key, active in state.status.items() if active]
    if active_clues:
        st.write("**Known clues:** " + ", ".join(active_clues))

    if state.is_victory():
        st.success(f"You reached the objective in {state.turn} turns!")


if __name__ == "__main__":
    main()
