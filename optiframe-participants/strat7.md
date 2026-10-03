# OptiFrame · Strategy 7: Multi-shot fusion and consistency checking

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (cheap accuracy gain + bonus) |
| **Effort** | 2–3 h |
| **Depends on** | strategy 2 (single-shot measurement) |
| **Rubric lines** | Measurement accuracy (30), Robustness (10: "résultats cohérents sur plusieurs prises de vue"); bonus "cohérence entre les prises" |
| **Work folder** | `optiframe-participants/work/strat7/` |

---

## 1. Context you need

The robustness criterion checks *"résultats cohérents sur plusieurs prises de vue (angle, éclairage) et sur une paire de lunettes apportée par le jury, sans plantage"*. Bonus: *"pour un même verre, l'app compare au moins deux photos et affiche l'écart de A et de B entre elles."* Performance limit: result in < 30 s per pair of lenses.

## 2. The idea

Never trust one photo. Capture a short **burst** (or 3–5 shots with small phone movements, or a 2-second video), measure each frame, reject outliers, and fuse the contours. Show the per-shot spread to the user (and the jury) as a consistency indicator, and ask for another shot when the spread is too large.

## 3. Why it could score

Random errors (edge noise, small focus differences, specular glints) average out; inconsistent shots are detected before they become a wrong answer; and the bonus is delivered by the same code.

## 4. Implementation plan

### 4.1 Files

```
work/strat7/
  fuse.py              # list of contours (mm) → fused contour + stats
  burst_capture.js     # in-app: capture N frames from the video stream at full resolution
  consistency_ui.md    # what the app displays
  eval_fusion.py
```

### 4.2 Capture

- Preferred: `ImageCapture.takePhoto()` (Chrome Android) for full-resolution stills, 3–5 in a row; fallback: grab frames from the `getUserMedia` video at the highest supported resolution (iOS Safari), or multiple file inputs.
- Encourage slight viewpoint changes between shots ("bougez légèrement le téléphone") so perspective-related errors decorrelate.

### 4.3 Fusion

1. Each shot → contour in board coordinates (mm), so all contours share a frame (the lens did not move relative to the board).
2. Quality gates per shot: homography reprojection error, sharpness (variance of Laplacian in the window), mask plausibility.
3. Robust fusion: resample each contour at 720 angles around the common centroid (radius per angle), take the **median radius per angle**, smooth. Or fuse masks by majority vote, then refine edges.
4. Outlier rejection: a shot whose A or B deviates > 2 × MAD from the median is dropped.
5. Outputs: fused A, B, perimeter; per-shot A and B; spread (max − min, and SD).
6. Decision: spread > 0.6 mm → "Mesures incohérentes, reprenez une photo" (and say which factor failed if known).

### 4.4 Optional: rotate-the-lens protocol

Shoot the lens at 0° and rotated 90° on the board; residual anisotropic errors (e.g. perspective along one axis) cancel when both are fused after aligning the contours (rotation estimated by shape registration).

## 5. How to test it

| # | Experiment | Metric | Target |
|---|---|---|---|
| E1 | 8 own lenses: single shot vs fused 3 / 5 shots | MAE A/B vs calliper | fused MAE ≤ 0.8 × single-shot MAE |
| E2 | Spread as an error predictor | correlation between spread and absolute error | positive; threshold catches ≥ 80% of shots with error > 1 mm |
| E3 | Deliberately bad shots in the burst (blur, glare) | fused MAE | unchanged within 0.1 mm (outliers rejected) |
| E4 | Time budget | total time for 2 lenses × 5 shots on a mid-range phone | < 30 s |

## 6. Risks

Users moving the lens between shots breaks the common frame; detect it (contours do not overlap after board alignment) and warn.

## 7. Combines with

Strategy 2 (per-shot measurement), 3 / 5 / 6 (segmenters), 10 (UI and capture), 8 (bias calibration applied after fusion).

## 8. Results log

| Date | Who | Shots | MAE single | MAE fused | Spread threshold | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
