"""Build the seminar showcase: a single self-contained HTML page, driven by the
thesis logs, with animated step-by-step reveals (arrow keys / click).

    python src/build_showcase.py            -> demo/showcase.html

The page embeds the essay text of the featured essays, so demo/showcase.html is
gitignored (ICNALE licence). Regenerate it on the presenting laptop; it works
offline, needs no server, and every number is read from results/.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).parent))

FEATURED = ["WE_PHL_PTJ0_087_B1_2", "WE_THA_PTJ0_237_B1_2", "WE_ENS_SMK0_073_XX_1"]
MODELS = ["gpt-4o", "claude-sonnet", "gemini-pro", "qwen3-local"]
LABEL = {"gpt-4o": "GPT-4o", "claude-sonnet": "Claude Sonnet 4.6",
         "gemini-pro": "Gemini 3.1 Pro", "qwen3-local": "Qwen3-14B (local)"}
PANEL5 = ["western", "sea", "east_asian", "mekong", "neutral"]


def bds(v):
    c = sum(v) / len(v)
    return c, (sum((x - c) ** 2 for x in v) / len(v)) ** 0.5


def main() -> None:
    cfg = yaml.safe_load(Path("configs/experiment.yaml").read_text())
    mf = pd.read_csv(cfg["paths"]["manifest"]).drop_duplicates("essay_id").set_index("essay_id")
    logs = pd.concat([pd.DataFrame([json.loads(l) for l in Path(f"results/{e}/scores.jsonl").read_text().splitlines()])
                      for e in ("E1", "E2")], ignore_index=True)
    summary = json.loads(Path("results/demo_summary.json").read_text())

    essays = {}
    for eid in FEATURED:
        text = (Path(cfg["paths"]["icnale_root"]) / mf.loc[eid, "path"]).read_text(encoding="utf-8-sig").strip()
        m = re.search(r"[.!?](\s|$)", text)
        cut = m.end() if m else 120
        per_model = {}
        for mdl in MODELS:
            r = logs[(logs.essay_id == eid) & (logs.model == mdl)]
            if r.empty:
                continue
            base = r[r.agent == "neutral_single"].iloc[0]
            k5 = r[r.condition == "camps_k5"]; k3 = r[r.condition == "camps_k3"]
            src = k5 if not k5.empty else k3
            lens = {a: {"score": float(src[src.agent == a].iloc[0].score),
                        "rationale": src[src.agent == a].iloc[0].rationale}
                    for a in PANEL5 if not src[src.agent == a].empty}
            adj = r[r.agent == "adjudicator"]
            c, b = bds([v["score"] for v in lens.values()])
            per_model[mdl] = {"baseline": {"score": float(base.score), "rationale": base.rationale},
                              "lens": lens, "consensus": round(c, 2), "bds": round(b, 2),
                              "adjudicator": (float(adj.iloc[0].score) if not adj.empty else None)}
        meta = mf.loc[eid]
        essays[eid] = {"id": eid, "opening": text[:cut], "rest": text[cut:],
                       "region": str(meta.region), "band": ("native, unbanded" if str(meta.cefr).startswith("XX") else str(meta.cefr)),
                       "cohort": str(meta.cohort), "words": len(text.split()), "models": per_model}

    # GRA: 140 essays x 80 human raters vs the five-lens panel (E3)
    from metrics import consensus_and_bds
    from scipy.stats import pearsonr, spearmanr
    e3 = pd.DataFrame([json.loads(l) for l in Path("results/E3/scores.jsonl").read_text().splitlines()])
    gd = pd.read_csv("results/gra_dispersion.csv")
    thr = float(gd.dispersion.quantile(0.75))
    a3 = consensus_and_bds(e3).merge(gd, on="essay_id")
    gra = {}
    for mdl in ["gpt-4o", "claude-sonnet"]:
        x = a3[a3.model == mdl]
        gra[mdl] = {"r": round(float(pearsonr(x.consensus, x.content_mean)[0]), 2),
                    "rho": round(float(spearmanr(x.consensus, x.content_mean)[0]), 2),
                    "pts": [{"h": round(float(r.content_mean), 2), "p": round(float(r.consensus), 2),
                             "c": int(r.dispersion >= thr), "id": r.essay_id} for r in x.itertuples()]}
    data = {"gra": gra, "essays": essays, "featured": FEATURED, "models": MODELS, "label": LABEL,
            "e1": summary["models"], "e2": summary["e2"], "lens_gaps": summary["lens_gaps"], "e3": summary["e3"]}
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    out = Path("demo/showcase.html"); out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>CAMPS — seminar showcase</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400;1,600&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{--cream:#EFEBE2;--cream2:#F8F5EE;--line:#D8D2C2;--ink:#16161A;--navy:#1E2333;--mute:#6E6A5E;--mute2:#9BA0B5;
  --orange:#C96A28;--blue:#4A69BD;--red:#B8503F;--teal:#2A9D8F;--grey:#7f7f7f;}
*{box-sizing:border-box} html,body{margin:0;height:100%;background:var(--cream);color:var(--ink);font-family:Inter,Helvetica,Arial,sans-serif;overflow:hidden}
.stage{position:relative;width:100vw;height:100vh}
.scene{position:absolute;inset:0;padding:5vh 6vw;display:none;flex-direction:column;opacity:0;transition:opacity .45s ease}
.scene.on{display:flex;opacity:1}
.scene.dark{background:var(--ink);color:var(--cream)}
.band{position:absolute;left:0;right:0;height:1.4vh;background:var(--ink)} .band.top{top:0}.band.bot{bottom:0}
.kicker{font-family:"JetBrains Mono",Menlo,monospace;font-size:1.3vh;letter-spacing:.25em;text-transform:uppercase;color:var(--orange);margin-bottom:1.2vh}
.dark .kicker{color:var(--orange)}
h1{font-family:"Playfair Display",Georgia,serif;font-weight:400;font-size:5.2vh;line-height:1.12;margin:0 0 1.6vh 0}
h1 em{font-style:italic;color:var(--orange)} h1 em.red{color:var(--red)} h1 em.blue{color:var(--blue)}
.sub{font-size:2vh;color:var(--mute);max-width:70vw;line-height:1.45}
.dark .sub{color:var(--mute2)}
.foot{position:absolute;bottom:2.6vh;left:6vw;right:6vw;display:flex;justify-content:space-between;font-family:"JetBrains Mono",Menlo,monospace;font-size:1.3vh;letter-spacing:.15em;color:var(--mute);border-top:1px solid var(--line);padding-top:1vh}
.dark .foot{color:var(--mute2);border-color:#333}
.grid{display:grid;gap:1.6vw;margin-top:2vh;flex:1;min-height:0}
.card{background:var(--cream2);border:1px solid var(--line);border-radius:1.2vh;padding:2vh 1.6vw;opacity:0;transform:translateY(18px);transition:all .5s cubic-bezier(.2,.8,.2,1)}
.card.in{opacity:1;transform:none}
.card .lbl{font-family:"JetBrains Mono",Menlo,monospace;font-size:1.25vh;letter-spacing:.2em;text-transform:uppercase;color:var(--mute)}
.card .desc{font-family:"Playfair Display",Georgia,serif;font-style:italic;font-size:1.7vh;margin:.6vh 0;color:#333}
.card .src{font-family:"JetBrains Mono",Menlo,monospace;font-size:1.15vh;color:var(--mute)}
.card .rat{font-size:1.55vh;line-height:1.5;color:#222;margin-top:1vh;border-top:1px solid var(--line);padding-top:1vh}
.card .num{font-family:"Playfair Display",Georgia,serif;font-size:6vh;line-height:1;font-weight:600}
.dcard{background:var(--navy);color:var(--cream);border-radius:1.2vh;padding:2.2vh 1.8vw;opacity:0;transform:translateY(18px);transition:all .5s cubic-bezier(.2,.8,.2,1)}
.dcard.in{opacity:1;transform:none}
.dcard .lbl{font-family:"JetBrains Mono",Menlo,monospace;font-size:1.25vh;letter-spacing:.2em;text-transform:uppercase;color:var(--mute2)}
.dcard .q{font-family:"Playfair Display",Georgia,serif;font-style:italic;font-size:2.1vh;line-height:1.5;margin-top:1vh}
.essay{background:var(--cream2);border:1px solid var(--line);border-radius:1.2vh;padding:3vh 2.4vw;font-family:"Playfair Display",Georgia,serif;font-size:2.25vh;line-height:1.7;overflow:auto;flex:1;min-height:0}
.essay mark{background:#F5D9BF;padding:0 .3em;border-radius:.3em}
.meta{display:flex;gap:1vw;margin:1.6vh 0}
.pill{font-family:"JetBrains Mono",Menlo,monospace;font-size:1.3vh;letter-spacing:.1em;border:1px solid var(--line);border-radius:999px;padding:.6vh 1.2vw;background:var(--cream2)}
.big{font-family:"Playfair Display",Georgia,serif;font-style:italic;font-size:14vh;line-height:1;font-weight:600}
.big small{font-size:4vh;color:var(--mute);font-style:normal}
.row{display:flex;gap:1.2vw;align-items:stretch}
.chips{display:flex;gap:.8vw;flex-wrap:wrap;margin:1.5vh 0}
.chip{border-radius:999px;color:#fff;padding:1vh 1.6vw;font-size:1.8vh;display:flex;align-items:center;gap:.8vw;opacity:0;transform:scale(.8);transition:all .45s cubic-bezier(.2,.8,.2,1)}
.chip.in{opacity:1;transform:none}
.chip b{font-family:"Playfair Display",Georgia,serif;font-size:3vh}
.modelbar{display:flex;gap:.6vw;margin-top:1.2vh}
.mbtn{font-family:"JetBrains Mono",Menlo,monospace;font-size:1.3vh;letter-spacing:.12em;text-transform:uppercase;border:1px solid var(--line);background:var(--cream2);padding:.8vh 1.2vw;border-radius:.8vh;cursor:pointer;color:var(--ink)}
.mbtn.on{background:var(--ink);color:var(--cream);border-color:var(--ink)}
.dark .mbtn{background:transparent;color:var(--cream);border-color:#444}.dark .mbtn.on{background:var(--cream);color:var(--ink)}
.bars{display:grid;grid-template-columns:repeat(4,1fr);gap:2vw;align-items:end;flex:1;min-height:0;margin-top:2vh;padding-bottom:1vh}
.bgroup{display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end}
.bpair{display:flex;gap:.8vw;align-items:flex-end;height:82%;width:100%;justify-content:center}
.bar{width:38%;border-radius:.6vh .6vh 0 0;height:0;transition:height 1.1s cubic-bezier(.2,.8,.2,1);position:relative}
.bar .v{position:absolute;top:-3.2vh;left:0;right:0;text-align:center;font-family:"Playfair Display",Georgia,serif;font-size:2.3vh;font-weight:600}
.bar .ci{position:absolute;left:50%;width:2px;background:rgba(0,0,0,.45);transform:translateX(-50%)}
.bname{font-family:"JetBrains Mono",Menlo,monospace;font-size:1.35vh;letter-spacing:.1em;margin-top:1.2vh;text-transform:uppercase}
.bnote{font-size:1.5vh;color:var(--mute);text-align:center;margin-top:.4vh;height:2.2vh}
.legend{display:flex;gap:2vw;font-size:1.6vh;margin-top:1vh}
.sw{display:inline-block;width:1.4vh;height:1.4vh;border-radius:.3vh;vertical-align:middle;margin-right:.5vw}
.verd{display:grid;grid-template-columns:1.4fr 1fr 2fr;gap:0;margin-top:2vh;border-top:1px solid var(--line)}
.verd div{padding:1.8vh 1vw;border-bottom:1px solid var(--line);font-size:1.9vh;opacity:0;transform:translateX(-12px);transition:all .5s}
.verd div.in{opacity:1;transform:none}
.verd .h{font-family:"Playfair Display",Georgia,serif;font-size:2.2vh}
.verd .v{font-family:"JetBrains Mono",Menlo,monospace;font-size:1.5vh;letter-spacing:.1em;text-transform:uppercase}
.ok{color:var(--blue)} .bad{color:var(--red)} .mid{color:var(--mute)}
.hint{position:absolute;right:6vw;top:4vh;font-family:"JetBrains Mono",Menlo,monospace;font-size:1.2vh;letter-spacing:.15em;color:var(--mute2)}
.sc{width:100%;height:100%} .sc .dot{opacity:0;transition:opacity .35s} .sc .dot.in{opacity:.85}
.sc text{font-family:Inter,Helvetica,sans-serif;font-size:2.2px;fill:#6E6A5E} .sc .ax{stroke:#D8D2C2;stroke-width:.3}
.gauge{height:1.6vh;background:var(--line);border-radius:999px;overflow:hidden;margin-top:1.2vh;position:relative}
.gauge i{display:block;height:100%;width:0;background:var(--orange);transition:width 1.1s cubic-bezier(.2,.8,.2,1)}
.gauge b{position:absolute;top:-.6vh;width:2px;height:2.8vh;background:var(--ink);left:0}
</style></head>
<body><div class="stage" id="stage"></div>
<script>
const D = __DATA__;
const LENS={western:"Western",sea:"Southeast Asian",east_asian:"East Asian",mekong:"Mekong",neutral:"Neutral"};
const DESC={western:["thesis first · linear progression · explicit links","Kaplan 1966 · Connor 2011"],
  sea:["thesis may emerge gradually · hedging as courtesy","Connor 2011 · Ishikawa 2023"],
  east_asian:["reader-responsible · late or implied thesis","Hinds 1987"],
  mekong:["proverb-anchored claims · indirectness as politeness","regional relevance · VN · TH · LA · KH"],
  neutral:["argumentative merit, regardless of ordering","a regulatory ideal · Fricker 2007"]};
const COL={western:"#4A69BD",sea:"#C96A28",east_asian:"#2A9D8F",mekong:"#B8503F",neutral:"#7f7f7f"};
let essayId=D.featured[0], model="gpt-4o", scene=0;
const esc=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
const n0=x=>Number.isInteger(x)?x.toFixed(0):x.toFixed(1);
function cur(){return D.essays[essayId].models[model];}
function modelbar(){return `<div class="modelbar">`+D.models.map(m=>`<button class="mbtn ${m===model?'on':''}" onclick="setModel('${m}')" ${D.essays[essayId].models[m]?'':'disabled style="opacity:.35"'}>${D.label[m]}</button>`).join("")+`</div>`;}
function setModel(m){model=m;render();}
function foot(l,n){return `<div class="foot"><span>${l}</span><span>${n} / 9 &nbsp;·&nbsp; → next · ← back · M model</span></div>`;}

const scenes=[
()=>`<div class="scene dark on"><div class="kicker">RMIT Vietnam · COSC2993 · Minor thesis seminar · September 2026</div>
 <h1 style="font-size:8vh;max-width:78vw;margin-top:8vh">The same essay.<br>Five readers.<br><em class="red">Two bands apart.</em></h1>
 <div class="sub" style="font-size:2.4vh;margin-top:2vh">CAMPS — Culturally-Aware Multi-Perspective Scoring. Every number on these screens is read from the thesis experiment logs: 200 ICNALE essays, four model families, 80 human raters.</div>
 <div class="hint">press → to begin</div>${foot("Bao Nguyen · s4139514 · supervisor Dr Ginel Dorleon","1")}</div>`,

()=>{const e=D.essays[essayId];return `<div class="scene on"><div class="band top"></div><div class="kicker">01 · A real essay from the corpus</div>
 <h1>She opens with a proverb and lets her position <em>emerge.</em></h1>
 <div class="meta"><span class="pill">${e.id.replace(/_/g," ")}</span><span class="pill">region ${e.region}</span><span class="pill">CEFR ${e.band}</span><span class="pill">${e.words} words</span><span class="pill">topic: part-time jobs</span></div>
 <div class="essay"><mark>${esc(e.opening)}</mark>${esc(e.rest).replace(/\n/g,"<br>")}</div>
 ${foot("Highlighted: the opening move that the lenses read differently","2")}<div class="band bot"></div></div>`;},

()=>{const c=cur();return `<div class="scene on"><div class="band top"></div><div class="kicker">02 · One standard AI grader · ${D.label[model]}</div>
 <h1>A plain IELTS prompt gives it <em class="blue">band ${n0(c.baseline.score)}.</em></h1>${modelbar()}
 <div class="row" style="margin-top:4vh;align-items:center"><div class="big">${n0(c.baseline.score)}<small> / 9</small></div>
 <div class="dcard in" style="flex:1;margin-left:3vw"><div class="lbl">the grader's rationale, verbatim</div><div class="q">“${esc(c.baseline.rationale)}”</div></div></div>
 <div class="sub" style="margin-top:3vh">IELTS Coherence &amp; Cohesion band, 1–9. The descriptors are named in the prompt, not reproduced: the score is the model's own reading of that rubric.</div>
 ${foot("Experiment 1 baseline · temperature 0 where supported · cached and logged","3")}<div class="band bot"></div></div>`;},

()=>{const c=cur();const ks=Object.keys(c.lens);const lo=ks.reduce((a,b)=>c.lens[a].score<=c.lens[b].score?a:b);const hi=ks.reduce((a,b)=>c.lens[a].score>=c.lens[b].score?a:b);
 const spread=c.lens[hi].score-c.lens[lo].score;
 return `<div class="scene on"><div class="band top"></div><div class="kicker">03 · Same essay, same model, five cultural lenses</div>
 <h1>Change the reader's cultural frame and the band moves <em class="red">${n0(spread)} band${spread==1?"":"s"}.</em></h1>${modelbar()}
 <div class="grid" style="grid-template-columns:repeat(${ks.length},1fr);flex:0 0 auto">${ks.map((a,i)=>`<div class="card" data-i="${i}" style="border-top:.6vh solid ${COL[a]}"><div class="lbl" style="color:${COL[a]}">${LENS[a]}</div><div class="num" style="color:${COL[a]}">${n0(c.lens[a].score)}</div><div class="desc">${DESC[a][0]}</div><div class="src">${DESC[a][1]}</div></div>`).join("")}</div>
 <div class="grid" style="grid-template-columns:1fr 1fr;flex:1"><div class="dcard" data-i="${ks.length}"><div class="lbl" style="color:${COL[lo]}">${LENS[lo]} lens · band ${n0(c.lens[lo].score)}</div><div class="q">“${esc(c.lens[lo].rationale)}”</div></div>
 <div class="dcard" data-i="${ks.length+1}"><div class="lbl" style="color:${COL[hi]}">${LENS[hi]} lens · band ${n0(c.lens[hi].score)}</div><div class="q">“${esc(c.lens[hi].rationale)}”</div></div></div>
 ${foot("One system prompt per lens · the agents never see each other · prompts verbatim in Appendix A","4")}<div class="band bot"></div></div>`;},

()=>{const c=cur();const vals=Object.values(c.lens).map(v=>v.score);const flag=c.bds>=0.40;
 return `<div class="scene on"><div class="band top"></div><div class="kicker">04 · Consensus and disagreement</div>
 <h1>The panel averages to <em class="blue">${c.consensus.toFixed(2)}</em> — and its disagreement is the <em>signal.</em></h1>${modelbar()}
 <div class="grid" style="grid-template-columns:1fr 1fr 1fr;flex:0 0 auto;margin-top:3vh">
  <div class="card" data-i="0"><div class="lbl">panel consensus S*</div><div class="num" style="color:var(--blue)">${c.consensus.toFixed(2)}</div><div class="desc">mean of ${vals.map(n0).join(", ")}${c.adjudicator!=null?` · meta-adjudicator ruled ${n0(c.adjudicator)}`:""}</div></div>
  <div class="card" data-i="1"><div class="lbl">Bias Divergence Score</div><div class="num" style="color:var(--orange)">${c.bds.toFixed(2)}</div><div class="desc">spread of the lens scores, in bands</div><div class="gauge"><i id="gauge" style="width:0"></i><b style="left:${(0.40/1.2*100).toFixed(1)}%"></b></div><div class="src">marker = Youden threshold 0.40</div></div>
  <div class="card" data-i="2" style="border-top:.6vh solid ${flag?'var(--red)':'var(--teal)'}"><div class="lbl">proposed review trigger</div><div class="num" style="font-size:4vh;color:${flag?'var(--red)':'var(--teal)'};padding:1.2vh 0">${flag?"FLAG · send to a human":"accept automated score"}</div><div class="desc">BDS ${c.bds.toFixed(2)} ${flag?"≥":"<"} τ 0.40</div></div>
 </div>
 <div class="dcard" data-i="3" style="margin-top:2.4vh"><div class="lbl">honesty note</div><div class="q">Experiment 3 tested this trigger against the disagreement of 80 human raters on 140 essays. At the specified 5% false-positive rate it caught 1 of 18 contested essays on GPT-4o and 0 of 18 on Claude. It is a candidate, not a validated detector — and that is reported as a finding.</div></div>
 ${foot("Consensus = weighted mean · BDS = √ mean squared deviation from the consensus","5")}<div class="band bot"></div></div>`;},

()=>{const e=D.essays[essayId];const ms=D.models.filter(m=>e.models[m]);
 return `<div class="scene on"><div class="band top"></div><div class="kicker">05 · The same essay under four graders</div>
 <h1>The effect is <em>model-dependent.</em> Which grader an institution licenses is itself a fairness decision.</h1>
 <div class="grid" style="grid-template-columns:repeat(${ms.length},1fr)">${ms.map((m,i)=>{const c=e.models[m];return `<div class="card" data-i="${i}"><div class="lbl">${D.label[m]}</div>
  <div class="row" style="align-items:baseline;gap:1vw;margin-top:1vh"><div class="num" style="font-size:4.2vh">${n0(c.baseline.score)}</div><div class="src">standard grader</div></div>
  <div class="chips">${Object.keys(c.lens).map(a=>`<span class="chip in" style="background:${COL[a]};padding:.6vh 1vw;font-size:1.4vh">${LENS[a]}<b style="font-size:2.2vh">${n0(c.lens[a].score)}</b></span>`).join("")}</div>
  <div class="src">consensus ${c.consensus.toFixed(2)} · BDS ${c.bds.toFixed(2)}${Object.keys(c.lens).length===3?" · 3-lens pilot panel (E1)":" · 5-lens panel (E2)"}</div></div>`;}).join("")}</div>
 ${foot("Gemini and Qwen3 ran the 3-lens pilot panel only (Experiment 1)","6")}<div class="band bot"></div></div>`;},

()=>{const ms=D.e1;const H=Math.max(...ms.map(m=>Math.max(m.baseline_ci[1],m.k3_ci[1])))*1.15;
 const bar=(v,ci,col,i)=>`<div class="bar" data-h="${(v/H*100).toFixed(1)}" style="background:${col}"><div class="v">${v.toFixed(2)}</div><div class="ci" style="bottom:${((ci[0]-v)/H*100).toFixed(1)}%;height:${((ci[1]-ci[0])/H*100).toFixed(1)}%"></div></div>`;
 return `<div class="scene on"><div class="band top"></div><div class="kicker">06 · At scale · 200 essays · 100 per cohort · 95% writer-cluster CIs</div>
 <h1>Every model scored Southeast Asian writing <em class="red">lower.</em> The panel narrowed the gap on two — and widened it on one.</h1>
 <div class="legend"><span><i class="sw" style="background:var(--red)"></i>standard grader</span><span><i class="sw" style="background:var(--blue)"></i>CAMPS 3-lens panel</span><span style="color:var(--mute)">bars = native − SEA gap in bands; whiskers = 95% CI</span></div>
 <div class="bars">${ms.map((m,i)=>`<div class="bgroup"><div class="bpair">${bar(m.baseline_gap,m.baseline_ci,"var(--red)",i)}${bar(m.k3_gap,m.k3_ci,"var(--blue)",i)}</div><div class="bname">${m.label}</div><div class="bnote">${m.reduction>0.05?`−${m.reduction_pct.toFixed(0)}%`:(m.reduction<-0.05?"amplified":"no clear change")}</div></div>`).join("")}</div>
 <div class="sub">An <b>unadjusted disparity</b>: the cohorts were not matched on human-judged quality, so this is consistent with cultural filtering but does not prove it. The panel narrows the gap by marking both cohorts down, the native cohort more.</div>
 ${foot("Thesis Figure 4-1 · Table 4.1 · writer-cluster bootstrap, 10,000 resamples","7")}<div class="band bot"></div></div>`;},

()=>{const g=D.gra[model==="claude-sonnet"?"claude-sonnet":"gpt-4o"];const mdl=model==="claude-sonnet"?"claude-sonnet":"gpt-4o";
 const W=100,H=62,x0=10,y0=6,x1=96,y1=54;const sx=h=>x0+(h/10)*(x1-x0);const sy=p=>y1-((p-1)/8)*(y1-y0);
 const pts=g.pts.map((q,i)=>`<circle class="dot" data-i="${Math.floor(i/6)}" cx="${sx(q.h).toFixed(2)}" cy="${sy(q.p).toFixed(2)}" r="1.1" fill="${q.c?'#B8503F':'#4A69BD'}"><title>${q.id}: human ${q.h}/10 · panel ${q.p}/9</title></circle>`).join("");
 const ticksX=[0,2,4,6,8,10].map(v=>`<line class="ax" x1="${sx(v)}" y1="${y1}" x2="${sx(v)}" y2="${y1+1}"/><text x="${sx(v)}" y="${y1+4}" text-anchor="middle">${v}</text>`).join("");
 const ticksY=[1,3,5,7,9].map(v=>`<line class="ax" x1="${x0-1}" y1="${sy(v)}" x2="${x0}" y2="${sy(v)}"/><text x="${x0-2}" y="${sy(v)+0.8}" text-anchor="end">${v}</text>`).join("");
 return `<div class="scene on"><div class="band top"></div><div class="kicker">07 · Human raters vs the AI panel · 140 GRA essays × 80 raters each</div>
 <h1>Where humans exist, the panel tracks them <em class="blue">closely</em> — in rank, not in level.</h1>
 <div class="modelbar"><button class="mbtn ${mdl==='gpt-4o'?'on':''}" onclick="setModel('gpt-4o')">GPT-4o</button><button class="mbtn ${mdl==='claude-sonnet'?'on':''}" onclick="setModel('claude-sonnet')">Claude Sonnet 4.6</button></div>
 <div class="row" style="flex:1;min-height:0;margin-top:1.5vh;gap:2.5vw">
  <div style="flex:1.35;min-width:0"><svg class="sc" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet"><rect x="${x0}" y="${y0}" width="${x1-x0}" height="${y1-y0}" fill="#F8F5EE" stroke="#D8D2C2" stroke-width=".3"/>${ticksX}${ticksY}
   <text x="${(x0+x1)/2}" y="${H-0.5}" text-anchor="middle">80-rater human mean, Content (0–10)</text><text transform="translate(2.5 ${(y0+y1)/2}) rotate(-90)" text-anchor="middle">panel consensus, IELTS C&amp;C band (1–9)</text>${pts}</svg></div>
  <div style="flex:1;display:flex;flex-direction:column;gap:1.6vh">
   <div class="card" data-i="0"><div class="lbl">association with 80 human raters</div><div class="num" style="color:var(--blue)">r = ${g.r.toFixed(2)}</div><div class="desc">Spearman ρ = ${g.rho.toFixed(2)} · ${D.label[mdl]}</div></div>
   <div class="card" data-i="1"><div class="lbl">what this does and does not show</div><div class="rat" style="border:0;padding:0;margin:0">The panel <b>orders</b> essays much as 80 humans do. It does <b>not</b> show calibration (different scales, different rubric: humans rated Content, lenses rated Coherence &amp; Cohesion), and it cannot settle the native−SEA question: this set has only four native essays.</div></div>
   <div class="card" data-i="2" style="border-top:.6vh solid var(--red)"><div class="lbl">the red dots</div><div class="rat" style="border:0;padding:0;margin:0"><span style="color:var(--red)">●</span> top-quartile human disagreement — the "contested" essays BDS was supposed to find. At the specified 5% false-positive rate it found 1 of 18 (GPT-4o) and 0 of 18 (Claude).</div></div>
  </div></div>
 ${foot("Thesis §4.4 human-anchored check (exploratory) · §4.3 Experiment 3","8")}<div class="band bot"></div></div>`;},

()=>`<div class="scene dark on"><div class="kicker">08 · Four hypotheses, four answers</div>
 <h1 style="color:var(--cream)">Two survived scrutiny. Two did not. <em>Both kinds are findings.</em></h1>
 <div class="verd" style="border-color:#333">
  <div class="h" data-i="0">H1 · a native−SEA gap on ≥ 4 models</div><div class="v ok" data-i="0">Supported — as an unadjusted disparity</div><div data-i="0">0.19 – 1.18 bands; every interval excludes zero; cultural cause not isolated</div>
  <div class="h" data-i="1">H2 · adjudicated 5 lenses beat 3</div><div class="v bad" data-i="1">Not supported (GPT-4o) · rejected (Claude)</div><div data-i="1">direct test +0.05 [−0.03, 0.14]; −0.10 [−0.18, −0.02]; no panel beat the SEA lens alone</div>
  <div class="h" data-i="2">H3 · BDS flags contested essays (90% / 5%)</div><div class="v bad" data-i="2">Not supported</div><div data-i="2">1/18 and 0/18 caught at ≤ 5% false positives; AUC 0.64 / 0.48; lenses disagreed more about native essays</div>
  <div class="h" data-i="3">H4 · a fairness–accuracy boundary</div><div class="v mid" data-i="3">Not testable against graded truth · small trade-off on a proxy</div><div data-i="3">10,626 weightings; equal weighting dominated; exploratory</div>
 </div>
 <div class="sub" style="margin-top:3vh;font-size:2.2vh;color:var(--cream)">The scoring gap is real and uneven; it is partially narrowable today, without retraining — and not yet self-diagnosing. Neither a single judge nor a diverse panel should be presumed fair without a test like this one.</div>
 ${foot("Thesis Table 5.1 · code and logs: github.com/mikenk2010/vs4139514-Final-Thesis-CAMPS-Code","9")}</div>`
];

function render(){const st=document.getElementById("stage");st.innerHTML=scenes[scene]();
 const els=[...st.querySelectorAll("[data-i]")];els.forEach(el=>setTimeout(()=>el.classList.add("in"),120+(el.classList.contains("dot")?60:180)*(+el.dataset.i)));
 st.querySelectorAll(".card:not([data-i]),.dcard:not([data-i])").forEach(el=>el.classList.add("in"));
 st.querySelectorAll(".chip:not(.in)").forEach((el,i)=>setTimeout(()=>el.classList.add("in"),150*i));
 st.querySelectorAll(".bar").forEach((b,i)=>setTimeout(()=>b.style.height=b.dataset.h+"%",200+120*i));
 const g=document.getElementById("gauge");if(g){const c=cur();setTimeout(()=>g.style.width=Math.min(100,c.bds/1.2*100)+"%",400);}
}
document.addEventListener("keydown",e=>{if(e.key==="ArrowRight"||e.key===" "||e.key==="PageDown"){scene=Math.min(scenes.length-1,scene+1);render();}
 else if(e.key==="ArrowLeft"||e.key==="PageUp"){scene=Math.max(0,scene-1);render();}
 else if(e.key.toLowerCase()==="m"){const i=D.models.indexOf(model);let j=i;do{j=(j+1)%D.models.length}while(!D.essays[essayId].models[D.models[j]]);model=D.models[j];render();}
 else if(e.key>="1"&&e.key<="3"){essayId=D.featured[+e.key-1];if(!D.essays[essayId].models[model])model="gpt-4o";render();}
 else if(e.key.toLowerCase()==="f"){document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen();}});
document.addEventListener("click",e=>{if(e.target.closest("button"))return;scene=Math.min(scenes.length-1,scene+1);render();});
render();
</script></body></html>
"""

if __name__ == "__main__":
    main()
