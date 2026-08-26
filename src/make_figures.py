"""Generate Chapter 4 figures from experiment logs (reproducibility rule:
every thesis figure is script-generated).

    python src/make_figures.py --results results/E1
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from metrics import consensus_and_bds
from make_tables import gap_ci

MODEL_LABEL = {"gpt-4o": "GPT-4o", "claude-sonnet": "Claude Sonnet",
               "gemini-pro": "Gemini Pro", "qwen3-local": "Qwen3 14B"}
BAND_MAP = {"A2_0": 1, "B1_1": 2, "B1_2": 3, "B2_0": 4}


def fig_gaps(agg: pd.DataFrame, out: Path) -> None:
    """Baseline vs CAMPS k=3 cohort score gap per model, with 95% CIs."""
    models = [m for m in MODEL_LABEL if m in set(agg.model)]
    conds = [("baseline", "Baseline (single evaluator)", "#c44e52"),
             ("camps_k3", "CAMPS $k$=3 panel", "#4c72b0")]
    width = 0.36
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for j, (cond, label, colour) in enumerate(conds):
        xs, ys, los, his = [], [], [], []
        for i, m in enumerate(models):
            g = agg[(agg.model == m) & (agg.condition == cond)]
            sea = g[g.cohort == "sea"].consensus.to_numpy()
            nat = g[g.cohort == "native"].consensus.to_numpy()
            if len(sea) < 50 or len(nat) < 50:
                continue
            point, lo, hi = gap_ci(sea, nat)
            xs.append(i + (j - 0.5) * width)
            ys.append(point); los.append(point - lo); his.append(hi - point)
        ax.bar(xs, ys, width, label=label, color=colour,
               yerr=[los, his], capsize=4)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([MODEL_LABEL[m] for m in models])
    ax.set_ylabel("Native $-$ SEA score gap (bands)")
    ax.set_title("Cohort score gap by model and condition "
                 "(95% bootstrap CIs, $n$=100/cohort)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out)
    print(f"wrote {out}")


def fig_band(df: pd.DataFrame, agg: pd.DataFrame, out: Path) -> None:
    """Baseline gap disaggregated by SEA proficiency band."""
    meta = df.drop_duplicates("essay_id").set_index("essay_id")["cefr"]
    models = [m for m in MODEL_LABEL if m in set(agg.model)]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    width = 0.36
    colours = {"B1_2": "#dd8452", "B2_0": "#55a868"}
    for j, band in enumerate(["B1_2", "B2_0"]):
        xs, ys = [], []
        for i, m in enumerate(models):
            g = agg[(agg.model == m) & (agg.condition == "baseline")]
            nat = g[g.cohort == "native"].consensus.mean()
            sea_ids = [e for e in g[g.cohort == "sea"].essay_id
                       if meta.get(e) == band]
            if len(sea_ids) < 10:
                continue
            sea = g[g.essay_id.isin(sea_ids)].consensus.mean()
            xs.append(i + (j - 0.5) * width)
            ys.append(nat - sea)
        label = "SEA B1 upper ($n$=74)" if band == "B1_2" \
            else "SEA B2+ ($n$=26)"
        ax.bar(xs, ys, width, label=label, color=colours[band])
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([MODEL_LABEL[m] for m in models])
    ax.set_ylabel("Baseline gap vs native cohort (bands)")
    ax.set_title("The bias concentrates on mid-proficiency writing")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out)
    print(f"wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/E1")
    ap.add_argument("--figures-dir",
                    default="../s4139514-Final-Thesis-CAMPS/figures")
    args = ap.parse_args()
    rows = [json.loads(l) for l in
            (Path(args.results) / "scores.jsonl").read_text().splitlines()]
    df = pd.DataFrame(rows)
    agg = consensus_and_bds(df)
    figs = Path(args.figures_dir)
    fig_gaps(agg, figs / "fig-e1-gaps.pdf")
    fig_band(df, agg, figs / "fig-e1-gap-by-band.pdf")


if __name__ == "__main__":
    main()
