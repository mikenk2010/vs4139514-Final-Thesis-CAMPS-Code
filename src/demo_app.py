"""CAMPS interactive demo (Streamlit).

    pip install streamlit
    streamlit run src/demo_app.py

Paste any English essay, or load a sample from the ICNALE corpus
(Kobe University), and watch the five culturally-calibrated evaluators
score it, disagree, and route it - the full thesis pipeline, live.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent))
from models import ScoringClient, extract_json  # noqa: E402

PANEL = ["western", "sea", "east_asian", "mekong", "neutral"]
LENS_LABEL = {
    "western": "Western",
    "sea": "Southeast Asian",
    "east_asian": "East Asian",
    "mekong": "Mekong / Vietnamese",
    "neutral": "Neutral (regulatory ideal)",
}

st.set_page_config(page_title="CAMPS demo", layout="wide")
st.title("CAMPS — Culturally-Aware Multi-Perspective Scoring")
st.markdown(
    "**What you are looking at:** AI essay graders trained mostly on "
    "Western text tend to under-score valid non-Western writing styles. "
    "CAMPS scores every essay with a *panel of five AI evaluators*, each "
    "applying a documented cultural interpretation of the same rubric. "
    "When the panel disagrees strongly (a high **Bias Divergence Score**), "
    "the essay is flagged for a human — disagreement itself becomes a "
    "bias detector. This demo runs the exact pipeline used for the "
    "thesis experiments.")

cfg = yaml.safe_load(Path("configs/experiment.yaml").read_text())
with st.sidebar:
    st.header("Settings")
    model_name = st.selectbox("Model",
                              [m["name"] for m in cfg["models"]], index=1)
    tau = st.slider("BDS threshold (tau)", 0.0, 2.0, 0.75, 0.05)
    st.caption("tau = 0.75 is the pilot's operating point; Experiment 3 "
               "calibrates it against 80 human raters.")

model_cfg = next(m for m in cfg["models"] if m["name"] == model_name)

tab_manual, tab_icnale = st.tabs(["Paste an essay", "ICNALE sample (Kobe)"])
essay_text, essay_label = None, None
with tab_manual:
    txt = st.text_area("Essay text (English, ideally 150+ words)",
                       height=260, key="manual")
    if st.button("Score this essay", type="primary"):
        essay_text, essay_label = txt.strip(), "manual input"
with tab_icnale:
    cohort = st.radio("Cohort", ["sea", "native", "mekong_validation"],
                      horizontal=True)
    if st.button("Load and score a random ICNALE essay"):
        mf = pd.read_csv(cfg["paths"]["manifest"])
        row = mf[mf.cohort == cohort].sample(1).iloc[0]
        essay_text = (Path(cfg["paths"]["icnale_root"]) / row.path
                      ).read_text(encoding="utf-8-sig")
        essay_label = f"{row.essay_id} ({cohort})"

if essay_text:
    if len(essay_text.split()) < 30:
        st.warning("Very short text — results may be unreliable.")
    st.subheader(f"Analysing: {essay_label}")
    with st.expander("Show essay text"):
        st.write(essay_text)
    client = ScoringClient(model_cfg["provider"], model_cfg["id"],
                           Path(cfg["paths"]["cache"]),
                           cfg["generation"]["max_retries"])
    user_prompt = ('Score the following essay. Respond with JSON: '
                   '{"score": <band>, "rationale": "<2-3 sentences>"}.\n\n'
                   f"ESSAY:\n{essay_text}")
    eid = f"demo_{hash(essay_text) & 0xffffffff:x}"
    results = []
    prog = st.progress(0.0, "Scoring with the cultural panel...")
    for i, agent in enumerate(PANEL):
        res = client.score(eid, agent,
                           Path(f"prompts/cri_{agent}.txt").read_text(),
                           user_prompt)
        results.append(res)
        prog.progress((i + 1) / (len(PANEL) + 1),
                      f"{LENS_LABEL[agent]} scored...")
    scores = [r.score for r in results]
    consensus = sum(scores) / len(scores)
    bds = (sum((s - consensus) ** 2 for s in scores) / len(scores)) ** 0.5

    cols = st.columns(5)
    for c, agent, res in zip(cols, PANEL, results):
        with c:
            st.metric(LENS_LABEL[agent], f"{res.score:.1f}")
            st.caption(res.rationale)

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Panel consensus (equal weights)", f"{consensus:.2f}")
    c2.metric("Bias Divergence Score", f"{bds:.2f}",
              delta=f"threshold {tau}", delta_color="off")
    with c3:
        if bds >= tau:
            st.error("FLAGGED FOR HUMAN REVIEW\n\nThe cultural lenses "
                     "disagree: this essay's score depends on which "
                     "tradition the evaluator assumes.")
        else:
            st.success("AUTOMATED SCORE ACCEPTED\n\nThe lenses agree "
                       "regardless of cultural framing.")

    summary = "\n".join(f"Evaluator {i+1} score: {r.score}. "
                        f"Rationale: {r.rationale}"
                        for i, r in enumerate(results))
    adj_user = ("Five evaluators scored the same essay under different "
                "documented cultural interpretations of the rubric.\n"
                f"{summary}\n\nESSAY:\n{essay_text}\n\n"
                'Give your adjudicated score as JSON: {"score": <band>, '
                '"confidence": <0-1>, "rationale": "<3-4 sentences>"}')
    adj = client.score(eid, "adjudicator",
                       Path("prompts/adjudicator.txt").read_text(), adj_user)
    prog.progress(1.0, "Done")
    conf = None
    try:
        conf = json.loads(extract_json(adj.raw)).get("confidence")
    except Exception:
        pass
    st.divider()
    st.subheader("Meta-adjudicator verdict")
    a1, a2 = st.columns([1, 4])
    a1.metric("Adjudicated score", f"{adj.score:.1f}",
              delta=(f"confidence {conf}" if conf is not None else None),
              delta_color="off")
    a2.write(adj.rationale)
