# Transforming `GameState` into an LLM Prompt

`GameState` should not be sent directly to the language model as a raw dump in most cases. A better pattern is to keep `GameState` as the engine's canonical structured state, then convert only the relevant parts into a compact prompt context for narration.[cite:1][cite:2]

## Why transform instead of dumping

The project architecture separates mechanical truth from narration: the game engine decides what happened, while the LLM explains it in natural language.[cite:2] The fog-of-war design follows the same principle and recommends building a filtered “player knowledge” section rather than sending uncontrolled raw state every turn.[cite:1]

This matters because `GameState` contains implementation-friendly data structures such as coordinates, boolean discovery grids, inventories, and status flags. Those are useful for code, but they are not always the clearest or cheapest format for an LLM prompt.[cite:1]

## What `GameState` contains

In the current module, `GameState` stores map size, player position, goal position, turn count, log entries, inventory, status flags, and discovered tiles.[cite:3] It also applies resolved `MoveResult` objects, which means it is meant to hold committed game truth rather than free-form narration state.[cite:3]

A practical prompt builder should therefore treat `GameState` as the source of facts and select only the facts that matter for the current turn. This keeps prompts smaller, more stable, and easier for the model to follow.[cite:1][cite:2]

## World truth versus player knowledge

The most important distinction is that hidden engine facts and player-facing knowledge are not the same thing. The fog-of-war architecture explicitly separates world truth from what the player has seen, heard, or inferred so far.[cite:1]

That means values like `goal_pos` may exist in `GameState` for mechanics while still being unknown to the player. If the player does not know the exact destination coordinates, those coordinates should not appear inside the player-knowledge block.[cite:1]

For example, this would be incorrect if the goal is hidden:

```text
Player knowledge
- Objective: reach the goal at (5, 5).
```

A better version would express the objective only as the player understands it:

```text
Player knowledge
- Current objective: find the tavern said to lie east of the forest.
```

If the model still needs the hidden truth for grounding, that fact should belong in a separate world-truth or engine-truth section, not in player knowledge.[cite:1]

## Recommended transformation flow

A good pipeline is:

1. Read the current `GameState`.
2. Separate hidden engine facts from player-visible knowledge.
3. Select only the fields relevant to the current turn.
4. Convert those fields into short natural-language lines.
5. Combine them with the current action and the mechanical move result.
6. Pass that compact context into the LLM prompt.[cite:1]

This follows the roadmap idea of injecting dynamic variables such as action, biome, memory, and state, while keeping the prompt short enough for a turn-based loop.[cite:2]

## What to include in player knowledge

The most useful `GameState`-derived facts for a player-knowledge block are usually:

- **Current position or local description**: where the player is now, expressed in player-facing terms when possible.[cite:1][cite:3]
- **Objective as understood by the player**: not necessarily the hidden true goal coordinates.[cite:1]
- **Recent log items**: a short memory of meaningful recent events.[cite:1][cite:2][cite:3]
- **Inventory**: only items that matter to the current narration or options.[cite:2][cite:3]
- **Status flags**: current conditions or knowledge flags such as `poisoned`, `heard_rumor`, or `has_torch_lit`.[cite:3]
- **Discovery or fog-of-war state**: summarized as what the player currently knows or sees, not as a raw grid dump.[cite:1][cite:3]

The full `discovered` grid usually should not be inserted into the prompt directly. Instead, it should be summarized into statements such as “the player has explored the road west of the forest” or “the ruins are known but not yet entered.”[cite:1]

## What to avoid sending directly

Some `GameState` fields are too raw to be prompt-ready without conversion. For example, a 2D `discovered` boolean matrix is ideal for rendering and logic, but it is not a natural format for narration.[cite:3]

The same is true for raw dictionaries when they are large or noisy. A compact sentence like “The player carries a rusty key and a torch” is usually more useful to the model than `{"rusty_key": 1, "torch": 1}` unless the prompt is explicitly designed around structured JSON.[cite:1]

It is also important not to leak hidden truths into the player-knowledge section by accident. If `goal_pos = (5, 5)` is only known by the engine, then the serializer should not expose it as though the player already knows it.[cite:1]

## Turning fields into player knowledge

The fog-of-war architecture recommends a “player knowledge” block that includes only facts the player can reasonably know at that turn.[cite:1] That means the prompt should distinguish between world truth held by the engine and player-facing knowledge derived from `GameState` plus recent resolved events.[cite:1]

A simple example transformation might look like this:

### Raw state

