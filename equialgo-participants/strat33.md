# EquiAlgo · Strategy 33: Heteroskedastic probit with merit-dependent committee noise

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P2 · **Effort** 4–5 h · **Depends on** history features and candidate file |
| **Rubric** | Hidden-reference accuracy; exact grant budget |
| **Work folder** | work/strat33/ |

## 1. Context and evidence

Committee-label CV AUC is about .957, but this is not hidden-reference accuracy. Existing strategy 12 models group thresholds with fixed probit scale. Applicant decision noise may vary with merit or program, changing confidence near different decision regions.

## 2. Idea and novelty

Fit a heteroskedastic probit: shared latent merit mean plus committee regional penalty, with noise scale sigma(x) depending on merit band/program. At prediction, rank by posterior mean merit after excluding committee penalty, not by award probability inflated by scale. This varies conditional noise rather than fixed-scale thresholding or label-transition rates.

## 3. Rubric

Tests whether structured committee uncertainty explains outcomes better than a homoskedastic model.

## 4. Implementation

Create `work/strat33/hetero_probit.py`; fix latent location/scale normalization, bound sigma ratios, and preregister one merit-band and one program-dependent form. Profile identifiability; output exact top 1,600.

## 5. Experiment

Freeze one candidate and use one authorized upload at most. Adopt only if hidden-reference leaderboard accuracy is >94% on the confirmed metric. Committee-fit likelihood is diagnostic only. No hidden labels may be inferred from aggregate feedback.

## 6. Risks

Location/scale are confounded; heteroskedasticity may absorb misspecification or real program rules. Small strata destabilize scale estimates.

## 7. Combines with

Compare against 28 robust-link and 34 program-threshold candidates, separately.

## 8. Results log

NOT RUN. No heteroskedastic fit or hidden-reference score exists.
