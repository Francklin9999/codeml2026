# EquiAlgo · Strategy 27: Positive-unlabeled latent merit estimator

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P2 · **Effort** 5–7 h · **Depends on** committee-history labels and rubric |
| **Rubric** | Hidden-reference accuracy; 36–44% selection constraint |
| **Work folder** | work/strat27/ |

## 1. Context and evidence

Only committee outcomes are observed for historical applicants. If committee-positive cases are enriched for deservingness while many negatives remain unlabeled, treating every negative as a true negative may train the wrong boundary. The PU assumption is hypothetical and must be stated.

## 2. Idea and novelty

Fit a positive-unlabeled risk estimator, varying class prior and selection mechanism; rank candidates and impose the required quota. Unlike strategy 11's reweighing/massaging, this treats negatives as unlabeled rather than known clean negatives.

## 3. Rubric

Explores a plausible hidden-reference structure when recorded committee negatives may contain positive latent cases.

## 4. Implementation

Create `work/strat27/pu.py`; compare nonnegative PU risk with standard logistic using the same features, folds and fixed prior grid. Keep assumptions and candidate files separate from evaluation results.

## 5. Experiment

Pre-register two priors, choose one candidate before official evaluation, and upload only with authorization. Adoption requires >94% leaderboard accuracy on the same metric. If not, report no improvement; do not infer hidden positive IDs from score deltas.

## 6. Risks

PU assumptions may not hold; prior is unknown; class-conditional selection can invalidate estimator.

## 7. Combines with

Compare 26 and 21; combine only after independent metric evidence.

## 8. Results log

NOT RUN. No PU assumption or model has been validated.
