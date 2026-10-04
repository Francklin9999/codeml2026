# Brief 14: Evaluation page and validation tools

> One agent, one brief. This file is self-contained: you need nothing else to start.
> **Wave 2: with brief 10, after wave 1 is merged.** Build `tools/` first, the eval page last.

## Your goal

Measure what we ship: run the deployed pipeline on a batch of real photos against calliper values, and check the STL like a slicer would.

## You own

- app/eval.html, app/src/eval/ (tests)
- tools/ (validate_stl.py, accuracy_report.py, requirements.txt, README.md, tests)
- data/own_lenses.template.csv

## What to build

1. `eval.html` (second Vite entry, not linked from the app): the user selects many photos and one CSV. File name convention `<lensId>_<phone>_<rep>.jpg`. Each photo goes through the same `pipeline.measureOne` as the app (import it; if `app/src/pipeline.ts` does not exist yet, call rectify → segmentClassic → measureLens directly). Output a table and a downloadable `results.csv`: file, lensId, phone, rep, A, B, perimeter, method, reprojErrMm, sharpness, error code if any.
2. `data/own_lenses.template.csv`: `lensId, description, A_mm_1, A_mm_2, A_mm_3, B_mm_1, B_mm_2, B_mm_3, edge_thickness_mm, tint, notes` with two example rows marked as examples.
3. `accuracy_report.py results.csv own_lenses.csv`: reference = median of the three calliper readings. Reports: MAE of A and of B, overall and per phone; bias (mean signed error) and 95 % limits of agreement; failure rate; repeatability (SD across repetitions of the same lens and phone); a least-squares fit `ref = a0 + a1·measured` for A and B written as `bias.json` with leave-one-lens-out MAE before and after, and a line saying whether the correction helps; the **predicted rubric score**: `30 if MAE ≤ 1 else max(0, 30·(4 − MAE)/3)`, with a bootstrap over random pairs of lenses (median and 5th percentile). Output `accuracy_report.md`.
4. `validate_stl.py file.stl`: with `trimesh`: watertight, winding consistent, single body, positive volume, bounding box in mm, minimum wall estimate not required. Exit code non-zero on failure, one line per check.

## Done when

- [ ] pytest: `accuracy_report.py` on a synthetic results file with a known +0.4 mm bias recovers the bias, the MAE and the score formula at MAE = 0.5, 1, 2.5, 4
- [ ] pytest: `validate_stl.py` passes on a generated cube and fails on a cube with one triangle removed
- [ ] unit test for the file-name parser and CSV writer of the eval page
- [ ] pytest: variance components (lens, phone, residual) recovered on a synthetic file with a known between-phone offset
- [ ] pytest: `bias.json` is written with the fitted values only when the leave-one-lens-out MAE improves, otherwise with the identity and a line saying so
- [ ] at the end of your work, if `app/src/pipeline.ts` exists the eval page imports `measureOne(photo: Photo, eye: Eye): Promise<LensMeasurement>` from it; say in the report which path you used
- [ ] the final report is written (see rule 7 below)

## Strategy inputs

The team's friend wrote 20 strategy files (`strat1.md` to `strat20.md`, in the project root). Read the ones named below before you code.
How to use them: an idea marked "Adopt" is part of this brief and is checked at the end. Anything else is optional: keep it only if it fits "What to build" and "You own". When a strategy conflicts with a contract, a constant or another brief's files, the brief wins; say so in your report. Do not create the strategies' `work/stratN/` folders: fold what you keep into your own files. Your report ends with a strategy log: one line per strategy read, adopted or left out, and why.

Read: `strat18.md` (all), `strat8.md` §4.5 and §5, `strat2.md` §5.3 (error budget).

Adopt:
- Reproducibility next to repeatability: variance components (lens, phone, residual) by a random-effects ANOVA in numpy only, with the share of total variation (strat18 §4.2). If a factor is missing, write "not estimable".
- Bland-Altman: bias, limits of agreement, and the proportional-bias slope (difference regressed on the mean).
- Decision line (strat18 T4): when the predicted median score is under 25, name the dominant component among bias, repeatability and between-phone, and the follow-up strategy.
- `bias.json` carries metadata keys (`fittedOn`, `nLenses`, `phones`, `loMaeBefore`, `loMaeAfter`, `helps`) besides `a0, a1, b0, b1`; brief 06's loader ignores them. Never tune and evaluate on the same lenses (strat18 §7).

Leave out: the AR overlay, a Jupyter notebook (a plain Python script instead).

## Shared context (identical in every brief, do not change it)

**Product.** OptiFrame, a 24-hour hackathon project. A static mobile web app (public HTTPS URL, no install, no account, no API key, no paid or closed service) that photographs a spectacle lens lying in the window of a printed reference sheet, rectifies the photo, segments the lens, measures width **A**, height **B** and perimeter in mm (jury compares A and B with a calliper: full marks if mean error <= 1 mm), then generates a 3D-printable frame front (two rims, bridge, hinge tenons) as a watertight STL. Must run on recent Chrome (Android) and Safari (iOS), under 30 s per pair of lenses on a mid-range phone. All processing in the browser.

