export const meta = {
  name: 'optiframe-wave',
  description: 'OptiFrame: run one wave of briefs (parallel builders, independent adversarial verification with fix loop, whole-project integration check)',
  whenToUse: 'Pass args {wave: 0|1|2|3}. Wave 0 = brief 01; wave 1 = 02-09,11,12,13; wave 2 = 10,14; wave 3 = 15,16 plus audit.',
  phases: [
    { title: 'Build', detail: 'one builder per brief, in parallel' },
    { title: 'Verify', detail: 'independent verifier per brief, fix loop up to 2 rounds' },
    { title: 'Integrate', detail: 'whole-project typecheck, tests, build, cross-module chain; fix attributable failures' },
    { title: 'Audit', detail: 'wave 3 only: rubric coverage, contract consistency, end-to-end regression test' },
  ],
}

const ROOT = 'C:/Users/raybo/Documents/projets/CodeML_2026/codeml2026/optiframe-participants'
const BACKUP = ROOT + '/agents/orchestration/docs_backup'
const wave = (args && args.wave !== undefined) ? args.wave : 0
const WAVES = { 0: ['01'], 1: ['02', '03', '04', '05', '06', '07', '08', '09', '11', '12', '13'], 2: ['10', '14', '17'], 3: ['15', '16'] }
const ids = WAVES[wave]
if (!ids) throw new Error('unknown wave ' + wave)

const bullets = (a) => a.map((x) => '- ' + x).join('\n')

const OWNERSHIP = [
  '01: app/package.json, app/vite.config.ts, app/tsconfig.json, app/src/contracts.ts, app/src/test/, app/src/swRegister.ts, app/public/sw.js, app/public/manifest.webmanifest, .gitignore, ../.github/workflows/deploy.yml, app/README.md, the stub index.ts files',
  '02: rig/ (make_board.py, set_print_scale.py, tests, README, out/), app/public/board_spec.json, app/public/lightbox.html',
  '03: app/src/capture/',
  '04: app/src/vision/rectify.ts, opencv.ts, homography.ts, app/public/vendor/opencv/',
  '05: app/src/vision/segmentClassic.ts',
  '06: app/src/measure/, app/public/bias.json',
  '07: app/src/quality/',
  '08: app/src/frame/, app/public/vendor/manifold/',
  '09: app/src/export/',
  '10: app/index.html, app/src/main.ts, app/src/worker.ts, app/src/ui/, app/src/pipeline.ts',
  '11: training/data/, training/requirements.txt',
  '12: training/model/',
  '13: app/src/vision/segmentModel.ts, app/public/vendor/ort/, app/public/models/README.md',
  '14: app/eval.html, app/src/eval/, tools/, data/',
  '15: README.md, docs/DISPOSITIF_CAPTURE.md, docs/PAS_A_PAS.md, docs/DONNEES_ET_IA.md, docs/LICENCES_ET_OUTILS_IA.md',
  '16: docs/ARCHITECTURE.md, docs/TEST_PLAN.md, docs/RUBRIC_CHECKLIST.md, docs/RISKS.md, CLAUDE.md, link fixes in CHALLENGE.md/docs/WINNING_PLAN.md/PLAN_24H.md/DEMO_SCRIPT.md',
  '17: app/collect.html, app/src/collect/, docs/COLLECTE_DONNEES.md',
  'Shared small files edited by the orchestrator between waves (attribute to 01 unless clearly another brief): app/vite.config.ts, app/src/capture/index.ts (03), docs/MENTOR_NOTES.md',
].join('\n')

