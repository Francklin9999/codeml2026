# DayOne · Strategy 30: Handwriting-preserving image transform audit

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Depends on** | strategy 2 registration; strategy 4 degradation benchmark |
| **Work folder** | `dayone-participants/work/strat30/` |

## 1. Context and evidence

Strategies 2 and 4 plan registration and degradation testing, but the current report lists no phone-photo labels and no OCR evaluation (`work/shared/report.md`). Geometric correction can make a page visually neat while interpolating away thin strokes. This idea measures the image-processing pipeline's effect on local stroke evidence, not a new OCR model or image-quality retake classifier.

Evidence: [DayOne evaluation audit](work/shared/report.md) reports no phone-photo OCR labels or OCR evaluation.

## 2. Idea and distinction

Create a transformation audit that compares original and rectified images in matched field crops. Quantify stroke-width preservation, local contrast, edge continuity, and crop alignment across warp/interpolation options. Overlay differences for human review and attach the selected transform parameters to each extraction run. Do not sharpen or “repair” handwriting as if it were original evidence.

## 3. Rubric relevance

Protects extraction quality and evidence transparency by identifying when preprocessing itself damages writing.

## 4. Implementation steps

Implement `work/strat30/transform_audit.py` under the DayOne work tree. Use synthetic line targets plus hand-labeled, locally stored crops where permitted. Compare nearest, bilinear, and area resampling, avoiding any upload or external processing. Preserve originals read-only.

## 5. Proposed experiment

Use 60 synthetic strokes at three widths and 40 manually inspected field crops; baseline is the current rectification transform. Adopt a transform if median stroke-width error remains ≤0.2 px, at least 95% of thin synthetic strokes remain connected, and no reviewer sees a material lost stroke in the 40 crops. Kill if no transform meets all three. Proposed, not measured.

## 6. Risks

Synthetic marks cannot represent all real ink and paper. The five real photos have no labels and must not be treated as ground truth.

## 7. Combinations

Complements strategies 2, 4, 11, 21, and 24.

## 8. Results log

NOT RUN. No preprocessing comparison completed.
