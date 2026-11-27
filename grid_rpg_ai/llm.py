from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from typing import Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .data.maps import MapData
from .gamestate import GameState, MoveResult, Position
from .localization import Language, normalize_language

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_RECENT_LOG_ENTRIES = 5
ENVIRONMENT_CUES: dict[str, dict[Language, str]] = {
    "plains": {"en": "grass and open ground", "es": "hierba y terreno abierto"},
    "forest": {"en": "trees and undergrowth", "es": "árboles y maleza"},
    "swamp": {"en": "mud and standing water", "es": "barro y agua estancada"},
    "desert": {"en": "sand and dry ground", "es": "arena y suelo seco"},
    "hill": {"en": "sloping ground", "es": "terreno inclinado"},
    "road": {"en": "a traveled path", "es": "una ruta transitada"},
    "ruins": {"en": "old broken stones", "es": "piedras antiguas y rotas"},
    "lake": {"en": "a body of water", "es": "una extensión de agua"},
    "mountain": {"en": "rocky heights", "es": "alturas rocosas"},
}


@dataclass(frozen=True)
class NarrationContext:
    action: str
    biome: str
    move_result: MoveResult
    player_pos: Position
    inventory: Mapping[str, int]
    status: Mapping[str, bool]
    recent_log: tuple[str, ...]
    objective_description: str
    language: Language


@dataclass(frozen=True)
class NarrationResponse:
    text: str
    used_fallback: bool
    error: str | None = None


class NarrationError(Exception):
    """Raised when a narration provider cannot return a usable response."""


class OllamaUnavailable(NarrationError):
    """Raised when the local Ollama server cannot be reached."""


