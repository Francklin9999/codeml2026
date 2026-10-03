# EquiAlgo · Strategy 35: Cross-family stacking with out-of-fold score calibration

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P2 · **Effort** 5 h · **Depends on** candidates from diverse families |
| **Rubric** | Hidden-reference accuracy; fixed 40% rate |
| **Work folder** | work/strat35/ |

## 1. Context and evidence

Current V1–V3/V5 are similar logistic variants; V4 is a GBM and less stable. Their agreement is not independent evidence and no official target score is available. A deliberately diverse stack may capture complementary ranking signal.

## 2. Idea and novelty

Calibrate out-of-fold scores from distinct candidates (noise-corrected, monotone GAM, robust link, and program-threshold) using a small regularized meta-ranker trained only on committee folds, then threshold to 1,600. Unlike strategy 8's ensemble over simulated reference worlds, this stacks predictive families, not hypotheses.

## 3. Rubric

Tests complementarity while guarding against a single variant's misspecification.

## 4. Implementation

Create `work/strat35/stack.py`; require base diversity, nested out-of-fold fitting, and at most three base models. Include simple mean-rank ensemble as control; never fit meta-weights on leaderboard scores.

## 5. Experiment

One frozen stack, one authorized upload if allowed. Adopt only if >94% on the actual confirmed accuracy metric. No tuning from individual hidden outcomes; committee-CV stacking is not proof of success.

## 6. Risks

Correlated errors and leakage can make stacks look strong internally but fail hidden evaluation.

## 7. Combines with

Only after 21–34 standalone candidates and split pipeline are frozen.

## 8. Results log

NOT RUN. No diverse stack or leaderboard score exists.
