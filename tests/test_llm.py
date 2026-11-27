import importlib.util
import json
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request

import pytest

import grid_rpg_ai.llm as llm
from grid_rpg_ai.data.maps import create_map_from_grid
from grid_rpg_ai.gamestate import GameState, MoveResult
from grid_rpg_ai.llm import (
    NarrationError,
    OllamaProvider,
    OllamaUnavailable,
    build_narration_context,
    build_narration_prompt,
    deterministic_fallback,
    generate_narration,
    list_ollama_models,
    start_ollama,
)

spec = importlib.util.spec_from_file_location(
    "narration_demo", Path(__file__).resolve().parents[1] / "examples" / "narration_demo.py"
)
assert spec is not None and spec.loader is not None
narration_demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(narration_demo)


def make_context(language="en", result=None):
    game_map = create_map_from_grid(
        name="narration_test_map",
        grid=[["plains", "forest"], ["road", "ruins"]],
        start=(0, 0),
        goal=(1, 1),
    )
    state = GameState(
        rows=game_map.height,
        cols=game_map.width,
        player_pos=(1, 0),
        goal_pos=game_map.goal,
        log=[f"event {number}" for number in range(7)],
        inventory={"torch": 1},
        status={"heard_rumor": True, "inactive": False},
    )
    move_result = result or MoveResult(
        intended_direction="right",
        attempted_pos=(1, 0),
        final_pos=(1, 0),
        success=True,
    )
    return build_narration_context(state, game_map, move_result, language)


def test_prompt_uses_grounded_context_without_hidden_goal_coordinates():
    context = make_context()

    prompt = build_narration_prompt(context)

    assert "move right" in prompt
    assert "trees and undergrowth" in prompt
    assert "Forest" not in prompt
    assert "torch x1" in prompt
    assert "heard_rumor" in prompt
    assert "event 2" in prompt
    assert "event 6" in prompt
    assert "(1, 1)" not in prompt
    assert "hidden objective" in prompt


def test_provider_failure_returns_fallback_and_surfaces_error():
    class BrokenProvider:
        def generate(self, prompt):
            raise NarrationError("Ollama is unavailable")

    context = make_context()

    response = generate_narration(context, BrokenProvider())

    assert response.text == "You move east."
    assert response.used_fallback is True
    assert response.error == "Ollama is unavailable"


def test_missing_provider_uses_deterministic_fallback():
    response = generate_narration(make_context())

    assert response.text == "You move east."
    assert response.used_fallback is True
    assert response.error is None


def test_spanish_fallback_localizes_direction():
    assert deterministic_fallback(make_context(language="es")) == (
        "Avanzas hacia el este."
    )


def test_prompt_requests_literary_style_without_coordinates_or_biome_names():
    prompt = build_narration_prompt(make_context(language="es"))

    assert "literary style" in prompt
    assert "Never state coordinates, grid positions, or the biome's name" in prompt
    assert "Style examples only" in prompt
    assert "Avanzas mientras la hierba se mece" in prompt
    assert "árboles y maleza" in prompt
    assert "Bosque" not in prompt


def test_prompt_identifies_blocked_and_detoured_outcomes():
    blocked = make_context(result=MoveResult(
        intended_direction="right", attempted_pos=(1, 0), final_pos=(0, 0),
        success=False,
    ))
    detoured = make_context(result=MoveResult(
        intended_direction="right", attempted_pos=(1, 0), final_pos=(0, 0),
        success=True,
    ))

    assert "blocked; the player stays in place" in build_narration_prompt(blocked)
    assert "detoured to a different position" in build_narration_prompt(detoured)


def test_provider_success_uses_generated_text():
    class FakeProvider:
        def __init__(self):
            self.prompt = None

        def generate(self, prompt):
            self.prompt = prompt
            return "The forest stirs around you."

    provider = FakeProvider()
    response = generate_narration(make_context(), provider)

    assert response.text == "The forest stirs around you."
    assert response.used_fallback is False
    assert "Movement succeeded: True" in provider.prompt


def test_deterministic_fallback_describes_blocked_and_detoured_moves():
    blocked = make_context(
        language="es",
        result=MoveResult(
            intended_direction="right",
            attempted_pos=(1, 0),
            final_pos=(0, 0),
            success=False,
            event_type="obstacle",
            event_text="Los lobos te obligan a retroceder.",
        ),
    )
    detoured = make_context(
        result=MoveResult(
            intended_direction="right",
            attempted_pos=(1, 0),
            final_pos=(0, 0),
            success=True,
            event_type="detour",
            event_text="A sandstorm pushes you aside.",
        ),
    )

    assert "permaneces donde estás" in deterministic_fallback(blocked)
    assert "lobos" in deterministic_fallback(blocked)
    assert "detour" in deterministic_fallback(detoured)
    assert "sandstorm" in deterministic_fallback(detoured)