const B = {
  '01': { file: '01_app-scaffold-deploy.md', name: 'app scaffold and deployment', effort: 'high', venv: 'none (no Python in this brief)',
    extra: 'You run alone: no other agent is working yet. You ARE allowed (and expected) to run npm install in app/ because installing every dependency is your job (item 7 of the brief). Verify with npm ls --depth=0. app/ does not exist yet: create it.',
    hints: [
      'Extract the contracts code block from the brief Shared context with a script and diff it against app/src/contracts.ts: the code must be identical.',
      'Each of the 8 entry-point stub files exists at the path of the table, has the exact signature, and throws OptiError with code LOAD_FAILED and detail not implemented. Run tsc.',
      'Serve a COPY of app/dist from a sub-path (a temp dir like a/b/dist served with python -m http.server) and fetch index.html plus every asset it references: all 200, no absolute / URLs, no CDN URL anywhere in package.json, index.html, dist.',
      '.github/workflows/deploy.yml parses as YAML, triggers on push to main and workflow_dispatch, builds optiframe-participants/app, publishes dist to Pages with the right permissions.',
      'npm ls --depth=0 shows every dependency of item 7 (opencv-js, js-aruco2, manifold-3d, clipper2-js, earcut, three, onnxruntime-web, vitest, jsdom, qrcode, pngjs and the @types).',
      'sw.js: read it. Cache-first only for vendor/ and models/, network-first with cache fallback for the rest, old caches deleted, no caching of POST/non-GET. swRegister.ts: no-op without navigator.serviceWorker, nosw=1 path unregisters and clears caches.',
      'setup.ts polyfill: constructors (w,h) and (data,w,h), data is Uint8ClampedArray of length 4*w*h, throws on a wrong length like the real ImageData, instanceof works, and it does not override a real global ImageData.',
      'The worker test calls the handler with stubs and gets ok:false code LOAD_FAILED. Check the handler never lets another exception escape.',
    ] },
  '02': { file: '02_reference-sheet.md', name: 'reference sheet and light-box', effort: 'high', venv: 'rig/.venv',
    extra: 'Suggested packages in rig/.venv: opencv-contrib-python (cv2.aruco; check that cv2.aruco exists in the installed build), numpy, reportlab, pytest, pypdf. Fixtures are regenerated by the script and are git-ignored, but they must exist on disk when you finish because briefs 04 and 10 use them.',
    hints: [
      'Rerun make_board.py --fixtures from the builder venv and check the outputs are regenerated and the JSON is stable between two runs.',
      'Open both PDFs with pypdf: page size equals A4 (210x297 mm) and US Letter (215.9x279.4 mm); then check the ruler is 100 mm and the window is 80x65 mm in the drawing (render with PyMuPDF if it is installed in a temp venv, or read the content stream), and that the printed content fits 180x150 mm.',
      'board_spec.json: at least 12 markers, unique ids, side 15 mm, no marker closer than 4 mm to the window, corner order TL,TR,BR,BL, negative coordinates for markers left of or above the window, printScale 1, dictionary DICT_4X4_50, valid against the BoardSpec contract.',
      'With your own code (not the builder test), detect the markers in 3 fixtures, fit a homography with cv2.findHomography, measure the drawn shape and compare to the JSON truth: within 0.1 mm.',
      'Look at the PNG of at least two fixtures (and a render of the sheet if you can produce one) with the Read tool: the labels HAUT, ŒIL DROIT, ŒIL GAUCHE and the ruler text are present, the guide line ticks are outside the window, the shapes look like lenses with blur and noise.',
      'lightbox.html: no external URL, wake lock feature-detected, full-screen button, brightness hint, tracing-paper hint, works with no script error when Wake Lock is missing.',
      'set_print_scale.py: run on copies of the two JSON files: 99.0 gives 0.99, 90 and 110 rejected with a non-zero exit, both copies stay in sync.',
    ] },
  '03': { file: '03_capture.md', name: 'camera capture and file import', effort: 'medium', venv: 'none',
    extra: 'Tests run in the node environment with fakes; use a jsdom docblock only where the DOM is needed.',
    hints: [
      'EXIF parser fuzz: truncated JPEG, no APP1, big-endian (MM) and little-endian (II) TIFF headers, orientation values 2,4,5,7 (mirrored or transposed) and 0 or 9 (invalid), IFD offsets out of range, FocalLengthIn35mmFilm absent or zero. It must never throw: fall back to orientation 1 and focal undefined.',
      'Downscale rule: 4032x3024 unchanged, 8000x6000 reduced to at most 4096 on the long side and 16 megapixels, a 5000x5000 square reduced by the area rule, portrait images, aspect ratio preserved within rounding.',
      'capturePhoto and pickFile: the hidden input is removed from the DOM after use, the cancel path does not leave the promise hanging forever or leak listeners, calling capturePhoto 5 times in a row leaks nothing. NotAllowedError maps to OptiError CAMERA_DENIED and no raw DOMException escapes.',
      'The module imports in plain Node and in a worker with no DOM access at import time.',
    ] },
  '04': { file: '04_rectify.md', name: 'marker detection and rectification', effort: 'high', venv: 'none',
    extra: 'OpenCV.js is in app/node_modules (@techstark/opencv-js). Loading it under Vitest in Node may need awaiting its runtime-initialised promise and a longer test timeout. rig/out/fixtures/ (brief 02) may or may not exist while you work: render your own scenes from app/public/board_spec.json or rig/out/board_spec.json if present, otherwise build a board spec in the test. Report the exact ArUco API names you found.',
    hints: [
      'In a throwaway vitest file (put it in app/tests/_verify04.test.ts and delete it afterwards), render the board with a homography different from the tests (tilt 25 degrees, rotation 10, different scale), draw a 50.0 mm shape in the window: after rectify it measures 50.0 within 0.1 mm.',
      'Occlude 3 markers: still succeeds. Occlude so that fewer than 4 remain: NO_REFERENCE.',
      'printScale direction: a sheet printed at 99 percent has its marker positions at nominal times 0.99 on paper; check rectify with printScale 0.99 produces true-mm geometry in that case and reason about the sign in the code.',
      'Worker safety: grep rectify.ts, opencv.ts, homography.ts for window, document, HTMLCanvasElement, new Image: none at module level or in the hot path (only self or globalThis).',
      'The OpenCV.js file in app/public/vendor/opencv/ is byte-identical to the one in node_modules (compare hashes), its licence file is present, the loader uses no CDN and resolves the file relative to the page so it works from a sub-path.',
      'homography.ts with 20 percent outliers: run 100 random trials, report the success rate. Degenerate input (collinear points, fewer than 4) throws OptiError NO_REFERENCE, never a raw error.',
      'REFERENCE_TILTED triggers for a board tilted more than 35 degrees and for a high reprojection error, BLURRY for a blurred scene, each with its own test.',
    ] },
  '05': { file: '05_segment-classic.md', name: 'classical segmentation', effort: 'high', venv: 'none',
    extra: 'Pure typed arrays; no OpenCV. Build synthetic images inside the tests.',
    hints: [
      'Generate shapes of your own: aviator-like, rounded rectangle with a 2 mm notch, circle 45 mm, ellipse 65x45 rotated 8 degrees, on several noise seeds and lighting gradients: IoU against the known filled shape at least 0.98 (0.97 acceptable for the notch).',
      'Time the segmenter on 800x650 five times: all under 300 ms; report the max.',
      'Error codes with cases not copied from the tests: LENS_OUT_OF_WINDOW (shape touching the border), GLARE (more than 5 percent saturated inside), NO_LENS (empty bright window, dust only, faint rim below the contrast constant).',
      'Mm-based thresholds: the same scene rendered at pxPerMm 10 and 20 gives the same mask area in mm2 within 2 percent.',
      'Degenerate input (1x1, all zeros, all 255) throws only OptiError.',
      'Tinted filled lens, thick dark band (outer boundary measured), faint rim: each passes.',
    ] },
  '06': { file: '06_measure.md', name: 'contour refinement and boxing', effort: 'high', venv: 'none',
    extra: 'Build synthetic Rectified images and Masks inside the tests. Brief 05 runs at the same time: do not import segmentClassic; make masks yourself.',
    hints: [
      'Through the full measureLens, on blurred dark-ring images you generate yourself at 10 px/mm with ring width 0.5 to 1.5 mm and blur sigma 0.5 to 1.5 px (ellipse 50x36, rotated rectangle, rounded rectangle 52x34): A and B within 0.05 mm, perimeter within 0.3 percent.',
      'Exactly 720 points. State and verify the orientation convention in the board frame (y down): compute the shoelace sum and report its sign. Briefs 07 and 08 rely on the same convention; 08 must normalise any orientation, which is checked in wave 1 by the integration step.',
      'Parallax D=300, h=3 gives a 0.99 factor about the window centre (the window centre is (40, 32.5) mm for an 80x65 window); D undefined means no scaling.',
      'Non-identity bias (a0=0.3, a1=1.0, b0=-0.2, b1=1.01): contour extents equal the reported A and B within 0.01 mm and the perimeter is recomputed.',
      'rotationWarningDeg: rectangle 52x34 rotated 8 degrees gives about 8; near-circular gives none or 0; check range and sign.',
      'Empty or tiny masks throw only OptiError (NO_LENS). loadBias with a missing file or malformed JSON behaves as documented (identity or LOAD_FAILED) and is consistent with brief 10 which maps load failures to LOAD_FAILED.',
      'Left eye versus right eye: eye is stored in the measurement; contour is not mirrored by measureLens (mirroring, if any, happens in frame layout).',
    ] },
  '07': { file: '07_quality-fusion.md', name: 'multi-shot fusion and messages', effort: 'medium', venv: 'none',
    extra: 'Do not import from app/src/measure/ (the brief says to write a local helper): brief 06 is being written at the same time.',
    hints: [
      'Diff the 10 messageFor strings character by character against the sentences in the brief (accents, apostrophes, guillemets as written).',
      'Fusion statistics: 50 random seeds of 5 noisy ellipses (0.2 mm radial noise): the fused A and B error is no worse than the mean single-shot error in at least 90 percent of trials.',
      'Outlier: one shot enlarged by 2 mm is rejected with 3 and with 5 shots and moves the result by no more than 0.05 mm; with exactly 2 shots behaviour is explicit (spread above 0.6 gives INCONSISTENT_SHOTS).',
      'Contours with different point counts and different start angles fuse correctly; the orientation sign of the output equals the sign of the inputs.',
      'MAX_CENTRE_SHIFT_MM: kept shots shifted by 0.5 mm pass, by 1.5 mm throw INCONSISTENT_SHOTS; the constant is named.',
      'Single shot returns the same measurement (nShots 1); the fused quality fields are the worst-of rule.',
      'Only OptiError escapes; empty array input is handled.',
    ] },
  '08': { file: '08_frame-generator.md', name: 'parametric frame front', effort: 'high', venv: 'none',
    extra: 'manifold-3d and the fallback clipper2-js and earcut are in app/node_modules. Report the exact manifold-3d API names you verified. Free every WASM object. Keep generation under 2 s in the test environment.',
    hints: [
      'Write your OWN mesh checker (not the builder one): every undirected edge used by exactly two triangles in opposite directions, no zero-area triangle, one connected component (merge coincident vertices at 1e-4), signed volume positive.',
      'Random sweep beyond the tests: 30 random combinations (clearance 0.1-0.3, bridge 14-22, rim 2.5-5, lip 0.3-0.7, thickness 3-5) with random shape pairs including a superellipse and an aviator-like outline: all pass and each takes under 2 s.',
      'Layout: right lens on the -x side with its nasal edge (its max x) at -bridge/2, left lens on the +x side with its nasal edge (min x) at +bridge/2: the distance between the nasal edges equals bridgeMm within 0.01. Check the exact definition against the code (contour edge, not seat edge).',
      'Input orientation: the same contour reversed (clockwise) gives a valid, identical result (the code normalises). A contour with a repeated closing point, duplicate points or a small self-intersection still produces a valid mesh.',
      'Seat outline distance to the input contour equals clearance within 0.02 mm (measure it yourself with point-to-polygon distance).',
      'Topology: tenon through-holes exist. Compute the Euler characteristic and genus; two rims plus two tenon holes suggests genus 4: report your number and explain any difference.',
      'Memory: grep that every manifold or cross-section object is deleted; run 20 generations in a loop and confirm no growth beyond noise.',
      'The vendored WASM (if used) is in app/public/vendor/manifold/ and resolved by a relative URL that works from a sub-path and in Node tests.',
    ] },
  '09': { file: '09_exports.md', name: 'SVG, STL and JSON exports', effort: 'medium', venv: 'none',
    extra: 'Build LensMeasurement and FrameResult values yourself inside tests.',
    hints: [
      'Parse the SVG with a real XML parser (jsdom DOMParser): width and height end with mm and match the viewBox; the path bounding box (parse the d attribute yourself) equals A x B within 0.01; the scale bar is exactly 50 units; the text Imprimer à 100 % (taille réelle) is present; special characters are XML-escaped; the eye label is correct.',
      'SVG fits 190x250 mm for A and B up to 75 mm.',
      'STL: independent re-parse (numpy frombuffer in a temp Python script, or DataView): length equals 84 + 50 n, little-endian, header 80 bytes, attribute bytes zero, normals are unit length and agree with the right-hand rule of the vertex order on a cube.',
      'saveBlob: object URL plus temporary anchor with download attribute, anchor removed, URL revoked after a delay, no use of window.open; works from a click handler in a jsdom test.',
      'measurementToJson: stable key order, round-trip equality, no NaN or Infinity serialised silently, date and version come from arguments and the clock is never read.',
      'File names exactly contour-gauche.svg, contour-droit.svg, monture.stl, mesures.json; Eye L maps to gauche and R to droit.',
    ] },
  '10': { file: '10_ui-flow.md', name: 'screens and pipeline orchestration', effort: 'high', venv: 'none',
    extra: 'The wave-1 modules now exist: read their real code and wire them (check what they export: setBias, loadBias, rotationWarningDeg, isModelAvailable, getLastTimings, registerServiceWorker). Brief 14 runs at the same time and may import your pipeline.ts: keep measureOne(photo, eye) exported with a stable, documented return type and add that type to the top of pipeline.ts as a comment. Do not use the Browser pane (the orchestrator uses it). Verify UI with jsdom tests and a production build.',
    hints: [
      'Run the ui and pipeline tests plus a production build. In a jsdom test walk ?demo=1 through all five screens and produce monture.stl: parse the downloaded Blob as binary STL and check its length formula.',
      'Pipeline probes with mocked modules: NO_LENS then model fallback when available; model unavailable gives the NO_LENS message; unknown Error, TypeError and a thrown string map to LOAD_FAILED; every ErrorCode shows exactly its messageFor sentence; the visible DOM never contains Error, undefined, stack lines.',
      'The real-fixture test without mocks: run it and report the actual A and B errors against the fixture JSON truth.',
      'CSS reading: buttons at least 48 px high, no fixed width above 360 px, viewport meta present, inputs at least 16 px font (iOS zoom), no horizontal overflow rule, dynamic viewport units used sensibly.',
      'sessionStorage mirror keeps only measurements (no ImageData, no base64 images, no blobs).',
      'worker.ts: the measure message carries photo, spec, eye, bias; setBias is called; reply shape is ok true/result or ok false/code; main.ts calls registerServiceWorker.',
      'The four progress sentences match the brief exactly; all UI text is French; the 3D preview is a dynamic import (three.js is not in the initial chunk: check the build output).',
      '?demo=1&error=CODE works for every code.',
    ] },
  '11': { file: '11_dataset-tools.md', name: 'dataset tools', effort: 'high', venv: 'training/data/.venv',
    extra: 'Suggested packages in the venv: numpy, opencv-contrib-python, pillow, pytest. Brief 02 produces rig/make_board.py and board_spec.json at the same time: for your autolabel tests build your own small board and spec inside the test (do not import from rig/); if app/public/board_spec.json exists you may read it as an example only. Never generate the large dataset in the repository; tests use tmp paths.',
    hints: [
      'Run synth.py with your own seed for 12 samples: sizes 800x650, mask area within 1 percent of the analytic area, rotation within plus or minus 10 degrees, aspect 0.6-0.95, width 35-65 mm. Open 3 images and their masks with the Read tool and judge plausibility (dark rim, highlights, background magnification).',
      'autolabel on a synthetic group: IoU at least 0.97; shifting one photo by 5 px makes the group rejected; a shift of 1 px keeps it; the output index.csv has the columns file, lensId, pos, cond, source.',
      'split.py: for 100 random sets of lens ids no id appears in two splits; synthetic only in train; proportions near 70/15/15; deterministic for a seed.',
      'File naming lensId_pos_cond.jpg: the parser handles lensIds with underscores or documents and enforces a rule, with a test.',
      'capture_protocol.md and dataset_card.md are in French, one page for the protocol, every number in the card is À COMPLÉTER, the privacy statement is present.',
      'autolabel --qc N writes N overlay images.',
      'requirements.txt installs on Python 3.13.',
    ] },
  '12': { file: '12_train-export.md', name: 'train and export the segmenter', effort: 'high', venv: 'training/model/.venv',
    extra: 'Install the CPU build of torch to save time (pip install torch --index-url https://download.pytorch.org/whl/cpu), plus segmentation_models_pytorch, albumentations, onnx, onnxruntime, numpy, pytest. Python is 3.13: if a wheel is missing, report it and use the closest working version. Brief 11 is written at the same time: do not import from training/data; your smoke test generates its own 16 tiny synthetic images and masks (ellipses and rectangles with noise) inside the test. Never write weights or models under app/. Keep smoke-test outputs in a tmp dir.',
    hints: [
      'Re-run the pytest smoke test on CPU and time it. Load the exported ONNX with onnx.checker: opset 17, input named input with shape 1x3x320x384, output named logits with shape 1x1x320x384. Parity against PyTorch at most 1e-3 on 3 random inputs you generate. The int8 file loads in onnxruntime and its masks agree with the float model (IoU on a few samples); report both sizes.',
      'evaluate.py unit check: a perfect prediction gives IoU 1, boundary F 1, A and B error 0; a prediction shifted by 3 px gives the expected nonzero numbers; the Otsu baseline is computed on the same split; per-condition and overall rows exist in metrics.md and metrics.json.',
      'Preprocessing contract with brief 13: RGB order, ImageNet mean and std, input H=320 and W=384 (not swapped), resize direction.',
      'README: each licence row was read in package metadata (pip show or the package licence file): spot check three; no metric figure appears in any document except as produced by evaluate.py.',
      'No file is written under app/; no .pt or .onnx outputs sit in tracked locations.',
      'train.py --sources real|synth|both works on the tiny set; seeds are fixed: two tiny runs give the same first-epoch loss.',
      'Encoder name used with segmentation_models_pytorch exists in the installed version; the smoke test needs no network (encoder_weights None).',
    ] },
  '13': { file: '13_model-in-browser.md', name: 'segmenter in the browser', effort: 'high', venv: 'none',
    extra: 'onnxruntime-web is in app/node_modules. Tests use a fake session; the int8 check needs a tiny quantised model: build one in the OS temp directory (a throwaway Python venv with onnx is fine there, never inside the repo) or find one in node_modules, and run it with onnxruntime-web on the WASM provider in Node. If you cannot, report UNVERIFIED instead of guessing. The model file lens_seg.onnx does not exist in the repository and must not be created by you.',
    hints: [
      'Preprocessing by hand-computed values: a 2-colour image gives tensor layout NCHW, RGB order, values (c/255 - mean)/std with mean 0.485,0.456,0.406 and std 0.229,0.224,0.225, size H=320 W=384.',
      'Postprocessing with a fake session returning crafted logits: largest component kept, holes filled, resized back to the rectified size, a mask touching the border gives LENS_OUT_OF_WINDOW, a tiny area gives NO_LENS.',
      'Missing model (404 or a failing session): isModelAvailable false, segmentModel throws OptiError LOAD_FAILED, and no unhandled promise rejection (install a process unhandledRejection listener in a probe).',
      'ort.env.wasm.numThreads is 1 before the session is created; wasmPaths points to vendor/ort/ relative to the document base so it works from a sub-path; the WASM files in app/public/vendor/ort/ match the installed onnxruntime-web version.',
      'The int8 claim: confirm the builder really ran an int8 model on the WASM provider or marked it UNVERIFIED.',
      'No DOM or OffscreenCanvas use at module level or in preprocessing (worker-safe); getLastTimings exists and returns four numbers.',
    ] },
  '14': { file: '14_eval-tools.md', name: 'evaluation page and validation tools', effort: 'high', venv: 'tools/.venv',
    extra: 'Suggested packages in tools/.venv: numpy, trimesh, pytest. Build tools/ and data/ first (they do not depend on anything), the eval page last. Brief 10 is written at the same time: check at the end whether app/src/pipeline.ts exists and what measureOne returns; if it does not exist yet, call rectify, segmentClassic and measureLens directly and say so in the report.',
    hints: [
      'Create your own synthetic results file with a known +0.4 mm bias and noise: accuracy_report.py recovers the bias within 0.05, the predicted-score formula gives 30, 30, 15, 0 at MAE 0.5, 1, 2.5, 4, limits of agreement and proportional-bias slope are reported, the bootstrap gives a median and 5th percentile, the leave-one-lens-out fit really leaves the lens out (read the code), bias.json is identity when the correction does not help.',
      'validate_stl.py: a cube passes with exit 0; a cube with one triangle removed fails non-zero; a flipped-normal triangle fails the winding check; two disjoint cubes fail the single-body check; output is one line per check.',
      'Variance components: build a file with a known between-phone offset and check the share is recovered; missing factor gives not estimable.',
      'eval page: the file-name parser handles lens_01_pixel7_2.jpg, uppercase extension, underscores in lensId (documented rule), missing rep; the CSV writer escapes commas and quotes; the header columns equal the brief.',
      'eval.html is not linked from index.html and appears in dist after a build; data/own_lenses.template.csv has exactly the columns of the brief and two rows marked as examples.',
    ] },
  '15': { file: '15_docs-jury.md', name: 'jury documents (French)', effort: 'high', venv: 'none',
    extra: 'Everything is built by now: describe only what exists (read app/, rig/, training/, tools/). You may run read-only git commands and npm run listing. Do not run npm install.',
    hints: [
      'Write and run a link checker over README.md and docs/*.md (relative links, anchors when present): all resolve. Image placeholders under docs/img are marked À COMPLÉTER, not silently broken.',
      'Search the owned files for digits followed by mm, %, ms, s or points, and check each is a spec value from CHALLENGE.md or a brief, or marked À COMPLÉTER.',
      'The 6-step assembly is numbered, self-contained and short enough for one printed page (count lines and characters: report them).',
      'Licence table versus reality: for 5 random packages from app/package.json and the requirements files, read the licence in node_modules/<pkg>/package.json or pip metadata and compare; unknown rows say À VÉRIFIER.',
      'The local-launch commands in README.md equal those of app/README.md and the scripts that exist in app/package.json.',
      'The vocabulary of the brief is used (verre, monture, cercle, pont, tenon, pied à coulisse, dispositif de capture, système boxing); no English prose remains; every file path or feature described exists.',
    ] },
  '16': { file: '16_docs-internal.md', name: 'internal documents and link repair', effort: 'high', venv: 'none',
    extra: 'Everything is built by now. Pristine copies of CHALLENGE.md and docs/ (before your link repairs) are in ' + BACKUP + ' so that you and the verifier can diff them. Your link checker lives in the OS temp directory and is not committed.',
    hints: [
      'Run your own link checker over every .md file in the project tree (skip node_modules): zero broken relative links. Diff each of the four repaired documents against the pristine copy in ' + BACKUP + ': only link targets changed, nothing else.',
      'The four repaired links point to the right briefs: measurement to 04/05/06/07, frame to 08, web app to 03/10, deployment to 01.',
      'RUBRIC_CHECKLIST: parse the points column and check the sum is 100; there are rows for every rubric line of CHALLENGE.md section 4, every bullet of section 5, the deliverables of section 6 and the submission checklist.',
      'CLAUDE.md has fewer than 60 lines and contains the rules: one module = one owner brief, never state an accuracy figure that is not in the TEST_PLAN results, work/stratN are scratch.',
      'RISKS.md has at most 15 rows with the five columns. TEST_PLAN thresholds equal the constants in code (MAX_SPREAD_MM 0.6, MAX_CENTRE_SHIFT_MM, MIN_SHARPNESS, MAX_REPROJ_MM) and no result cell is filled.',
      'ARCHITECTURE.md: the Data contracts section equals the contracts block of the briefs; the repository layout equals the real tree (compare with a directory listing).',
    ] },
  '17': { file: '17_data-collection.md', name: 'data collection page for the phone', effort: 'high', venv: 'none (a throwaway Python snippet for the zipfile check is fine in the OS temp directory)',
    extra: 'The wave-1 modules exist (read agents/WAVE1_INTERFACES.md). capture now exports chooseOriginalFile and decodeFile. Briefs 10 and 14 run at the same time: pipeline.ts (brief 10) will export measureOne(photo: Photo, eye: Eye): Promise<LensMeasurement>; use measureAdapter.ts until it exists, and check at the end. data/own_lenses.template.csv comes from brief 14 at the same time: if it is missing use the columns written in your brief. The page must work offline from a sub-path and must not need any server. Do not use the Browser pane (the orchestrator uses it).',
    hints: [
      'File names: all three modes produce exactly the documented patterns; rep increments per lensId and phone; identifiers with underscores or spaces are refused or sanitised as documented; names are unique and filesystem-safe on Windows (no colon, no slash).',
      'ZIP: re-read the archive with Python zipfile from a throwaway script (testzip passes, names, sizes, CRC), with a 0-byte file, a 49 MB file, and a set that must split into 2 parts; an empty export is refused; entry names use forward slashes; the stored original bytes are byte-identical to the input File bytes (compare SHA-256).',
      'CSV: own_lenses.csv columns equal data/own_lenses.template.csv exactly (read both); results.csv columns equal the eval page header of brief 14 when it exists; a note with a comma, a quote and a newline round-trips through Python csv.',
      'Storage: add, list, delete, mark exported with the fake IndexedDB; a quota-exceeded error is shown as a French sentence, not an exception; delete-exported never removes a non-exported photo (test); nothing is deleted without the confirmation step.',
      'Measurement path: a failed shot (OptiError) is stored with its code and shown via messageFor; unknown exceptions map to the LOAD_FAILED message; the signed error against the calliper median is computed correctly (median of three, sign = measured minus caliper) and a spread above 0.2 mm is flagged.',
      'Privacy: no fetch or XMLHttpRequest or sendBeacon in the collect code (grep), manifest.csv contains no name field, the fixed privacy line is on the page.',
      'Build: npm run build emits collect.html and its chunk; asset URLs are relative so the page works from a sub-path; the page is linked from the home screen by brief 10 (check later in integration, not a blocker here).',
      'UI: French text, buttons at least 48 px, no horizontal overflow rule, inputs with 16 px font (iOS zoom), decimal keypad for caliper fields (inputmode decimal), object URLs for thumbnails are revoked.',
    ] },
}

