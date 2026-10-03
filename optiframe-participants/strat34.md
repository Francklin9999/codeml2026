# OptiFrame · Strategy 34: Nasal bridge feasibility interval for asymmetric pairs

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Depends on** | strategy 9 STL generator |
| **Work folder** | `optiframe-participants/work/strat34/` |

## 1. Context and evidence

Strategy 9 generates a bridge between two contours and supports two different lens shapes; the smoke STL passed mesh gates, but physical fit is untested. Its plan uses a default bridge width and places rims from nasal extents. This proposal computes whether any bridge range is geometrically feasible for an asymmetric pair before mesh construction; it does not add another export manifest or hinge feature.

Evidence: [STL audit](work/strat9/report.md) confirms tested topology but synthetic-derived input and no physical fit evidence.

## 2. Idea and distinction

For each pair of canonical contours, derive the minimum bridge span that avoids aperture/rim collision and the maximum span that retains a connected front within a chosen global width. Report a feasible interval plus contour-specific collision locations. If the interval is empty, explain that this pair cannot use the current bridge topology instead of silently forcing a default.

## 3. Rubric relevance

Supports the generated-frame rubric by detecting incompatible asymmetric lens pairs before writing an STL.

## 4. Implementation steps

Add `work/strat34/bridge_feasibility.py` and a plot showing two nasal contours, collision constraints, and the feasible bridge interval. Reuse existing offset/union routines but calculate feasibility before creating the STL. Use millimeters and preserve asymmetric outlines.

## 5. Proposed experiment

Test 12 synthetic left/right contour pairs, including four asymmetric holdouts, over bridge spans from 10 to 30 mm. Baseline: strategy-9 default bridge of 18 mm. Adopt if feasible/infeasible classification matches exact polygon intersection across every holdout and accepted endpoints have zero collisions. Proposed thresholds, not measured.

## 6. Risks

The model checks only 2D aperture and connectivity; it does not assess nose comfort, material strength, or physical assembly.

## 7. Combinations

Pairs with strategies 8, 9, 17, 21, and 28.

## 8. Results log

NOT RUN. Existing generator uses a default bridge; no feasible-interval calculation exists.
