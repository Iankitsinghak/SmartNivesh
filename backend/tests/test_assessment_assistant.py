from app.services.ai import assistant


def test_assistant_fallback_is_safe_without_a_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = assistant.answer_assessment_question("What should I do next?", "en", {"competition": "UNKNOWN"})
    assert response.generated_by == "safe_fallback"
    assert "source of truth" in response.answer


def test_assistant_uses_only_compact_context(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def read(self):
            return b'{"candidates":[{"content":{"parts":[{"text":"Use the displayed evidence. What to do next: verify locally."}]}}]}'

    monkeypatch.setattr(assistant, "urlopen", lambda *_args, **_kwargs: FakeResponse())
    response = assistant.answer_assessment_question(
        "What should I do next?", "en", {"competition": "UNKNOWN", "secret": "must-not-pass"}
    )
    assert response.generated_by == "gemini"
    assert response.answer.startswith("Use the displayed evidence")
