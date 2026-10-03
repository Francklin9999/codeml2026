# DayOne · Strategy 24: Field-aware crop boundary diagnostics

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Depends on** | strategy 2 registration; reviewed zones from strategy 1 |
| **Work folder** | `dayone-participants/work/strat24/` |

## 1. Context and evidence

Strategy 2 already registers a page and extracts per-cell crops, while strategy 4 studies capture degradation. The current report (`work/shared/report.md`) confirms there are no reviewed zones or ground truth yet, so neither field boundary failures nor downstream OCR error causes have been measured. This proposal addresses crop containment and clipping diagnostics, not another page recognizer or general image-quality gate.

Evidence: [DayOne evaluation audit](work/shared/report.md) (no reviewed zones or OCR evaluation).

## 2. Idea and distinction

For each template field, calculate whether printed labels, handwriting strokes, neighboring separators, or table borders cross the crop boundary. When evidence lies near an edge, expand the contextual crop or mark the crop “zone uncertain” before recognition. Preserve a tight crop for field-specific reading and a wider context crop for human review. Estimate a boundary-risk score using pixel ink density at margins and template-coordinate drift.

## 3. Rubric relevance

Protects field assignment accuracy and gives a concrete reason to request review or recapture instead of presenting a clipped reading as certain.

## 4. Implementation steps

Implement `work/strat24/crop_audit.py` and an overlay report under `work/strat24/`. For each zone, save only opaque field identifiers, tight/context crop coordinates, edge-ink score, and registration residual. Add crop expansion limits and a review flag to strategy 2's output contract.

## 5. Proposed experiment

On 80 fields from 16 pages, inject zone shifts of 0, 2, 4, and 8 pixels into synthetic copies; compare boundary flags with human judgments and field transcription. Baseline: fixed crop only. Adopt if ≥90% of visibly clipped crops are flagged and false flags stay below 10% on unshifted examples; kill if useful expansion leaks neighboring fields in more than 5%. Proposed thresholds, not measured.

## 6. Risks

Pixel thresholds can confuse printed rules with handwriting, and small crops may contain no contextual margin. Human confirmation remains the ground truth.

## 7. Combinations

Use with strategies 2, 4, 6, 9, and 22; strategy 21 can retain crop provenance.

## 8. Results log

NOT RUN. No zone-boundary audit performed.
