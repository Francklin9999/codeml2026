# Model trained on historical applications

**Current best verified model: sparse spline, 94.88% accuracy and 94.66% macro
F1 on the platform.** The >95% target is still unmet. `best_model.json` records
the saved artifact and its associated scored prediction hash. Default prediction
uses that artifact and writes `upload_model_best/predictions.csv`.

This pipeline fits models to the 10,000 original historical applications, saves
the fitted estimators, and applies them to unseen applicants. Its only label
source is `data/donnees_demandes.csv`. It does not read submission results,
correction files, or reconstructed evaluation labels. Applicant IDs are used
only for joining the output back to the input rows.

## Reproduce

From `equialgo-participants/`:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python model_ensemble.py train
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python model_ensemble.py predict
python work/codex_model/test_model.py
```

Training needs only the historical file; it does not load evaluation features.
The second command loads the best platform-verified clean model when available,
otherwise the model selected by historical validation. It writes
`upload_model_best/predictions.csv`. It accepts `--input` and `--output` for a different
cohort. To select a particular saved family, pass, for example,
`--model work/codex_model/artifacts/spline.joblib` to `predict`.

To reproduce all family CSVs in one run:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python model_ensemble.py train \
  --candidates data/candidats_evaluation.csv
```

## Model selection and measured results

The split is fixed: 8,000 development rows and 2,000 holdout rows. Five-fold
development validation compares 31 configurations: regularized linear models,
additive cubic splines, histogram boosted trees, and a random forest. All scalers,
spline knots, and categorical encoders are fitted inside each training fold.

Two ensembles are also compared: equal weights, and nonnegative weights summing
to one. The latter learns from the best linear, spline, and boosted model's
out-of-fold development probabilities. The weight fitting is cross-validated
on development data; final weights use all development OOF predictions. Model
selection and weight fitting never consult the reserved holdout. Development
scores guide a hyperparameter search and are not independent final test scores.

The ensemble selected by development log loss has weights:

| Member | Weight |
|---|---:|
| Regularized logistic regression | 74.505% |
| Additive spline logistic regression | 24.380% |
| Histogram boosted trees | 1.115% |

The small tree weight is learned, not forced. More complexity did not improve
historical validation much.

| Estimator | Holdout committee accuracy | Holdout committee log loss |
|---|---:|---:|
| Best individual model | 88.45% | 0.267102 |
| Selected ensemble | 88.65% | 0.267084 |

The ensemble's accuracy interval is 87.19–89.97% (Wilson 95%, 2,000 rows).
The improvement is small; these results do not establish a significant advantage.
This holdout was reserved for this run; earlier exploratory work in the wider
repository had access to the historical dataset.

**These numbers measure reproduction of historical committee decisions before
mitigation. The challenge's hidden reference is a different target. Its accuracy
was initially unmeasured. The subsequent platform preview scored the selected
ensemble at 94.63% accuracy and 94.40% macro F1. This work has not established
>95% on that target.** After selection and reporting, final models are refitted on all
10,000 historical rows, as is usual before scoring the evaluation cohort.

## Mitigation and allocation

During training the estimators can use income, region, and other nuisance
features to distinguish their associations from academic performance and hours
worked. During corrected scoring, each applicant's academic score and hours
are kept, while all other features take the same 64 profiles sampled from
historical training data. The model averages over these profiles; the ensemble
then averages the member probabilities using its fitted weights.

This encodes an explicit policy assumption: academic performance and work
effort may affect merit, while wealth, geography, programme, and first-generation
status should not directly drive these corrected scores. Observational data
alone do not identify the jury's reference or prove this causal interpretation.
The resulting score is a ranking signal, not a calibrated probability of the
hidden reference label.

`GrantModel.score()` and `predict()` work on one new applicant or a batch.
Scores use training-fitted transforms and do not depend on the composition of
the evaluation cohort. `predict()` applies a threshold learned on historical
scores. `allocate()` is the separate budget policy: grant the highest-scoring
40% of the supplied cohort. On 4,000 applicants that is 1,600 grants, within the
required 36–44% range. Ties use academic score and work hours; exact remaining
ties use stable input order. There are no per-applicant exceptions.

