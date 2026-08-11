"""Run a CAMPS experiment: essay x model x condition, with JSON logging.

Reads the manifest produced by sample_icnale.py, loads essay texts from the
licensed data directory (never copied elsewhere), and scores each essay under
every agent of the requested conditions. One JSON line per scoring call.
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import pandas as pd
import yaml

from models import ScoringClient


def load_prompt(name: str) -> str:
    return Path(f"prompts/cri_{name}.txt").read_text()


def bds(scores: list[float]) -> float:
    mean = sum(scores) / len(scores)
    return (sum((s - mean) ** 2 for s in scores) / len(scores)) ** 0.5


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/experiment.yaml")
    ap.add_argument("--experiment", required=True, choices=["E1", "E2", "E3"])
    ap.add_argument("--models", nargs="*", help="subset of model names")
    ap.add_argument("--limit", type=int, default=None,
                    help="smoke test: only score the first N essays")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text())
    exp = cfg["experiments"][args.experiment]
    root = Path(cfg["paths"]["icnale_root"])
    manifest = pd.read_csv(cfg["paths"]["manifest"])
    manifest = manifest[manifest.cohort.isin(exp["cohorts"])]
    if args.limit:
        manifest = manifest.head(args.limit)
        print(f"SMOKE TEST: limited to {len(manifest)} essays")

    out_dir = Path(cfg["paths"]["results"]) / args.experiment
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "scores.jsonl"
    done: set[tuple] = set()
    if log_path.exists():
        for line in log_path.read_text().splitlines():
            d = json.loads(line)
            done.add((d["essay_id"], d["model"], d["condition"], d["agent"]))
        print(f"Resuming: {len(done)} calls already logged")

    models = [m for m in cfg["models"]
              if not args.models or m["name"] in args.models]
    with log_path.open("a") as log:
        for m in models:
            client = ScoringClient(m["provider"], m["id"],
                                   Path(cfg["paths"]["cache"]),
                                   cfg["generation"]["max_retries"])
            for cond_name in exp["conditions"]:
                agents = cfg["conditions"][cond_name]["agents"]
                for _, row in manifest.iterrows():
                    essay_text = (root / row.path).read_text(encoding="utf-8-sig")
                    user_prompt = (
                        "Score the following essay. Respond with JSON: "
                        '{"score": <band>, "rationale": "<2-3 sentences>"}.\n\n'
                        f"ESSAY:\n{essay_text}"
                    )
                    scores: list[float] = []
                    for agent in agents:
                        if (row.essay_id, m["name"], cond_name, agent) in done:
                            continue
                        res = client.score(row.essay_id, agent,
                                           load_prompt(agent), user_prompt)
                        scores.append(res.score)
                        log.write(json.dumps({
                            "essay_id": row.essay_id, "cohort": row.cohort,
                            "task": row.task, "cefr": row.cefr,
                            "model": m["name"], "condition": cond_name,
                            "agent": agent, "score": res.score,
                            "rationale": res.rationale}) + "\n")
                        log.flush()
                    if len(scores) > 1:
                        print(f"{row.essay_id} {m['name']} {cond_name}: "
                              f"mean={statistics.mean(scores):.2f} "
                              f"BDS={bds(scores):.2f}")
    print(f"Done. Log: {log_path}")


if __name__ == "__main__":
    main()
