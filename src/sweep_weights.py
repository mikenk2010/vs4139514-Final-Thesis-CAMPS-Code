"""E2 consensus-weight sweep: trace the fairness-accuracy frontier (H4).

Pure post-processing: recomputes the weighted consensus from logged
per-agent scores at every weight vector on a simplex grid, so the sweep
costs zero API calls. Outputs a CSV of (weights, QWK_sea, QWK_native,
gap) and the frontier figure for the thesis.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from metrics import qwk

BAND_MAP = {"A2_0": 1, "B1_1": 2, "B1_2": 3, "B2_0": 4}


def simplex_grid(k: int, step: float):
    """All weight vectors of length k, entries >=0, summing to 1."""
    n = round(1 / step)
    for combo in itertools.combinations_with_replacement(range(k), n):
        w = np.bincount(combo, minlength=k) / n
        yield w


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/E2")
    ap.add_argument("--condition", default="camps_k5")
    ap.add_argument("--model", required=True)
    ap.add_argument("--step", type=float, default=0.05)
    ap.add_argument("--out", default="results/E2/weight_sweep.csv")
    args = ap.parse_args()

    rows = [json.loads(l) for l in
            (Path(args.results) / "scores.jsonl").read_text().splitlines()]
    df = pd.DataFrame(rows)
    df = df[(df.condition == args.condition) & (df.model == args.model)
            & (df.agent != "adjudicator")]
    agents = sorted(df.agent.unique())
    print(f"agents ({len(agents)}): {agents}")

    # pivot: essay x agent score matrix, plus cohort and ground truth
    pivot = df.pivot_table(index="essay_id", columns="agent",
                           values="score").dropna()
    meta = df.drop_duplicates("essay_id").set_index("essay_id")
    cohorts = meta.loc[pivot.index, "cohort"]
    truth = meta.loc[pivot.index, "cefr"].map(BAND_MAP)
    S = pivot[agents].to_numpy()
    sea_m = (cohorts == "sea").to_numpy()
    nat_m = (cohorts == "native").to_numpy()
    h = truth.to_numpy()

    # Accuracy is QWK against CEFR bands, computable only on the banded
    # SEA cohort; fairness is the native-SEA cohort score gap (the
    # thesis's primary metric -- the native cohort carries no band).
    out_rows = []
    for w in simplex_grid(len(agents), args.step):
        cons = S @ w
        q_sea = qwk(h[sea_m], np.rint(cons[sea_m])) if sea_m.any() else np.nan
        gap = (cons[nat_m].mean() - cons[sea_m].mean()
               if nat_m.any() and sea_m.any() else np.nan)
        out_rows.append([*w, q_sea, gap])
    out = pd.DataFrame(out_rows, columns=[*agents, "qwk_sea", "gap"])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"swept {len(out)} weight vectors -> {args.out}")

    # frontier figure (script-generated, per reproducibility convention)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.scatter(out.gap.abs(), out.qwk_sea, s=6, alpha=0.25, color="#4878CF",
               label="weight vectors")
    eq = out.iloc[(out[agents].sub(1 / len(agents)).abs().sum(axis=1)
                   ).idxmin()]
    ax.scatter([abs(eq.gap)], [eq.qwk_sea], marker="*", s=200,
               color="#D65F5F", label="equal weights", zorder=3)
    # Pareto frontier: minimal |gap| for any given accuracy or better
    srt = out.assign(agap=out.gap.abs()).sort_values("agap")
    best = -np.inf; fx = []; fy = []
    for _, r in srt.iterrows():
        if r.qwk_sea > best:
            best = r.qwk_sea; fx.append(r.agap); fy.append(r.qwk_sea)
    ax.plot(fx, fy, "-o", ms=3.5, color="#2A2A35", lw=1.2,
            label="Pareto frontier")
    ax.set_xlabel("|native $-$ SEA| cohort score gap (bands)")
    ax.set_ylabel("QWK vs CEFR bands (SEA cohort)")
    ax.set_title(f"Fairness–accuracy frontier: {args.model}")
    ax.legend()
    fig.tight_layout()
    fig_path = (Path("../s4139514-Final-Thesis-CAMPS/figures")
                / f"fig-e2-frontier-{args.model}.pdf")
    fig.savefig(fig_path)
    print(f"frontier figure -> {fig_path}")
    # console summary for the thesis prose
    i = out.gap.abs().idxmin()
    print(f"equal weights: gap {eq.gap:.3f}, QWK_sea {eq.qwk_sea:.3f}")
    print(f"min |gap| vector: gap {out.loc[i].gap:.3f}, "
          f"QWK_sea {out.loc[i].qwk_sea:.3f}, weights "
          f"{dict(zip(agents, out.loc[i][agents].round(2)))}")
    print(f"max QWK_sea: {out.qwk_sea.max():.3f} at gap "
          f"{out.loc[out.qwk_sea.idxmax()].gap:.3f}")


if __name__ == "__main__":
    main()
