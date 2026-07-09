# RPG LLM Project Roadmap

This document defines a small MVP for a grid-based narrative RPG built with Streamlit and an LLM-driven narration layer. The original project outline proposes a 6x6 grid, biome-based regions, session state persistence, and an LLM that reacts to the current turn context [cite:1].

## Project goal

The goal of the MVP is to produce a playable demo that is small enough to finish quickly but still demonstrates three things clearly: deterministic game logic, reactive narrative generation, and a clean web interface. The original outline already provides the right base for this by separating grid navigation, persistence, and narrative prompting [cite:1].

A good MVP target is a single-player adventure where the player moves through a 6x6 map trying to reach a fixed objective such as a treasure tile or a tavern tile. This fits the existing grid structure and keeps the win condition easy to understand in a short demo [cite:1].

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

A practical build order is:

1. Build `game_state.py` and `rules.py` first.
2. Add `render.py` to display the grid and player.
3. Connect everything in `app.py` with Streamlit buttons and session state [cite:1].
4. Add `llm.py` only after the base loop is already playable.
5. Add structured events before adding NPCs or retrieval.

This order reduces debugging difficulty because state and movement issues are solved before narrative complexity is added.

## Development notes

The original outline proposes `st.session_state` for persistence and `st.secrets` for API key handling in Streamlit, which should remain part of the final implementation [cite:1]. It also recommends short prompts with injected environmental variables, which is the right strategy for keeping token use under control in a turn-based loop [cite:1].
