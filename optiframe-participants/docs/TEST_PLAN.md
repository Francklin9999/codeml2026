# OptiFrame: test plan

> **Purpose:** the only place where real-world numbers live. A figure quoted anywhere else (README, pitch, demo) must point to a filled row here.
> **State:** every results cell below is empty. Nothing has been measured on a real lens, a real phone or a real printer. Fill a cell only from a run you made, with the date and your initials.
> **Read with:** [`COLLECTE_DONNEES.md`](COLLECTE_DONNEES.md) (what to shoot, in French), [`ARCHITECTURE.md`](ARCHITECTURE.md).

## 1. Calliper protocol (ground truth)

1. Give every lens an identifier (`L01`, `L02`, ...) **written on its bag, never on the lens**. Identifiers use letters, digits and hyphens only (no underscore: it separates the fields of a file name).
2. Lay the lens flat, aligned on the guide line of the sheet: that line is the horizontal of the boxing system. A = width of the enclosing rectangle, B = its height.
3. **Three readings of A and three of B**, jaws parallel to the axes, light pressure, the lens put down again between two readings. The reference is the median of the three (this is what `tools/accuracy_report.py` uses).
4. Write the six readings, the edge thickness and the tint in `data/own_lenses.csv` (columns of [`../data/own_lenses.template.csv`](../data/own_lenses.template.csv): `lensId, description, A_mm_1, A_mm_2, A_mm_3, B_mm_1, B_mm_2, B_mm_3, edge_thickness_mm, tint, notes`; delete the two EXAMPLE rows), or type them in `collect.html`, mode Validation, which exports the same file.
5. If possible a second person repeats the readings without seeing the first ones: the spread between people is the noise floor of the reference.
6. Mounted glasses (SN-SF stand, they stay at the stand): A and B of each opening and the distance between lenses, without dismantling anything.

## 2. Test matrix

| Set | Lenses | Phones | Repetitions | Conditions | Purpose |
|---|---|---|---|---|---|
| A. Validation | 8 minimum, 15 aimed; clear, tinted, plus, minus, several shapes and sizes | 1 minimum, 2 aimed (one iPhone, one mid-range Android) | 3 per lens and phone, sheet and phone put down again at least once | backlit rig, phone flat at 35 to 45 cm | MAE of A and B, bias, repeatability, predicted score |
| A'. Stress | 4 of the lenses | same | 1 each | tilt 10° and 20°; distance 30 and 50 cm; room light only; window light | robustness to angle and lighting |
| B. Paired capture | 8 minimum, 15 aimed | 1, fixed on a stand | 3 to 6 positions per lens | `easy` first, then `room`, `lampL`, `lampT`, `lampR`, `flash`, `pattern`, `colour` | training set without manual labels |
| C. Mounted glasses | the pairs of the SN-SF stand | 1 | 3 photos per pair | plain background; on the sheet when the pair fits | **must not crash**: a measurement or a clear sentence |
| D. Wanted failures | none or any | 1 | 10 photos | sheet cut off, sheet very tilted, blurred, hand in the frame, flash glare, lens past the window, lens rotated 10°, empty window | every failure gives a French sentence, never a technical error |
| E. Devices | demo pair | Android Chrome, iOS Safari, one other browser, laptop Chrome (`lightbox.html`) | 1 full flow each | fresh phone, no cache, opened by QR | web-app criterion |

File names: set A `<lensId>_<phone>_<rep>.jpg`; set B `<lensId>_<pos>_<cond>.jpg`; set C and D `<label>_<n>.jpg`. `collect.html` writes them. Original files only, never through WhatsApp.

## 3. Acceptance thresholds

| # | What | Threshold | Source | Checked with |
|---|---|---|---|---|
| Q1 | MAE of A and B on our own lenses, internal target | ≤ 0.5 mm | SN-SF mentor (ISO 12870) | `tools/accuracy_report.py` |
| Q2 | MAE of A and B, gate G2 and full marks of the rubric | ≤ 1.0 mm | CHALLENGE §4 | `tools/accuracy_report.py` |
| Q3 | Spread of A or B between shots of one lens | ≤ 0.6 mm (`MAX_SPREAD_MM = 0.6`, `quality/fuse.ts`) | brief 07 | result screen, `quality` in `mesures.json` |
| Q4 | Shift of the box centre between shots of one lens | ≤ 1.0 mm (`MAX_CENTRE_SHIFT_MM = 1.0`) | brief 07 | `INCONSISTENT_SHOTS` on set D |
| Q5 | Printed SVG scale bar | 50.0 ± 0.2 mm | printed scale bar | calliper on the print, from Chrome and from Safari |
| Q6 | Printed reference sheet ruler | 100 mm; otherwise `rig/set_print_scale.py <measured mm>` (accepted 0.97 to 1.03) | brief 02 | calliper |
| Q7 | STL | passes `tools/validate_stl.py` (watertight, winding consistent, single body, positive volume) **and** opens in a slicer with no error | CHALLENGE §4 | script and slicer |
| Q8 | Rig set up by a stranger from the instruction sheet | under 2 minutes | CHALLENGE §3 | stopwatch, 3 people |
| Q9 | A pair of lenses processed | under 30 s on a mid-range phone | CHALLENGE §5 | "Pas à pas" timings |
| Q10 | Mounted glasses and wanted failures | no crash, no technical text on screen | CHALLENGE §4 | sets C and D |

