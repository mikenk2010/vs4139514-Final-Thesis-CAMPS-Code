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
plt.rcParams.update({"font.size": 11, "axes.labelsize": 11,
                     "xtick.labelsize": 10, "ytick.labelsize": 10,
                     "legend.fontsize": 10})
import numpy as np
import pandas as pd

from metrics import consensus_and_bds, gap_ci_cluster, paired_reduction_cluster
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
    vals = {}
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for j, (cond, label, colour) in enumerate(conds):
        xs, ys, los, his = [], [], [], []
        for i, m in enumerate(models):
            g = agg[(agg.model == m) & (agg.condition == cond)]
            sea = g[g.cohort == "sea"].consensus.to_numpy()
            nat = g[g.cohort == "native"].consensus.to_numpy()
            if len(sea) < 50 or len(nat) < 50:
                continue
            point, lo, hi = gap_ci_cluster(g)
            xs.append(i + (j - 0.5) * width)
            ys.append(point); los.append(point - lo); his.append(hi - point)
        ax.bar(xs, ys, width, label=label, color=colour,
               yerr=[los, his], capsize=4)
        for x, y, h in zip(xs, ys, his):
            ax.text(x, y + h + 0.03, f"{y:.2f}", ha="center", va="bottom",
                    fontsize=8.5)
        vals[cond] = dict(zip(models, ys))
    # change annotation above each model's pair
    ymax = ax.get_ylim()[1]
    for i, m in enumerate(models):
        b, k = vals["baseline"].get(m), vals["camps_k3"].get(m)
        if b is None or k is None:
            continue
        pct = (b - k) / b * 100
        if k > b * 1.5:
            txt, col = "widened", "#c44e52"
        elif abs(pct) < 20:
            txt, col = "no change", "#666666"
        else:
            txt, col = f"$-${pct:.0f}%", "#2e7d32"
        ax.text(i, ymax * 0.97, txt, ha="center", va="top", fontsize=9.5,
                fontstyle="italic", color=col)
    ax.set_ylim(top=ymax * 1.08)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([MODEL_LABEL[m] for m in models])
    ax.set_ylabel("Native $-$ SEA score gap (bands)")
    ax.set_title("Cohort score gap by model and condition\n"
                 "(95% writer-cluster bootstrap CIs, $n$=100 per cohort)")
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
        for x, y in zip(xs, ys):
            ax.text(x, y + 0.02, f"{y:.2f}", ha="center", va="bottom",
                    fontsize=9)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([MODEL_LABEL[m] for m in models])
    ax.set_ylabel("Baseline gap vs native cohort (bands)")
    ax.set_title("Baseline gap is largest for mid-proficiency (B1 upper) writing")
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
            point, lo, hi = gap_ci_cluster(agg)
            xs.append(i + (j - 1.5) * width)
            ys.append(point); los.append(point - lo); his.append(hi - point)
        if xs:
            ax.bar(xs, ys, width, label=label, color=colours[j],
                   yerr=[los, his], capsize=3)
            for x, y, h in zip(xs, ys, his):
                ax.text(x, y + h + 0.02, f"{y:.2f}", ha="center",
                        va="bottom", fontsize=7.5)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([MODEL_LABEL[m] for m in models])
    ax.set_ylabel("Native $-$ SEA score gap (bands)")
    ax.set_title("E2 ablation: cohort gap by panel configuration\n"
                 "(95% writer-cluster bootstrap CIs)")
    ax.set_ylim(top=ax.get_ylim()[1] * 1.15)
    ax.legend(loc="upper center", ncol=4, fontsize=8.5, frameon=False)
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
    gap, one point per model, writer-cluster paired-bootstrap 95% CIs.
    Descriptive: four model-level observations; the baseline gap enters
    both axes, so the picture is a summary, not a fitted dose-response."""
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for m in [x for x in MODEL_LABEL if x in set(agg.model)]:
        g = agg[agg.model == m]
        a, b = g[g.condition == "baseline"], g[g.condition == "camps_k3"]
        if a.empty or b.empty:
            continue
        base = (a[a.cohort == "native"].consensus.mean()
                - a[a.cohort == "sea"].consensus.mean())
        red, lo, hi, _ = paired_reduction_cluster(a, b, n_boot, seed)
        colour = "#4c72b0" if lo > 0 else ("#c44e52" if hi < 0 else "#8c8c8c")
        ax.errorbar(base, red, yerr=[[red - lo], [hi - red]], fmt="o",
                    ms=8, color=colour, capsize=4, lw=1.4)
        ax.annotate(MODEL_LABEL[m], (base, red), xytext=(8, 6),
                    textcoords="offset points", fontsize=10)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel("Baseline native $-$ SEA gap (bands)")
    ax.set_ylabel("Gap reduction under $k$=3 panel (bands)")
    ax.set_title("Model-dependent panel effect\n"
                 "(paired-bootstrap 95% CIs; blue = reduced, red = widened)")
    ax.set_xlim(left=0)
    fig.tight_layout()
    fig.savefig(out)
    print(f"wrote {out}")


def fig_case_study(e1: pd.DataFrame, e2: pd.DataFrame, out: Path,
                   essay: str = "WE_PHL_PTJ0_087_B1_2") -> None:
    """One essay, every lens, every model: a score grid showing the
    Western lens as the consistent low scorer on a proverb-opening,
    inductively organised essay."""
    df = pd.concat([e1, e2], ignore_index=True)
    df = df[df.essay_id == essay]
    agents = ["neutral_single", "western", "sea", "east_asian", "mekong",
              "neutral", "adjudicator"]
    labels = ["single evaluator\n(baseline)", "Western lens", "SEA lens",
              "East Asian lens", "Mekong lens", "Neutral lens",
              "adjudicator"]
    models = [m for m in MODEL_LABEL if m in set(df.model)]
    grid = np.full((len(agents), len(models)), np.nan)
    for j, m in enumerate(models):
        for i, a in enumerate(agents):
            s = df[(df.model == m) & (df.agent == a)].score
            if len(s):
                grid[i, j] = s.iloc[-1]   # k5 rows supersede k3 duplicates
    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    im = ax.imshow(grid, cmap="RdYlBu", vmin=4, vmax=8, aspect="auto")
    for i in range(len(agents)):
        for j in range(len(models)):
            v = grid[i, j]
            ax.text(j, i, "–" if np.isnan(v) else f"{v:.1f}",
                    ha="center", va="center", fontsize=11,
                    color="black", fontweight="bold" if agents[i] == "western" else "normal")
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([MODEL_LABEL[m] for m in models])
    ax.set_yticks(range(len(agents)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_title(f"One essay, every lens: {essay}\n"
                 "(proverb opening, thesis emerges inductively; band 1–9)",
                 fontsize=10)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("band")
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
        fig_case_study(df, e2, figs / "fig-case-study.pdf")
        fig_lens_radar(e2, figs / "fig-e2-lens-radar.pdf")
    dp = Path("results/gra_dispersion.csv")
    if e3p.exists() and dp.exists():
        e3 = pd.DataFrame([json.loads(l)
                           for l in e3p.read_text().splitlines()])
        disp = pd.read_csv(dp).set_index("essay_id")["dispersion"]
        fig_e3_roc(e3, disp, figs / "fig-e3-roc.pdf")


if __name__ == "__main__":
    main()
