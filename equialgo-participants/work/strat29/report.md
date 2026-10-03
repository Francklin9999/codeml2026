# Strategy 29: within-region pairwise ranking

## Result

The preregistered model sampled 25,000 positive-negative comparisons in each of five regions (125,000 comparisons per fit), with pair seed 2901. Separate fits were made for the 70% development training subset and the full history used for the candidate file; those samples can overlap and are not described as unique jointly. Each fit uses one shared logistic Bradley–Terry scorer with no region or postal columns. The committee diagnostic used a stratified 70/30 split with seed 42, reserved before this run; the data has already informed earlier development, so this is post-hoc and not a sealed test.

| Metric | Pairwise | V1 (`C=1`) |
|---|---:|---:|
| Holdout committee AUC | 0.94158 | 0.95439 |
| Holdout committee agreement after global top-40% allocation | 0.86733 | 0.86267 |
| Holdout rows | 3,000 | 3,000 |

The pairwise score is a ranking score, not a calibrated committee probability; no threshold-0.5 accuracy is reported. The top-40% committee agreement is a ranking/allocation diagnostic only. The small increase over V1 on this reused-development slice neither establishes statistical significance nor predicts hidden-reference performance.

The generated candidate has 1,600 grants and differs from the validated V1 CSV on 18 of 4,000 candidate IDs. Candidate group counts are 1,628 remote (631 selected) and 2,372 central (969 selected). Validation confirms exact row count, quota, and 40% grant rate.

Candidate: `work/_local/strat29/candidate_predictions_S29_pairwise.csv`  
SHA-256: `65F64E5FE63E803CC940E0B3B221B5B72922805FEFDF0BC3B24E1FC2CC9B6B4E`

## Limits and next step

No official upload or hidden-reference score has been recorded. Committee accuracy/AUC do not establish the required hidden-reference accuracy above 94%. User can manually upload the hash-locked artifact if organizer rules and remaining attempts allow.
