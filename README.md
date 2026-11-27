# Grid RPG with LLM Narration

Work-in-progress Python project for a small grid-based RPG that combines deterministic game rules with LLM-driven content.

The goal is to build a playable demo that is small enough to finish, but still strong as a GitHub portfolio project. It should show game state management, rule-based movement, event handling, map exploration, and an AI layer that adds narrative and structured suggestions without replacing the underlying game engine.

## Project idea

This project explores a simple RPG engine where the player moves through a map while an LLM helps make the world feel reactive and alive.

The main design rule is:

- The **engine** owns the game state and hard rules.
- The **LLM** adds narrative, suggestions, and higher-level world flavor.

That separation keeps the game testable and consistent while still making it feel dynamic.

## Current direction

The current MVP direction is a single-player adventure on a **10x10 grid** with:

- A player start position.
- One objective tile, such as a treasure or a tavern.
- Turn-based movement.
- Small biome-based events.
- Short LLM narration after each move.
- A lightweight log of recent turns.
- Space to grow into fog of war and richer world knowledge.

The intended gameplay loop is:

1. The player chooses a direction.
2. The rules engine validates the move.
3. A structured event may modify the outcome in a limited way.
4. The game state updates.
5. The LLM narrates the result.
6. The game checks whether the objective has been reached.

## LLM role

In the first version, the LLM is mainly a narrator. It should describe the current biome, the result of a move, and the immediate atmosphere of the turn.

Over time, the LLM can do more than narration while still staying grounded in engine-owned data:

- **Narration**: describe movement results, discoveries, obstacles, and short environmental flavor.
- **Map creation support**: help generate candidate maps, regions, landmarks, and points of interest that are then stored as structured game data.
- **Event suggestion**: propose event ideas for the current biome or location, with the rules layer validating or selecting only allowed outcomes.
- **NPC control**: drive higher-level NPC behavior, goals, or reactions after the engine resolves what is mechanically possible.
- **NPC conversations**: generate dialogue grounded in known world facts, player state, and discovered information.
- **Hint generation**: turn structured world facts into rumors, clues, signs, or dialogue without inventing invalid geography.

The important constraint is that the engine should still decide what is true, what is reachable, and what happened mechanically. The LLM can suggest or narrate, but it should not override game rules.

## Architecture

The roadmap points toward a modular structure where rules, state, rendering, and narration are kept separate.

Planned module responsibilities:

- `app.py` — Streamlit layout, controls, and interaction flow.
- `game_state.py` or `gamestate.py` — Core state model: grid, player position, goal, turns, logs, and discovered knowledge.
- `rules.py` — Movement validation, event resolution, collisions, and victory checks.
- `render.py` — Map drawing, HUD/status display, fog-of-war rendering, and visualization helpers.
- `llm.py` — Prompt construction, narration, dialogue, and controlled content generation.
- `data/maps.py` — Static maps or map factory functions.
- `data/events.py` — Event definitions by biome or region.
- `data/npcs.py` — Optional later module for NPC definitions and dialogue hooks.

This structure keeps rendering independent from rules, and it makes the project easier to test and extend.

## Debug app

The experimental Streamlit demo runs the integrated game loop: validated movement, biome events, persistent state, discovery, fog of war, and victory checks. Run it from the repository root with:

```powershell
uv sync
uv run streamlit run examples/debug_app.py
```

`uv sync` installs the project in editable mode, so the app imports `grid_rpg_ai` as an installed package rather than modifying `sys.path`.

Use the arrow buttons to move. The debug app supports biome events, resettable `GameState`, recent-turn history, color or image tiles, an adjustable vision radius, fog toggles, and an English/Spanish language selector. The selected language also controls the mechanical event phrases and clues shown in the turn log. Its player and goal markers are procedurally drawn RGBA sprites with transparent backgrounds.

The **Ollama** sidebar panel checks whether the local server is available, lets you start it or refresh its status, and lists installed models. Select one and enable Ollama narration to generate a response after each move. Narration is disabled by default; when disabled or unavailable, the app uses deterministic narration and remains playable. Provider errors are shown in the app. A generation request can take up to 120 seconds.

The start button runs `ollama serve` on the machine hosting Streamlit, only if the server is not already reachable. Ollama must be installed and available on that machine's PATH; the app does not download models or stop an existing server. Install models separately with `ollama pull <model-name>`, then refresh the list.

The language selection is carried into both the rules layer and the narration prompt, so generated narration uses the selected language.

