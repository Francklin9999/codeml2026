# Context-dependent historical committee rules

The incumbent's highest exactly documented platform accuracy remains 94.88%.
The latest round-five feedback reports 94.85% for "the last three" and 94.73%
for the others. Exact filenames and macro F1 were not supplied; these results
are recorded without assigning them to individual files or replacing the best
artifact.

This experiment tests whether the historical committee's academic-score and
work-hour effects differ across regional groups or household incomes. It fits
spline interactions using original historical labels. During corrected scoring,
each applicant's academic score and hours remain fixed, and regional/income
context is averaged over the same training profiles. Unlike the previous
regional-retention models, applicant region does not affect the corrected score.

Nine configurations were compared on the existing five development folds.
The best interaction configuration uses regional group interactions and C=3.
Historical development accuracy was 88.925% versus the incumbent's 88.850%,
while log loss worsened from 0.256633 to 0.257017. These small differences do
not demonstrate a better model or establish a hidden reference rule. Historical
committee decisions remain a different target from the organizer reference.

| Submission | Model | Grants | Decisions differing from incumbent |
|---|---|---:|---:|
| `context_slopes_blend.csv` | Equal-weight probability ensemble of incumbent and interaction model | 1,600 | 18 |
| `context_slopes.csv` | Corrected regional interaction model | 1,600 | 42 |

Platform results: `context_slopes.csv` scored 94.43% accuracy / 94.19% macro F1;
`context_slopes_blend.csv` scored 94.73% / 94.50%. Neither beat the incumbent. The ensemble's 50/50 weights were fixed
before exporting evaluation predictions, not optimized on platform outcomes.
Each model was refitted to all 10,000 original training examples after historical
development selection. No hidden reference labels, CSV probes, IDs as features,
per-applicant overrides, or generator recovery enter fitting or prediction.

Checks passed for serialization/export byte equality, score independence from
IDs, supplied labels, applicant income and region, row-order invariance, and
single-applicant scoring. Reports include artifact and submission hashes.

## Reproduce

From `equialgo-participants/`:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python work/codex_model/context_slopes.py
python model_ensemble.py predict \
  --model work/codex_model/context_slopes/context_slopes_blend.joblib \
  --input data/candidats_evaluation.csv \
  --output upload_model_round6/context_slopes_blend.csv
```

Detailed historical validation, provenance, verification, and saved estimators
are in `work/codex_model/context_slopes/report.json` and that directory's model
artifacts. Repeated platform previews are model selection on this evaluation
cohort, not independent evidence of generalization.
