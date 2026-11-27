from __future__ import annotations

import argparse
import sys

from grid_rpg_ai.data.maps import get_map
from grid_rpg_ai.gamestate import GameState
from grid_rpg_ai.llm import (
    DEFAULT_OLLAMA_MODEL,
    NarrationError,
    OllamaProvider,
    build_narration_context,
    build_narration_prompt,
)
from grid_rpg_ai.rules import resolve_move


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show a resolved-turn prompt and request narration from Ollama."
    )
    parser.add_argument(
        "--model", default=DEFAULT_OLLAMA_MODEL, help="Ollama model to use"
    )
    args = parser.parse_args()

    game_map = get_map()
    state = GameState(
        rows=game_map.height,
        cols=game_map.width,
        player_pos=game_map.start,
        goal_pos=game_map.goal,
    )
    result = resolve_move(state, game_map, "right", event_chance=0, language="es")
    state.apply_move_result(result)
    context = build_narration_context(state, game_map, result, language="es")
    prompt = build_narration_prompt(context)

    print("=== Prompt ===")
    print(prompt, flush=True)
    print(f"Solicitando respuesta a Ollama ({args.model})...", flush=True)

    try:
        response = OllamaProvider(model=args.model, timeout=120).generate(prompt)
    except NarrationError as exc:
        print(f"Error al consultar Ollama: {exc}", file=sys.stderr)
        return 1

    print("\n=== Respuesta ===")
    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
