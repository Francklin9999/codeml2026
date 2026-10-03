# DayOne · Strategy 35: Status transition policy audit

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 1 schema and evaluator |
| **Work folder** | `dayone-participants/work/strat35/` |

## 1. Context and evidence

The six status values are central to the brief and encoded in the provisional schema, but no reviewed GT pages exist (`work/shared/report.md`). The evaluator already reports status accuracy and confusion. Strategy 6 plans confidence-to-status classification; this proposal clarifies legal status transitions during human review, including when a system proposal becomes confirmed, corrected, or deferred.

Evidence: [DayOne evaluation audit](work/shared/report.md) notes the status evaluator exists but no gold pages.

## 2. Idea and distinction

Specify a finite transition table with event source and required actor: extraction proposes a status, reviewer confirms or edits, and unresolved items remain pending. Preserve prior state in an audit trail. Forbid automated changes from uncertain to confirmed based solely on cross-field logic. The workflow is policy and state-transition behavior, not probabilistic classification or dialogue orchestration.

## 3. Rubric relevance

Makes uncertainty handling explicit and prevents an interface from silently converting ambiguous values into accepted records.

## 4. Implementation steps

Add `work/strat35/status_machine.py`, transition table, and fixture tests. Link transitions to the existing status enum while leaving clinical meaning subject to expert review. Display previous and proposed state for any human change.

## 5. Proposed experiment

Enumerate every status pair and 20 scripted user actions. Baseline: unconstrained status edits. Adopt if every valid transition is accepted, every forbidden transition is blocked, and no action loses the previous value/status; kill if rules cannot be justified from the project brief. Proposed threshold, not measured.

## 6. Risks

Over-constraining reviewer actions may block correction. Allow an explicit override with reason, never fabricate ground truth.

## 7. Combinations

Complements strategies 1, 6, 9, 23, 27, and 32.

## 8. Results log

NOT RUN. No transition policy has been reviewed or implemented.
