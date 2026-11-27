from __future__ import annotations

from html import escape
from pathlib import Path
from random import Random

import streamlit as st

from grid_rpg_ai.data.maps import get_map
from grid_rpg_ai.gamestate import GameState
from grid_rpg_ai.llm import (
    DEFAULT_OLLAMA_MODEL,
    NarrationError,
    NarrationResponse,
    OllamaProvider,
    build_narration_context,
    generate_narration,
    list_ollama_models,
    start_ollama,
)
from grid_rpg_ai.localization import (
    LANGUAGE_LABELS,
    SUPPORTED_LANGUAGES,
    Language,
    biome_name,
    text,
)
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
    if "language" not in st.session_state:
        st.session_state.language = "en"
    if "ollama_models" not in st.session_state:
        refresh_ollama()
    if "narration_response" not in st.session_state:
        st.session_state.narration_response = None


def refresh_ollama(start: bool = False) -> None:
    try:
        models = start_ollama() if start else list_ollama_models()
    except NarrationError as exc:
        st.session_state.ollama_models = None
        st.session_state.ollama_error = str(exc)
    else:
        st.session_state.ollama_models = models
        st.session_state.ollama_error = None


def ollama_controls(language: Language) -> None:
    with st.expander("Ollama", expanded=False):
        if st.button(text("ollama_check", language), key="ollama_check"):
            refresh_ollama()
        if st.button(text("ollama_start", language), key="ollama_start"):
            with st.spinner(text("starting_ollama", language)):
                refresh_ollama(start=True)

        models = st.session_state.ollama_models
        if models is None:
            st.warning(
                f"{text('ollama_unavailable', language)}: {st.session_state.ollama_error}"
            )
        else:
            st.success(text("ollama_available", language))
            if not models:
                st.info(text("ollama_no_models", language))

        models = models or []
        if st.session_state.get("ollama_model") not in models:
            st.session_state.ollama_model = (
                DEFAULT_OLLAMA_MODEL if DEFAULT_OLLAMA_MODEL in models
                else (models[0] if models else None)
            )
        st.selectbox(
            text("ollama_model", language),
            options=models,
            key="ollama_model",
            disabled=not models,
        )
        st.checkbox(text("enable_llm", language), key="narration_enabled")


def move_player(direction: str, event_chance: float, language: Language) -> None:
    state: GameState = st.session_state.game_state
    result = resolve_move(
        state,
        MAP,
        direction,
        rng=st.session_state.event_rng,
        event_chance=event_chance,
        language=language,
    )
    state.apply_move_result(result)
    context = build_narration_context(state, MAP, result, language)
    if not st.session_state.narration_enabled:
        st.session_state.narration_response = generate_narration(context)
    elif not st.session_state.ollama_models or not st.session_state.ollama_model:
        fallback = generate_narration(context)
        st.session_state.narration_response = NarrationResponse(
            text=fallback.text,
            used_fallback=True,
            error=text("ollama_select_model", language),
        )
    else:
        provider = OllamaProvider(model=st.session_state.ollama_model, timeout=120)
        with st.spinner(text("generating_narration", language)):
            st.session_state.narration_response = generate_narration(context, provider)


