# DayOne · Strategy 12: Multi-engine voting with field-level arbitration

| | |
|---|---|
| **Status** | DONE - partly adopted (Claude Code, 2026-10-03) |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Depends on** | strategy 1 (ground truth, eval harness), at least two extractors among strategies 2, 3, 11 |
| **Rubric lines** | Extraction quality (30), Uncertainty (20: disagreement is an honest doubt signal) |
| **Differs from 1–10** | Strategy 6 calibrates a confidence for one output. This **combines several engines' outputs** into a better value per field (weighted voting by field type, with learned engine reliabilities), and uses their disagreement to drive À_RÉVISER |
| **Work folder** | `dayone-participants/work/strat12/` |

---

## 1. Context you need

- Candidate engines: zonal recognisers on registered crops (strategy 2), whole-page or crop-level VLM (strategy 3), fine-tuned small recogniser (strategy 11), possibly a second VLM or a classic OCR (Tesseract / PaddleOCR).
- Engines fail differently: VLMs hallucinate on blanks and swap rows in dense tables; OCR engines misread handwriting but rarely invent; zonal methods fail when registration fails.

## 2. The idea

For each field, collect each engine's normalised value and confidence, then arbitrate:

1. **Exact agreement** of ≥ 2 independent engines → accept with high confidence.
2. **Weighted vote** with per-engine, per-field-type reliabilities learned on the ground truth (e.g. VLM weight high for free text, low for blank detection; zonal OCR weight high for dates).
3. **Character-level fusion** (ROVER-style alignment) for numeric strings when engines differ by one character, using per-character confidences.
4. **Validator tie-break:** prefer the candidate that satisfies strategy 7's rules (e.g. the date consistent with DDR + 280 days).
5. Disagreement that remains → `À_RÉVISER`, with all candidates shown to the midwife as quick-reply options.

## 3. Why it could score

Ensembles of diverse engines are a reliable way to gain accuracy, and "two engines disagree" is an intuitive, honest reason to ask the midwife, which the uncertainty criterion rewards.

## 4. Implementation plan

### 4.1 Files

```
work/strat12/
  collect.py          # run engines, store outputs per field: {engine: (value, conf)}
  reliability.py      # per engine × field type accuracy and calibration on GT (patients 1–7)
  arbitrate.py        # rules 1–5 above
  rover.py            # character alignment fusion for numeric fields
  eval_12.md
```

### 4.2 Arbitration details

```python
def arbitrate(field, cands):        # cands: list of (engine, value, conf)
    norm = [(e, normalise(field, v), c) for e, v, c in cands if v is not None]
    votes = Counter()
    for e, v, c in norm: votes[v] += reliability[e][field.type] * c
    best, score = votes.most_common(1)[0]
    if valid(field, best) and agreement(norm, best) >= 2: return best, "CONNU", calibrated(score)
    alt = [v for v in votes if valid(field, v)]
    return (alt[0] if alt else best), "À_RÉVISER", calibrated(score)
```

Blank handling: if the zonal ink detector says "blank" with high confidence and only the VLM outputs a value, prefer `NON_FOURNI` (VLM hallucination guard).

### 4.3 Engine costs

Running all engines on every page is slow; variant: run the cheap engines first and call the expensive VLM only on fields where they disagree or are low-confidence (cascade). Measure the accuracy / latency trade-off.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Accuracy | arbitrated field accuracy ≥ best single engine + 1 pt on held-out patients (8–10) and degraded pages |
| T2 | Hallucination on blanks | lower than the VLM alone |
| T3 | Review load | fraction of fields sent to À_RÉVISER and the accuracy of those that are not |
| T4 | Cascade | ≥ 95% of the full-ensemble accuracy at ≤ 50% of its latency |
| T5 | Real photos | arbitration vs best single engine on the 5 hand-labelled photos |

## 6. Risks

Correlated engines (two VLMs) add little. Measure pairwise error correlation and keep diverse engines.

## 7. Combines with

Strategy 2, 3, 11 (engines), 6 (confidence calibration on the arbitrated output), 7 (tie-break), 9 (show candidates as buttons).

## 8. Results log

| Date | Who | Engines | Accuracy (single best / vote) | Blank halluc. | Review % | Notes |
|---|---|---|---|---|---|---|
| 2026-10-03 | Claude Code | CRNN x 3 stretched views (adopted); CRNN + VLM (rejected); checkpoint ensemble (code only) | 0.893 single view -> 0.933 multi-view (599 filled fields, patients 2/3/6, clean) | blank_acc 1.000 clean | see strategy 6 |

**Implementation notes (2026-10-03).** `arbitrate.py` implements vote + CRNN-likelihood arbitration with a blank guard; `fieldlogic.decide_multi` scores every candidate (each view's reading, vocabulary, format repairs) by the mean CTC log-likelihood over views. VLM arbitration not adopted (strategy 3).
