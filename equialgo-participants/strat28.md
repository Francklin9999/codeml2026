# EquiAlgo · Strategy 28: Robust Student-t latent-score link

| | |
|---|---|
| **Status** | IN PROGRESS (Student-t fits; official evaluation pending) · **Priority** P2 · **Effort** 4 h · **Depends on** feature pipeline and V1 baseline |
| **Rubric** | Hidden-reference accuracy; valid quota |
| **Work folder** | work/strat28/ |

## 1. Context and evidence

Current neutralized candidates mostly use logistic regression; the small GBM V4 has lower stability. Synthetic data and committee residuals may include outliers or heavier tails than logistic link assumes, but there is no hidden-label evidence for this.

## 2. Idea and novelty

Fit a robust latent-score model with Student-t residual/link approximation and compare with probit under fixed features. This targets outlier sensitivity in the conditional response, not the region-threshold Bayesian model of strategy 12 or broad model-family search of strategy 16.

## 3. Rubric

Provides one parsimonious alternative likelihood for candidate hidden-reference accuracy.

## 4. Implementation

Create `work/strat28/robust_link.py`; fix degrees of freedom at two preregistered values, standardize within folds, and generate exact top-k output. Record score/rank differences from V1.

## 5. Experiment

Select one robust fit before any authorized leaderboard result; maximum one upload for this family. Adopt only if accuracy >94% on same confirmed metric. Historical likelihood/CV differences do not count as target success.

## 6. Risks

Tail robustness may reduce accuracy when logistic assumptions are adequate; numerical fitting may be unstable.

## 7. Combines with

Compare against 23 monotone GAM; no stacking until standalone evaluation.

## 8. Results log

The two fixed-degree Student-t link fits have been run; committee diagnostics, optimizer status and candidate hashes are in [`work/strat28/report.md`](work/strat28/report.md). No authorized upload or hidden-reference score exists; the official >94% criterion remains NOT RUN.
