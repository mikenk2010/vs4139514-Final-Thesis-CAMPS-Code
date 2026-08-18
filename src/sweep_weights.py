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

    out_rows = []
    for w in simplex_grid(len(agents), args.step):
        cons = np.rint(S @ w)
        q_sea = qwk(h[sea_m], cons[sea_m]) if sea_m.any() else np.nan
        q_nat = qwk(h[nat_m], cons[nat_m]) if nat_m.any() else np.nan
        out_rows.append([*w, q_sea, q_nat, q_nat - q_sea])
    out = pd.DataFrame(out_rows, columns=[*agents, "qwk_sea", "qwk_native",
                                          "gap"])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"swept {len(out)} weight vectors -> {args.out}")

    # frontier figure (script-generated, per reproducibility convention)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 4.2))
    ax.scatter(out.qwk_sea, out.qwk_native, s=6, alpha=0.25,
               label="weight vectors")
    eq = out.iloc[(out[agents].sub(1 / len(agents)).abs().sum(axis=1)
                   ).idxmin()]
    ax.scatter([eq.qwk_sea], [eq.qwk_native], marker="*", s=160,
               label="equal weights", zorder=3)
    ax.set_xlabel("QWK (SEA cohort)")
    ax.set_ylabel("QWK (native cohort)")
    ax.set_title(f"Fairness-accuracy frontier: {args.model}")
    ax.legend()
    fig.tight_layout()
    fig_path = Path(args.out).with_name(f"frontier_{args.model}.pdf")
    fig.savefig(fig_path)
    print(f"frontier figure -> {fig_path}")


if __name__ == "__main__":
    main()
