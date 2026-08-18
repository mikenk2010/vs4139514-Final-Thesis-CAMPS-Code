"""Run a CAMPS experiment: essay x model x condition, with JSON logging.

Reads the manifest produced by sample_icnale.py, loads essay texts from the
licensed data directory (never copied elsewhere), and scores each essay under
every agent of the requested conditions. One JSON line per scoring call.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from datetime import datetime, timezone
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
    if not models:
        available = [m["name"] for m in cfg["models"]]
        raise SystemExit(f"No models matched {args.models}. "
                         f"Available in config: {available}")

    # --- run-history record (results/runs.jsonl) ---
    run_rec = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "experiment": args.experiment,
        "models": [m["name"] for m in models],
        "model_ids": {m["name"]: m["id"] for m in models},
        "limit": args.limit,
        "essays": len(manifest),
        "started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "calls_new": 0, "calls_cached_or_resumed": 0, "errors": 0,
        "tokens_in": 0, "tokens_out": 0,
    }
    t0 = time.time()
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
                            run_rec["calls_cached_or_resumed"] += 1
                            continue
                        try:
                            res = client.score(row.essay_id, agent,
                                               load_prompt(agent), user_prompt)
                        except Exception:
                            run_rec["errors"] += 1
                            raise
                        run_rec["calls_new"] += 1
                        print(f"  [{run_rec['calls_new']}] {row.essay_id} "
                              f"{cond_name}/{agent} -> {res.score}",
                              flush=True)
                        if res.usage:
                            run_rec["tokens_in"] += res.usage.get("in", 0)
                            run_rec["tokens_out"] += res.usage.get("out", 0)
                        scores.append(res.score)
                        log.write(json.dumps({
                            "ts": datetime.now(timezone.utc).isoformat(
                                timespec="seconds"),
                            "run_id": run_rec["run_id"],
                            "essay_id": row.essay_id, "cohort": row.cohort,
                            "task": row.task, "cefr": row.cefr,
                            "model": m["name"], "model_id": m["id"],
                            "condition": cond_name,
                            "agent": agent, "score": res.score,
                            "rationale": res.rationale,
                            "usage": res.usage}) + "\n")
                        log.flush()
                    if (cfg["conditions"][cond_name].get("adjudicator")
                            and (row.essay_id, m["name"], cond_name,
                                 "adjudicator") not in done):
                        # gather the panel's scores + rationales from the log
                        panel = [json.loads(l) for l in
                                 log_path.read_text().splitlines()]
                        panel = [r for r in panel
                                 if r["essay_id"] == row.essay_id
                                 and r["model"] == m["name"]
                                 and r["condition"] == cond_name
                                 and r["agent"] in agents]
                        if len(panel) == len(agents):
                            summary = "\n".join(
                                f"Evaluator {i+1} score: {r['score']}. "
                                f"Rationale: {r['rationale']}"
                                for i, r in enumerate(panel))
                            adj_user = (
                                "Five evaluators scored the same essay "
                                "under different documented cultural "
                                "interpretations of the rubric.\n"
                                f"{summary}\n\nESSAY:\n{essay_text}\n\n"
                                "Give your adjudicated score as JSON: "
                                '{"score": <band>, "confidence": <0-1>, '
                                '"rationale": "<3-4 sentences>"}')
                            res = client.score(row.essay_id, "adjudicator",
                                               load_prompt("adjudicator")
                                               if Path("prompts/cri_adjudicator.txt").exists()
                                               else Path("prompts/adjudicator.txt").read_text(),
                                               adj_user)
                            run_rec["calls_new"] += 1
                            if res.usage:
                                run_rec["tokens_in"] += res.usage.get("in", 0)
                                run_rec["tokens_out"] += res.usage.get("out", 0)
                            conf = None
                            try:
                                from models import extract_json
                                conf = json.loads(
                                    extract_json(res.raw)).get("confidence")
                            except Exception:
                                pass
                            log.write(json.dumps({
                                "ts": datetime.now(timezone.utc).isoformat(
                                    timespec="seconds"),
                                "run_id": run_rec["run_id"],
                                "essay_id": row.essay_id,
                                "cohort": row.cohort, "task": row.task,
                                "cefr": row.cefr, "model": m["name"],
                                "model_id": m["id"],
                                "condition": cond_name,
                                "agent": "adjudicator",
                                "score": res.score,
                                "confidence": conf,
                                "rationale": res.rationale,
                                "usage": res.usage}) + "\n")
                            log.flush()
                            print(f"  [adj] {row.essay_id} -> {res.score} "
                                  f"(conf={conf})", flush=True)
                    if len(scores) > 1:
                        print(f"{row.essay_id} {m['name']} {cond_name}: "
                              f"mean={statistics.mean(scores):.2f} "
                              f"BDS={bds(scores):.2f}")
    run_rec["finished"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    run_rec["duration_s"] = round(time.time() - t0, 1)
    runs_path = Path(cfg["paths"]["results"]) / "runs.jsonl"
    with runs_path.open("a") as f:
        f.write(json.dumps(run_rec) + "\n")
    print(f"Done. Log: {log_path}")
    print(f"Run record appended to {runs_path}: "
          f"{run_rec['calls_new']} new calls, "
          f"{run_rec['calls_cached_or_resumed']} resumed/cached, "
          f"tokens in/out {run_rec['tokens_in']}/{run_rec['tokens_out']}, "
          f"{run_rec['duration_s']}s")


if __name__ == "__main__":
    main()
