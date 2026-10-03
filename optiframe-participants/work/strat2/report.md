# OptiFrame foundation results — 2026-10-03

All results below come from **synthetic images**, not real lens measurements. Strategies 1–3 remain IN PROGRESS because physical tests and phone integration are incomplete.

## Reproduction

From the repository root:

```powershell
.\.venv\Scripts\python.exe optiframe-participants\work\strat2\eval_measure.py --generate
.\.venv\Scripts\python.exe -m unittest discover -s optiframe-participants\work -p test_pipeline.py -v
```

Environment used: OpenCV 5.0.0 (aruco present), NumPy 2.1.2, ReportLab 5.0.1. The implementation uses the modern OpenCV ChArUco detector API. Requirements and run instructions are in `work/README.md`.

## Final results

| Check | Result |
|---|---|
| Zero-height measurement cases | 12/12 measured |
| Combined width/height MAE, zero-height cases | 0.080234 mm |
| Maximum width/height absolute error | 0.312796 mm (blurred case) |
| Raised lens at 3 mm | Measured; uncorrected A/B errors +0.440025 / +0.369844 mm |
| Raised lens after supplied height correction | A/B errors +0.020475 / +0.063320 mm |
| Empty window | Rejected |
| Missing calibration markers | Rejected |
| Unexpected failure / acceptance | 0 / 0 across 15 cases |
| Unit/integration checks | 6 passed |
| Printable board PDF | Generated, A4 page checked, rendered layout visually inspected |
| Tilted contour overlay | Visually inspected |
| Physical lens, printer scale, reassembly and phone tests | NOT RUN |

The MAE is the mean over 24 absolute errors (A and B on twelve zero-height cases). The raised case is separate because height adds a known geometric bias. No simulated result has been converted into an official jury score.

The geometry generator first draws an ideal 0.5 mm rim between explicit inner and outer metric polygons. Labels use the outer contour, independently of the detector. An early version used OpenCV stroke thickness for rendering, which introduced a raster-dependent width inconsistent with the analytic labels; it was replaced before recording these results. The fixed test suite was used during development, so it is not an independent held-out physical evaluation.

## Remaining limitations

- A/B are measured in board axes; correct lens placement is required. Canonical orientation is not implemented.
- The simple parallax correction needs externally supplied height, distance and nadir and is valid for the demonstrated fronto-parallel setup. No phone intrinsics or camera pose are estimated.
- The classical segmenter requires one complete, sufficiently large, mostly convex rim. Small children's lenses, severe glare, holes, notches and partial visibility have not been validated.
- SVG output uses millimetre units and a 50 mm scale bar. Physical print scaling remains unverified.
- No mobile UI, STL frame, browser port, learned segmentation model or physical test results are included.

See `error_budget.md` for why a small reprojection residual does not establish real-lens accuracy.
