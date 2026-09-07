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
               seed: int = 4139514) -> None:
    """E3: ROC of BDS against top-quartile human dispersion, held-out
    split, per model, plus the BDS-vs-dispersion scatter."""
    from sklearn.metrics import roc_curve, roc_auc_score
    colours = {"gpt-4o": "#4c72b0", "claude-sonnet": "#c44e52"}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    n_hold = None
    for model, colour in colours.items():
        sub = e3[(e3.model == model) & (e3.cohort == "gra")]
        if sub.empty:
            continue
        agg = consensus_and_bds(sub).set_index("essay_id")
        common = agg.index.intersection(dispersion.index)
        agg = agg.loc[common]
        disp = dispersion.loc[common]
        contested = (disp >= disp.quantile(0.75)).astype(int)
        rng = np.random.default_rng(seed)
        idx = rng.permutation(len(agg))
        hold = idx[len(idx) // 2:]
        n_hold = len(hold)
        y, s = contested.to_numpy()[hold], agg.bds.to_numpy()[hold]
        fpr, tpr, _ = roc_curve(y, s)
        auc = roc_auc_score(y, s)
        ax1.plot(fpr, tpr, color=colour, lw=1.8,
                 label=f"{MODEL_LABEL[model]} (AUC = {auc:.2f})")
        r = np.corrcoef(disp, agg.bds)[0, 1]
        ax2.scatter(disp, agg.bds, s=12, alpha=0.55, color=colour,
                    label=f"{MODEL_LABEL[model]} ($r$={r:.2f})")
    ax1.plot([0, 1], [0, 1], "--", color="grey", lw=1, label="chance")
    ax1.set_xlabel("False-positive rate")
    ax1.set_ylabel("Sensitivity")
    ax1.set_title(f"ROC, held-out GRA split ($n$={n_hold})")
    ax1.legend()
    ax2.set_xlabel("Human rating dispersion (SD across 80 raters)")
    ax2.set_ylabel("BDS ($k$=5 panel)")
    ax2.set_title(f"BDS vs human dispersion (all {len(agg)} matched essays)")
    ax2.legend()
    fig.tight_layout()
    fig.savefig(out)
    print(f"wrote {out}")


def fig_lens_radar(e2: pd.DataFrame, out: Path) -> None:
    """Radar chart: mean lens-level score per cohort, per model, on the
    five-lens panel -- the visual signature of cultural divergence."""
    agents = ["western", "sea", "east_asian", "mekong", "neutral"]
    labels = ["Western", "SEA", "East Asian", "Mekong", "Neutral"]
    models = [m for m in MODEL_LABEL if m in set(e2.model)]
    angles = np.linspace(0, 2 * np.pi, len(agents),
                         endpoint=False).tolist()
    angles += angles[:1]
    fig, axes = plt.subplots(1, len(models), figsize=(9.6, 4.4),
                             subplot_kw={"projection": "polar"})
    if len(models) == 1:
        axes = [axes]
    for ax, mdl in zip(axes, models):
        sub = e2[(e2.model == mdl) & (e2.condition == "camps_k5")
                 & (e2.agent != "adjudicator")]
        for cohort, colour in [("native", "#c44e52"), ("sea", "#4c72b0")]:
            g = sub[sub.cohort == cohort]
            vals = [g[g.agent == a].score.mean() for a in agents]
            vals += vals[:1]
            ax.plot(angles, vals, color=colour, lw=1.8,
                    label={"native": "Native cohort",
                           "sea": "SEA cohort"}[cohort])
            ax.fill(angles, vals, color=colour, alpha=0.12)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylim(3, 7)
        ax.set_yticks([3, 4, 5, 6, 7])
        ax.tick_params(axis="y", labelsize=7)
        ax.set_title(MODEL_LABEL[mdl], pad=16)
    axes[0].legend(loc="upper center", bbox_to_anchor=(1.12, -0.08),
                   ncol=2, frameon=False)
    fig.tight_layout()
    fig.savefig(out)
    print(f"wrote {out}")


def fig_dose_response(agg: pd.DataFrame, out: Path,
                      n_boot: int = 10_000, seed: int = 4139514) -> None:
    """E1: change in cohort gap under the k=3 panel against the baseline
    gap, one point per model, with paired-bootstrap 95% CIs -- the
    dose-response picture (reduce / inert / over-correct)."""
    rng = np.random.default_rng(seed)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for m in [x for x in MODEL_LABEL if x in set(agg.model)]:
        g = agg[agg.model == m]
        piv = g.pivot_table(index=["essay_id", "cohort"],
                            columns="condition", values="consensus")
        if "baseline" not in piv or "camps_k3" not in piv:
            continue
        piv = piv.dropna().reset_index()
        nat, sea = piv[piv.cohort == "native"], piv[piv.cohort == "sea"]
        base = nat.baseline.mean() - sea.baseline.mean()
        red = base - (nat.camps_k3.mean() - sea.camps_k3.mean())
        boots = np.empty(n_boot)
        for b in range(n_boot):
            ni = rng.integers(0, len(nat), len(nat))
            si = rng.integers(0, len(sea), len(sea))
            gb = nat.baseline.values[ni].mean() - sea.baseline.values[si].mean()
            gk = nat.camps_k3.values[ni].mean() - sea.camps_k3.values[si].mean()
            boots[b] = gb - gk
        lo, hi = np.percentile(boots, [2.5, 97.5])
        colour = "#4c72b0" if red > 0 and lo > 0 else (
            "#c44e52" if hi < 0 else "#8c8c8c")
        ax.errorbar(base, red, yerr=[[red - lo], [hi - red]], fmt="o",
                    ms=8, color=colour, capsize=4, lw=1.4)
        ax.annotate(MODEL_LABEL[m], (base, red), xytext=(8, 6),
                    textcoords="offset points", fontsize=10)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel("Baseline native $-$ SEA gap (bands)")
    ax.set_ylabel("Gap reduction under $k$=3 panel (bands)")
    ax.set_title("Mitigation is dose-dependent: reduction vs baseline gap\n"
                 "(paired bootstrap 95% CIs; blue = reduced, red = widened)")
    ax.set_xlim(left=0)
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
    fig_dose_response(agg, figs / "fig-e1-dose-response.pdf")
    e2p, e3p = Path("results/E2/scores.jsonl"), Path("results/E3/scores.jsonl")
    if e2p.exists():
        e2 = pd.DataFrame([json.loads(l)
                           for l in e2p.read_text().splitlines()])
        fig_e2_ablation(df, e2, figs / "fig-e2-ablation.pdf")
        fig_lens_radar(e2, figs / "fig-e2-lens-radar.pdf")
    dp = Path("results/gra_dispersion.csv")
    if e3p.exists() and dp.exists():
        e3 = pd.DataFrame([json.loads(l)
                           for l in e3p.read_text().splitlines()])
        disp = pd.read_csv(dp).set_index("essay_id")["dispersion"]
        fig_e3_roc(e3, disp, figs / "fig-e3-roc.pdf")


if __name__ == "__main__":
    main()
