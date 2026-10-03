# OptiFrame · Strategy 37: Rectified-image sampling and pixel-phase floor

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 2 rectification and edge refinement |
| **Work folder** | `optiframe-participants/work/strat37/` |

## 1. Context and evidence

The synthetic evaluator rectifies at 20 px/mm and reports good measurements on twelve zero-height cases, including a blurred case with the largest 0.312796 mm error. Strategy 2 uses sub-pixel localization, but the minimum safe image sampling density and sensitivity to contour position within a pixel are not reported. This proposal tests the discretization floor, not the edge detector or camera calibration itself.

Evidence: [metrology report](work/strat2/report.md) specifies 20 px/mm and reports the blurred case as the largest synthetic error.

## 2. Idea and distinction

Render the same analytic shapes at multiple pixel/mm rates and fractional-pixel phases, rectify each at candidate output resolutions, and isolate quantization/interpolation error from segmentation error. Determine when raising output resolution stops improving A/B and perimeter, then select the smallest stable working resolution. Include a 0.25-pixel contour translation sweep to expose phase-dependent bias.

## 3. Rubric relevance

Supports measurable accuracy and runtime efficiency by choosing a resolution based on evidence rather than a fixed convention.

## 4. Implementation steps

Add `work/strat37/sampling_sweep.py` and deterministic analytic contours. Report label-to-output error before and after edge refinement at 5, 10, 15, 20, and 30 px/mm. Keep each render generator version fixed.

## 5. Proposed experiment

Use 12 current shapes, four pixel phases, and five resolutions; hold out four asymmetric shapes before tuning. Baseline: current 20 px/mm pipeline. Adopt the lowest resolution whose held-out A/B max error is within 0.05 mm of the best resolution and whose perimeter drift is under 0.1 mm; otherwise retain current setting. Proposed thresholds, not measured.

## 6. Risks

Raster simulations do not represent phone optics or real lens edges. This only bounds digital resampling error.

## 7. Combinations

Complements strategies 2, 21, 26, and 30; informs memory budgets in 32.

## 8. Results log

NOT RUN. Existing results use one rectification sampling density.
