# Brief 04: Marker detection and rectification

> One agent, one brief. This file is self-contained: you need nothing else to start.
> **Wave 1: all in parallel, after 01 is merged.**

## Your goal

From a photo to a top-view image of the window at 10 px/mm, with a quality figure.

## You own

- app/src/vision/rectify.ts, app/src/vision/opencv.ts (loader), app/src/vision/homography.ts, tests, app/src/vision/js-aruco2.d.ts (js-aruco2 ships no types: declare the module there)
- app/public/vendor/opencv/ (the OpenCV.js build you select; use only this subfolder)

## What to build

1. **Check first:** find an OpenCV.js build that exposes ArUco detection (`cv.aruco_ArucoDetector` or `cv.ArucoDetector`, `getPredefinedDictionary`) in a 4.8+ release or the `@techstark/opencv-js` package. Report what you found. **Fallback if absent:** the `js-aruco2` package with a dictionary equal to `DICT_4X4_50`, keeping OpenCV.js only for `findHomography` and `warpPerspective`; if OpenCV.js is unusable altogether, implement the DLT homography with normalisation and a RANSAC loop in `homography.ts` and a bilinear warp by hand.
2. `rectify`: detect markers on a copy downscaled to about 1600 px wide, refine corners at full resolution (`cornerSubPix` or a local gradient-based refinement), match ids to `spec.markers`, multiply board coordinates by `spec.printScale`. Fewer than 4 markers → `NO_REFERENCE`.
3. Homography board(mm) → image(px) from all matched corners, RANSAC then least-squares on inliers. `reprojErrMm` = RMS residual expressed in mm. Above 0.3 mm → `REFERENCE_TILTED`. Also reject when the board plane is tilted more than 35° (estimate from the homography's perspective terms or the ratio of marker side lengths).
4. Warp only the window region to an `ImageData` of `windowMm.w * 10` by `windowMm.h * 10` px.
5. `sharpness` = variance of the Laplacian of the rectified grey image. Below a named constant `MIN_SHARPNESS` → `BLURRY` (pick a provisional value, mark it `TO MEASURE`).
6. `cameraDistMm`: when `focal35mm` is known, estimate from the apparent marker size (`f_px = focal35mm / 36 * imageWidthPx`); otherwise leave undefined.
7. Load OpenCV.js lazily, once, with a promise; it must work inside a Web Worker.

## Done when

- [ ] on synthetic scenes (render the board from `board_spec.json` with a known homography in the test, or use `rig/out/fixtures/` when present) a 50.0 mm segment drawn in the window measures 50.0 ± 0.1 mm in the rectified image
- [ ] `NO_REFERENCE`, `REFERENCE_TILTED` and `BLURRY` each triggered by a dedicated test
- [ ] `homography.ts` unit-tested alone on exact correspondences and with 20 % outliers
- [ ] the final report is written (see rule 7 below)

## Strategy inputs

The team's friend wrote 20 strategy files (`strat1.md` to `strat20.md`, in the project root). Read the ones named below before you code.
How to use them: an idea marked "Adopt" is part of this brief and is checked at the end. Anything else is optional: keep it only if it fits "What to build" and "You own". When a strategy conflicts with a contract, a constant or another brief's files, the brief wins; say so in your report. Do not create the strategies' `work/stratN/` folders: fold what you keep into your own files. Your report ends with a strategy log: one line per strategy read, adopted or left out, and why.

Read: `strat2.md` (§4.2, §4.3), `strat10.md` §4.3 (worker and timing).

Adopt:
- Refit on the RANSAC inliers and report the residual in mm (already in the brief). Keep `MAX_REPROJ_MM = 0.3` as the provisional named constant; write strat2's stricter 0.1 mm as a `TO MEASURE` target next to it.
- Resample the window with Lanczos or bicubic interpolation rather than bilinear when OpenCV.js is available (strat2 §4.2 step 3).
- `cameraDistMm`: prefer the pose from the homography with intrinsics built from `focal35mm` (strat2 §4.3) if you can unit-test it within 3 % on a synthetic scene; otherwise use the marker-size estimate of the brief. Say which one you shipped.
- Timing (strat10 §4.3: markers under 1 s, rectify under 1 s on a phone): a test prints the desktop timings; the phone numbers stay `TO MEASURE`.

Leave out: ChArUco, lens-distortion calibration (strat2 optional part), 20 px/mm (the contract is 10).

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
