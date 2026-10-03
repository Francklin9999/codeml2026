# DayOne · Strategy 40: Challenge-brief traceability matrix

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P3 |
| **Effort** | 1–2 h |
| **Depends on** | current challenge brief and strategy set |
| **Work folder** | `dayone-participants/work/strat40/` |

## 1. Context and evidence

The repository contains an analysis, twenty initial proposals, a continuation record, and a tested schema/evaluator; several planned capabilities remain unimplemented. The DayOne report explicitly says there are no reviewed zones, gold pages, or phone OCR labels (`work/shared/report.md`). Strategy 1 tracks its own tests, while this proposal links every claim and planned work item to an observable brief requirement.

Evidence: [DayOne evaluation audit](work/shared/report.md) distinguishes tested evaluator code from missing GT/OCR.

## 2. Idea and distinction

Build a compact traceability matrix with requirement, evidence artifact, status (measured, synthetic, proposed, not run), owner, and next verification step. Add an automated check that every demo claim has a linked source artifact or is labeled a hypothesis. Unlike a presentation plan, it is an evidence index with explicit limits.

## 3. Rubric relevance

Improves clarity and honesty during judging; prevents synthetic or untested performance from being presented as field evidence.

## 4. Implementation steps

Create `work/strat40/traceability.md` and a lightweight link checker. Reference challenge files and reports by relative path. Link parent `RESULTS_OVERVIEW.md` after integration; until then, preserve local report links. Do not invent scores.

## 5. Proposed experiment

Audit 20 challenge requirements and 10 demo statements against repository evidence. Baseline: current README and slides. Adopt if every statement is traceable and all untested claims carry visible labels; kill if the matrix adds no evidence beyond existing reports. Proposed acceptance criteria, not measured.

## 6. Risks

A matrix can become stale. Keep it short and regenerate status from reports where practical.

## 7. Combinations

Pairs with strategies 1, 21, 26, 27, and 38; supports final reporting across all DayOne work.

## 8. Results log

NOT RUN. No traceability audit has been performed.
