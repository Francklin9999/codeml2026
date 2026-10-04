# Income and allocation hypotheses

The best platform-verified model remains 94.88% accuracy / 94.66% macro F1.
All eight round-four models scored lower. Retaining regional effects and
regional merit normalization did not improve agreement with the reference.

The following four models test income correction separately. Their underlying
coefficients are learned from the original 10,000 historical committee labels.
Region is still neutralized. The income effect is a global model setting,
applied equally to unseen applicants; no individual predictions are edited.

| File | Model assumption | Grants |
|---|---|---:|
| `income_retained_05.csv` | Retain 5% of the fitted income association | 1,600 |
| `income_retained_15.csv` | Retain 15% of that association | 1,600 |
| `income_need_05.csv` | Reverse 5% of the association to favor financial need | 1,600 |
| `income_need_15.csv` | Reverse 15% of the association | 1,600 |
| `budget_39.csv` | Same incumbent model, 39% allocation policy | 1,560 |
| `budget_41.csv` | Same incumbent model, 41% allocation policy | 1,640 |

Suggested first comparison: `income_retained_05.csv` and `income_need_05.csv`.
The income settings are policy hypotheses, not policies validated by historical
committee accuracy. Reversing an observed income association explicitly adds
a need-based policy assumption. No organizer definition establishes this as
the reference's rule. The budget variants test the allowed grant envelope;
they do not constitute better learned rankings. None has a measured platform
score yet.

Saved models, source hashes, output hashes, provenance, and verification results
are in `work/codex_model/income_policy/`. Checks cover exact serialization/export
reproduction, novel identifiers, supplied-label exclusion, and single-applicant
and row-order score invariance. All files satisfy the 36–44% budget envelope.

## Reproduction

From the challenge directory:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python work/codex_model/income_policy.py
python model_ensemble.py predict \
  --model work/codex_model/income_policy/income_need_05.joblib \
  --input data/candidats_evaluation.csv \
  --output upload_model_round5/income_need_05.csv
```

## Rejected modeling hypothesis

`work/codex_model/noise_model.py` additionally fitted a symmetric label-flip
likelihood, testing floors 0%, 3%, 6%, and 9% on the existing five development
folds, with preprocessing learned separately inside every fold. No holdout or
evaluation labels were used. Log losses were approximately 0.25665, 0.26556,
0.27824, and 0.29312: the zero-noise version won. Its `noise_aware.csv` is a
research export with zero noise correction, not a recommended new hypothesis.
The likelihood's analytical gradient passed a finite-difference check. The
complete diagnostics are in `work/codex_model/noise_model/report.json`.
