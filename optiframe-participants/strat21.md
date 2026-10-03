# OptiFrame · Strategy 21: Contour tessellation and STL approximation budget

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 2 contour output; strategy 9 mesh prototype |
| **Work folder** | `optiframe-participants/work/strat21/` |

## 1. Context and evidence

The strategy-2 report records 0.080234 mm combined A/B MAE on twelve synthetic zero-height cases. Strategy 9 offsets/simplifies contours and validates mesh topology, but does not bound dimensional error from polygon simplification, offsetting, triangulation, or STL export. Physical lenses and slicer behavior remain NOT RUN. This isolates numerical representation error, not repeatability or calibration.

Evidence: [OptiFrame metrology results](work/strat2/report.md) and [STL audit](work/strat9/report.md) are synthetic-only.

## 2. Idea and distinction

For each contour stage, compare the original dense polygon against simplified, offset, and reloaded STL section geometry using Hausdorff distance, area, A/B extents, and perimeter drift. Allocate a maximum geometry-error budget across simplification tolerance and output resolution, then reject exports whose accumulated deviation exceeds it. This focuses on approximation mechanics after image measurement, not the camera or measurement error budget in strategy 2.

## 3. Rubric relevance

Explains when a dimension is precise enough to use and when the operator should inspect or recapture.

## 4. Implementation steps

Add `work/strat21/contour_error.py` and fixture report. Compare canonical contours, each transformed polygon, and section samples from reloaded STL. Seed generated outlines, state units, and report each stage's incremental contribution rather than combining them into one unexplained total.

## 5. Proposed experiment

Run 12 shapes with 3 vertex densities and 5 simplification tolerances; hold out 4 asymmetric outlines chosen before tuning. Baseline: strategy-9 current 0.05 mm simplification and default mesh export. Adopt if held-out max Hausdorff deviation ≤0.05 mm and A/B drift ≤0.1 mm while reducing vertex count by ≥30%; reject a tolerance if either geometry bound fails. Proposed thresholds only; no result measured.

## 6. Risks

Hausdorff distance can miss semantic features such as a narrow notch; include adversarial narrow-feature shapes. Passing geometry bounds says nothing about print fit or optical measurement accuracy.

## 7. Combinations

Combines with strategies 2, 9, 28, and 30; can gate mesh export without changing input measurements.

## 8. Results log

NOT RUN. Existing mesh checks do not report approximation error against source contours.
