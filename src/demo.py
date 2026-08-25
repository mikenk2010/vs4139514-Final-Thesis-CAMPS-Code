"""CAMPS live demo: score any essay through the full cultural panel.

Two modes:
  1) ICNALE sample (Kobe University data):
       python src/demo.py --icnale 2 --model gpt-4o
  2) Manual essay (paste your own text, or point at a file):
       python src/demo.py --file my_essay.txt --model gpt-4o
       python src/demo.py --model gpt-4o            # then paste, Ctrl-D to end

Shows per-agent scores and rationales, the weighted consensus, the
Bias Divergence Score, the adjudicator's reasoned verdict, and the
human-review routing decision.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import pandas as pd
import yaml

from models import ScoringClient, extract_json

PANEL = ["western", "sea", "east_asian", "mekong", "neutral"]
TAU_DEFAULT = 0.75  # pilot threshold; superseded by E3 calibration

BAR = "=" * 66


def score_essay(text: str, label: str, cfg: dict, model_cfg: dict,
                tau: float) -> None:
    client = ScoringClient(model_cfg["provider"], model_cfg["id"],
                           Path(cfg["paths"]["cache"]),
                           cfg["generation"]["max_retries"])
    user_prompt = (
        'Score the following essay. Respond with JSON: '
        '{"score": <band>, "rationale": "<2-3 sentences>"}.\n\n'
        f"ESSAY:\n{text}")
    print(f"\n{BAR}\nCAMPS panel analysis: {label}   "
          f"(model: {model_cfg['name']})\n{BAR}")
    words = len(text.split())
    print(f"Essay length: {words} words\n")
    results = []
    for agent in PANEL:
        prompt = Path(f"prompts/cri_{agent}.txt").read_text()
        res = client.score(f"demo_{hash(text) & 0xffffffff:x}", agent,
                           prompt, user_prompt)
        results.append(res)
        print(f"--- {agent.upper():<11s} score: {res.score:.1f}")
        print(f"    {res.rationale}\n")
    scores = [r.score for r in results]
    consensus = sum(scores) / len(scores)
    bds = (sum((s - consensus) ** 2 for s in scores) / len(scores)) ** 0.5
    print(f"{BAR}")
    print(f"Panel scores:     {[f'{s:.1f}' for s in scores]}")
    print(f"Consensus (equal weights): {consensus:.2f}")
    print(f"Bias Divergence Score:     {bds:.2f}  (threshold tau = {tau})")
    flag = bds >= tau
    print(f"Routing decision:  "
          f"{'FLAG FOR HUMAN REVIEW - culturally contested' if flag else 'automated score accepted'}")
    # adjudicator
    summary = "\n".join(
        f"Evaluator {i+1} score: {r.score}. Rationale: {r.rationale}"
        for i, r in enumerate(results))
    adj_user = ("Five evaluators scored the same essay under different "
                "documented cultural interpretations of the rubric.\n"
                f"{summary}\n\nESSAY:\n{text}\n\n"
                'Give your adjudicated score as JSON: {"score": <band>, '
                '"confidence": <0-1>, "rationale": "<3-4 sentences>"}')
    adj = client.score(f"demo_{hash(text) & 0xffffffff:x}", "adjudicator",
                       Path("prompts/adjudicator.txt").read_text(), adj_user)
    conf = None
    try:
        conf = json.loads(extract_json(adj.raw)).get("confidence")
    except Exception:
        pass
    print(f"\nMETA-ADJUDICATOR:  score {adj.score:.1f}"
          + (f"  (confidence {conf})" if conf is not None else ""))
    print(f"    {adj.rationale}")
    print(BAR)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/experiment.yaml")
    ap.add_argument("--model", default="gpt-4o")
    ap.add_argument("--tau", type=float, default=TAU_DEFAULT)
    ap.add_argument("--icnale", type=int, metavar="N",
                    help="score N random ICNALE essays (one SEA, one native "
                         "alternating)")
    ap.add_argument("--file", help="score an essay from a text file")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text())
    model_cfg = next(m for m in cfg["models"] if m["name"] == args.model)

    if args.icnale:
        manifest = pd.read_csv(cfg["paths"]["manifest"])
        rng = random.Random()
        picks = []
        for i in range(args.icnale):
            cohort = "sea" if i % 2 == 0 else "native"
            row = manifest[manifest.cohort == cohort].sample(
                1, random_state=rng.randint(0, 9999)).iloc[0]
            picks.append(row)
        for row in picks:
            text = (Path(cfg["paths"]["icnale_root"]) / row.path
                    ).read_text(encoding="utf-8-sig")
            score_essay(text, f"ICNALE {row.essay_id} ({row.cohort})",
                        cfg, model_cfg, args.tau)
    elif args.file:
        score_essay(Path(args.file).read_text(), Path(args.file).name,
                    cfg, model_cfg, args.tau)
    else:
        print("Paste the essay text, then press Ctrl-D:")
        text = sys.stdin.read().strip()
        if len(text.split()) < 50:
            print("Warning: very short text; results may be unreliable.")
        score_essay(text, "manual input", cfg, model_cfg, args.tau)


if __name__ == "__main__":
    main()
