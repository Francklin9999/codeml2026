# Brief 01: App scaffold, contracts, deployment

> One agent, one brief. This file is self-contained: you need nothing else to start.
> **Wave 0: run alone, first.**

## Your goal

A deployable skeleton that every other brief plugs into. This brief runs first; the others start once it is merged.

## You own

- app/package.json, app/vite.config.ts, app/tsconfig.json, app/index.html
- app/src/contracts.ts, app/src/main.ts, app/src/worker.ts
- stub `index.ts` for every module in the entry-point table
- .github/workflows/deploy.yml (at the Git repository root)
- app/README.md
- .gitignore (in the project root, `optiframe-participants/.gitignore`)
- app/package-lock.json, app/src/test/setup.ts, app/src/swRegister.ts
- app/public/sw.js, app/public/manifest.webmanifest

## What to build

1. Vite + TypeScript strict project in `app/`, `base: './'` so it works from a sub-path on GitHub Pages. Scripts: `dev`, `build`, `test` (Vitest), `typecheck`.
2. Write `contracts.ts` exactly as in the shared context.
3. For each entry point in the table, create the file with the exact signature and a body that throws `new OptiError('LOAD_FAILED', 'not implemented')`. The project must type-check with all stubs.
4. `worker.ts`: a Web Worker that receives `{ type: 'measure', photo, spec, eye }`, calls `rectify` → `segmentClassic` → `measureLens`, and posts either `{ ok: true, result }` or `{ ok: false, code }`. `main.ts` only mounts a placeholder page that says the app loaded and shows whether `navigator.mediaDevices` exists.
5. GitHub Actions workflow: on push to the main branch, build `optiframe-participants/app` and publish `dist/` to GitHub Pages.
6. `app/README.md`: how to run locally, build, test, deploy, and how to make a QR code of the final URL with the `qrcode` npm package (generate `app/public/qr.svg` with a script `npm run qr -- <url>`).
7. **Pre-install every dependency the other briefs need**, so that no later agent edits `package.json` or the lock file. Runtime: `@techstark/opencv-js`, `js-aruco2`, `manifold-3d`, `clipper2-js`, `earcut`, `three`, `onnxruntime-web`. Dev: `typescript`, `vite`, `vitest`, `jsdom`, `qrcode`, `pngjs` (tests decode the PNG fixtures of brief 02 with it), `@types/node`, `@types/three`, `@types/earcut`, `@types/qrcode`, `@types/pngjs`. Run `npm install` and keep `package-lock.json`. Put each package's installed version and the licence you read in its own `package.json` into your report (brief 15 reuses it). If a name does not resolve, say which one and what you used instead.
8. `.gitignore` in the project root: `node_modules/`, `dist/`, `.venv*/`, `**/.venv/`, `__pycache__/`, `.pytest_cache/`, `training/_local/`, `*.pt`, `*.pth`, `rig/out/fixtures/`, `*.log`. Do not ignore `app/public/models/*.onnx` or `rig/out/*.pdf`.
9. Vitest config: `environment: 'node'`, `include: ['src/**/*.test.ts', 'tests/**/*.test.ts']`, `setupFiles: ['src/test/setup.ts']`. `setup.ts` defines a minimal `ImageData` (constructors `(width, height)` and `(data, width, height)`, `colorSpace: 'srgb'`) when `globalThis.ImageData` is missing, because Node and jsdom have none; every brief's tests rely on it. A test that needs the DOM adds `// @vitest-environment jsdom`.
10. Offline after the first load: `app/public/sw.js` (cache-first for `vendor/` and `models/`, network-first with cache fallback for everything else, cache name from a version constant, old caches deleted), `app/public/manifest.webmanifest`, and `app/src/swRegister.ts` exporting `registerServiceWorker()` (registers `./sw.js`; no-op when unsupported; `?nosw=1` unregisters it and clears the caches). `main.ts` calls it; brief 10 keeps the call.
11. `vite.config.ts` builds `index.html` and also `eval.html` when that file exists (brief 14 adds it later). `lightbox.html` is a static file in `public/` (brief 02).
12. The deploy workflow also runs on `workflow_dispatch`, so a known-good commit can be redeployed by hand.

## Done when

- [ ] `npm run typecheck`, `npm run test` and `npm run build` pass
- [ ] the built `dist/` opens from a sub-path and shows the placeholder
- [ ] one Vitest test posts a message to the worker pipeline with stubs and receives `{ ok: false, code: 'LOAD_FAILED' }` (call the handler function directly if Worker is unavailable in the test environment)
- [ ] `npm ls` shows every dependency of item 7 installed; versions and licences are in the report
- [ ] a test creates `new ImageData(2, 2)` in the default environment (setup polyfill)
- [ ] `dist/` contains `sw.js` and `manifest.webmanifest`; `registerServiceWorker()` is a no-op when `navigator.serviceWorker` is absent (test)
- [ ] the final report is written (see rule 7 below)

## Strategy inputs

The team's friend wrote 20 strategy files (`strat1.md` to `strat20.md`, in the project root). Read the ones named below before you code.
How to use them: an idea marked "Adopt" is part of this brief and is checked at the end. Anything else is optional: keep it only if it fits "What to build" and "You own". When a strategy conflicts with a contract, a constant or another brief's files, the brief wins; say so in your report. Do not create the strategies' `work/stratN/` folders: fold what you keep into your own files. Your report ends with a strategy log: one line per strategy read, adopted or left out, and why.

Read: `strat10.md` (§4.1, §4.3, §4.5, §5.3). `strat19.md` only to know what plan B means; do not build it.

Adopt:
- Offline after first load (strat10 T4): the service worker of item 10.
- Last known good (strat10 §5.3): item 12.
- Heavy work in a Web Worker (strat10 §4.3): `worker.ts` keeps an extensible message `type` because brief 10 will add messages.

Leave out: the light-box page (brief 02), camera code (03), the message table (07), the server path of strat19.

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
