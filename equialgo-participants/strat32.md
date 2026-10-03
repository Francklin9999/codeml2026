# EquiAlgo · Strategy 32: Cross-fitted leave-one-region-out transfer model

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P2 · **Effort** 4–5 h · **Depends on** region labels and history |
| **Rubric** | Hidden-reference accuracy; generalization |
| **Work folder** | work/strat32/ |

## 1. Context and evidence

The data has multiple regions and the model runner includes regional terms. Aggregate committee CV can hide failure to transfer into a region. No hidden-reference labels exist by region.

## 2. Idea and novelty

Train on all but one region, predict the held-out region, rotate regions, and use transfer behavior to choose between shared and region-specific feature effects. Unlike strategy 17's intersectional fairness audit, this is a predictive transport stress test and model-selection constraint.

## 3. Rubric

Favors candidate families whose learned relationships transfer instead of memorizing region identity.

## 4. Implementation

Create `work/strat32/leave_region_out.py`; report committee-label log loss and ranking stability by held-out region for candidate families 21–35. Do not advertise these as hidden-target metrics.

## 5. Experiment

Preselect one model using a fixed worst-region committee-transfer criterion, then use one authorized leaderboard upload. Adoption still requires >94% official accuracy. A poor region fold blocks the candidate from being described as robust but does not infer target errors.

## 6. Risks

Regions may differ in target mechanism, and small folds are noisy. Committee transfer is not hidden-reference transfer.

## 7. Combines with

Compare 23 monotone GAM and 31 covariate shift; do not claim external validation.

## 8. Results log

NOT RUN. No leave-region-out experiment is available.