const BUILD_SCHEMA = {
  type: 'object',
  properties: {
    briefId: { type: 'string' },
    status: { type: 'string', enum: ['done', 'partial', 'blocked'] },
    filesWritten: { type: 'array', items: { type: 'string' } },
    testCommands: { type: 'array', items: { type: 'string' } },
    testsSummary: { type: 'string' },
    doneWhen: { type: 'array', items: { type: 'object', properties: { item: { type: 'string' }, met: { type: 'boolean' }, evidence: { type: 'string' } }, required: ['item', 'met', 'evidence'] } },
    libraryFindings: { type: 'array', items: { type: 'string' } },
    toMeasure: { type: 'array', items: { type: 'string' } },
    contractProblems: { type: 'array', items: { type: 'string' } },
    outOfScopeChangesNeeded: { type: 'array', items: { type: 'string' } },
    interfaceNotes: { type: 'array', items: { type: 'string' } },
    strategyLog: { type: 'array', items: { type: 'string' } },
  },
  required: ['briefId', 'status', 'filesWritten', 'testCommands', 'testsSummary', 'doneWhen', 'strategyLog'],
}
const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    briefId: { type: 'string' },
    pass: { type: 'boolean' },
    testsRerun: { type: 'string' },
    doneWhenChecked: { type: 'array', items: { type: 'object', properties: { item: { type: 'string' }, met: { type: 'boolean' }, evidence: { type: 'string' } }, required: ['item', 'met', 'evidence'] } },
    blockers: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, problem: { type: 'string' }, howToFix: { type: 'string' } }, required: ['file', 'problem', 'howToFix'] } },
    minor: { type: 'array', items: { type: 'string' } },
    scopeViolations: { type: 'array', items: { type: 'string' } },
    inventedFigures: { type: 'array', items: { type: 'string' } },
    strategyMisses: { type: 'array', items: { type: 'string' } },
    probesRun: { type: 'array', items: { type: 'string' } },
  },
  required: ['briefId', 'pass', 'testsRerun', 'doneWhenChecked', 'blockers'],
}
const FIX_SCHEMA = {
  type: 'object',
  properties: { fixed: { type: 'array', items: { type: 'string' } }, remaining: { type: 'array', items: { type: 'string' } }, testsAfter: { type: 'string' } },
  required: ['fixed', 'remaining', 'testsAfter'],
}
const INTEG_SCHEMA = {
  type: 'object',
  properties: {
    pass: { type: 'boolean' },
    commands: { type: 'array', items: { type: 'object', properties: { cmd: { type: 'string' }, ok: { type: 'boolean' }, summary: { type: 'string' } }, required: ['cmd', 'ok', 'summary'] } },
    chain: { type: 'array', items: { type: 'object', properties: { stage: { type: 'string' }, ok: { type: 'boolean' }, detail: { type: 'string' } }, required: ['stage', 'ok', 'detail'] } },
    failures: { type: 'array', items: { type: 'object', properties: { owner: { type: 'string' }, file: { type: 'string' }, message: { type: 'string' }, suggestedFix: { type: 'string' } }, required: ['owner', 'file', 'message', 'suggestedFix'] } },
  },
  required: ['pass', 'commands', 'chain', 'failures'],
}

