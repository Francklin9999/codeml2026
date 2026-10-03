# DayOne · Strategy 6: Calibrated confidence and status classifier

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 1 (GT), one extractor (2 or 3); better with 4, 5, 7 |
| **Rubric lines** | Uncertainty handling (20); drives Review (20) |
| **Work folder** | `dayone-participants/work/strat6/` |

---

## 1. Context you need

Rubric: *"Statuts de champ corrects, scores de confiance pertinents, un agent qui ne cache jamais ses doutes."* Brief tips: *"Traiter l'information manquante comme un état à part entière ; un simple « N/A » cache si le champ était vide, illisible ou non applicable"* and *"Utiliser la confiance par champ pour décider quand l'agent pose une question de suivi."* Statuses: CONNU, INCONNU, NON_FOURNI, ILLISIBLE, NON_APPLICABLE, À_RÉVISER.

## 2. The idea

Turn raw extractor signals into a **calibrated probability that the value is correct**, then map (probability, cell content, form logic) to one of the six statuses with explicit, documented rules. Ask the midwife only where the calibrated probability is low.

## 3. Why it could score

Most teams will show a model's raw self-reported confidence, which is poorly calibrated. A reliability diagram, an ECE number and a selective-accuracy curve prove that our confidence means something, and they set the review load objectively.

## 4. Implementation plan

### 4.1 Files

```
work/strat6/
  signals.py          # per-field feature vector
  calibrate.py        # fit + save calibrator
  status_rules.py     # probability + content + logic → status
  thresholds.yaml     # τ_low, τ_high, blank-ink threshold, per field type
  plots/reliability.png  plots/selective_accuracy.png
  eval_06.md
```

### 4.2 Signals per field

| Signal | Source |
|---|---|
| recogniser / VLM token log-prob (mean, min) | strategy 2 / 3 |
| self-consistency agreement over N samples | strategy 3 |
| agreement between zonal (2) and VLM (3) readings | both |
| parser success (value matches the field grammar) | strategy 2 recognisers |
| validator flags (hard / soft) | strategy 7 |
| image quality features of the page / crop | strategy 4 |
| crop ink density and stroke count | strategy 2 crops |
| field type, page type, language | metadata |

### 4.3 Calibrator

Target = 1 if the extracted normalised value equals the GT value. Training data: degraded specimen pages (4) + synthetic multilingual pages (5), split by **patient** to avoid leakage (pages of one patient all in train or all in test). Model: logistic regression on the signals (or a small GBM) then isotonic regression on its output if the reliability diagram bends. Save with `joblib`.

### 4.4 Status rules (document them in the project README)

```python
def status(field, p, ink, logic):
    if logic.not_applicable(field):                  return "NON_APPLICABLE"   # e.g. césarienne indication with vaginal delivery; RAI when Rh+
    if ink < BLANK_INK and p_blank_high:             return "NON_FOURNI"       # empty cell or a dash
    if field.raw in {"?", "inconnu", "ne sait pas"}:  return "INCONNU"
    if not field.parsed or p < TAU_LOW:              return "ILLISIBLE"        # ink present, cannot read
    if p < TAU_HIGH or field.validator_conflict:     return "À_RÉVISER"
    return "CONNU"                                    # becomes CONNU (confirmed) after the midwife confirms
```

### 4.5 Threshold choice

From the selective-accuracy curve: choose τ_high so that fields auto-accepted as CONNU are ≥ 99% correct; τ_low where accuracy drops below ~50%. Report the resulting review load (questions per page).

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Calibration | reliability diagram on held-out patients; ECE < 0.05 |
| T2 | Selective accuracy | ≥ 99% accuracy on auto-accepted fields at the chosen τ_high |
| T3 | Status accuracy | confusion matrix vs GT statuses (blank → NON_FOURNI, logic → NON_APPLICABLE…) ≥ 95% on clean pages |
| T4 | **Never hide doubt** | inject scribbled / heavily blurred crops and partially erased values: 100% end as ILLISIBLE or À_RÉVISER, never CONNU |
| T5 | Review load | ≤ 8 questions per page at moderate degradation (strategy 4 severity 2) |
| T6 | Per-language calibration | ECE reported for FR / EN / AR separately (strategy 5) |

## 6. Risks

Calibrating on synthetic pages may be optimistic for real handwriting. Report ECE on the 5 hand-labelled photos separately, even if the sample is small.

## 7. Combines with

Strategy 2 / 3 (signals), 7 (conflicts), 9 (question selection and wording, e.g. *« Je ne suis pas sûr de la tension de la visite 2 : 106/77 ? »*).

## 8. Results log

| Date | Who | Extractor | ECE | Acc. @ auto-accept | Questions / page | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
