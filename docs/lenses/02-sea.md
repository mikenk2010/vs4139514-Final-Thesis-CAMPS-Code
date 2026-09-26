# 2. Southeast Asian lens

`prompts/cri_sea.txt` · *thesis may emerge gradually · hedging as courtesy* · colour `#C96A28` in the deck and demo

Other lenses: [Western lens](01-western.md) · [East Asian lens](03-east_asian.md) · [Mekong / Vietnamese lens](04-mekong.md) · [Neutral lens](05-neutral.md) · [Overview](../HOW-THE-LENSES-GRADE.md)

---

## What this lens is for

Pilot lens (Part A). In E1 and E2. The lens the framework was built around: the reading under which the cohort the thesis studies is not penalised for its rhetorical form.

**Grounding.** Connor (2011) on inductive, reader-responsible coherence in Asian academic writing; Ishikawa (2023), The ICNALE Guide, on the Southeast Asian learner cohorts this thesis samples.

---

## The exact system prompt (verbatim, as sent to the model)

```text
You are an essay evaluator calibrated to Southeast Asian rhetorical traditions. Evaluate coherence and cohesion recognising that: (1) thesis may emerge gradually through contextual development rather than appearing in the opening paragraph, (2) coherence may follow an inductive pattern where evidence and context precede the main claim, (3) hedging language ("perhaps," "one might consider") indicates respectful, reader-considerate argumentation rather than weak reasoning, (4) collectivist framing and appeals to shared values constitute valid argumentative strategies. Score 1-9 on the IELTS Coherence and Cohesion band descriptors.
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

The lens uses the verb **"recognising that"** — these forms are to be *accepted as valid* while judging coherence and cohesion.

| Convention | Instruction | Effect on a proverb-first, inductive essay |
|---|---|---|
| (1) Thesis | The thesis may emerge gradually through contextual development rather than appearing in the opening paragraph. | A proverb or context-first opening is a *convention*, not a missing thesis. |
| (2) Organisation | Coherence may follow an inductive pattern: evidence and context precede the main claim. | Build-up before the claim is *structure*, not disorder. |
| (3) Hedging | 'Perhaps', 'one might consider' indicate respectful, reader-considerate argumentation rather than weak reasoning. | Politeness hedging is *not* penalised. |
| (4) Framing | Collectivist framing and appeals to shared values constitute valid argumentative strategies. | 'We all know that...', family and community appeals count as *a kind of evidence*. |

**Rewards.** Inductively organised essays whose position is clear by the end, with courteous hedging and community-anchored appeals.

**Still penalises.** Genuine incoherence: ideas that do not connect regardless of order, missing transitions, an unclear final position. It still asks for coherence; it changes what counts as evidence of it.

---

## This lens on the case essay (`WE_PHL_PTJ0_087_B1_2`, Philippines, B1 upper)

Opens *"Experience is the best teacher."*; the standard grader gave 6 on GPT-4o and 6 on Claude.

**GPT-4o — band 7**
> The essay demonstrates a coherent and cohesive structure, with the thesis emerging through contextual development. The argument is built inductively, presenting evidence and context before arriving at the main claim. The use of hedging language and collectivist framing effectively appeals to shared values, enhancing the argument's persuasiveness. However, the essay could benefit from clearer paragraph transitions to further improve coherence.

**Claude Sonnet 4.6 — band 6**
> The essay demonstrates a generally clear progression of ideas with each paragraph developing a distinct benefit of part-time work, following an inductive pattern that builds toward the concluding claim—consistent with Southeast Asian rhetorical traditions where the thesis is reinforced rather than front-loaded. Cohesive devices are present but somewhat mechanical and repetitive ('through,' 'part-time jobs'), and the transition between paragraphs could be smoother, with some ideas (e.g., the scholarship example) feeling loosely integrated. The collectivist framing and appeals to shared values around preparation and responsibility are rhetorically appropriate, though the overall argument would benefit from tighter logical sequencing and more varied cohesive strategies.

---

## What this lens did at scale

Native − SEA gap under this lens alone (five-lens run for GPT-4o and Claude; three-lens run for Gemini and Qwen3; n = 100 per cohort; point estimates):

| Model | Gap (bands) |
|---|---|
| GPT-4o | 0.32 |
| Claude Sonnet 4.6 | 0.79 |
| Gemini 3.1 Pro | 0.27 |
| Qwen3-14B (local) | 0.29 |

For reference: standard grader 0.80 (GPT-4o), 1.18 (Claude), 0.19 (Gemini), 0.23 (Qwen3); five-lens panel 0.55 / 1.01; three-lens panel 0.57 / 0.91 / 0.45 / 0.27.

**Contribution.** The largest single contributor to the reduction: 0.16 of 0.23 (GPT-4o) and 0.13 of 0.27 (Claude). Alone it gave a smaller gap than *any* panel (0.32 vs 0.55 five-lens on GPT-4o; 0.79 vs 1.01 on Claude).

**Note.** Trap question. On the 140 human-rated GRA essays the SEA lens on GPT-4o was more generous to Southeast Asian essays than the 80 raters (+0.24 SD [+0.07, +0.41]), a lean the consensus averages out. So 'smallest gap' is not automatically 'most accurate'; that is the levelling-down question the thesis leaves open.

---

*All quotations are copied from `results/E1|E2/scores.jsonl`; all numbers are the thesis's (Tables 4.1–4.2, §4.2). References: thesis Appendix A (prompts), §3.2–3.3 (design), §4.2 (lens-level results), §4.5 (construct validity).*
