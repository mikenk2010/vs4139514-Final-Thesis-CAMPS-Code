# 5. Neutral lens

`prompts/cri_neutral.txt` · *argumentative merit, regardless of ordering* · colour `#7f7f7f` in the deck and demo

Other lenses: [Western lens](01-western.md) · [Southeast Asian lens](02-sea.md) · [East Asian lens](03-east_asian.md) · [Mekong / Vietnamese lens](04-mekong.md) · [Overview](../HOW-THE-LENSES-GRADE.md)

---

## What this lens is for

Pilot lens (Part A). In E1 and E2. The control-like reading: it asks for merit 'regardless of cultural rhetorical conventions' and explicitly says ordering and presentation style should not matter.

**Grounding.** Fricker (2007): no evaluator judges from nowhere, so a 'culturally neutral' grader is a regulatory ideal, not an achievable standpoint. The lens is retained to test that idea empirically.

---

## The exact system prompt (verbatim, as sent to the model)

```text
You are an essay evaluator focused purely on argumentative merit regardless of cultural rhetorical conventions. Evaluate coherence and cohesion based on: (1) whether the writer's position is ultimately clear by the end of the essay, (2) whether ideas connect logically regardless of structural ordering, (3) whether evidence supports claims regardless of presentation style, (4) whether the essay achieves its communicative purpose. Score 1-9 on the IELTS Coherence and Cohesion band descriptors.
```

The user turn, identical for every lens:

```text
Score the following essay. Respond with JSON: {"score": <band>, "rationale": "<2-3 sentences>"}.

ESSAY:
<full essay text>
```

Score = IELTS Coherence & Cohesion band, 1–9 (descriptors named, not reproduced). Temperature 0 where the client exposes it. Called independently of the other lenses.

---

## The four conventions, and what they change

The lens uses the verb **"based on"** — these are the criteria the essay is judged *on*.

| Convention | Instruction | Effect on a proverb-first, inductive essay |
|---|---|---|
| (1) Position | Whether the writer's position is ultimately clear *by the end* of the essay. | A late thesis is fine *if* the position is clear at the end. |
| (2) Logic | Whether ideas connect logically regardless of structural ordering. | Order is *not* a criterion. |
| (3) Evidence | Whether evidence supports claims regardless of presentation style. | Style is *not* a criterion. |
| (4) Purpose | Whether the essay achieves its communicative purpose. | Holistic. |

**Rewards.** Essays with a clear end position and connected ideas, whatever their shape.

**Still penalises.** In practice, the same things the default model penalises: its gaps were the *widest* of the three pilot lenses.

---

## This lens on the case essay (`WE_PHL_PTJ0_087_B1_2`, Philippines, B1 upper)

Opens *"Experience is the best teacher."*; the standard grader gave 6 on GPT-4o and 6 on Claude.

**GPT-4o — band 7**
> The essay presents a clear position advocating for the benefits of part-time jobs for college students. Ideas are logically connected, discussing how part-time work aids in professional transition, skill development, and financial support. Evidence is provided through examples of students using part-time jobs to fund education and schools offering work opportunities. The essay effectively communicates its purpose, though it could benefit from more structured paragraphing to enhance clarity.

**Claude Sonnet 4.6 — band 6**
> The writer's position is clear throughout and maintained consistently to the conclusion, with logical progression across three distinct supporting points (career preparation, skill development, and financial support). Ideas connect reasonably well with each point building on the central thesis, though transitions between paragraphs are somewhat mechanical and the personal anecdote ('I've heard of') weakens evidential support. The essay achieves its communicative purpose effectively, though some claims remain underdeveloped and the cohesive devices are repetitive rather than varied.

---

## What this lens did at scale

Native − SEA gap under this lens alone (five-lens run for GPT-4o and Claude; three-lens run for Gemini and Qwen3; n = 100 per cohort; point estimates):

| Model | Gap (bands) |
|---|---|
| GPT-4o | 0.86 |
| Claude Sonnet 4.6 | 1.06 |
| Gemini 3.1 Pro | 0.85 |
| Qwen3-14B (local) | 0.34 |

For reference: standard grader 0.80 (GPT-4o), 1.18 (Claude), 0.19 (Gemini), 0.23 (Qwen3); five-lens panel 0.55 / 1.01; three-lens panel 0.57 / 0.91 / 0.45 / 0.27.

**Contribution.** Contributed -0.02 on GPT-4o (its gap 0.86 exceeded the 0.80 baseline) and +0.04 on Claude. On Gemini it was the lens that expanded the score range (7.18 native vs 6.33 SEA) and drove the panel's gap amplification (0.19 to 0.45).

**Note.** The headline lesson of this lens: telling a model to ignore culture does not remove its cultural prior; it leaves the default in place. 'Neutral' prompts are not neutral in effect (thesis sections 4.2 and 4.6).

---

*All quotations are copied from `results/E1|E2/scores.jsonl`; all numbers are the thesis's (Tables 4.1–4.2, §4.2). References: thesis Appendix A (prompts), §3.2–3.3 (design), §4.2 (lens-level results), §4.5 (construct validity).*
