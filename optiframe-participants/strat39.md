# OptiFrame · Strategy 39: STL slicing orientation and support-volume preview

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P3 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 9 STL prototype |
| **Work folder** | `optiframe-participants/work/strat39/` |

## 1. Context and evidence

Strategy 9's mesh passes five topology gates, but slicer acceptance, support use, printing, and lens fit are NOT RUN. Existing strategy 17 expands to temples and hinges; this idea is limited to the required front and predicts how its current geometry sits on a build plate. It does not claim material strength or successful printing.

Evidence: [STL audit](work/strat9/report.md) records topology only; slicer and print validation are NOT RUN.

## 2. Idea and distinction

Evaluate candidate rigid rotations of the generated frame front and compute projected footprint, overhang area, bridge orientation, and theoretical support volume against a simple layer-wise geometric model. Recommend an orientation with the smallest unsupported volume while keeping the lens-seat plane flat where feasible. Export the chosen transform as a sidecar, not a modified mesh unless requested.

## 3. Rubric relevance

Addresses the printable-frame requirement and helps prepare a clear slicer demonstration.

## 4. Implementation steps

Add `work/strat39/orientation.py` and compare it with a real slicer's estimates when available. Test arbitrary and axis-aligned rotation, preserve units, and validate the transformed STL topology again.

## 5. Proposed experiment

Run 10 existing synthetic-derived frame meshes over 24 candidate orientations; baseline flat front orientation from strategy 9. Adopt an orientation only if predicted support volume is lower by ≥20% and the lens-seat plane remains within 0.2 mm of the build plane; compare prediction against slicer output within ±15% on five models before presenting as useful. Thresholds proposed, not measured.

## 6. Risks

Support algorithms vary by slicer and material; geometric prediction cannot establish printability or lens fit.

## 7. Combinations

Pairs with strategies 9, 17, 28, and 34.

## 8. Results log

NOT RUN. No slicer or print validation has been performed.
