# EquiAlgo shared evaluator: partial continuation

Claude left `data.py`. Codex added format/budget validation, shared model fitting, reference simulations and the scorer, then shifted priority to OptiFrame at the user's request.

Implemented: H1, H1n5, H1n10, H2, three H3 weights, H4 and H5; metrics accuracy/F1/balanced accuracy; 2-group and 5-region EO gap; fixed published denominator 0.270 and measured simulated baseline denominator. Strategy 1's V1–V5 runner and measured report are now available under `work/strat1/`. H6, strategy registry, robustness heatmap and notebook-test-split calibration remain unfinished. No selected production model or official submission is produced.

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s equialgo-participants\work\shared -p test_score.py -v
.\.venv\Scripts\python.exe equialgo-participants\work\shared\validate_submission.py path\to\predictions.csv
.\.venv\Scripts\python.exe equialgo-participants\work\shared\score.py --pred path\to\predictions.csv --all-hypotheses --metric accuracy,f1,balanced_accuracy --grouping 2,5 --output equialgo-participants\work\_local\scores.csv
```

Six scorer/validator sanity tests pass. A smoke run on the supplied files generated nine reference hypotheses with exactly 1,600 positives each among 4,000 candidates. A perfect simulated predictor scored 35/35. The smoke prediction file under `_local/` is a fixture, **not a recommended submission**.

Assumptions differ from the incomplete pseudocode where necessary:

- H1n5/H1n10 swap equal numbers of positive/negative labels; the stated noise fraction counts all changed labels and the 40% budget remains fixed.
- H5 trains a gradient booster **with** the remote flag, then averages over that flag using historical group proportions. A model trained without region cannot average out a region input; distance and other proxies remain, so H5 is only one hypothetical world.
- H4 quantile-maps distance to the central historical distribution before neutralising the V1 remote flag. V1 excludes postal code. V3 neutralises postal indicators using a consistent Montreal distribution and all region terms together.
- The random comparator draws the same number of grants as the submitted prediction. The unknown official comparator may instead always use 1,600; compare only 40% runs until that rule is verified.
- An EO comparison with a group having no reference positives is rejected as undefined. When the simulated baseline gap is zero, measured-mode equity gives full points only for zero residual gap; this is an explicit simulation convention, not a known official rule.
- Cross-validation fits standardisation inside each fold. Reference hypotheses fitted to committee decisions are not independent ground truth; V1/H1 and V4/H5 share model families and can agree by construction.

Do not pick a model solely because it matches its own simulated reference. The organisers' reference and exact scoring function remain unknown.
