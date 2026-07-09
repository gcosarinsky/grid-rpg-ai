# Fog of War Map + LLM World Knowledge Sketch

This document sketches a practical architecture for an LLM-driven RPG that uses fog of war on the player-facing map while still letting the narrative model reason over the full world state.[cite:13][cite:1]

## Core idea

The best pattern is to separate **world truth** from **player knowledge**. The engine keeps a complete canonical map with terrain, landmarks, roads, and named places, while the UI reveals only explored or partially known areas through fog of war.[cite:13][cite:1]

This allows the LLM to generate grounded hints such as "there is said to be a town east of the forest" without inventing geography on the fly. It also preserves exploration, because the player does not automatically see everything the model knows.[cite:1]

## Recommended map layers

A clean implementation should use multiple layers rather than a single grid.[cite:1][cite:13]

| Layer | Purpose | Visible to player | Sent to LLM |
|---|---|---:|---:|
| `world_map` | Full terrain and topology, including roads, rivers, forests, settlements, dungeons, and obstacles | No | Yes [cite:13] |
| `poi_index` | Structured named locations and metadata, such as tavern, shrine, ruins, forest, or town | No | Yes [cite:1] |
| `fog_map` | Discovery state per tile: hidden, seen, visited | Yes | Yes [cite:1] |
| `knowledge_log` | Rumors, signs, NPC hints, discovered names, and resolved clues | Partly | Yes [cite:1] |
| `event_layer` | Engine-defined events or encounters attached to zones or tiles | No, except when triggered | Yes [cite:1] |

## Engine rule

The engine should own all hard facts. This follows the same rule already identified for movement and events: the rules system decides what is true, what is reachable, and what happened mechanically; the LLM narrates those facts in natural language.[cite:1]

That means the LLM must not invent new towns, move landmarks, create secret shortcuts, or contradict map topology. It can phrase uncertainty in-character, but the underlying hint must come from structured world data.[cite:1]

## Data model sketch

A simple Python-friendly structure could look like this.[cite:13][cite:1]

```python
world = {
    "size": {"width": 10, "height": 10},
    "tiles": [[...]],
    "regions": [
        {"id": "blackwood", "type": "forest", "bounds": [(3,2), (5,4)]},
        {"id": "old_road", "type": "road", "path": [(0,3), (1,3), (2,3), (3,3)]}
    ],
    "pois": {
        "dunmere": {
            "kind": "town",
            "position": [6,3],
            "tags": ["settlement", "supplies"],
            "hintable_from": ["road_npc", "signpost"]
        },
        "tavern_red_hart": {
            "kind": "tavern",
            "position": [7,3],
            "inside": "dunmere"
        }
    }
}

player_state = {
    "position": [2,3],
    "facing": "east",
    "biome": "road",
    "visited": [[False, ...]],
    "seen": [[True, ...]],
    "seen_pois": ["Blackwood Forest"],
    "known_facts": [
        "A trader mentioned a town east of Blackwood.",
        "The old road continues through the forest edge."
    ],
    "recent_events": [
        "Blocked by wolves near the tree line.",
        "Found cart tracks on the road."
    ],
    "objective": "Find the tavern in Dunmere"
}
```

## Visibility model

For the MVP, the fog system can stay simple.[cite:1]

- `hidden`: the tile has never been seen, shown as dark or blank.[cite:1]
- `seen`: the tile was observed before but is not currently in vision, shown dimmed.[cite:1]
- `visited`: the tile is currently known from direct exploration, shown clearly.[cite:1]
- Optional `rumored`: not visible on the map, but represented in text or journal as an uncertain clue.[cite:1]

That last state is useful because it lets the narrative layer mention places before the UI reveals exact positions. A rumor can exist as text first, then become a visible landmark when the player gets close enough.[cite:1]

## Prompt architecture

The prompt should include a compact world summary, not an uncontrolled dump of every raw tile every turn. This matches the earlier prompt-optimization direction in the project notes, where dynamic variables and selected context are preferred over bloated history.[cite:13]

A strong system prompt setup can be split into four blocks.[cite:13][cite:1]

