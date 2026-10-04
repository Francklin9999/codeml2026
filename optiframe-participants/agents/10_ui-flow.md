# Brief 10: Screens and pipeline orchestration

> One agent, one brief. This file is self-contained: you need nothing else to start.
> **Wave 2: with brief 14, after wave 1 is merged.** You import every wave-1 module, so wire the real ones, not stubs.

## Your goal

The five screens that take a stranger from the QR code to `monture.stl`, one-handed, on a 6-inch screen. Start after brief 01; the other modules may still be stubs, so build against the contracts and keep a `?demo=1` mode that uses built-in synthetic measurements.

## You own

- app/index.html, app/src/main.ts, app/src/ui/ (screens, state, styles, tests)
- app/src/pipeline.ts
- app/src/ui/preview3d.ts
- app/src/worker.ts (written by 01 as a stub; you now own it: wire the real modules into it)

## What to build

1. Screens, plain DOM, French text, buttons at least 48 px high, no horizontal scroll at 360 px width:
   - **Accueil:** what the app does in one sentence, link "Comment installer le dispositif", buttons "Verre gauche" and "Verre droit" each showing done / not done.
   - **Capture:** reminder with a pictogram of where the nasal side goes for the chosen eye, buttons "Prendre la photo" and "Importer une photo"; after each photo a counter "photo 2 sur 3" (3 shots per lens, the user may stop at 1).
   - **Résultat du verre:** control image (rectified image with the contour drawn), A, B, perimeter with one decimal, spread between shots, buttons "Exporter le contour (SVG 1:1)", "Reprendre", "Valider".
   - **Monture:** bridge width slider 14–22 mm (default 18), 3D preview, a 2D overlay of measured contours and seats with the gap in mm, buttons "Télécharger monture.stl" and "Télécharger les mesures".
   - **Pas à pas:** for the last photo: original with detected markers, rectified image, mask, contour.
2. `pipeline.ts`: `measureOne(photo, eye)` runs the worker (rectify → segmentClassic → on `NO_LENS` or low mask score try `segmentModel` if available → measureLens); `finishLens(shots)` calls `fuseShots`; errors are caught and shown with `messageFor(code)` in a dismissible banner with a "Reprendre" button. No error text other than those messages ever reaches the screen; unknown exceptions map to `LOAD_FAILED`.
3. A progress indicator names the current step (« Je repère la feuille », « Je redresse l'image », « J'isole le verre », « Je mesure »).
4. `preview3d.ts`: three.js (self-hosted from npm), `BufferGeometry` from `FrameResult`, orbit by touch, neutral material, fits the frame in view. Loaded lazily on the frame screen.
5. State kept in memory and mirrored to `sessionStorage` (measurements only, no images) so a reload does not lose a validated lens.
6. Load `board_spec.json` and `bias.json` from `public/` at start; failure → `LOAD_FAILED`.
7. `worker.ts`: the `measure` message carries `{ photo, spec, eye, bias }`; the worker calls `setBias(bias)` (from `measure/`) before measuring. Keep the reply shape `{ ok: true, result } | { ok: false, code }`.
8. `main.ts` keeps the call to `registerServiceWorker()` written by brief 01. The home screen links to `lightbox.html` (« Page de rétro-éclairage »).
10. Fixed signature, because briefs 14 and 17 import it: `export async function measureOne(photo: Photo, eye: Eye): Promise<LensMeasurement>`, which throws `OptiError`; the step-by-step images come from a separate function (for example `measureOneDebug`), not from a different return type.
11. The bottom of the home screen links to `collect.html` (« Collecte de données (équipe) », small and discreet): brief 17 owns that page.
9. Test hook for the stranger test and the jury: `?demo=1&error=<ErrorCode>` shows the banner for that code exactly as a real failure would, with its `messageFor` sentence (strat10 T3).

## Done when

- [ ] `?demo=1` walks all five screens without a camera and downloads a valid STL
- [ ] a test for the pipeline with mocked modules: fallback to the model on `NO_LENS`, every `ErrorCode` displayed with its message, unknown exception → `LOAD_FAILED`
- [ ] no element overflows at 360x640 (test with jsdom-computed layout is not reliable: list this as `TO MEASURE` on a phone and check your CSS by reasoning)
- [ ] one test sends a fixture from `rig/out/fixtures/` through the real modules (no mocks) and records the measured A and B against the truth in its JSON; it must be within 0.5 mm (write the actual error in the report; if the fixtures are missing, generate a synthetic scene in the test)
- [ ] `?demo=1&error=NO_LENS` (and every other code) shows the matching message (test)
- [ ] the final report is written (see rule 7 below)

## Strategy inputs

The team's friend wrote 20 strategy files (`strat1.md` to `strat20.md`, in the project root). Read the ones named below before you code.
How to use them: an idea marked "Adopt" is part of this brief and is checked at the end. Anything else is optional: keep it only if it fits "What to build" and "You own". When a strategy conflicts with a contract, a constant or another brief's files, the brief wins; say so in your report. Do not create the strategies' `work/stratN/` folders: fold what you keep into your own files. Your report ends with a strategy log: one line per strategy read, adopted or left out, and why.

Read: `strat10.md` (§4.4, §4.5, T3), `strat16.md` §4 (only the static 2D overlay), `strat7.md` §4.2, `strat8.md` §4.4.

Adopt:
- The "Vérifier" view is 2D: measured contour, seat and outer rim, with the gap in mm from `FrameResult` (bonus 1). No live camera overlay (parked in WINNING_PLAN §6).
- Between shots show « Bougez légèrement le téléphone » (strat7 §4.2: different viewpoints decorrelate perspective errors) and the spread of A and B (bonus 2).
- Eye choice with a nasal-side pictogram (strat8 §4.4); `rotationWarningDeg` produces a non-blocking `LENS_ROTATED` hint.
- Every failure of strat10 §4.5 reaches the user through brief 07's `messageFor` wording, never the strat10 draft.

Leave out: auto-capture, live AR overlay, English strings, a UI framework.

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
