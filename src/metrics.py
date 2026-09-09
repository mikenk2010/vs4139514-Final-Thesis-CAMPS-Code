"""Metrics for CAMPS experiments: QWK, bootstrap CIs, Fisher z, BDS, ROC.

All tables in the thesis are generated from these functions (reproducibility
convention): no hand-computed numbers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import cohen_kappa_score, roc_curve, auc


def qwk(human: np.ndarray, model: np.ndarray) -> float:
    return cohen_kappa_score(human, model, weights="quadratic")


def bootstrap_ci(human: np.ndarray, model: np.ndarray,
                 n_boot: int = 10_000, seed: int = 4139514,
                 alpha: float = 0.05) -> tuple[float, float, float]:
    """QWK with percentile bootstrap CI. Returns (point, lo, hi)."""
    rng = np.random.default_rng(seed)
    n = len(human)
    point = qwk(human, model)
    boots = np.empty(n_boot)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for b in range(n_boot):
            idx = rng.integers(0, n, n)
            boots[b] = qwk(human[idx], model[idx])
    # degenerate resamples (single label) yield nan; exclude them
    lo, hi = np.nanpercentile(boots,
                              [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return point, float(lo), float(hi)


def fisher_z_diff(r1: float, n1: int, r2: float, n2: int) -> tuple[float, float]:
    """Two-sided z test for difference between two correlations."""
    z1, z2 = np.arctanh(r1), np.arctanh(r2)
    se = np.sqrt(1 / (n1 - 3) + 1 / (n2 - 3))
    z = (z1 - z2) / se
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    return float(z), float(p)


def consensus_and_bds(df: pd.DataFrame,
                      weights: dict[str, float] | None = None) -> pd.DataFrame:
    """Per essay x model x condition: weighted consensus score and BDS.

    The meta-adjudicator is excluded: BDS and the weighted consensus are
    defined over the panel agents only. Use adjudicated_scores() for the
    adjudicator's alternative aggregate.
    """
    df = df[df.agent != "adjudicator"]
    def agg(g: pd.DataFrame) -> pd.Series:
        w = np.array([weights.get(a, 1.0) if weights else 1.0
                      for a in g.agent])
        s = g.score.to_numpy(dtype=float)
        consensus = float(np.average(s, weights=w))
        return pd.Series({"consensus": consensus,
                          "bds": float(np.sqrt(np.mean((s - consensus) ** 2))),
                          "k": len(s)})
    return (df.groupby(["essay_id", "cohort", "model", "condition"])
              .apply(agg, include_groups=False).reset_index())


def adjudicated_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Per essay x model x condition: the adjudicator's score (E2 path B)."""
    adj = df[df.agent == "adjudicator"]
    return adj[["essay_id", "cohort", "model", "condition",
                "score"]].rename(columns={"score": "adjudicated"})


def roc_calibrate(bds_values: np.ndarray, contested: np.ndarray
                  ) -> tuple[float, float]:
    """Choose tau by Youden's J; returns (tau, auc)."""
    fpr, tpr, thresholds = roc_curve(contested, bds_values)
    j = tpr - fpr
    return float(thresholds[np.argmax(j)]), float(auc(fpr, tpr))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    args = ap.parse_args()
    rows = [json.loads(l) for l in
            (Path(args.results) / "scores.jsonl").read_text().splitlines()]
    df = pd.DataFrame(rows)
    print(f"{len(df)} scoring calls, models: {sorted(df.model.unique())}")
    agg = consensus_and_bds(df)
    print(agg.groupby(["model", "condition", "cohort"])
             [["consensus", "bds"]].describe().round(3))


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------
# Writer-level clustering (ICNALE writers contribute up to two essays,
# one per topic; the unit of independence is the writer, not the essay)

def writer_id(essay_id: str) -> str:
    """WE_PHL_PTJ0_087_B1_2 -> WE_PHL_087 (country + student number)."""
    p = essay_id.split("_")
    return f"{p[0]}_{p[1]}_{p[3]}"


def gap_ci_cluster(agg: pd.DataFrame, n_boot: int = 10_000,
                   seed: int = 4139514) -> tuple[float, float, float]:
    """Native-minus-SEA mean consensus gap with a writer-cluster
    percentile bootstrap CI. `agg` has essay_id, cohort, consensus."""
    rng = np.random.default_rng(seed)
    out = {}
    for cohort in ("sea", "native"):
        g = agg[agg.cohort == cohort].copy()
        g["w"] = g.essay_id.map(writer_id)
        groups = [grp.consensus.to_numpy() for _, grp in g.groupby("w")]
        out[cohort] = groups
    point = (np.concatenate(out["native"]).mean()
             - np.concatenate(out["sea"]).mean())
    boots = np.empty(n_boot)
    for b in range(n_boot):
        means = []
        for cohort in ("native", "sea"):
            grp = out[cohort]
            pick = rng.integers(0, len(grp), len(grp))
            means.append(np.concatenate([grp[i] for i in pick]).mean())
        boots[b] = means[0] - means[1]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(point), float(lo), float(hi)


def paired_reduction_cluster(aggA: pd.DataFrame, aggB: pd.DataFrame,
                             n_boot: int = 10_000, seed: int = 4139514):
    """Gap(A) - Gap(B) on the same essays, writer-cluster bootstrap.
    Returns (reduction, lo, hi, p_one_sided_no_reduction)."""
    rng = np.random.default_rng(seed)
    piv = (pd.concat([aggA.assign(c="A"), aggB.assign(c="B")])
             .pivot_table(index=["essay_id", "cohort"], columns="c",
                          values="consensus").dropna().reset_index())
    piv["w"] = piv.essay_id.map(writer_id)
    cl = {}
    for cohort in ("sea", "native"):
        g = piv[piv.cohort == cohort]
        cl[cohort] = [(grp.A.to_numpy(), grp.B.to_numpy())
                      for _, grp in g.groupby("w")]
    def gaps(sel):
        nA = np.concatenate([cl["native"][i][0] for i in sel["native"]])
        nB = np.concatenate([cl["native"][i][1] for i in sel["native"]])
        sA = np.concatenate([cl["sea"][i][0] for i in sel["sea"]])
        sB = np.concatenate([cl["sea"][i][1] for i in sel["sea"]])
        return (nA.mean() - sA.mean()) - (nB.mean() - sB.mean())
    full = {c: np.arange(len(cl[c])) for c in cl}
    point = gaps(full)
    boots = np.empty(n_boot)
    for b in range(n_boot):
        sel = {c: rng.integers(0, len(cl[c]), len(cl[c])) for c in cl}
        boots[b] = gaps(sel)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(point), float(lo), float(hi), float((boots <= 0).mean())


def band_association(agg: pd.DataFrame, band_map: dict) -> float:
    """Spearman rho between panel score and the CEFR band ordinal on
    the banded (SEA) cohort. Replaces QWK, which compared a 1-9 score
    scale with 1-4 band codes and was therefore not an agreement
    statistic on a common category system."""
    from scipy.stats import spearmanr
    g = agg[agg.cohort == "sea"]
    if g.empty:
        return float("nan")
    return float(spearmanr(g.band.to_numpy(), g.consensus.to_numpy()).correlation)