1. **Narrator role**: dark, concise dungeon-master style; brief responses.[cite:13]
2. **World truth**: authoritative structured facts about map regions, landmarks, adjacency, and goal state.[cite:13]
3. **Player knowledge**: what the character has seen, heard, or inferred so far.[cite:1]
4. **Narration limits**: never invent geography, never override engine results, never reveal hidden map details unless a clue source justifies it.[cite:1]

## Building player knowledge

The player-knowledge section should be generated from the state dict as a filtered summary, not by dumping raw JSON into the prompt. This follows the same prompt-optimization principle from the project outline: inject relevant state, memory, and action variables while keeping the context small and coherent.[cite:13][cite:1]

A good player-knowledge block should include only facts the player can reasonably know at that turn.[cite:1]

- Immediate perception: current position, biome, nearby visible features, and active encounter.[cite:13]
- Stable discoveries: named places seen, roads found, regions entered, and clues already confirmed.[cite:1]
- Recent memory: the last 3 to 5 meaningful events, which fits the earlier "memory lite" MVP direction.[cite:1]
- Goal awareness: the current objective as the player understands it.[cite:1]

A useful distinction is to separate **confirmed** knowledge from **rumors**. That helps the LLM speak with the right certainty level, so a place heard from a trader is phrased as hearsay while a visited place is described as fact.[cite:1]

## Serialization example

The transformation from dict data to prompt text can be simple and explicit.[cite:13][cite:1]

Given a state like this:

```python
player_state = {
    "position": [2, 3],
    "biome": "road",
    "seen_pois": ["Blackwood Forest"],
    "known_facts": [
        "A trader said a town lies east of Blackwood.",
        "Wolves roam near the tree line at dusk."
    ],
    "recent_events": [
        "Found cart tracks on the road.",
        "A wolf blocked the eastern path."
    ],
    "objective": "Find the tavern in Dunmere"
}
```

A compact prompt block could be rendered as:

```text
Player knowledge:
- Current location: on the old road at (2,3), beside the forest edge.
- Known places: Blackwood Forest.
- Known rumors: A trader said a town lies east of Blackwood; wolves roam near the tree line at dusk.
- Recent events: Found cart tracks on the road; a wolf blocked the eastern path.
- Current objective: Find the tavern in Dunmere.
```

This is usually better than raw JSON because it is shorter, easier for the model to parse, and easier to control from turn to turn.[cite:13][cite:1]

## Serializer function sketch

A basic serializer can convert a curated subset of the state dict into the final prompt section.[cite:13][cite:1]

```python
def build_player_knowledge(player_state):
    position = tuple(player_state.get("position", ["?", "?"]))
    biome = player_state.get("biome", "unknown terrain")
    seen_pois = player_state.get("seen_pois", [])
    known_facts = player_state.get("known_facts", [])
    recent_events = player_state.get("recent_events", [])
    objective = player_state.get("objective", "No clear objective")

    lines = ["Player knowledge:"]
    lines.append(f"- Current location: {biome} at {position}.")

    if seen_pois:
        lines.append(f"- Known places: {', '.join(seen_pois)}.")
    if known_facts:
        lines.append(f"- Known rumors: {'; '.join(known_facts[:3])}.")
    if recent_events:
        lines.append(f"- Recent events: {'; '.join(recent_events[-3:])}.")

    lines.append(f"- Current objective: {objective}.")
    return "\n".join(lines)
```

This pattern works well with `st.session_state` because the game can store much more state than the LLM actually needs on a single turn, then serialize only the most relevant subset into the prompt.[cite:13][cite:1]

## Certainty-aware format

A stronger version is to group the knowledge by certainty level. This makes it easier for the model to distinguish between direct knowledge and hearsay.[cite:1]

```text
Player knowledge:
Confirmed:
- The player is on the old road west of Blackwood.
- The player has seen the forest edge.

Rumors:
- A trader claimed there is a town east of Blackwood.

Recent turn memory:
- Cart tracks were found on the road.
- A wolf blocked movement to the east.

Objective:
- Reach the tavern in Dunmere.
```

