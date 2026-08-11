"""Provider adapters: deterministic, JSON-scored essay evaluation calls.

Every call: temperature 0.0, JSON response, retried with backoff, and
cached on disk keyed by (model, condition, agent, essay_id, prompt hash),
so re-runs are free and results reproducible.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScoreResult:
    essay_id: str
    model: str
    agent: str
    score: float
    rationale: str
    raw: str


def _cache_key(model_id: str, agent: str, essay_id: str, system_prompt: str,
               user_prompt: str) -> str:
    h = hashlib.sha256(
        "|".join([model_id, agent, essay_id, system_prompt, user_prompt]).encode()
    )
    return h.hexdigest()[:32]


class ScoringClient:
    """Uniform interface over the four providers."""

    def __init__(self, provider: str, model_id: str, cache_dir: Path,
                 max_retries: int = 5) -> None:
        self.provider = provider
        self.model_id = model_id
        self.cache_dir = cache_dir
        self.max_retries = max_retries
        cache_dir.mkdir(parents=True, exist_ok=True)

    def score(self, essay_id: str, agent: str, system_prompt: str,
              user_prompt: str) -> ScoreResult:
        key = _cache_key(self.model_id, agent, essay_id, system_prompt, user_prompt)
        cached = self.cache_dir / f"{key}.json"
        if cached.exists():
            d = json.loads(cached.read_text())
        else:
            raw = self._call_with_retry(system_prompt, user_prompt)
            d = {"essay_id": essay_id, "model": self.model_id, "agent": agent,
                 "raw": raw}
            parsed = json.loads(raw)
            d["score"] = float(parsed["score"])
            d["rationale"] = str(parsed.get("rationale", ""))
            cached.write_text(json.dumps(d, ensure_ascii=False, indent=1))
        return ScoreResult(**{k: d[k] for k in
                              ("essay_id", "model", "agent", "score",
                               "rationale", "raw")})

    def _call_with_retry(self, system_prompt: str, user_prompt: str) -> str:
        delay = 2.0
        for attempt in range(self.max_retries):
            try:
                return self._call(system_prompt, user_prompt)
            except Exception as exc:  # noqa: BLE001 - provider SDK variety
                if attempt == self.max_retries - 1:
                    raise
                print(f"  retry {attempt + 1} after error: {exc}")
                time.sleep(delay)
                delay *= 2
        raise RuntimeError("unreachable")

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            r = client.chat.completions.create(
                model=self.model_id, temperature=0.0,
                response_format={"type": "json_object"},
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": user_prompt}])
            return r.choices[0].message.content
        if self.provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
            r = client.messages.create(
                model=self.model_id, max_tokens=1024, temperature=0.0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}])
            return r.content[0].text
        if self.provider == "google":
            from google import genai
            client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
            r = client.models.generate_content(
                model=self.model_id,
                contents=user_prompt,
                config={"system_instruction": system_prompt, "temperature": 0.0,
                        "response_mime_type": "application/json"})
            return r.text
        if self.provider == "together":
            from openai import OpenAI  # Together exposes an OpenAI-compatible API
            client = OpenAI(api_key=os.environ["TOGETHER_API_KEY"],
                            base_url="https://api.together.xyz/v1")
            r = client.chat.completions.create(
                model=self.model_id, temperature=0.0,
                response_format={"type": "json_object"},
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": user_prompt}])
            return r.choices[0].message.content
        raise ValueError(f"unknown provider: {self.provider}")
