"""Direct H2 comparison: adjudicated five-lens panel vs three-lens pilot panel.
Writer-cluster paired bootstrap for the cohort-gap change and the
Spearman band-association change (thesis Section 4.2, Table 5.1)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from metrics import consensus_and_bds, adjudicated_scores, paired_reduction_cluster, writer_id
from scipy.stats import spearmanr

BAND = {"B1_2": 2, "B2_0": 3}

def main():
    load = lambda e: pd.DataFrame([json.loads(l) for l in open(f"results/{e}/scores.jsonl")])
    e1, e2 = load("E1"), load("E2")
    cef = dict(zip(e1.essay_id, e1.cefr))
    a1 = consensus_and_bds(e1)
    adj = adjudicated_scores(e2).rename(columns={"adjudicated": "consensus"})
    for m in ["gpt-4o", "claude-sonnet"]:
        k3 = a1[(a1.model == m) & (a1.condition == "camps_k3")]
        ad = adj[adj.model == m]
        red = paired_reduction_cluster(k3, ad)
        print(f"{m}: gap reduction k3 -> k5+adj = {red[0]:.3f} [{red[1]:.2f}, {red[2]:.2f}] p={red[3]:.4f}")
        sea = {k: v[v.cohort == "sea"].set_index("essay_id").consensus for k, v in {"k3": k3, "adj": ad}.items()}
        ids = sea["k3"].index
        w = pd.Series(ids.map(writer_id), index=ids)
        groups = [list(v.index) for _, v in w.groupby(w)]
        rng = np.random.default_rng(4139514)
        bb = np.array([BAND[cef[i]] for i in ids])
        pt = spearmanr(bb, sea["adj"][ids]).correlation - spearmanr(bb, sea["k3"][ids]).correlation
        boots = []
        for _ in range(10_000):
            pick = rng.integers(0, len(groups), len(groups))
            sel = [i for p in pick for i in groups[p]]
            b2 = np.array([BAND[cef[i]] for i in sel])
            boots.append(spearmanr(b2, sea["adj"][sel].values).correlation
                         - spearmanr(b2, sea["k3"][sel].values).correlation)
        print(f"   rho change k3 -> k5+adj = {pt:.3f} [{np.percentile(boots, 2.5):.3f}, {np.percentile(boots, 97.5):.3f}]")

if __name__ == "__main__":
    main()
