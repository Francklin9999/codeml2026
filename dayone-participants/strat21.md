# DayOne · Strategy 21: Patient-grouped holdout and duplicate leakage audit

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 1 schema; existing `work/shared/eval.py` |
| **Work folder** | `dayone-participants/work/strat21/` |

## 1. Context and evidence

The source inventory lists 80 specimen pages from ten fictional patients and 44 byte-identical duplicate PNGs. The audit (`work/shared/report.md`) confirms no reviewed ground truth. Strategy 4 proposes degraded synthetic data, but no split manifest is reported. Page-level random splitting could put the same patient or duplicate renders on both sides and inflate apparent generalization.

Evidence: [DayOne evaluation audit](work/shared/report.md) (no reviewed ground truth or phone-OCR results).

## 2. Idea and distinction

Build a split manifest grouped by fictional patient and assign each patient's pages and duplicate images to one partition. Audit exact hashes and perceptual near-duplicates across partitions; report counts by page type without exporting identifiers. Freeze the manifest before tuning. Unlike strategy 4's data generation and strategy 31's evidence display, this prevents leakage between train/dev/holdout sets.

## 3. Rubric relevance

Supports credible extraction accuracy claims by preventing the same fictional patient or duplicate page from appearing in both tuning and evaluation partitions.

## 4. Implementation steps

Add `split_manifest.py`, `duplicate_audit.py`, and a report under `work/strat21/`. Use opaque patient-group IDs and file hashes; do not place names, phone numbers, or CIN values in the manifest. Include an explicit no-patient-label mode for datasets whose grouping is unknown; those samples remain in a separate provisional pool rather than being randomly distributed.

## 5. Proposed experiment

Partition all 80 specimen pages using opaque patient groups and run exact plus perceptual duplicate checks across partitions. Baseline: naive page-level random split. Adopt if all 44 known duplicate PNGs remain with their source page and no patient group crosses splits; use a proposed near-duplicate threshold calibrated on 20 hand-inspected pairs, with zero cross-split matches required. These are proposed gates; no split exists or metric has been measured.

## 6. Risks

Patient-group IDs must be assigned correctly before splitting; unknown group membership can still leak. Synthetic patient splits do not prove generalization to real facilities or handwriting.

## 7. Combinations

Pairs with strategies 1, 4, 5, 22, and 38; it gates future model-training and evaluation runs.

## 8. Results log

NOT RUN. No patient-group split manifest or leakage audit exists.
