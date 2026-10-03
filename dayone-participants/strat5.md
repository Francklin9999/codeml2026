# DayOne · Strategy 5: Multilingual (FR / AR / EN) synthetic page generator

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 4–5 h |
| **Depends on** | strategy 1 (schema, zones), 7 (consistency rules for sampling) |
| **Rubric lines** | Extraction (30: "écriture manuscrite et imprimée (français, arabe, anglais)"); bonus "robustesse sur l'écriture arabe et les pages multilingues" |
| **Work folder** | `dayone-participants/work/strat5/` |

---

## 1. Context you need

The test set includes Arabic and English entries, but the specimen PDF's text layer contains **no Arabic** and French values only. `maternal_registry_synthetic.csv` (200 rows × 31 numeric columns, some blanks) gives realistic value distributions (age 15–43, systolic BP 72.6–130.7, diastolic 42.3–83.4, haemoglobin 8.7–14.7, birth weight 2,234–4,800 g, head circumference 35–40 cm, gestational age at birth 34.6–42.0 weeks…).

## 2. The idea

Generate our own labelled pages: take each blank page layout, fill every zone with **plausible random values** in **handwriting fonts**, in French, Arabic (script and Eastern-Arabic digits) and English, plus mixed pages, and keep the ground-truth JSON. Measure the extractors per language before the jury does.

## 3. Why it could score

It is the only way to measure Arabic script, Arabic-Indic digits (٠١٢٣٤٥٦٧٨٩), right-to-left free text, English terms ("Negative", "Normal", "Cephalic") and mixed pages, and to build the normalisation layer those require.

## 4. Implementation plan

### 4.1 Setup and files

```bash
pip install pymupdf pillow arabic-reshaper python-bidi numpy pyyaml
# Pillow with libraqm gives correct Arabic shaping natively; otherwise use arabic-reshaper + python-bidi
```

```
work/strat5/
  blank_forms/p1.png ... p8.png     # form without handwriting
  fonts/                             # OFL handwriting fonts (record licences in fonts/LICENSES.md)
  vocab.yaml                         # FR / EN / AR vocabularies per enum field
  sample_values.py                   # consistent random record
  render_pages.py                    # record → page images + GT JSON
  normalise.py                       # used by extractors: digits + enums → canonical
  bench_languages.csv
```

Generated pages go to `work/_local/synth_pages/` (git-ignored, regenerable from a seed).

### 4.2 Blank forms

Preferred: re-render each PDF page **from a copy** with the handwriting spans removed. Identify value spans by font name (`page.get_text("dict")` → spans' `font`), add redaction annotations over them in the copy (`page.add_redact_annot(bbox)`, `page.apply_redactions(images=0)`), render at 200 DPI. Never modify the original PDF. Alternative: inpaint the PNG with OpenCV (`cv2.inpaint`) using GT bboxes.

### 4.3 Value sampler

- Numeric fields: sample from the CSV's empirical distribution (with jitter), or from physiological ranges for fields not in the CSV.
- Dates: sample DDR, then derive EDD = DDR + 280 d, term-exceeded = EDD + 7 d, visit dates and "Âge probable" consistently (strategy 7's rules), delivery date around EDD ± 2 weeks.
- Enums: sample from `vocab.yaml`; blanks with probability ~15% per optional field (to test NON_FOURNI); some "?" / "inconnu" (to test INCONNU).

### 4.4 Languages

| Variant | Content |
|---|---|
| FR | as the specimen |
| EN | "NAD" / "Normal", "Negative" / "Positive", "Cephalic", "Closed", "Yes" / "No", dates dd/mm/yyyy |
| AR | Arabic enums, e.g. "سلبي" (negative), "إيجابي" (positive), "طبيعي" (normal), "نعم" / "لا" (yes / no); numbers in Western or Eastern-Arabic digits (choose per field at random); free text in Arabic, right-to-left |
| MIX | language chosen per field |

Have an Arabic reader on the team check `vocab.yaml`.

### 4.5 Rendering

Fonts (examples, verify licences on Google Fonts, OFL): Latin handwriting such as Caveat, Kalam, Patrick Hand, Indie Flower; Arabic such as Aref Ruqaa, Reem Kufi Ink, Lateef, Amiri (less handwritten-looking). Randomise size (90–120% of cell height), slant (shear ±8°), baseline jitter, ink colour (blue / black, slight opacity), occasional writing above the line. Output page PNG + GT JSON (same schema as strategy 1, plus `lang` per field).

### 4.6 Normalisation layer (`normalise.py`)

- Eastern-Arabic and Persian digits → ASCII (`str.translate`).
- Enum mapping per field to canonical codes (`NEG`, `POS`, `NORMAL`, `CEPHALIC`, `YES`, `NO`…), keeping the raw text as evidence.
- Date normalisation (dd/mm/yyyy, d/m/yy, Arabic separators).

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Visual review | 10 pages per language reviewed; Arabic shaping and direction correct; values plausible |
| T2 | GT consistency | strategy 7's validator passes on all generated records |
| T3 | Bench | accuracy of strategies 2, 3 and hybrid by language and by digit system (after normalisation) |
| T4 | Target | Arabic within 10 points of French after normalisation; otherwise document as a known limitation with numbers |
| T5 | Degraded multilingual | run strategy 4's degradations on a subset and report the curve per language |

## 6. Risks

Fonts are easier than real handwriting: present the results as an upper bound and validate on the 5 real photos.

## 7. Combines with

Strategy 1, 2, 3, 4, 6 (calibration data per language), 7.

## 8. Results log

| Date | Who | Extractor | FR | EN | AR | MIX | Notes |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
