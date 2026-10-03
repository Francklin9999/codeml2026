# OptiFrame · Strategy 31: Contour topology and hole policy

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 3 classical segmenter; strategy 9 frame offsets |
| **Work folder** | `optiframe-participants/work/strat31/` |

## 1. Context and evidence

The classical segmenter expects one complete, sufficiently large, mostly convex rim; severe holes and partial visibility are unvalidated. The frame generator rejects self-intersections and vanished offsets. This idea formalizes contour topology and handling of holes/islands so a valid-looking polygon is not silently built from ambiguous segmentation.

Evidence: [metrology report](work/strat2/report.md) lists contour limitations; [STL audit](work/strat9/report.md) records offset rejection behavior.

## 2. Idea and distinction

Add topology diagnostics for disconnected components, enclosed holes, self-touching boundaries, winding direction, and nesting depth. Define supported cases and explicit rejection messages. For accepted contours, preserve holes as evidence but never infer that an inner component is a second lens boundary without a specified rule. This is input contract validation, not another segmenter or statistical shape prior.

## 3. Rubric relevance

Supports robustness in measurement and protects downstream offsets from invalid outlines.

## 4. Implementation steps

Add `work/strat31/topology.py` and synthetic shapes including notches, holes, and two components. Attach diagnostics to pipeline JSON and test that invalid cases stop before measurement/STL generation.

## 5. Proposed experiment

Use 40 generated contours across four topology classes, baseline current acceptance/rejection behavior. Adopt if all unsupported classes are rejected with a reason and supported simple contours retain A/B within 0.05 mm of baseline; kill if the policy rejects more than 5% of valid controls. Thresholds proposed, not measured.

## 6. Risks

Real lenses may contain unusual cutouts or occlusion. Maintain an explicit “unsupported” path, not a claim that all lenses are convex.

## 7. Combinations

Complements strategies 3, 5, 6, 9, 14, 21, and 26.

## 8. Results log

NOT RUN. Current reports do not include a topology class matrix.
