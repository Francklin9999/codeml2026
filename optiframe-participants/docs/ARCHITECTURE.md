# OptiFrame: architecture

> **Purpose:** how the pieces fit, for someone about to change one of them. Short on purpose.
> **Read with:** [`../CHALLENGE.md`](../CHALLENGE.md) (the rules), [`TEST_PLAN.md`](TEST_PLAN.md) (how each claim is checked).
> **Rule:** no accuracy or phone-timing figure appears here. Real-world numbers are `TO MEASURE` until they are in the results tables of [`TEST_PLAN.md`](TEST_PLAN.md).

## 1. Pipeline

Everything runs in the browser. One photo of one lens goes down the left column; two fused lenses go into the frame.

```
 phone camera / file picker
        |  capturePhoto, pickFile, decodeFile          capture/        (03)   EXIF orientation, downscale, focal35mm
        v
      Photo ------------------------------------------- page thread
        |  postMessage, pixel buffer transferred        pipeline.ts     (10)   one photo at a time, queue
 =======|========================================================== Web Worker (worker.ts, 10)
        |  rectify(photo, spec)                         vision/rectify  (04)   ArUco markers, homography, sharpness
        v                                               + board_spec.json (02)
    Rectified   window only, 10 px/mm (800 x 650 px for 80 x 65 mm)
        |  segmentClassic(r)                            vision/segmentClassic (05)
        |  segmentModel(r), only when classic says NO_LENS or scores < LOW_MASK_SCORE
        v                                               vision/segmentModel   (13) + models/lens_seg.onnx (12, absent)
      Mask      1 = lens, same size as Rectified.image
        |  measureLens(r, mask, eye)                    measure/        (06)   sub-pixel contour, parallax, bias.json
        v
 LensMeasurement  (one shot: contourMm 720 points, A, B, perimeter)
 =======|==========================================================
        |  fuseShots(shots)   1 to 3 shots per lens     quality/        (07)   outliers, spread, INCONSISTENT_SHOTS
        v
 LensMeasurement  (per eye, fused) ---- contourToSvg ----> contour-gauche.svg, contour-droit.svg   export/ (09)
        |                          \--- measurementToJson -> mesures.json
        |  generateFrame(left, right, params)           frame/          (08)   2D offsets, manifold-3d extrusion
        v
   FrameResult  (triangle mesh in mm, seats, gap) -- meshToStl --> monture.stl
        |
        v  ui/preview3d.ts (three.js) and the contour-over-rim overlay                ui/ (10)
```

Every failure leaves a module as `OptiError(code)`; `quality/messageFor(code)` turns the code into a French sentence. The worker sends back the code only (the detail text is dropped). `LENS_ROTATED` is never thrown: the UI derives it from `rotationWarningDeg`.

Side pages built from the same modules: `eval.html` (batch of photos to `results.csv`, brief 14), `collect.html` (data collection on the phone: original photo bytes in IndexedDB, calliper readings, ZIP export, brief 17), `public/lightbox.html` (white screen used as backlight, brief 02). Both `eval.html` and `collect.html` measure through `pipeline.measureOne`.

Offline side (Python, never loaded by the app): `rig/` draws the reference sheet and the test fixtures, `training/` builds the dataset and the model, `tools/` turns `results.csv` into the accuracy report and checks an STL.

```
 phone (collect.html) --ZIP--> training/_local/raw/ --+--> tools/accuracy_report.py --> accuracy_report.md, bias.json --> app/public/bias.json
                                                      +--> training/data/autolabel.py, synth.py, split.py --> training/model/train.py, export.py --> app/public/models/lens_seg.onnx
```

## 2. Data contracts

The code is `app/src/contracts.ts`; if this section and that file differ, the file wins and this section is fixed. Never edit the contracts without telling every module owner.

**Conventions.**
- Units are millimetres everywhere outside image buffers. `PX_PER_MM = 10` for rectified images.
- Board frame: origin at the top-left corner of the lens window, x to the right, y down, in mm.
- A contour is a closed polygon `Pt[]`, counter-clockwise, last point not repeated, seen from above with the lens concave side down (front view of the wearer). Right eye: nasal side is +x. Left eye: nasal side is -x.
- A and B follow the boxing system: extents of the contour along the board x axis (A) and y axis (B).

**Contracts** (`app/src/contracts.ts`):

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

**What the code adds to the contracts**:

