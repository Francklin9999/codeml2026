# tools/ : evaluation and STL validation

Offline Python 3.11+ tools. Setup (once):

```
python -m venv tools/.venv
tools/.venv/Scripts/python -m pip install -r tools/requirements.txt     # Windows; use bin/ on macOS and Linux
```

## 1. Collect results (app/eval.html)

1. Measure each lens with a calliper three times per axis and fill `data/own_lenses.template.csv` (copy it to `own_lenses.csv`, delete the two EXAMPLE rows). Reference = median of the three readings.
2. Photograph every lens on the printed sheet, several phones, several repetitions. Name files `<lensId>_<phone>_<rep>.jpg`; `lensId` must match the CSV, `phone` has no underscore.
3. Serve the app (`npm run dev` in `app/`), open `/eval.html`, select all photos (and optionally `own_lenses.csv`), press Run, download `results.csv`.
   Run it with the identity `public/bias.json`: the report fits the correction on the raw measurements.
   The page imports `measureOne` from `src/pipeline.ts` when that file exists, otherwise it calls `rectify`, `segmentClassic`, `measureLens` itself (the status line says which).

`results.csv` columns: `file,lensId,phone,rep,A,B,perimeter,method,reprojErrMm,sharpness,error` (`error` is an error code; A and B are empty on failure).

## 2. Accuracy report

```
python tools/accuracy_report.py results.csv own_lenses.csv [--out DIR] [--seed N]
```

Writes `accuracy_report.md` and `bias.json` (default: next to `results.csv`):

- MAE of A and B, overall and per phone; failure rate (failed photos are excluded from the other figures).
- Bland-Altman: bias, 95 % limits of agreement, slope of difference on mean (proportional bias).
- Repeatability (pooled SD across repetitions of one lens and phone) and variance components lens / phone / residual by random-effects ANOVA, with their share of the total variation. The lens x phone interaction is pooled in the residual; unbalanced data are trimmed to the smallest cell. A missing factor gives "not estimable".
- Least-squares fit `ref = a0 + a1 x measured` per axis with leave-one-lens-out MAE before and after (needs 4 lenses). `bias.json` holds the fitted values for an axis only when its leave-one-lens-out MAE improves, otherwise the identity; it also carries `fittedOn, nLenses, phones, loMaeBefore, loMaeAfter, helps` (plus `helpsA`, `helpsB`), which the app loader ignores. Check the correction on lenses that were not used for the fit before copying it to `app/public/bias.json`.
- Predicted rubric score `30 if MAE <= 1 else max(0, 30 x (4 - MAE) / 3)`: median and 5th percentile over 10 000 random pairs of lenses (error of a lens = mean absolute error over its rows and both axes).
- Decision line: when the predicted median score is under 25, names the dominant component among bias, repeatability and between-phone SD.

## 3. STL check

```
python tools/validate_stl.py monture.stl
```

One line per check (watertight, winding consistent, single body, positive volume, bounding box in mm); exit code 1 if any fails.

## Tests

```
tools/.venv/Scripts/python -m pytest tools/tests -q
```