const RULES = [
  'Write only files listed under "You own" in your brief. Never edit another brief, another builder file, or the briefs themselves. A needed change elsewhere goes in outOfScopeChangesNeeded.',
  'Never run git add, commit, checkout, stash, reset, clean or restore. Never run npm install, ci, update, uninstall or remove (every dependency was installed by brief 01 in app/node_modules; if a package you expect is missing, use the fallback of the brief and report it). Exception: brief 01 installs.',
  'TypeScript: from ' + ROOT + '/app run npx vitest run on your own test files or folder, and npx tsc --noEmit -p . . tsc errors in files you do not own come from other builders mid-edit: ignore them but keep your own files clean. Never run the whole suite while other builders edit.',
  'Python: create a virtual environment inside your own directory (see the venv line), install only into it, run python and pytest from it. The machine is Windows with Python 3.13. If a package has no wheel for 3.13 say so and use the closest working alternative. Never touch the global Python.',
  'Shell is Windows: Git Bash and PowerShell exist. Scratch files go in the OS temp directory, never in the repository. No server or background process may outlive you.',
  'Data honesty: never invent a real-world measurement. Use TO MEASURE in code and English docs, À COMPLÉTER in French docs. Figures that are the actual output of a run you made are fine.',
  'Finish only when every Done-when box is true, or you have written down exactly why one cannot be.',
]