- "Counter-clockwise" is meant in the numeric y-down frame: positive shoelace area. Contours have exactly 720 points.
- `Rectified.H` maps board mm (already multiplied by `printScale`) to PHOTO pixels, 9 numbers row-major. It is not a rectified-pixel matrix.
- `Photo.image` is upright and already downscaled; all photo coordinates refer to it, not to the original file.
- `Rectified.sharpness` is a dimensionless gauge, not a distance.
- `FrameResult` mesh has y UP and z from 0 to `thicknessMm`; `seatL`, `seatR` are in frame coordinates (y down); `gapMm` equals `clearanceMm`.
- `generateFrame` takes (left, right); in the mesh seen from +z the wearer's right lens is at -x.
- The bias (`bias.json`) is module state per JS realm: `pipeline.ts` sends it with each request and the worker calls `setBias`.

## 3. Modules and owners

One module = one owner brief. A change in a file goes through its brief's owner.

| Entry point | File | Brief |
|---|---|---|
| contracts, Vite and test setup, service worker, deploy workflow | `app/src/contracts.ts`, `app/vite.config.ts`, `app/src/test/`, `app/src/swRegister.ts`, `app/public/sw.js`, `../.github/workflows/deploy.yml` | 01 |
| reference sheet, print scale, fixtures, light box | `rig/`, `app/public/board_spec.json`, `app/public/lightbox.html` | 02 |
| `capturePhoto(): Promise<Photo>`, `pickFile`, `chooseOriginalFile`, `decodeFile` | `app/src/capture/index.ts` | 03 |
| `rectify(photo: Photo, spec: BoardSpec): Promise<Rectified>`, `locateReference`, `loadOpenCv` | `app/src/vision/rectify.ts`, `opencv.ts`, `homography.ts` | 04 |
| `segmentClassic(r: Rectified): Mask` | `app/src/vision/segmentClassic.ts` | 05 |
| `measureLens(r: Rectified, m: Mask, eye: Eye): LensMeasurement`, `setBias`, `loadBias`, `rotationWarningDeg` | `app/src/measure/index.ts`, `app/public/bias.json` | 06 |
| `fuseShots(shots: LensMeasurement[]): LensMeasurement`, `messageFor(code: ErrorCode): string` | `app/src/quality/index.ts` | 07 |
| `generateFrame(left: LensMeasurement, right: LensMeasurement, p: FrameParams): Promise<FrameResult>` | `app/src/frame/index.ts` | 08 |
| `contourToSvg(m: LensMeasurement): string`, `meshToStl(f: FrameResult): ArrayBuffer`, `measurementToJson`, `saveBlob` | `app/src/export/index.ts` | 09 |
| screens, `measureOne`, `measureOneDebug`, `checkSheet`, `warmUp`, `finishLens`, worker `handleMessage` | `app/index.html`, `app/src/main.ts`, `app/src/ui/`, `app/src/pipeline.ts`, `app/src/worker.ts`, `app/src/timing.ts` | 10 |
| `synth.py`, `autolabel.py`, `split.py` | `training/data/` | 11 |
| `train.py`, `export.py`, `evaluate.py`, `train_colab.ipynb` | `training/model/` | 12 |
| `segmentModel(r: Rectified): Promise<Mask>`, `isModelAvailable`, `getLastTimings` | `app/src/vision/segmentModel.ts`, `app/public/vendor/ort/` | 13 |
| evaluation page, `accuracy_report.py`, `validate_stl.py`, calliper template | `app/eval.html`, `app/src/eval/`, `tools/`, `data/` | 14 |
| jury documents (French) | `README.md`, `docs/DISPOSITIF_CAPTURE.md`, `docs/PAS_A_PAS.md`, `docs/DONNEES_ET_IA.md`, `docs/LICENCES_ET_OUTILS_IA.md` | 15 |
| internal documents | `docs/ARCHITECTURE.md`, `docs/TEST_PLAN.md`, `docs/RUBRIC_CHECKLIST.md`, `CLAUDE.md` | 16 |
| data-collection page | `app/collect.html`, `app/src/collect/`, `docs/COLLECTE_DONNEES.md` | 17 |

Screens of the main page (`ui/screens.ts`, `data-screen` values): `home`, `capture`, `result`, `steps` ("Pas à pas": intermediate images and stage timings), `frame` (bridge, 3D preview, overlay, downloads). `?demo=1` walks them without a camera; `?demo=1&error=CODE` shows the sentence of one error code.

## 4. Repository layout

Paths relative to `optiframe-participants/` (the Git repository root is one level up and holds `.github/workflows/deploy.yml`).

