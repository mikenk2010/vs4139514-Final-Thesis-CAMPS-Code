# 4. Mekong / Vietnamese lens

`prompts/cri_mekong.txt` · *proverb-anchored claims · indirectness as politeness* · colour `#B8503F` in the deck and demo

Other lenses: [Western lens](01-western.md) · [Southeast Asian lens](02-sea.md) · [East Asian lens](03-east_asian.md) · [Neutral lens](05-neutral.md) · [Overview](../HOW-THE-LENSES-GRADE.md)

---

## What this lens is for

Added in Part B (E2 only). Motivated by the region this research serves; validatable in principle against ICNALE WEP (Vietnam, Cambodia, Laos, Myanmar), which has no comparable bands, so it was not separately validated.

**Grounding.** Regional relevance (Vietnam, Cambodia, Laos, Myanmar); the ICNALE Guide (Ishikawa 2023) on the WEP cohorts; Shujaa, Dorleon and Tang (2026) on cultural bias in LLM treatment of Southeast Asian content. The contrastive-rhetoric literature on Mekong-region academic writing is thin: this lens is the partial exception to the 'documented in the literature' criterion (thesis section 3.3) and is admitted on regional relevance.

---

## The exact system prompt (verbatim, as sent to the model)

```text
You are an essay evaluator calibrated to Mekong-region (Vietnamese, Khmer, Lao, Myanmar) learner writing traditions. Evaluate coherence and cohesion recognising that: (1) arguments may be anchored in proverbs, family or community narratives that carry the essay's claim implicitly, (2) contextual and relational framing may precede the position statement, (3) deference markers and indirectness reflect politeness conventions rather than uncertainty, (4) the conclusion may perform the thesis rather than restate it. Score 1-9 on the IELTS Coherence and Cohesion band descriptors.
```
> The file also carries a first line *"DRAFT - review with supervisor before E2 (grounding: ICNALE Guide; Shujaa, Dorleon & Tang 2026)."*. That header was part of the system prompt sent in E2/E3; the prompt was reviewed and frozen before E2 and the header left in place. It is reproduced in Appendix A because nothing was edited after the runs.

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
| (1) Claim | Arguments may be anchored in proverbs, family or community narratives that carry the essay's claim implicitly. | 'Experience is the best teacher' *is* the claim, not decoration. |
| (2) Framing | Contextual and relational framing may precede the position statement. | Relationship-first openings are *structure*. |
| (3) Tone | Deference markers and indirectness reflect politeness conventions rather than uncertainty. | Indirectness is *not* penalised as vagueness. |
| (4) Closing | The conclusion may *perform* the thesis rather than restate it. | An affirming close counts as a *conclusion*. |

**Rewards.** Proverb- and narrative-anchored essays whose stance is enacted rather than announced.

**Still penalises.** Loose paragraph-level coherence and mechanical cohesive devices. On the case essay it still noted 'loosely connected supporting sentences'.

---

## This lens on the case essay (`WE_PHL_PTJ0_087_B1_2`, Philippines, B1 upper)

Opens *"Experience is the best teacher."*; the standard grader gave 6 on GPT-4o and 6 on Claude.

**GPT-4o — band 6**
> The essay demonstrates a clear progression of ideas, with each paragraph contributing to the overall argument that part-time jobs are beneficial for college students. The use of proverbs and community narratives, such as 'Experience is the best teacher,' effectively anchors the argument. However, the essay could improve coherence by explicitly linking some ideas and providing clearer transitions between points. The conclusion effectively performs the thesis by reinforcing the benefits of part-time jobs, but it could be more explicitly connected to the introduction.

**Claude Sonnet 4.6 — band 6**
> The essay opens with a culturally familiar proverb ('Experience is the best teacher') that anchors the argument implicitly before the position emerges, consistent with Mekong-region framing conventions. Cohesive devices (through, adding, not only...but also) are used adequately though somewhat mechanically, and the progression across paragraphs—field experience, skill-building, financial support—is logical if not tightly signposted. The conclusion performs the thesis by affirming part-time work's value rather than restating it analytically, which suits the essay's rhetorical tradition, though overall paragraph-level coherence occasionally lapses with loosely connected supporting sentences.

---

## What this lens did at scale

Native − SEA gap under this lens alone (five-lens run for GPT-4o and Claude; three-lens run for Gemini and Qwen3; n = 100 per cohort; point estimates):

| Model | Gap (bands) |
|---|---|
| GPT-4o | 0.52 |
| Claude Sonnet 4.6 | 1.14 |

For reference: standard grader 0.80 (GPT-4o), 1.18 (Claude), 0.19 (Gemini), 0.23 (Qwen3); five-lens panel 0.55 / 1.01; three-lens panel 0.57 / 0.91 / 0.45 / 0.27.

**Contribution.** Did not add mitigation. GPT-4o 0.52 (about the panel); Claude 1.14, above the three-lens panel's 0.91 (though *below* the 1.18 baseline). One of the two lenses that pushed Claude's five-lens gap up.

**Note.** Be ready for: 'Isn't this lens just made up?' Answer: it is the least grounded of the five and the thesis says so; it was kept because the framework is meant for this region, and its results are reported, not hidden.

---

*All quotations are copied from `results/E1|E2/scores.jsonl`; all numbers are the thesis's (Tables 4.1–4.2, §4.2). References: thesis Appendix A (prompts), §3.2–3.3 (design), §4.2 (lens-level results), §4.5 (construct validity).*
