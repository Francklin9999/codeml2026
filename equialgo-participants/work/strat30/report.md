# Strategy 30: income functional-form competition

## Preregistered setup

The three forms share V1 features, seed-42 stratified 70/30 history split, logistic `C=1`, and the same global top-40% candidate allocation after setting the remote indicator to zero. The spline uses four quantile knots fitted on the corresponding training rows only. The holdout was fixed before this experiment but is post-hoc development data, not a sealed test. All three candidates are preserved; no form was selected by hidden feedback.

## Committee-label diagnostics

| Form | Holdout accuracy at 0.5 | Holdout AUC | Top-40% committee agreement | Holdout selection changes vs V1 | Candidate changes vs V1 |
|---|---:|---:|---:|---:|---:|
| V1 (`C=1`) | 0.88667 | 0.95439 | 0.86267 | 0 | 0 |
| Raw income / 100,000 | 0.88367 | 0.95402 | 0.86333 | 48 | 50 |
| Log income | 0.88667 | 0.95442 | 0.86200 | 2 | 2 |
| Restricted cubic spline income | 0.88700 | 0.95429 | 0.86133 | 18 | 10 |

These are committee-label metrics, not hidden-reference accuracy. Differences are small and measured on a post-hoc development split; they do not pass the >94% official criterion.

## Candidate files

All files validate with exactly 4,000 ordered rows and 1,600 grants. Candidate counts are 1,628 remote and 2,372 central.

| Form | Remote grants | Central grants | SHA-256 |
|---|---:|---:|---|
| Raw | 633 | 967 | `BF5BF82B6A053DFDA64DCE2883196B4350809CE9E3B3634901087D8E105071F7` |
| Log | 628 | 972 | `4582A5E09BA4C1CFD966E5E0FE98E0D38AF924F8CBD0A23A99B085823BDBCFCB` |
| Restricted cubic spline | 628 | 972 | `BD417202A2F90E56870291B375A75B8F13F27D351D4FC46E6F6BA00B7005CDCE` |

Files: `work/_local/strat30/candidate_predictions_S30_income_raw.csv`, `work/_local/strat30/candidate_predictions_S30_income_log.csv`, and `work/_local/strat30/candidate_predictions_S30_income_spline.csv`.

No leaderboard upload or official hidden-reference score has been recorded. User can upload a chosen preregistered file manually if attempts allow; any returned score must be recorded against that exact hash.
