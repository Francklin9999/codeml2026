# OptiFrame implementation resumed from Claude's strategy notes

This implements the local foundations of strategies 1, 2 and 3: printable ChArUco board, seeded synthetic photos, metric rectification, classical rim segmentation, sub-pixel outer-edge refinement, A/B/perimeter measurement, explicit optional height correction and a 1:1 SVG export.

It is a Python command-line prototype. Strategy 9 now generates a connected grooved frame STL from two measured contours, with bridge, tenons and geometry validation. The mobile application, canonical anatomical orientation and real-lens/printed-frame validation remain unfinished.

## Run from the repository root

Python 3.10+ with the packages in `optiframe-participants/work/requirements.txt`. Claude's existing `.venv` works on this machine; elsewhere create your own environment and install those requirements. Avoid installing both `opencv-python` and `opencv-contrib-python` into one environment; use the contrib build, which provides `cv2.aruco`.

```powershell
.\.venv\Scripts\python.exe optiframe-participants\work\strat1\make_board.py
.\.venv\Scripts\python.exe optiframe-participants\work\strat2\eval_measure.py --generate
.\.venv\Scripts\python.exe -m unittest discover -s optiframe-participants\work -p test_pipeline.py -v
.\.venv\Scripts\python.exe optiframe-participants\work\strat9\frame.py optiframe-participants\work\_local\evaluation\oval_1\measurement.json optiframe-participants\work\_local\evaluation\rounded_rectangle_1\measurement.json optiframe-participants\work\_local\frame_demo.stl
.\.venv\Scripts\python.exe -m unittest discover -s optiframe-participants\work\strat9 -p test_frame.py -v
```

Generated outputs are ignored by Git under `work/_local/`:

- `board/charuco_board.pdf`: exact nominal scale A4 print and PNG.
- `synthetic/`: photos and independent metric contour labels.
- `evaluation/results.csv`, `evaluation/summary.json`: signed errors, failures, quality metrics and an aggregate summary.
- `evaluation/<case>/`: rectified photo, enhanced rim, binary mask, contour overlay, metric `measurement.json` and `contour.svg`.

Measure a real image:

```powershell
.\.venv\Scripts\python.exe optiframe-participants\work\strat2\measure.py path\to\original-photo.jpg --output optiframe-participants\work\_local\my_lens
```

The default quality gate requires at least 20 ChArUco corners surrounding the lens in all four quadrants and ≤ 0.1 mm RMS reprojection residual. The lens must be complete inside the window; ambiguous shapes or low-contrast rims are rejected with a retake message. A residual is a calibration-fit diagnostic, not an estimate of total measurement accuracy.

## Changes to the proposed geometry

The notes proposed a 9 × 7 board (108 × 84 mm) around an approximately 70 × 55 mm window. That leaves very little visible checkerboard for the strategy-2 requirement of 20 calibration corners. This implementation uses a **13 × 11** board (156 × 132 mm), **12 mm squares**, **9 mm markers**, and an **84 × 60 mm** window aligned to square boundaries. The board and detector use the same specification. Keep the nominal spec unchanged; write a separate measured spec after checking the print.

## What the synthetic test means

The suite contains three shapes at three viewing angles, plus tint, blur, low contrast, a raised lens, an empty window and a missing calibration reference. Images come from a seeded pinhole projection with a known metric contour, illumination gradient and pixel noise. The dark rim is an ideal 0.5 mm stroke; labels describe its outer boundary. There is no learned model and no external data download.

The software estimates the outer half-contrast boundary, then smooths it. It reports boxing dimensions along the board axes and perimeter in millimetres. Real refraction, glare, lens curvature, camera distortion, holes and severe occlusion are not modelled. Synthetic measurements must not be presented as calliper results or jury scores. The evaluator exits nonzero on unexpected acceptance/rejection or A/B MAE above `--max-mae-mm` (default 0.5).

Height correction requires a supplied camera distance, effective rim height and camera nadir in the board plane. The simple similarity correction is intended for a fronto-parallel camera; it is not a calibrated pose-based correction for oblique captures. Do not guess these inputs for real lenses.

Next implementation: validate the rig with physical lenses, add canonical left/right contour orientation, validate the generated frame in a slicer and print, then integrate the pipeline into strategy 10's phone UI. See `strat1/rig_instructions.md` for the unrun physical protocol and `strat9/report.md` for the audited mesh checks.
