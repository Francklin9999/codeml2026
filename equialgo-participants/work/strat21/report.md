# Strategy 21: fixed label-noise sensitivity likelihoods

## Preregistered setup

This is a fixed-rate sensitivity analysis, not EM and not an estimate of the hidden label-noise process. The likelihood uses `p(committee=1)=FP+q(1-FN-FP)` where `q` is a fitted latent logistic score. Rates were frozen before fitting: pooled FN=.05/FP=.02; remote FN=.10/FP=.02; and remote FN=.05/FP=.06, with central FN=.05/FP=.02 in the group-specific cases. These rates are assumptions within bounded ranges; they are not identified from the single committee-label source.

The shared V1 feature set and seed-42 stratified 70/30 development split were used. On candidate scoring the remote feature is set to zero; the final allocation is global top-1,600. The split is post-hoc development data, not sealed.

## Committee-label diagnostics

| Scenario | Holdout accuracy at 0.5 | Holdout AUC | Top-40% committee agreement | Holdout changes vs V1 | Candidate changes vs V1 |
|---|---:|---:|---:|---:|---:|
| V1 (`C=1`) | 0.88667 | 0.95439 | 0.86267 | 0 | 0 |
| Pooled FN=.05/FP=.02 | 0.88500 | 0.95435 | 0.86267 | 6 | 8 |
| Remote FN=.10/FP=.02 | 0.88500 | 0.95399 | 0.86200 | 8 | 8 |
| Remote FN=.05/FP=.06 | 0.88633 | 0.95267 | 0.86333 | 12 | 8 |

The modest committee diagnostic differences cannot validate the assumed noise rates or establish hidden-reference accuracy. All three configurations converge, but optimizer convergence says nothing about rate identifiability.

## Candidate files

All candidates validate with 4,000 ordered rows and exactly 1,600 grants. Candidate group sizes are 1,628 remote and 2,372 central.

| Scenario | Remote grants | Central grants | SHA-256 |
|---|---:|---:|---|
| Pooled FN=.05/FP=.02 | 625 | 975 | `180DC7475EF002C5E6C51271FE18EC4AF07E40EE9C532102D5C98C54542873E1` |
| Remote FN=.10/FP=.02 | 625 | 975 | `1212EE6371026D800650ED02CC1428C5A4E78353FBAB762490003B48DCB2677F` |
| Remote FN=.05/FP=.06 | 624 | 976 | `2995057C531D908C2ED0FC7FF6B7F650BE7A75FB132FB794F0991E6ED0D81138` |

Files are under `work/_local/strat21/`. No official upload or hidden-reference score is recorded; the >94% criterion remains untested.