Constants in the code that these tests must confirm or move (all provisional, set on synthetic scenes or the 10 rig fixtures):

| Constant | Value in code | File | Real-world value |
|---|---|---|---|
| `MAX_REPROJ_MM` | 0.3 mm (target 0.1 mm) | `app/src/vision/rectify.ts` | TO MEASURE |
| `MAX_TILT_DEG` | 35° | `app/src/vision/rectify.ts` | TO MEASURE |
| `MIN_SHARPNESS` | 0.00015 (dimensionless) | `app/src/vision/rectify.ts` | TO MEASURE |
| `MAX_EDGE_WIDTH_PX` | 7.5 px | `app/src/vision/rectify.ts` | TO MEASURE |
| `MIN_RIM_CONTRAST` | 0.1 | `app/src/vision/segmentClassic.ts` | TO MEASURE |
| `LOW_MASK_SCORE` | 0.3 | `app/src/worker.ts` | TO MEASURE |
| `MAX_SPREAD_MM` | 0.6 mm | `app/src/quality/fuse.ts` | TO MEASURE |
| `MAX_CENTRE_SHIFT_MM` | 1.0 mm | `app/src/quality/fuse.ts` | TO MEASURE |
| `EDGE_HEIGHT_MM` | 3 mm | `app/src/measure/correction.ts` | TO MEASURE |
| rotation warning | 5° (`ROTATION_LIMIT_DEG`) | `app/src/measure/index.ts` | TO MEASURE |
| default clearance, lip | 0.2 mm, 0.5 mm (`DEFAULT_FRAME`) | `app/src/contracts.ts` | TO MEASURE on a print |

## 4. How to run

Automated tests (synthetic inputs only; they prove the code, not the accuracy):

```
cd app
npm run typecheck
npm test                      # loads OpenCV.js: allow several minutes; needs rig/out/fixtures (see below)
npm run build && npm run size
cd ../rig   && .venv/Scripts/python make_board.py --fixtures && .venv/Scripts/python -m pytest tests -q
cd ..       && tools/.venv/Scripts/python -m pytest tools/tests -q
```

Accuracy on real photos:

1. Photograph set A with `collect.html` (or any camera, original files) and fill the calliper readings.
2. Keep `app/public/bias.json` at the identity `{a0:0, a1:1, b0:0, b1:1}` for this run: the report fits the correction on raw measurements, and a non-identity file would be applied twice.
3. `cd app && npm run dev`, open `http://localhost:5173/eval.html`, select all photos of set A (and `own_lenses.csv`), press Run, download `results.csv` (columns `file,lensId,phone,rep,A,B,perimeter,method,reprojErrMm,sharpness,error`). The ZIP exported by `collect.html` already contains a `results.csv` with the same columns.
4. `tools/.venv/Scripts/python tools/accuracy_report.py results.csv own_lenses.csv [--out DIR] [--seed N]` writes `accuracy_report.md` and `bias.json`: MAE overall and per phone, failure rate, Bland-Altman bias and limits of agreement, repeatability, variance components, leave-one-lens-out fit, predicted rubric score (median and 5th percentile), decision line.
5. Copy `bias.json` to `app/public/` only if the report says it helps, and check it on lenses that were not used for the fit.
6. Copy the headline numbers into §6 below, with the date.

STL: download `monture.stl` from the app, then `tools/.venv/Scripts/python tools/validate_stl.py monture.stl` (one line per check, exit code 1 on failure), then open it in a slicer.

Error sentences without a camera: `http://localhost:5173/?demo=1&error=NO_LENS` (any of the ten codes).

## 5. Strategy experiments

One row per experiment of the adopted strategies. "Made measurable by" names what exists in the repository; the result column is filled by the team. Where a strategy assumed something the product does not have, the row says so (the brief wins over the strategy).

