# OptiFrame · Strategy 3: Classical edge-based segmentation on backlit images

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (reliable baseline; the brief: "une mesure fiable sans IA vaut mieux qu'une IA sans mesure") |
| **Effort** | 3–4 h |
| **Depends on** | strategy 1 (rig), 2 (rectified metric image) |
| **Rubric lines** | Measurement accuracy (30), Robustness (10); baseline for Data & AI (15) comparisons |
| **Work folder** | `optiframe-participants/work/strat3/` |

---

## 1. Context you need

Brief tips: *"Un verre transparent se voit mieux par son bord que par sa surface : regardez les gradients, pas seulement la luminosité."* and *"Faites marcher le palier 1 de bout en bout sur une seule photo avant d'entraîner quoi que ce soit."* On a backlit rig (strategy 1) the lens rim appears as a dark band (light refracted / totally internally reflected at the bevel) on a bright background; the lens interior is almost as bright as the background.

## 2. The idea

Segment the lens with classical operations tuned to the backlit appearance: find the **dark rim ring**, close it into a single outer contour, and refine it to sub-pixel accuracy (strategy 2). No training data needed, runs in OpenCV.js in milliseconds.

## 3. Why it could score

It secures Palier 1 early, it is fully explainable, and with good backlight it may already reach sub-millimetre accuracy. It is also the baseline against which the AI strategies must prove their value.

## 4. Implementation plan

### 4.1 Files

```
work/strat3/
  segment_classic.py     # rectified image → binary mask + outer contour
  params.yaml            # thresholds in mm (not px) so they survive resolution changes
  debug_views.py         # intermediate images for the app's "pas à pas" page
  eval_seg.py
```

### 4.2 Pipeline (on the rectified image at 20 px/mm, window region only)

1. **Background normalisation:** divide by a heavily blurred version of the image (flat-field), so uneven screen brightness disappears.
2. **Rim enhancement:** black-hat morphology (`cv2.morphologyEx(img, MORPH_BLACKHAT, ellipse kernel ~1.5 mm)`) highlights thin dark structures; plus gradient magnitude (Scharr).
3. **Threshold:** Otsu on the enhanced image, or adaptive threshold; remove components smaller than 5 mm² and those touching the window border.
4. **Close the ring:** morphological closing (kernel ~1 mm), then fill holes (`floodFill` from the background) → solid lens mask.
5. **Largest component** with plausibility checks: area between 600 and 4,000 mm², width 30–75 mm, solidity > 0.9; otherwise return a clear error ("verre non détecté : vérifiez qu'il est dans la fenêtre").
6. **Outer contour** (`findContours`, `CHAIN_APPROX_NONE`) → sub-pixel refinement (strategy 2 §4.4) → smoothing.
7. Alternative refinement: active contour (`skimage.segmentation.active_contour`) or a polar dynamic-programming edge tracer (unwrap the image around the lens centroid into polar coordinates, find the outermost strong dark-to-bright transition per angle with a smoothness constraint). The polar DP is very robust for convex-ish lens shapes; test it.

### 4.3 Hard cases to handle

| Case | Expected problem | Handling |
|---|---|---|
| High minus lens (thick edge) | wide dark band, inner and outer edges | always take the **outer** boundary |
| High plus lens (thin edge) | faint rim | rely on gradient + polar DP; increase exposure |
| Tinted / sunglasses | whole lens darker | plain threshold works; check no inner edge |
| Drill holes / notches (rimless) | concavities | keep them in the contour (they matter for fit) |
| Dust, scratches, reflections | spurious edges | morphology size filter; polar DP smoothness |
| Lens partly outside window | open contour | error message, ask to recentre |

### 4.4 Debug views

Save each step (normalised, enhanced, mask, contour overlay) for the app's step-by-step page (deliverable: *"une photo avec ses images intermédiaires (référence, redressement, contour)"*).

## 5. How to test it

### 5.1 Ground truth

- **Measurement GT:** calliper A, B of own lenses (strategy 2 §5.1).
- **Contour GT (optional):** trace a few lenses on paper with a fine pen, scan the paper at 600 dpi next to a ruler, digitise the contour; or use a high-quality backlit shot taken with a tripod and manual mask cleanup as GT for harder shots of the same lens in the same position.

### 5.2 Metrics

A / B MAE vs calliper; boundary error (mean and 95th percentile distance between predicted and GT contours, in mm) where contour GT exists; failure rate (no lens / wrong lens) over all shots; runtime.

### 5.3 Experiments

| # | Experiment | Target |
|---|---|---|
| E1 | 8 own lenses × 5 shots on the backlit rig | MAE ≤ 0.5 mm, failure rate ≤ 5% |
| E2 | Same with room light only (no backlight) | measure how far it degrades (motivates strategies 4–6) |
| E3 | Polar DP vs plain contour | boundary p95 error |
| E4 | OpenCV.js port vs Python | identical A/B within 0.05 mm |

### 5.4 Acceptance

E1 passes → this is the production segmenter for backlit shots, and the AI strategies are used for non-backlit or failure cases.

## 6. Risks

Over-tuning to our lenses. Keep thresholds in mm and test on lenses not used for tuning.

## 7. Combines with

Strategy 2 (refinement and measurement), 4 (alternative signal), 5 / 6 (AI fallback; this also provides pseudo-labels for 6), 7 (multi-shot), 10 (OpenCV.js).

## 8. Results log

| Date | Who | Experiment | MAE A / B | Boundary p95 | Failures | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
