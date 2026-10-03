# DayOne · Strategy 11: Fine-tune a small handwriting recogniser on synthetic cell crops

| | |
|---|---|
| **Status** | NOT STARTED *(set to IN PROGRESS / DONE / ABANDONED with your name and the date)* |
| **Priority** | P2 |
| **Effort** | 6–8 h (data generation 2 h, training 3 h, evaluation 1–2 h) |
| **Depends on** | strategy 1 (schema, ground truth, cell zones), strategy 2 (cell crops), strategy 5 helps (fonts, vocabularies) |
| **Rubric lines** | Extraction quality (30), Uncertainty (20: real per-character confidences), offline robustness (a small model can run on a device or edge box) |
| **Differs from 1–10** | Strategies 2 and 3 use off-the-shelf recognisers or a large VLM. This **trains a small, specialised recogniser** for the registry's narrow vocabulary (dates, numbers, BP, short enums, FR/AR digits), which is fast, local and calibratable |
| **Work folder** | `dayone-participants/work/strat11/` |

---

## 1. Context you need

- Data facts (verified 2026-10-03): `data/Paper Registry/dossiers_specimen_10_patientes.pdf` has a text layer with the filled-in values for its 80 pages (10 patients × 8 page types); the matching PNGs are clean A4 renders at 200 DPI written in a handwriting-style font; 5 real phone photos (`1-1.jpg…1-5.jpg`) show real blue-ink handwriting on the pink booklet. No Arabic in the specimen.
- Rubric: extraction 30 (field accuracy on a test set; handwriting + print; FR, AR, EN), uncertainty 20.
- The values in most cells are short and constrained: dates `dd/mm/yyyy`, numbers with units (`58.8`, `11.8 g/dL`, `12 SA`), BP `104/74`, enums (RAS, Normales, Oui, Non, Neg, Pos, Fermé, Céphalique, Immune…).

## 2. The idea

Generate a large synthetic dataset of **single-cell crops** (value rendered in many handwriting fonts, inks, sizes, slants, with the cell's printed lines, pink background and photo degradations), add the real crops we can label (specimen cells + the 5 photos), and fine-tune a small text-recognition model. Use **constrained decoding** per field type (only digits and `/` for dates; vocabulary list for enums) to cut errors further.

## 3. Why it could score

A specialised model can beat general OCR on this narrow task, gives meaningful per-character probabilities for the status / confidence logic, and runs offline on modest hardware (fits the offline-first story).

## 4. Implementation plan

### 4.1 Model candidates

| Model | Size | Notes |
|---|---|---|
| TrOCR-small (handwritten) via `transformers` | ~60M params | English-pretrained; fine-tune for French accents and Arabic-Indic digits |
| PARSeq (scene-text recogniser) | ~24M | fast, strong on short strings; check licence (Apache-2.0) |
| CRNN + CTC from scratch | ~5M | simplest; trains quickly on synthetic data, easy to constrain |

### 4.2 Files

```
work/strat11/
  gen_crops.py          # synthetic cell crops + labels (seeded); output in work/_local/crops/
  vocab/                # per-field value generators and enum lists (FR/EN/AR)
  real_crops.py         # crops from specimen PNGs using strategy 1 GT bboxes; from photos via strategy 2 registration
  train.py              # fine-tuning script (Colab/Kaggle-friendly)
  constrained_decode.py # field-type grammars / vocab-constrained beam search
  eval_11.md
```

### 4.3 Data

- Synthetic: 200k crops (dates 30%, numbers / units 30%, BP 10%, enums 25%, short free text 5%); fonts with OFL licences (record them); random ink colour (blue / black), stroke width, slant ±12°, baseline jitter, writing above the line, partial overlap with cell borders; degradations from strategy 4 (blur, JPEG, shadows, low light); Arabic-Indic digits for 10% of numbers.
- Real: all value cells of the 80 specimen pages (~a few thousand crops), **split by patient** (patients 1–7 train, 8–10 test); the 5 photos' cells as a separate real-handwriting test set only.

### 4.4 Training

Start from pretrained weights; 2–5 epochs on synthetic, then 2–3 on synthetic + real (patients 1–7); character error rate (CER) on validation for early stopping; mixed precision on a Colab T4 or the local CUDA GPU if available.

### 4.5 Constrained decoding

Per field type, restrict the output alphabet (dates: `0-9/`; BP: `0-9/`; numbers: `0-9.,` + unit tokens) and, for enums, rescore beams against the vocabulary (pick the closest valid value, keep the edit distance as a confidence feature).

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Held-out specimen patients (8–10) | field exact-match ≥ 97%, CER ≤ 1% |
| T2 | Real photo crops (5 photos) | report CER and exact match vs strategy 2's off-the-shelf recogniser and strategy 3's VLM on the same crops |
| T3 | Degradation curve | accuracy vs strategy 4 severity for synthetic test crops |
| T4 | Arabic-Indic digits | exact match on synthetic AR-digit crops ≥ 90% |
| T5 | Calibration | sequence probability vs correctness: ECE ≤ 0.05 (feeds strategy 6) |
| T6 | Speed | ≤ 20 ms per crop on CPU |

**Adopt** for a field type if it beats the alternatives on T1 and T2 for that type.

## 6. Risks

Synthetic fonts are easier than real handwriting (T2 is the honest check). Training time: cap at the effort estimate and keep strategy 3 as the fallback.

## 7. Combines with

Strategy 2 (crops, registration), 5 (fonts, AR vocab), 6 (confidence signal), 12 (one engine in the vote), 20 (edge deployment).

## 8. Results log

| Date | Who | Model | Train data | CER held-out | Exact match (photos) | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