| Id | Experiment | Made measurable by (brief) | Threshold | Result | Date, who |
|---|---|---|---|---|---|
| S1-T1 | Print scale of the sheet (the sheet has a 100 mm ruler, not chessboard squares) | `rig/set_print_scale.py` (02) | within ± 0.2 mm, or `printScale` updated | | |
| S1-T2 | Edge contrast on the rig, 3 lenses (clear, tinted, high minus) | rectified image of the "Pas à pas" screen (10); the app's own gauge is `Mask.score` (05) | ≥ 60 grey levels | | |
| S1-T3 | Printed shapes (circle Ø 50.00 mm, rectangle 55 × 40 mm), 10 photos at different angles | `eval.html` (14), rectify (04), measure (06) | MAE ≤ 0.15 mm | | |
| S1-T4 | Reassembly by a person who never saw the rig | `docs/DISPOSITIF_CAPTURE.md` (15) | under 2 min, 3 different people | | |
| S1-T5 | Ambient light: room lights, window, flash | set A' with `collect.html` (17) | S1-T2 still passes; note what fails | | |
| S1-T6 | Phone diversity | per-phone MAE of `accuracy_report.py` (14) | S1-T3 passes on each phone | | |
| S2-E1 | Printed shapes in the window (no height) | same as S1-T3 | MAE ≤ 0.15 mm | | |
| S2-E2 | Printed shape raised on 3 mm spacers | parallax in `measure/correction.ts` (06); needs `focal35mm` in the EXIF | correction removes ≥ 80 % of the bias | | |
| S2-E3 | Own lenses, concave side down against convex side down | `eval.html` (14) | concave-down clearly better | | |
| S2-E4 | Distance 250, 350, 450 mm; 1× against 2× camera | `eval.html` (14) | pick the protocol | | |
| S2-E5 | Own lenses, final pipeline, 5 shots each, 3 phones | `accuracy_report.py` (14) | MAE ≤ 0.5 mm, max ≤ 1.0 mm | | |
| S2-E6 | SVG print | `contourToSvg` (09) | scale bar 50.0 ± 0.2 mm | | |
| S3-E1 | 8 own lenses × 5 shots on the backlit rig | `segmentClassic` (05); failure rate of `accuracy_report.py` (14) | MAE ≤ 0.5 mm, failure rate ≤ 5 % | | |
| S3-E2 | Same with room light only | set A', `eval.html` (14) | none: report the degradation | | |
| S3-E3 | Polar DP against plain contour (not built: one contour method, `measure/contour.ts`) | not measurable as written (06) | boundary p95 error | | |
| S3-E4 | OpenCV.js port against Python (no Python reference pipeline exists: the rig fixtures with known sizes replace it) | `vision/rectify.fixtures.test.ts`, `ui/fixture.test.ts` (04, 10) | A and B within 0.05 mm | | |
| S6-E1 | Label quality of the paired capture, 50 random pairs | `training/data/autolabel.py --qc N` (11) | ≥ 95 % visually correct | | |
| S6-E2 | Held-out lenses, hard conditions | `training/model/evaluate.py` (12) | IoU ≥ 0.97, MAE ≤ 0.7 mm | | |
| S6-E3 | Ablation: synthetic only, real only, both | `train.py --sources synth, real, both` (12) | both best, or report honestly | | |
| S6-E4 | Trained model against the classic segmenter on the same hard set | `method` column of `results.csv` (14), `evaluate.py` (12) | better than classic in hard conditions | | |
| S6-E5 | Browser latency on 2 phones; parity with PyTorch | `getLastTimings()` (13); `export_report.json` of `export.py` (12) | ≤ 3 s per lens; IoU parity ≥ 0.99 | | |
| S7-E1 | Single shot against fused 3 shots, 8 lenses (the app fuses 1 to 3 shots, not 5) | `fuseShots` (07), result screen (10) | fused MAE ≤ 0.8 × single-shot MAE | | |
| S7-E2 | Spread as a predictor of error | `quality.spreadA`, `spreadB` in `mesures.json` (07, 09) | positive correlation; threshold catches ≥ 80 % of shots with error > 1 mm | | |
| S7-E3 | Deliberately bad shot in the burst (blur, glare) | `fuseShots` (07), set D | fused MAE unchanged within 0.1 mm | | |
| S7-E4 | Time for 2 lenses with their shots on a mid-range phone | "Pas à pas" timings (10) | under 30 s | | |
| S8-E1 | Calliper protocol, 3 people on the same 8 lenses | `data/own_lenses.csv` (14), by hand | none: inter-person SD is the noise floor | | |
| S8-E2 | Orientation methods O1 to O4 (only the guide line, O1, is built) | measure (06) | choose the best; O1 expected | | |
| S8-E3 | Lens at +5° and −5° off the guide line | `rotationWarningDeg` (06), `LENS_ROTATED` sentence (07) | none: quantify the sensitivity, confirm the 5° warning | | |
| S8-E4 | Bias calibration, leave one lens out | `accuracy_report.py` (14) | MAE after < before, else keep the identity | | |
| S8-E5 | Final MAE on A and B over all own lenses | `accuracy_report.py` (14) | ≤ 0.5 mm | | |
| S9-T1 | Watertight, winding consistent | `tools/validate_stl.py` (14), `frame/frame.test.ts` (08) | true for all test shapes | | |
| S9-T2 | Volume > 0, no degenerate face, single body | `tools/validate_stl.py` (14) | pass | | |
| S9-T3 | Two shapes: ellipse 50 × 36 and rounded rectangle 52 × 34 | `frame/frame.test.ts` (08), overlay of the frame screen (10) | overlay gap = clearance ± 0.02 mm | | |
| S9-T4 | Sweep: clearance 0.1 to 0.3, bridge 14 to 22, rim width 2.5 to 5 | `frame/frame.test.ts` (08) | all pass S9-T1 | | |
| S9-T5 | Slicer check (PrusaSlicer or Cura) | by hand on `monture.stl` | no error, flat on the bed, supports about 0 | | |
| S9-T6 | Print one rim with a real lens | by hand | lens clips in without play or forcing; adjust the clearance | | |
| S9-T7 | Frame generation time on a mid-range phone | `frame` timing of the "Pas à pas" screen (10) | under 5 s | | |
| S9-T8 | SVG scale | `contourToSvg` (09) | scale bar 50.0 ± 0.2 mm | | |
| S10-T1 | Fresh phone opens the app by QR, no cache | deployed URL (01), `npm run qr` | usable in under 10 s on 4G | | |
| S10-T2 | End to end, two lenses | main page (10) | under 30 s of processing; STL downloads; SVG exports | | |
| S10-T3 | Each error condition reproduced on purpose | set D; `?demo=1&error=CODE` (10); `messageFor` (07) | the right sentence, no crash, no stack trace | | |
| S10-T4 | Offline after the first load | `public/sw.js` (01) | reload works in airplane mode | | |
| S10-T5 | Accuracy parity with a reference (no Python reference: rig fixtures) | same as S3-E4 | within 0.05 mm on the same photo | | |
| S10-T6 | Stranger test | QR, instruction sheet (15) | a result without help | | |
| S10-T7 | Backup video | `docs/DEMO_SCRIPT.md` §7 | exists and plays offline | | |
| S18-T1 | Completeness of the validation study | set A, `collect.html` (17) | all planned measurements collected, or gaps written down | | |
| S18-T2 | Reproducible analysis (`accuracy_report.py` replaces the notebook) | `tools/accuracy_report.py` (14) | runs from the two CSV files with one command | | |
| S18-T3 | Headline for A and B | `accuracy_report.md` (14) | bias, limits of agreement, variance components, predicted score distribution reported | | |
| S18-T4 | Decision | decision line of the report (14) | if the predicted median score is under 25 points, the dominant error component and its fix are named | | |

