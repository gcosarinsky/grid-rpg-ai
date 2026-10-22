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

## Fog of war sandbox

The experimental Streamlit demo lets you move around the starter map and inspect the fog of war without using the game engine:

```powershell
uv sync
uv run streamlit run examples/fog_sandbox.py
```

`uv sync` installs the project in editable mode, so the demo imports `grid_rpg_ai` as an installed package rather than modifying `sys.path`.

Use the arrow buttons to move. The sandbox supports color or image tiles, an adjustable vision radius, and a fog toggle for comparison. Its player and goal markers are procedurally drawn RGBA sprites with transparent backgrounds.

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

Movement is expected to be **mostly deterministic**.

If the player chooses a direction, the engine first attempts that move. Then an event layer may do one of a few bounded things:

- No effect.
- Block the move.
- Redirect the player.
- Reveal a clue.
- Grant a small reward or hint.

For example, a wolf event may block the path, but the rules engine should decide that outcome. The LLM should narrate it, or at a later stage suggest event flavor that is validated before being applied.

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

The architecture and MVP scope are already defined, but the implementation is still being assembled. The focus right now is on keeping the first version small, clear, and demo-friendly, then expanding the LLM role in controlled ways.

## Next steps

- Create `rules.py` for movement validation, event resolution, and win checks.
- Build the Streamlit app in `app.py`.
- Create and connect `llm.py` once the base loop is already playable.
- Add `render.py` for map and status visualization.
- Add a clean screenshot or GIF for the repository page.

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
- `st.secrets` for API key handling.
- Short prompts with structured context for the LLM layer.
- A modular architecture where rules, rendering, and narrative generation remain separate.

## Run goal

The near-term goal is a playable GitHub-ready demo that clearly shows:

- a rule-based game loop,
- a clean modular Python structure,
- grounded LLM narration,
- and a path toward richer AI features such as map generation, event suggestion, and NPC interaction without giving up control of the game state.
