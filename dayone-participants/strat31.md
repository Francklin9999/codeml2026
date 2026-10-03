# DayOne · Strategy 31: Per-field evidence packet export

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 9 review flow; strategy 21 provenance |
| **Work folder** | `dayone-participants/work/strat31/` |

## 1. Context and evidence

The evaluator measures field and status accuracy, while strategy 9 proposes showing an evidence crop during conversational review. No reviewed GT or phone-OCR results exist (`work/shared/report.md`). This idea packages a prediction with the minimal evidence needed for a human to verify it, rather than proposing a new recognizer or another review interface.

Evidence: [DayOne evaluation audit](work/shared/report.md) reports no GT pages or phone OCR implementation.

## 2. Idea and distinction

Define a portable evidence packet containing a tight crop, a context crop, proposed value/status, source page type, bounding box, transform version, and a one-line explanation of normalization. Generate a redacted preview and validate the packet against an allowlist before display or export. Missing evidence is itself a review blocker. This is a presentation and serialization contract, distinct from confidence calibration or identifier masking.

## 3. Rubric relevance

Makes uncertainty actionable and lets a reviewer verify the relationship between extracted values and source marks.

## 4. Implementation steps

Add `work/strat31/packet.py`, JSON schema, and a static viewer. Use opaque page references and ensure no image leaves local storage. Support rotated/rectified overlays and “evidence unavailable” states; do not store free-text explanations from a model without review.

## 5. Proposed experiment

Prepare 80 synthetic packets: 60 valid and 20 malformed (wrong crop, missing bbox, unsupported status, forbidden key). Baseline: bare value/status display. Adopt if all malformed packets are blocked, all valid overlays align within 2 px, and reviewers find the source in ≤10 seconds in ≥90% of 30 timed tasks. Proposed thresholds, not measured.

## 6. Risks

Cropping can accidentally reveal adjacent identifiers. Redaction should be tested at the image boundary and original pixels remain protected.

## 7. Combinations

Pairs with strategies 9, 10, 21, 24, 26, and 27.

## 8. Results log

NOT RUN. Packet schema and viewer do not exist.
