# EquiAlgo · Strategy 30: Raw/log income spline competition

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P2 · **Effort** 3–4 h · **Depends on** fixed candidate table |
| **Rubric** | Hidden-reference accuracy; exact top-k budget |
| **Work folder** | work/strat30/ |

## 1. Context and evidence

Report 01 shows both raw income and log income in different variants; their committee coefficients do not establish the hidden reference's functional form. Income range is broad, and linear/log assumptions may both be misspecified.

## 2. Idea and novelty

Compare raw linear, log-linear, and restricted cubic spline income terms, each with identical folds, features, and regularization. Unlike strategy 5's proxy association audit, this tests a specific representation choice as a predictive candidate family.

## 3. Rubric

May improve ranking if hidden awards respond nonlinearly to financial need; effect remains a hypothesis until official evaluation.

## 4. Implementation

Create `work/strat30/income_forms.py`; preregister three forms and knot locations from training quantiles. Keep the best internal form by a fixed rule, create one candidate CSV, and validate 1,600 grants.

## 5. Experiment

Upload once if allowed. The only adoption criterion is >94% on confirmed leaderboard accuracy; committee CV selects a diagnostic form but does not satisfy the target. Do not use upload feedback for row-label reconstruction.

## 6. Risks

Income may be a weak or impermissible criterion; flexible splines can overfit.

## 7. Combines with

Compare within 22 and 23; avoid multiplying feature-search degrees of freedom.

## 8. Results log

NOT RUN. No functional-form comparison or official score exists.
