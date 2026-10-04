# Brief 12: Train a small segmenter and export it to ONNX

> One agent, one brief. This file is self-contained: you need nothing else to start.
> **Wave 1: all in parallel, after 01 is merged.**

## Your goal

A lightweight lens segmenter trained on the dataset of brief 11, exported for the browser, with honest metrics.

## You own

- training/model/ (train.py, export.py, evaluate.py, train_colab.ipynb, README.md, tests)
- training/model/requirements.txt (the heavy ML stack; brief 11 owns `training/requirements.txt`)

## What to build

Input format (from brief 11): `images/`, `masks/` (800×650, mask 0/255), `index.csv`, `split.csv`.
1. Model: U-Net with a MobileNetV3-Small encoder from `segmentation_models_pytorch` (ImageNet weights), 1 output channel. Input 3×320×384 (rectified window resized), normalised with ImageNet mean/std.
2. `train.py`: Albumentations (perspective, brightness/contrast, blur, noise, JPEG, random shadow), loss = BCE + Dice, AdamW 1e-3 with cosine schedule, 40 epochs, batch 16, best checkpoint on validation IoU. Seeds fixed. Runs on a free Colab T4; `train_colab.ipynb` only clones the repo, installs requirements and calls the scripts.
3. `evaluate.py`: on the test split, per condition and overall: IoU, boundary F-score at 0.5 mm tolerance (5 px at 10 px/mm, scaled to the model resolution), and A / B error in mm between the predicted mask's bounding extents and the label's. Writes `metrics.md` and `metrics.json`. Add the same metrics for a baseline you compute in the script: Otsu threshold on the grey image.
4. `export.py`: ONNX opset 17, fixed input `1×3×320×384` named `input`, output `logits`; verify with onnxruntime that the max absolute difference to PyTorch is below 1e-3; also write a dynamically quantised int8 copy and report both file sizes. Output `lens_seg.onnx` and `lens_seg.int8.onnx`.
5. `README.md`: exact commands, library versions, and a licence table for every dependency and pre-trained weight you used. Check each licence in the package metadata or repository and say where you read it.

## Done when

- [ ] pytest smoke test: 2 epochs on 16 synthetic samples generated in the test runs end to end on CPU, exports ONNX, and the parity check passes
- [ ] `evaluate.py` produces both files on that tiny set
- [ ] no metric is quoted in any document except as produced by `evaluate.py`
- [ ] `train.py --sources real|synth|both` selects the training data (ablation); the smoke test uses `both`
- [ ] smoke-test weights are never written under `app/` (a toy model must not be shipped as `lens_seg.onnx`)
- [ ] the final report is written (see rule 7 below)

## Notes

All real metrics are `TO MEASURE` after the team shoots the dataset.

## Strategy inputs

The team's friend wrote 20 strategy files (`strat1.md` to `strat20.md`, in the project root). Read the ones named below before you code.
How to use them: an idea marked "Adopt" is part of this brief and is checked at the end. Anything else is optional: keep it only if it fits "What to build" and "You own". When a strategy conflicts with a contract, a constant or another brief's files, the brief wins; say so in your report. Do not create the strategies' `work/stratN/` folders: fold what you keep into your own files. Your report ends with a strategy log: one line per strategy read, adopted or left out, and why.

Read: `strat6.md` (§4.4 to §4.6, E2 to E5), `strat5.md` §4.4 (teacher and student note only).

Adopt:
- Ablation of strat6 E3 through the `--sources` switch; `evaluate.py` reports per condition and the Otsu baseline.
- ONNX parity of strat6 E5 (the 1e-3 check of the brief) and both file sizes.
- The input stays 320 x 384, the interface fixed with brief 13, not strat6's 512 x 512.
- In the smoke test use `encoder_weights=None` so it needs no download; the README commands use the ImageNet weights. Check in the installed package that the encoder name you pick exists, and say which.

Leave out: a boundary loss, YOLO (AGPL), SAM export.

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
