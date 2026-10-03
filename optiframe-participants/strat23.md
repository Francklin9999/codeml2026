# OptiFrame · Strategy 23: Lens placement sensitivity map

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Depends on** | strategy 2 synthetic generator and pipeline |
| **Work folder** | `optiframe-participants/work/strat23/` |

## 1. Context and evidence

The synthetic generator uses explicit metric polygons, and the report notes board-axis measurements require correct lens placement; canonical orientation remains incomplete. The fixed suite reports good zero-height synthetic errors but does not test placement shifts or rotation. Strategy 8 defines axes and orientation, while strategy 11 plans mechanical stops. This proposal measures tolerance to translation/rotation, rather than adding another orientation estimator or fixture.

Evidence: [OptiFrame metrology report](work/strat2/report.md) reports synthetic results and incomplete orientation handling.

## 2. Idea and distinction

Sweep lens translation, rotation, and slight lift relative to the board window and map resulting dimension errors and segmentation failures. Derive an allowed placement envelope and show a simple placement overlay. Test whether cropping/window limits or polygon clipping alter measurements under otherwise unchanged conditions.

## 3. Rubric relevance

Supports robustness and provides evidence-based setup guidance before a potentially invalid measurement.

## 4. Implementation steps

Add `work/strat23/placement_sweep.py` and outputs to `work/strat23/`. Parameterize scene generation independently of label generation, include asymmetric synthetic outlines, and report error by placement perturbation. Do not update production limits until physical captures confirm them.

## 5. Proposed experiment

Run 15 existing synthetic shapes at ±0, 2, 5, and 10 mm translation and ±0, 3, 7 degrees rotation, baseline exact centered placement. Adopt an on-screen warning boundary where 95% of tests remain under 0.5 mm A/B error; kill the warning rule if false alarms exceed 15% in nominal placements. Proposed thresholds, not measurements.

## 6. Risks

Synthetic stability may overstate real operator consistency; no claim about humans until tested.

## 7. Combinations

Pairs with strategies 2, 8, 11, 16, and 21.

## 8. Results log

NOT RUN. Existing results use controlled synthetic placement.