function buildPrompt(id) {
  const b = B[id]
  return [
    'You are the builder of OptiFrame brief ' + id + ' (' + b.name + '). Other builders of the same wave run right now in the same checkout on other directories.',
    'Project root (absolute): ' + ROOT,
    'Your brief: ' + ROOT + '/agents/' + b.file,
    'Read your brief completely first. Its Shared context and Rules for you are binding. So is its Strategy inputs section: read the strategy files it names (they are in the project root) and implement every Adopt item. The Done-when list is your checklist, including the boxes added by the strategy review.',
    '',
    'PARALLEL-RUN RULES (they add to the rules of the brief):',
    bullets(RULES),
    '',
    'Python virtual environment for you: ' + b.venv,
    'Notes for this brief: ' + b.extra,
    '',
    'REPORT: your final answer is a structured object. doneWhen has one entry per checkbox of the brief (including added ones) with the command or file that proves it. libraryFindings: what you verified in installed packages (exact names, versions, licences). strategyLog: one line per strategy read, adopted or left out, and why. Keep strings short and factual.',
  ].join('\n')
}

function verifyPrompt(id, report, round) {
  const b = B[id]
  return [
    'You are an independent verifier of OptiFrame brief ' + id + ' (' + b.name + '), round ' + (round + 1) + '. You did not build it and you do not trust its report. Your job is to find what is wrong, not to confirm.',
    'Project root: ' + ROOT + '. Brief: ' + ROOT + '/agents/' + b.file + ' (read it fully, including Shared context, Strategy inputs and Done when). Python venv of the builder: ' + b.venv + '.',
    'Builder report (claims to check, not facts):',
    JSON.stringify(report),
    '',
    'Do, in order:',
    '1. Scope: list what exists in the owned paths (ls with times, git status --short). Report any file written outside "You own" (other than the OS temp directory) as a scope violation; ignore files of other briefs.',
    '2. Re-run the brief tests yourself (commands from the report; Python from the builder venv). Quote exact pass and fail counts.',
    '3. Walk Done-when line by line, including the boxes added under the strategy review: find the test or file that proves each, READ that test to confirm it asserts the claim (not tautological, thresholds as in the brief, truth generated independently from the code under test). A box is met only if you saw the evidence.',
    '4. Contract compliance: entry-point signature and path equal the table of the Shared context; only OptiError with a listed code escapes; contracts.ts untouched; conventions (mm, board frame, polygon orientation, eye and nasal sides).',
    '5. Honesty: grep the owned files for numbers that look like real-world measurements (accuracy, phone latency, metrics) not marked TO MEASURE or À COMPLÉTER or produced by a run.',
    '6. Adversarial probes for this brief (run them with throwaway scripts in the OS temp directory, or a throwaway test named _verify' + id + '.test.ts inside app/tests/ that you delete afterwards):',
    bullets(b.hints),
    '7. Strategy check: read the strategy files named in the brief. Every Adopt item must be present. Note high-value missed ideas that the scope allows (strategyMisses; a blocker only if listed under Adopt).',
    '',
    'You may not modify owned files, install packages, or change git state. A blocker is anything that makes a Done-when box false, breaks a contract, violates scope or honesty, or crashes on a probe. Style issues are minor. pass is true only with zero blockers. Each blocker needs file, problem and a concrete howToFix.',
  ].join('\n')
}

