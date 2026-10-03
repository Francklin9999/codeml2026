# DayOne · Strategy 28: Review-time keyboard and correction ergonomics study

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 9 review prototype; evaluator optional |
| **Work folder** | `dayone-participants/work/strat28/` |

## 1. Context and evidence

Strategy 9 already proposes a deterministic chat-style review with evidence crops and quick replies; strategy 15 covers offline capture. No reviewed data or operator usability results are reported in `work/shared/report.md`. This proposal evaluates a specific interaction constraint: whether corrections can be made accurately and with low effort on a small phone screen, including keyboard locale and navigation.

Evidence: [DayOne evaluation audit](work/shared/report.md) includes no operator usability results.

## 2. Idea and distinction

Create a scripted usability benchmark using fictitious records and representative field widgets: date entry, BP pair, numeric quantity, enumerated choice, illegible, and blank. Measure time, correction errors, accidental status changes, and focus loss for chat cards versus a compact field table. The purpose is interaction ergonomics rather than new dialogue logic or OCR confidence.

## 3. Rubric relevance

Supports conversational review and mobile usability, where the human must safely confirm or correct extraction results.

## 4. Implementation steps

Create a static prototype and task runner in `work/strat28/`. Use generated fictitious examples only. Log task IDs and timings, not typed personal data. Include keyboard focus order, large touch targets, French/Arabic keyboard toggling, and undo for changed values.

## 5. Proposed experiment

Ask five internal reviewers to complete 12 tasks each in randomized layouts; baseline is the current chat mock. Adopt table/card changes if median completion time improves ≥15% with no increase in uncorrected errors and zero lost edits; kill if errors rise by >2 percentage points. Proposed thresholds, not measured. Small sample results are usability signals only.

## 6. Risks

Internal participants do not represent midwives or literacy contexts. Avoid collecting health information and avoid interpreting speed as clinical competence.

## 7. Combinations

Use with strategies 9, 14, 15, 23, and 24; correction events can feed strategy 27.

## 8. Results log

NOT RUN. No usability sessions conducted.
