# EquiAlgo · Strategy 24: Matched central/remote residual transport

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P2 · **Effort** 5 h · **Depends on** candidate/history features |
| **Rubric** | Hidden-reference accuracy; exact award budget |
| **Work folder** | work/strat24/ |

## 1. Context and evidence

Report 01 shows region and proxy features influence committee decisions; simulated reference construction is uncertain. Strategy 14 proposes score-distribution transport. This proposal tests whether locally matched historical residuals transport to candidates, rather than mapping score distributions after fitting.

## 2. Idea and novelty

Within academic-merit and program neighborhoods, match central/remote historical applicants on defensible covariates; estimate a shrunken residual correction from committee-label differences, then apply only where overlap is adequate. The matching is a training correction, not individual counterfactual rewriting or global quantile mapping.

## 3. Rubric

Candidate family that can remove local systematic shifts without assuming one global regional penalty.

## 4. Implementation

Create `work/strat24/matched_transport.py`; define calipers and overlap thresholds before fitting. Exclude unsupported areas rather than extrapolate. Emit correction magnitude, matched count, and candidate mask.

## 5. Experiment

Compare one correction setting with V1 in a single authorized upload; only if allowed. Primary pass is accuracy >94% on the same official metric. If score is ≤94% or overlap covers <80% of candidates, reject; do not infer row labels from scalar score.

## 6. Risks

Committee residual differences may be real eligibility rules; matching cannot identify causality or hidden labels.

## 7. Combines with

Compare with 21 and 30; never use protected-group correction without rubric authority.

## 8. Results log

NOT RUN. No matching correction or leaderboard result has been measured.