This structure is especially useful in a fog-of-war game because it lets the model mention uncertain places without treating them as directly observed map facts.[cite:1]

## System prompt sketch

```text
You are the narrator of a turn-based exploration RPG.

Your job is to narrate events, hints, NPC dialogue, and environmental descriptions.
You must remain consistent with the world data provided below.

Rules:
- Do not invent new towns, roads, forests, or landmarks.
- Do not change coordinates or relative directions.
- Do not decide movement success or failure; the engine decides that.
- If giving a hint, base it only on known world facts or the current clue source.
- If the player has not discovered a place directly, mention it as rumor, memory, sign, or hearsay.
- Keep outputs under 3 short paragraphs.

World truth:
- Blackwood is a forest occupying the central-east zone.
- Dunmere lies east of Blackwood.
- The old road skirts the northern edge of Blackwood and continues toward Dunmere.
- Wolves are active near the tree line.

Player knowledge:
Confirmed:
- The player is on the old road west of Blackwood.
- The player has seen the forest edge.

Rumors:
- The player previously heard that a town may lie east of the forest.

Recent turn memory:
- Cart tracks were found on the road.
- A wolf blocked movement to the east.

Objective:
- Find the tavern in Dunmere.

Current turn input:
- Intended action: move east.
- Mechanical result from engine: blocked by wolf encounter, player remains in place.
- Nearby visible features: road, forest edge, cart tracks.

Narration goal:
Describe the failed advance and provide one grounded hint if appropriate.
```

## Hint generation pattern

Hints should be emitted from data, not improvised. A useful pipeline is.[cite:1]

1. The engine selects a clue source, such as NPC, signpost, tracks, ruined milestone, or shrine inscription.[cite:1]
2. The engine chooses a valid target fact from `poi_index` or regional topology.[cite:1]
3. The prompt exposes only that fact and the source context to the LLM.[cite:1]
4. The LLM turns it into natural dialogue or narration.[cite:1]

Example transformations:

| Source | Structured fact | Possible narration |
|---|---|---|
| Road traveler | `dunmere is east of blackwood` | "A weary traveler swears a town lies east of the forest, where the road grows quieter." [cite:1] |
| Signpost | `old road -> dunmere` | "A rotten sign leans toward the trees; beneath the moss, one name is still legible: Dunmere." [cite:1] |
| Hunter | `wolves near forest edge` | "The hunter warns that the tree line is restless tonight, and safer paths cling to the road." [cite:1] |

## UI sketch

The player-facing map should communicate uncertainty clearly.[cite:1]

- Current tile: bright marker.[cite:1]
- Adjacent visible tiles: full color.[cite:1]
- Previously seen tiles: desaturated or darkened.[cite:1]
- Hidden tiles: opaque fog.[cite:1]
- Rumors and discovered landmarks: shown in a side journal, not necessarily pinned to exact coordinates yet.[cite:1]

A useful interface split would be:
- Left panel: map with fog of war.[cite:1]
- Right panel: narrative log, current objective, known rumors, and recent discoveries.[cite:1]
- Bottom controls: movement buttons and optional `inspect` or `ask` actions.[cite:1]

## MVP scope

The safest first implementation is still modest: an 8x8 or 10x10 map, one forest region, one road, one town, one destination, and a handful of clue sources. This keeps the project small enough to finish while making the exploration system feel much richer than a fully visible 6x6 grid.[cite:1][cite:13]

A good MVP checklist is:
- Deterministic world map stored in code.[cite:13]
- Fog-of-war rendering with `hidden`, `seen`, and `visited` states.[cite:1]
- One or two named locations in `poi_index`.[cite:1]
- Engine-generated clues tied to real places.[cite:1]
- LLM prompt fed with world truth plus player knowledge, not raw unrestricted history.[cite:13]
- A serializer function that converts state dicts into compact prompt sections.[cite:13][cite:1]

## Key principle

The strongest version of this project is not "the LLM imagines a map." It is "the engine owns the world, and the LLM speaks about that world elegantly and consistently." That makes the demo more believable as an AI systems project because it shows control, grounding, and state-aware narration rather than freeform text generation alone.[cite:1]
