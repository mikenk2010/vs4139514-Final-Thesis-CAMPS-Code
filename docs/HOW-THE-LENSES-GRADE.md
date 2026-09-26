# How the CAMPS lenses grade an essay — the exact instructions, side by side

Bao Nguyen · s4139514 · reference sheet for the seminar Q&A. Everything below is copied from `Code/prompts/` (verbatim in thesis Appendix A) and `Code/src/run_experiment.py` / `models.py`. No markdown files are used; each lens is a **plain-text system prompt** of 20–114 words.

---

## 1. One scoring call, step by step

Every score in the thesis — baseline, each lens, each model — is produced by the same three-part call:

| Part | Content | Same for every lens? |
|---|---|---|
| **System prompt** | The lens file (`prompts/cri_<lens>.txt`). Defines who the evaluator is and which four rhetorical conventions to recognise. | **No — this is the only thing that differs.** |
| **User turn** | `Score the following essay. Respond with JSON: {"score": <band>, "rationale": "<2-3 sentences>"}.` then a blank line, `ESSAY:` and the full essay text. | Yes, byte-identical. |
| **Settings** | Temperature 0 where the client exposes it (not in the pinned Anthropic client); JSON output requested; response cached by (model, agent, essay, system prompt, user prompt) and logged as one JSON line. | Yes. |

The model returns `{"score": 7, "rationale": "…"}`. The score is an **IELTS Coherence & Cohesion band, 1–9** (whole bands requested; Qwen3 returned half-bands in 295/800 calls, GPT-4o in 34/3,700; kept as returned).

The five lens calls are made **independently** — no lens sees another's output. Aggregation happens afterwards: consensus S* = mean of the five bands; BDS = standard deviation of the five bands.

```
essay ──┬─▶ [system: Western]        + user turn ──▶ score, rationale ─┐
        ├─▶ [system: Southeast Asian] + user turn ──▶ score, rationale ─┤
        ├─▶ [system: East Asian]      + user turn ──▶ score, rationale ─┼─▶ S* = mean · BDS = spread ─▶ (optional) adjudicator
        ├─▶ [system: Mekong]          + user turn ──▶ score, rationale ─┤
        └─▶ [system: Neutral]         + user turn ──▶ score, rationale ─┘
```

---

## 2. The shared skeleton

Every lens prompt has exactly this shape; only the bracketed parts change:

> You are an essay evaluator **calibrated to [tradition]**. Evaluate coherence and cohesion **[based on / recognising that]**: (1) **[convention]**, (2) **[convention]**, (3) **[convention]**, (4) **[convention]**. Score 1-9 on the IELTS Coherence and Cohesion band descriptors.

Note the verb: the Western and Neutral lenses say *"based on"* (these are the criteria); the Southeast Asian, East Asian and Mekong lenses say *"recognising that"* (these forms are to be accepted as valid). That single word is the mechanism by which a lens stops penalising a rhetorical move.

---

## 3. The six evaluators, side by side

| | Standard grader (baseline) | Western | Southeast Asian | East Asian | Mekong / Vietnamese | Neutral |
|---|---|---|---|---|---|---|
| **File** | `cri_neutral_single.txt` | `cri_western.txt` | `cri_sea.txt` | `cri_east_asian.txt` | `cri_mekong.txt` | `cri_neutral.txt` |
| **Words** | 20 | 56 | 84 | 114 | 95 | 71 |
| **Identity line** | "an essay evaluator" | "calibrated to Western academic conventions" | "calibrated to Southeast Asian rhetorical traditions" | "calibrated to East Asian academic writing traditions" | "calibrated to Mekong-region (Vietnamese, Khmer, Lao, Myanmar) learner writing traditions" | "focused purely on argumentative merit regardless of cultural rhetorical conventions" |
| **Verb** | "using the standard descriptors" | based on | recognising that | recognising that | recognising that | based on |
| **(1) Thesis** | — | clear thesis statement in the opening paragraph | thesis may emerge gradually through contextual development | central claim may be left for the reader to infer | claim carried implicitly by proverbs, family or community narratives | position clear *by the end* of the essay |
| **(2) Organisation** | — | linear progression, explicit topic sentences | inductive: evidence and context precede the claim | four-part development (intro, development, *turn*, conclusion); a digression before the conclusion is valid | contextual and relational framing precedes the position | ideas connect logically regardless of ordering |
| **(3) Hedging / tone** | — | direct evidence marshalling, *assertive* hedging | hedging ("perhaps", "one might consider") = respectful, reader-considerate | restraint and understatement = convention, not lack of conviction | deference markers and indirectness = politeness, not uncertainty | evidence supports claims regardless of presentation style |
| **(4) Cohesion / closing** | — | explicit cohesive devices (however, therefore, moreover) | collectivist framing and appeals to shared values are valid | thesis may be stated late or implied | the conclusion may *perform* the thesis rather than restate it | achieves its communicative purpose |
| **Grounding** | IELTS descriptors, named only | Kaplan 1966; Connor 2011 | Connor 2011; Ishikawa 2023 | Hinds 1987 (reader-responsible coherence) | ICNALE Guide; regional relevance — literature thin, partial exception | Fricker 2007 — a regulatory ideal, not an achievable standpoint |
| **Panel** | E1 baseline only | E1 (k=3) and E2 (k=5) | E1 and E2 | E2 only | E2 only | E1 and E2 |
| **Gap alone, GPT-4o / Claude** | 0.80 / 1.18 | 0.54 / 0.88 | **0.32 / 0.79** | 0.51 / 1.19 | 0.52 / 1.14 | 0.86 / 1.06 |

