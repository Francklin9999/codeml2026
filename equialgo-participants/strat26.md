# EquiAlgo · Strategy 26: Identifiable label-transition correction

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P1 · **Effort** 5 h · **Depends on** history and candidate features |
| **Rubric** | Hidden-reference accuracy under official metric |
| **Work folder** | work/strat26/ |

## 1. Context and evidence

Committee decisions are observed; hidden reference labels are not. Strategies 11 and 21 address label bias/noise differently. An explicit transition matrix offers a candidate correction if noise rates can be bounded from defensible assumptions.

## 2. Idea and novelty

Estimate a class-conditional transition matrix P(committee|latent) with separate false-positive and false-negative rates, then correct the logistic likelihood. Unlike strategy 21's group-specific EM, start with pooled noise and compare only a predeclared region-conditional extension if pooled diagnostics warrant it.

## 3. Rubric

Tests a standard noisy-label estimator without equating committee choices to merit or assuming symmetric flips.

## 4. Implementation

Create `work/strat26/transition.py`; profile likelihood over feasible rates, disclose identifiability limits, impose exact budget at prediction time, and save one candidate per fixed matrix.

## 5. Experiment

Use at most two permitted accuracy-leaderboard uploads: pooled then conditional only if predeclared trigger fires. Adoption requires >94% on the confirmed metric. Do not use scalar scores to estimate individual hidden labels or tune unboundedly.

## 6. Risks

Transition rates are not identified from one noisy label source alone; wrong rates can worsen predictions substantially.

## 7. Combines with

Contrast 21 and 27; do not combine before separate results.

## 8. Results log

NOT RUN. No transition rates, corrected model, or leaderboard score exists.
