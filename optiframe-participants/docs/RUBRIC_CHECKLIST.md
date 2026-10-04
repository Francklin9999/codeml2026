# OptiFrame: rubric checklist

> **Purpose:** every line the jury scores or requires, with the evidence that proves it and who owns it. Ticked line by line at H+23 ([`PLAN_24H.md`](PLAN_24H.md)).
> **Source:** [`../CHALLENGE.md`](../CHALLENGE.md) §4, §5 and §6, itself taken from `consignes.pdf`.
> **Roles:** L = lead, integration, presentation; V = capture and vision; D = data and AI; F = 3D and interface.
> **Rule:** a box is ticked only when the evidence exists: a file in the repository, a screen on a real phone, or a filled row of [`TEST_PLAN.md`](TEST_PLAN.md) §6. "Built" in the last column means the code exists and passes its synthetic tests; it is not a tick.

## 1. Scoring grid (CHALLENGE §4)

| Criterion | Points | Evidence (file or screen) | Owner | Done | State today |
|---|---|---|---|---|---|
| Précision des mesures | 30 | [`TEST_PLAN.md`](TEST_PLAN.md) §6.2 and §6.3: MAE of A and B on our own lenses, per phone; result screen of the app | V | ☐ | Built; no real lens measured: TO MEASURE |
| Qualité du contour | 5 | "Exporter le contour (SVG 1:1)" on the result screen; TEST_PLAN §6.6 (scale bar and lens laid on the print) | F | ☐ | Built; never printed: TO MEASURE |
| Robustesse | 10 | TEST_PLAN §6.4 and §6.5: tilt, lighting, mounted glasses, wanted failures; spread of A and B between shots on the result screen | V | ☐ | Built; not tried on real photos: TO MEASURE |
| Données et IA | 15 | [`DONNEES_ET_IA.md`](DONNEES_ET_IA.md), [`LICENCES_ET_OUTILS_IA.md`](LICENCES_ET_OUTILS_IA.md), `training/data/dataset_card.md`, TEST_PLAN §6.10 | D | ☐ | Model v2 trained on 24 159 synthetic rig-like windows (zero manual labels) and shipped; held-out synthetic metrics and an app-side benchmark in DONNEES_ET_IA §6.0 and §7.1. Real-photo dataset and metrics on our own lenses: TO MEASURE |
| Web app mobile | 15 | Public URL and QR code in [`../README.md`](../README.md); TEST_PLAN §6.9 (Android Chrome, iOS Safari); TEST_PLAN §6.5 (sentences) | L | ☐ | Online (https://francklin9999.github.io/codeml2026/). End-to-end run on the live URL passes in desktop Chrome with a phone viewport (`app/bench/e2e_browser.mjs`: import, measure both lenses, SVG, STL); every page and the ten error sentences checked at 390 px wide (`app/bench/pages_smoke.mjs`). Real iPhone and Android: TO MEASURE |
| Monture générée | 10 | Frame screen (3D preview, overlay with the gap in mm), `monture.stl`; TEST_PLAN §6.6 (`tools/validate_stl.py`, slicer, print) | F | ☐ | Built; never sliced or printed |
| Qualité du code | 5 | [`../README.md`](../README.md) (local launch), [`ARCHITECTURE.md`](ARCHITECTURE.md), `npm test`, results reproducible with `tools/accuracy_report.py` | L | ☐ | Built; results tables empty |
| Présentation | 10 | [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) §8 (three timed rehearsals), backup video, limits slide | L | ☐ | Script drafted; not rehearsed |

The points of the eight criteria add up to one hundred, as in the brief. Bonuses (contour over rim with the gap in mm, difference of A and B between shots, real print) add no points: they break ties.

## 2. Imposed format (CHALLENGE §5)

| # | Requirement | Evidence (file or screen) | Owner | Done | State today |
|---|---|---|---|---|---|
| F1 | Public HTTPS URL and a QR code of that URL shown during the demo | URL in [`../README.md`](../README.md); `app/public/qr.svg` from `npm run qr -- <url>`; printed QR | L | ☐ | URL live; `app/public/qr.svg` generated and decoded back to the URL (jsQR); printed copies TO DO |
| F2 | No installation, no account, no API key | Fresh phone opens the app by QR (TEST_PLAN §6.9) | L | ☐ | Static app, no key in the code; TO MEASURE on a fresh phone |
| F3 | Mobile first: one hand, recent Chrome (Android) and Safari (iOS), readable on a 6-inch screen | TEST_PLAN §6.9; no overflow at 360 × 640 | L | ☐ | Built; never opened on a phone |
| F4 | Camera built into the app, file import fallback if the camera is refused | Capture screen: "Prendre la photo", "Importer une photo" | L | ☐ | Built (`app/src/capture/`); TO MEASURE on both phones |
| F5 | In-browser processing (recommended); a server only if its URL stays up | [`ARCHITECTURE.md`](ARCHITECTURE.md) §1: no server | L | ☐ | True by design |
| F6 | Free hosting (GitHub Pages or similar); a temporary tunnel is tolerated | `.github/workflows/deploy.yml` at the Git root; `app/README.md` | L | ☑ | GitHub Pages; deploys of `548901c` and `6f54bd9` green (typecheck and tests gate the deploy) |
| F7 | No paid service and no closed API in the final version | [`LICENCES_ET_OUTILS_IA.md`](LICENCES_ET_OUTILS_IA.md); libraries self-hosted under `app/public/vendor/` | L | ☐ | No runtime network call besides the app's own files |
| F8 | Result in under 30 seconds per pair of lenses on a mid-range phone | TEST_PLAN §6.8 ("Pas à pas" timings) | V | ☐ | TO MEASURE |
| F9 | Button that exports the contour as SVG at 1:1 scale | Result screen: "Exporter le contour (SVG 1:1)"; TEST_PLAN §6.6 | F | ☐ | Built; print scale TO MEASURE |
| F10 | Clear message, not a technical error, when the reference is missing, the photo is blurry or the lens is badly placed | TEST_PLAN §6.5; `?demo=1&error=CODE` | V | ☐ | Ten codes, ten French sentences (`app/src/quality/messages.ts`); `CAMERA_DENIED` cannot occur in the shipped flow (the native camera sheet needs no permission; "Importer une photo" is the fallback); TO MEASURE on real failures |
| F11 | One page: a left lens and a right lens, bridge width (18 mm by default), measurements, 3D preview, STL | Home, capture, result and frame screens of `index.html` | F | ☐ | Built; walk it with `?demo=1` |
| D1 | Pre-trained models and public datasets cited with their licence | [`LICENCES_ET_OUTILS_IA.md`](LICENCES_ET_OUTILS_IA.md), [`DONNEES_ET_IA.md`](DONNEES_ET_IA.md) | D | ☐ | To check against what is really used |
| D2 | No personal data in our datasets (faces, names, prescriptions) | `training/data/dataset_card.md`; fixed line on `collect.html`; review of the photos before training | D | ☐ | No dataset yet |
| D3 | No manual annotation of photos taken during evaluation | Automatic pipeline; no touch-up screen exists | V | ☐ | True by design |
| D4 | WhatsApp photos not used for measurement | Capture keeps the original file; instruction sheet and [`COLLECTE_DONNEES.md`](COLLECTE_DONNEES.md) say so | V | ☐ | True by design |
| D5 | Nasal side faces the centre of the frame; the user chooses the eye (left or right) for each lens | Home screen (one entry per eye); sheet labels "ŒIL DROIT", "ŒIL GAUCHE"; `Eye` in the contracts | F | ☐ | Built |
| D6 | Mandatory technologies: none | nothing to prove | L | ☐ | Not applicable |

## 3. Deliverables (CHALLENGE §6)

| # | Deliverable | Expected content | Evidence (file or screen) | Owner | Done | State today |
|---|---|---|---|---|---|---|
| L1 | Web app online | Public HTTPS URL and QR code, testable on a smartphone without installation | URL and QR in [`../README.md`](../README.md) | L | ☐ | Online with QR; a real phone still has to open it (S1) |
| L2 | Source code | Public Git repository (or shared with the jury) with local launch instructions | [`../README.md`](../README.md), `app/README.md` | L | ☑ | https://github.com/Francklin9999/codeml2026 is public (GitHub API `visibility: public`) |
| L3 | "Données et IA" file | Datasets and models (sources, licences), training method, performance measured on our own lenses | [`DONNEES_ET_IA.md`](DONNEES_ET_IA.md), TEST_PLAN §6.2 and §6.10 | D | ☐ | Sources, licences, training method and synthetic results written; performance on our own lenses TO MEASURE |
| L4 | Trained model | Weights loaded by the app, plus a download link if they exceed 100 MB | `app/public/models/lens_seg.onnx` | D | ☑ | v2, 7.9 MB (no link needed), loaded by the live app: Chrome shows "méthode modèle" on the faint-rim fixtures (`app/bench/e2e_browser.mjs`); provenance and SHA-256 in `app/public/models/README.md` |
| L5 | "Pas à pas" page | One photo with its intermediate images (reference, rectification, contour) | [`PAS_A_PAS.md`](PAS_A_PAS.md); "Pas à pas" screen of the app | V | ☐ | Screen built; real-photo images to add |
| L6 | 3D file | `monture.stl` downloadable from the app, for the demonstration pair | Frame screen: "Télécharger monture.stl" | F | ☐ | Built; demo pair not chosen |
| L7 | README | App link, capture rig, technical choices, known limits, AI tools cited | [`../README.md`](../README.md), [`DISPOSITIF_CAPTURE.md`](DISPOSITIF_CAPTURE.md), [`LICENCES_ET_OUTILS_IA.md`](LICENCES_ET_OUTILS_IA.md) | L | ☐ | Written by brief 15; link and limits to complete |
| L8 | Demonstration | 5 minutes on a phone, live, then 2 minutes of questions | [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) | L | ☐ | Not rehearsed |

## 4. Submission checklist (annex of the brief)

Tick at H+23, on the deployed version, no deployment in the last 30 minutes.

| # | Item | How to check | Owner | Done |
|---|---|---|---|---|
| S1 | The URL opens on a brand-new phone | A phone that never opened the app, mobile data, scan the QR | L | ☐ |
| S2 | QR code ready | Two printed copies, scanned with a phone camera | L | ☐ |
| S3 | Rig that can be reassembled in 2 minutes | TEST_PLAN §6.7, a stranger with the instruction sheet; two kits packed | V | ☐ |
| S4 | `monture.stl` downloadable | Downloaded on an iPhone and on an Android, passes `tools/validate_stl.py` | F | ☐ |
| S5 | README with sources and licences | [`../README.md`](../README.md) and [`LICENCES_ET_OUTILS_IA.md`](LICENCES_ET_OUTILS_IA.md) have no `À COMPLÉTER` or `À VÉRIFIER` left | L | ☐ |
| S6 | Rehearsed demo | Three rows filled in [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) §8; backup video plays offline | L | ☐ |
| S7 | Every member can explain their part | Each one answers the questions of [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) §6 marked with their role | all | ☐ |

Also before submitting: no figure in the README, the data file or the slides that is not in [`TEST_PLAN.md`](TEST_PLAN.md) §6; last-known-good tag pushed (`app/README.md`, Deploy).
