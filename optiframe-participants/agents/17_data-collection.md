# Brief 17: Data collection mode (phone)

> One agent, one brief. This file is self-contained: you need nothing else to start.
> **Wave 2: with briefs 10 and 14, after wave 1 is merged.**

## Your goal

The team owns real lenses, a calliper and phones, but no dataset. Build the page that turns a phone into the data-collection tool: take photos with the native camera, name and label them correctly, enter the calliper readings, see at once whether the sheet was detected and what the app measures, and carry everything to a laptop as ZIP files that `tools/` and `training/` read unchanged. Everything stays on the phone: no server, no upload.

## You own

- app/collect.html, app/src/collect/ (index.ts, naming.ts, storage.ts, zip.ts, manifest.ts, measureAdapter.ts, ui.ts, styles, tests)
- docs/COLLECTE_DONNEES.md (the orchestrator wrote version 1 before this brief: keep it consistent with the page, do not shrink it)

## What to build

A page in French, one-handed, no horizontal scroll at 360 px, buttons at least 48 px high, no framework. It imports `chooseOriginalFile` and `decodeFile` from `app/src/capture/index.ts` (they exist), `messageFor` from `quality/`, `rectify` from `vision/rectify.ts`, `saveBlob` from `export/download.ts`, and the board spec from `public/board_spec.json`.

1. **Three modes**, as tabs remembered in `localStorage`:
   - **Validation** (accuracy set; feeds `tools/accuracy_report.py` and `eval.html`). Fields: lensId (remembered), eye L or R, phone label (guessed from the user agent, editable, remembered), calliper readings A1 A2 A3 B1 B2 B3 in mm (decimal keypad, optional but encouraged), edge thickness, tint, notes. "Prendre la photo" opens the native camera; the file name is `<lensId>_<phone>_<rep>.jpg`, `rep` counting up per lensId and phone from 1. After the shot: decode, run the app pipeline, show A, B, perimeter and the signed error against the calliper median when readings exist, or the `messageFor` sentence when it fails. A failed shot is still kept (failures are data).
   - **Entraînement** (paired capture, brief 11). Fields: lensId, position (1 to 6), a grid of condition buttons `easy` (backlit, must come first), `room`, `lampL`, `lampT`, `lampR`, `flash`, `pattern`, `colour`; done conditions are ticked per (lensId, position). File name `<lensId>_<pos>_<cond>.jpg` as in `training/data/capture_protocol.md`. Fixed text: « Ne bougez ni le verre ni le téléphone entre deux photos. » Warn when a condition is shot before `easy`. After each shot show « Feuille détectée (n marqueurs) » or the `messageFor` sentence, using `rectify` only.
   - **Libre** (mounted glasses at the SN-SF stand, other surfaces, hard cases). Free label and tags, file name `<label>_<n>.jpg`, no measurement, the sheet check is optional.
   Identifiers use letters, digits and hyphens only (underscore separates the fields of a name, so it is refused); sanitise as the user types.
