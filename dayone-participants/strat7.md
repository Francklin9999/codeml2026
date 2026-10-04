# DayOne · Strategy 7: Cross-field clinical-consistency validator

| | |
|---|---|
| **Status** | DONE (Claude Code, 2026-10-03) |
| **Priority** | P1 (cheap, deterministic, high value) |
| **Effort** | 2–3 h |
| **Depends on** | strategy 1 (schema; GT to test against) |
| **Rubric lines** | Extraction (30), Uncertainty (20), Review (20: follow-up questions) |
| **Work folder** | `dayone-participants/work/strat7/` |

---

## 1. Context you need

A pregnancy record has strong internal arithmetic, and the specimen respects it. Verified on patient 1: DDR 26/04/2025 → expected delivery 31/01/2026 (DDR + 280 days) → term-exceeded 07/02/2026 (+ 7 days); visit "Âge probable 12 SA" on 20/07/2025 (DDR + 12.1 weeks). **Out of scope:** risk prediction, triage, clinical decision support. This validator checks *data consistency*, not health.

## 2. The idea

Encode consistency rules and use them to (1) catch misreads (1↔7, 3↔8, day/month swaps), (2) propose corrections ("you read 31/07/2026, the DDR implies 31/01/2026"), and (3) lower confidence on conflicting fields (strategy 6).

## 3. Why it could score

It is cheap and explainable, it catches exactly the errors handwriting recognisers make, and its messages become natural follow-up questions in the chat.

## 4. Implementation plan

### 4.1 Files

```
work/strat7/
  rules.yaml          # declarative rules
  validator.py        # evaluates rules on a schema Page / patient record
  ranges.py           # derives soft ranges from maternal_registry_synthetic.csv
  test_validator.py
  inject_errors.py    # creates corrupted copies of GT for detection tests
  eval_07.md
```

### 4.2 Rules (each with id, fields, severity hard/soft, message FR/EN, optional correction)

| ID | Rule | Severity |
|---|---|---|
| D1 | EDD = DDR + 280 d (± 1 d) | hard; suggests correction of whichever field has lower confidence |
| D2 | term-exceeded = EDD + 7 d | hard |
| D3 | visit dates within [DDR, delivery date] | hard |
| D4 | "Âge probable" at a visit ≈ (visit date − DDR)/7, ± 1 week | soft |
| D5 | delivery GA ≈ (delivery date − DDR)/7, ± 1 week | soft |
| D6 | post-partum consultation dates after delivery; early consultation box consistent with day 7–8 vs after day 8 | hard |
| D7 | next appointment after consultation date | hard |
| O1 | gravidity ≥ parity | hard |
| O2 | gravidity ≥ parity + abortions (current pregnancy may add 1) | soft |
| O3 | living children ≤ parity (+ multiples) | soft |
| O4 | number of filled previous-delivery columns ≤ parity | soft |
| V1 | BP written `sys/dia` with sys > dia, 60 ≤ sys ≤ 250, 30 ≤ dia ≤ 150 | hard (format) |
| V2 | weight 30–200 kg; visit-to-visit change ≤ 10 kg | hard / soft |
| V3 | temperature 34–42 °C | hard |
| V4 | haemoglobin 4–20 g/dL | hard |
| V5 | fetal heart rate 80–220 bpm | hard |
| V6 | fundal height 5–45 cm, non-decreasing across visits | soft |
| V7 | birth weight 400–6,000 g; head circumference 20–45 cm | hard |
| L1 | caesarean indication filled only if mode = caesarean | hard (form logic) |
| L2 | RAI only if Rh− | soft |
| L3 | complication type only if "présence de complications" ticked | soft |

Soft ranges: from `maternal_registry_synthetic.csv`, take the 0.5–99.5 percentiles of each matching column (e.g. systolic BP, haemoglobin, birth weight) as warnings; keep the wide physiological ranges as hard errors.

### 4.3 Correction suggestions

For date rules, compute the implied value and the edit distance between it and the read string; if ≤ 2 characters differ, propose the implied value with the confusable characters highlighted ("31/07 → 31/01 ?").

### 4.4 API

```python
issues = validate(record)   # list of {rule_id, severity, fields, message_fr, message_en, suggestion}
```

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | No false alarms on GT | 0 hard violations on the 80 GT pages (strategy 1) and the 5 photo labels; if a rule fires, fix the GT or the rule |
| T2 | Error detection | `inject_errors.py` applies OCR-like corruptions (digit confusions 1/7, 3/8, 0/6, 5/6, 4/9; day/month swap; dropped digit; decimal shift ×10) to GT values; detection rate per error type; target ≥ 60% overall on numeric/date errors |
| T3 | Corrections | for injected date errors caught by D1/D2, the suggested value equals the original GT ≥ 80% |
| T4 | Unit tests | one passing and one failing example per rule |

## 6. Risks

Rules drifting into clinical judgement. Keep messages factual ("valeur hors format / incohérente avec…"), never advice.

## 7. Combines with

Strategy 6 (flags lower confidence), 9 (messages become questions), 5 (sampler generates consistent records with the same rules), 1 (T3 of strategy 1).

## 8. Results log

| Date | Who | False alarms on GT | Detection rate | Correction accuracy | Notes |
|---|---|---|---|---|---|
| 2026-10-03 | Claude Code | 0 on the 10 GT booklets | 50/50 injected digit confusions (stub scorer) | 50/50 | on real runs: 2 / 19 / 16 repairs at sev 0 / 2 / 4 |

**Implementation notes (2026-10-03).** Two parts. (1) `fieldlogic.py`: per-field grammar + vocabulary candidates rescored with the CTC likelihood (snap if within 6 nats of the free reading; tuned on patients 1-5, confirmed on 6-10): +5 to +11 pts on filled fields. A first version had a bug (the free reading was compared against a maximum that already contained itself, so nothing ever snapped). (2) `validator.py`: DPA = DDR+280, DDT = DPA+7, visit GA, GA at birth, newborn age in days, same fact on two pages; a rule only changes a value if the recogniser finds the implied value plausible, otherwise it flags and offers the value as a quick reply.
