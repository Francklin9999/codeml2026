# DayOne · Strategy 17: Document assembly engine (page typing, ordering, duplicate and re-scan detection)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 1 (page types), strategy 2 (page classification) |
| **Rubric lines** | Conversational review (20: multi-page sessions), Offline robustness (15: failure state "doublon suspecté"), Extraction (30: correct page type → correct schema) |
| **Differs from 1–10** | Strategy 9 handles multi-page sessions in the dialogue. This is the **engine underneath**: deciding which booklet and page type each photo belongs to, detecting the same page photographed twice (exact or near duplicates, re-scans with new handwriting), and assembling one document per registry |
| **Work folder** | `dayone-participants/work/strat17/` |

---

## 1. Context you need

- Brief task 7: *"les pages d'un même registre forment un seul document ; si un registre est rephotographié, afficher le dossier existant et laisser la sage-femme choisir quoi mettre à jour."* Lifecycle includes the failure state **"doublon suspecté"**.
- Data facts: the specimen has 8 page types per booklet; **44 of the 124 PNGs are byte-identical duplicates** (pairs sharing a SHA-256 with different file-name suffixes): a ready-made duplicate-detection test.
- Real photos may show two pages at once (`1-5.jpg` is a spread).

## 2. The idea

For every incoming image:
1. **Exact duplicate:** SHA-256 of the file → same capture uploaded twice (retry, double tap).
2. **Near duplicate (same page, new photo):** perceptual hash of the registered page (pHash / dHash on the masked, rectified image) + structural similarity of the handwriting layer → same page re-photographed. Distinguish *identical content* (true duplicate) from *same page with new entries* (re-scan with updates) by comparing extracted values.
3. **Page type and order:** classifier (strategy 2) + header text; order pages by type within a session; flag missing types.
4. **Booklet membership:** registry code (strategy 10) on the cover / page headers, session context (same midwife, same time window), and consistency of stable fields (DDR, etc.).
5. Output: a **document object** (booklet) with pages, versions per page, and suspected duplicates for the midwife to resolve.

## 3. Why it could score

Multi-page sessions and duplicates are explicit requirements; a robust engine prevents double records and makes the review flow simpler. The dataset's duplicate pairs provide a free test.

## 4. Implementation plan

### 4.1 Files

```
work/strat17/
  hashing.py         # sha256, pHash/dHash (imagehash library) on rectified, masked pages
  assemble.py        # session → booklet document; page versions; missing pages
  duplicates.py      # exact / near-duplicate / re-scan-with-changes classification
  eval_17.md
```

### 4.2 Thresholds

Calibrate the pHash Hamming distance threshold on: (a) the 44 duplicate pairs (distance 0), (b) the same page under strategy 4's degradations (should be "same page"), (c) different patients' same page type (should be "different": the printed form is identical, so hash on the **handwriting layer** only, e.g. blue-ink mask, to avoid false matches), (d) visit-k versions from strategy 13 (same page, new content).

### 4.3 Decisions

| Situation | Action |
|---|---|
| exact duplicate | drop silently, log |
| same page, same content | mark `DOUBLON_SUSPECTÉ`, ask "Cette page a déjà été enregistrée. La remplacer ?" |
| same page, new entries | route to strategy 13 (re-digitisation diff) |
| new page type for the booklet | add to document; update missing-pages list |
| two-page spread | split (strategy 2), process as two pages |

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Exact duplicates | the 44 duplicate pairs detected, 0 false positives across the 80 unique pages |
| T2 | Same page under degradation | ≥ 95% recognised as same page |
| T3 | Same page type, different patients | ≥ 99% recognised as different |
| T4 | Re-scan with changes | visit-k versions classified as "new entries", not duplicates |
| T5 | Assembly | shuffled pages of 10 patients assembled into 10 booklets with correct types and missing-page lists |

## 6. Risks

Hashing the whole page matches every copy of the printed form; hash the handwriting layer only (T3).

## 7. Combines with

Strategy 2 (classification, spreads), 8 (states), 9 (dialogue), 13 (re-digitisation), 10 (codes).

## 8. Results log

| Date | Who | T1–T5 | Hamming threshold | Notes |
|---|---|---|---|---|
| | | | | |
