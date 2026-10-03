# DayOne · Strategy 27: Field-level data lineage and versioned transformations

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Depends on** | strategy 1 schema; strategy 21 optional |
| **Work folder** | `dayone-participants/work/strat27/` |

## 1. Context and evidence

DayOne's schema/evaluator is provisional and tested, but no reviewed labels exist (`work/shared/report.md`). Strategies 1 and 21 focus on building labels and tracing source evidence. This proposal versions the sequence of transformations from observed text to normalized output, so a correction or parser update can be explained and reproduced without changing the source data.

Evidence: [DayOne evaluation audit](work/shared/report.md) covers evaluator checks but no reviewed labels.

## 2. Idea and distinction

Store an append-only, de-identified lineage record for each field: source artifact hash, crop/template version, raw candidate reference, normalization rule ID, human correction event, and final status. Raw values remain in the protected local record, not in shared logs. A replay tool recomputes normalized output from a permitted local fixture and highlights which transformation changed. This is data lineage, not cross-visit reconciliation or online learning.

## 3. Rubric relevance

Improves auditability, correction review, and reproducibility; supports clear evidence when explaining a changed output.

## 4. Implementation steps

Implement `work/strat27/lineage.py` with typed event objects and a deterministic replay command. Version normalization rules and schema separately. Keep source hashes and opaque field keys only in exportable traces; make local replay require explicit access to the original artifact.

## 5. Proposed experiment

Use 50 synthetic fields with known parse-normalize-correct histories. Baseline: final value only. Adopt if replay exactly reproduces all final values and status transitions, and a rule-version change identifies every affected field; kill if logs reveal raw identifiers or cannot distinguish human edits from parser changes. Proposed thresholds, not measured.

## 6. Risks

Hashes and timestamps may still be linkable metadata; retention and access need limits. Replay must not overwrite originals.

## 7. Combinations

Pairs with strategies 1, 6, 8, 9, 21, and 26.

## 8. Results log

NOT RUN. No lineage data captured.
