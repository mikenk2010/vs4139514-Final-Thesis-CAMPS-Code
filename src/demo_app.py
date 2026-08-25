"""CAMPS interactive demo (Streamlit) - v2 with charts and examples.

    pip install streamlit plotly
    streamlit run src/demo_app.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent))
from models import ScoringClient, extract_json  # noqa: E402

PANEL = ["western", "sea", "east_asian", "mekong", "neutral"]
LENS_LABEL = {"western": "Western", "sea": "Southeast Asian",
              "east_asian": "East Asian", "mekong": "Mekong/Vietnamese",
              "neutral": "Neutral"}
LENS_COLOR = {"western": "#1f77b4", "sea": "#ff7f0e", "east_asian": "#2ca02c",
              "mekong": "#d62728", "neutral": "#7f7f7f"}
DIMS = ["thesis_clarity", "organisation", "cohesion", "tone_hedging",
        "argument_support"]
DIM_LABEL = {"thesis_clarity": "Thesis clarity", "organisation": "Organisation",
             "cohesion": "Cohesion", "tone_hedging": "Tone & hedging",
             "argument_support": "Argument support"}

EXAMPLES = {
    "Western-style essay (deductive, thesis-first)": """College students should take a part-time job during their studies. Three reasons support this position: financial independence, transferable skills, and stronger employment prospects after graduation.

First, financial independence matters. A student who earns even a modest income covers daily expenses without depending entirely on family support. This reduces household pressure and teaches budgeting directly; managing one's own money is learned by doing it, not by reading about it.

Second, part-time work builds transferable skills. Serving customers trains communication under pressure. Meeting shift schedules trains reliability. Balancing work hours against assignment deadlines trains time management more effectively than any study-skills seminar. These abilities transfer directly to professional life.

Third, employers favour graduates with work experience. A resume that shows two years of part-time employment signals discipline and familiarity with workplace norms. Studies of graduate recruitment consistently show that candidates with employment history receive more interview offers than those without.

Critics argue that part-time work distracts from academic study, and excessive hours certainly can. However, the solution is moderation rather than avoidance: ten to fifteen hours per week is compatible with full academic performance for most students.

In conclusion, part-time employment develops financial independence, practical skills, and employability. Universities should encourage students to take moderate part-time work, because the benefits clearly outweigh the manageable risks. The case, on balance, is decisive.""",
    "Southeast Asian-style essay (inductive, context-first)": """My grandmother often says that a tree grows strong not from the wind that shakes it, but from the roots that hold it. When I think about students and part-time jobs, I think first of her words, and of my cousin Minh.

Minh comes from a family of rice farmers in the Mekong Delta. When he entered university in the city, his parents sold a buffalo to pay his first year of fees. In his second year, he began serving in a small noodle shop near the campus, four evenings each week. At first his mother worried that the work would pull him away from his books. Perhaps many families would share this worry, and it is not without reason.

Yet something else happened. Because his evenings had a price, Minh began to treasure his mornings. He planned his study before the week began, the way the shop owner planned her orders. When customers were rude, he learned patience; when the till was short, he learned carefulness. He sent a little money home, and one might say that with each transfer, he repaid not the buffalo but the trust.

His marks did not fall. They rose, slowly, like water finding its level.

