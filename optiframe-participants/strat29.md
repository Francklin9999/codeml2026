# OptiFrame · Strategy 29: Lens-seat clearance tolerance sweep

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 3 h |
| **Depends on** | strategy 9 frame generator |
| **Work folder** | `optiframe-participants/work/strat29/` |

## 1. Context and evidence

The Python frame prototype passes mesh validity gates on simulated contours. Physical groove fit and print tests are NOT RUN. Strategy 9 proposes a nominal 0.1–0.3 mm clearance and a print test; this proposal isolates tolerance sensitivity across plausible printer and lens measurement errors, rather than implementing frame geometry or claiming fit.

Evidence: [STL audit](work/strat9/report.md) says physical groove fit and print tests are NOT RUN.

## 2. Idea and distinction

Sweep seat clearance and lens-outline perturbations independently, then calculate insertion interference, play, and minimum rim wall geometry in the digital model. Produce a sensitivity surface that shows which combination of measurement bias and printer scale error makes the design infeasible. Keep hypothetical material deformation out of the rigid model unless separately measured.

## 3. Rubric relevance

Helps select a testable print configuration and prevents an arbitrary clearance value from being treated as proven.

## 4. Implementation steps

Add `work/strat29/clearance_sweep.py`, fixed contour fixtures, and CSV/plot outputs. Include scale perturbation from strategy 22 as an input parameter and label elastic snap behavior as unknown.

## 5. Proposed experiment

Sweep 0.05–0.50 mm seat clearance in 0.05 mm steps against ±0.5 mm contour offset on six synthetic shapes. Baseline: default 0.2 mm. Adopt a candidate only if all meshes remain valid and nominal collision/play metrics pass specified geometric bounds; keep physical fit marked unverified until a real lens and print are tested. Proposed thresholds: predicted radial gap 0.1–0.3 mm nominal, no negative gap at ±0.2 mm error.

## 6. Risks

Rigid geometry cannot predict plastic flex, lens bevel, printer shrinkage, or breakage. No fit recommendation follows without printing.

## 7. Combinations

Pairs with strategies 9, 22, 28, and 30.

## 8. Results log

NOT RUN. No physical clearance or printed fit results exist.
