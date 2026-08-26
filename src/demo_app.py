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
    "5. IELTS Band 8.0 model essay — part-time jobs (prep material)": {
        "desc": "A published IELTS model answer on this demo's exact topic "
                "(user-supplied prep material, reported Band 8.0). "
                "High-band Western academic form: the panel should agree "
                "high.",
        "text": """In recent years working and studying simultaneously has become an important and widely debated issue. While some people maintain that a part time job is highly beneficial for a student's future, others reject this notion, believing that working is detrimental to a person's studies. Personally, I believe the drawbacks outweigh the advantages.

For a variety of reasons it can be worthwhile for students to get a job while they study. First of all, a student can gain vital knowledge in their given field. For example, if a person is studying to be a teacher, then working as a tutor in their free time will allow them to acquire experience before they begin their teaching career. Another advantage is the financial aspect. Many people rely on loans from their family or banks to partake in university. By having a part-time job students can earn money as they learn, which means they may not have the financial burden of paying back loans after they finish studying.

On the other hand, there are many negative aspects of working and studying at the same time. The biggest disadvantage is that work can be time-consuming. Students, especially those in university, have a heavy workload while studying due to numerous assignments and many tests throughout the course. If a student is overworked it could distract from their studies and cause them to lose focus, resulting in bad grades, which would affect their future careers. Moreover, students may have higher levels of stress due to their hectic schedules. This could result in a student feeling dejected with their career choice and they may even drop out of university.

Taking everything into account, although there are strong arguments to support the claim that working part time is advantageous, I am inclined to believe that it is better for students to focus on their studies because high grades often help them secure a better career in the future."""},
    "6. IELTS Band 8.5 model essay — urban housing (prep material)": {
        "desc": "A published IELTS model answer on a different topic "
                "(user-supplied prep material, reported Band 8.5). Tests "
                "the panel off-topic and at the top of the scale.",
        "text": """It is undeniable that soaring urban populations have pushed many residents into compact apartments without private outdoor areas. While not without drawbacks, I believe that the financial savings, reduced maintenance burdens, and access to communal amenities make small-space living a viable and largely positive development.

Living in small homes without outdoor space can harm both physical and mental well-being. One key concern is that limited access to nature and fresh air deprives residents of personal relaxation areas. Without gardens or balconies, individuals cannot easily soak up sunlight or enjoy ventilated environments. As a consequence, this lack of open space leads to increased stress levels and reduced physical activity. Equally troubling is the fact that cramped living conditions can hamper family life and child development. For instance, children confined to tiny flats lack safe, spacious areas in which to play and explore. In turn, their physical growth and creative play opportunities are significantly restricted.

Nonetheless, living in a smaller home offers certain advantages and can be effectively mitigated, which makes this trend largely positive. To begin with, lower costs and minimal upkeep make compact apartments financially attractive. Reduced square footage often results in lower rent or mortgage payments and less time required for cleaning and household chores. As a result, residents benefit from decreased living expenses and gain more time for leisure or personal pursuits. In addition, the absence of private outdoor spaces can be offset by access to shared urban amenities. For example, community parks, rooftop gardens, and nearby recreation centres provide alternative green environments for rest and recreation. Through this kind of thoughtful urban planning, city dwellers are able to enjoy fresh air and leisure activities outside their homes, maintaining a balanced lifestyle despite limited private space.

In conclusion, although the absence of private outdoor space can pose certain risks to residents' physical health and children's development, I believe that compact city apartments deliver considerable economic relief, reduced maintenance demands, and are easily compensated for by the convenience of shared urban infrastructure."""},
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
    {"id": "WEP_VNM_PTJ0_359_B2_0",
     "title": "Real case D - Vietnamese essay, B2+ (ICNALE WEP)",
     "desc": "Authentic Vietnamese student essay from the newest ICNALE "
             "module; used to validate the Mekong/Vietnamese lens."},
    {"id": "WEP_VNM_PTJ0_364_B1_2",
     "title": "Real case E - Vietnamese essay, B1 upper (ICNALE WEP)",
     "desc": "Authentic Vietnamese student essay, mid proficiency; the "
             "band where Experiment 1 found the bias concentrates."},
]

st.set_page_config(page_title="CAMPS demo", layout="wide")
st.markdown("""<style>
section[data-testid="stSidebar"] div.stButton > button {
  text-align: left; justify-content: flex-start;
}
section[data-testid="stSidebar"] div.stButton > button p {
  text-align: left;
}
</style>""", unsafe_allow_html=True)
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

