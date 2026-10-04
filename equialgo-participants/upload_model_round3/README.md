# Spline model comparisons

The verified best model remains `upload_model_round2/sparse_spline.csv` at
94.88% accuracy and 94.66% macro F1. All seven variants have now been scored;
the 95% target has not been reached.

Measured results (all are outputs of saved, reusable models):

| File | Accuracy | Macro F1 | Grants |
|---|---:|---:|---:|
| `flexible.csv` | 94.88% | 94.66% | 1,600 |
| `regularized.csv` | 94.88% | 94.66% | 1,600 |
| `less_regularized.csv` | 94.88% | 94.66% | 1,600 |
| `spline_blend.csv` | 94.73% | 94.50% | 1,600 |
| `smooth.csv` | 94.73% | 94.50% | 1,600 |
| `uniform.csv` | 94.73% | 94.50% | 1,600 |
| `training_threshold.csv` | 94.53% | 94.32% | 1,634 |

The blend weights are 76.58% smooth, 19.72% flexible, and 3.70% uniform. They
are learned from historical out-of-fold probabilities. Historical validation
still favors the existing five-knot model; these alternatives are hypotheses
for a different reference target, not guaranteed improvements.

`regularized.csv` and `less_regularized.csv` are additional regularization
diagnostics. Each changes only two predictions from the verified model, so
neither alone can take the current score over 95%. They need not consume the
next preview slots.

The first four files use a 40% cohort allocation. The last uses a single fixed
threshold learned on historical data: it applies `model.predict()` unchanged
to each applicant. All satisfy the 36–44% budget. No CSV is manually altered.

Training loads only original historical labels and the audited development
split; it reads the evaluation features only after fitting and saving models.
The historical holdout is not reused for selection, and no preview scores or
reconstructed evaluation labels are used for fitting. Preview feedback selects
the model family to investigate and must not be mistaken for independent test
validation after repeated comparisons.

Reproduce all model fits and predictions from `equialgo-participants/`:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python model_ensemble.py tune-spline
python work/codex_model/verify_spline.py
```

To run one saved model on any compatible applicant file:

```bash
python model_ensemble.py predict \
  --model work/codex_model/spline_tuning/spline_blend.joblib \
  --input data/candidats_evaluation.csv \
  --output upload_model_round3/spline_blend.csv
```

Training reports, parameters, saved models, file hashes, and verification are
under `work/codex_model/spline_tuning/`.