def list_ollama_models(timeout: float = 2.0) -> list[str]:
    """Check the local server and return the names of its installed models."""
    try:
        with urlopen(f"{DEFAULT_OLLAMA_URL}/api/tags", timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise NarrationError(f"Ollama returned HTTP {exc.code}: {exc.reason}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise OllamaUnavailable(f"Could not connect to Ollama: {exc}") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise NarrationError(f"Ollama returned an invalid model list: {exc}") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
        raise NarrationError("Ollama returned an invalid model list.")
    names = []
    for model in payload["models"]:
        if not isinstance(model, dict) or not isinstance(model.get("name"), str) or not model["name"]:
            raise NarrationError("Ollama returned an invalid model name.")
        names.append(model["name"])
    return sorted(set(names))


def start_ollama() -> list[str]:
    """Start the local server if needed, and wait briefly for it to respond."""
    try:
        return list_ollama_models()
    except OllamaUnavailable:
        pass

    try:
        process = subprocess.Popen(["ollama", "serve"], stdin=subprocess.DEVNULL)
    except OSError as exc:
        raise NarrationError(f"Could not start Ollama: {exc}") from exc

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            return list_ollama_models(timeout=1.0)
        except OllamaUnavailable:
            exit_code = process.poll()
            if exit_code is not None:
                raise NarrationError(
                    f"Ollama exited with code {exit_code}; check the application terminal."
                )
            time.sleep(0.25)
    raise NarrationError(
        "Ollama did not become available within 10 seconds; check the application terminal."
    )


class NarrationProvider(Protocol):
    def generate(self, prompt: str) -> str:
        """Generate narration from a grounded prompt."""


def build_narration_context(
    state: GameState,
    game_map: MapData,
    move_result: MoveResult,
    language: Language,
    objective_description: str | None = None,
) -> NarrationContext:
    """Build a compact, player-facing context without exposing hidden goal data."""
    language = normalize_language(language)
    final_x, final_y = move_result.final_pos
    if objective_description is None:
        objective_description = (
            "Encuentra el objetivo oculto."
            if language == "es"
            else "Find the hidden objective."
        )
    return NarrationContext(
        action=move_result.intended_direction,
        biome=game_map.biome_at(final_x, final_y).key,
        move_result=move_result,
        player_pos=move_result.final_pos,
        inventory=dict(state.inventory),
        status={key: value for key, value in state.status.items() if value},
        recent_log=tuple(state.log[-MAX_RECENT_LOG_ENTRIES:]),
        objective_description=objective_description,
        language=language,
    )


def build_narration_prompt(context: NarrationContext) -> str:
    """Create a short prompt grounded only in supplied, player-visible facts."""
    language_name = "English" if context.language == "en" else "Spanish"
    result = context.move_result
    if not result.success:
        movement_outcome = "blocked; the player stays in place"
    elif result.final_pos != result.attempted_pos:
        movement_outcome = "detoured to a different position"
    else:
        movement_outcome = "reached the intended position"
    if context.language == "es":
        style_examples = (
            '- Successful movement: "Avanzas mientras la hierba se mece a tu paso."\n'
            '- Blocked movement: "El paso se cierra ante ti y te obliga a detenerte."'
        )
    else:
        style_examples = (
            '- Successful movement: "You press on as the grass sways around you."\n'
            '- Blocked movement: "The path closes before you, forcing you to stop."'
        )
    inventory = ", ".join(
        f"{item} x{quantity}" for item, quantity in context.inventory.items()
    ) or "empty"
    status = ", ".join(
        key for key, active in context.status.items() if active
    ) or "none"
    recent_log = "\n".join(f"- {entry}" for entry in context.recent_log) or "- none"

    return (
        "You are the narrator of a grid-based adventure. Write 1-3 concise "
        "sentences in "
        f"{language_name}. Narrate only the resolved result below; never change "
        "game rules, invent outcomes, or reveal hidden map information. "
        "Use an evocative, literary style with subtle sensory details appropriate "
        "to the surroundings. Never state coordinates, grid positions, or the "
        "biome's name in the narration; evoke the surroundings without naming "
        "their biome. Do not invent discoveries, encounters, items, or changes "
        "to the objective.\n\n"
        "Style examples only; do not copy their facts into the current turn:\n"
        f"{style_examples}\n\n"
        "Player-facing objective:\n"
        f"{context.objective_description}\n\n"
        "Resolved turn:\n"
        f"- Action: move {context.action}\n"
        f"- Environmental cues: {ENVIRONMENT_CUES[context.biome][context.language]}\n"
        f"- Movement succeeded: {result.success}\n"
        f"- Movement outcome: {movement_outcome}\n"
        f"- Final position: {context.player_pos}\n"
        f"- Event: {result.event_text or 'none'}\n"
        f"- Inventory: {inventory}\n"
        f"- Active status: {status}\n"
        f"- Recent log:\n{recent_log}\n"
    )


def deterministic_fallback(context: NarrationContext) -> str:
    """Return a short deterministic narration for unavailable providers."""
    result = context.move_result
    direction = context.action
    if context.language == "es":
        direction = {
            "up": "hacia el norte",
            "down": "hacia el sur",
            "left": "hacia el oeste",
            "right": "hacia el este",
        }.get(direction, direction)
    else:
        direction = {
            "up": "north",
            "down": "south",
            "left": "west",
            "right": "east",
        }.get(direction, direction)

    if not result.success:
        if context.language == "es":
            base = "El camino se interrumpe y permaneces donde estás."
        else:
            base = "The way is blocked, and you remain where you are."
        if result.event_text and result.event_type not in {
            "out_of_bounds",
            "blocked_terrain",
        }:
            return f"{base} {result.event_text}"
        return base

    if result.final_pos != result.attempted_pos:
        if context.language == "es":
            base = "Un desvío altera tu ruta, pero alcanzas otra zona cercana."
        else:
            base = "A sudden detour alters your route, but you reach a nearby area."
        return f"{base} {result.event_text or ''}".strip()

    if result.event_type and result.event_text:
        return result.event_text

    if context.language == "es":
        return f"Avanzas {direction}."
    return f"You move {direction}."


def generate_narration(
    context: NarrationContext,
    provider: NarrationProvider | None = None,
) -> NarrationResponse:
    """Generate narration, retaining playable deterministic fallback behavior."""
    if provider is None:
        return NarrationResponse(
            text=deterministic_fallback(context),
            used_fallback=True,
        )

    try:
        narration = provider.generate(build_narration_prompt(context)).strip()
    except NarrationError as exc:
        return NarrationResponse(
            text=deterministic_fallback(context),
            used_fallback=True,
            error=str(exc),
        )

    if not narration:
        error = "Narration provider returned an empty response."
        return NarrationResponse(
            text=deterministic_fallback(context),
            used_fallback=True,
            error=error,
        )
    return NarrationResponse(text=narration, used_fallback=False)


@dataclass(frozen=True)
class OllamaProvider:
    model: str = DEFAULT_OLLAMA_MODEL
    base_url: str = DEFAULT_OLLAMA_URL
    timeout: float = DEFAULT_TIMEOUT_SECONDS

    def generate(self, prompt: str) -> str:
        request = Request(
            f"{self.base_url.rstrip('/')}/api/generate",
            data=json.dumps(
                {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 160},
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise NarrationError(
                f"Ollama returned HTTP {exc.code}: {exc.reason}"
            ) from exc
        except (URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise NarrationError(f"Could not get narration from Ollama: {exc}") from exc

        if not isinstance(payload, dict):
            raise NarrationError("Ollama returned an invalid response payload.")
        narration = payload.get("response")
        if not isinstance(narration, str) or not narration.strip():
            raise NarrationError("Ollama returned an invalid or empty response.")
        return narration.strip()
