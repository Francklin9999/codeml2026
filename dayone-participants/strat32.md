# DayOne · Strategy 32: Schema migration and backward-compatibility gate

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Depends on** | strategy 1 provisional schema |
| **Work folder** | `dayone-participants/work/strat32/` |

## 1. Context and evidence

The DayOne report describes a provisional schema and evaluator with tests, but says the field inventory is not yet an enforced ontology and no GT pages exist (`work/shared/report.md`). As fields are added or normalized, stored records and evaluator inputs can silently become incompatible. Strategy 27 tracks field lineage; this idea specifically gates schema version changes and migration behavior.

Evidence: [DayOne evaluation audit](work/shared/report.md) calls the schema provisional.

## 2. Idea and distinction

Assign explicit schema versions and write declarative migrations between versions. A migration must preserve original status, source evidence references, and unknown fields, and produce a before/after summary. Include a compatibility matrix for current reader, evaluator, and export format. Reject lossy migrations unless an explicit reviewed mapping is supplied.

## 3. Rubric relevance

Supports reliable offline records and credible longitudinal review by preventing updates from changing old field meaning invisibly.

## 4. Implementation steps

Implement `work/strat32/migrate.py`, JSON Schema snapshots, migration fixtures, and a no-write dry-run mode. Keep transformations deterministic and reversible where possible. Avoid introducing clinical interpretation in migrations.

## 5. Proposed experiment

Create 30 synthetic records spanning three draft schema versions with renamed, optional, and unknown fields. Baseline: current schema parse only. Adopt if round-trip migration preserves all source text, status and evidence references, and every lossy operation is reported; kill if any unrecognized field is silently discarded. Proposed acceptance criteria, not measured.

## 6. Risks

No reviewed ontology exists yet, so versions should remain explicitly provisional. Do not migrate real records until reviewed fixtures exist.

## 7. Combinations

Use with strategies 1, 8, 13, 21, 27, and 31.

## 8. Results log

NOT RUN. Schema versioning and migration fixtures are proposals only.
