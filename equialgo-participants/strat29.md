# EquiAlgo · Strategy 29: Within-region pairwise ranking without region intercepts

| | |
|---|---|
| **Status** | IN PROGRESS (pairwise fit; official evaluation pending) · **Priority** P1 · **Effort** 4–6 h · **Depends on** committee history, region labels, V1 baseline |
| **Rubric** | Hidden-reference accuracy; global 1,600-grant budget |
| **Work folder** | work/strat29/ |

## 1. Context and evidence

Current logit models predict committee labels and include regional signals. Hidden reference is unknown. A regional intercept can reproduce a group-level decision penalty; within-region comparison can instead learn shared feature ordering without using region at candidate scoring.

## 2. Idea and novelty

Train a pairwise Bradley–Terry or pairwise boosting model on within-region applicant pairs, ordering committee positives above negatives while cancelling additive regional baseline shifts. Score candidates with a shared ranking function, then select global top 1,600. Unlike strategy 12's group-specific thresholds, this removes region intercepts structurally and learns pairwise preference.

## 3. Rubric

Tests whether relative feature ordering transfers better than absolute committee grant probability.

## 4. Implementation

Create `work/strat29/pairwise.py`; sample pairs reproducibly, cap pair count, tune only inside training folds, and quantify cross-region overlap. Do not create cross-region pairs unless feature comparability is justified.

## 5. Experiment

Freeze one candidate before authorized leaderboard evaluation. Adopt only if accuracy >94% on confirmed same metric; committee pairwise validation is diagnostic, not success. Keep exact quota and candidate order.

## 6. Risks

Within-region ordering may not identify cross-region ranking offsets; reference could use legitimate group thresholds or absolute cutoffs.

## 7. Combines with

Compare 23, 34 and V1 independently; no post-hoc blend without a separate test.

## 8. Results log

The preregistered pairwise implementation has been run; committee-label diagnostics, candidate hash/quota validation and limitations are in [`work/strat29/report.md`](work/strat29/report.md). No authorized upload or hidden-reference score exists, so the official >94% criterion remains NOT RUN.