**Project root** = `optiframe-participants/`. All paths below are relative to it. Stack: Vite + TypeScript (strict), no UI framework, Vitest for tests, every third-party library self-hosted (no CDN at runtime). Python 3.11+ only for offline tools under `rig/`, `training/`, `tools/`.

**Conventions.**
- Units are millimetres everywhere outside image buffers. `PX_PER_MM = 10` for rectified images.
- Board frame: origin at the top-left corner of the lens window, x to the right, y down, in mm.
- A contour is a closed polygon `Pt[]`, counter-clockwise, last point not repeated, seen from above with the lens concave side down (front view of the wearer). Right eye: nasal side is +x. Left eye: nasal side is -x.
- A and B follow the boxing system: extents of the contour along the board x axis (A) and y axis (B).

**Contracts** (`app/src/contracts.ts`, created by brief 01; if the file is absent, create it with exactly this content):

```ts
export type Pt = [number, number];                       // mm
export type Eye = 'L' | 'R';
export const PX_PER_MM = 10;
export interface BoardSpec { dictionary: string; markerMm: number; markers: { id: number; corners: Pt[] }[];   // corners in board frame, TL,TR,BR,BL
  windowMm: { w: number; h: number }; guideLineYMm: number; rulerMm: number; printScale: number }             // printScale = measured/nominal, 1 if perfect
export interface Photo { image: ImageData; source: 'camera' | 'file'; focal35mm?: number }
export interface Rectified { image: ImageData; pxPerMm: number; H: number[]; reprojErrMm: number; sharpness: number; cameraDistMm?: number }  // image covers the window only
export interface Mask { data: Uint8Array; width: number; height: number; method: 'classic' | 'model'; score: number }   // 1 = lens, same size as Rectified.image
export interface LensMeasurement { eye: Eye; contourMm: Pt[]; A: number; B: number; perimeter: number; boxCentre: Pt;
  method: 'classic' | 'model'; quality: { reprojErrMm: number; sharpness: number; nShots: number; spreadA: number; spreadB: number } }
export interface FrameParams { bridgeMm: number; clearanceMm: number; rimWidthMm: number; thicknessMm: number; lipMm: number; tenonMm: { w: number; h: number; hole: number } }
export const DEFAULT_FRAME: FrameParams = { bridgeMm: 18, clearanceMm: 0.2, rimWidthMm: 3.5, thicknessMm: 4, lipMm: 0.5, tenonMm: { w: 6, h: 8, hole: 1.5 } };
export interface FrameResult { positions: Float32Array; indices: Uint32Array; seatL: Pt[]; seatR: Pt[]; gapMm: number }   // triangle mesh in mm
export type ErrorCode = 'NO_REFERENCE' | 'REFERENCE_TILTED' | 'BLURRY' | 'NO_LENS' | 'LENS_OUT_OF_WINDOW' | 'GLARE' | 'INCONSISTENT_SHOTS' | 'LENS_ROTATED' | 'CAMERA_DENIED' | 'LOAD_FAILED';
export class OptiError extends Error { constructor(public code: ErrorCode, detail = '') { super(code + (detail ? ': ' + detail : '')); } }
```

**Module entry points** (each brief owns one; the others may be stubs when you work):

| Function | File | Brief |
|---|---|---|
| `capturePhoto(): Promise<Photo>` | `app/src/capture/index.ts` | 03 |
| `rectify(photo: Photo, spec: BoardSpec): Promise<Rectified>` | `app/src/vision/rectify.ts` | 04 |
| `segmentClassic(r: Rectified): Mask` | `app/src/vision/segmentClassic.ts` | 05 |
| `measureLens(r: Rectified, m: Mask, eye: Eye): LensMeasurement` | `app/src/measure/index.ts` | 06 |
| `fuseShots(shots: LensMeasurement[]): LensMeasurement`, `messageFor(code: ErrorCode): string` | `app/src/quality/index.ts` | 07 |
| `generateFrame(left: LensMeasurement, right: LensMeasurement, p: FrameParams): Promise<FrameResult>` | `app/src/frame/index.ts` | 08 |
| `contourToSvg(m: LensMeasurement): string`, `meshToStl(f: FrameResult): ArrayBuffer` | `app/src/export/index.ts` | 09 |
| `segmentModel(r: Rectified): Promise<Mask>` | `app/src/vision/segmentModel.ts` | 13 |

**Rules for you.**
1. Create or edit only the files listed under "You own". If you need a change elsewhere, write it in your final report instead of making it.
2. Never change the contracts. If one is wrong, say so in the report.
3. You have no physical lens, phone or printer. Prove your work with unit tests on synthetic inputs that you generate in the test itself. Never invent a measured accuracy figure: write `TO MEASURE` where a real-world number is needed.
4. Failures are thrown as `OptiError` with a code from the list. No other exception may escape a module entry point.
5. Before relying on a library feature you are not certain exists, check it in the installed package (types, source) and say what you found. If it is missing, use the fallback named in the brief.
6. Keep it small: no extra features, no abstraction for later, comments only where the reason is not obvious.
7. Final report, at most 25 lines: files written, how to run the tests and their result, what you verified about libraries, what is left `TO MEASURE` on real hardware, and any contract problem.
