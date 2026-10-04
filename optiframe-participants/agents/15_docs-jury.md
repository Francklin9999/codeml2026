# Brief 15: Jury-facing documents (French)

> One agent, one brief. This file is self-contained: you need nothing else to start.
> **Wave 3: in parallel with brief 16, after waves 1 and 2 are merged.** You describe what exists, so you run last.

## Your goal

The written deliverables the jury reads. French, sober, no marketing. Read `CHALLENGE.md` (the rules) and `docs/DEMO_SCRIPT.md` (tone) first, then look at what actually exists in `app/`, `rig/`, `training/`, `tools/` and describe only that.

## You own

- README.md
- docs/DISPOSITIF_CAPTURE.md, docs/PAS_A_PAS.md, docs/DONNEES_ET_IA.md, docs/LICENCES_ET_OUTILS_IA.md

## What to build

Every figure that needs a real measurement is written `À COMPLÉTER`, never invented. Use the vocabulary of the brief: verre, monture, cercle, pont, tenon, pied à coulisse, dispositif de capture, système boxing.
1. `README.md`, in this order: lien de l'app et QR code (`À COMPLÉTER`); ce que fait l'app (5 lignes); tester en 2 minutes; dispositif de capture (résumé + lien); lancement local (commandes exactes lues dans `app/README.md`); choix techniques (un tableau : étape, choix, raison); données et IA (résumé + lien); résultats mesurés (tableau vide : nombre de verres, téléphones, erreur moyenne A et B, pire cas); limites connues; outils d'IA utilisés (lien); sources et licences (lien); structure du dépôt; équipe.
2. `DISPOSITIF_CAPTURE.md`: liste du matériel; impression de la feuille (100 %, A4 ou Lettre, vérification de la règle de 100 mm au pied à coulisse, que faire si elle mesure autre chose); **montage en 6 étapes numérotées, lisible en 30 secondes, tenant sur une page imprimée**; pose du verre (face bombée vers le haut, aligné sur la ligne guide, côté nez selon l'œil); tenue du téléphone (à plat, 35 à 45 cm, toute la feuille visible); dépannage (tableau problème → geste).
3. `PAS_A_PAS.md`: une photo et ses images intermédiaires (référence détectée, image redressée, masque, contour, mesures), avec des emplacements d'images `docs/img/pas-a-pas-N.png` `À COMPLÉTER` et deux lignes d'explication par étape.
4. `DONNEES_ET_IA.md`: le problème des annotations; la capture appariée (pourquoi elle évite toute annotation manuelle); les images synthétiques; le modèle et l'entraînement; la séparation par verre; les mesures (tableaux vides aux colonnes de `training/model/evaluate.py`); comparaison avec la méthode sans IA; où l'IA est utilisée dans l'app et où elle ne l'est pas; données personnelles: aucune.
5. `LICENCES_ET_OUTILS_IA.md`: tableau des bibliothèques réellement présentes dans `app/package.json` et les `requirements.txt` (nom, version, licence lue dans le paquet, usage); tableau des modèles pré-entraînés et jeux de données; tableau des outils d'IA utilisés pour coder (outil, usage, partie du code), lignes à compléter par l'équipe.

## Done when

- [ ] every relative link resolves to an existing file
- [ ] no number that would require a real measurement appears without `À COMPLÉTER`
- [ ] the 6-step assembly fits on one printed page
- [ ] every licence listed was read in the package itself; unknown ones are marked `À VÉRIFIER`
- [ ] the final report is written (see rule 7 below)

## Strategy inputs

The team's friend wrote 20 strategy files (`strat1.md` to `strat20.md`, in the project root). Read the ones named below before you code.
How to use them: an idea marked "Adopt" is part of this brief and is checked at the end. Anything else is optional: keep it only if it fits "What to build" and "You own". When a strategy conflicts with a contract, a constant or another brief's files, the brief wins; say so in your report. Do not create the strategies' `work/stratN/` folders: fold what you keep into your own files. Your report ends with a strategy log: one line per strategy read, adopted or left out, and why.

Also read: `docs/MENTOR_NOTES.md`, `docs/COLLECTE_DONNEES.md` (mention the collection page and the SN-SF ISO 12870 target of ±0.5 mm in the jury documents where relevant), and `agents/WAVE1_INTERFACES.md` (what the modules really export).

Read: `strat1.md` §4.4 and §6, `strat6.md` and `strat18.md` (the story and the statistics the tables will hold), `docs/WINNING_PLAN.md` §6 (which strategies are parked).

Adopt:
- `DISPOSITIF_CAPTURE.md` troubleshooting from strat1 §6: moire (tracing paper), dim screen (tablet, torch behind a diffuser, window), adapted to the real sheet described in `rig/README.md`.
- README "limites connues": list the parked strategies as perspectives for INOVA: refraction pattern (4), cross-polarisation (12), two-height capture (13), shape model (14), complete eyewear (17), lens power (20), live AR overlay (16).
- Result tables have the columns of strat18 (bias, limits of agreement, repeatability, predicted score), all `À COMPLÉTER`.

Leave out: anything presented as measured.

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
