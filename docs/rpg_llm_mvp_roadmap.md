# RPG LLM Project Roadmap

This document defines a small MVP for a grid-based narrative RPG built with Streamlit and an LLM-driven narration layer. The original project outline proposes a 6x6 grid, biome-based regions, session state persistence, and an LLM that reacts to the current turn context [cite:1].

## Project goal

The goal of the MVP is to produce a playable demo that is small enough to finish quickly but still demonstrates three things clearly: deterministic game logic, reactive narrative generation, and a clean web interface. The original outline already provides the right base for this by separating grid navigation, persistence, and narrative prompting [cite:1].

A good MVP target is a single-player adventure where the player moves through a 6x6 map trying to reach a fixed objective such as a treasure tile or a tavern tile. This fits the existing grid structure and keeps the win condition easy to understand in a short demo [cite:1].

## Current development checkpoint

Last updated: 2026-11-27.

The deterministic MVP is playable through `examples/debug_app.py`. The repository uses Python 3.10+ and the local development environment is managed with `uv`.

### Completed

- `grid_rpg_ai/gamestate.py`
  - Canonical game state, turns, logs, inventory, status flags, and discovery.
  - Move results are applied without mixing state and movement rules.
  - Coordinates consistently use `(x, y)` while grids use `[y][x]`.
- `grid_rpg_ai/rules.py`
  - Movement bounds and biome walkability.
  - Direction aliases.
  - Biome event selection with injectable randomness.
  - Bounded event effects: no effect, block, adjacent detour, and persisted clues.
  - Victory remains a `GameState` responsibility.
- `grid_rpg_ai/data/dataevents.py`
  - Static events grouped by biome.
  - Validation for supported effects and clue requirements.
- `grid_rpg_ai/render.py`
  - Image/color tiles, player and goal sprites, and fog of war.
- `examples/debug_app.py`
  - Integrated loop: `GameState` -> `resolve_move` -> `apply_move_result` -> rendering.
  - Movement controls, reset, turn count, recent log, event toggle, discovery, and victory display.
- Tests
  - Rules and event-resolution coverage in `tests/test_rules.py`.
  - Narration prompt, Ollama adapter, and fallback coverage in `tests/test_llm.py`.

Run the integrated debug app from the repository root:

```powershell
uv sync
uv run streamlit run examples/debug_app.py
```

### Remaining plan

#### Phase 5: LLM narration — core complete

`grid_rpg_ai/llm.py` remains downstream from the rules engine. The initial local-provider implementation is complete:

- A compact `NarrationContext` and `build_narration_prompt`, with no hidden goal coordinates.
- An `OllamaProvider` behind a mockable provider protocol.
- Deterministic fallback narration for missing or failed providers.
- Focused tests for prompt grounding, hidden-goal protection, localized output, provider failures, and resolved move outcomes.

Follow-up: add the Google Gemini provider using the same interface, reading its API key from environment variables or Streamlit secrets without committing credentials.

#### Phase 6: Connect narration to Streamlit

1. Pass the committed `MoveResult` and resulting `GameState` to the prompt builder.
2. Persist only the latest narration in `st.session_state`.
3. Display narration separately from mechanical log entries.
4. Avoid provider calls during initial rendering or unrelated widget changes.
5. Keep the game playable when narration is disabled or unavailable.
6. Document secrets configuration in `.streamlit/secrets.toml.example`; never commit local secrets.

#### Phase 7: Prepare `app.py`

Refactor the working sandbox into the repository-facing application:

1. Move stable UI helpers out of `examples/debug_app.py`.
2. Keep the example thin or replace its documented entry point with `app.py`.
3. Add clear objective, narration, log, reset, and status panels.
4. Preserve a no-LLM mode for local use and tests.
5. Keep movement and event resolution out of UI callbacks.

#### Phase 8: Validate and polish the MVP

1. Run the full suite with `uv run pytest -q`.
2. Add an end-to-end movement -> event -> state -> narration test.
3. Remove the Pillow deprecation warning in the tests if compatible with Python 3.10+.
4. Update README screenshots and entry-point instructions.
5. Confirm the sandbox and `app.py` share the same loop without duplication.

### Resume checklist

Before starting the next session:

1. Confirm the branch and worktree with `git status --short --branch`.
2. Read this checkpoint section.
3. Run `uv run pytest -q`.
4. Start Phase 5 with `llm.py`; do not integrate LLM-generated events yet.

LLM-suggested events remain a later extension. The model may propose structured content, but `rules.py` must validate and resolve every mechanical effect.

## MVP scope

The first version should be intentionally narrow:

- 6x6 map.
- A player starting position.
- One goal tile, hidden or visible.
- Four movement controls.
- A small turn log.
- Short LLM narration after each move.
- Basic biome-dependent events.
- A win screen when the player reaches the destination.

The important design rule is that the game engine should decide what happens mechanically, while the LLM explains it in narrative form. This is consistent with the project outline, where the map, turns, and state are already framed as structured systems rather than purely free-form text [cite:1].

## Milestone roadmap

### Milestone 1: Playable core

