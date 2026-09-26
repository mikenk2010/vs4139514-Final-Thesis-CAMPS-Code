# 1. Western lens

`prompts/cri_western.txt` · *thesis first · linear progression · explicit links* · colour `#4A69BD` in the deck and demo

Other lenses: [Southeast Asian lens](02-sea.md) · [East Asian lens](03-east_asian.md) · [Mekong / Vietnamese lens](04-mekong.md) · [Neutral lens](05-neutral.md) · [Overview](../HOW-THE-LENSES-GRADE.md)

---

## What this lens is for

Pilot lens (Part A). In E1 as one of three; in E2 as one of five. This is the reading most graders trained on Western text already apply; it is in the panel so that the standard the baseline implicitly uses is made explicit and can be weighed against the others.

**Grounding.** Kaplan (1966) on culturally learned rhetorical organisation; Connor (2011) on writer-responsible, thesis-first Anglo-American academic prose.

---

## The exact system prompt (verbatim, as sent to the model)

```text
You are an essay evaluator calibrated to Western academic conventions. Evaluate coherence and cohesion based on: (1) clear thesis statement in the opening paragraph, (2) linear logical progression with explicit topic sentences, (3) direct evidence marshalling with assertive hedging, (4) explicit cohesive devices (however, therefore, moreover). Score 1-9 on the IELTS Coherence and Cohesion band descriptors.
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
| (1) Thesis | A clear thesis statement must appear in the opening paragraph. | An essay that opens with context, a proverb or a story and states its position later is read as *lacking a thesis*. |
| (2) Organisation | Linear logical progression with explicit topic sentences. | Inductive build-up (evidence first, claim later) reads as *disjointed*. |
| (3) Evidence and hedging | Direct evidence marshalling with *assertive* hedging. | Deferential, reader-considerate hedging ('perhaps', 'one might consider') reads as *weak reasoning*. |
| (4) Cohesion | Explicit cohesive devices: however, therefore, moreover. | Cohesion carried by repetition or implicit links reads as *absent cohesive devices*. |

**Rewards.** Essays that announce their position in sentence one, signpost every paragraph, and connect ideas with visible connectives.

**Still penalises.** Essays whose position emerges late, whose links are implicit, or whose hedging is polite rather than assertive: the very features the contrastive-rhetoric literature documents as valid in many Asian traditions.

---

## This lens on the case essay (`WE_PHL_PTJ0_087_B1_2`, Philippines, B1 upper)

Opens *"Experience is the best teacher."*; the standard grader gave 6 on GPT-4o and 6 on Claude.

**GPT-4o — band 5**
> The essay presents a clear thesis in the opening paragraph, suggesting that part-time jobs are beneficial for college students. However, the progression of ideas lacks clear topic sentences, leading to a somewhat disjointed argument. While there is some evidence provided, it is not consistently linked back to the thesis with assertive hedging. Cohesive devices such as 'however,' 'therefore,' and 'moreover' are absent, which affects the overall coherence and cohesion of the essay.

**Claude Sonnet 4.6 — band 5**
> The essay presents a recognizable position on part-time jobs for college students, but the opening paragraph lacks a clearly articulated thesis statement, instead relying on a general aphorism ('Experience is the best teacher') before gradually narrowing focus. Logical progression exists across paragraphs—covering career preparation, skill development, and financial support—but topic sentences are often implicit rather than explicit, and cohesive devices are sparse and elementary (e.g., 'To add to that'), with little use of sophisticated linking language such as 'therefore,' 'consequently,' or 'moreover.' The concluding paragraph attempts to synthesize but merely restates points without demonstrating cumulative logical development, and the anecdotal first-person reference ('I've heard') undermines the academic register expected for higher band scores.

---

## What this lens did at scale

Native − SEA gap under this lens alone (five-lens run for GPT-4o and Claude; three-lens run for Gemini and Qwen3; n = 100 per cohort; point estimates):

| Model | Gap (bands) |
|---|---|
| GPT-4o | 0.54 |
| Claude Sonnet 4.6 | 0.88 |
| Gemini 3.1 Pro | 0.23 |
| Qwen3-14B (local) | 0.18 |

For reference: standard grader 0.80 (GPT-4o), 1.18 (Claude), 0.19 (Gemini), 0.23 (Qwen3); five-lens panel 0.55 / 1.01; three-lens panel 0.57 / 0.91 / 0.45 / 0.27.

**Contribution.** Contributed 0.09 (GPT-4o) and 0.10 (Claude) of the three-lens reduction. It is *less* harsh on SEA essays than the plain baseline prompt (gap 0.80 / 1.18), because the baseline leaves the model's default fully in place.

**Note.** On the case essay the Western lens was the lowest or joint-lowest scorer on all four models. It is not a 'villain' lens; it is the standard many examiners would recognise. But it is one reading of the rubric, not the rubric.

---

*All quotations are copied from `results/E1|E2/scores.jsonl`; all numbers are the thesis's (Tables 4.1–4.2, §4.2). References: thesis Appendix A (prompts), §3.2–3.3 (design), §4.2 (lens-level results), §4.5 (construct validity).*
