"""Replay archived CAMPS scores from the disk cache. No provider calls.

Rebuilds the exact prompts used in the thesis runs and checks that
results/cache still returns the logged score. A cache miss stops the
check. It does not call OpenAI, Anthropic, Google, or Ollama.

    python src/replay_check.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

from models import CacheMiss, ScoringClient

CASE_ID = "WE_PHL_PTJ0_087_B1_2"
ROOT = Path(__file__).resolve().parents[1]


def user_prompt(essay_text: str) -> str:
    return (
        "Score the following essay. Respond with JSON: "
        '{"score": <band>, "rationale": "<2-3 sentences>"}.\n\n'
        f"ESSAY:\n{essay_text}"
    )


def adjudicator_prompt(essay_text: str, panel: list[dict]) -> str:
    summary = "\n".join(
        f"Evaluator {i + 1} score: {r['score']}. Rationale: {r['rationale']}"
        for i, r in enumerate(panel))
    return (
        "Five evaluators scored the same essay "
        "under different documented cultural "
        "interpretations of the rubric.\n"
        f"{summary}\n\nESSAY:\n{essay_text}\n\n"
        "Give your adjudicated score as JSON: "
        '{"score": <band>, "confidence": <0-1>, '
        '"rationale": "<3-4 sentences>"}'
    )


def load_logs() -> pd.DataFrame:
    frames = []
    for exp in ("E1", "E2", "E3"):
        path = ROOT / "results" / exp / "scores.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        frames.append(pd.DataFrame(rows).assign(experiment=exp))
    return pd.concat(frames, ignore_index=True)


def system_prompt(agent: str) -> str:
    if agent == "adjudicator":
        return (ROOT / "prompts" / "adjudicator.txt").read_text()
    return (ROOT / "prompts" / f"cri_{agent}.txt").read_text()


def main() -> None:
    cfg = yaml.safe_load((ROOT / "configs" / "experiment.yaml").read_text())
    manifest = pd.read_csv(ROOT / "results" / "manifest.csv")
    by_id = (manifest.drop_duplicates("essay_id")
             .set_index("essay_id")["path"].to_dict())
    model_ids = {m["name"]: (m["provider"], m["id"]) for m in cfg["models"]}
    logs = load_logs()

    # The case essay, every logged call, plus five essays from each
    # main cohort on GPT-4o. Fixed ids, so the check is repeatable.
    case = logs[logs.essay_id == CASE_ID]
    extra_ids = []
    for cohort in ("sea", "native"):
        ids = sorted(manifest.loc[manifest.cohort == cohort, "essay_id"])[:5]
        extra_ids.extend(ids)
    extra = logs[(logs.essay_id.isin(extra_ids)) & (logs.model == "gpt-4o")
                 & (logs.experiment == "E1")]
    sample = pd.concat([case, extra], ignore_index=True)
    sample = sample.drop_duplicates(
        ["essay_id", "model", "condition", "agent"])

    clients = {}
    hits = 0
    mismatches = []
    texts: dict[str, str] = {}

    def essay_text(essay_id: str) -> str:
        if essay_id not in texts:
            rel = by_id[essay_id]
            texts[essay_id] = (ROOT / "data" / rel).read_text(encoding="utf-8-sig")
        return texts[essay_id]

    print(f"Offline replay: {len(sample)} archived calls, no provider traffic")
    for rec in sample.to_dict(orient="records"):
        provider, model_id = model_ids[rec["model"]]
        if rec["model"] not in clients:
            clients[rec["model"]] = ScoringClient(
                provider, model_id, ROOT / "results" / "cache")
        client = clients[rec["model"]]
        text = essay_text(rec["essay_id"])
        if rec["agent"] == "adjudicator":
            panel = logs[(logs.essay_id == rec["essay_id"])
                         & (logs.model == rec["model"])
                         & (logs.condition == rec["condition"])
                         & (logs.experiment == rec["experiment"])
                         & (logs.agent != "adjudicator")]
            prompt_user = adjudicator_prompt(text, panel.to_dict(orient="records"))
        else:
            prompt_user = user_prompt(text)
        try:
            got = client.score(rec["essay_id"], rec["agent"],
                               system_prompt(rec["agent"]), prompt_user,
                               offline=True)
        except CacheMiss as exc:
            print(f"CACHE MISS {rec['model']} {rec['condition']} "
                  f"{rec['agent']} {rec['essay_id']}")
            print(exc)
            sys.exit(1)
        if float(got.score) != float(rec["score"]):
            mismatches.append(
                f"{rec['essay_id']} {rec['model']} {rec['agent']}: "
                f"cache {got.score} log {rec['score']}")
        hits += 1

    if mismatches:
        print("Score mismatches:")
        print("\n".join(mismatches))
        sys.exit(1)

    print(f"Cache hits: {hits}/{len(sample)}. Every score matched the log.")
    print()
    order = ["neutral_single", "western", "sea", "east_asian",
             "mekong", "neutral", "adjudicator"]
    print(f"Case essay {CASE_ID} (scores from the log, confirmed against the cache)")
    show = case.copy()
    show["ord"] = show.agent.map({a: i for i, a in enumerate(order)})
    for (model, cond), g in show.sort_values(["model", "condition", "ord"]).groupby(
            ["model", "condition"], sort=False):
        lenses = g[g.agent != "adjudicator"]
        scores = lenses.score.tolist()
        mean = sum(scores) / len(scores)
        spread = (sum((s - mean) ** 2 for s in scores) / len(scores)) ** 0.5
        bits = [f"{r.agent} {r.score:g}" for r in g.itertuples()]
        print(f"  {model:16s} {cond:14s} " + " | ".join(bits))
        print(f"  {'':16s} {'':14s} mean {mean:.2f}  BDS {spread:.2f}")


if __name__ == "__main__":
    main()