Build a version that works without any advanced AI behavior. The player should be able to move on the 6x6 grid, the game should validate map boundaries, and the app should detect when the goal tile has been reached [cite:1].

Features:
- Create the map matrix.
- Store player position in session state.
- Add buttons for up, down, left, and right.
- Track turns.
- Render the map and current status.
- Detect victory.

### Milestone 2: Narrative layer

Once the game loop works, add the LLM as a narrator. The outline already suggests a short-response system prompt and a dynamic prompt based on coordinates, biome, memory, and player action, which is a good fit for this stage [cite:1].

Features:
- Send biome plus player action to the LLM.
- Generate 1 to 3 short sentences.
- Keep narration stylistically consistent.
- Show the latest narration under the map.

### Milestone 3: Structured events

Add simple game events that are still controlled by code. For example, entering a tile may trigger an obstacle, a harmless flavor event, a hint, or a forced detour.

Features:
- Event table by biome.
- Event effects such as block move, no effect, reveal hint, or push to adjacent tile.
- LLM narration based on the selected effect.

This hybrid approach is safer than letting the model invent movement consequences on its own, because the rules remain testable and consistent.

### Milestone 4: GitHub-ready polish

The final MVP step is presentation. The app should clearly show the objective, expose the turn count, provide a restart option, and make the demo understandable to someone who opens the repository for the first time [cite:1].

Features:
- Restart game button.
- Clean README.
- Screenshot or GIF for repository page.
- Better prompt templates.
- Small set of handcrafted event texts.

## Movement rules

The recommended movement model is deterministic input plus bounded randomness. If the player chooses "move right," the engine first attempts to move right, then an event layer may block that move or modify the outcome in a limited way.

This means the player keeps agency, but the world can still feel dynamic. For example, a wolf event can cancel the move, a sandstorm can push the player sideways, or a helpful sign can reveal the goal direction.

A useful event schema is:

| Event type | Engine effect |
|------------|---------------|
| Flavor | No gameplay change |
| Obstacle | Cancel move |
| Detour | Redirect to another valid tile |
| Reward | Give clue or item |
| Goal clue | Reveal distance or direction hint |

## Recommended module structure

The project should keep rendering separate from rules. The original outline already distinguishes between navigation logic, state persistence, and narrative behavior, so the codebase should mirror that structure [cite:1].

| File | Responsibility |
|------|----------------|
| `app.py` | Streamlit layout, controls, and interaction flow |
| `game_state.py` | Core state model: grid, player, goal, turns, logs |
| `rules.py` | Movement validation, collisions, event resolution, victory checks |
| `render.py` | Map drawing, status panels, tile styling, simple HUD |
| `llm.py` | Prompt building and narrative generation |
| `data/maps.py` | Static maps or map factory functions |
| `data/events.py` | Event definitions by biome |

The visualization code for the map and player should live in `render.py`, not in `rules.py`. The rules module should decide whether a move is valid, while the renderer should decide how to display biome tiles, the player marker, and the goal marker.

## File tree

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
│   └── events.py
└── assets/
    └── screenshot.png
```

## Future extensions

After the MVP is stable, the next upgrades should build on the same architecture rather than replacing it.

### 1. NPCs

The outline already mentions an NPC moving by AI with collision checks, so this is a natural second phase [cite:1]. Start with a deterministic NPC pattern such as random walk or chase-within-radius before making the NPC LLM-driven.

### 2. Wider maps

Expand from 6x6 to 10x10 or larger once the renderer and rules are stable. At that point, adding fog of war or discovered tiles becomes useful so the map does not feel visually empty.

### 3. Inventory and items

A very small inventory can enrich the event system. For example, meat can distract wolves, a lantern can reduce night penalties, or a key can unlock a goal tile.

### 4. True memory retrieval

The outline proposes using a vector database such as ChromaDB or FAISS for selective recall instead of sending all history into context [cite:1]. That is a strong later-stage feature, but it is best added only after the base loop already generates enough narrative history to justify retrieval.

### 5. Multiple objectives

Once the engine works, the same system can support different mission types:
- Find the treasure.
- Reach the tavern.
- Escape the desert.
- Deliver a message.
- Survive a fixed number of turns.

## Implementation order

A practical revised build order is:

1. Complete the deterministic state, rules, event, and rendering loop. **Done.**
2. Integrate the loop in the Streamlit debug app. **Done.**
3. Add grounded narration in `llm.py`. **Done: prompt builder, Ollama provider, fallback, and focused tests.**
4. Connect narration to Streamlit without blocking deterministic play. **Next.**
5. Refactor the debug app into the final `app.py`.
6. Add structured LLM event suggestions only after narration is stable and validated.
7. Add NPCs or retrieval only after the core MVP is complete.

This order reduces debugging difficulty because state and movement issues are solved before narrative complexity is added.

## Development notes

The original outline proposes `st.session_state` for persistence and `st.secrets` for API key handling in Streamlit, which should remain part of the final implementation [cite:1]. It also recommends short prompts with injected environmental variables, which is the right strategy for keeping token use under control in a turn-based loop [cite:1].
