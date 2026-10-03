# OptiFrame · Strategy 24: Exposure and saturation quality diagnostics

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 1 rig; strategy 3 segmenter |
| **Work folder** | `optiframe-participants/work/strat24/` |

## 1. Context and evidence

Current segmentation was tested on synthetic images; real lighting, lens materials, and phone auto-exposure have not been validated. Strategies 1 and 3 establish backlit capture and a classical rim baseline. Strategy 7 covers repeated-image fusion. This proposal monitors exposure clipping and local contrast in a single capture, without changing the segmentation algorithm or requesting extra shots.

Evidence: [metrology report](work/strat2/report.md) states real-phone lighting and lens behavior are unvalidated.

## 2. Idea and distinction

Measure luminance histogram clipping, color-channel clipping, glare-connected area, and rim-to-background contrast in the board window. Convert these into interpretable capture diagnostics and thresholds tied to synthetic failure tests. Do not normalize away saturated pixels; flag conditions in which edge information has been lost.

## 3. Rubric relevance

Reduces silent failures and makes robustness checks explainable to users.

## 4. Implementation steps

Implement `work/strat24/exposure.py`, overlay, and a small threshold sweep. Expose diagnostic values in measurement JSON and label suggested thresholds as provisional until real-phone capture exists.

## 5. Proposed experiment

Generate 60 controlled images varying exposure and glare over 15 synthetic cases, baseline current accept/reject behavior. Adopt if the diagnostic rejects ≥90% of cases where contour error exceeds 1 mm and falsely rejects <10% of in-tolerance cases; kill if no threshold separates these groups. Proposed numbers, not measured results.

## 6. Risks

Synthetic glare and tone mapping may not resemble real camera processing. Validate on multiple phones before enabling hard blocks.

## 7. Combinations

Complements strategies 1, 3, 6, 7, 10, and 21.

## 8. Results log

NOT RUN. No real-phone exposure samples are reported.
