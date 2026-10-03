# Reproduce the IVADO candidate experiments

Run from a checkout with the supplied `equialgo-participants/data` files and the existing NumPy, pandas, SciPy and scikit-learn environment. The source data remains read-only. Python module tests use temporary synthetic CSV fixtures; no hidden labels or leaderboard access are required.

```powershell
$python = '.\.venv\Scripts\python.exe'
$dataRoot = (Resolve-Path 'equialgo-participants/data').Path
$v1 = (Resolve-Path 'equialgo-participants/work/_local/strat1/candidate_predictions_V1.csv').Path
& $python equialgo-participants/work/strat29/pairwise.py --data-root $dataRoot --output-dir equialgo-participants/work/_local/strat29 --v1-path $v1
& $python equialgo-participants/work/strat30/income_forms.py --data-root $dataRoot --output-dir equialgo-participants/work/_local/strat30 --v1-path $v1
& $python equialgo-participants/work/strat21/noise_likelihood.py --data-root $dataRoot --output-dir equialgo-participants/work/_local/strat21 --v1-path $v1
& $python equialgo-participants/work/strat28/robust_link.py --data-root $dataRoot --output-dir equialgo-participants/work/_local/strat28 --v1-path $v1
```

Generate V1 first with `work/strat1/neutralise.py` if its ignored CSV is absent. All nine new CSVs select 1,600 of 4,000 applicants; they are regenerable, not committed source data. Validate any file with `work/shared/validate_submission.py <path> --data-root <directory>`.

The parent independently reran the tests and the fixed-noise/Student-t runners. Nineteen focused tests pass across `shared`, `strat21`, `strat28`, `strat29` and `strat30` (run `python -m unittest discover -s <folder> -p 'test_*.py' -v` separately for each). Audit fixes include raw-income double scaling, the erroneous 62,500 pair-count report (correct count: 125,000 per fit), rejection of fractional target labels and invalid regularization values.

Committee development accuracy/AUC and simulated references **are not** official hidden-reference accuracy. The user has not uploaded V1 yet; no official score is available, and beating 94% remains unverified. A t-link df=10 artifact has exactly the same decisions as V1, so uploading both cannot provide a distinct prediction test. Do not spend an attempt on duplicate binary predictions.

For measured diagnostics and candidate hashes, read the four per-strategy reports and [the complete test matrix](STRATEGY_TEST_MATRIX_21_40.md). Full strategy adoption gates remain unrun.
