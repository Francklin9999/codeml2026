# DayOne · Strategy 4: Field-photo degradation bench + on-device quality gate

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 1 (ground truth) |
| **Rubric lines** | Extraction (30) robustness; bonus "vérification de la qualité de l'image sur l'appareil avant d'accepter la capture"; drives "Reprendre la photo" in Review (20) |
| **Work folder** | `dayone-participants/work/strat4/` |

---

## 1. Context you need

The brief describes the test images as *"photos dégradées comme sur le terrain (flou, ombres, inclinaison, faible lumière)"*, but the 80 specimen PNGs we have are clean renders. The 5 real photos show realistic conditions: perspective, dark fabric background, uneven light, a covering paper strip, a two-page spread, blue ballpoint ink.

## 2. The idea

Build a **parametric degradation pipeline** that turns each clean page into realistic phone photos while keeping the ground truth, measure each extractor's accuracy vs degradation type and severity, and use the same measurements to train a cheap **quality gate** that asks for a retake before accepting a bad capture.

## 3. Why it could score

It prevents the classic failure (perfect on clean scans, collapses on the jury's photos), produces a robustness chart for the presentation, and delivers a bonus feature.

## 4. Implementation plan

### 4.1 Setup and files

```bash
pip install albumentations opencv-python-headless numpy
```

```
work/strat4/
  degrade.py            # seeded; writes to work/_local/degraded/ (git-ignored, regenerable)
  backgrounds/          # a few textures (fabric, wood, table), self-made or CC0
  bench.py              # runs extractors, writes bench_results.csv
  quality_features.py   # cheap on-device features
  quality_gate.py       # trained classifier + threshold
  quality_gate.js       # optional port for a browser client
```

### 4.2 Degradations (each with severity 0–4)

| Family | Implementation |
|---|---|
| Perspective / skew | random corner jitter up to 4–18% of page size; `cv2.warpPerspective`; paste on a background texture |
| Rotation | ±2° to ±15° |
| Defocus / motion blur | `A.Defocus`, `A.MotionBlur` (kernel 3–15) |
| Noise | Gaussian / ISO noise |
| JPEG and downscale | quality 90 → 30; resize long side to 1600 px (WhatsApp-like) |
| Illumination | brightness/gamma down (low light), radial vignette, linear gradients |
| Hard shadows | random polygons darkened 20–60%, blurred edges (`A.RandomShadow`) |
| Colour cast | warm / cool white balance shifts on the pink paper |
| Page curl | mesh warp near one edge (binding side) |
| Occlusion | a white paper strip (like `1-1.jpg`), a finger-shaped blob |
| Two-page spread | concatenate two pages with a gutter shadow, crop partially |

Generate 3 variants × 5 severities per page (≈ 1,200 images). Store the warp so registration error can be measured exactly (strategy 2).

### 4.3 Realism calibration

Compute simple statistics (variance of Laplacian, brightness percentiles, saturation, estimated skew, text stroke height) on the 5 real photos and on the degraded set; adjust severity ranges so the real photos fall inside the generated distribution.

### 4.4 Bench

`bench.py --extractor {zonal,vlm,hybrid}` → per (degradation family, severity): field accuracy, status accuracy, hallucination on blanks. Plot accuracy vs severity curves, one panel per family.

### 4.5 Quality gate

Features (cheap enough for a phone): variance of Laplacian (blur), mean and 5th/95th brightness percentiles, glare fraction (pixels with V > 0.97 and S < 0.1), page quad found (bool), quad area / image area, skew angle, estimated text height in px. Label = "extraction field accuracy < 85%" from the bench. Model: logistic regression or a depth-3 decision tree (exportable as plain rules to JS).

Messages tied to the failing feature (for strategy 9): "La photo est floue, tenez le téléphone immobile", "Trop sombre, rapprochez-vous de la lumière", "La page n'est pas entière dans le cadre", "Reflet sur la page, inclinez légèrement le téléphone".

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Determinism | same seed → identical images (hash) |
| T2 | Realism | the 5 real photos' feature values fall within the generated 5–95% range |
| T3 | Bench | curves produced for strategies 2 and 3 (and hybrid) |
| T4 | Gate ROC | on held-out degraded pages: recall of "bad captures" ≥ 0.8 at ≤ 10% false rejects |
| T5 | Gate on real photos | none of the 5 real photos rejected unless they truly fail extraction (check with their hand labels) |

## 6. Risks

Synthetic degradations may be easier or harder than reality. T2 is the safeguard; report it.

## 7. Combines with

Strategy 2 and 3 (robustness numbers), 6 (degradation features as confidence signals), 9 ("Reprendre la photo" prompt), 8 (gate runs at capture time, offline).

## 8. Results log

| Date | Who | Extractor | Family | Accuracy at sev. 0/2/4 | Gate recall / FRR | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