## Local narration provider

The first narration provider is Ollama. Install Ollama separately and start its local server in a terminal:

```powershell
ollama serve
```

Keep that terminal open. If Ollama is already running (for example, through its Windows application), do not start a second server. In another terminal, download the default model:

```powershell
ollama pull llama3.1:8b
```

`grid_rpg_ai.llm` builds a bounded prompt from a resolved move and exposes an `OllamaProvider`; it uses Ollama's local HTTP API and does not require an API key. Provider errors can be reported alongside a deterministic fallback, so narration does not control movement or prevent the game from continuing.

The prompt gives the model environmental cues instead of biome names and asks for evocative narration without coordinates or explicit biome names, with style examples. These instructions guide the model but do not guarantee compliance; the engine remains authoritative.

To see an example prompt and Ollama's response in the terminal, run:

```powershell
uv run python examples/narration_demo.py
```

The script uses the default model above. To choose another installed model, add `--model <model-name>`. It connects to Ollama at `http://localhost:11434`, allows up to 120 seconds for the request, and reports errors if the service or model is unavailable.

## Why this project

This is meant to be a compact demo of applied AI engineering rather than a full RPG.

What makes it interesting is the combination of:

- Deterministic game logic.
- LLM-based narration and content assistance.
- Clear separation of concerns.
- Streamlit as a fast interface layer.
- Room for future extensions like fog of war, memory, NPCs, conversations, and inventory.

For a portfolio project, that combination is stronger than trying to build a huge content-heavy RPG from the start.

## MVP scope

The current MVP is intentionally narrow:

- 10x10 map.
- One player.
- One goal tile.
- Four movement controls.
- Turn counter.
- Recent event log.
- Short narration per move.
- Basic biome-dependent events.
- Win condition when the destination is reached.

The game should remain playable even if the LLM layer is removed. That is an important design constraint for reliability.

## Movement and events

Movement is **mostly deterministic**. The rules engine first validates bounds and biome walkability. A valid arrival then has a configurable chance of triggering one event from the destination biome's static catalog.

Supported event effects are deliberately bounded:

- No gameplay effect.
- Block the intended move.
- Redirect the player to a walkable adjacent tile.
- Reveal and persist a clue.
- Grant a clue from an encounter.

For example, a wolf event can cancel a valid forest move, while a sandstorm can push the player to another legal adjacent tile. Randomness is injectable so these outcomes remain reproducible in tests. The LLM should narrate the resolved result, or at a later stage suggest event flavor that is validated before being applied.

## Planned file tree

```text
grid-rpg-ai/
├── app.py
├── game_state.py
├── rules.py
├── render.py
├── llm.py
├── requirements.txt
├── README.md
├── .streamlit/
│   └── secrets.toml
├── data/
│   ├── maps.py
│   ├── events.py
│   └── npcs.py
└── assets/
    └── screenshot.png
```

## Status

This repository is currently a **work in progress**.

The deterministic game loop and local Ollama narration are implemented in the Streamlit debug app. Movement, biome events, state persistence, fog of war, discovery, and victory checks are connected.

## Next steps

- Add Google Gemini as an optional narration provider with secure API key configuration.
- Refactor the integrated sandbox into the final `app.py`.
- Add an end-to-end movement, event, state, and narration test.
- Add a clean screenshot or GIF for the repository page.

See the [current development checkpoint](./docs/rpg_llm_mvp_roadmap.md) for the full session-to-session implementation plan.

## Future ideas

After the MVP is stable, likely extensions include:

- NPC movement and behavior.
- NPC conversations.
- Larger maps.
- Small inventory and items.
- Retrieval-based memory with ChromaDB or FAISS.
- Multiple objectives built on the same engine.
- LLM-assisted map generation.
- LLM-suggested events validated by the rules engine.
- World knowledge layers where the engine stores full map truth and the player only sees partial knowledge.

## Tech notes

The roadmap suggests using:

- `Streamlit` for the UI.
- `st.session_state` for persistence during play.
- `st.secrets` or environment variables for future API key handling.
- Short prompts with structured context for the LLM layer.
- A modular architecture where rules, rendering, and narrative generation remain separate.

## Run goal

The near-term goal is a playable GitHub-ready demo that clearly shows:

- a rule-based game loop,
- a clean modular Python structure,
- grounded LLM narration,
- and a path toward richer AI features such as map generation, event suggestion, and NPC interaction without giving up control of the game state.