The last row is why the panel behaved as it did: the Southeast Asian lens alone had the smallest gap on both models; the Neutral lens — the "no culture" ideal — the widest of the three pilot lenses; and on Claude the two added lenses sat above the three-lens panel's 0.91, so the five-lens mean rose to 1.01.

---

## 4. The same sentence, read by two lenses

Case-study essay `WE_PHL_PTJ0_087_B1_2` (Philippines, B1 upper). It opens: *"Experience is the best teacher."*

| Lens | Instruction that applies | What it wrote (GPT-4o, verbatim) | Band |
|---|---|---|---|
| Western | (1) clear thesis statement in the opening paragraph; (4) explicit cohesive devices | "…the progression of ideas lacks clear topic sentences, leading to a somewhat disjointed argument … Cohesive devices such as 'however,' 'therefore,' and 'moreover' are absent…" | **5** |
| Southeast Asian | (1) thesis may emerge gradually through contextual development; (3) hedging = respectful | "…a coherent and cohesive structure, with the thesis emerging through contextual development. The argument is built inductively … hedging language and collectivist framing effectively appeals to shared values…" | **7** |
| Mekong (Claude) | (1) claim carried implicitly by a proverb | "…opens with a culturally familiar proverb … that anchors the argument implicitly before the position emerges, consistent with Mekong-region framing conventions" | 6 |
| Adjudicator (Claude) | weigh arguments, discount a rationale that contradicts the essay | ruled that the Western rationale "overstates the structural deficiency" | 6 |

Same essay, same model, same user turn. The Western instruction (1) makes the proverb opening a *defect*; the Southeast Asian instruction (1) makes it a *convention*. That is the two-band split, and it is the mechanism the thesis calls evaluative epistemic filtering — illustrated, not proven, because no human graded this essay.

---

## 5. The adjudicator (optional, E2 only)

System prompt (`adjudicator.txt`, 80 words): *a meta-adjudicator for an essay-scoring panel … weigh the arguments in the rationales (not the identities of the evaluators). Discount a rationale that misidentifies the essay's structure or contradicts the essay's text. You are not told anything about the writer.* Returns `{"score", "confidence", "rationale"}`.

User turn: the five evaluators' scores and rationales, then the **full essay**, then the JSON instruction. It runs after the five independent scores, never during them.

Result: no clear change on either model (GPT-4o +0.03 [−0.03, 0.09]; Claude 0.002 [−0.08, 0.08]); on Claude it lowered band association (−0.06 [−0.10, −0.03]).

---

## 6. What the prompts do **not** contain — say these before you are asked

1. **No IELTS descriptor text.** The descriptors are *named*, not reproduced, so each band rests partly on the model's own learned reading of IELTS. Not examiner-equivalent bands (§3.4).
2. **No examples, no few-shot, no rubric table.** Each lens is a single paragraph.
3. **No fixed rubric being reinterpreted.** The lens prompts *add* criteria. So the panel's effect may be changed scoring expectations rather than corrected bias — the construct-drift limitation (§4.5); a non-cultural control panel would separate the two and was not run.
4. **No empirical tuning.** "Calibrated" means informed by the contrastive-rhetoric literature, not fitted to data (Table 1.2). The Mekong lens rests on thin literature and is admitted on regional relevance.
5. **A housekeeping header.** The East Asian, Mekong and adjudicator files begin with a line *"DRAFT – review with supervisor before E2 (grounding: …)"*. That line was part of the system prompt sent in E2/E3. The prompts were reviewed and frozen before E2; the header was left in, and it stays in Appendix A because nothing was edited after the runs.

---

## 7. Thirty-second spoken version

> Each lens is a short plain-text system prompt — sixty to a hundred words — with the same skeleton: *you are an evaluator calibrated to this tradition; evaluate coherence and cohesion recognising these four conventions; score 1 to 9 on the IELTS coherence-and-cohesion descriptors.* The four conventions come from the contrastive-rhetoric literature: thesis-first and explicit links for the Western lens; thesis emerging inductively and hedging as courtesy for the Southeast Asian lens; reader-responsible coherence for the East Asian lens; proverb-anchored claims for the Mekong lens; merit regardless of ordering for the Neutral lens. The essay and the user turn are identical for all five; they are called independently and never see each other. The descriptors are named, not pasted in. Everything is verbatim in Appendix A.
