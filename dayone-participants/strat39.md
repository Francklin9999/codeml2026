# DayOne · Strategy 39: Manual fallback parity contract

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 9 review; strategy 15 offline client |
| **Work folder** | `dayone-participants/work/strat39/` |

## 1. Context and evidence

The challenge requires a usable workflow when automatic extraction is uncertain or unavailable. Strategy 9 proposes chat review, strategy 15 a PWA, and strategy 20 an edge box; no extraction or phone workflow is currently validated (`work/shared/report.md`). This proposal defines parity between manual entry and assisted entry so offline fallback does not silently omit fields or statuses.

Evidence: [DayOne evaluation audit](work/shared/report.md) reports no OCR implementation; [CONTINUATION.md](../CONTINUATION.md) records remaining workflow plans.

## 2. Idea and distinction

Create a contract that every schema field can be entered manually with value, status, optional confidence/source, and evidence note, regardless of OCR availability. Compare records produced by manual entry and by correcting a prefilled record; both must serialize identically under the same values. This is a completeness and serialization test, not a new chat or offline architecture.

## 3. Rubric relevance

Supports resilience and human control when the model fails, while ensuring manual completion remains scorable by the same evaluator.

## 4. Implementation steps

Add `work/strat39/manual_contract.py`, schema-driven form rendering, and round-trip tests. Include keyboard-only operation and explicit blank/unreadable choices. Use synthetic records only, with no external data submission.

## 5. Proposed experiment

Populate 40 synthetic fields once through manual mode and once by editing prefilled values. Baseline: manual form built independently of schema. Adopt if normalized serialization and status match 100% and no schema fields are omitted; kill if UI requires OCR-only fields. Proposed thresholds, not measured.

## 6. Risks

A complete form can be burdensome and doesn't prove real-world usability. Keep low-confidence review prioritized, but allow full manual entry.

## 7. Combinations

Pairs with strategies 1, 8, 9, 15, 23, 28, and 35.

## 8. Results log

NOT RUN. No manual fallback implementation exists.
