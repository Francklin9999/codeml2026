# OptiFrame · Strategy 18: Metrology validation study (Bland–Altman, repeatability and reproducibility)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (evidence for Data & AI and Presentation; tells us our real expected score) |
| **Effort** | 3 h (data collection 2 h, analysis 1 h) |
| **Depends on** | a working measurement pipeline (strategies 1–3, 8) |
| **Rubric lines** | Data & AI (15: "mesures de performance"), Measurement accuracy (30: know our true error), Robustness (10), Presentation (10) |
| **Differs from 1–10** | Other strategies each run their own experiments. This is a **formal validation study** of the final system, using the methods metrology and optometry use to compare a new instrument with a reference: Bland–Altman agreement, repeatability (same operator), reproducibility (different operators and phones), i.e. a gauge R&R |
| **Work folder** | `optiframe-participants/work/strat18/` |

---

## 1. Context you need

- The jury compares our A and B with **calliper** measurements; the score drops linearly from 30 points at ≤ 1 mm MAE to 0 at 4 mm.
- The calliper itself has error (jaw placement on a curved, bevelled edge). Our "ground truth" is noisy too.

## 2. The idea

Run a small, well-designed study on the final pipeline:
- **Lenses:** 10 own lenses spanning shapes, sizes, powers (plus / minus), materials, tinted vs clear.
- **Reference:** each lens measured with the calliper 3 times by 2 people → reference = mean; calliper repeatability = SD.
- **System:** each lens measured by 3 operators × 2 phones × 3 repetitions (reassembling the rig between sessions for at least one operator).
- **Analysis:** Bland–Altman (bias, 95% limits of agreement) for A and B; repeatability and reproducibility variance components (ANOVA gauge R&R); MAE and the **predicted rubric score** (30 at ≤ 1 mm, linear to 0 at 4 mm) with a bootstrap distribution for "2 random jury lenses".

## 3. Why it could score

It gives the jury a credible, professional performance statement ("bias −0.1 mm, limits of agreement ±0.6 mm, 90% of lenses within 1 mm"), and it tells the team whether to spend the remaining hours on accuracy or elsewhere.

## 4. Implementation plan

### 4.1 Files

```
work/strat18/
  protocol.md          # randomised order of measurements, roles, phones
  data/measurements.csv  # lens, operator, phone, rep, A, B, perimeter, timestamp (no personal data)
  data/calliper.csv
  analysis.ipynb       # Bland–Altman, gauge R&R, predicted score
  report_18.md         # one-page summary for the README and a slide
```

### 4.2 Analysis details

- Bland–Altman: difference (system − reference) vs mean; bias; limits bias ± 1.96·SD; check for proportional bias (regress difference on mean).
- Gauge R&R: random-effects ANOVA (lens, operator, phone, residual) → repeatability (residual SD), reproducibility (operator + phone SD), and % of total variation.
- Predicted score: draw 2 lenses at random from the 10, average their |error| on A and B, map to points; repeat 10,000 times → distribution of expected points.
- Compare with the calliper's own repeatability (if the system's error is near the calliper's, say so: the remaining error is partly in the reference).

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Completeness | all planned measurements collected (or gaps documented) |
| T2 | Reproducible analysis | `analysis.ipynb` runs top to bottom from the CSVs |
| T3 | Headline | bias, limits of agreement, gauge R&R %, predicted score distribution reported for A and B |
| T4 | Decision | if the predicted median score < 25 points, list the dominant error component and the strategy to fix it (e.g. parallax → 13, orientation → 8) |

## 6. Risks

Time to collect data; reduce to 6 lenses × 2 operators × 1 phone × 3 reps if needed, and say so.

## 7. Combines with

Strategy 8 (bias calibration uses these data with care: do not tune and evaluate on the same measurements; split lenses), 2, 11, 13 (improvements to verify), 10 (results page in the app's README).

## 8. Results log

| Date | Who | Lenses | Bias A / B | LoA A / B | Gauge R&R % | Predicted score (median) |
|---|---|---|---|---|---|---|
| | | | | | | |
