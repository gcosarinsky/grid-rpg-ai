from pathlib import Path

from streamlit.testing.v1 import AppTest

import grid_rpg_ai.llm as llm


APP_PATH = str(Path(__file__).resolve().parents[1] / "examples" / "debug_app.py")


def click_button(app, label):
    next(button for button in app.button if button.label == label).click().run()


def test_narration_uses_selected_model_only_for_moves(monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "list_ollama_models", lambda: ["one:latest", "two:latest"])

    def generate(provider, prompt):
        calls.append((provider.model, prompt))
        return "Una senda se abre ante ti."

    monkeypatch.setattr(llm.OllamaProvider, "generate", generate)
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert not app.exception
    assert app.selectbox(key="ollama_model").options == ["one:latest", "two:latest"]
    assert calls == []

    app.selectbox(key="ollama_model").select("two:latest").run()
    app.checkbox(key="narration_enabled").check().run()
    app.checkbox(key="events_enabled").uncheck().run()
    assert calls == []
    click_button(app, "➡️")

    assert not app.exception
    assert len(calls) == 1
    assert calls[0][0] == "two:latest"
    assert "Final position: (1, 0)" in calls[0][1]
    assert "Una senda se abre ante ti." in app.session_state["narration_response"].text
    assert app.session_state["game_state"].turn == 1

    app.slider[0].set_value(3).run()
    assert len(calls) == 1
    click_button(app, "Reset game")
    assert app.session_state["narration_response"] is None


def test_unavailable_ollama_falls_back_and_start_refreshes_models(monkeypatch):
    def unavailable():
        raise llm.OllamaUnavailable("offline")

    monkeypatch.setattr(llm, "list_ollama_models", unavailable)
    monkeypatch.setattr(llm, "start_ollama", lambda: ["local:latest"])
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert not app.exception
    assert any("offline" in warning.value for warning in app.warning)

    app.checkbox(key="narration_enabled").check().run()
    click_button(app, "➡️")
    assert app.session_state["game_state"].turn == 1
    assert app.session_state["narration_response"].used_fallback
    assert any("deterministic fallback" in warning.value for warning in app.warning)

    app.button(key="ollama_start").click().run()
    assert not app.exception
    assert app.selectbox(key="ollama_model").options == ["local:latest"]
    assert app.selectbox(key="ollama_model").value == "local:latest"


def test_failed_narration_preserves_turn_and_surfaces_error(monkeypatch):
    monkeypatch.setattr(llm, "list_ollama_models", lambda: ["local:latest"])

    def fail(provider, prompt):
        raise llm.NarrationError("model failure")

    monkeypatch.setattr(llm.OllamaProvider, "generate", fail)
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    app.checkbox(key="narration_enabled").check().run()
    click_button(app, "➡️")

    assert not app.exception
    assert app.session_state["game_state"].turn == 1
    assert app.session_state["narration_response"].used_fallback
    assert any("model failure" in warning.value for warning in app.warning)


def test_refresh_updates_model_selector_and_handles_empty_list(monkeypatch):
    installed = ["first:latest", "second:latest"]
    monkeypatch.setattr(llm, "list_ollama_models", lambda: installed.copy())
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    app.selectbox(key="ollama_model").select("second:latest").run()

    installed[:] = ["first:latest", "third:latest"]
    app.button(key="ollama_check").click().run()
    assert not app.exception
    assert app.selectbox(key="ollama_model").options == installed
    assert app.selectbox(key="ollama_model").value == "first:latest"

    installed.clear()
    app.button(key="ollama_check").click().run()
    assert not app.exception
    assert app.selectbox(key="ollama_model").disabled
    assert any("No models are installed" in info.value for info in app.info)
