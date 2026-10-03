# OptiFrame · Strategy 35: Morphological gap-closure sensitivity budget

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Depends on** | strategy 2 rectification; strategy 3 detector |
| **Work folder** | `optiframe-participants/work/strat35/` |

## 1. Context and evidence

Strategy 3 closes the detected dark rim ring into a contour, while strategy 14 fits shape priors to incomplete edge evidence. Synthetic evaluation reports accepted/rejected cases but no study of when the morphology operation bridges a real-looking gap and changes the dimension. This proposal quantifies the specific sensitivity of contour closure to structuring-element size, rather than learning a shape prior or measuring global exposure.

Evidence: [metrology report](work/strat2/report.md) documents simple segmenter limitations; current output is synthetic.

## 2. Idea and distinction

Run the same thresholded rim mask through a small sweep of morphological closing radii. Track which gaps close, when component count changes, and the resulting A/B/perimeter shifts. Flag a measurement as closure-sensitive when a small kernel change causes a large dimension jump; preserve the pre-closure mask and never pretend interpolated pixels were observed edges.

## 3. Rubric relevance

Makes measurement failure explainable and avoids false precision when a segmenter has filled in an unseen edge.

## 4. Implementation steps

Add `work/strat35/closure_sweep.py` and synthetic annuli with known radial gaps and notches. Output kernel range, topology transitions, and dimension sensitivity in a diagnostic report. Keep the current default result unchanged until the warning is evaluated.

## 5. Proposed experiment

Use 12 synthetic shapes with controlled 0–3 mm gaps and 3–5 px closing kernels; hold out four asymmetric contours before tuning. Baseline: current fixed morphology settings. Adopt a sensitivity warning if it detects ≥90% of cases where kernel choice changes A/B by >0.5 mm, with <10% false warnings on stable cases; kill if no stable threshold exists. Proposed values, not measured.

## 6. Risks

Synthetic gaps do not fully model reflections or actual rim breaks. The warning measures algorithmic instability, not whether a physical edge exists.

## 7. Combinations

Complements strategies 3, 14, 21, 24, and 31.

## 8. Results log

NOT RUN. Existing reports do not sweep morphology parameters or quantify dimension sensitivity.
