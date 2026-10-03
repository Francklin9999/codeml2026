# OptiFrame · Strategy 4: Refraction-pattern segmentation (screen-displayed pattern + distortion map)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (differentiating idea, moderate risk) |
| **Effort** | 4–5 h |
| **Depends on** | strategy 1 (screen-based rig), 2 (rectification) |
| **Rubric lines** | Measurement accuracy (30), Robustness (10), Data & AI ingenuity (15), Presentation (10) |
| **Work folder** | `optiframe-participants/work/strat4/` |

---

## 1. Context you need

A corrective lens **bends light**: anything seen through it is magnified or minified and shifted. In plain light the lens is nearly invisible, but a **known background pattern** seen through it is visibly distorted. Our rig already puts the lens on a screen we control (strategy 1's `/lightbox` page), so we can display any pattern we want behind it.

## 2. The idea

Display a high-frequency pattern (fine stripes, a checkerboard, or random dots) on the screen under the lens. Inside the lens, the pattern is distorted; outside, it is not. Compute a **distortion map** between the observed pattern and the expected one; the lens is exactly the region where the map is non-zero, and its border is a sharp discontinuity. Two variants:

- **Two-shot:** pattern photographed without the lens (reference) and with the lens, same phone position (phone on a stand). Dense optical flow between the two rectified images.
- **One-shot:** the pattern is known analytically (e.g. sinusoidal stripes at known frequency in two orientations shown in two quick frames, or a random-dot pattern stored in the app); compute local phase / frequency deviation from the known pattern (Fourier-transform profilometry style).

Bonus: the magnification inside the lens is related to its **optical power**, so the same data could estimate the lens power (out of scope for scoring, great for the presentation, and useful to SN-SF).

## 3. Why it could score

It works even for perfectly clear lenses with faint rims, and it uses physics rather than appearance, which makes a memorable "ingenuity" story for the Data & AI and presentation criteria.

## 4. Implementation plan

### 4.1 Files

```
work/strat4/
  patterns.py            # generates stripes / checker / random dots (also served by the app at /lightbox?mode=...)
  flow_segment.py        # two-shot: rectified ref + lens images → flow → mask
  phase_segment.py       # one-shot: known pattern → local phase deviation → mask
  eval_refraction.py
```

### 4.2 Patterns

- Random dots: 1–2 px dots at ~30% density, pre-blurred by 0.5 px to avoid aliasing; good for dense flow.
- Sinusoidal stripes: period ~1.5–3 mm on the board plane (check the camera resolves them at 20 px/mm), shown horizontally then vertically (2 frames).
- Avoid moiré with the screen's pixel grid: pattern period not close to a multiple of the screen pixel pitch; slight defocus helps.

### 4.3 Two-shot pipeline

1. Rectify both images with the board homography (strategy 2), crop to the window.
2. Dense optical flow: `cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)` or Farnebäck; or RAFT (PyTorch) offline for comparison.
3. Flow magnitude map → smooth → threshold (Otsu) → largest component → fill holes.
4. Edge: the flow field is discontinuous at the rim; refine the contour at the strongest flow-gradient magnitude along normals.
5. Hand-held variant: register the two shots by the board first; the residual flow outside the window should be ~0 (use it as a quality check).

### 4.4 One-shot pipeline

For sinusoidal stripes along x: band-pass the rectified image around the known frequency (FFT), compute the analytic signal (Hilbert transform along x) → phase; subtract the expected linear phase → deviation map; repeat for y. Lens region = high deviation. Simpler variant: local frequency estimation in sliding windows (period differs inside the lens).

### 4.5 Integration

Use as (a) the primary segmenter when the backlit rim is weak, or (b) a second opinion fused with strategy 3 (agreement as a confidence measure).

## 5. How to test it

| # | Experiment | Metric | Target |
|---|---|---|---|
| E1 | Feasibility: one clear lens, two-shot, tripod | visual mask quality | rim clearly visible in the flow magnitude map |
| E2 | 8 own lenses × 3 shots, two-shot | A/B MAE vs calliper; boundary error vs strategy 3 | MAE ≤ 0.6 mm |
| E3 | Low-power lenses (±0.5 D) | detection rate | ≥ 90% detected (weak refraction is the hard case) |
| E4 | One-shot stripes | MAE | within 0.2 mm of two-shot |
| E5 | Hand-held two-shot | MAE degradation | ≤ +0.2 mm vs tripod |
| E6 | Fusion with strategy 3 | MAE and failure rate | better than either alone |

**Kill:** if E3 fails (low-power lenses invisible) and E2 is not better than strategy 3, keep it only as a presentation demo.

## 6. Risks

- Near-zero-power lenses produce little distortion; the rim (prism at the bevel) still distorts strongly, so the border may still be found even if the interior is not.
- Requires the phone and pattern screen to stay put between two shots (two-shot variant).

## 7. Combines with

Strategy 1 (pattern on the light box), 2 (rectification and refinement), 3 (fusion), 6 (flow maps as an extra input channel), 10 (pattern modes in the `/lightbox` page).

## 8. Results log

| Date | Who | Variant | MAE A / B | Low-power detection | Notes |
|---|---|---|---|---|---|
| | | | | | |
