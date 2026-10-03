# DayOne · Strategy 37: Retention and deletion lifecycle rehearsal

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 3 h |
| **Depends on** | strategy 8 store; strategy 10 privacy controls |
| **Work folder** | `dayone-participants/work/strat37/` |

## 1. Context and evidence

The brief requires privacy and offline-first handling. Strategy 8 proposes an encrypted store and strategy 10 identifier masking/linking, but implementation remains unreported; current DayOne work is limited to schema/evaluator foundations (`work/shared/report.md`). This proposal exercises deletion and retention behavior across primary records, retries, caches, exports, and queued sync items.

Evidence: [DayOne evaluation audit](work/shared/report.md) limits implemented checks to schema/evaluator tests.

## 2. Idea and distinction

Define a retention policy with explicit record lifecycle events and a deletion rehearsal that searches every storage layer for a synthetic record after deletion. Verify deletion tombstones sync safely and that stale retries cannot recreate the item. Unlike strategy 10's identifier detection, this tests data lifecycle completeness, not recognition or redaction.

## 3. Rubric relevance

Provides demonstrable privacy behavior and protects user trust in offline workflows.

## 4. Implementation steps

Add `work/strat37/retention.py`, a storage inventory, test fixtures, and a deletion report. Use only synthetic records. Include cache, logs, thumbnail, local database, export, and outbox; avoid claiming secure erasure from flash storage beyond what platform APIs guarantee.

## 5. Proposed experiment

Create 25 synthetic records across all known storage locations, delete them online and offline, restart, and retry sync. Baseline: current deletion behavior. Adopt if zero records reappear and all indexed copies are removed or inaccessible after the policy action; kill if offline tombstones can be lost. Proposed acceptance criteria, not measured.

## 6. Risks

Logical deletion does not prove physical erasure. Document platform limitations and keep all tests fictional.

## 7. Combinations

Pairs with strategies 8, 10, 15, 20, 26, and 29.

## 8. Results log

NOT RUN. No lifecycle store or deletion audit is included in current results.
