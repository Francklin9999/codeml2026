# Brief 07: Multi-shot fusion and user messages

> One agent, one brief. This file is self-contained: you need nothing else to start.
> **Wave 1: all in parallel, after 01 is merged.**

## Your goal

Never trust one photo: fuse several measurements of the same lens, expose their spread, and turn every error code into one clear French sentence.

## You own

- app/src/quality/ (index.ts, fuse.ts, messages.ts, tests)

## What to build

1. `fuseShots(shots)`: all contours are in the same board frame. With one shot, return it. Otherwise resample each contour as radius per angle (720 angles) around the mean of the box centres, take the median radius per angle, rebuild the contour, recompute A, B, perimeter and box centre the same way as brief 06 (extents along x and y; write a local helper, do not import from `measure/`).
2. Outliers: with 3 shots or more, drop a shot whose A or B is further than `max(0.3 mm, 2.5 × MAD)` from the median before fusing.
3. `quality.nShots` = shots kept, `spreadA` / `spreadB` = max − min over kept shots, `reprojErrMm` and `sharpness` = worst of kept shots.
4. If `spreadA` or `spreadB` exceeds `MAX_SPREAD_MM = 0.6` after outlier removal → `INCONSISTENT_SHOTS`.
5. `messageFor(code)` returns French text, one sentence saying what is wrong and one saying what to do, no technical word. Required wording basis:
   - NO_REFERENCE: « Je ne vois pas la feuille de référence en entier. Reculez un peu et cadrez toute la feuille. »
   - REFERENCE_TILTED: « La feuille est trop inclinée. Tenez le téléphone bien à plat au-dessus. »
   - BLURRY: « La photo est floue. Tenez le téléphone immobile et touchez l'écran pour faire la mise au point. »
   - NO_LENS: « Je ne trouve pas le verre. Posez-le au centre de la fenêtre. »
   - LENS_OUT_OF_WINDOW: « Le verre dépasse de la fenêtre. Recentrez-le. »
   - GLARE: « Il y a un reflet sur le verre. Éteignez le flash ou changez légèrement d'angle. »
   - INCONSISTENT_SHOTS: « Les photos ne donnent pas la même mesure. Reprenons une photo sans bouger le verre. »
   - LENS_ROTATED: « Le verre semble posé de travers. Alignez-le sur la ligne guide. »
   - CAMERA_DENIED: « L'accès à la caméra est refusé. Vous pouvez importer une photo à la place. »
   - LOAD_FAILED: « Le chargement a échoué. Vérifiez la connexion puis rechargez la page. »

## Done when

- [ ] fusing 5 noisy copies of an ellipse (0.2 mm radial noise) gives A and B closer to truth than the mean single-shot error
- [ ] one shot enlarged by 2 mm is rejected and does not change the result by more than 0.05 mm
- [ ] spread above the limit throws `INCONSISTENT_SHOTS`
- [ ] every `ErrorCode` has a message (test iterates over the list)
- [ ] kept shots whose box centres differ by more than `MAX_CENTRE_SHIFT_MM` throw `INCONSISTENT_SHOTS` (the lens moved between shots)
- [ ] the final report is written (see rule 7 below)

## Strategy inputs

The team's friend wrote 20 strategy files (`strat1.md` to `strat20.md`, in the project root). Read the ones named below before you code.
How to use them: an idea marked "Adopt" is part of this brief and is checked at the end. Anything else is optional: keep it only if it fits "What to build" and "You own". When a strategy conflicts with a contract, a constant or another brief's files, the brief wins; say so in your report. Do not create the strategies' `work/stratN/` folders: fold what you keep into your own files. Your report ends with a strategy log: one line per strategy read, adopted or left out, and why.

Read: `strat7.md` (all).

Adopt:
- Moved-lens detection (strat7 §6): after outlier removal, if two kept shots have box centres further apart than `MAX_CENTRE_SHIFT_MM = 1.0` (provisional, `TO MEASURE`), throw `INCONSISTENT_SHOTS`. Name the constant and test both sides of it.

Leave out: the rotate-the-lens protocol (§4.4), burst capture (briefs 03 and 10), per-shot quality gates (they belong to the pipeline in brief 10), SD statistics (the contract only has the spread).

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