function fixPrompt(id, blockers) {
  const b = B[id]
  return [
    'You are the fixer of OptiFrame brief ' + id + ' (' + b.name + '). An independent verifier found blockers.',
    'Project root: ' + ROOT + '. Brief: ' + ROOT + '/agents/' + b.file + ' (read "You own", Shared context and Rules). Python venv: ' + b.venv + '.',
    'Parallel-run rules:',
    bullets(RULES),
    'Fix exactly these blockers, only in files owned by this brief, then re-run the brief tests and typecheck your files:',
    JSON.stringify(blockers),
    'Return what you fixed, what remains, and the test result after the fix.',
  ].join('\n')
}

async function verifyLoop(id, report) {
  if (!report) return { id, build: null, verify: null, rounds: 0 }
  let last = null
  for (let round = 0; round < 3; round++) {
    const v = await agent(verifyPrompt(id, report, round), { label: 'verify:' + id + '#' + (round + 1), phase: 'Verify', schema: VERIFY_SCHEMA, effort: 'high' })
    if (!v) break
    last = v
    if (v.pass || v.blockers.length === 0) return { id, build: report, verify: v, rounds: round + 1 }
    if (round === 2) break
    log('brief ' + id + ': ' + v.blockers.length + ' blocker(s), fixing (round ' + (round + 1) + ')')
    await agent(fixPrompt(id, v.blockers), { label: 'fix:' + id + '#' + (round + 1), phase: 'Verify', schema: FIX_SCHEMA, effort: 'high' })
  }
  return { id, build: report, verify: last, rounds: 3 }
}

