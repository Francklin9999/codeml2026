# DayOne · Strategy 38: Deterministic extraction replay harness

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Depends on** | strategy 1 evaluator; at least one local extractor |
| **Work folder** | `dayone-participants/work/strat38/` |

## 1. Context and evidence

DayOne has an evaluator but no reviewed gold pages or implemented OCR pipeline in its report. Existing strategy 6 addresses confidence calibration, while strategy 4 explores degradation. This proposal makes a fixed evaluation run reproducible and isolates nondeterminism across software versions, rather than proposing another metric or data generator.

Evidence: [DayOne evaluation audit](work/shared/report.md) reports no extraction pipeline or GT pages.

## 2. Idea and distinction

Create a replay manifest that pins input hashes, model and tokenizer versions, preprocessing parameters, locale, random seed, and output schema. Re-run identical fixtures and compare normalized values, statuses, confidence, and evidence coordinates. Report exact, tolerated, and unexplained changes separately. Never store source content in the manifest.

## 3. Rubric relevance

Supports trustworthy accuracy claims and lets the team detect accidental regressions before a demo.

## 4. Implementation steps

Implement `work/strat38/replay.py`, a manifest schema, and a machine-readable diff. Keep images local and source references opaque. For hosted models, do not send real or personal data; use only synthetic inputs and record provider version metadata if available.

## 5. Proposed experiment

Replay 100 synthetic crops three times on the same environment and once after a dependency update. Baseline: current one-off evaluator run. Adopt if same-environment deterministic fields are identical, or all nondeterminism is bounded and documented; kill if version changes cannot be attributed. Proposed criteria, not measured.

## 6. Risks

Some OCR services are nondeterministic or change silently. The manifest records observed conditions but cannot guarantee provider reproducibility.

## 7. Combinations

Complements strategies 1, 4, 6, 21, 26, 27, and 32.

## 8. Results log

NOT RUN. No OCR run exists to replay.
