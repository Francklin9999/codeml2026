# Brief 13: Run the segmenter in the browser

> One agent, one brief. This file is self-contained: you need nothing else to start.
> **Wave 1: all in parallel, after 01 is merged.** (Moved up from wave 2: it needs only the model interface below.)

## Your goal

The fallback segmenter: load `models/lens_seg.onnx` and return a `Mask` for a rectified image.

## You own

- app/src/vision/segmentModel.ts, tests
- app/public/vendor/ort/ (onnxruntime-web WASM assets; use only this subfolder)
- app/public/models/README.md

## What to build

Model interface (from brief 12): input `input`, float32 `1×3×320×384` (N, C, H, W), RGB scaled to 0–1 then normalised with mean (0.485, 0.456, 0.406) and std (0.229, 0.224, 0.225); output `logits` `1×1×320×384`, sigmoid > 0.5 = lens.
1. `onnxruntime-web` from npm, WASM execution provider, **single thread** (`ort.env.wasm.numThreads = 1`) because static hosts cannot send the cross-origin-isolation headers that threads need. WASM files self-hosted under `vendor/`, path set with `ort.env.wasm.wasmPaths`.
2. `segmentModel(r)`: resize the rectified image to 384×320 (bilinear), build the tensor, run, sigmoid, resize the probability map back to the rectified size (bilinear), threshold, keep the largest component, fill holes. `score` = mean probability inside the mask. `method: 'model'`.
3. Session created lazily once and reused. If the model file is missing (404), `isModelAvailable()` returns false and `segmentModel` throws `OptiError('LOAD_FAILED')`; the pipeline then simply does not use the model.
4. Same plausibility checks and error codes as the classical segmenter: `NO_LENS`, `LENS_OUT_OF_WINDOW` (state the thresholds as constants: area 600–4000 mm², mask not touching the border).
5. `models/README.md`: where the weights come from and how to regenerate them (point to `training/model/`).

## Done when

- [ ] unit tests for preprocessing (tensor layout and normalisation on a 2-colour image) and post-processing (largest component, fill, resize) with a fake session object
- [ ] missing model → `isModelAvailable()` false, no unhandled rejection
- [ ] check and report whether onnxruntime-web in the installed version runs int8-quantised models on the WASM provider
- [ ] `getLastTimings()` returns `{ loadMs, preMs, runMs, postMs }` after a run (brief 10 and the eval page can show it)
- [ ] the final report is written (see rule 7 below)

## Notes

`TO MEASURE`: load time and inference time on both phones (budget: 3 s per lens).

## Strategy inputs

The team's friend wrote 20 strategy files (`strat1.md` to `strat20.md`, in the project root). Read the ones named below before you code.
How to use them: an idea marked "Adopt" is part of this brief and is checked at the end. Anything else is optional: keep it only if it fits "What to build" and "You own". When a strategy conflicts with a contract, a constant or another brief's files, the brief wins; say so in your report. Do not create the strategies' `work/stratN/` folders: fold what you keep into your own files. Your report ends with a strategy log: one line per strategy read, adopted or left out, and why.

Read: `strat6.md` E5, `strat5.md` §5 (latency table), `strat10.md` §4.3.

Adopt:
- Pure typed-array pre and post-processing, no DOM and no `OffscreenCanvas`, so it runs in a worker and in Node tests.
- Fixed model URL `models/lens_seg.onnx`, so the service worker of brief 01 caches it.
- Timing helper `getLastTimings()`; the phone numbers (budget 3 s per lens) stay `TO MEASURE`.

Leave out: SAM or MobileSAM in the browser (not shipped), the WebGPU provider (iOS support varies; WASM single thread only).

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
