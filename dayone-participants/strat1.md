# DayOne · Strategy 1: Ground truth from the specimen PDF text layer + field schema

| | |
|---|---|
| **Status** | NOT STARTED *(set to IN PROGRESS / DONE / ABANDONED with your name and the date)* |
| **Priority** | P1 (foundation: every extraction strategy is scored with it) |
| **Effort** | 4–5 h |
| **Depends on** | nothing |
| **Rubric lines** | makes Extraction quality (30) and Uncertainty handling (20) measurable |
| **Work folder** | `dayone-participants/work/strat1/` (outputs shared in `work/shared/`) |

---

## 1. Context you need

- **Challenge:** a WhatsApp-style agent photographs pages of a paper maternal registry, extracts a predefined schema with a **status** (CONNU, INCONNU, NON_FOURNI, ILLISIBLE, NON_APPLICABLE, À_RÉVISER) and a **confidence** per field, guides the midwife's verification, works offline-first and links visits by a random code. Rubric: extraction 30 (field accuracy on a test set, handwriting + print, FR/AR/EN), uncertainty 20, conversational review 20, offline 15, linking & privacy 10, code & docs 5.
- **Data facts verified on 2026-10-03** (they correct analysis §7.5.3):
  - `data/Paper Registry/dossiers_specimen_10_patientes.pdf` = **80 pages = 10 fictional patients × 8 page types**, and it **has a text layer with the filled-in values** (≈ 15.6k words). PDF page *n* ↔ `dossiers_specimen_10_patientes-NN.png`.
  - Page types in order: 1 cover *Fiche de surveillance* (region, province, facility, facility type, coverage mode, name, risk box), 2 *Identification et antécédents*, 3 *Grossesse actuelle* (visit table), 4 *Déroulement de l'accouchement*, 5 *Post-partum précoce – mère*, 6 *Post-partum précoce – nouveau-né*, 7–8 *Post-partum tardif* (check whether 7 = mother and 8 = newborn).
  - 124 PNGs, 1654×2339 (A4 at 200 DPI), clean renders; **44 are byte-identical duplicates** (the `__xxxxxxxxxx` suffix pairs) → 80 unique pages.
  - 5 real phone photos `1-1.jpg … 1-5.jpg` (900×1600) of the real pink booklet, handwritten (no ground truth).
  - Checkbox ticks (blood group, Rh, facility type…) are **not** in the text layer; they appear to be vector marks.
  - `pdftotext -layout` misaligns table columns; use word coordinates. The local `pdftotext` is xpdf 4.00 (no `-bbox`), so use **PyMuPDF**.
  - The text layer has **no Arabic** and values are French.
- Constraint: original images and reference files must never be modified.

## 2. The idea

Extract every word of the PDF text layer **with its coordinates**, assign words to schema fields through per-page-type **zone templates**, read checkbox states from the vector drawings, and write one ground-truth JSON per page. This turns the 80 specimen pages into an exact, free test set. Define the field schema at the same time (the brief: "start from the schema, not from OCR").

## 3. Why it matters

The brief scores "field-level accuracy on a test set". Without labels we cannot compare extractors, tune thresholds, or calibrate confidence. Hand-labelling 80 dense pages would cost a day; this takes hours and is exact.

## 4. Implementation plan

### 4.1 Setup

```bash
cd dayone-participants
python -m venv ../.venv && ../.venv/Scripts/activate
pip install pymupdf pydantic pyyaml pillow numpy
mkdir -p work/strat1 work/shared/gt
```

### 4.2 Files

```
work/shared/schema.py          # Pydantic models (shared by every strategy)
work/strat1/zones/p1_cover.yaml ... p8_*.yaml   # field zones per page type (PDF points)
work/strat1/build_gt.py
work/strat1/overlay.py         # draws GT on PNGs for visual checks
work/shared/gt/page_01.json ... page_80.json
work/shared/gt/index.csv       # page → patient, page type, PNG file names incl. duplicates
work/shared/gt/photo_1-1.json ... photo_1-5.json  # hand labels for the real photos
work/shared/eval.py            # shared scorer for every extraction strategy (§4.8)
```

### 4.3 Schema (`work/shared/schema.py`)

```python
from enum import Enum
from pydantic import BaseModel
class Status(str, Enum):
    CONNU="CONNU"; INCONNU="INCONNU"; NON_FOURNI="NON_FOURNI"
    ILLISIBLE="ILLISIBLE"; NON_APPLICABLE="NON_APPLICABLE"; A_REVISER="À_RÉVISER"
class Field(BaseModel):
    key: str                      # e.g. "grossesse.visites[3].ta"
    value: str | None
    normalized: str | float | None
    status: Status
    confidence: float | None = None
    page_type: int
    bbox: tuple[float, float, float, float] | None   # in template coordinates
    raw_text: str | None = None
class Page(BaseModel):
    page_type: int
    patient_ref: str | None       # registry code, never a name
    fields: list[Field]
```