## Artifacts and verification

- `artifacts/model.joblib`: selected fitted ensemble, with all preprocessors.
- `artifacts/{linear,spline,boosted,ensemble}.joblib`: fitted family alternatives.
- `artifacts/training_report.json`: search settings, complete results, versions,
  input hash, and explicit null hidden-reference accuracy.
- `artifacts/validation_split.csv`: audit of development folds and the holdout.
- `artifacts/holdout_predictions.csv`: held-out committee predictions and corrected
  allocations; corrected agreement with historical labels is only a diagnostic.
- `artifacts/submissions.json`: output hashes and allocation checks.
- `test_model.py`: checks that IDs and supplied labels do not affect scores,
  scoring works for new profiles and a single applicant, nuisance changes are
  neutralized, the split is disjoint, invalid inputs fail, and saved models
  reproduce the exported decisions.

The existing `model_corrige.py` belongs to the previous approach that reproduces
preview-derived corrections. Use `model_ensemble.py` for this clean pipeline.

## Refinement after the 94.63% preview

`python model_ensemble.py refine` trains sparse additive splines, monotonic
boosted trees, and a 20-member bootstrap spline ensemble. These use historical
training labels and the original development folds; the historical holdout
outcomes are not revisited for selection. The refinement script does not load
platform results or previous prediction files. It writes separate artifacts in
`refinement/` and separate predictions in `upload_model_round2/`.

The platform measured sparse spline at 94.88% accuracy / 94.66% macro F1,
bootstrap spline at 94.78% / 94.56%, and monotonic trees at 94.33% / 94.09%.
The sparse spline is the verified winner so far. These observations choose
which whole model to use; they are not used to reconstruct applicant labels.

## Spline tuning after the 94.88% preview

`python model_ensemble.py tune-spline` compares 30 spline configurations on the
same historical development folds, then fits nearby model alternatives and
a blend whose weights are learned from out-of-fold predictions. The current
five-knot spline remains best on historical validation. The neighboring models
are comparison hypotheses, not claimed local-validation improvements.

`upload_model_round3/` contains the model-generated comparison files. The
`training_threshold` artifact applies the existing spline's threshold learned
from the historical score distribution; its 1,634 grants respect the budget.
This threshold is global and applies to any new applicant. The remaining
models use the same cohort allocation policy as earlier (top 40%).

`python work/codex_model/verify_spline.py` verifies exact regeneration of every
new file, identifier/label independence, single-applicant inference, budget and
schema, and that all scored files remain unchanged. A platform preview is still
needed to measure the new models against the reference.

All seven round-three comparisons were subsequently scored: flexible and the
two regularization variants tied 94.88%; smooth, uniform, and spline blend
scored 94.73%; the training-derived threshold scored 94.53%. The original sparse
spline remains the selected verified model.

## Structural models after the plateau

`python model_ensemble.py structural` trains interaction models, training-fitted
regional merit normalization, and an additional-context model. It also compares
three global regional-correction strengths applied to the original learned
regional coefficient. Fitting uses historical data only; preview results choose
which modeling assumptions to investigate, not the fitted coefficients.

The eight outputs are under `upload_model_round4/`, with saved models and
training diagnostics under `structural/`. `verify_structural.py` checks exact
regeneration, budget/schema, independence from applicant IDs or supplied labels,
single-applicant scoring, and preservation of every scored file. Their platform
accuracy is unmeasured until a user preview.

Feature independence alone cannot establish which features an unknown reference
uses. Regional normalization gave a small historical-validation improvement;
the unknown target still requires external measurement. Correction-strength
and additional-context choices are explicitly exploratory policy assumptions.

Python/package versions used are recorded in the report; the exact environment
is listed in `requirements-lock.txt`. No network access is needed to train or
predict when those dependencies are installed.
