# OptiFrame · Strategy 11: Mechanical capture fixture (printable / cardboard phone stand + lens tray with alignment stops)

| | |
|---|---|
| **Status** | NOT STARTED *(set to IN PROGRESS / DONE / ABANDONED with your name and the date)* |
| **Priority** | P2 |
| **Effort** | 3–5 h (design 1–2 h, print or cut 1–2 h, validation 1 h) |
| **Depends on** | strategy 1 (board spec) |
| **Rubric lines** | Measurement accuracy (30), Robustness (10: repeatable shots), Presentation (10: rig reassembled by the jury in < 2 min) |
| **Differs from 1–10** | Strategy 1 designs the optical setup (backlight + ChArUco board). This designs the **mechanics**: a stand that fixes the phone's height and keeps it parallel to the board, and a tray that positions the lens and its horizontal axis, removing hand-held variability |
| **Work folder** | `optiframe-participants/work/strat11/` |

---

## 1. Context you need

- Rubric: measurement accuracy 30 (MAE on A and B of the jury's 2 lenses: 30 pts at ≤ 1 mm, 0 at 4 mm); robustness 10; the jury **reassembles our capture rig in < 2 minutes** and uses **their own phone**.
- Main error sources (strategy 2): perspective tilt, distance (parallax of the lens edge above the board), lens orientation (strategy 8), motion blur.
- No equipment is provided; the brief suggests a laptop screen as a light box and a printed board.

## 2. The idea

A fixture with two parts:
1. **Phone bridge:** a stand that holds any phone (width 65–80 mm, adjustable clamp or a simple ledge with a rubber band) **parallel** to the board at a fixed height (e.g. 350 mm, chosen from strategy 2's distance experiment), with the camera hole above the window. Works for both camera positions (top-left on iPhones, top-centre on many Androids) via a sliding plate.
2. **Lens tray:** a thin frame that sits on the board and has two **alignment stops**: a straight edge for the lens's horizontal reference and a nasal stop, so A / B are measured along the right axis (strategy 8).

Materials: 3D printed (PLA, flat-packed parts with snap joints) **or** laser-cut / hand-cut cardboard (fallback if no printer), plus the printed ChArUco board.

## 3. Why it could score

Fixed geometry turns most systematic errors into constants that strategy 8's calibration removes, and makes the jury's shots as good as ours regardless of their skill. The fixture itself is a good presentation object.

## 4. Implementation plan

### 4.1 Files

```
work/strat11/
  fixture.scad (or .py with CadQuery)   # parametric: phone width range, height, window size
  stl/                                  # exported parts
  cardboard_template.pdf                # 1:1 cut template (fallback)
  assembly_steps.md                     # 5 steps with photos, target < 2 min
  validation.md
```

### 4.2 Design parameters

| Parameter | Default | Note |
|---|---|---|
| Camera height above board | 350 mm | from strategy 2 E4; trade-off resolution vs parallax |
| Window | 75 × 60 mm | fits lenses up to ~70 mm |
| Legs | 4, foldable | stable on a laptop keyboard deck or a table |
| Phone plate | sliding, 0–40 mm lateral | aligns the lens of any phone above the window |
| Tray stops | 1 mm high | low enough not to shadow the lens edge |

Use OpenSCAD or CadQuery so the parts are parametric and the STL is reproducible; print flat, no supports.

### 4.3 Assembly target

1) unfold legs; 2) place board on the light box; 3) put tray on the board's window; 4) set phone on the plate, slide until the window is centred in the preview; 5) shoot. Rehearse with strangers.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Parallelism | homography-derived camera tilt (from `solvePnP`) ≤ 2° across 10 placements of the phone |
| T2 | Repeatability | same lens, 10 shots with the phone removed and replaced each time: SD of A and B ≤ 0.1 mm |
| T3 | Accuracy | MAE vs calliper on 8 own lenses, fixture vs hand-held: fixture better |
| T4 | Phone diversity | 3 phone models (incl. one iPhone) fit and pass T1 |
| T5 | Assembly | 3 people who never saw it assemble in < 2 min using `assembly_steps.md` |
| T6 | Transport | survives being packed and unpacked 5 times |

## 6. Risks

Printing time and failed prints: start with the cardboard version, print in parallel.

## 7. Combines with

Strategy 1 (optics), 2 (geometry), 8 (orientation from the tray stop), 7 (consistent multi-shots).

## 8. Results log

| Date | Who | Version | Tilt | Repeatability SD | MAE | Assembly time | Notes |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
