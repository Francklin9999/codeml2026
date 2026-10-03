# OptiFrame · Strategy 13: Two-height capture to measure and remove parallax (3D edge estimation)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 2 (homography, contour), strategy 11 helps (fixed heights) |
| **Rubric lines** | Measurement accuracy (30), Robustness (10) |
| **Differs from 1–10** | Strategy 2 corrects parallax with an **assumed** edge height and camera distance. This **measures** it: two shots at different camera heights (or with a second marker plane at a known height) let us estimate the true height of the lens edge and the camera geometry, then correct each contour point |
| **Work folder** | `optiframe-participants/work/strat13/` |

---

## 1. Context you need

- A point at height *h* above the board plane, seen from a camera at distance *D*, projects (through the board homography) at a position scaled outward from the camera's nadir by about *D / (D − h)*. With h = 3 mm and D = 300 mm the scale error is 1% (≈ 0.5 mm on a 50 mm lens), i.e. about 5 accuracy points.
- Lens edges are not at h = 0: edge thickness (1.5–6 mm), base curve (sag ≈ 3 mm for a 50 mm lens with a ~100 mm radius surface), and which side faces down all matter.

## 2. The idea

1. Take **two shots** of the same, unmoved lens from two camera heights (e.g. 300 mm and 450 mm, using the fixture's two stops, or by hand with the board fully visible).
2. In each shot, compute the board homography and the camera pose (`solvePnP` with approximate intrinsics from EXIF; refine focal length from the board itself).
3. The lens silhouette edge seen from each height shifts differently according to its height *h*: solve per contour point (or per angular sector) for *h* and the true planar position by intersecting the two viewing rays.
4. Use the recovered positions (projected onto the board plane, i.e. what a calliper measures) to compute A and B.

Alternative single-shot variant: add a **second marker plane** raised by a known height (e.g. a transparent sheet with markers on 3 mm spacers around the window); two homographies from one photo give the camera centre, then the edge height from a lens-model assumption.

## 3. Why it could score

It replaces a guess with a measurement and makes the method robust to how the jury places the lens (convex or concave side down) and to the phone distance they happen to use.

## 4. Implementation plan

### 4.1 Files

```
work/strat13/
  pose.py               # board → camera pose and intrinsics estimate (focal from EXIF + board refinement)
  two_view.py           # match contour points by angle around the lens centre; triangulate
  raised_plane.py       # single-shot variant with a second marker plane
  eval_parallax.py
```

### 4.2 Two-view triangulation (per angular sector)

```python
# For sector θ: rays r1, r2 from camera centres C1, C2 through the edge pixels (in board coordinates, z = 0 is the board)
X = least_squares_intersection([C1, C2], [r1, r2])   # 3D edge point (x, y, h)
planar = X[:2]                                       # calliper-equivalent position (orthographic projection)
```

Smooth *h(θ)* (it varies slowly around the lens) before correcting, to limit noise.

### 4.3 Intrinsics

Phones report focal length in EXIF (35 mm equivalent); convert to pixels using the sensor width or calibrate quickly from the board (Zhang's method needs several views; two views at different tilts help). Lens distortion assumed small at the image centre.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Synthetic | simulated two-view projections of a known 3D contour: recovered planar A/B within 0.05 mm |
| T2 | Raised shapes | printed shapes on 2, 4 and 6 mm spacers: recovered height within ± 0.5 mm, planar size error ≤ 0.15 mm |
| T3 | Own lenses | MAE vs calliper: two-view vs single-view with assumed height (strategy 2) |
| T4 | Orientation robustness | convex-down vs concave-down placements give the same A/B within 0.2 mm |
| T5 | UX cost | the extra shot adds ≤ 10 s per lens |

## 6. Risks

Matching contour points between views is the fragile part; using angular sectors around the boxing centre avoids explicit point matching.

## 7. Combines with

Strategy 2 (geometry), 11 (two heights on the fixture), 7 (multi-shot fusion also benefits), 8 (calliper-equivalent definition).

## 8. Results log

| Date | Who | Variant | Height error | MAE (single / two-view) | Notes |
|---|---|---|---|---|---|
| | | | | | |
