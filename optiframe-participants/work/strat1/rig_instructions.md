# Assemble the OptiFrame capture rig

The software and synthetic checks work locally. Physical print scale, real lens accuracy, phone diversity and reassembly time are **NOT RUN**.

1. Print `_local/board/charuco_board.pdf` on A4 at **100%**, with fit-to-page disabled. Keep the board flat. Measure the 72 mm verification span; it should be 72.0 ± 0.2 mm. Record three measurements.
2. Prefer transparency film or tracing paper. With opaque paper, cut out only the central white 84 × 60 mm window. Keep the surrounding squares and markers intact. Do not write a placement line through the measurement window.
3. Lay the board on a diffuse white light source. A tablet or a safely supported laptop screen can provide the backlight. Avoid bending the screen or pressing a lens against it. A protective transparent sheet changes the height of the lens relative to the calibration plane and needs its own validation.
4. Place **one lens** inside the window, with its concave side down. Align its horizontal boxing axis with the board's horizontal edges. The software uses this axis; it does not infer the anatomical nasal side or rotate lenses automatically.
5. Hold the phone about 400 mm above the board. Include the entire marker frame and keep the image sharp. Transfer the original-resolution image. Leave at least 2 mm between the lens rim and the window boundary.
6. Run the measurement command in `../README.md`; inspect the contour overlay before using the measurements. Repeat for the second lens. Keep real calliper measurements separate from simulated ground truth.

## If the print scale differs

From the repository root, using your actual measured span:

```powershell
.\.venv\Scripts\python.exe optiframe-participants\work\strat1\scale_check.py --measured-span-mm 72.72 --write-spec optiframe-participants\work\_local\measured_board_spec.json
```

The number above is an **example**, not a physical measurement. Pass the resulting specification to `measure.py --spec`. It rescales squares, markers and the window together. Never mark the nominal source specification as physically verified without measuring its print.

## Physical validation still required

- Three new users assembling the rig in under two minutes.
- Printed 50 mm circle and 55 × 40 mm rectangle, ten views, A/B MAE ≤ 0.15 mm.
- At least eight real lenses, five photos each, multiple phones, measured independently with a calliper. Target A/B MAE ≤ 0.5 mm and maximum error ≤ 1 mm.
- Clear, tinted, thick-edge and thin-edge lenses; lighting and glare stress tests.
- Print the contour SVG at 100% and verify its 50 mm scale bar.
