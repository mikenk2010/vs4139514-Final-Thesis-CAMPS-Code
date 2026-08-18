"""Progress dashboard: read the JSON logs and show where every experiment stands.

    python src/status.py            # overall progress per model x condition
    python src/status.py --runs     # run history (results/runs.jsonl)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/experiment.yaml")
    ap.add_argument("--runs", action="store_true", help="show run history")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text())
    results = Path(cfg["paths"]["results"])

    if args.runs:
        rp = results / "runs.jsonl"
        if not rp.exists():
            raise SystemExit("no runs recorded yet")
        runs = pd.DataFrame([json.loads(l) for l in rp.read_text().splitlines()])
        cols = ["run_id", "experiment", "models", "limit", "calls_new",
                "calls_cached_or_resumed", "errors", "tokens_in",
                "tokens_out", "duration_s"]
        print(runs[[c for c in cols if c in runs]].to_string(index=False))
        return

    manifest = pd.read_csv(cfg["paths"]["manifest"])
    for exp, spec in cfg["experiments"].items():
        log = results / exp / "scores.jsonl"
        n_essays = len(manifest[manifest.cohort.isin(spec["cohorts"])])
        expected_per_model = sum(
            len(cfg["conditions"][c]["agents"])
            + (1 if cfg["conditions"][c].get("adjudicator") else 0)
            for c in spec["conditions"]) * n_essays
        print(f"\n=== {exp}: {n_essays} essays, "
              f"{expected_per_model} calls expected per model ===")
        if not log.exists():
            print("  (no runs yet)")
            continue
        df = pd.DataFrame([json.loads(l) for l in log.read_text().splitlines()])
        prog = (df.groupby(["model", "condition"]).size()
                  .rename("calls").reset_index())
        for _, r in prog.iterrows():
            n_agents = len(cfg["conditions"][r.condition]["agents"]) + (
                1 if cfg["conditions"][r.condition].get("adjudicator") else 0)
            pct = 100 * r.calls / (n_essays * n_agents)
            print(f"  {r.model:15s} {r.condition:14s} "
                  f"{r.calls:5d} calls  ({pct:5.1f}%)")


if __name__ == "__main__":
    main()
