# Brief 16: Internal documents and link repair

> One agent, one brief. This file is self-contained: you need nothing else to start.
> **Wave 3: in parallel with brief 15, after waves 1 and 2 are merged.** You describe and check what exists, so you run last.

## Your goal

The team's working documents, in English, short. Read `CHALLENGE.md`, `docs/WINNING_PLAN.md`, `docs/PLAN_24H.md` and every file in `agents/` first.

## You own

- docs/ARCHITECTURE.md, docs/TEST_PLAN.md, docs/RUBRIC_CHECKLIST.md, docs/RISKS.md
- CLAUDE.md
- link fixes only in CHALLENGE.md, docs/WINNING_PLAN.md, docs/PLAN_24H.md, docs/DEMO_SCRIPT.md

## What to build

1. `ARCHITECTURE.md`: one diagram (text) of the pipeline photo → Rectified → Mask → LensMeasurement → FrameResult → files; a section **"Data contracts"** reproducing the shared contracts and conventions; the module table with owner brief; repository layout as it actually is; time budget per step toward the 30 s limit (`TO MEASURE`).
2. `TEST_PLAN.md`: calliper protocol (three readings, lens id on the bag); test matrix (lenses × phones × repetitions, lighting, tilt, mounted glasses must not crash); acceptance thresholds (MAE ≤ 0.5 mm internal target, ≤ 1.0 mm gate; spread ≤ 0.6 mm; printed scale bar 50.0 ± 0.2 mm; STL passes `tools/validate_stl.py` and a slicer; stranger sets up the rig in under 2 minutes; pair processed in under 30 s); how to run `eval.html` and `tools/accuracy_report.py`; empty results tables.
3. `RUBRIC_CHECKLIST.md`: one row per rubric line of `CHALLENGE.md` §4 (points, evidence file or screen, owner role, status box); one row per imposed-format requirement of §5; the deliverables of §6; the submission checklist.
4. `RISKS.md`: at most 15 rows: risk, early sign, mitigation, fallback, owner. Take them from `WINNING_PLAN.md` §3 and §8 and from the `TO MEASURE` items you find in `agents/`.
5. `CLAUDE.md`: under 60 lines: what the project is, the conventions, commands to build and test, the rule "one module = one owner brief", and "never state an accuracy figure that is not in TEST_PLAN results".
6. Link repair: the four existing documents link to `MEASUREMENT_SPEC.md`, `FRAME_SPEC.md`, `WEBAPP_SPEC.md`, `DEPLOYMENT.md`, which do not exist. Point each link to the matching brief in `agents/` (measurement → 04/05/06/07, frame → 08, web app → 03/10, deployment → 01). Change nothing else in those files.

## Done when

- [ ] every relative link in the whole `optiframe-participants/` tree resolves (write and run a small link checker, do not commit it)
- [ ] rubric points in the checklist sum to 100
- [ ] no invented measurement
- [ ] the final report is written (see rule 7 below)

## Strategy inputs

The team's friend wrote 20 strategy files (`strat1.md` to `strat20.md`, in the project root). Read the ones named below before you code.
How to use them: an idea marked "Adopt" is part of this brief and is checked at the end. Anything else is optional: keep it only if it fits "What to build" and "You own". When a strategy conflicts with a contract, a constant or another brief's files, the brief wins; say so in your report. Do not create the strategies' `work/stratN/` folders: fold what you keep into your own files. Your report ends with a strategy log: one line per strategy read, adopted or left out, and why.

Also read: `docs/MENTOR_NOTES.md`, `docs/COLLECTE_DONNEES.md`, `agents/17_data-collection.md` (the collection page is part of the architecture, the repository layout and the test plan; its results feed the TEST_PLAN tables), and `agents/WAVE1_INTERFACES.md` (what the modules really export).

Read: every `stratN.md` "How to test it" table, `strat18.md`, `docs/WINNING_PLAN.md` §3, §6 and §8.

Adopt:
- `TEST_PLAN.md` consolidates the adopted strategies' experiments: strat1 T1 to T6, strat2 E1 to E6, strat3 E1 to E4, strat6 E1 to E5, strat7 E1 to E4, strat8 E1 to E5, strat9 T1 to T8, strat10 T1 to T7, strat18 T1 to T4. For each: the module or brief that makes it measurable, the threshold, and an empty results row. One line each for the parked strategies.
- `RISKS.md` includes the plan-B triggers (strat19 server path, strat11 fixture) and the kill criteria of WINNING_PLAN §8.
- `CLAUDE.md` says that `work/stratN/` folders are scratch space, not source.

Leave out: nothing.

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