const waveChecks = {
  0: 'Serve a COPY of app/dist from a sub-path in a temp dir with python -m http.server and fetch index.html and each asset URL it references (all must be 200 and relative). Stop the server afterwards.',
  1: 'CHAIN with the real modules. Put a throwaway test at app/tests/_integration_tmp.test.ts (delete it afterwards). Load 3 fixtures from rig/out/fixtures (PNG decoded with pngjs, truth from the neighbouring JSON; if no fixtures exist, say so and render a scene in the test). For each: Photo -> rectify -> segmentClassic -> measureLens -> compare A and B with the truth (report the actual errors in mm) -> fuseShots on 3 copies -> generateFrame(left,right,DEFAULT_FRAME) -> meshToStl -> check the STL length formula. Report each stage in chain[] with numbers. Also confirm polygon orientation consistency: the shoelace sign of measureLens output, of fuseShots output, and that generateFrame accepts both orientations. Attribute failures to the owning brief.',
  2: 'CHAIN again through pipeline.measureOne if it can run under Node (otherwise through the worker handler), then to the STL, then run tools/validate_stl.py on the produced STL from tools/.venv (write the STL to the OS temp dir). Confirm dist contains index.html, eval.html, collect.html, sw.js, manifest.webmanifest, lightbox.html, board_spec.json, bias.json and vendor/opencv, vendor/manifold, vendor/ort, and that index.html links to collect.html. Check the collect page ZIP export of a test run opens with Python zipfile and that its results.csv and own_lenses.csv headers equal those of the eval page and data/own_lenses.template.csv. Confirm ?demo=1 text is in the built JS. Confirm eval page imports measureOne from pipeline.ts or says why not.',
  3: 'Link check over every .md file of the project tree (skip node_modules): list broken relative links. Check that README.md exists at the project root, that docs/ARCHITECTURE.md, TEST_PLAN.md, RUBRIC_CHECKLIST.md, RISKS.md, DISPOSITIF_CAPTURE.md, PAS_A_PAS.md, DONNEES_ET_IA.md, LICENCES_ET_OUTILS_IA.md and CLAUDE.md exist, and that the earlier waves still pass (full npm run typecheck, test, build; all pytest suites).',
}

function integratePrompt() {
  return [
    'You are the integration checker after wave ' + wave + ' (briefs ' + ids.join(', ') + ') of OptiFrame. Every builder of this wave has finished: nothing else is running now, so you may run whole-project commands.',
    'Project root: ' + ROOT,
    'Run and report in this order, skipping what does not exist yet and saying so:',
    'a) cd app, then npm run typecheck, npm run test, npm run build (counts, failing test names, first error lines).',
    'b) The Python suites that exist, each from its own venv without creating new ones: rig/.venv, training/data/.venv, training/model/.venv, tools/.venv (if a venv is missing say so).',
    'c) JSON validity of app/public/board_spec.json and app/public/bias.json; expected built files in app/dist.',
    'd) Cross-module check for this wave: ' + waveChecks[wave],
    'Attribute every failure to the owning brief using this table (owner is the brief number):',
    OWNERSHIP,
    'Do not fix anything yourself. Delete any throwaway test you created. Return failures[] (owner, file, message, suggestedFix), the chain stages and pass.',
  ].join('\n')
}

function integFixPrompt(owner, failures) {
  const b = B[owner]
  return [
    'You are the integration fixer for OptiFrame brief ' + owner + ' (' + b.name + ') after wave ' + wave + '. The whole-project check found failures attributed to this brief.',
    'Project root: ' + ROOT + '. Brief: ' + ROOT + '/agents/' + b.file + ' (read "You own", Shared context and Rules). Python venv: ' + b.venv + '.',
    'You may edit only files owned by this brief (nothing else is running now). Same prohibitions on git state and npm install.',
    'Failures:',
    JSON.stringify(failures),
    'Fix them at the root cause (do not weaken a test to make it pass unless the test itself is wrong, and then say why), re-run the brief tests, and report.',
  ].join('\n')
}

// ---------------------------------------------------------------- BUILD + VERIFY
log('wave ' + wave + ': briefs ' + ids.join(', '))
phase('Build')
const results = await pipeline(
  ids,
  (id) => agent(buildPrompt(id), { label: 'build:' + id + ' ' + B[id].name, phase: 'Build', schema: BUILD_SCHEMA, effort: B[id].effort }),
  (report, id) => verifyLoop(id, report),
)

