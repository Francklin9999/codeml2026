# Strategy 28: fixed-degree Student-t links

## Preregistered setup

The model uses the shared V1 feature matrix with a binary Student-t cumulative distribution link, fixed `df=3` and `df=10`, standardized training features, fixed `C=1` coefficient regularization, and seed-42 stratified 70/30 committee development split. For candidate rankings, the remote feature is set to zero on a copy of the feature matrix. This holdout is post-hoc development data, not a sealed test.

## Committee-label diagnostics

| Link | Holdout accuracy at 0.5 | Holdout AUC | Top-40% committee agreement | Holdout changes vs V1 | Optimizer iterations |
|---|---:|---:|---:|---:|---:|
| V1 logistic (`C=1`) | 0.88667 | 0.95439 | 0.86267 | 0 | n/a |
| Student-t, df=3 | 0.88600 | 0.95433 | 0.86267 | 8 | 24 |
| Student-t, df=10 | 0.88667 | 0.95441 | 0.86200 | 2 | 22 |

These are committee-label metrics only. Similar fit and convergence do not establish better hidden-reference performance.

## Candidate files

Both files validate at 4,000 ordered candidates and 1,600 grants. Candidate group sizes are 1,628 remote and 2,372 central.

| Link | Remote grants | Central grants | Candidate changes vs V1 | SHA-256 |
|---|---:|---:|---:|---|
| Student-t, df=3 | 626 | 974 | 4 | `DBA7897048ED03529FF4A4F7E39B0421B2392A9702225564ABA206F969E3D8EE` |
| Student-t, df=10 | 628 | 972 | 0 | `0C5E42FCC201884F5A45BE71B6454E8CA9B69183F02BB85B7A5F654D9977662E` |

Files are under `work/_local/strat28/`. The df=10 candidate matches V1's binary decisions. No official upload or hidden-reference score is recorded; the >94% criterion remains untested.