Strategies not built as their own feature (one line each; none has a result to report):

| Strategy | Status | What would be tested if it were taken up |
|---|---|---|
| 4 Refraction pattern | parked | two-shot distortion map against the classic segmenter, MAE ≤ 0.6 mm |
| 5 Promptable foundation model | helper, not built | offline teacher for labels; browser latency ≤ 10 s per lens before shipping |
| 11 Mechanical fixture | plan B, not built | SD of A and B ≤ 0.1 mm over 10 replaced shots |
| 12 Cross-polarisation | parked | background ≥ 10 × darker when crossed, outline visible on ≥ 6 of 8 lenses |
| 13 Two-height capture | parked | recovered edge height within ± 0.5 mm on raised shapes |
| 14 Shape model | parked | fitted A and B error ≤ 0.3 mm on corrupted edges |
| 15 Exports (1:1 PDF only) | not built; only if the SVG print test fails | printed scale bar 50.0 ± 0.2 mm on two printers |
| 16 Overlay | 2D overlay with the gap in mm is built (brief 10); live camera overlay parked | registration within 0.3 mm while the phone moves |
| 17 Complete eyewear | parked | hinge coupon rotates freely after printing |
| 19 Server-side path | plan B, not built | parity with the browser within 0.05 mm, ≤ 30 s per pair on 4G |
| 20 Lens power | parked | sphere error ≤ 0.25 D on known lenses |

