# EquiAlgo · Strategy 25: Soft-label confidence weighting from model disagreement

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P2 · **Effort** 4 h · **Depends on** V1–V5 score outputs |
| **Rubric** | Hidden-reference accuracy; fixed quota |
| **Work folder** | work/strat25/ |

## 1. Context and evidence

Existing V1–V5 candidates overlap strongly, while V4 is less stable (mean refit Jaccard .917) despite lower parity gap. Their labels are model outputs, not independent truth. Disagreement can identify uncertain examples but cannot reveal hidden labels.

## 2. Idea and novelty

Train a soft-target model from committee labels, weighting each history row by a confidence score derived from out-of-fold predictive entropy and refit agreement. This differs from strategy 16's Rashomon-based borderline policy: uncertainty changes the training loss, not applicant handling or ensemble membership.

## 3. Rubric

Tests whether noisy/ambiguous historical cases should exert less influence on the fitted ranking.

## 4. Implementation

Create `work/strat25/soft_confidence.py`; generate out-of-fold probabilities, freeze entropy/agreement weights, then fit a soft-label logistic model. Sweep only three predeclared temperature values and produce top-k candidates.

## 5. Experiment

Select at most one setting for authorized accuracy leaderboard, if uploads are permitted. Strict adoption threshold >94% on same official metric. CV on committee labels may debug calibration but cannot pass acceptance. No hidden-label guessing.

## 6. Risks

Model consensus can be confidently wrong and same-family agreement is correlated. Confidence weighting may amplify shared bias.

## 7. Combines with

Pair with 21 noise model; compare to V1 as anchor.

## 8. Results log

NOT RUN. No soft-label model or official metric result exists.
