"""Project E1/E2/E3 API costs from measured token usage in the logs.

Usage:
    python src/cost_estimate.py --results results/E1 \
        --price-in 2.50 --price-out 10.00     # USD per 1M tokens

Reads usage fields captured by models.py (calls made after the usage
patch); prints average tokens per call and projected costs for the
full experiment matrix at the given prices.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# call counts per model, from configs/experiment.yaml
CALLS = {
    "E1": 200 * (1 + 3),            # 200 essays x (baseline + k3)
    "E2": 200 * (5 + 6),            # k5 + k5_adj (incl. adjudicator call)
    "E3": 140 * 5,                  # GRA essays x k5
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/E1")
    ap.add_argument("--price-in", type=float, required=True,
                    help="USD per 1M input tokens")
    ap.add_argument("--price-out", type=float, required=True,
                    help="USD per 1M output tokens")
    args = ap.parse_args()

    rows = [json.loads(l) for l in
            (Path(args.results) / "scores.jsonl").read_text().splitlines()]
    used = [r["usage"] for r in rows if r.get("usage")]
    if not used:
        raise SystemExit(
            "No usage data in the log yet. Run a smoke test AFTER the "
            "usage-capture patch (clear results/cache first, or use "
            "--limit with fresh essays) and try again.")
    avg_in = sum(u["in"] for u in used) / len(used)
    avg_out = sum(u["out"] for u in used) / len(used)
    per_call = (avg_in * args.price_in + avg_out * args.price_out) / 1e6
    print(f"measured calls with usage: {len(used)}")
    print(f"avg tokens/call: in={avg_in:.0f}  out={avg_out:.0f}")
    print(f"cost per call at given prices: ${per_call:.4f}")
    print()
    for exp, n in CALLS.items():
        print(f"{exp}: {n} calls/model  ->  ${n * per_call:,.2f} per model")
    total = sum(CALLS.values())
    print(f"\nfull matrix on ONE model: {total} calls -> ${total * per_call:,.2f}")
    print("multiply by the number of models run per experiment; prices "
          "vary per provider, so run once per provider's price sheet.")


if __name__ == "__main__":
    main()
