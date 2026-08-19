"""Paired bootstrap for H2: gap reduction (baseline minus CAMPS) per model.

Resamples essays (within cohort) jointly across conditions, so the
statistic is the within-essay effect of the panel, not a comparison of
two independent estimates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from metrics import consensus_and_bds


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/E1")
    ap.add_argument("--base", default="baseline")
    ap.add_argument("--treat", default="camps_k3")
    ap.add_argument("--n-boot", type=int, default=10_000)
    args = ap.parse_args()
    rows = [json.loads(l) for l in
            (Path(args.results) / "scores.jsonl").read_text().splitlines()]
    df = pd.DataFrame(rows)
    agg = consensus_and_bds(df)
    rng = np.random.default_rng(4139514)
    for model, g in agg.groupby("model"):
        piv = g.pivot_table(index=["essay_id", "cohort"],
                            columns="condition", values="consensus")
        if args.base not in piv or args.treat not in piv:
            continue
        piv = piv.dropna(subset=[args.base, args.treat]).reset_index()
        sea = piv[piv.cohort == "sea"]
        nat = piv[piv.cohort == "native"]
        if len(sea) < 30 or len(nat) < 30:
            print(f"{model}: insufficient paired data "
                  f"(sea={len(sea)}, native={len(nat)})")
            continue
        def gaps(s_idx, n_idx):
            gb = (nat[args.base].to_numpy()[n_idx].mean()
                  - sea[args.base].to_numpy()[s_idx].mean())
            gt = (nat[args.treat].to_numpy()[n_idx].mean()
                  - sea[args.treat].to_numpy()[s_idx].mean())
            return gb, gt
        gb, gt = gaps(np.arange(len(sea)), np.arange(len(nat)))
        boots = np.empty(args.n_boot)
        for b in range(args.n_boot):
            si = rng.integers(0, len(sea), len(sea))
            ni = rng.integers(0, len(nat), len(nat))
            b_gb, b_gt = gaps(si, ni)
            boots[b] = b_gb - b_gt
        lo, hi = np.percentile(boots, [2.5, 97.5])
        p_onesided = float((boots <= 0).mean())
        print(f"{model}: gap {gb:.3f} -> {gt:.3f} | reduction "
              f"{gb-gt:.3f} [{lo:.3f}, {hi:.3f}] "
              f"({100*(gb-gt)/gb:.0f}%), P(reduction<=0)={p_onesided:.4f}")


if __name__ == "__main__":
    main()
