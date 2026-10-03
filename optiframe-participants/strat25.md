# OptiFrame · Strategy 25: Transparent-board flatness and local warp map

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 1 board; strategy 2 rectification |
| **Work folder** | `optiframe-participants/work/strat25/` |

## 1. Context and evidence

The rig places a transparent ChArUco board on a laptop screen; the physical rig has not been tested. A thin sheet can bow or wrinkle, making a single planar homography inconsistent across the window. Strategy 2 fits a global homography and strategy 13 addresses lens height above the board. This tests deformation of the reference sheet itself and estimates a spatial warp field, independent of printer scale and lens parallax.

Evidence: [CONTINUATION.md](../CONTINUATION.md) records physical rig tests as NOT RUN; [metrology report](work/strat2/report.md) describes the planar pipeline.

## 2. Idea and distinction

Photograph a board on a flat rigid reference and then on the intended screen, using the same pose and multiple board positions. Compare locally reconstructed marker-grid spacing and residual vectors to a rigid-plane fit. Infer a smooth deformation map only if it repeats across captures; otherwise issue a board-not-flat warning. Do not silently warp lens contours based on one fit.

## 3. Rubric relevance

Establishes a traceable metric scale before judging lens measurements or frame dimensions.

## 4. Implementation steps

Add `work/strat25/flatness.py`, a target board specification, and displacement-vector plots. Record board ID, support surface, and repeated capture ID. Compare marker-local scale changes and homography residual fields; keep metric scale fixed to isolate flatness from printer scaling.

## 5. Proposed experiment

Take 10 repeats on rigid flat support and 10 on intended screen support, then move the board to four screen locations; baseline is one global homography. Adopt a flatness warning if local displacement exceeds 0.2 mm and repeats agree within 0.05 mm. Apply no correction unless held-out marker points improve spatial error by at least 30%; reject unstable warp estimates. Proposed thresholds; no data measured.

## 6. Risks

Marker interpolation and lens-edge height can mimic warp. Repeat and support-surface controls are required to separate effects; screen support may change with pressure or temperature.

## 7. Combinations

Pairs with strategies 1, 2, 11, 13, and 33.

## 8. Results log

NOT RUN. No board flatness or spatial deformation data exist.
