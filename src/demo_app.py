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
    "1. Western style — deductive, thesis-first": {
        "desc": "States the thesis in sentence one, three signposted "
                "reasons, explicit transitions. The form Western-trained "
                "evaluators expect.",
        "text": """College students should take a part-time job during their studies. Three reasons support this position: financial independence, transferable skills, and stronger employment prospects after graduation.

First, financial independence matters. A student who earns even a modest income covers daily expenses without depending entirely on family support. This reduces household pressure and teaches budgeting directly; managing one's own money is learned by doing it, not by reading about it.

Second, part-time work builds transferable skills. Serving customers trains communication under pressure. Meeting shift schedules trains reliability. Balancing work hours against assignment deadlines trains time management more effectively than any study-skills seminar.

Third, employers favour graduates with work experience. A resume that shows two years of part-time employment signals discipline and familiarity with workplace norms, and candidates with employment history receive more interview offers than those without.

Critics argue that part-time work distracts from academic study, and excessive hours certainly can. However, the solution is moderation rather than avoidance: ten to fifteen hours per week is compatible with full academic performance for most students.

In conclusion, part-time employment develops financial independence, practical skills, and employability. Universities should encourage students to take moderate part-time work, because the benefits clearly outweigh the manageable risks."""},
    "2. Vietnamese/Mekong style — inductive, narrative-anchored": {
        "desc": "Opens with a proverb, argues through a family story, states "
                "its position only at the end. Valid reasoning in a "
                "reader-responsible tradition — watch the lenses disagree.",
        "text": """My grandmother often says that a tree grows strong not from the wind that shakes it, but from the roots that hold it. When I think about students and part-time jobs, I think first of her words, and of my cousin Minh.

Minh comes from a family of rice farmers in the Mekong Delta. When he entered university in the city, his parents sold a buffalo to pay his first year of fees. In his second year, he began serving in a small noodle shop near the campus, four evenings each week. At first his mother worried that the work would pull him away from his books. Perhaps many families would share this worry, and it is not without reason.

Yet something else happened. Because his evenings had a price, Minh began to treasure his mornings. He planned his study before the week began, the way the shop owner planned her orders. When customers were rude, he learned patience; when the till was short, he learned carefulness. He sent a little money home, and one might say that with each transfer, he repaid not the buffalo but the trust.

His marks did not fall. They rose, slowly, like water finding its level.

It seems to me, then, that a part-time job is not truly separate from education. For students like Minh, and perhaps for most students, the shop and the classroom teach one lesson together: that effort, given steadily, becomes strength. This is why, in the end, I believe students should be encouraged to work while they study."""},
    "3. East Asian style — four-part development with a turn": {
        "desc": "Introduction, development, an apparent digression (the "
                "'turn'), then conclusion; the central claim is implied "
                "before it is stated. Reader-responsible coherence.",
        "text": """In spring, the university noticeboard fills with two kinds of paper: examination schedules, and advertisements for part-time workers. Students pass both every day, and most pause at each.

The examination schedule speaks of one duty. Lectures, libraries, and laboratory hours ask for a student's whole attention, and teachers remind us that these years will not return. A scholarship student who fails a course loses more than a grade. This duty is real, and no serious person dismisses it.

Consider, however, the tea master. It is said that a master once sent his student not to practise the ceremony, but to work a season in the market. When the student returned, his tea had improved, though he had not touched the utensils. Handling money taught his hands care; serving strangers taught his eyes attention. What appeared to be a departure from training was training.

A part-time job may stand in the same relation to study. The hours given to work are not subtracted from education but folded into it, provided the proportion is kept. Perhaps ten hours in a week; not thirty. Kept in measure, the market becomes a second library. For this reason, students should be permitted, and quietly encouraged, to work alongside their studies."""},
    "4. Weak essay — unfocused (all lenses should agree)": {
        "desc": "Multiple unrelated topics, no unified argument. A control "
                "case: cultural lenses agree on genuine incoherence, so "
                "BDS stays low and the score is low.",
        "text": """Part-time jobs are one thing students think about. There are many jobs like cafe work, tutoring, and delivery. Some students like them. University food is also expensive now, and the canteen queue is very long at lunch time, which wastes time for everyone.

Another topic is online learning. Since the pandemic, many classes are recorded, so students can watch them later. This is convenient but some students never come to campus anymore, which changes friendship. Friendship at university is important because later in life it is hard to make friends.

About money, part-time jobs give money. But scholarships also give money, and some students get money from parents. There are many ways to get money, and each way is different for each person, so it is hard to say which is best.

Also, health is important. Students should sleep eight hours and do exercise. A job at night is bad for sleep. But morning jobs are hard because of classes. In conclusion, there are many factors and everyone should decide for themselves what is good for their own situation and future."""},
}