def select(label: str, text: str, meta: dict | None = None) -> None:
    st.session_state["sel_label"] = label
    st.session_state["sel_text"] = text
    st.session_state["sel_meta"] = meta

with st.sidebar:
    st.header("Settings")
    model_name = st.selectbox("Model", [m["name"] for m in cfg["models"]],
                              index=1, key="model_sel")
    tau = st.slider("BDS threshold (tau)", 0.0, 2.0, 0.75, 0.05)
    compare_models = st.multiselect(
        "Compare with additional models",
        [m["name"] for m in cfg["models"]],
        help="Runs the same panel on each selected model and shows a "
             "cross-model comparison - the same essay, different "
             "graders. Cloud models recommended.")
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
            row_m = mf_all.loc[case["id"]]
            select(case["title"] + " — " + case["desc"], text,
                   {"essay_id": case["id"], "region": row_m.region,
                    "band": row_m.cefr, "cohort": row_m.cohort})

    st.markdown("**Synthetic demonstration essays**")
    for name, ex in EXAMPLES.items():
        if st.button(name, key=f"ex_{name}", use_container_width=True):
            select(name + " — " + ex["desc"], ex["text"])

    st.markdown("**GRA-rated essay (80 human raters)**")
    if st.button("Random GRA-rated ICNALE essay", use_container_width=True):
        row = (pd.read_csv(cfg["paths"]["manifest"])
               .query("cohort == 'gra'").sample(1).iloc[0])
        text = (Path(cfg["paths"]["icnale_root"]) / row.path
                ).read_text(encoding="utf-8-sig")
        select(f"{row.essay_id} (GRA, 80 human ratings)", text,
               {"essay_id": row.essay_id, "region": row.region,
                "band": row.cefr, "cohort": "gra"})

    st.markdown("**Random from the corpus**")
    cohort = st.radio("Cohort", ["sea", "native", "mekong_validation"],
                      horizontal=True, label_visibility="collapsed")
    if st.button("Random ICNALE essay", use_container_width=True):
        row = (pd.read_csv(cfg["paths"]["manifest"])
               .query("cohort == @cohort").sample(1).iloc[0])
        text = (Path(cfg["paths"]["icnale_root"]) / row.path
                ).read_text(encoding="utf-8-sig")
        select(f"{row.essay_id} ({cohort})", text,
               {"essay_id": row.essay_id, "region": row.region,
                "band": row.cefr, "cohort": cohort})

    st.divider()
    st.header("History")
    hist_path = Path("results/demo_history.jsonl")
    if hist_path.exists():
        recs = [json.loads(l) for l in hist_path.read_text().splitlines()]
        for i, r in enumerate(reversed(recs[-12:])):
            flag = "FLAG" if r["flagged"] else "ok"
            if st.button(
                    f"{r['label'][:34]} | {r['model']} | "
                    f"{r['consensus']:.1f} / BDS {r['bds']:.2f} [{flag}]",
                    key=f"hist_{i}", use_container_width=True):
                st.session_state["sel_label"] = r["label"]
                st.session_state["sel_text"] = r["text"]
                st.session_state["sel_meta"] = r.get("meta")
                st.session_state["model_sel"] = r["model"]
                st.rerun()
        st.caption("Click to replay instantly (served from cache - no "
                   "API calls).")
    else:
        st.caption("Completed analyses appear here for instant replay.")

model_cfg = next(m for m in cfg["models"] if m["name"] == model_name)
if model_cfg["provider"] == "ollama":
    st.sidebar.warning("Local thinking model: expect 30-90s per call "
                       "(7 calls per analysis, so 4-10 minutes total). "
                       "Cloud models respond in seconds.")
    import urllib.request
    base = __import__("os").environ.get("OLLAMA_BASE_URL",
                                        "http://localhost:11434/v1")
    try:
        urllib.request.urlopen(base.replace("/v1", "/api/tags"), timeout=2)
    except Exception:
        st.error("Ollama does not respond at " + base +
                 " - start it with `ollama serve` (or pick a cloud model).")
        st.stop()

with st.expander("Or paste your own essay"):
    txt = st.text_area("Essay text (English, ideally 150+ words)",
                       height=200)
    if st.button("Score pasted essay", type="primary"):
        select("manual input", txt.strip())

