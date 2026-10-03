# EquiAlgo strategies 21–40

All 20 are untested proposals. The user confirms the target is **leaderboard accuracy against the hidden reference**, and the required result is **strictly above 94% on that same metric**. The user-reported 94% leader has not been independently verified here, and the validated V1 baseline CSV has no recorded leaderboard score yet. Neither committee CV AUC nor self-generated H1–H5 simulation scores count as success. Do not infer individual hidden labels from scalar feedback or seek leaked labels.

## First experiments

1. **Upload the validated V1 baseline first**, after confirming allowed attempts; record returned score and file hash. This establishes the actual starting point rather than assuming V1 trails 94%.
2. **Strategy 21 — Asymmetric group-conditional label-noise model (P1).** Tests group-varying false-positive/false-negative corruption, a plausible hidden-reference mechanism. First run is a bounded sensitivity fit; it does not assume noise is identified.
3. **Strategy 23 — Monotone shape-constrained GAM (P1).** A distinct, interpretable nonlinear candidate to test when income/merit response is not linear. Preselect the form before any leaderboard score.
4. **Strategy 29 — Within-region pairwise ranking (P1).** Learns shared relative merit order while cancelling additive regional shifts, distinct from region-threshold logistic models.

Other high-value families include pooled transition correction, positive-unlabeled risk, matched residual transport, and covariate-shift weighting. Ask the organizer for upload limits; use a small preregistered set and stop when attempts are exhausted. Candidate modeling here is separate from evaluation/provenance safeguards (36–40).

## Proposals

| # | Proposal | Priority | Nearest prior (1–20) | First experiment |
|---:|---|---|---|---|
| [21](strat21.md) | Asymmetric group-conditional label-noise model | P1 | 11 label-bias correction | Bounded EM over region-specific flip rates |
| [22](strat22.md) | Ordinal merit with financial-need interaction | P1 | 12 threshold probit | Fit ordinal merit bands × income spline |
| [23](strat23.md) | Monotone shape-constrained GAM | P1 | 15 scorecard | Three preregistered spline complexities |
| [24](strat24.md) | Matched central/remote residual transport | P2 | 14 score transport | Match within merit/program; check overlap |
| [25](strat25.md) | Soft-label confidence weighting | P2 | 16 Rashomon audit | OOF entropy/agreement weights |
| [26](strat26.md) | Pooled label-transition correction | P1 | 11 reweighing/massaging | Profile asymmetric flip rates |
| [27](strat27.md) | Positive-unlabeled latent merit | P2 | 11 label correction | Fixed class-prior sensitivity grid |
| [28](strat28.md) | Robust Student-t latent-score link | P2 | 6 Fairlearn control arm | Compare fixed robust-link parameters |
| [29](strat29.md) | Within-region pairwise ranking | P1 | 12 group threshold model | Bradley–Terry/pairwise learner, global top-k |
| [30](strat30.md) | Raw/log/spline income competition | P2 | 5 proxy audit | Compare three predeclared income forms |
| [31](strat31.md) | Candidate-density covariate weighting | P2 | 11 reweighing | Cross-fit density ratio and ESS guard |
| [32](strat32.md) | Leave-one-region-out transfer model | P2 | 17 intersectional audit | Rotate held-out region folds |
| [33](strat33.md) | Heteroskedastic probit noise scale | P2 | 12 threshold probit | Profile merit/program-dependent decision noise |
| [34](strat34.md) | Program-specific ordinal thresholds | P2 | 12 threshold probit | Partially pool program cutpoints |
| [35](strat35.md) | Cross-family OOF stacking | P2 | 8 minimax ensemble | Stack distinct predictive families |
| [36](strat36.md) | Preregistered limited leaderboard tournament | P1 | 3 leaderboard probing | Baseline, then bounded candidate set |
| [37](strat37.md) | Score receipt and blind verification | P1 | 10 governance/model card | Pair each returned score with hash |
| [38](strat38.md) | Candidate leakage/order audit | P1 | 20 generator analysis | Check lineage, IDs, budget, hidden-label access |
| [39](strat39.md) | Independent reproduction of >94% candidate | P2 | 16 stability analysis | Regenerate and hash-compare finalist |
| [40](strat40.md) | Final choice against confirmed accuracy target | P1 | 10 governance/model card | Verify score receipt; select only if >94% |

## Evaluation gate

For existing recorded results and their limitations, see [RESULTS_OVERVIEW.md](../RESULTS_OVERVIEW.md).

Confirm the exact leaderboard accuracy definition and upload cap before testing. Every candidate must preserve candidate order and exactly 1,600 grants. The ultimate adoption rule is **official hidden-reference accuracy >94%**; a score of 94% or below does not beat the reported benchmark. All CV, committee-label and simulated-reference results are diagnostics only. If permitted attempts do not produce a result above 94%, report that the goal remains unmet.
