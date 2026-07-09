# LLM-Based Map Generation Module for the RPG Project

This document describes a new module for the grid-based RPG project: using an LLM to generate default world maps in a structured and reusable way. The goal is to expand the project beyond LLM-based narration and make map creation itself part of the AI system, while keeping the game engine in control of final gameplay truth.[cite:1][cite:2]

## Core idea

The project already separates mechanics from narration: the engine decides movement, collisions, events, and victory conditions, while the LLM explains what happened in natural language.[cite:1][cite:2] Building on that architecture, map generation can follow the same rule: the LLM proposes a map blueprint, and the engine validates, fixes if necessary, and stores the final canonical version used by the game.[cite:2]

This approach is stronger than asking the LLM to invent geography freely every turn. The fog-of-war design notes argue that the engine should own hard facts such as terrain, roads, settlements, landmarks, and obstacles, while the LLM should speak consistently about those facts without changing them.[cite:2]

## Why this improves the project

Adding an LLM map-generation module makes the repository more interesting as an AI systems demo because it shows controlled generation rather than simple text output.[cite:1][cite:2] It also fits the project roadmap, which already recommends a modular structure with separate files for map data, rules, rendering, and prompt logic.[cite:1]

A generated map can make each playthrough feel fresh while still staying small enough for an MVP. The roadmap already suggests starting with compact grid maps and later expanding toward larger worlds, fog of war, and named locations once the core loop is stable.[cite:1]

## Recommended architecture

A clean implementation would add a new module such as `mapgen.py` or `data/map_factory.py`, next to the existing modules for game state, rules, rendering, and LLM narration.[cite:1] The map generation pipeline should have three stages:[cite:1][cite:2]

1. Prompt the LLM to generate a structured map blueprint.
2. Validate the result with Python rules such as bounds checks, path connectivity, and point-of-interest constraints.
3. Save the validated result as the canonical world state for the game.

The internal world model should stay layered. The fog-of-war sketch recommends separating the complete world map, the named point-of-interest index, the player discovery state, the knowledge log, and the event layer rather than treating everything as one loose grid.[cite:2]

## Best generation pattern

The safest pattern is **LLM proposes, engine validates**. That means the LLM should not return prose descriptions for direct gameplay use; it should return structured data that the engine can inspect and approve.[cite:2]

The prompt should ask for a compact JSON schema containing:

- Grid size.
- Tile biome layout.
- Regions.
- Named points of interest.
- Start and goal positions.
- Optional narrative hooks tied to specific locations.

This matches the existing prompt-optimization direction in the project, where dynamic variables and compact structured context are preferred over large uncontrolled text histories.[cite:2][cite:3]

## Suggested prompt design

The map-generation prompt should be strict and reusable. It should tell the model to output only valid JSON, avoid markdown, keep the map small, ensure a path from start to goal, and use a controlled set of biome and location types.[cite:1][cite:2]

A practical function could accept variables such as:

- `width`, `height`
- `theme`
- `allowed_biomes`
- `max_pois`
- `required_locations`
- `tone`

This would let the same prompt generate different default maps for forests, deserts, ruins, or road-based travel scenarios while still preserving a consistent internal schema.[cite:2][cite:3]

## Example output schema

A useful schema for the generated result would include:

```json
{
  "width": 8,
  "height": 8,
  "tiles": [["plains", "plains"], ["forest", "road"]],
  "regions": [
    {"id": "blackwood", "type": "forest", "bounds": [[2, 2], [5, 5]]}
  ],
  "pois": [
    {"id": "dunmere", "kind": "town", "name": "Dunmere", "position": [6, 3], "tags": ["settlement", "supplies"]}
  ],
  "start": [0, 3],
  "goal": [6, 3],
  "hooks": [
    {"type": "rumor", "text": "A town lies east of the forest.", "poi_id": "dunmere"}
  ]
}
```

This schema aligns well with the fog-of-war design because it can feed both gameplay systems and narration systems. The validated result can become the source for `worldmap`, `poiindex`, fog states, and player knowledge summaries used in later prompts.[cite:2]

## Validation layer

The validator is essential. It should reject or repair maps that place locations outside the grid, create unreachable goals, overfill the world with landmarks, or contradict traversal rules.[cite:1][cite:2]

Minimum checks should include:

- Grid dimensions are correct.
- All coordinates are inside bounds.
- Start and goal exist.
- At least one traversable path connects start to goal.
- Points of interest do not overlap illegally.
- Biomes and region types belong to the allowed vocabulary.

This keeps the project reliable and prevents the LLM from silently breaking core gameplay logic.[cite:1][cite:2]

## MVP scope

For the first version, the map generator should stay modest. The fog-of-war notes recommend an 8x8 or 10x10 world with one road, one forest region, one town, one destination, and a small set of clue sources, which is enough to make exploration feel richer without making the system hard to debug.[cite:2]

A good MVP implementation would include:

- One reusable map-generation prompt.
- One validator function.
- One fallback handcrafted map.
- A conversion step from generated JSON into canonical game state.
- Support for named locations and clue hooks.

That scope stays consistent with the project roadmap, which favors a small playable core first and adds richer systems only after the base loop is dependable.[cite:1]

## Suggested file structure

A practical file split for this feature would be:

- `mapgen.py` — builds the prompt and requests a structured map from the LLM.
- `map_validator.py` — validates schema, bounds, and connectivity.
- `data/maps.py` — stores handcrafted fallback maps and approved generated maps.[cite:1]
- `llm.py` — keeps narrative generation separate from map generation.[cite:1][cite:2]

This separation preserves the architecture already outlined in the project notes and makes the repository easier to explain on GitHub as an example of grounded AI-assisted game design.[cite:1][cite:2]
