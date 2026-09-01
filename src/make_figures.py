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


def fig_e2_ablation(e1: pd.DataFrame, e2: pd.DataFrame,
                    out: Path) -> None:
    """E2: gap by panel configuration per model, with 95% CIs.

    Complete cells only (100 essays per cohort); the adjudicated
    condition uses the adjudicator's final score as the aggregate.
    """
    from metrics import adjudicated_scores
    conds = [("baseline", "$k$=1"), ("camps_k3", "$k$=3"),
             ("camps_k5", "$k$=5"), ("camps_k5_adj", "$k$=5+adj.")]
    colours = ["#c44e52", "#dd8452", "#4c72b0", "#2A2A55"]
    df = pd.concat([e1, e2], ignore_index=True)
    models = [m for m in MODEL_LABEL
              if m in set(e2.model)]
    width = 0.2
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for j, (cond, label) in enumerate(conds):
        xs, ys, los, his = [], [], [], []
        for i, m in enumerate(models):
            sub = df[(df.model == m) & (df.condition == cond)]
            if sub.empty:
                continue
            if cond == "camps_k5_adj":
                agg = (adjudicated_scores(sub)
                       .rename(columns={"adjudicated": "consensus"}))
            else:
                agg = consensus_and_bds(sub)
            sea = agg[agg.cohort == "sea"].consensus.to_numpy()
            nat = agg[agg.cohort == "native"].consensus.to_numpy()
            if len(sea) < 100 or len(nat) < 100:
                continue
            point, lo, hi = gap_ci(sea, nat)
            xs.append(i + (j - 1.5) * width)
            ys.append(point); los.append(point - lo); his.append(hi - point)
        if xs:
            ax.bar(xs, ys, width, label=label, color=colours[j],
                   yerr=[los, his], capsize=3)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([MODEL_LABEL[m] for m in models])
    ax.set_ylabel("Native $-$ SEA score gap (bands)")
    ax.set_title("E2 ablation: cohort gap by panel configuration "
                 "(95% bootstrap CIs)")
    ax.legend(title="Configuration")
    fig.tight_layout()
    fig.savefig(out)
    print(f"wrote {out}")


def fig_e3_roc(e3: pd.DataFrame, dispersion: pd.Series, out: Path,
               model: str = "gpt-4o", seed: int = 4139514) -> None:
    """E3: ROC of BDS against top-quartile human dispersion, held-out
    split, plus the BDS-vs-dispersion scatter."""
    from sklearn.metrics import roc_curve, roc_auc_score
    sub = e3[(e3.model == model) & (e3.cohort == "gra")]
    agg = consensus_and_bds(sub).set_index("essay_id")
    common = agg.index.intersection(dispersion.index)
    agg = agg.loc[common]
    disp = dispersion.loc[common]
    contested = (disp >= disp.quantile(0.75)).astype(int)
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(agg))
    hold = idx[len(idx) // 2:]
    y, s = contested.to_numpy()[hold], agg.bds.to_numpy()[hold]
    fpr, tpr, _ = roc_curve(y, s)
    auc = roc_auc_score(y, s)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    ax1.plot(fpr, tpr, color="#4c72b0", lw=1.8,
             label=f"BDS (AUC = {auc:.2f})")
    ax1.plot([0, 1], [0, 1], "--", color="grey", lw=1,
             label="chance")
    ax1.set_xlabel("False-positive rate")
    ax1.set_ylabel("Sensitivity")
    ax1.set_title(f"ROC, held-out GRA split ($n$={len(hold)})")
    ax1.legend()
    ax2.scatter(disp, agg.bds, s=14, alpha=0.6, color="#4c72b0")
    ax2.set_xlabel("Human rating dispersion (SD across 80 raters)")
    ax2.set_ylabel("BDS ($k$=5 panel)")
    r = np.corrcoef(disp, agg.bds)[0, 1]
    ax2.set_title(f"BDS vs human dispersion ($n$={len(agg)}, "
                  f"$r$={r:.2f})")
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
    e2p, e3p = Path("results/E2/scores.jsonl"), Path("results/E3/scores.jsonl")
    if e2p.exists():
        e2 = pd.DataFrame([json.loads(l)
                           for l in e2p.read_text().splitlines()])
        fig_e2_ablation(df, e2, figs / "fig-e2-ablation.pdf")
    dp = Path("results/gra_dispersion.csv")
    if e3p.exists() and dp.exists():
        e3 = pd.DataFrame([json.loads(l)
                           for l in e3p.read_text().splitlines()])
        disp = pd.read_csv(dp).set_index("essay_id")["dispersion"]
        fig_e3_roc(e3, disp, figs / "fig-e3-roc.pdf")


if __name__ == "__main__":
    main()
