# EquiAlgo · Strategy 34: Merit-stratified ordinal probit with program thresholds

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P2 · **Effort** 4–6 h · **Depends on** program/cote-R features |
| **Rubric** | Hidden-reference accuracy; 1,600 grant count |
| **Work folder** | work/strat34/ |

## 1. Context and evidence

Strategy 12 proposes Bayesian region-specific thresholds; current V1–V5 are mostly binary committee fits. Program competition may make a single global cutoff inaccurate, but there is no source proving hidden references differ by program.

## 2. Idea and novelty

Fit an ordinal probit with program-specific merit cutpoints partially pooled toward a common cutoff; rank posterior latent merit across all candidates to meet the global 40% budget. Unlike strategy 22's income interaction, this models program-specific award thresholds without a need interaction.

## 3. Rubric

Tests a plausible allocation structure while retaining a single exact global budget.

## 4. Implementation

Create `work/strat34/program_threshold.py`; fix shared slopes, shrink program cutpoints, assess support, and report how many awards shift by program relative to V1.

## 5. Experiment

Freeze one model and upload once, if allowed. Acceptance requires >94% on confirmed official accuracy. No program-specific leaderboard probing or row-level label deduction; internal committee fit is only a fit diagnostic.

## 6. Risks

Small programs may have unstable cutpoints; the target may use a global rather than program quota.

## 7. Combines with

Compare against 22 and 23 as standalone candidates.

## 8. Results log

NOT RUN. No ordinal model or official metric result has been measured.
