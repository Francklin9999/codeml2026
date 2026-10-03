# OptiFrame · Strategy 12: Cross-polarised imaging (LCD screen + polarising filter on the phone)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P3 (experimental; high upside if it works, cheap to test) |
| **Effort** | 2–3 h |
| **Depends on** | strategy 1 (screen-based rig), 2 (rectification) |
| **Rubric lines** | Measurement accuracy (30) on hard (clear, low-power) lenses, Data & AI ingenuity (15), Presentation (10) |
| **Differs from 1–10** | Strategy 1 uses plain backlight and strategy 4 a displayed pattern. This uses the **polarisation** of the laptop's LCD light: with a crossed polariser in front of the phone camera, the background turns dark while the lens edge and stressed lens material can light up, inverting the contrast problem |
| **Work folder** | `optiframe-participants/work/strat12/` |

---

## 1. Context you need

- Most laptop LCD screens emit **linearly polarised** light. Looking at a white LCD through a polariser rotated 90° to the screen's polarisation makes it look nearly black.
- A lens between the screen and the crossed polariser can change the light's polarisation: plastic lenses (polycarbonate, CR-39) often show **stress birefringence** (coloured fringes, strongest near edges and mounting points), and refraction / reflection at the bevel changes polarisation too. Glass lenses may show little.
- Cheap polarisers: **polarised sunglasses** (one lens held in front of the phone camera), or polariser film sheets. The jury would need one too (we would provide it with the rig).
- OLED screens are generally **not** polarised in the same way: test the actual laptop / tablet.

## 2. The idea

Shoot two images of the same scene from the fixed phone position:
1. **Parallel** polariser (normal backlight, background bright).
2. **Crossed** polariser (background dark; lens edge / stressed regions bright).

The crossed image, or the difference / ratio of the two, gives a high-contrast lens mask where plain backlight is weak (clear, low-power lenses with thin edges). Fuse with strategy 3's mask.

## 3. Why it could score

If it works on our lenses, it is a striking, low-cost physical trick (memorable for the jury) and a robust segmentation cue. If it does not, we learn it in 2 hours.

## 4. Implementation plan

### 4.1 Files

```
work/strat12/
  feasibility.md        # photos: which screens and lenses show contrast
  polar_segment.py      # crossed / parallel images → mask
  eval_polar.py
```

### 4.2 Steps

1. **Screen check:** look at the white `/lightbox` page through a polarised sunglass lens while rotating it: if the screen darkens strongly at some angle, the screen is polarised; note the angle (usually 0°, 45° or 90°).
2. **Lens survey:** for 8 own lenses (plastic and glass, plus and minus), take crossed and parallel shots; record visually where contrast appears (edge only, whole lens, fringes).
3. **Segmentation:** normalise both images; compute `C = crossed / (parallel + ε)` or simply threshold the crossed image; morphological cleanup; outer contour; refine edges in the **parallel** image (strategy 2's sub-pixel step), using the polarised mask only as the region prior.
4. **Fusion:** where strategy 3's backlit mask is uncertain (weak rim), use the polarised mask; agreement as a confidence measure.

### 4.3 Practical holder

A clip that holds the polariser over the phone camera and rotates in 90° steps (3D printed, or tape + cardboard for the test).

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Screen polarisation | ≥ 10× darker background when crossed (measure mean grey level) |
| T2 | Lens visibility | in the crossed image, the lens outline is visible for ≥ 6 of 8 lenses |
| T3 | Accuracy | on lenses where strategy 3 struggles, MAE with polarised prior < MAE without |
| T4 | Jury feasibility | a stranger can mount the polariser clip and get the crossed angle right in < 30 s with an on-screen guide |

**Kill:** if T1 or T2 fails on the laptops we will bring, stop and document it as a tested negative result (still a nice Data & AI slide).

## 6. Risks

Depends on screen type and lens material; the jury's setup must use our laptop / tablet, so bring a screen confirmed to work.

## 7. Combines with

Strategy 1 (light box), 3 (fusion), 4 (alternative physical cue), 6 (extra input channel for training).

## 8. Results log

| Date | Who | Screen | Lenses visible | MAE gain | Verdict |
|---|---|---|---|---|---|
| | | | | | |
