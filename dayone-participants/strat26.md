# DayOne · Strategy 26: Privacy-safe error analytics

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 1 evaluator; strategy 8 lifecycle optional |
| **Work folder** | `dayone-participants/work/strat26/` |

## 1. Context and evidence

The evaluator report (`work/shared/report.md`) can report field accuracy, status confusion, hallucination, and key-like identifier leaks, but it has no annotated pages and notes that personal data in free text is not detected by key checks. Strategies 10 and 19 handle masking and aggregate analytics. This proposal focuses on a minimized, privacy-reviewed event format for measuring errors without retaining source content.

Evidence: [DayOne evaluation audit](work/shared/report.md) identifies free-text privacy detection as a limitation.

## 2. Idea and distinction

Emit aggregateable events with opaque run/page IDs, field category, error class, confidence bin, and processing version. Exclude raw text, image paths, patient-level identifiers, and free-form model prompts by construction. Add a schema allowlist and test that serialized telemetry cannot carry unknown fields. Unlike strategy 19's epidemiology dashboard, this is internal model-quality telemetry and deliberately contains no clinical values.

## 3. Rubric relevance

Supports privacy, reproducible evaluation, and debugging while avoiding secondary exposure of sensitive source material.

## 4. Implementation steps

Create `work/strat26/events.py`, `event_schema.json`, and red-team tests in `work/strat26/tests/`. Hash run IDs with a per-run salt, aggregate to minimum cell sizes before export, and provide a local-only report by field category and status. Never transmit event data externally.

## 5. Proposed experiment

Generate 500 synthetic events with intentionally injected forbidden keys and values. Baseline: raw evaluator JSON export. Adopt if the allowlist rejects 100% of injected forbidden fields, preserves all approved aggregate counts, and an audit of 100 outputs finds no source strings; kill if useful metrics cannot be recovered without raw values. Proposed thresholds, not measured.

## 6. Risks

Hashing does not anonymize low-entropy personal data; avoid patient-derived identifiers entirely. Small cohorts can expose rare combinations, so suppress small counts.

## 7. Combinations

Complements strategies 6, 8, 10, 19, and 21. It should consume evaluator outputs without changing scoring semantics.

## 8. Results log

NOT RUN. No telemetry is implemented or transmitted.
