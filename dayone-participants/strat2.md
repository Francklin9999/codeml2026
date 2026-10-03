# DayOne · Strategy 2: Template registration + per-cell zonal extraction

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (extractor A) |
| **Effort** | 6–8 h |
| **Depends on** | strategy 1 (schema, zones, ground truth) |
| **Rubric lines** | Extraction quality (30); provides evidence crops for Review (20) and masks for Privacy (10) |
| **Work folder** | `dayone-participants/work/strat2/` |

---

## 1. Context you need

- The registry is a **fixed form** with 8 page layouts (see strategy 1). The specimen PNGs are clean A4 renders at 200 DPI; the 5 real photos (`1-1.jpg … 1-5.jpg`) show what the field looks like: pink paper on dark fabric, perspective, shadows, blue ballpoint, values written **above** row lines, a paper strip covering the name (`1-1.jpg`), and a **two-page spread whose row labels are off-frame** (`1-5.jpg`).
- The brief's tip: *"Start from the schema, not from the OCR."*

## 2. The idea

1. Classify the page type. 2. **Register** the photo onto a clean template of that page (homography). 3. Crop each field's zone. 4. Read each crop with a recogniser specialised for its field type (date, number, BP, enum, checkbox, free text).

## 3. Why it could score

Field identity comes from geometry (reliable), the recogniser solves a small typed problem, and each field gets a natural confidence and an evidence crop to show the midwife. It also handles `1-5.jpg`: even without visible row labels, registration tells which row a value belongs to.

## 4. Implementation plan

### 4.1 Setup

```bash
pip install opencv-python-headless numpy pillow pymupdf
# recognisers (pick after a quick bake-off): transformers (TrOCR), paddleocr, or a VLM from strategy 3
```

### 4.2 Files

```
work/strat2/
  templates/p1.png ... p8.png        # clean page per type (patient 1), + zone polygons in pixels
  classify_page.py
  register.py
  recognisers/{checkbox,date,number,bp,enum,freetext}.py
  extract_zonal.py                   # image → schema Page (with bbox, crop path, confidence)
  eval_02.md
```

### 4.3 Page-type classification

- Option A: OCR the top 15% of the warped page and match the header (*GROSSESSE ACTUELLE*, *DÉROULEMENT DE L'ACCOUCHEMENT*, *CONSULTATION DU POST-PARTUM…* + *NOUVEAU-NÉ*…).
- Option B: global descriptor (downscaled grayscale + HOG, or CLIP image embedding) and nearest template.
- If confidence is low, the chat (strategy 9) asks: "Quelle page est-ce ?" with 8 buttons.

### 4.4 Registration

1. **Page quad:** segment the pink paper (HSV threshold on the pink hue + largest contour, `cv2.approxPolyDP` to 4 corners) → perspective warp to 1654×2339.
2. **Fine alignment:** ORB/SIFT keypoints on printed structure (mask out handwriting by keeping dark-gray/black pixels, dropping blue ink via HSV) → `cv2.findHomography(..., cv2.RANSAC, 3.0)` to the template.
3. **Table pages:** alternatively align detected table lines (morphological opening with long horizontal/vertical kernels → line maps → ECC alignment `cv2.findTransformECC` on the line maps). Usually more robust than keypoints on grids.
4. **Two-page spreads:** detect the gutter (strong vertical shadow / fold line), split, register each half to its template (the left half of `1-5.jpg` belongs to a different page than the right half).
5. Output the homography and a registration quality score (mean reprojection error of matched lines / keypoints).

### 4.5 Recognisers per field type

| Type | Method | Output check |
|---|---|---|
| checkbox | ink density inside the box (after removing the printed square by erosion) vs empty-box baseline; threshold tuned on GT | ticked / not ticked + margin as confidence |
| date | handwriting recogniser on the crop → regex `\d{1,2}/\d{1,2}/\d{2,4}` → parse | valid calendar date |
| number / number+unit | recogniser → regex `\d+([.,]\d+)?\s*(kg|cm|g/dL|g/L|SA|g)?` | numeric parse |
| BP | recogniser → `\d{2,3}/\d{2,3}` | sys > dia |
| enum (RAS, Normal(e)s, Oui/Non, Neg/Pos, Fermé, Céphalique, Immune…) | recogniser + closest match in the field's vocabulary (normalised Levenshtein); or constrained decoding | distance as confidence |
| free text | VLM on the crop (strategy 3's model) | none |

Recogniser bake-off (1 h): TrOCR-base-handwritten (English-trained; check French accents), PaddleOCR (latin + arabic models), and the strategy 3 VLM run on crops. Pick per field type.

Crops: add a margin of ~15% of the cell height **above** the cell (values are often written above the line in real photos).

## 5. How to test it

### 5.1 Datasets

(a) 80 clean specimen pages; (b) strategy 4's degraded versions (severity 0–4); (c) the 5 hand-labelled photos; (d) strategy 5's multilingual pages.

### 5.2 Metrics (via `work/shared/eval.py`)

- field accuracy (exact after type-aware normalisation), by field type and page type;
- registration error: on synthetically warped specimen pages, mean corner error in px vs the known warp (target < 5 px at 200 DPI);
- page-type classification accuracy;
- time per page.

### 5.3 Ablations

with / without fine alignment; keypoints vs line-ECC on table pages; crop margin 0% vs 15%; each recogniser per field type.

### 5.4 Acceptance / kill

- **Target:** ≥ 95% field accuracy on clean pages; degradation curve (strategy 4) falls more slowly than strategy 3's whole-page VLM.
- **Kill:** if registration fails on > 30% of real photos after 4 h, keep only the quad warp and use strategy 3 for reading the warped page.

## 6. Risks

Real booklets may differ slightly from the specimen layout (different print run). The photos `1-1` to `1-5` show the real layout: check that the specimen templates match it; if not, build templates from the photos too.

## 7. Combines with

Strategy 3 (hybrid: VLM reads registered crops), 6 (confidence signals), 7 (validation), 9 (crops shown in chat), 10 (identifier zones masked right after registration).

## 8. Results log

| Date | Who | Dataset | Field acc. | Reg. error | Notes |
|---|---|---|---|---|---|
| | | | | | |