def test_ollama_provider_posts_non_streaming_request(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({"response": "A quiet path opens."}).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("grid_rpg_ai.llm.urlopen", fake_urlopen)
    provider = OllamaProvider(
        model="test-model",
        base_url="http://localhost:11434/",
        timeout=4.0,
    )

    assert provider.generate("Tell the story.") == "A quiet path opens."
    request = captured["request"]
    assert isinstance(request, Request)
    assert request.full_url == "http://localhost:11434/api/generate"
    assert json.loads(request.data) == {
        "model": "test-model",
        "prompt": "Tell the story.",
        "stream": False,
        "options": {"num_predict": 160},
    }
    assert captured["timeout"] == 4.0


def test_list_ollama_models_reads_installed_names(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"models": [{"name": "z:latest"}, {"name": "a:8b"}]}'

    def fake_urlopen(url, timeout):
        assert url == "http://localhost:11434/api/tags"
        assert timeout == 2.0
        return FakeResponse()

    monkeypatch.setattr(llm, "urlopen", fake_urlopen)
    assert list_ollama_models() == ["a:8b", "z:latest"]


def test_list_ollama_models_surfaces_unavailable_server(monkeypatch):
    def fail_urlopen(*args, **kwargs):
        raise URLError("connection refused")

    monkeypatch.setattr(llm, "urlopen", fail_urlopen)
    with pytest.raises(OllamaUnavailable, match="connection refused"):
        list_ollama_models()


def test_list_ollama_models_rejects_malformed_response(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"models": [{"name": 42}]}'

    monkeypatch.setattr(llm, "urlopen", lambda *args, **kwargs: FakeResponse())
    with pytest.raises(NarrationError, match="invalid model name"):
        list_ollama_models()


def test_start_ollama_does_not_launch_a_second_server(monkeypatch):
    monkeypatch.setattr(llm, "list_ollama_models", lambda: ["model:latest"])

    def fail_if_started(*args, **kwargs):
        pytest.fail("An already running server must not be restarted")

    monkeypatch.setattr(llm.subprocess, "Popen", fail_if_started)
    assert start_ollama() == ["model:latest"]


def test_start_ollama_starts_server_and_waits_until_ready(monkeypatch):
    probes = iter([OllamaUnavailable("offline"), ["local:latest"]])
    launches = []

    def probe(*args, **kwargs):
        result = next(probes)
        if isinstance(result, OllamaUnavailable):
            raise result
        return result

    def launch(args, **kwargs):
        launches.append(args)
        return object()

    monkeypatch.setattr(llm, "list_ollama_models", probe)
    monkeypatch.setattr(llm.subprocess, "Popen", launch)
    assert start_ollama() == ["local:latest"]
    assert launches == [["ollama", "serve"]]


def test_start_ollama_surfaces_missing_executable(monkeypatch):
    def unavailable(*args, **kwargs):
        raise OllamaUnavailable("offline")

    def missing(*args, **kwargs):
        raise FileNotFoundError("ollama not found")

    monkeypatch.setattr(llm, "list_ollama_models", unavailable)
    monkeypatch.setattr(llm.subprocess, "Popen", missing)
    with pytest.raises(NarrationError, match="ollama not found"):
        start_ollama()


def test_start_ollama_reports_server_exiting(monkeypatch):
    def unavailable(*args, **kwargs):
        raise OllamaUnavailable("offline")

    class FailedProcess:
        def poll(self):
            return 1

    monkeypatch.setattr(llm, "list_ollama_models", unavailable)
    monkeypatch.setattr(llm.subprocess, "Popen", lambda *args, **kwargs: FailedProcess())
    with pytest.raises(NarrationError, match="exited with code 1"):
        start_ollama()


def test_narration_demo_shows_the_prompt_sent_and_response(monkeypatch, capsys):
    seen = {}

    def fake_generate(provider, prompt):
        seen["model"] = provider.model
        seen["prompt"] = prompt
        seen["before_request"] = capsys.readouterr().out
        return "Una senda se abre ante ti."

    monkeypatch.setattr(narration_demo.OllamaProvider, "generate", fake_generate)
    monkeypatch.setattr(sys, "argv", ["narration_demo.py", "--model", "test-model"])

    assert narration_demo.main() == 0
    after_request = capsys.readouterr().out
    assert seen["model"] == "test-model"
    assert seen["prompt"] in seen["before_request"]
    assert "Spanish" in seen["prompt"]
    assert "=== Respuesta ===" in after_request
    assert "Una senda se abre ante ti." in after_request


def test_narration_demo_reports_provider_errors(monkeypatch, capsys):
    def fail_generate(provider, prompt):
        raise NarrationError("Ollama unavailable")

    monkeypatch.setattr(narration_demo.OllamaProvider, "generate", fail_generate)
    monkeypatch.setattr(sys, "argv", ["narration_demo.py"])

    assert narration_demo.main() == 1
    captured = capsys.readouterr()
    assert "=== Prompt ===" in captured.out
    assert "Ollama unavailable" in captured.err
    assert "=== Respuesta ===" not in captured.out
