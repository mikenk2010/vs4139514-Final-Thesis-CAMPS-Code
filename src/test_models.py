"""Provider-adapter regression tests that never call external APIs."""
import sys
from types import SimpleNamespace

from models import ScoringClient


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