## 6. Results

Empty until measured. One row per run; never overwrite a row, add one.

### 6.1 Ground truth (summary of `data/own_lenses.csv`)

| Date | Who | Lenses measured | Calliper model and resolution | Repeatability of the readings (SD, mm) | Inter-person SD (mm) |
|---|---|---|---|---|---|
| | | | | | |

### 6.2 Accuracy (from `accuracy_report.md`)

| Date | Who | Commit | Lenses | Phones | Photos | Failure rate | MAE A (mm) | MAE B (mm) | Bias A / B (mm) | Limits of agreement A / B (mm) | Repeatability SD (mm) | Predicted score (median / 5th percentile) | `bias.json` applied |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | | | | |

### 6.3 Accuracy per phone

| Date | Phone model | Browser | Photos | Failure rate | MAE A (mm) | MAE B (mm) |
|---|---|---|---|---|---|---|
| | | | | | | |

### 6.4 Robustness (sets A', C, D)

| Date | Case | Photos | Measured within 1 mm | Refused with a sentence | Crash or technical text | Notes |
|---|---|---|---|---|---|---|
| | tilt 10° | | | | | |
| | tilt 20° | | | | | |
| | distance 30 cm | | | | | |
| | distance 50 cm | | | | | |
| | room light only | | | | | |
| | window light | | | | | |
| | mounted glasses | | | | | |
| | wanted failures | | | | | |

### 6.5 Error sentences (one photo made on purpose per code)

| Code | How to provoke it | Sentence shown (yes / no) | Phone | Date |
|---|---|---|---|---|
| `NO_REFERENCE` | sheet cut off | | | |
| `REFERENCE_TILTED` | sheet very tilted | | | |
| `BLURRY` | move the phone | | | |
| `NO_LENS` | empty window | | | |
| `LENS_OUT_OF_WINDOW` | lens past the window edge | | | |
| `GLARE` | flash on the lens | | | |
| `INCONSISTENT_SHOTS` | move the lens between two shots | | | |
| `LENS_ROTATED` | lens 10° off the guide line | | | |
| `CAMERA_DENIED` | refuse the camera (live-camera path) | | | |
| `LOAD_FAILED` | cancel the picker; airplane mode before the first load | | | |

### 6.6 Print and frame

| Date | Test | Printer or slicer | Result | Pass |
|---|---|---|---|---|
| | Reference sheet ruler (nominal 100 mm), measured mm | | | |
| | SVG scale bar (nominal 50 mm), printed from Chrome, measured mm | | | |
| | SVG scale bar (nominal 50 mm), printed from Safari, measured mm | | | |
| | Lens laid on its printed 1:1 outline | | | |
| | `validate_stl.py` on `monture.stl` of a real pair | | | |
| | Slicer: errors, supports, estimated time | | | |
| | Printed rim: lens fit at the default clearance | | | |
| | Printed front: two different shapes, bridge, tenons | | | |

### 6.7 Rig and stranger test

| Date | Person (role, not name) | Setup time (s) | Got a result alone | What blocked them |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

### 6.8 Timings on phones ("Pas à pas" screen, ms)

| Date | Phone model | Browser | `opencv-load` | `detect` | `warp` | `sharpness` | `segment` | `measure` | `round-trip` | `fuse` | `frame` | `stl` | Pair total (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | | | | |
| | | | | | | | | | | | | | |

### 6.9 Devices

| Date | Device | Browser and version | Opens by QR | Camera | File import | Full flow | STL download | SVG download | Offline reload |
|---|---|---|---|---|---|---|---|---|---|
| | mid-range Android | Chrome | | | | | | | |
| | iPhone | Safari | | | | | | | |
| | any phone | other browser | | | | | | | |
| | laptop | Chrome (`lightbox.html`) | | | | | | | |

### 6.10 Trained model (from `training/model/evaluate.py` and the phones)

| Date | Training sources | Lenses train / test | IoU | Boundary F-score at 0.5 mm | MAE A / B with the model (mm) | MAE A / B classic, same photos (mm) | ONNX size (MB) | Load / inference on Android (ms) | Load / inference on iPhone (ms) | Shipped (G4) |
|---|---|---|---|---|---|---|---|---|---|---|
| | synthetic only | | | | | | | | | |
| | real only | | | | | | | | | |
| | both | | | | | | | | | |