REAL_CASES = [
    {"id": "WE_PHL_PTJ0_087_B1_2",
     "title": "Real case A - Philippine essay, B1 upper",
     "desc": "The largest lens disagreement in Experiment 1: the Western "
             "lens scored it 5.0, the SEA and Neutral lenses 7.0. "
             "Two full bands hang on the evaluator's cultural assumption."},
    {"id": "WE_IDN_PTJ0_113_B1_2",
     "title": "Real case B - Indonesian essay, B1 upper",
     "desc": "Western lens 5.0 vs SEA/Neutral 6.0 in Experiment 1: the "
             "typical one-band penalty documented across the corpus."},
    {"id": "WE_IDN_PTJ0_161_B2_0",
     "title": "Real case C - Indonesian essay, B2+ (high proficiency)",
     "desc": "Even at the top proficiency band: Western 5.0 vs SEA/Neutral "
             "6.0. The bias shrinks with proficiency but does not vanish."},
]

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

def select(label: str, text: str) -> None:
    st.session_state["sel_label"] = label
    st.session_state["sel_text"] = text

with st.sidebar:
    st.header("Settings")
    model_name = st.selectbox("Model", [m["name"] for m in cfg["models"]],
                              index=1)
    tau = st.slider("BDS threshold (tau)", 0.0, 2.0, 0.75, 0.05)
    st.caption("0.75 = pilot operating point; Experiment 3 calibrates "
               "this against 80 human raters.")

    st.divider()
    st.header("Samples")
    st.caption("Click any sample to run the full analysis.")

    st.markdown("**Real ICNALE essays (Kobe University)** — selected from "
                "the Experiment 1 logs as the largest measured lens "
                "disagreements.")
    mf_all = (pd.read_csv(cfg["paths"]["manifest"])
              .drop_duplicates("essay_id").set_index("essay_id"))
    for case in REAL_CASES:
        if case["id"] not in mf_all.index:
            continue
        if st.button(case["title"], key=f"real_{case['id']}",
                     use_container_width=True):
            text = (Path(cfg["paths"]["icnale_root"])
                    / mf_all.loc[case["id"], "path"]
                    ).read_text(encoding="utf-8-sig")
            select(case["title"] + " — " + case["desc"], text)

    st.markdown("**Synthetic demonstration essays**")
    for name, ex in EXAMPLES.items():
        if st.button(name, key=f"ex_{name}", use_container_width=True):
            select(name + " — " + ex["desc"], ex["text"])

    st.markdown("**Random from the corpus**")
    cohort = st.radio("Cohort", ["sea", "native", "mekong_validation"],
                      horizontal=True, label_visibility="collapsed")
    if st.button("Random ICNALE essay", use_container_width=True):
        row = (pd.read_csv(cfg["paths"]["manifest"])
               .query("cohort == @cohort").sample(1).iloc[0])
        text = (Path(cfg["paths"]["icnale_root"]) / row.path
                ).read_text(encoding="utf-8-sig")
        select(f"{row.essay_id} ({cohort})", text)

model_cfg = next(m for m in cfg["models"] if m["name"] == model_name)

with st.expander("Or paste your own essay"):
    txt = st.text_area("Essay text (English, ideally 150+ words)",
                       height=200)
    if st.button("Score pasted essay", type="primary"):
        select("manual input", txt.strip())

essay_label = st.session_state.get("sel_label")
essay_text = st.session_state.get("sel_text")

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
    prog = st.progress(0.0, "Scoring with a standard AI grader...")
    baseline_res = client.score(
        eid, "neutral_single",
        Path("prompts/cri_neutral_single.txt").read_text(),
        'Score the following essay. Respond with JSON: '
        '{"score": <band>, "rationale": "<2-3 sentences>"}.\n\n'
        f"ESSAY:\n{essay_text}")
    results, details = [], {}
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

    # ---- the bias, made visible ----
    st.divider()
    b1, b2, b3 = st.columns([1, 1, 2])
    b1.metric("Standard AI grader (single evaluator)",
              f"{baseline_res.score:.1f}")
    b2.metric("Culturally-aware panel (consensus)", f"{consensus:.2f}",
              delta=f"{consensus - baseline_res.score:+.2f} vs standard")
    with b3:
        st.caption(f"**Standard grader's rationale:** "
                   f"{baseline_res.rationale}")

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
