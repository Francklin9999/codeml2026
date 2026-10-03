# EquiAlgo · Strategy 23: Monotone shape-constrained merit/need GAM

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P1 · **Effort** 4–5 h · **Depends on** candidate inputs and frozen baseline |
| **Rubric** | Hidden-reference accuracy; transparent allocation |
| **Work folder** | work/strat23/ |

## 1. Context and evidence

The report records committee-fit coefficients but does not establish the hidden rule. Linear logits may miss nonlinear response in cote-R, income, or work hours. Historical AUC near .957 is committee discrimination, not target accuracy.

## 2. Idea and novelty

Fit an additive logistic GAM with shape constraints: probability nondecreasing in cote-R, nonincreasing in financial need proxy (income), and a predeclared shape for hours. Unlike strategy 15's binned integer scorecard, this estimates smooth constrained curves without arbitrary point bins.

## 3. Rubric

Tests a parsimonious nonlinear family while making directional assumptions visible.

## 4. Implementation

Create `work/strat23/monotone_gam.py`; select smoothing using training folds only, export partial-dependence curves and top-k IDs, and validate exact quota. Limit candidate settings to three predeclared spline complexities.

## 5. Experiment

Freeze one configuration before authorized leaderboard use. Compare V1 and candidate on confirmed accuracy, max two uploads if permitted. Success/adoption requires >94%; no CV-AUC or simulation surrogate counts. If not achieved, do not tune to scalar feedback beyond one predeclared next experiment.

## 6. Risks

Monotonicity may be socially or factually unjustified; constrained shape can suppress true interactions.

## 7. Combines with

Use 32's response curves; compare directly with 22 and 35.

## 8. Results log

NOT RUN. No GAM fit, candidate file, or leaderboard score exists.