```
CHALLENGE.md, CLAUDE.md, README.md                   rules decoded, working rules, jury README
consignes.pdf                                        the organisers' brief (source of truth)
docs/          DEMO_SCRIPT, COLLECTE_DONNEES, ARCHITECTURE, TEST_PLAN, RUBRIC_CHECKLIST, JOURNAL_POSTE2,
               and the jury documents
data/          own_lenses.template.csv (copy to own_lenses.csv for the calliper readings)
app/
  index.html, eval.html, collect.html                the three Vite entries
  package.json, package-lock.json, vite.config.ts, tsconfig.json, README.md
  scripts/     qr.mjs (QR code of the URL), size-report.mjs (bundle size budget)
  public/      board_spec.json, bias.json, lightbox.html, sw.js, manifest.webmanifest,
               models/ (README.md only: lens_seg.onnx is absent), vendor/opencv, vendor/manifold, vendor/ort
  src/
    contracts.ts, main.ts, pipeline.ts, worker.ts, timing.ts, swRegister.ts
    capture/   index.ts, exif.ts, geometry.ts
    vision/    rectify.ts, homography.ts, opencv.ts, segmentClassic.ts, segmentModel.ts
    measure/   index.ts, contour.ts, correction.ts, boxing.ts
    quality/   index.ts, fuse.ts, messages.ts
    frame/     index.ts, layout.ts, polygons.ts
    export/    index.ts, svg.ts, stl.ts, json.ts, download.ts, check.ts
    ui/        app.ts, screens.ts, state.ts, dom.ts, chrome.ts, demo.ts, preview3d.ts, styles.css
    eval/      main.ts, parse.ts
    collect/   index.ts, ui.ts, naming.ts, storage.ts, zip.ts, manifest.ts, exporter.ts, measureAdapter.ts, styles.css
    test/      setup.ts (ImageData polyfill for every test)
    *.test.ts next to the code they test
  tests/perf/  budget.test.ts (Node regression guard, not a phone figure)
  dist/, node_modules/                               git-ignored
rig/           make_board.py, set_print_scale.py, requirements.txt, README.md, tests/,
               out/ (board_A4.pdf, board_Letter.pdf, board_spec.json, fixtures/ git-ignored)
training/      requirements.txt
  data/        synth.py, autolabel.py, split.py, capture_protocol.md, dataset_card.md, tests/
  model/       train.py, export.py, evaluate.py, common.py, train_colab.ipynb, requirements.txt, README.md, tests/
  _local/      git-ignored: raw photos, datasets, checkpoints (created by the team, absent from a fresh clone)
tools/         accuracy_report.py, validate_stl.py, requirements.txt, README.md, tests/
```

There is no `work/` folder. The strategy files name `work/stratN/` folders: they are scratch space, not source, and nothing in the product may depend on them.

## 5. Time budget toward the 30 s limit

The rule: a pair of lenses is processed in under 30 s on a mid-range phone ([`../CHALLENGE.md`](../CHALLENGE.md) §5). The "Pas à pas" screen shows the duration of each stage of the last photo on the device in hand, under the stage names below (`app/src/timing.ts`, `ui/screens.ts`). Design budget per lens: markers 1 s, rectify 1 s, segment 1 to 8 s, refine 1 s, fuse 1 s, at most 12 s per lens and 25 s for two.

| Stage (timing key) | What runs | Design budget | Mid-range Android | iPhone |
|---|---|---|---|---|
| `opencv-load` (first photo only, or warm-up from the home screen) | fetch and compile `vendor/opencv/opencv.js` (13.3 MB file) | none set | TO MEASURE | TO MEASURE |
| decode (not timed by the app) | `decodeFile`: EXIF, orientation, downscale | none set | TO MEASURE | TO MEASURE |
| `detect` | ArUco markers and homography | 1 s | TO MEASURE | TO MEASURE |
| `warp` + `sharpness` | window warped to 10 px/mm, sharpness gauge | 1 s | TO MEASURE | TO MEASURE |
| `segment` (classic) | `segmentClassic` | 1 s | TO MEASURE | TO MEASURE |
| `segment` (model fallback) | `segmentModel`, load plus inference (`getLastTimings`) | 3 s per lens (brief 13) | TO MEASURE (no model yet) | TO MEASURE (no model yet) |
| `measure` | contour refinement, parallax, bias, boxing | 1 s | TO MEASURE | TO MEASURE |
| `round-trip` | what the page waits for one photo (worker time plus moving the pixels) | 12 s per lens | TO MEASURE | TO MEASURE |
| `fuse` | `fuseShots`, 1 to 3 shots | 1 s | TO MEASURE | TO MEASURE |
| `frame` | `generateFrame` (manifold-3d WASM) | 5 s | TO MEASURE | TO MEASURE |
| `stl` | `meshToStl` | none set | TO MEASURE | TO MEASURE |
| **Pair total** (2 lenses, shots as taken, frame, STL; user time excluded) | | **under 30 s** | TO MEASURE | TO MEASURE |

Desktop guard, not a phone figure: `app/tests/perf/budget.test.ts` fails when one photo, a fuse of 3 shots, the frame and the STL take more than 3000 ms in Node after OpenCV has loaded. Size guard: `npm run size` fails when the initial JavaScript exceeds 250 kB gzip.
