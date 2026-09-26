# The five CAMPS lenses — one file each

| # | Lens | Tagline | Verb | Grounding | In panel | Gap alone GPT-4o / Claude |
|---|---|---|---|---|---|---|
| 1 | [Western lens](01-western.md) | thesis first · linear progression · explicit links | based on | Kaplan (1966) on culturally learned rhetorical organisation | E1, E2 | 0.54 / 0.88 |
| 2 | [Southeast Asian lens](02-sea.md) | thesis may emerge gradually · hedging as courtesy | recognising that | Connor (2011) on inductive, reader-responsible coherence in Asian academic writing | E1, E2 | 0.32 / 0.79 |
| 3 | [East Asian lens](03-east_asian.md) | reader-responsible · late or implied thesis | recognising that | Hinds (1987) on reader-responsible coherence in Japanese (and, by extension, Chinese and Korean) expository prose | E2 | 0.51 / 1.19 |
| 4 | [Mekong / Vietnamese lens](04-mekong.md) | proverb-anchored claims · indirectness as politeness | recognising that | Regional relevance (Vietnam, Cambodia, Laos, Myanmar) | E2 | 0.52 / 1.14 |
| 5 | [Neutral lens](05-neutral.md) | argumentative merit, regardless of ordering | based on | Fricker (2007): no evaluator judges from nowhere, so a 'culturally neutral' grader is a regulatory ideal, not an achievable standpoint | E1, E2 | 0.86 / 1.06 |

Reference gaps: standard grader 0.80 / 1.18; three-lens panel 0.57 / 0.91; five-lens panel 0.55 / 1.01. Overview of the scoring call and the side-by-side table: [../HOW-THE-LENSES-GRADE.md](../HOW-THE-LENSES-GRADE.md).

Every lens is a plain-text system prompt (`prompts/cri_<lens>.txt`), sent with a byte-identical user turn containing the essay, called independently. "Calibrated" means informed by the contrastive-rhetoric literature, not empirically tuned (thesis Table 1.2).
