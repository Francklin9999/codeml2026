# Brief 06: Contour refinement and boxing measurement

> One agent, one brief. This file is self-contained: you need nothing else to start.
> **Wave 1: all in parallel, after 01 is merged.**

## Your goal

From a mask to a smooth contour in mm and to A, B, perimeter as a calliper would measure them.

## You own

- app/src/measure/ (index.ts, contour.ts, boxing.ts, correction.ts, tests)
- app/public/bias.json

## What to build

1. Outer contour of the mask (Moore tracing or marching squares), in pixels.
2. Sub-pixel refinement: at each contour point sample the grey profile along the normal over ±1 mm and move the point to the **outermost** position where the profile crosses half-way between the outside level and the rim level. Skip the move when the profile contrast is too low.
3. Convert to mm (`/ pxPerMm`), resample to 720 points equally spaced along the curve, smooth with a low-pass on the closed curve (keep 30 Fourier harmonics), force counter-clockwise order.
4. `A` = max x − min x, `B` = max y − min y of the contour in the board frame; `boxCentre` = centre of that rectangle; `perimeter` = polygon length.
5. Parallax correction in `correction.ts`: when `cameraDistMm` D is known, scale the contour about the window centre by `(D − h) / D` with `h = EDGE_HEIGHT_MM = 3` (the lens edge is above the sheet). When D is unknown, no scaling.
6. Bias: read `bias.json` `{ a0, a1, b0, b1 }` and apply `A = a0 + a1·A`, `B = b0 + b1·B`. Ship the identity (0, 1, 0, 1); the team fits it on real lenses (brief 14 writes the file). Apply the bias to the contour as well, not only to the two numbers: scale x by A'/A and y by B'/B about the box centre and recompute the perimeter, so that the SVG, the frame and the displayed A and B always agree. Export `setBias(b)` (default identity) and `loadBias(url)`; the loader ignores extra keys such as `fittedOn`, `nLenses`, `phones`, `loMaeBefore`, `loMaeAfter`, `helps`.
7. Orientation check: compute the minimum-area bounding rectangle; if its long side is more than 5° from the x axis and the shape is not near-circular (A/B > 1.1), attach a warning by throwing nothing but exporting `rotationWarningDeg(m)` that returns the angle (the UI shows `LENS_ROTATED`).
8. Fill `quality` from `Rectified` with `nShots: 1`, `spreadA: 0`, `spreadB: 0`.

## Done when

- [ ] synthetic rectified images with a blurred dark ring of known outer size: A and B within 0.05 mm, perimeter within 0.3 %
- [ ] the boxing function tested on a rotated rectangle and an ellipse with closed-form answers
- [ ] parallax scaling tested with D = 300, h = 3
- [ ] contour is counter-clockwise with exactly 720 points
- [ ] with a non-identity bias, the contour's own extents equal the reported A and B within 0.01 mm
- [ ] the final report is written (see rule 7 below)

## Strategy inputs

The team's friend wrote 20 strategy files (`strat1.md` to `strat20.md`, in the project root). Read the ones named below before you code.
How to use them: an idea marked "Adopt" is part of this brief and is checked at the end. Anything else is optional: keep it only if it fits "What to build" and "You own". When a strategy conflicts with a contract, a constant or another brief's files, the brief wins; say so in your report. Do not create the strategies' `work/stratN/` folders: fold what you keep into your own files. Your report ends with a strategy log: one line per strategy read, adopted or left out, and why.

Read: `strat2.md` (§4.4, §4.5), `strat8.md` (all), `strat3.md` §4.2 steps 6 and 7.

Adopt:
- `extentAlong(contour, theta)` in `boxing.ts` (strat8 §4.2): the extent between two parallel lines, as a calliper measures it. A and B are its values at 0 and 90 degrees (board x and y axes). The warning of item 7 doubles as strat8's check of the guide-line axis (O1) against the minimum-area rectangle (O2).
- A comment in `contour.ts` states which edge is measured: the outer boundary of the dark band, because the calliper measures the outer extent (strat2 §4.4).

Leave out: bias fitting (brief 14), orientation by PCA or maximum width (O3, O4), effective diameter, polar dynamic programming.

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