```python
state.player_pos = (2, 3)
state.goal_pos = (5, 5)
state.inventory = {"rusty_key": 1, "torch": 1}
state.status = {"poisoned": True, "heard_tavern_rumor": True}
state.log = [
    "Found muddy tracks near the road.",
    "A wolf blocked the eastern path.",
    "You lit your torch."
]
```

### Incorrect player-knowledge version

```text
Player knowledge
- Current location: road tile at (2, 3).
- Objective: reach the goal at (5, 5).
- Inventory: a rusty key and a lit torch.
- Current condition: poisoned.
- Known rumor: there may be a tavern nearby.
- Recent events: muddy tracks were found; a wolf blocked the eastern path; the torch is now lit.
```

The problem is that the second line exposes hidden engine truth as if the player already knew it.[cite:1]

### Corrected player-knowledge version

```text
Player knowledge
- Current location: on the road near the forest edge.
- Current condition: poisoned.
- Inventory: a rusty key and a lit torch.
- Known rumor: there may be a tavern somewhere east of the forest.
- Recent events: muddy tracks were found; a wolf blocked the eastern path; the torch is now lit.
- Current objective: follow clues toward the rumored tavern.
```

This version is better aligned with the narration layer because it is shorter, clearer, and organized around what the player actually knows.[cite:1]

## Role of the `status` field

The `status` field in `GameState` is a good place for compact persistent flags that are not inventory items and not just one-off log text, such as conditions, temporary effects, or remembered facts.[cite:3] Examples include `poisoned`, `blessed`, `has_torch_lit`, `met_guard`, or `heard_tavern_rumor`.[cite:3]

When transferred to the prompt, `status` should usually be filtered and translated into plain language. Only active or relevant flags should be included on a given turn.[cite:1]

## Example serializer function

A practical serializer can convert `GameState` into a prompt context string while avoiding leakage of hidden engine facts:

```python
def build_player_knowledge(state) -> str:
    lines = []

    lines.append("- Current location: on the road near the forest edge.")

    if state.inventory:
        items = ", ".join(
            f"{name} x{qty}" for name, qty in state.inventory.items()
        )
        lines.append(f"- Inventory: {items}.")

    active_status = []
    if state.status.get("poisoned"):
        active_status.append("poisoned")
    if state.status.get("has_torch_lit"):
        active_status.append("carrying a lit torch")
    if state.status.get("heard_tavern_rumor"):
        active_status.append("heard a rumor about a tavern east of the forest")

    if active_status:
        lines.append("- Status: " + "; ".join(active_status) + ".")

    if state.log:
        recent = " | ".join(state.log[-3:])
        lines.append(f"- Recent events: {recent}")

    lines.append("- Current objective: follow clues toward the rumored tavern.")

    return "\n".join(lines)
```

This pattern matches the design recommendation to serialize a curated subset of state into compact natural language instead of exposing the whole raw data structure.[cite:1]

## Using `MoveResult` with the prompt

Because `GameState` applies resolved `MoveResult` objects, the prompt can also include the current action and its mechanical result separately.[cite:3] This is useful because the model should narrate what actually happened, not decide the outcome itself.[cite:1][cite:2]

For example, the final prompt input might contain:

```text
Current turn input
- Intended action: move east.
- Mechanical result: blocked by wolf encounter, player remains in place.
- Nearby visible features: road, forest edge, muddy tracks.
```

That structure is explicitly aligned with the fog-of-war prompt design, where the engine provides the final mechanical truth and the LLM turns it into grounded narration.[cite:1]

## Suggested prompt structure

A strong prompt can be split into four parts:

1. **Narrator role**: tone and brevity rules.[cite:1]
2. **World truth**: stable map facts and hidden constraints from the engine.[cite:1]
3. **Player knowledge**: a summary derived from `GameState` that includes only what the player knows.[cite:1][cite:3]
4. **Current turn input**: intended action plus resolved result.[cite:1][cite:3]

That structure keeps the model grounded while preserving the engine-first design recommended in the project roadmap.[cite:1][cite:2]

## Practical advice

When building the first MVP, keep the transformation simple. Start by serializing position in player-facing terms, the last 3 log messages, a short inventory summary, and a filtered subset of status flags.[cite:1][cite:2]

If the real objective is hidden, do not serialize exact goal coordinates into player knowledge. Instead, serialize the objective as rumor, clue, mission text, or partial understanding, and keep the exact destination only in engine-side world truth when needed.[cite:1]

After that works, the serializer can become more sophisticated by distinguishing confirmed facts, rumors, recent events, and visible surroundings. That is especially useful in a fog-of-war design, because the prompt should reflect only what the player actually knows, not everything stored in the world model.[cite:1]
