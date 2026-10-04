# Brief 08: Parametric frame front

> One agent, one brief. This file is self-contained: you need nothing else to start.
> **Wave 1: all in parallel, after 01 is merged.**

## Your goal

Two lens contours and a bridge width in, a watertight triangle mesh of a printable frame front out.

## You own

- app/src/frame/ (index.ts, polygons.ts, layout.ts, tests)
- app/public/vendor/manifold/ (manifold WASM asset if needed; use only this subfolder)

## What to build

1. **Check first:** the `manifold-3d` npm package: confirm in its types that `CrossSection` can be built from polygons, has `offset(delta, joinType, ...)`, boolean operations and `extrude(height)`, and that `Manifold` has `union`, `getMesh()` and a status or validity check. Report the exact names. **Fallback:** a Clipper2 port (`clipper2-js`) for 2D offsets and booleans, earcut for triangulation, and your own extrusion of each layer (top cap, bottom cap, side walls), layers sharing identical boundaries so the stack is closed.
2. Layout (`layout.ts`), front view, frame coordinates with the bridge centre at x = 0: translate each contour so its box centre is on y = 0. Right lens placed on the −x side with its nasal edge (its max x) at x = −bridgeMm/2; left lens on the +x side with its nasal edge (its min x) at x = +bridgeMm/2.
3. Per lens, 2D shapes: `seat` = contour offset by +clearanceMm (round joins); `lipOpening` = contour offset by −lipMm; `outer` = contour offset by +(clearanceMm + rimWidthMm).
4. Three layers along z, total `thicknessMm`: front lip (25 %): `outer − lipOpening`; groove (50 %): `outer − seat`; back lip (25 %): `outer − lipOpening`. The lens sits in the groove and is held by the two lips.
5. Bridge: in every layer, a bar joining the two `outer` shapes, 4 mm high, centred 3 mm above y = 0 (towards the top of the lenses; mind that y points down in the contour frame), slightly overlapping both rims. Tenons: on each temporal extreme, a block `tenonMm.w` × `tenonMm.h` overlapping the rim by 1 mm, full thickness, with a through-hole of diameter `tenonMm.hole` along y for the hinge pin.
6. Union per layer in 2D, extrude, stack, union in 3D. Return positions (mm, z up from the print bed), indices, the two seat outlines in frame coordinates, and `gapMm` = clearanceMm.
7. Simplify input contours first (drop points closer than 0.05 mm, remove self-intersections with a union) so offsets never fail. Free every WASM object you allocate.

## Done when

- [ ] mesh is watertight for: two ellipses 50x36; ellipse + rounded rectangle 52x34; parameter sweep clearance 0.1–0.3, bridge 14–22, rim 2.5–5 (test: every edge shared by exactly two triangles with opposite orientation, volume > 0, one connected body)
- [ ] the seat outline is at clearance ± 0.02 mm from the input contour
- [ ] distance between the two lens nasal edges equals `bridgeMm` ± 0.01
- [ ] generation under 2 s in the test environment
- [ ] the final report is written (see rule 7 below)

## Strategy inputs

The team's friend wrote 20 strategy files (`strat1.md` to `strat20.md`, in the project root). Read the ones named below before you code.
How to use them: an idea marked "Adopt" is part of this brief and is checked at the end. Anything else is optional: keep it only if it fits "What to build" and "You own". When a strategy conflicts with a contract, a constant or another brief's files, the brief wins; say so in your report. Do not create the strategies' `work/stratN/` folders: fold what you keep into your own files. Your report ends with a strategy log: one line per strategy read, adopted or left out, and why.

Read: `strat9.md` (all), `strat16.md` §4 (only to see what the 2D overlay needs: the seat outlines and the gap).

Adopt:
- Defaults equal `DEFAULT_FRAME`; no extra parameters (no pantoscopic angle).
- Printability (strat9 §4.2): the frame lies flat, every overhang is at most the lip (0.5 mm), so no supports. Add a test that no layer opening is smaller than the lip rule allows.
- Mesh checks of strat9 T1 and T2: watertight, consistent winding, one connected body, positive volume, and no zero-area triangle.

Leave out: hinge screw sizes, SVG rim export (brief 09), the slicer and print tests (team, `TO MEASURE`).

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
