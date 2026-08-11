# CAMPS Part B — Experiment Pipeline

Config-driven pipeline for Experiments E1–E3.
**Never put ICNALE essay texts in this repo** — `data/` is gitignored; only
essay-ID manifests, configs, prompts, and aggregate results are committed.

## Layout
- `configs/experiment.yaml` — models, conditions, paths, seed
- `src/sample_icnale.py` — builds the stratified sampling manifest from the
  ICNALE download (per official file-naming rules)
- `src/models.py` — provider adapters (OpenAI / Anthropic / Google / Together),
  t=0.0, JSON output, disk cache
- `src/run_experiment.py` — essay × model × condition runner with JSON logging
- `src/metrics.py` — QWK, bootstrap CIs, Fisher z, BDS, ROC
- `prompts/` — CRI system prompts (verbatim copies go to thesis Appendix A)

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install pyyaml pandas numpy scikit-learn scipy openai anthropic google-genai openpyxl
cp .env.example .env   # add your personal API keys
```

## Usage
```bash
# 1. after unzipping ICNALE into data/ (passwords from registration):
python src/sample_icnale.py --config configs/experiment.yaml
# 2. run an experiment condition:
python src/run_experiment.py --config configs/experiment.yaml --experiment E1
# 3. compute metrics:
python src/metrics.py --results results/E1
```
