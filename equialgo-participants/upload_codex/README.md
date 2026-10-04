# Independent Codex candidates

Try these alongside Claude's `upload_r3` files. All files here contain 4,000
candidate IDs in original order and exactly 1,600 grants (40%).

## Suggested upload order

1. `model_F_ensemble.csv` — average of spline, probit and boosted-tree rankings.
2. `model_B_spline_academic_hours.csv` — smooth nonlinear effects learned from historical data.
3. `model_E_probit_academic_hours.csv` — Gaussian latent-score model, learned linear effects.
4. `model_A_boosted_academic_hours.csv` — boosted-tree nonlinear effects.
5. `model_D_boosted_regional_transport.csv` — different assumption: retain income information but adjust income/distance distributions for region.
6. `model_C_extra_trees_academic_hours.csv` — randomized-tree alternative.

This order is a practical test order, **not a validated ranking**. None of these
new files has a measured leaderboard accuracy yet. Keep the highest actual result.
`00_known_best_93_63.csv` reproduces the supplied `r2_11.csv` as a fallback:
93.63% accuracy and 93.36% macro F1, as reported in the screenshot.

Record both Accuracy and F1 macro with each filename. The platform displays these
before confirmation; confirm only if you want to replace the current submission.

## What differs from Claude's search

Models A/B/C learn the historical committee's response from the 10,000 labeled
applications. At scoring time, they keep each applicant's academic score and
hours, averaging the other features over the same 48 observed profiles for
everyone. This tests the hypothesis that income and geography should not directly
affect the hidden reference. Model E estimates the academic/hours weights with a
probit model. Model F combines three distinct fitted models.

Model D instead maps income and distance from each region to central-region
distributions using training-data percentiles, then averages predictions under
Montreal and Capitale-Nationale. It preserves program, hours and first-generation
status. This is a competing causal assumption, not a proven correction.

Held-out historical committee validation (2,500 rows, seed 2026):

| Model | Accuracy | ROC AUC | Log loss |
|---|---:|---:|---:|
| Boosted trees | 88.12% | 0.9531 | 0.2704 |
| Spline logistic | 88.60% | 0.9541 | 0.2667 |
| Extra trees | 88.60% | 0.9528 | 0.2798 |

**These are committee-reproduction metrics before correction, not estimates of
leaderboard accuracy.** The hidden reference labels are unavailable. Tree and
spline corrections can still transfer poorly if our reference assumptions are wrong.

The `optional_rule_candidates/` subfolder contains seven additional rule/consensus
candidates from an exploratory simulation. Their simulated performance depends on
assumptions and must not be treated as validation or a promise of 95% accuracy.
Prioritize the six independently fitted models above, per your request.

## Reproduce

From `equialgo-participants/`:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 python work/codex_accuracy/models.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 python work/codex_accuracy/search.py
```

Code, logs, fitted coefficient diagnostics, raw score arrays and manifests live in
`work/codex_accuracy/`. No existing strategy scripts or root predictions were changed.
