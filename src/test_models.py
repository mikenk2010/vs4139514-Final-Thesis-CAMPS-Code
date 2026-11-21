"""Provider-adapter regression tests that never call external APIs."""
import json
import sys
from types import SimpleNamespace

import pytest

from models import CacheMiss, ScoringClient, _cache_key


def test_anthropic_v1_call_omits_removed_temperature(monkeypatch, tmp_path):
    """Anthropic SDK v1 rejects sampling parameters on Messages.create."""
    captured = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                content=[SimpleNamespace(text='{"score": 5}')],
                usage=SimpleNamespace(input_tokens=10, output_tokens=4),
            )

    class FakeAnthropic:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.messages = FakeMessages()

    monkeypatch.setitem(
        sys.modules, "anthropic", SimpleNamespace(Anthropic=FakeAnthropic)
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    client = ScoringClient("anthropic", "claude-sonnet-4-6", tmp_path)
    raw, usage = client._call("system prompt", "user prompt")

    assert "temperature" not in captured
    assert captured == {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "system": "system prompt",
        "messages": [{"role": "user", "content": "user prompt"}],
    }
    assert raw == '{"score": 5}'
    assert usage == {"in": 10, "out": 4}


def test_offline_miss_does_not_call_provider(monkeypatch, tmp_path):
    client = ScoringClient("openai", "gpt-4o", tmp_path)

    def boom(*_args, **_kwargs):
        raise AssertionError("offline mode called the provider")

    monkeypatch.setattr(client, "_call", boom)
    with pytest.raises(CacheMiss):
        client.score("essay-1", "western", "system", "user", offline=True)


def test_offline_hit_returns_the_stored_score(monkeypatch, tmp_path):
    client = ScoringClient("openai", "gpt-4o", tmp_path)

    def boom(*_args, **_kwargs):
        raise AssertionError("offline mode called the provider")

    monkeypatch.setattr(client, "_call", boom)
    key = _cache_key("gpt-4o", "western", "essay-1", "system", "user")
    (tmp_path / f"{key}.json").write_text(json.dumps({
        "essay_id": "essay-1", "model": "gpt-4o", "agent": "western",
        "score": 6.0, "rationale": "stored", "raw": "{}", "usage": None,
    }))
    res = client.score("essay-1", "western", "system", "user", offline=True)
    assert res.score == 6.0
    assert res.rationale == "stored"