// ---------------------------------------------------------------- INTEGRATE
phase('Integrate')
let integ = await agent(integratePrompt(), { label: 'integrate#1', phase: 'Integrate', schema: INTEG_SCHEMA, effort: 'high' })
const unattributed = []
for (let r = 0; r < 2 && integ && !integ.pass && integ.failures.length > 0; r++) {
  const byOwner = {}
  for (const f of integ.failures) {
    const o = String(f.owner).padStart(2, '0')
    if (B[o]) { (byOwner[o] = byOwner[o] || []).push(f) } else { unattributed.push(f) }
  }
  const owners = Object.keys(byOwner)
  if (owners.length === 0) break
  log('integration failures for briefs ' + owners.join(', ') + ': fixing')
  await parallel(owners.map((o) => () => agent(integFixPrompt(o, byOwner[o]), { label: 'integfix:' + o, phase: 'Integrate', schema: FIX_SCHEMA, effort: 'high' })))
  integ = await agent(integratePrompt(), { label: 'integrate#' + (r + 2), phase: 'Integrate', schema: INTEG_SCHEMA, effort: 'high' })
}

// ---------------------------------------------------------------- AUDIT (wave 3)
let audit = null
if (wave === 3) {
  phase('Audit')
  const AUDIT_SCHEMA = {
    type: 'object',
    properties: {
      rows: { type: 'array', items: { type: 'object', properties: { requirement: { type: 'string' }, evidence: { type: 'string' }, status: { type: 'string', enum: ['implemented', 'partial', 'missing', 'needs-hardware'] }, note: { type: 'string' } }, required: ['requirement', 'evidence', 'status', 'note'] } },
      issues: { type: 'array', items: { type: 'object', properties: { modules: { type: 'string' }, issue: { type: 'string' }, severity: { type: 'string', enum: ['high', 'medium', 'low'] }, fix: { type: 'string' } }, required: ['modules', 'issue', 'severity', 'fix'] } },
      summary: { type: 'string' },
    },
    required: ['summary'],
  }
  const common = 'Project root: ' + ROOT + '. Nothing else is running. Read-only analysis unless stated. Do not install packages or change git state.'
  audit = await parallel([
    () => agent([
      'RUBRIC COVERAGE AUDIT of OptiFrame. ' + common,
      'Read CHALLENGE.md sections 4, 5 and 6 and docs/RUBRIC_CHECKLIST.md. For each rubric line, each imposed-format requirement and each deliverable, find the concrete evidence in the tree (file, test, screen) and rate it implemented, partial, missing or needs-hardware (needs a phone, printer, calliper or real lenses). Be strict: an item is implemented only if code or a document exists and a test or run backs it. Return rows[] and a summary of the top gaps ranked by points at stake.',
    ].join('\n'), { label: 'audit:rubric', phase: 'Audit', schema: AUDIT_SCHEMA, effort: 'high' }),
    () => agent([
      'CROSS-MODULE CONTRACT AUDIT of OptiFrame. ' + common,
      'Read app/src/contracts.ts and every module: capture, vision (rectify, segmentClassic, segmentModel), measure, quality, frame, export, pipeline, worker, ui, eval, collect (file names and CSV columns must match what training/data and tools/ read). Check consistency across modules: polygon orientation sign produced by measure/quality and expected by frame; nasal side and eye mirroring from measureLens through layout to the SVG export (right eye nasal +x, left eye nasal -x, right lens drawn on the -x side of the frame front); units; board frame origin; PX_PER_MM; the bias and board_spec loading paths and the worker message shapes; the error-code flow from every module to messageFor; sub-path hosting of all asset URLs (opencv, manifold, ort, models, board_spec, bias, sw). Return issues[] with severity and a concrete fix naming the owner brief.',
    ].join('\n'), { label: 'audit:contracts', phase: 'Audit', schema: AUDIT_SCHEMA, effort: 'high' }),
    () => agent([
      'END-TO-END REGRESSION TEST for OptiFrame. ' + common,
      'You may create exactly one file: app/tests/e2e/pipeline.e2e.test.ts (plus a small helper in app/tests/e2e/ if needed). Write a Vitest test that, for at least 3 fixtures of rig/out/fixtures (PNG decoded with pngjs, truth in the neighbouring JSON), runs Photo -> rectify -> segmentClassic -> measureLens -> fuseShots (3 copies) -> generateFrame (left and right from two different fixtures) -> meshToStl, asserts the measured A and B against the truth with the tolerance you find the pipeline actually achieves (state it as a constant with a comment, never looser than 1.0 mm), asserts the STL length formula and that bridge nasal distance equals 18 mm within 0.05, and when tools/.venv exists runs tools/validate_stl.py on the produced STL through child_process (skip with a clear message if Python is absent). Run it with npx vitest run tests/e2e from app/. If it fails because a module is wrong, do NOT patch the module: report the failure precisely in issues[] with the owner brief, and leave the test failing only if the failure is a real defect (mark it with test.fails? no: keep it a normal test and report). Return the actual error figures in summary.',
    ].join('\n'), { label: 'audit:e2e-test', phase: 'Audit', schema: AUDIT_SCHEMA, effort: 'high' }),
  ])
}

// ---------------------------------------------------------------- RESULT
function compact(r) {
  if (!r) return null
  const b = r.build
  const v = r.verify
  return {
    id: r.id,
    buildStatus: b ? b.status : 'build agent returned nothing',
    unmetDoneWhen: b ? b.doneWhen.filter((d) => !d.met).map((d) => d.item) : [],
    verifierPass: v ? v.pass : null,
    verifyRounds: r.rounds,
    blockers: v ? v.blockers : [],
    minor: v ? (v.minor || []) : [],
    scopeViolations: v ? (v.scopeViolations || []) : [],
    inventedFigures: v ? (v.inventedFigures || []) : [],
    strategyMisses: v ? (v.strategyMisses || []) : [],
    testsRerun: v ? v.testsRerun : '',
    filesWritten: b ? b.filesWritten : [],
    toMeasure: b ? (b.toMeasure || []) : [],
    contractProblems: b ? (b.contractProblems || []) : [],
    outOfScopeChangesNeeded: b ? (b.outOfScopeChangesNeeded || []) : [],
    interfaceNotes: b ? (b.interfaceNotes || []) : [],
    libraryFindings: b ? (b.libraryFindings || []) : [],
    strategyLog: b ? b.strategyLog : [],
  }
}
return {
  wave,
  briefs: results.map(compact),
  integration: integ,
  unattributedFailures: unattributed,
  audit,
}
