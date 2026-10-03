# OptiFrame · Strategy 36: Metrology golden-fixture separation

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 2 evaluator and synthetic generator |
| **Work folder** | `optiframe-participants/work/strat36/` |

## 1. Context and evidence

The 15 synthetic cases were used during development, so their 0.080234 mm MAE is a development-set synthetic metric. Strategy 2 lacks physical validation. This proposal creates new sealed synthetic shape/parameter families and, if available, a separately controlled physical reference set; it does not relabel or split the current 15 cases as an independent holdout.

Evidence: [metrology report](work/strat2/report.md) explicitly says the fixed synthetic suite is not an independent holdout.

## 2. Idea and distinction

Generate new held-out shapes from parameter families not used by the current ellipse and rounded-rectangle fixtures, with parameter ranges sealed before evaluation. Keep any future physical-reference lenses in a separate, blinded set with dimensions measured independently. Leave all 15 existing images available only as regression fixtures; do not use them to claim generalization.

## 3. Rubric relevance

Improves credibility of accuracy reporting by distinguishing tuning results from evaluation evidence.

## 4. Implementation steps

Add `work/strat36/holdout_spec.json`, generator-family registry, and report template. Record held-out family hashes and seal selection parameters before tuning. Keep physical controls in a separately tagged table and never combine their errors with synthetic scores.

## 5. Proposed experiment

Create 20 new shapes from four held-out families plus 10 new nuisance-parameter settings; use the existing 15 only as regression. If independent caliper-measured physical controls are available, collect eight and keep them blind. Adopt the process if no held-out parameter/family is used in tuning and reports keep physical and synthetic metrics separate; small synthetic results remain illustrative. Proposed process, not measured result.

## 6. Risks

Synthetic family separation still cannot establish real-lens accuracy. Physical controls may not be available and must not be fabricated; report the limitation.

## 7. Combinations

Pairs with strategies 2, 6, 14, 18, 21, and 30.

## 8. Results log

NOT RUN. No new sealed shape-family holdout or physical controls exist.