It seems to me, then, that a part-time job is not truly separate from education. For students like Minh, and perhaps for most students, the shop and the classroom teach one lesson together: that effort, given steadily, becomes strength. This is why, in the end, I believe students should be encouraged to work while they study.""",
}

st.set_page_config(page_title="CAMPS demo", layout="wide")
st.title("CAMPS — Culturally-Aware Multi-Perspective Scoring")
st.markdown(
    "**The problem:** AI essay graders trained mostly on Western text "
    "under-score valid non-Western writing styles. **The solution "
    "demonstrated here:** a panel of five AI evaluators, each applying a "
    "documented cultural interpretation of the same rubric. Strong "
    "disagreement (a high **Bias Divergence Score**) flags the essay for "
    "human review — disagreement itself becomes a bias detector. "
    "This demo runs the same pipeline as the thesis experiments, with an "
    "extended output format for visual analysis.")

cfg = yaml.safe_load(Path("configs/experiment.yaml").read_text())
with st.sidebar:
    st.header("Settings")
    model_name = st.selectbox("Model", [m["name"] for m in cfg["models"]],
                              index=1)
    tau = st.slider("BDS threshold (tau)", 0.0, 2.0, 0.75, 0.05)
    st.caption("0.75 = pilot operating point; Experiment 3 calibrates "
               "this against 80 human raters.")
model_cfg = next(m for m in cfg["models"] if m["name"] == model_name)

tab_ex, tab_manual, tab_icnale = st.tabs(
    ["Built-in examples", "Paste an essay", "ICNALE sample (Kobe)"])
essay_text = essay_label = None
with tab_ex:
    st.caption("Two synthetic essays authored for this demonstration: the "
               "same position on the same topic, written in two rhetorical "
               "traditions. Watch the lenses disagree about the second one.")
    choice = st.radio("Choose an example", list(EXAMPLES), index=1)
    if st.button("Score this example", type="primary"):
        essay_text, essay_label = EXAMPLES[choice], choice
with tab_manual:
    txt = st.text_area("Essay text (English, ideally 150+ words)", height=240)
    if st.button("Score pasted essay", type="primary"):
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
    st.subheader(f"Analysing: {essay_label}")
    with st.expander("Show essay text"):
        st.write(essay_text)
    client = ScoringClient(model_cfg["provider"], model_cfg["id"],
                           Path(cfg["paths"]["cache"]),
                           cfg["generation"]["max_retries"])
    user_prompt = (
        "Score the following essay on the IELTS Coherence and Cohesion "
        "band descriptors, applying your calibration. Respond with JSON:\n"
        '{"score": <overall band 1-9>, '
        '"dimensions": {"thesis_clarity": <1-9>, "organisation": <1-9>, '
        '"cohesion": <1-9>, "tone_hedging": <1-9>, '
        '"argument_support": <1-9>}, '
        '"strengths": "<one sentence>", "weaknesses": "<one sentence>", '
        '"rationale": "<2-3 sentences>"}\n\n'
        f"ESSAY:\n{essay_text}")
    eid = f"demoV2_{hash(essay_text) & 0xffffffff:x}"
    results, details = [], {}
    prog = st.progress(0.0, "Scoring with the cultural panel...")
    for i, agent in enumerate(PANEL):
        res = client.score(eid, agent,
                           Path(f"prompts/cri_{agent}.txt").read_text(),
                           user_prompt)
        results.append(res)
        try:
            details[agent] = json.loads(extract_json(res.raw))
        except Exception:
            details[agent] = {}
        prog.progress((i + 1) / (len(PANEL) + 1),
                      f"{LENS_LABEL[agent]} scored: {res.score:.1f}")
    scores = [r.score for r in results]
    consensus = sum(scores) / len(scores)
    bds = (sum((s - consensus) ** 2 for s in scores) / len(scores)) ** 0.5

    # ---- score bar chart ----
    c_left, c_right = st.columns([1, 1])
    with c_left:
        fig = go.Figure(go.Bar(
            x=[LENS_LABEL[a] for a in PANEL], y=scores,
            marker_color=[LENS_COLOR[a] for a in PANEL],
            text=[f"{s:.1f}" for s in scores], textposition="outside"))
        fig.add_hline(y=consensus, line_dash="dash",
                      annotation_text=f"consensus {consensus:.2f}")
        fig.update_yaxes(range=[0, 9.5], title="band score")
        fig.update_layout(title="Overall score by cultural lens",
                          height=380, margin=dict(t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with c_right:
        radar = go.Figure()
        for a in PANEL:
            dims = details.get(a, {}).get("dimensions") or {}
            vals = [dims.get(d) for d in DIMS]
            if any(v is None for v in vals):
                continue
            radar.add_trace(go.Scatterpolar(
                r=vals + vals[:1],
                theta=[DIM_LABEL[d] for d in DIMS] + [DIM_LABEL[DIMS[0]]],
                name=LENS_LABEL[a], line_color=LENS_COLOR[a], opacity=0.75))
        radar.update_layout(
            title="Analytic profile per lens (spider)",
            polar=dict(radialaxis=dict(range=[0, 9], visible=True)),
            height=380, margin=dict(t=50, b=10))
        st.plotly_chart(radar, use_container_width=True)

    # ---- verdict row ----
    v1, v2, v3 = st.columns([1, 1, 2])
    v1.metric("Panel consensus", f"{consensus:.2f}")
    v2.metric("Bias Divergence Score", f"{bds:.2f}",
              delta=f"threshold {tau}", delta_color="off")
    with v3:
        if bds >= tau:
            st.error("**FLAGGED FOR HUMAN REVIEW** — the cultural lenses "
                     "disagree: this essay's score depends on which "
                     "rhetorical tradition the evaluator assumes.")
        else:
            st.success("**AUTOMATED SCORE ACCEPTED** — the lenses agree "
                       "regardless of cultural framing.")

    # ---- per-lens detail ----
    st.divider()
    st.subheader("What each lens saw")
    for a, res in zip(PANEL, results):
        d = details.get(a, {})
        with st.expander(f"{LENS_LABEL[a]} — score {res.score:.1f}"):
            if d.get("strengths"):
                st.markdown(f"**Strengths:** {d['strengths']}")
            if d.get("weaknesses"):
                st.markdown(f"**Weaknesses:** {d['weaknesses']}")
            st.markdown(f"**Rationale:** {d.get('rationale', res.rationale)}")

    # ---- adjudicator ----
    summary = "\n".join(f"Evaluator {i+1} ({LENS_LABEL[a]}) score: "
                        f"{r.score}. Rationale: {r.rationale}"
                        for i, (a, r) in enumerate(zip(PANEL, results)))
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