def render_narration_panel(language: Language, sidebar: bool = False) -> None:
    extra_class = " narration-panel--sidebar" if sidebar else ""
    response: NarrationResponse | None = st.session_state.narration_response
    narration = response.text if response else text("narration_placeholder", language)
    st.markdown(
        f"""
        <div class="narration-panel{extra_class}">
            <div class="narration-label">{text("narration_label", language)}</div>
            <p>{escape(narration)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if response and response.error:
        st.warning(f"{text('narration_fallback', language)}: {response.error}")


def main() -> None:
    st.set_page_config(
        page_title="Grid RPG Debug App",
        page_icon="🧭",
        layout="wide",
    )
    st.markdown(
        """
        <style>
            .block-container {
                max-width: 100%;
                padding: 0.75rem 1.25rem 1rem;
            }
            [data-testid="stHeader"] {
                display: none;
            }
            [data-testid="stSidebar"] {
                width: 16rem;
            }
            [data-testid="stSidebar"] > div {
                padding-top: 0.5rem;
            }
            [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
                gap: 0.35rem;
            }
            [data-testid="stSidebar"] h1 {
                font-size: 1.65rem;
                line-height: 1.15;
                margin-bottom: 0.15rem;
            }
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3 {
                font-size: 1.1rem;
                margin: 0.2rem 0;
            }
            [data-testid="stSidebar"] .stSlider,
            [data-testid="stSidebar"] .stCheckbox,
            [data-testid="stSidebar"] .stRadio {
                margin-bottom: -0.35rem;
            }
            [data-testid="stSidebar"] .stButton > button {
                min-height: 2rem;
                padding: 0.15rem 0.4rem;
            }
            [data-testid="stSidebar"] hr {
                margin: 0.45rem 0;
            }
            .narration-panel {
                min-height: 5rem;
                margin-bottom: 0.75rem;
                padding: 0.75rem 1rem;
                border: 1px solid rgba(128, 128, 128, 0.3);
                border-radius: 0.5rem;
                background: rgba(128, 128, 128, 0.08);
            }
            .narration-panel .narration-label {
                margin-bottom: 0.35rem;
                color: #777;
                font-size: 0.75rem;
                font-weight: 600;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }
            .narration-panel p {
                margin: 0;
            }
            .narration-panel--sidebar {
                min-height: 14rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    initialize_session()
    state: GameState = st.session_state.game_state
    with st.sidebar:
        language: Language = st.selectbox(
            text("language", st.session_state.language),
            options=list(SUPPORTED_LANGUAGES),
            format_func=lambda value: LANGUAGE_LABELS[value],
            key="language",
        )
        st.title(text("title", language))
        st.caption(text("caption", language))
        ollama_controls(language)
        st.subheader(text("move", language))
        event_chance = (
            DEFAULT_EVENT_CHANCE
            if st.session_state.get("events_enabled", True)
            else 0.0
        )
        controls_disabled = state.is_victory()
        top = st.columns(3)
        if top[1].button(
            "⬆️",
            use_container_width=True,
            help=text("move_up", language),
            disabled=controls_disabled,
        ):
            move_player("up", event_chance, language)
        middle = st.columns(3)
        if middle[0].button(
            "⬅️", use_container_width=True, help=text("move_left", language), disabled=controls_disabled
        ):
            move_player("left", event_chance, language)
        if middle[2].button(
            "➡️", use_container_width=True, help=text("move_right", language), disabled=controls_disabled
        ):
            move_player("right", event_chance, language)
        bottom = st.columns(3)
        if bottom[1].button(
            "⬇️",
            use_container_width=True,
            help=text("move_down", language),
            disabled=controls_disabled,
        ):
            move_player("down", event_chance, language)

        st.divider()
        with st.expander(text("settings", language), expanded=False):
            radius = st.slider(text("vision_radius", language), min_value=1, max_value=4, value=2)
            map_zoom = st.slider(
                text("map_zoom", language),
                min_value=50,
                max_value=200,
                value=100,
                step=10,
                format="%d%%",
            )
            fog_enabled = st.checkbox(
                text("enable_fog", language), value=True, key="fog_enabled"
            )
            st.checkbox(
                text("enable_events", language), value=True, key="events_enabled"
            )
            tile_style = st.radio(
                text("tile_style", language),
                options=[text("colors", language), text("images", language)],
                horizontal=True,
            )
            tile_mode = "colors" if tile_style == text("colors", language) else "folder"
            narration_position = st.radio(
                text("narration", language),
                options=[text("above_map", language), text("right_side", language)],
                horizontal=True,
            )
            if st.button(text("reset_game", language), use_container_width=True):
                st.session_state.game_state = new_game_state()
                st.session_state.event_rng = Random()
                st.session_state.narration_response = None
                state = st.session_state.game_state

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

    display_width = round(frame.width * map_zoom / 100)
    if narration_position == text("above_map", language):
        render_narration_panel(language)
        st.image(frame, width=display_width)
    else:
        map_column, narration_column = st.columns([2, 1], gap="large")
        with map_column:
            st.image(frame, width=display_width)
        with narration_column:
            render_narration_panel(language, sidebar=True)

    biome = MAP.biome_at(*position)
    st.write(
        f"**{text('position', language)}:** x={position[0]}, y={position[1]}  ·  "
        f"**{text('biome', language)}:** {biome_name(biome.key, language)}  ·  "
        f"**{text('turn', language)}:** {state.turn}"
    )

    if state.log:
        st.subheader(text("recent_turns", language))
        for entry in reversed(state.log[-5:]):
            st.write(f"- {entry}")

    if state.inventory:
        st.write(f"**{text('inventory', language)}:** " + ", ".join(state.inventory))
    active_clues = [key for key, active in state.status.items() if active]
    if active_clues:
        st.write(f"**{text('known_clues', language)}:** " + ", ".join(active_clues))

    if state.is_victory():
        st.success(text("victory", language, turn=state.turn))


if __name__ == "__main__":
    main()
