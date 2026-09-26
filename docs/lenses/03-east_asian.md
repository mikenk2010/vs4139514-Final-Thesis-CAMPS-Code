# 3. East Asian lens

`prompts/cri_east_asian.txt` · *reader-responsible · late or implied thesis* · colour `#2A9D8F` in the deck and demo

Other lenses: [Western lens](01-western.md) · [Southeast Asian lens](02-sea.md) · [Mekong / Vietnamese lens](04-mekong.md) · [Neutral lens](05-neutral.md) · [Overview](../HOW-THE-LENSES-GRADE.md)

---

## What this lens is for

Added in Part B (E2 only). Chosen because it is documented in the literature, is validatable against ICNALE's East Asian cohorts (CHN, JPN, KOR, TWN), and was expected to diverge from the pilot lenses on identifiable features.

**Grounding.** Hinds (1987) on reader-responsible coherence in Japanese (and, by extension, Chinese and Korean) expository prose; the ki-sho-ten-ketsu four-part structure.

---

## The exact system prompt (verbatim, as sent to the model)

```text
You are an essay evaluator calibrated to East Asian academic writing traditions. Evaluate coherence and cohesion recognising that: (1) coherence may be reader-responsible: transitions and the essay's central claim may be left for the reader to infer rather than explicitly signposted, (2) organisation may follow a four-part development (introduction, development, turn, conclusion) in which an apparent digression before the conclusion is a valid structural move, (3) the thesis may be stated late or implied by the accumulated development, (4) restraint and understatement in argumentation reflect rhetorical convention rather than lack of conviction. Score 1-9 on the IELTS Coherence and Cohesion band descriptors.
```
> The file also carries a first line *"DRAFT - review with supervisor before E2 (grounding: Hinds 1987 reader-responsible coherence)."*. That header was part of the system prompt sent in E2/E3; the prompt was reviewed and frozen before E2 and the header left in place. It is reproduced in Appendix A because nothing was edited after the runs.

The user turn, identical for every lens:

```text
Score the following essay. Respond with JSON: {"score": <band>, "rationale": "<2-3 sentences>"}.

ESSAY:
<full essay text>
```

Score = IELTS Coherence & Cohesion band, 1–9 (descriptors named, not reproduced). Temperature 0 where the client exposes it. Called independently of the other lenses.

---

## The four conventions, and what they change

The lens uses the verb **"recognising that"** — these forms are to be *accepted as valid* while judging coherence and cohesion.

| Convention | Instruction | Effect on a proverb-first, inductive essay |
|---|---|---|
| (1) Coherence | May be reader-responsible: transitions and the central claim may be left for the reader to infer rather than signposted. | Absence of explicit transitions is *not* by itself incoherence. |
| (2) Organisation | May follow a four-part development (introduction, development, turn, conclusion) in which an apparent digression before the conclusion is a valid structural move. | A late digression is *structure*, not drift. |
| (3) Thesis | May be stated late or implied by the accumulated development. | A late thesis is *acceptable*. |
| (4) Tone | Restraint and understatement reflect rhetorical convention rather than lack of conviction. | Understatement is *not* weak argument. |

**Rewards.** Essays with a clear central theme the reader can reconstruct, a genuine turn, and closure, even without explicit signposting.

**Still penalises.** Essays that never let the reader infer a claim, or whose turn is unmotivated. On the case essay it still docked marks for 'formulaic transitions'.

---

## This lens on the case essay (`WE_PHL_PTJ0_087_B1_2`, Philippines, B1 upper)

Opens *"Experience is the best teacher."*; the standard grader gave 6 on GPT-4o and 6 on Claude.

**GPT-4o — band 6**
> The essay demonstrates a clear central theme about the benefits of part-time jobs for college students, which is developed through various points such as gaining experience, financial support, and skill development. However, the coherence is somewhat reader-responsible, as transitions between ideas are not always explicit, requiring the reader to infer connections. The structure follows a logical progression, but the thesis is implied rather than explicitly stated, which may challenge some readers. Overall, the essay maintains a consistent focus and provides relevant examples, but could benefit from clearer signposting and more explicit connections between ideas.

**Claude Sonnet 4.6 — band 6**
> The essay follows a clear thematic progression through distinct benefit-focused paragraphs, and the concluding restatement provides adequate closure recognisable within both Western and reader-responsible traditions. Cohesive devices are present but mechanical (e.g., repeated topic-sentence pivots), and the central claim, while implicit from the outset, is never developed with sufficient depth or turn to exploit the four-part ki-shō-ten-ketsu structure fully. Transitions between paragraphs are formulaic rather than organic, limiting the score despite generally competent paragraph-level coherence.

---

## What this lens did at scale

Native − SEA gap under this lens alone (five-lens run for GPT-4o and Claude; three-lens run for Gemini and Qwen3; n = 100 per cohort; point estimates):

| Model | Gap (bands) |
|---|---|
| GPT-4o | 0.51 |
| Claude Sonnet 4.6 | 1.19 |

For reference: standard grader 0.80 (GPT-4o), 1.18 (Claude), 0.19 (Gemini), 0.23 (Qwen3); five-lens panel 0.55 / 1.01; three-lens panel 0.57 / 0.91 / 0.45 / 0.27.

**Contribution.** Did not add mitigation. On GPT-4o its gap (0.51) roughly matched the three-lens panel's; on Claude its gap (1.19) exceeded the three-lens panel's 0.91, so including it raised the five-lens mean to 1.01. This is the 'composition beats count' finding.

**Note.** Grounded in Japanese-origin scholarship; whether it transfers to Chinese, Korean or Taiwanese learners' English essays was not separately validated in E1-E3 (thesis section 4.5).

---

*All quotations are copied from `results/E1|E2/scores.jsonl`; all numbers are the thesis's (Tables 4.1–4.2, §4.2). References: thesis Appendix A (prompts), §3.2–3.3 (design), §4.2 (lens-level results), §4.5 (construct validity).*
