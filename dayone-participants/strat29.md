# DayOne · Strategy 29: Capture-session clock and event ordering audit

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 8 lifecycle; strategy 17 assembler |
| **Work folder** | `dayone-participants/work/strat29/` |

## 1. Context and evidence

The challenge expects a multi-page capture workflow and offline operation; strategy 8 proposes lifecycle states and strategy 17 handles ordering and duplicates. Current DayOne results only establish schema/evaluator tests, not an end-to-end queue (`work/shared/report.md`). This proposal checks causal event ordering and clock anomalies across retries and delayed sync; it does not implement another queue or duplicate detector.

Evidence: [CONTINUATION.md](../CONTINUATION.md) lists offline workflow as planned, with no integrated queue results.

## 2. Idea and distinction

Record monotonic local event sequence numbers alongside wall-clock timestamps for capture, upload, processing, review, and correction. On sync, preserve original event order even if device time changes or messages arrive late. Flag impossible transitions and clock jumps for audit rather than silently sorting by timestamp. Generate a compact session timeline for debugging.

## 3. Rubric relevance

Supports offline reliability, traceability, and understandable review histories. A reviewer can see when each page entered the workflow without exposing its contents.

## 4. Implementation steps

Add `work/strat29/timeline.py` and property-style fixtures using fake IDs. Include sequence counter persistence, retry idempotency key, clock-offset annotation, and transition validator. No external telemetry; export only opaque test timelines.

## 5. Proposed experiment

Simulate 100 sessions with time rollback, duplicate delivery, delayed sync, and app restart. Baseline: sorting events by wall time. Adopt if sequence reconstruction has zero inversions and all invalid transitions are flagged; kill if restart causes sequence reuse or lost events. These are proposed pass criteria, not measured.

## 6. Risks

Sequence numbers prove ordering only within the local store and do not establish trusted time. Keep clock uncertainty explicit.

## 7. Combinations

Pairs with strategies 8, 15, 17, 20, 26, and 27.

## 8. Results log

NOT RUN. No lifecycle event traces tested.
