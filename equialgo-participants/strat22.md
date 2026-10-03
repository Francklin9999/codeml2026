# EquiAlgo · Strategy 22: Ordinal merit threshold with financial-need interaction

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P1 · **Effort** 4–6 h · **Depends on** candidate features, V1 baseline CSV |
| **Rubric** | Hidden-reference accuracy; fixed 1,600-award quota |
| **Work folder** | work/strat22/ |

## 1. Context and evidence

The current logit uses cote-R, income, hours, program, and geography; its large standardized cote-R coefficient reflects committee decisions, not hidden-reference effects. No candidate has a reported leaderboard result. A latent scholarship rule could combine ordered merit with financial need rather than use one linear committee imitation.

## 2. Idea and novelty

Fit an ordinal merit band (cote-R ranks) with a smooth income interaction that changes award odds within, not across, merit bands. This differs from strategy 12's region-specific threshold probit: the threshold varies by merit stratum and need, with no regional intercept.

## 3. Rubric

Tests a plausible, interpretable reference family aligned to merit and need while preserving exact budget.

## 4. Implementation

Create `work/strat22/ordinal_need.py`; use ordered cote-R bins, monotone income spline, and preregistered interaction form. Generate top-1,600 mask; retain all coefficients and tie policy.

## 5. Experiment

Compare one frozen candidate with V1 on the authorized accuracy leaderboard; at most two uploads if allowed. No test-set tuning or label inference. Adoption requires >94% on the same confirmed metric; internal committee CV is diagnostic only.

## 6. Risks

Merit bands/need tradeoff are assumptions; nonlinearity may overfit and income can be proxy-laden.

## 7. Combines with

Compare against 23 and 35 on fixed seeds and inputs.

## 8. Results log

NOT RUN. No ordinal rule or hidden-reference result exists.
