# OptiFrame · Strategy 20: Smartphone lens-power estimate and pairing assistant for recycled lenses

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P3 (beyond the rubric; strong humanitarian and presentation value) |
| **Effort** | 4–6 h |
| **Depends on** | strategy 1 (screen rig), strategy 4 (pattern-distortion measurement) |
| **Rubric lines** | Presentation (10: impact and vision), Data & AI (15: ingenuity), bonus potential for the post-hackathon test with SN-SF |
| **Differs from 1–10** | Strategy 4 uses pattern distortion only to **find the lens outline**. This uses the same physics to **estimate the lens's optical power** (sphere, and possibly cylinder and axis), and builds a helper that matches recycled lenses to a prescription and to each other (left / right pairs) |
| **Work folder** | `optiframe-participants/work/strat20/` |

---

## 1. Context you need

- The brief's humanitarian context: recycled lenses each have their own shape **and power**; a prescription may pair two different lenses. Today an optician uses a lensmeter (focimeter) to read power. SN-SF wants to replace expensive optician equipment with a smartphone.
- Physics: a lens of power P (dioptres) placed at distance d from a patterned screen, viewed from distance L, magnifies (plus) or minifies (minus) the pattern seen through it. The apparent magnification depends on P, d and L; an astigmatic lens magnifies differently along two axes (cylinder and axis). Raising the lens above the screen by a known spacer makes the effect measurable.
- **Medical caution:** this would be a screening / sorting aid, not a certified measurement; any real use needs validation by professionals.

## 2. The idea

1. Place the lens on a spacer of known height (e.g. 20 mm) above the screen showing a fine grid; photograph from the fixed height (strategy 11).
2. Measure the local magnification of the grid inside the lens (along many directions) relative to outside (strategy 4's flow / phase methods).
3. Fit a thin-lens model to get **sphere**, and from the anisotropy of magnification, **cylinder and axis**.
4. **Pairing assistant:** store measured lenses (shape + estimated power) in a small local inventory; given a prescription (entered by an optician, no personal data stored), suggest left / right candidates whose powers are within tolerance and whose shapes fit a common frame (strategy 9 handles different shapes).

## 3. Why it could score

It shows the jury the bigger vision (sorting thousands of donated lenses quickly), reuses components we already build, and is a natural topic for SN-SF's November test with specialists. It does not replace the scored measurement work, so keep it behind a "Labo / expérimental" toggle.

## 4. Implementation plan

### 4.1 Files

```
work/strat20/
  optics_model.py       # thin-lens magnification model with spacer d, camera distance L
  power_estimate.py     # magnification field → sphere / cylinder / axis fit
  calibration.md        # spacer, distances, grid pitch; calibration with known lenses
  inventory.py          # local lens inventory (shape + power estimate + confidence)
  pairing.py            # prescription → candidate pairs within tolerances
  eval_power.py
```

### 4.2 Calibration

Use lenses of **known power** (e.g. reading glasses marked +1.0, +1.5, +2.0, +2.5; and minus lenses if available, labelled by an optician or from packaging) to fit the model's unknowns (effective distances) and check linearity.

### 4.3 Model fit

Measure magnification m(φ) along directions φ inside the optical-centre region; fit `m(φ) = m_s + m_c·cos²(φ − axis)`; convert m_s, m_c to sphere and cylinder with the calibrated model. Report uncertainty from the fit residuals and multi-shot spread.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Sphere on known lenses | absolute error ≤ 0.25 D on calibration lenses (leave-one-out) |
| T2 | Sign | plus vs minus correctly identified for 100% of test lenses |
| T3 | Cylinder (if astigmatic test lenses exist) | axis within ± 10°, cylinder within ± 0.5 D |
| T4 | Pairing | on a synthetic inventory, the assistant returns pairs within tolerance and ranks by fit |
| T5 | Safety messaging | the UI clearly labels results as estimates to be confirmed by a professional |

## 6. Risks

Accuracy may be insufficient for clinical use; present it as sorting / triage support with measured error, never as a prescription tool.

## 7. Combines with

Strategy 4 (pattern measurement), 11 (fixed geometry), 9 (frames for two different lenses), presentation.

## 8. Results log

| Date | Who | Lenses tested | Sphere MAE | Sign accuracy | Notes |
|---|---|---|---|---|---|
| | | | | | |
