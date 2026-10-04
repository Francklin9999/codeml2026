# Brief 02: Reference sheet generator and light-box page

> One agent, one brief. This file is self-contained: you need nothing else to start.
> **Wave 1: all in parallel, after 01 is merged.**

## Your goal

The printed sheet that gives scale and perspective, its machine-readable description, and a page that turns a laptop or tablet screen into a backlight.

## You own

- rig/make_board.py, rig/requirements.txt, rig/README.md
- rig/out/ (generated PDFs and PNG fixtures)
- app/public/board_spec.json
- app/public/lightbox.html
- rig/set_print_scale.py, rig/tests/

## What to build

1. `make_board.py` (OpenCV `cv2.aruco`, reportlab): a landscape sheet whose printed content fits in 180 x 150 mm so that it prints at 100 % on both A4 and US Letter and lies on a 13-inch screen. Central empty **window 80 x 65 mm**. Around it, a ring of **ArUco markers, dictionary `DICT_4X4_50`**, marker side 15 mm, at least 12 markers, no marker closer than 4 mm to the window. Outputs `board_A4.pdf` and `board_Letter.pdf` at exact physical size, plus `board_spec.json` matching `BoardSpec` (corners in the board frame: origin = top-left window corner, so markers left of or above the window have negative coordinates).
2. Printed on the sheet, outside the window: a **100 mm ruler** with ticks every 10 mm and the text "Imprimer à 100 % : cette règle doit mesurer 100 mm"; a thin horizontal **guide line** through the window centre extended as short ticks on both window sides (not drawn inside the window); the labels "HAUT" above the window, "ŒIL DROIT : nez de ce côté →" on the right, "← ŒIL GAUCHE : nez de ce côté" on the left; a small version string.
3. `--fixtures`: also render PNG test scenes into `rig/out/fixtures/` by warping the board image with a known random homography (tilt up to 20°), drawing a filled dark-rimmed ellipse or rounded rectangle of known size in the window, adding blur and noise. Write the truth (`H`, shape size in mm) next to each PNG as JSON. Other briefs use these as integration fixtures.
4. `lightbox.html`: standalone static page, full-screen white, a button to go full screen, a hint to set brightness to maximum, and the Screen Wake Lock API when available. No dependency.

## Done when

- [ ] running the script produces both PDFs, the JSON and 10 fixtures
- [ ] a test re-reads each PDF page size and checks the window and ruler dimensions from the JSON
- [ ] detecting the markers in a rendered fixture with `cv2.aruco` and fitting a homography from `board_spec.json` recovers the known shape size within 0.1 mm
- [ ] pytest: `rig/set_print_scale.py 99.0` writes `printScale` 0.99 into both copies of `board_spec.json` and rejects 90 and 110
- [ ] the final report is written (see rule 7 below)

## Notes

`printScale` is 1 in the generated JSON; the team overwrites it after measuring the printed ruler.

## Strategy inputs

The team's friend wrote 20 strategy files (`strat1.md` to `strat20.md`, in the project root). Read the ones named below before you code.
How to use them: an idea marked "Adopt" is part of this brief and is checked at the end. Anything else is optional: keep it only if it fits "What to build" and "You own". When a strategy conflicts with a contract, a constant or another brief's files, the brief wins; say so in your report. Do not create the strategies' `work/stratN/` folders: fold what you keep into your own files. Your report ends with a strategy log: one line per strategy read, adopted or left out, and why.

Read: `strat1.md` (§4.1 to §4.4, §6), `strat2.md` §4.2 (what makes corner detection accurate).

Adopt:
- Print verification (strat1 §4.3): `rig/set_print_scale.py <measured_ruler_mm>` sets `printScale = measured / 100` in `app/public/board_spec.json` and `rig/out/board_spec.json`, rejects values outside 0.97 to 1.03, and prints the new value. This replaces hand-editing the JSON.
- Risks of strat1 §6: the light-box page tells the user to put a sheet of tracing paper between screen and printed sheet if a moire pattern appears, and `rig/README.md` lists the dim-screen and moire risks with the backup (tablet, phone torch behind a diffuser, window).
- Fixtures: at least one with a thick dark band and one with a faint rim, so briefs 04 to 06 meet both extremes (strat3 §4.3).

Leave out: ChArUco (the shared contracts fix an ArUco ring), the transparency-film variant, scale checks on photographs (brief 14 covers them).

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
