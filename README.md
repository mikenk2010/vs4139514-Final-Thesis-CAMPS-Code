# CAMPS Part B — Experiment Pipeline

Config-driven pipeline for Experiments E1–E3.
**Never put ICNALE essay texts in this repo** — `data/` is gitignored; only
essay-ID manifests, configs, prompts, and aggregate results are committed.

## Layout
- `configs/experiment.yaml` — models, conditions, paths, seed
- `src/sample_icnale.py` — builds the stratified sampling manifest from the
  ICNALE download (per official file-naming rules)
- `src/models.py` — provider adapters (OpenAI / Anthropic / Google / Together),
  t=0.0 where supported, JSON output, disk cache; current Anthropic Messages
  models do not expose a temperature control
- `src/run_experiment.py` — essay × model × condition runner with JSON logging
- `src/metrics.py` — cohort gaps with writer-cluster bootstrap CIs, paired reduction tests, Spearman band association, BDS, ROC calibration (QWK retained for reference only)
- `src/h2_direct.py` — direct H2 comparison (adjudicated k=5 vs k=3, writer-cluster CIs)
- `src/make_demo_summary.py` — precomputes `results/demo_summary.json` for the demo's Findings tab
- `src/demo_app.py` — Streamlit seminar demo (see below)
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

## Seminar demo
```bash
pip install streamlit plotly
python src/make_demo_summary.py      # once; refresh if results change
streamlit run src/demo_app.py
```
Three tabs. **Essay explorer** shows the archived thesis scores and rationales
for any of the 340 scored essays (instant, no API calls, identical to the
thesis tables). **Findings** shows the E1–E3 results at scale from
`results/demo_summary.json`. **Live scoring** runs the exact thesis prompts on a
pasted essay or a Vietnamese WEP essay (API call), or on a thesis essay
(cache-served). Live runs are appended to `results/demo_history.jsonl`
(gitignored).

Two-minute demo path: Tab 1 → featured case A (GPT-4o) → open the Western and
Southeast Asian rationales → Tab 2 → Experiment 1 chart. Keep Tab 3 for Q&A.
