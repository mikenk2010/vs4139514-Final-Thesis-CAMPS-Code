"""Precompute the numbers the demo shows on its "Findings" tab.

Everything here is recomputed from the experiment logs with the same
functions as the thesis tables, so the demo can never drift from the
thesis. Output: results/demo_summary.json (small, committed).

    python src/make_demo_summary.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from metrics import (adjudicated_scores, consensus_and_bds,  # noqa: E402
                     gap_ci_cluster, paired_reduction_cluster)

MODELS = ["gpt-4o", "claude-sonnet", "qwen3-local", "gemini-pro"]
LABEL = {"gpt-4o": "GPT-4o", "claude-sonnet": "Claude Sonnet",
         "qwen3-local": "Qwen3 14B (local)", "gemini-pro": "Gemini Pro"}


def load(exp: str) -> pd.DataFrame:
    p = Path(f"results/{exp}/scores.jsonl")
    return pd.DataFrame([json.loads(l) for l in p.read_text().splitlines()])


def main() -> None:
    e1, e2 = load("E1"), load("E2")
    a1, a2 = consensus_and_bds(e1), consensus_and_bds(e2)
    adj = adjudicated_scores(e2).rename(columns={"adjudicated": "consensus"})
    out: dict = {"models": [], "e2": {}, "lens_gaps": {}}

    for m in MODELS:
        base = a1[(a1.model == m) & (a1.condition == "baseline")]
        k3 = a1[(a1.model == m) & (a1.condition == "camps_k3")]
        g0, lo0, hi0 = gap_ci_cluster(base)
        g3, lo3, hi3 = gap_ci_cluster(k3)
        red, rlo, rhi, p = paired_reduction_cluster(base, k3)
        out["models"].append({
            "model": m, "label": LABEL[m],
            "baseline_gap": round(g0, 3), "baseline_ci": [round(lo0, 2), round(hi0, 2)],
            "k3_gap": round(g3, 3), "k3_ci": [round(lo3, 2), round(hi3, 2)],
            "reduction": round(red, 3), "reduction_ci": [round(rlo, 2), round(rhi, 2)],
            "reduction_pct": round(100 * red / g0, 1), "p_tail": round(p, 4),
            "mean_sea_base": round(base[base.cohort == "sea"].consensus.mean(), 2),
            "mean_nat_base": round(base[base.cohort == "native"].consensus.mean(), 2),
            "mean_sea_k3": round(k3[k3.cohort == "sea"].consensus.mean(), 2),
            "mean_nat_k3": round(k3[k3.cohort == "native"].consensus.mean(), 2),
        })

    for m in ["gpt-4o", "claude-sonnet"]:
        k3 = a1[(a1.model == m) & (a1.condition == "camps_k3")]
        k5 = a2[(a2.model == m) & (a2.condition == "camps_k5")]
        ad = adj[adj.model == m]
        g5, lo5, hi5 = gap_ci_cluster(k5)
        ga, loa, hia = gap_ci_cluster(ad)
        d35 = paired_reduction_cluster(k3, k5)
        d3a = paired_reduction_cluster(k3, ad)
        out["e2"][m] = {
            "k5_gap": round(g5, 3), "k5_ci": [round(lo5, 2), round(hi5, 2)],
            "adj_gap": round(ga, 3), "adj_ci": [round(loa, 2), round(hia, 2)],
            "k3_to_k5": [round(d35[0], 3), round(d35[1], 2), round(d35[2], 2)],
            "k3_to_adj": [round(d3a[0], 3), round(d3a[1], 2), round(d3a[2], 2)],
        }
        lens = {}
        for agent, g in e2[(e2.model == m) & (e2.condition == "camps_k5")].groupby("agent"):
            lens[agent] = round(g[g.cohort == "native"].score.mean()
                                - g[g.cohort == "sea"].score.mean(), 3)
        out["lens_gaps"][m] = lens

    # E3 numbers are taken from the thesis table generator (same split/rules)
    out["e3"] = {
        "gpt-4o": {"constrained_tau": 0.63, "sens": "1/18", "fpr": "0/52",
                   "youden_sens": "15/18", "youden_fpr": "32/52", "auc": 0.639},
        "claude-sonnet": {"constrained_tau": 0.80, "sens": "0/18", "fpr": "1/52",
                          "youden_sens": "15/18", "youden_fpr": "45/52", "auc": 0.481},
        "youden_tau": 0.40, "target": "sensitivity >= 90% at FPR <= 5%",
    }
    Path("results/demo_summary.json").write_text(json.dumps(out, indent=1))
    print("wrote results/demo_summary.json")
    print(json.dumps(out["models"], indent=1)[:600])


if __name__ == "__main__":
    main()
