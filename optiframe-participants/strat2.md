# OptiFrame · Strategy 2: Metrology pipeline (ChArUco homography, sub-pixel edges, parallax correction, error budget)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (the 30 accuracy points live here) |
| **Effort** | 4–6 h |
| **Depends on** | strategy 1 (rig and board spec) |
| **Rubric lines** | Measurement accuracy (30), Robustness (10), Contour SVG 1:1 (5) |
| **Work folder** | `optiframe-participants/work/strat2/` |

---

## 1. Context you need

Accuracy score: MAE on A and B over the jury's 2 lenses; **30 pts at ≤ 1 mm, linearly down to 0 at 4 mm**. Each mm of systematic error costs ~10 points. The jury measures A and B with a calliper using the **boxing system** (ISO 8624: the rectangle that encloses the lens; A = horizontal width, B = vertical height).

## 2. The idea

Treat measurement as metrology, not just "detect a marker and divide": precise homography from many ChArUco corners, sub-pixel edge localisation, explicit **parallax correction** for the lens's height above the board, and an **error budget** that tells where the remaining error comes from.

## 3. Why it could score

With a decent rig, the dominant errors are systematic (scale, perspective, height above the plane, edge definition), and they are correctable. Getting from ~1.5 mm to ~0.4 mm MAE is the difference between ~25 and 30 points.

## 4. Implementation plan

### 4.1 Files

```
work/strat2/
  measure.py          # image → rectified image, contour in mm, A, B, perimeter
  homography.py       # ChArUco detection + refinement
  edges.py            # sub-pixel contour refinement
  parallax.py         # height correction
  error_budget.md     # measured contributions
  eval_measure.py     # vs calliper GT of our own lenses
  data/own_lenses.csv # lens_id, A_mm, B_mm, perimeter_mm (if measurable), thickness_edge_mm, base_curve
```

### 4.2 Homography

1. Detect markers (`cv2.aruco.ArucoDetector`), interpolate ChArUco corners (`cv2.aruco.CharucoDetector` in OpenCV ≥ 4.7), refine with `cv2.cornerSubPix`.
2. Fit the homography from ≥ 20 corners with RANSAC, then refine with Levenberg–Marquardt (`cv2.findHomography(..., cv2.RANSAC)` then `cv2.findHomography(..., 0)` on inliers).
3. Rectify to a metric image at a fixed resolution (e.g. **20 px/mm**) with `cv2.warpPerspective` (Lanczos).
4. Report reprojection error (px and mm) as a quality metric; reject the photo with a clear message if > 0.1 mm.

Optional: lens distortion. Phone images are already undistorted by the ISP in most cases; check by fitting a homography on the whole board and looking at residual patterns. If residuals are systematic (barrel), calibrate per phone model with `cv2.calibrateCameraCharuco` from 10 shots (not possible on the jury's phone in advance → prefer keeping the lens near the image centre and the board small in the frame).

### 4.3 Parallax (height) correction

The homography is valid **in the board plane**. Points above it are magnified: a point at height *h* above the plane, seen from a camera at distance *D*, is displaced outward by a factor ≈ *D / (D − h)* relative to the principal point's projection.

- Typical numbers: rim at h = 3 mm, D = 300 mm → 1% scale error → **0.5 mm** on a 50 mm lens. Too much.
- Mitigations, in order:
  1. Place the lens **concave side down** so the rim rests on the board (h ≈ 0 for the rim's bottom edge); the silhouette's outer extent is set by the rim edge.
  2. Shoot from further away (D ≥ 400 mm) or use the phone's **2×/3× telephoto** if available (smaller perspective effects).
  3. Correct: estimate *h* of the silhouette edge (edge thickness ~1.5–6 mm depending on power; half of it as the effective height) and *D* from the homography (camera pose via `cv2.solvePnP` on board corners with an approximate intrinsics guess from EXIF focal length), then scale contour points toward the camera's nadir by *(D − h)/D*.
  4. Calibrate the residual bias empirically (strategy 8).

### 4.4 Sub-pixel contour

On the rectified backlit image: coarse mask (strategy 3 or 5) → for each contour point, sample the intensity profile along the normal (±1 mm), fit an error function (or take the 50% crossing of the dark-rim profile) → sub-pixel edge position. Smooth the contour with a low-order Fourier series (≤ 30 harmonics) or Savitzky–Golay.

Decide and document **which edge** is measured: backlit lenses show a dark band at the rim (total internal reflection at the bevel). The calliper measures the **outer** extent, so use the outer boundary of the dark band.

### 4.5 Measurements

- A, B: boxing rectangle axis-aligned to the lens's horizontal reference (strategy 8 decides the axis), in mm.
- Perimeter: length of the smoothed contour.
- Also output the contour polygon in mm (shared with the frame generator and the SVG export).

### 4.6 SVG 1:1 export

`<svg width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">` with the contour path in mm; add a 50 mm scale bar and the text "Imprimer à 100 %". Test by printing and measuring the scale bar.

## 5. How to test it

### 5.1 Ground truth

Collect ≥ 8 own lenses (team glasses, cheap reading glasses, sunglasses; pop lenses out of cheap frames). Calliper A and B three times each (boxing: lens on a flat surface, horizontal axis defined by the guide line); record the median. Record edge thickness.

### 5.2 Experiments

| # | Experiment | Metric | Target |
|---|---|---|---|
| E1 | Printed shapes in the window (no height) | MAE A/B | ≤ 0.15 mm |
| E2 | Same printed shape raised by 3 mm spacers | error with / without parallax correction | correction removes ≥ 80% of the bias |
| E3 | Own lenses, concave side down vs convex side down | MAE | concave-down clearly better |
| E4 | Distance 250 / 350 / 450 mm, 1× vs 2× camera | MAE | pick the protocol |
| E5 | Own lenses, final pipeline, 5 shots each, 3 phones | MAE on A and B, max error | **MAE ≤ 0.5 mm**, max ≤ 1.0 mm |
| E6 | SVG print | printed scale bar | 50.0 ± 0.2 mm |

### 5.3 Error budget (`error_budget.md`)

Estimate each contribution separately (homography residual, edge localisation, parallax, segmentation, calliper repeatability) and check they add up (in quadrature for random parts) to the measured MAE.

### 5.4 Acceptance / kill

**Adopt** when E5 passes. If MAE stays > 1 mm, the first suspects are edge definition (which boundary) and parallax: re-run E2/E3 before touching segmentation.

## 6. Risks

Jury lenses may be unusual (high plus, high minus, tinted, progressive). Include at least one of each in the own-lens set if possible.

## 7. Combines with

Strategy 1 (rig), 3 / 4 / 5 / 6 (coarse masks), 7 (multi-shot), 8 (axis choice and bias calibration), 9 (contour → frame), 10 (runs in the browser).

## 8. Results log

| Date | Who | Experiment | MAE A | MAE B | Max err | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