2. Every shot keeps the **original file bytes untouched** (EXIF and focal length stay; never re-encode) in IndexedDB with its metadata: mode, ids, phone, rep or position and condition, calliper readings, timestamps, user-agent string, app version, measurement or error code, sheet check. Ask `navigator.storage.persist()`, show the number of photos and the usage from `navigator.storage.estimate()`, and warn above 80 % of the quota.
3. Session gallery: thumbnails (160 px, object URLs revoked), tap to retake or delete one photo (with confirmation), counters per lens and per mode.
4. **Export.** A STORE-only ZIP writer (no dependency: CRC-32, local headers, central directory), split into parts of at most 50 MB. Content: `photos/<name>.jpg`; `manifest.csv` (one row per photo, every metadata field); `own_lenses.csv` (the exact columns of `data/own_lenses.template.csv` from brief 14, `lensId, description, A_mm_1, A_mm_2, A_mm_3, B_mm_1, B_mm_2, B_mm_3, edge_thickness_mm, tint, notes`; read that file if it exists, else use these columns); `results.csv` (the columns of the eval page of brief 14: file, lensId, phone, rep, A, B, perimeter, method, reprojErrMm, sharpness, error code); `LISEZMOI.txt` (five lines: what is inside, how to use it on the laptop). Share with the Web Share API when `navigator.canShare({ files })` allows it, otherwise `saveBlob`. A separate button « Vider les photos exportées » deletes only photos marked as exported, after confirmation. Nothing is ever deleted automatically.
5. Measuring: import `measureOne(photo: Photo, eye: Eye): Promise<LensMeasurement>` from `app/src/pipeline.ts` (brief 10) with a dynamic import; it throws `OptiError`. If that file does not exist when you work, keep the call behind `measureAdapter.ts`, which uses `rectify`, `segmentClassic` and `measureLens` directly, and switch to `pipeline.measureOne` at the end of your work if the file exists by then. Say in the report which path shipped.
6. A fixed line on the page: « Pas de visages, pas de noms, pas d'ordonnances sur les photos. » The page makes no network call except loading itself.
7. `collect.html` is its own Vite entry (the config builds every top-level HTML file). Brief 10 adds a link to it at the bottom of the home screen.
8. `docs/COLLECTE_DONNEES.md`: keep it in sync (modes, file names, counts, export contents); add the exact commands to move a ZIP to the laptop and run `autolabel.py`, `eval.html` and `accuracy_report.py`, read from those READMEs when they exist.

## Done when

- [ ] unit tests: the file-name builder (three modes, rep increment, identifier sanitising), the ZIP writer (re-read by an independent parser written in the test: CRC-32 and sizes right, parts under 50 MB, an empty export refused), the CSV writer (commas, quotes and newlines escaped; columns equal to brief 14's), the calliper median and signed error, the condition grid (`easy` first)
- [ ] storage tests against a small in-memory fake of IndexedDB (written in the test; `fake-indexeddb` is not installed): add, list, delete, mark exported
- [ ] a jsdom test walks each mode with fakes for the camera and the pipeline and checks the stored record and the displayed result
- [ ] a ZIP produced by a test is opened with Python's `zipfile` from a throwaway script and its `manifest.csv` parses; the stored original bytes are identical to the input bytes
- [ ] `npm run build` emits `collect.html` and the page works from a sub-path
- [ ] the final report is written (see rule 7 below)

## Strategy inputs

The team's friend wrote 20 strategy files (`strat1.md` to `strat20.md`, in the project root). Read the ones named below before you code.
How to use them: an idea marked "Adopt" is part of this brief and is checked at the end. Anything else is optional: keep it only if it fits "What to build" and "You own". When a strategy conflicts with a contract, a constant or another brief's files, the brief wins; say so in your report. Do not create the strategies' `work/stratN/` folders. Your report ends with a strategy log: one line per strategy read, adopted or left out, and why.

Read: `strat6.md` §4.2 (paired protocol), `strat18.md` §4.1 (measurement CSV, randomised order), `strat2.md` §5.1 and `strat8.md` E1 (calliper protocol), `docs/COLLECTE_DONNEES.md` and `docs/MENTOR_NOTES.md` (what the team must collect and why), `agents/11_dataset-tools.md` and `agents/14_eval-tools.md` (the file formats you must match).

Adopt:
- The sequence of strat6 §4.2 as the order of the condition grid, `easy` first.
- strat2 §5.1: three readings per dimension, median as reference; the page shows the spread of the three readings and flags a spread above 0.2 mm as « lectures incohérentes, refaire ».
- strat18 §4.1: no personal data in `manifest.csv` (the user-agent string is allowed, a name is not).

Leave out: any upload, account or backend; measuring mounted glasses (strat17, parked); live camera overlay (strat16, parked).

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