Field groups (derive the exact list from the pages): profile (age, education, consanguinity, desired pregnancy), family and personal history (HTA, diabetes, hereditary disease, malformations, allergies; family of the woman / husband's family), obstetric history (abortion, preterm, fetal death, others: count, date, place, GA), previous deliveries (up to 5 columns: date, mode, caesarean indication, complication, newborn weight, newborn complication), gravidity, parity, living children, VAT doses, rubella / hepatitis B vaccination dates, smear; current pregnancy (DDR, height, blood group, Rh, EDD, term-exceeded date; visit table × 9 columns: appointment, came on, follow-up visit, probable GA, weight, BP, skeleton, conjunctivae, breasts, oedema, active movements, fundal height, fetal heart rate, speculum, cervix, presentation, pelvis, glycosuria, albuminuria, rubella, toxoplasmosis, syphilis, HBs Ag, HIV, haemoglobin, platelets, glycaemia, RAI, iron, examiner); delivery (place, date, mode, emergency, complications, newborn status, sex, weight, head circumference, anomaly, GA); post-partum mother (date, BP, pulse, weight, temperature, conjunctivae, uterine globe, lochia, perineum, sphincters, breasts, calves, complications, medication, treatment, next appointment, family planning); post-partum newborn (to list from pages 6 and 8).

**Identifier fields (patient name, husband's name, CIN, phone, address, profession if identifying) are deliberately absent from the schema.** Record their zones in a separate `identifier_zones` block of each zone file so strategy 10 can mask them.

### 4.4 Zone templates

Open page 1–8 (patient 1) with PyMuPDF and list printed labels with coordinates:

```python
import fitz
doc = fitz.open("data/Paper Registry/dossiers_specimen_10_patientes.pdf")
for w in doc[2].get_text("words"):   # (x0, y0, x1, y1, text, block, line, word)
    print(w)
```

Separate **printed form text** (identical across the 10 patients for the same page type) from **filled values** (vary across patients; also usually a different font: check `page.get_text("dict")` spans' `font` names; the handwriting font is a strong discriminator). Then define zones:

```yaml
# zones/p3_grossesse.yaml
page_type: 3
fields:
  - {key: grossesse.ddr,      zone: [140, 160, 330, 190], type: date}
  - {key: grossesse.taille,   zone: [500, 160, 640, 190], type: number_unit}
table:
  columns: {t1_v1: [360, 467], t1_v2: [467, 573], t1_v3: [573, 680], t2_v1: [680, 787], t2_v2: [787, 893], t2_v3: [893, 1000], m7: [1000, 1106], m8: [1106, 1212], m9: [1212, 1318]}
  rows: {rdv: [328, 370], venue: [370, 412], relance: [412, 455], age_probable: [455, 497], poids: [540, 582], ta: [582, 624], ...}
identifier_zones: []
```

(Coordinates above are illustrative pixel values from the PNG; store PDF points in the real file and convert with the 200/72 scale.)

### 4.5 Word → field assignment

For each value word (handwriting font), find the zone containing its centre; concatenate words in reading order; an empty zone becomes `NON_FOURNI`; a dash "–" becomes `NON_FOURNI` with `raw_text="–"` (document this convention); form logic sets `NON_APPLICABLE` (e.g. caesarean indication when mode is vaginal, RAI when Rh+).

### 4.6 Checkboxes

```python
for d in page.get_drawings():
    # squares: a 're' item roughly 8–12 pt wide; ticks: two 'l' (line) items crossing inside a square
```

A box is ticked if ≥ 2 crossing line segments lie inside its rectangle. If the ticks turn out to be glyphs or images, fall back to pixel ink density inside the box on the PNG (compare with an unticked box's density).

### 4.7 Real photos

Hand-label the 5 photos in the same JSON format (1–2 h); fields not visible (off-frame, covered) → leave out with a note. They are the only real-handwriting test.

### 4.8 Shared evaluation harness (`work/shared/eval.py`)

Every extraction strategy (2–7) is scored with this script, so build it here.

```bash
python work/shared/eval.py --pred work/strat3/out/ --gt work/shared/gt/ --by page_type,field_type,lang,severity
```

- **Matching:** by field `key`; missing predictions count as wrong; extra keys are reported (and identifier-like extra keys are flagged as leaks).
- **Type-aware normalisation before comparing:** dates parsed to ISO (`dd/mm/yyyy`, `d/m/yy`); numbers with units stripped and compared with a tolerance (weight ± 0.1 kg, haemoglobin ± 0.1 g/dL, temperature ± 0.1 °C, others exact); BP as an integer pair; enums mapped to canonical codes (`RAS`/`Normal(e)s` → `NORMAL`, `Neg` → `NEG`, …); free text compared with normalised Levenshtein ≥ 0.9 as a match.
- **Metrics:** field accuracy (overall and per breakdown); status accuracy and confusion matrix; hallucination rate (value predicted where GT status is `NON_FOURNI`); calibration (ECE, reliability bins) if confidences are present; identifier leak count.
- **Output:** a Markdown table printed to the console + `eval_<run>.json` for the results logs.

## 5. How to test it

| # | Test | How | Pass if |
|---|---|---|---|
| T1 | Visual spot check | `overlay.py` draws each GT value at its bbox on the PNG for 8 random pages (one per type) | a human finds 0 errors |
| T2 | Coverage | count value words (handwriting font) not assigned to any field | < 1% per page |
| T3 | Consistency | run strategy 7's validator on all GT pages | 0 hard-rule violations (a violation means a zone bug or a wrong rule) |
| T4 | Duplicates | `index.csv` maps all 124 PNGs to 80 pages; SHA-256 of each duplicate pair is equal | 124 → 80 |
| T5 | Identifier exclusion | grep `work/shared/gt/` for each patient's name, CIN, phone, address (from the text layer) | 0 hits |

## 6. Risks and guardrails

- These pages are clean and French-only; the jury's test set is likely degraded and multilingual. Use strategies 4 and 5 to cover that.
- Never write to `data/`.

## 7. Combines with

Every extraction strategy (2, 3, 4, 5, 6, 7) uses this schema and ground truth; 10 uses the identifier zones.

## 8. Results log

| Date | Who | Pages done | Spot-check errors | Unassigned words | Verdict |
|---|---|---|---|---|---|
| | | | | | |
