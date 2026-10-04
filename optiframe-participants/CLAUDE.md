# OptiFrame: working rules for this folder

## What this is
A 24-hour hackathon project. A static mobile web app (public HTTPS URL, no install, no account, no API key, no paid or closed service) photographs a spectacle lens lying in the window of a printed reference sheet, rectifies the photo, segments the lens, measures width A, height B and perimeter in mm, then generates a 3D-printable frame front (two rims, bridge, hinge tenons) as a watertight STL. All processing runs in the browser, under 30 s per pair, on recent Chrome (Android) and Safari (iOS). The jury compares A and B with a calliper: full marks at a mean error of 1 mm or less.

Read first: `CHALLENGE.md` (rules and rubric), `docs/ARCHITECTURE.md` (pipeline, contracts, layout).

## Rules
1. **One module = one owner.** The table in `docs/ARCHITECTURE.md` §3 says which files belong to which module. Edit only inside the module you were asked to change; a change needed elsewhere is reported, not made.
2. **Never state an accuracy figure that is not in the TEST_PLAN results** (`docs/TEST_PLAN.md` §6). The same goes for phone timings, model metrics and print results. Until measured, write `TO MEASURE` (English) or `À COMPLÉTER` (French). Numbers from synthetic tests are labelled as synthetic.
3. **Never change `app/src/contracts.ts`** without telling every owner; the same block is copied in `docs/ARCHITECTURE.md` §2.
4. Failures leave a module as `OptiError` with a code of `ErrorCode`; no other exception, and no technical text on screen (`quality/messageFor` gives the French sentence).
5. Keep it small: no extra feature, no abstraction for later, comments only where the reason is not obvious. No UI framework, no CDN at runtime (third-party libraries are self-hosted under `app/public/vendor/`).
6. No personal data in photos or datasets (faces, names, prescriptions). No manual annotation of evaluation photos.
7. AI tools used on the project are declared in `docs/LICENCES_ET_OUTILS_IA.md` as they are used.

## Conventions
- Millimetres everywhere outside image buffers; rectified images are 10 px/mm (`PX_PER_MM`).
- Board frame: origin at the top-left corner of the lens window, x right, y down.
- Contour: closed polygon `Pt[]`, counter-clockwise (positive shoelace in the y-down frame), 720 points, last point not repeated, lens concave side down. Right eye: nasal side +x. Left eye: nasal side -x.
- A and B: boxing system, extents along the board x axis (A) and y axis (B).
- `Rectified.H` maps board mm to photo pixels. The frame mesh has y up, z from the print bed.
- User-facing text and jury documents are in French; code, comments and internal documents are in English.

## Commands
```
cd app
npm ci                  # first time only; do not add or update packages casually
npm run dev             # http://localhost:5173 ; add ?demo=1 to walk the screens without a camera
npm run typecheck       # tsc --noEmit
npm test                # Vitest; loads OpenCV.js, allow several minutes
npx vitest run src/measure      # one module only
npm run build           # dist/, base './'
npm run size            # after a build: fails over 250 kB gzip of initial JavaScript
npm run qr -- https://<user>.github.io/<repo>/      # writes public/qr.svg
```
Other pages of the dev server: `/eval.html` (batch evaluation), `/collect.html` (data collection on the phone), `/lightbox.html` (backlight).

Python tools (3.11+), one virtual environment per folder (`rig/.venv`, `tools/.venv`, and one for `training/`):
```
cd rig && .venv/Scripts/python make_board.py --fixtures      # sheet PDFs, board_spec.json, test fixtures (needed by npm test)
.venv/Scripts/python set_print_scale.py <measured mm>        # after measuring the printed 100 mm ruler
.venv/Scripts/python -m pytest tests -q
cd .. && tools/.venv/Scripts/python -m pytest tools/tests -q
tools/.venv/Scripts/python tools/accuracy_report.py results.csv own_lenses.csv
tools/.venv/Scripts/python tools/validate_stl.py monture.stl
```
On macOS and Linux use `.venv/bin/python`. Deployment: push to `main`; the workflow is `.github/workflows/deploy.yml` at the Git repository root.

## Before saying "done"
- Typecheck and the tests of the module you touched pass; say what you ran and its result.
- A new threshold is a named constant, marked provisional until a real photo confirms it.
- Git-ignored and never committed: `node_modules/`, `dist/`, `.venv/`, `training/_local/`, `rig/out/fixtures/`, model checkpoints.
