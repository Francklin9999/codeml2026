# OptiFrame · Strategy 8: Boxing-system measurement, lens orientation and bias calibration

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (definitions decide whether our number matches the jury's calliper) |
| **Effort** | 2–3 h |
| **Depends on** | strategy 2 (contour in mm) |
| **Rubric lines** | Measurement accuracy (30), Generated frame (10: correct nasal / temporal orientation) |
| **Work folder** | `optiframe-participants/work/strat8/` |

---

## 1. Context you need

The jury measures A (width) and B (height) with a **calliper** using the **boxing system** (ISO 8624: the rectangle enclosing the lens, with sides parallel to the horizontal reference line of the lens). Convention in the brief: the nasal side faces the centre of the frame; the app lets the user choose the eye (left / right) for each lens. A calliper measures the **maximum physical extent** between parallel jaws, so if our axis differs from theirs, B and A shift even with a perfect contour.

## 2. The idea

Make the definition of A and B explicit and robust:

1. **Orientation:** define the horizontal axis from the rig (the printed guide line under the lens) and, as a cross-check, from the shape (minimum-area rectangle / principal axes / max-width direction).
2. **Calliper-equivalent measurement:** compute widths as the maximum projection extent between parallel lines (rotating calipers), exactly what a calliper does.
3. **Bias calibration:** with our own lenses, fit the residual systematic difference between our measurement and the calliper (edge definition, bevel), and apply it.

## 3. Why it could score

The effect of an axis error depends on the shape. For a rectangle-like 52 × 38 mm lens, a 3° axis error inflates B by up to 52·sin 3° + 38·(cos 3° − 1) ≈ 2.7 mm; for an ellipse of the same size the change is only ≈ 0.05 mm. Real lenses (rounded rectangles) fall in between, so orientation matters a lot for squarish shapes. Add a constant edge-definition bias of 0.3–0.5 mm and definition errors alone can cost several of the 30 accuracy points. Both are cheap to fix.

## 4. Implementation plan

### 4.1 Files

```
work/strat8/
  boxing.py          # contour + axis → A, B, boxing centre, perimeter, ED (effective diameter)
  orientation.py     # axis from guide line / shape; nasal side handling
  calibrate_bias.py  # fit measured vs calliper on own lenses
  bias.json          # fitted parameters (shipped with the app)
  eval_boxing.py
```

### 4.2 Measurements

```python
def extent(contour_mm, theta):           # width of the contour projected on direction theta
    u = np.array([np.cos(theta), np.sin(theta)])
    p = contour_mm @ u
    return p.max() - p.min()
A = extent(c, theta_h)                   # horizontal
B = extent(c, theta_h + np.pi/2)         # vertical
ED = 2 * max(np.linalg.norm(c - box_centre, axis=1))   # effective diameter, useful for blank-size checks
```

### 4.3 Orientation strategies to compare

| Method | Description |
|---|---|
| O1 rig guide | the user aligns the lens's horizontal axis with the printed line; θ_h = board x-axis |
| O2 min-area rectangle | `cv2.minAreaRect`; θ = the side closest to the board x-axis |
| O3 principal axes | PCA of the contour |
| O4 max-width | direction of maximum extent |

Default: O1 (matches how a human would hold the lens in the calliper), and show a warning if O1 and O2 differ by > 5° ("verre peut-être mal aligné sur la ligne").

### 4.4 Eye and nasal side

The user picks the eye; the nasal side is the side facing the guide arrow. Store the contour in a canonical frame (nasal side towards +x for the right eye, mirrored for the left) so strategy 9 builds rims with the right orientation.

### 4.5 Bias calibration

For ≥ 8 own lenses: `A_cal ≈ a0 + a1·A_meas`, `B_cal ≈ b0 + b1·B_meas` (or a single offset if slopes are ≈ 1). Use leave-one-lens-out cross-validation to estimate the error after calibration. Only keep the correction if it reduces LOO MAE. Store in `bias.json` with the date, phones used and lens count.

## 5. How to test it

| # | Experiment | Metric | Target |
|---|---|---|---|
| E1 | Calliper protocol | 3 people measure the same 8 lenses | inter-person SD (our GT noise floor) |
| E2 | Orientation methods O1–O4 | MAE A/B vs calliper | choose the best; O1 expected |
| E3 | Rotations: place each lens at +5° / −5° off the guide | MAE with O1 vs O2 | quantify sensitivity; warn threshold |
| E4 | Bias calibration LOO | MAE before / after | after < before, else drop calibration |
| E5 | Final | MAE on A and B over all own lenses | ≤ 0.5 mm |

## 6. Risks

The jury's calliper habits are unknown. In the presentation, state the convention used ("boxing, axe horizontal = ligne guide") and show both numbers if the shape is ambiguous.

## 7. Combines with

Strategy 2 (contour), 7 (fused contour), 9 (canonical orientation for rims), 10 (UI for eye choice and alignment warning).

## 8. Results log

| Date | Who | Orientation | Bias model | MAE A | MAE B | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
