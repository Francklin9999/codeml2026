# DayOne · Strategy 16: Human-in-the-loop learning: midwife corrections improve the extractor over time

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P3 (strong story; measurable in simulation) |
| **Effort** | 3–4 h |
| **Depends on** | strategy 1 (GT), 6 (confidence), 9 (review flow records corrections); 11 helps (a trainable recogniser) |
| **Rubric lines** | Extraction (30) over time, Uncertainty (20: thresholds adapt), Conversational review (20: fewer questions as the system learns), presentation value |
| **Differs from 1–10** | Strategies 1–10 treat the extractor as fixed. This closes the loop: every confirmation or correction becomes labelled data, used to **recalibrate confidence** quickly and to **fine-tune** the recogniser periodically, with a measured learning curve |
| **Work folder** | `dayone-participants/work/strat16/` |

---

## 1. Context you need

- The review flow (strategy 9) produces, for every reviewed field, the extracted value, the confidence and the midwife's final value. That is free supervision, collected without changing the midwife's work.
- Privacy: corrections are field values, not identifiers; images used for training must be the masked working copies (strategy 10), never originals with identifiers.

## 2. The idea

Three learning loops of increasing cost:
1. **Online recalibration (cheap):** update the confidence calibrator (strategy 6) with each batch of reviewed fields; thresholds τ adapt so the auto-accept accuracy stays ≥ 99% while asking fewer questions over time.
2. **Per-site vocabulary and priors:** learn local spelling habits ("RAS", "Nle", abbreviations) and value distributions; add them to the enum vocabularies and validators.
3. **Periodic fine-tuning (expensive):** retrain the small recogniser (strategy 11) on accumulated corrected crops, with a holdout to prevent regressions; deploy only if it beats the current model.

## 3. Why it could score

A learning curve ("after 100 reviewed pages, questions per page drop from 8 to 4 with the same accuracy") is a compelling, honest demonstration of a system that gets better in the field, and it directly supports the uncertainty and review criteria.

## 4. Implementation plan

### 4.1 Files

```
work/strat16/
  feedback_store.py    # (field key, page type, crop ref, predicted, confidence, final, reviewer, time)
  recalibrate.py       # incremental calibrator update + threshold re-selection
  vocab_learn.py       # frequent corrected forms → vocabulary / normaliser rules (human-approved)
  finetune_job.py      # periodic fine-tuning with regression gate
  simulate_stream.py   # simulated midwife: answers = ground truth
  eval_16.md
```

### 4.2 Simulation protocol

Stream pages in random order (degraded specimen + synthetic multilingual pages); the simulated midwife answers every question with the GT value. After every 20 pages: update calibrator; every 100 pages: run the fine-tuning job if strategy 11 exists. Track questions per page, residual error on auto-accepted fields, and overall field accuracy.

### 4.3 Safety gates

- Regression gate: a new model or calibrator is deployed only if accuracy on a fixed holdout (never used for training) does not drop.
- Human approval for vocabulary rules (no automatic rule from fewer than N consistent corrections).
- Audit log of every model / calibrator version used for each record.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Learning curve | questions per page decrease over the stream while auto-accept accuracy stays ≥ 99% |
| T2 | Regression gate | a deliberately corrupted batch (wrong labels) is rejected by the gate |
| T3 | Vocabulary | learned rules improve accuracy on a held-out set of pages with the same habits |
| T4 | Traceability | for any record, the model and calibrator versions are retrievable |

## 6. Risks

Feedback loops can amplify errors if midwives confirm wrong values out of fatigue. Mitigate with spot audits (random sample re-reviewed by a supervisor) and the regression gate.

## 7. Combines with

Strategy 6 (calibrator), 9 (feedback source), 11 (fine-tuning), 10 (masked images only).

## 8. Results log

| Date | Who | Pages streamed | Questions / page (start → end) | Auto-accept accuracy | Notes |
|---|---|---|---|---|---|
| | | | | | |
