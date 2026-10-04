# Brief 11: Dataset tools: paired capture and synthetic lenses

> One agent, one brief. This file is self-contained: you need nothing else to start.
> **Wave 1: all in parallel, after 01 is merged.**

## Your goal

Training data for lens segmentation with zero manual annotation.

## You own

- training/data/ (autolabel.py, synth.py, split.py, capture_protocol.md, dataset_card.md, tests)
- training/requirements.txt

## What to build

1. `capture_protocol.md` (French, one page, for the team): phone on a fixed stand above the reference sheet; for each lens position, shot 1 backlit (easy), then without moving anything: room light only, desk lamp from 3 directions, phone flash, a patterned page under the sheet, a coloured backlight. Naming: `<lensId>_<pos>_<cond>.jpg`, `cond = easy` for shot 1. Target 15 lenses × 6 positions × 8 conditions.
2. `autolabel.py`: input a folder of such photos and `board_spec.json`. For each photo detect the ArUco markers (`cv2.aruco`, `DICT_4X4_50`), rectify the window to 800×650 px. For `easy` shots compute the mask with the classical recipe (flat-field, black-hat, Otsu, fill from border, largest component). Copy that mask to every other photo of the same `<lensId>_<pos>`. Reject a group when the homographies of its photos map the window corners more than 3 px apart from the easy shot (the stand moved). Output `images/`, `masks/`, `index.csv` (file, lensId, pos, cond, source = real).
3. `synth.py`: generate N synthetic 800×650 samples: random lens outline (superellipse or rounded rectangle, 35–65 mm wide, aspect 0.6–0.95, rotation ±10°, optional asymmetry), on a background from a folder of images supplied by the team (or procedural noise/gradients if none), with: slight magnification of the background inside the shape, a dark rim 0.3–1.5 mm wide with random strength, 0–3 elliptical highlights, a soft shadow, blur, noise, JPEG compression. Exact mask saved. `source = synth`.
4. `split.py`: split **by lens id** (train / val / test 70/15/15), synthetic samples only in train. Writes `split.csv`.
5. `dataset_card.md` (French): template with counts, conditions, sources, licences, privacy statement (no faces, names or prescriptions), all numbers `À COMPLÉTER`.

## Done when

- [ ] pytest: `synth.py` produces images and masks of the right size with mask area matching the generated shape within 1 %
- [ ] pytest: `autolabel.py` on a tiny synthetic group (rendered with a known board and shape) reproduces the mask with IoU ≥ 0.97 and rejects a group where one photo is shifted
- [ ] pytest: no lens id appears in two splits
- [ ] `autolabel.py --qc N` writes N overlay images (mask outline on the hard shot) into `qc/` for visual inspection
- [ ] the final report is written (see rule 7 below)

## Strategy inputs

The team's friend wrote 20 strategy files (`strat1.md` to `strat20.md`, in the project root). Read the ones named below before you code.
How to use them: an idea marked "Adopt" is part of this brief and is checked at the end. Anything else is optional: keep it only if it fits "What to build" and "You own". When a strategy conflicts with a contract, a constant or another brief's files, the brief wins; say so in your report. Do not create the strategies' `work/stratN/` folders: fold what you keep into your own files. Your report ends with a strategy log: one line per strategy read, adopted or left out, and why.

Read: `strat6.md` (§4.2, §4.3, §4.5, E1), `strat3.md` §4.2 (the recipe `autolabel.py` reuses), `strat5.md` §4.4 (teacher option, documented only).

Adopt:
- Label quality check (strat6 E1): `--qc N` as in the Done-when list.
- Synthetic families: add `aviator` and `cat-eye` outlines next to superellipse and rounded rectangle, a Fresnel-like brighter edge, and the thin-lens magnification (strat6 §4.3).
- Raw and generated images live in `training/_local/` (git-ignored by brief 01), never in the repository.
- A README paragraph in `capture_protocol.md` documents the optional SAM teacher (strat5 §4.4) without code.

Leave out: Blender renders, SAM code, boundary loss.

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