essay_label = st.session_state.get("sel_label")
essay_text = st.session_state.get("sel_text")

if essay_text:
    st.subheader(f"Analysing: {essay_label}")
    meta = st.session_state.get("sel_meta")
    if meta:
        gra_path = Path("results/gra_dispersion.csv")
        gra_row = None
        if gra_path.exists():
            g = pd.read_csv(gra_path).set_index("essay_id")
            if meta["essay_id"] in g.index:
                gra_row = g.loc[meta["essay_id"]]
        cols = st.columns(4 if gra_row is None else 6)
        cols[0].metric("Corpus", "ICNALE (Kobe)")
        cols[1].metric("Region", str(meta["region"]))
        cols[2].metric("Official CEFR band", str(meta["band"]))
        cols[3].metric("Cohort", str(meta["cohort"]))
        if gra_row is not None:
            cols[4].metric("Human mean (80 raters)",
                           f"{gra_row.content_mean:.2f} / 10")
            cols[5].metric("Human disagreement (SD)",
                           f"{gra_row.dispersion:.2f}")
            st.caption("Human ratings from the ICNALE Global Rating "
                       "Archives: mean of the Content dimensions across "
                       "80 raters (0-10 scale; the panel scores on the "
                       "1-9 band scale, so compare standing, not raw "
                       "values). Human raters themselves disagree by "
                       f"{gra_row.dispersion:.1f} points SD on this essay "
                       "- disagreement is normal in essay assessment.")
    essay_slot = st.container()
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
        '"rationale": "<2-3 sentences>", '
        '"evidence": [{"quote": "<EXACT short phrase copied verbatim from '
        'the essay>", "comment": "<why this matters under your '
        'calibration>", "sentiment": "positive|negative"}, ... 2-3 '
        'items]}\n\n'
        f"ESSAY:\n{essay_text}")
    eid = f"demoV3_{hash(essay_text) & 0xffffffff:x}"
    import time as _time
    call_log = []
    log_box = st.status("Running the CAMPS pipeline...", expanded=True)

    def timed_score(agent_name, display, system_prompt, uprompt):
        t0 = _time.time()
        log_box.write(f"→ {display}: calling {model_cfg['id']} ...")
        r = client.score(eid, agent_name, system_prompt, uprompt)
        dt = _time.time() - t0
        cached = dt < 0.5
        u = r.usage or {}
        call_log.append({
            "step": display, "score": r.score,
            "seconds": round(dt, 1),
            "tokens_in": u.get("in"), "tokens_out": u.get("out"),
            "cached": cached})
        log_box.write(
            f"   done in {dt:.1f}s - score {r.score:.1f}"
            + (" (cached)" if cached else
               f" - tokens {u.get('in','?')}/{u.get('out','?')}"))
        return r

    prog = st.progress(0.0, "Scoring with a standard AI grader...")
    baseline_res = timed_score(
        "neutral_single", "Standard grader (baseline)",
        Path("prompts/cri_neutral_single.txt").read_text(),
        'Score the following essay. Respond with JSON: '
        '{"score": <band>, "rationale": "<2-3 sentences>"}.\n\n'
        f"ESSAY:\n{essay_text}")
    results, details = [], {}
    for i, agent in enumerate(PANEL):
        res = timed_score(agent, f"{LENS_LABEL[agent]} lens",
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

    # ---- annotated essay with hover tooltips ----
    import html as _html
    spans = []
    low = essay_text.lower()
    for a in PANEL:
        for ev in (details.get(a, {}).get("evidence") or []):
            q = (ev.get("quote") or "").strip().strip('"')
            if len(q) < 8:
                continue
            pos = low.find(q.lower())
            if pos < 0:
                continue
            spans.append((pos, pos + len(q), a,
                          ev.get("sentiment", ""), ev.get("comment", "")))
    spans.sort()
    merged, last_end = [], -1
    for sp in spans:
        if sp[0] >= last_end:
            merged.append(sp)
            last_end = sp[1]
    out, cur = [], 0
    for start, end_, a, sent, comment in merged:
        out.append(_html.escape(essay_text[cur:start]))
        tip = _html.escape(f"{LENS_LABEL[a]} ({sent}): {comment}",
                           quote=True)
        colour = LENS_COLOR[a]
        border = "#2ca02c" if sent == "positive" else "#d62728"
        out.append(
            f'<span title="{tip}" style="background:{colour}33;'
            f'border-bottom:2px solid {border};border-radius:3px;'
            f'cursor:help;">{_html.escape(essay_text[start:end_])}</span>')
        cur = end_
    out.append(_html.escape(essay_text[cur:]))
    legend = " &nbsp; ".join(
        f'<span style="background:{LENS_COLOR[a]}33;padding:1px 6px;'
        f'border-radius:3px;">{LENS_LABEL[a]}</span>' for a in PANEL)
    with essay_slot.expander("Essay with lens highlights "
                             "(hover a highlight for the analysis)",
                             expanded=True):
        st.markdown(
            f'<div style="line-height:1.8;">{legend}<br><span '
            f'style="font-size:0.85em;color:#666;">underline green = '
            f'praised, red = penalised; hover for the lens comment'
            f'</span><hr>'
            + "".join(out).replace("\n\n", "<br><br>").replace("\n", "<br>")
            + "</div>", unsafe_allow_html=True)

    # ---- key findings summary ----
    findings = []
    delta = consensus - baseline_res.score
    hi_i = max(range(len(scores)), key=lambda i: scores[i])
    lo_i = min(range(len(scores)), key=lambda i: scores[i])
    spread = scores[hi_i] - scores[lo_i]
    if spread >= 1.0:
        findings.append(
            f"**Cultural divergence detected:** the "
            f"{LENS_LABEL[PANEL[lo_i]]} lens gave **{scores[lo_i]:.1f}** "
            f"while the {LENS_LABEL[PANEL[hi_i]]} lens gave "
            f"**{scores[hi_i]:.1f}** — a {spread:.1f}-band disagreement "
            f"about the same essay. The score depends on which rhetorical "
            f"tradition the evaluator assumes.")
    else:
        findings.append(
            f"**All five cultural lenses agree** (spread "
            f"{spread:.1f} bands): this essay's qualities are recognised "
            f"the same way across rhetorical traditions — no cultural "
            f"contest for this essay under {model_name}.")
    if abs(delta) >= 0.3:
        direction = "under-scored" if delta > 0 else "over-scored"
        findings.append(
            f"**The standard single grader {direction} this essay by "
            f"{abs(delta):.1f} bands** relative to the culturally-aware "
            f"panel — the per-essay footprint of the bias measured at "
            f"scale in Experiment 1.")
    else:
        findings.append(
            f"**Standard grader and panel agree** "
            f"({baseline_res.score:.1f} vs {consensus:.2f}): no cultural "
            f"penalty on this essay.")
    # dimension-level insight from the radar data
    dim_spread = {}
    for d in DIMS:
        vals = [details[a].get("dimensions", {}).get(d)
                for a in PANEL if details.get(a)]
        vals = [v for v in vals if v is not None]
        if len(vals) >= 3:
            dim_spread[d] = max(vals) - min(vals)
    if dim_spread:
        d_max = max(dim_spread, key=dim_spread.get)
        if dim_spread[d_max] >= 2:
            findings.append(
                f"**The lenses disagree most about "
                f"{DIM_LABEL[d_max].lower()}** "
                f"(spread {dim_spread[d_max]:.0f} points on the radar) — "
                f"the dimension where cultural expectations differ for "
                f"this essay.")
    findings.append(
        ("**Routing: flagged for human review** "
         f"(BDS {bds:.2f} ≥ τ {tau})." if bds >= tau else
         f"**Routing: automated score accepted** (BDS {bds:.2f} < "
         f"τ {tau})."))
    st.info("#### Key findings\n\n" + "\n\n".join(
        f"{i+1}. {f}" for i, f in enumerate(findings)))

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
    adj = timed_score("adjudicator", "Meta-adjudicator",
                      Path("prompts/adjudicator.txt").read_text(), adj_user)
    prog.progress(1.0, "Done")
    log_box.update(label="Pipeline complete", state="complete",
                   expanded=False)

    # ---- run log & computation details ----
    with st.expander("Run log and computation details"):
        st.dataframe(pd.DataFrame(call_log), use_container_width=True)
        st.markdown("**Consensus calculation (equal weights):**")
        st.latex(r"S^{*} = \\frac{1}{k}\\sum_i s_i = \\frac{"
                 + " + ".join(f"{x:.0f}" for x in scores)
                 + f"}}{{{len(scores)}}} = {consensus:.2f}")
        st.markdown("**Bias Divergence Score:**")
        st.latex(r"\\mathrm{BDS} = \\sqrt{\\frac{1}{k}\\sum_i (s_i - "
                 + f"{consensus:.2f}" + r")^2} = " + f"{bds:.2f}")
        st.caption(f"Cache: results/cache/ - repeated analyses of the "
                   f"same essay are instant and free. Model id: "
                   f"{model_cfg['id']}.")
    conf = None
    try:
        conf = json.loads(extract_json(adj.raw)).get("confidence")
    except Exception:
        pass
    # ---- cross-model comparison ----
    extra = [m for m in compare_models if m != model_name]
    if extra:
        st.divider()
        st.subheader("Cross-model comparison: same essay, different graders")
        comp_rows = [{
            "model": model_name,
            "standard grader": baseline_res.score,
            "panel consensus": round(consensus, 2),
            "BDS": round(bds, 2),
            "flagged": "YES" if bds >= tau else "no"}]
        lens_data = {model_name: scores}
        for mn in extra:
            mc = next(m for m in cfg["models"] if m["name"] == mn)
            cclient = ScoringClient(mc["provider"], mc["id"],
                                    Path(cfg["paths"]["cache"]),
                                    cfg["generation"]["max_retries"])
            log_box2 = st.status(f"Scoring with {mn}...", expanded=False)
            try:
                b = cclient.score(
                    eid, "neutral_single",
                    Path("prompts/cri_neutral_single.txt").read_text(),
                    'Score the following essay. Respond with JSON: '
                    '{"score": <band>, "rationale": "<2-3 sentences>"}'
                    f'.\n\nESSAY:\n{essay_text}')
                sc = []
                for agent in PANEL:
                    r = cclient.score(
                        eid, agent,
                        Path(f"prompts/cri_{agent}.txt").read_text(),
                        user_prompt)
                    sc.append(r.score)
                    log_box2.write(f"{LENS_LABEL[agent]}: {r.score:.1f}")
                cons2 = sum(sc) / len(sc)
                bds2 = (sum((x - cons2) ** 2 for x in sc) / len(sc)) ** 0.5
                comp_rows.append({
                    "model": mn, "standard grader": b.score,
                    "panel consensus": round(cons2, 2),
                    "BDS": round(bds2, 2),
                    "flagged": "YES" if bds2 >= tau else "no"})
                lens_data[mn] = sc
                log_box2.update(label=f"{mn}: done", state="complete")
            except Exception as exc:  # provider not configured, quota, etc.
                log_box2.update(label=f"{mn}: unavailable ({exc})"[:80],
                                state="error")
        st.dataframe(pd.DataFrame(comp_rows).set_index("model"),
                     use_container_width=True)
        figc = go.Figure()
        for mn, sc in lens_data.items():
            figc.add_trace(go.Bar(name=mn,
                                  x=[LENS_LABEL[a] for a in PANEL], y=sc))
        figc.update_layout(barmode="group", height=360,
                           yaxis=dict(range=[0, 9.5], title="band score"),
                           title="Lens scores by model")
        st.plotly_chart(figc, use_container_width=True)
        st.caption("The same essay, the same five cultural lenses, "
                   "different underlying models: differences between the "
                   "bars are the model-dependence documented in "
                   "Experiment 1 - which grader an institution licenses "
                   "is itself a fairness decision.")

    # ---- save to demo history (dedupe on essay+model) ----
    hist_path = Path("results/demo_history.jsonl")
    rec = {"ts": __import__("datetime").datetime.now().isoformat(
               timespec="seconds"),
           "label": essay_label, "model": model_name,
           "text": essay_text, "meta": st.session_state.get("sel_meta"),
           "baseline": baseline_res.score,
           "consensus": round(consensus, 2), "bds": round(bds, 2),
           "flagged": bool(bds >= tau)}
    existing = []
    if hist_path.exists():
        existing = [json.loads(l)
                    for l in hist_path.read_text().splitlines()]
    if not any(e["label"] == rec["label"] and e["model"] == rec["model"]
               for e in existing):
        with hist_path.open("a") as f:
            f.write(json.dumps(rec) + "\n")

    st.divider()
    st.subheader("Meta-adjudicator verdict")
    a1, a2 = st.columns([1, 4])
    a1.metric("Adjudicated score", f"{adj.score:.1f}",
              delta=(f"confidence {conf}" if conf is not None else None),
              delta_color="off")
    a2.write(adj.rationale)
