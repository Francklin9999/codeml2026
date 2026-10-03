# DayOne · Strategy 22: Reviewer disagreement and adjudication queue

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 1; strategy 21 optional |
| **Work folder** | `dayone-participants/work/strat22/` |

## 1. Context and evidence

`work/shared/report.md` records that the evaluator exists and passes ten tests, while reviewed zones and ground truth do not. The synthetic specimen has ten fictional patients and 80 pages; five phone photos have no labels. A single annotator could produce consistent data that is still wrong, especially for dense tables and ambiguous marks. Existing strategy 1 describes a visual spot check, but not independent annotation or adjudication.

Evidence: [DayOne evaluation audit](work/shared/report.md) (schema and evaluator tests only; no reviewed labels).

## 2. Idea and distinction

Build a blind dual-review workflow for a stratified subset: each reviewer independently labels the same field crops, then the system surfaces disagreements without revealing the other answer until submission. An adjudicator resolves differences and records a reason code. Track agreement by field type and page type, and separate transcription ambiguity from schema ambiguity. This is a quality-control process for labels, rather than strategy 6's model confidence calibration or strategy 1's coordinate assignment.

## 3. Rubric relevance

Reliable ground truth is a prerequisite for credible extraction and uncertainty scores; transparent adjudication also gives reviewers a safe way to mark illegible entries rather than guess.

## 4. Implementation steps

Create `work/strat22/queue.py`, `review.html`, and `adjudicate.py`. Generate de-identified crops with opaque IDs, capture raw transcription, status, reviewer ID, and reason code. Calculate exact agreement for categorical fields, normalized agreement for dates and values, and adjudication rate. Keep original images read-only.

## 5. Proposed experiment

Blind-label 160 fields sampled across eight page types and visible mark classes; baseline is one-person annotation. Adopt if agreement reaches ≥95% on legible fields and adjudication correctly resolves ≥90% of disagreements on a separate 30-item audit; otherwise revise instructions and repeat before expanding. These proposed thresholds are not measured evidence.

## 6. Risks

Agreement does not imply truth, and small samples cannot characterize Arabic or real phone capture. Never force consensus on unreadable writing; preserve an unresolved state.

## 7. Combinations

Builds on strategy 1 and can feed the provenance ledger in 21, then support strategies 4 and 6.

## 8. Results log

NOT RUN. No annotation sessions or agreement statistics collected.
