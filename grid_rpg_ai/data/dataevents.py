from __future__ import annotations

from dataclasses import dataclass
from random import choice
from typing import Dict, List, Optional

from .biomes import BIOMES


@dataclass(frozen=True)
class Event:
    event_id: str
    biome: str
    event_type: str
    title: str
    effect: str
    description: str
    clue_text: Optional[str] = None


EVENTS_BY_BIOME: Dict[str, List[Event]] = {
    "plains": [
        Event(
            event_id="plains_wind",
            biome="plains",
            event_type="flavor",
            title="Restless Grass",
            effect="none",
            description="The grass bends in waves, and for a moment the open land feels almost watchful.",
        ),
        Event(
            event_id="plains_tracks",
            biome="plains",
            event_type="clue",
            title="Fresh Tracks",
            effect="reveal_hint",
            description="A set of recent footprints crosses the plain toward a safer route.",
            clue_text="Someone passed through here recently; routes with clearer ground may lead onward.",
        ),
    ],
    "forest": [
        Event(
            event_id="forest_wolves",
            biome="forest",
            event_type="obstacle",
            title="Wolves at the Tree Line",
            effect="block_move",
            description="Low growls ripple through the undergrowth and force a retreat from the deeper path.",
        ),
        Event(
            event_id="forest_tracks",
            biome="forest",
            event_type="clue",
            title="Broken Branches",
            effect="reveal_hint",
            description="Snapped twigs and scraped bark suggest that something important passed through not long ago.",
            clue_text="The disturbed trail hints that the objective lies beyond the denser woods.",
        ),
        Event(
            event_id="forest_clearing",
            biome="forest",
            event_type="flavor",
            title="Quiet Clearing",
            effect="none",
            description="A pocket of silence opens between the trees, offering a rare calm moment.",
        ),
    ],
    "swamp": [
        Event(
            event_id="swamp_mud",
            biome="swamp",
            event_type="obstacle",
            title="Sucking Mud",
            effect="block_move",
            description="The ground gives way underfoot and refuses a clean step forward.",
        ),
        Event(
            event_id="swamp_lights",
            biome="swamp",
            event_type="flavor",
            title="Marsh Lights",
            effect="none",
            description="Pale lights drift over the water and vanish when stared at directly.",
        ),
    ],
    "desert": [
        Event(
            event_id="desert_sandstorm",
            biome="desert",
            event_type="detour",
            title="Sand Whip",
            effect="push_random_adjacent",
            description="A sudden wall of sand throws off the route and shoves the traveler aside.",
        ),
        Event(
            event_id="desert_marker",
            biome="desert",
            event_type="clue",
            title="Half-Buried Marker",
            effect="reveal_hint",
            description="A weathered stone marker emerges from the sand with a faint directional carving.",
            clue_text="The worn symbol suggests the destination lies along the more stable approach.",
        ),
    ],
    "hill": [
        Event(
            event_id="hill_vantage",
            biome="hill",
            event_type="goal_clue",
            title="High Vantage",
            effect="reveal_hint",
            description="From higher ground, distant shapes align more clearly than before.",
            clue_text="From here, the objective feels easier to place relative to the surrounding land.",
        ),
        Event(
            event_id="hill_loose_stone",
            biome="hill",
            event_type="flavor",
            title="Loose Stone",
            effect="none",
            description="Pebbles slide underfoot, but the path remains passable.",
        ),
    ],
    "road": [
        Event(
            event_id="road_signpost",
            biome="road",
            event_type="clue",
            title="Old Signpost",
            effect="reveal_hint",
            description="A cracked sign leans beside the road, still useful despite age and moss.",
            clue_text="Travelers once marked this route for a reason; following the road is often safer.",
        ),
        Event(
            event_id="road_traveler",
            biome="road",
            event_type="reward",
            title="Passing Traveler",
            effect="give_clue",
            description="A hurried traveler shares a fragment of useful guidance before moving on.",
            clue_text="The road connects the quieter edges of the wilderness better than the rough ground does.",
        ),
    ],
    "ruins": [
        Event(
            event_id="ruins_inscription",
            biome="ruins",
            event_type="clue",
            title="Ancient Inscription",
            effect="reveal_hint",
            description="Faded markings on broken stone preserve a hint from an older age.",
            clue_text="The ruins point toward a destination once important to those who built them.",
        ),
        Event(
            event_id="ruins_collapse",
            biome="ruins",
            event_type="obstacle",
            title="Falling Masonry",
            effect="block_move",
            description="Loose stone crashes down and cuts off the intended step.",
        ),
    ],
    "lake": [],
    "mountain": [],
}


def validate_events() -> None:
    missing = [biome_key for biome_key in BIOMES if biome_key not in EVENTS_BY_BIOME]
    if missing:
        raise ValueError(f"Missing event definitions for biomes: {missing}")

    for biome_key, events in EVENTS_BY_BIOME.items():
        for event in events:
            if event.biome != biome_key:
                raise ValueError(
                    f"Event {event.event_id!r} biome mismatch: {event.biome!r} != {biome_key!r}"
                )


validate_events()


def get_events_for_biome(biome_key: str) -> List[Event]:
    if biome_key not in EVENTS_BY_BIOME:
        raise ValueError(f"Unknown biome for events: {biome_key!r}")
    return EVENTS_BY_BIOME[biome_key]


def choose_event_for_biome(biome_key: str) -> Optional[Event]:
    events = get_events_for_biome(biome_key)
    if not events:
        return None
    return choice(events)


def event_payload(event: Event) -> Dict[str, Optional[str]]:
    return {
        "event_id": event.event_id,
        "biome": event.biome,
        "event_type": event.event_type,
        "title": event.title,
        "effect": event.effect,
        "description": event.description,
        "clue_text": event.clue_text,
    }
