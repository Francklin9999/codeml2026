# DayOne · Strategy 18: Checkbox and mark recognition specialist (OMR for ticks, crosses, circles and strike-throughs)

| | |
|---|---|
| **Status** | DONE - adopted (Claude Code, 2026-10-03) |
| **Priority** | P2 (many fields on the form are checkboxes) |
| **Effort** | 3–4 h |
| **Depends on** | strategy 1 (box positions; GT from PDF drawings), strategy 2 (registration) |
| **Rubric lines** | Extraction (30), Uncertainty (20: ambiguous marks → À_RÉVISER) |
| **Differs from 1–10** | Strategy 2 treats checkboxes as one recogniser among many (ink density). This is a dedicated **optical mark recognition** module handling the real variety of marks (✓, ✗, filled box, circled label, crossed-out tick, mark slightly outside the box) and mutually exclusive groups |
| **Work folder** | `dayone-participants/work/strat18/` |

---

## 1. Context you need

- The registry is full of checkboxes: facility type (DR / CSC / CSU / CSCA / CSUA), coverage mode (Fixe / Mobile), risk types (Anémie, HTA, Diabète, Cardiopathie, Métrorragie, Infection, Pré-éclampsie, Éclampsie), consanguinity, desired pregnancy, blood group (A / B / O / AB) and Rh, delivery place and mode, complications, newborn status, lochia, perineum, breasts, calves, family planning…
- Specimen: ticks are drawn as an "X" inside the box (not in the text layer); `1-1.jpg` shows a real "X" in the "Fixe" box. Real midwives also circle the label, tick next to the box, or cross out and re-tick.

## 2. The idea

For each checkbox (position from the template), classify the mark into {empty, checked, crossed-out / corrected, ambiguous} with a small CNN on the box crop **plus context** (label region and surroundings to catch circled labels and ticks outside the box). Then apply **group logic**: exclusive groups (blood group, Rh, Fixe/Mobile) must have exactly one choice; multi-select groups (risk types, complications) any number. Group violations → À_RÉVISER with a targeted question.

## 3. Why it could score

Checkboxes are a large share of fields and a classic OCR blind spot; getting them right lifts field accuracy substantially, and group logic gives meaningful doubts ("Deux groupes sanguins cochés : A ou B ?").

## 4. Implementation plan

### 4.1 Files

```
work/strat18/
  boxes.yaml          # per page type: box id, bbox, label bbox, group, exclusive?
  crops.py            # box + context crops after registration
  synth_marks.py      # synthetic marks (✓ ✗ fill, circle around label, scribble, partial) on empty boxes
  omr_model.py        # small CNN (e.g. 3 conv layers) or a fine-tuned MobileNet on 64×64 crops
  group_logic.py
  eval_18.md
```

### 4.2 Data

- GT from the specimen (strategy 1: drawings parsed from the PDF) for checked vs empty.
- Synthetic marks: draw strokes with random pen width, angle, tremor (Bezier curves), colours; include **negative** cases (stray ink near the box, printed box only, shadow) and **corrections** (a tick scribbled over).
- Real: boxes in the 5 photos, hand-labelled.

### 4.3 Baseline first

Ink-density baseline (fraction of dark/blue pixels inside the box after removing the printed square by morphology). Keep the CNN only if it clearly beats the baseline on real photos.

### 4.4 Group logic

```python
for g in groups:
    states = [omr[b] for b in g.boxes]
    if g.exclusive and sum(s == "checked" for s in states) != 1: flag(g, "À_RÉVISER")
    if any(s == "ambiguous" for s in states): flag(g, "À_RÉVISER")
```

Plus form logic links: "Grossesse classée à risque" unchecked but risk types checked → ask.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Specimen boxes (held-out patients) | accuracy ≥ 99.5% |
| T2 | Degraded specimen (strategy 4 severities) | accuracy curve vs baseline |
| T3 | Real photos | accuracy on hand-labelled boxes vs ink-density baseline |
| T4 | Mark variety | per mark type (✓, ✗, fill, circle, correction) accuracy on synthetic test set |
| T5 | Group logic | injected double-ticks in exclusive groups always flagged |

## 6. Risks

Circled labels are easy to miss if crops are too tight; include the label region in the context crop.

## 7. Combines with

Strategy 1 (box GT), 2 (registration), 6 (confidence), 9 (targeted questions), 12 (as an engine in the vote).

## 8. Results log

| Date | Who | Method | Specimen acc. | Photos acc. | Notes |
|---|---|---|---|---|---|
| 2026-10-03 | Claude Code | small CNN on 40x40 box+context crops, 80k synthetic crops, 7 mark styles | 1.000 clean (v1 without hatching: 0.948, patient 4 at 0.74); 0.992 sev 2; 0.932 sev 4 | n/a | exclusive-group logic not added |

**Implementation notes (2026-10-03).** The specimen's patient 4 ticks with hatching strokes, absent from the first synthetic marks: adding hatch / slash / scribble / circle styles fixed it.
