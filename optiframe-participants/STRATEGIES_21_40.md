# OptiFrame strategies 21–40

All 20 entries are **proposals, not implementations**. The audited results are summarized in [RESULTS_OVERVIEW.md](../RESULTS_OVERVIEW.md): the existing 15-case pipeline evaluation and STL checks use synthetic contours/images; physical board, phone, lens, print, fit, and slicer validation remain NOT RUN. Existing strategies 1–20 were checked for mechanism overlap; each comparison below names the nearest one and the specific additional experiment proposed.

| # | Proposal · priority | Dependencies | Nearest existing strategy and mechanism difference | Proposed first experiment |
|---|---|---|---|---|
| 21 | [Contour tessellation and STL approximation budget](strat21.md) · P1 | 2 contour; 9 mesh | 2 budgets camera/metrology error; this isolates polygon simplification and STL geometric approximation. | Hold out four asymmetric outlines; test 12 shapes × 3 densities × 5 tolerances. |
| 22 | [Display refresh and rolling-shutter banding check](strat22.md) · P1 | 1 lightbox; 10 camera | 7 fuses repeated shots and 10 supports camera capture; this detects periodic banding within individual screen-lit frames. | Capture two phones, multiple brightness settings, plus synthetic band controls. |
| 23 | [Lens placement sensitivity map](strat23.md) · P2 | 2 pipeline | 11 builds alignment stops; this quantifies error as a function of placement perturbation. | Sweep translation/rotation on 15 generated shapes with explicit holdout cases. |
| 24 | [Exposure and saturation quality diagnostics](strat24.md) · P2 | 1 rig; 3 segmenter | 1 sets lighting and 7 fuses shots; this scores clipping/glare from one image before segmentation. | 60 controlled exposure/glare images with error-labeled cases. |
| 25 | [Transparent-board flatness and local warp map](strat25.md) · P1 | 1 board; 2 rectification | 2 fits one homography; this tests repeatable sheet bow/warp on the screen support. | Compare rigid support to screen support, repeat and move board to estimate local warp. |
| 26 | [Geometric failure taxonomy and fault injection](strat26.md) · P2 | 2 CLI and generator | 2 covers nominal cases; this enumerates malformed/numerically invalid input behavior. | Run 100 seeded invalid inputs through CLI and library entrypoints. |
| 27 | [Metamorphic invariants for lens/frame geometry](strat27.md) · P2 | 9 frame; 2 contour | 9 validates example STLs; this tests transformation invariants over generated valid inputs. | Run 30 contours through translation, rotation, reflection, and scale transforms. |
| 28 | [Mesh feature accessibility and inspection report](strat28.md) · P2 | 9 STL | 9 checks topology; this verifies designed groove, seat, wall, bore, and bridge dimensions. | Inspect 12 synthetic meshes and deliberately remove features. |
| 29 | [Lens-seat clearance tolerance sweep](strat29.md) · P1 | 9 frame | 9 proposes nominal clearance; this sweeps contour error and clearance interactions without claiming print fit. | Sweep six shapes over 0.05–0.50 mm with held fixed perturbations. |
| 30 | [Result package reproducibility bundle](strat30.md) · P2 | 2 CLI; 9 STL | Reports record commands; this binds inputs/configuration/environment to reproducible output hashes/metrics. | Recreate manifests for the 15 synthetic cases without copying source images. |
| 31 | [Contour topology and hole policy](strat31.md) · P2 | 3 segmentation; 9 offsets | 14 fits shape priors; this defines accepted/rejected topology and hole semantics. | Exercise 40 generated contours across four topology classes. |
| 32 | [Mobile interaction performance budget](strat32.md) · P2 | 10 browser app | 19 selects server/browser routing; this profiles each user-visible stage on phones. | Two phones, cold/warm timing, 10/5 runs with synthetic inputs. |
| 33 | [Fiducial-board pose uncertainty cross-check](strat33.md) · P2 | 1 ChArUco; 2 homography | 2 maps the board plane; this compares independent pose/homography estimates and is blind to raised lens-edge parallax. | 15 synthetic board-tilt/intrinsics cases plus 10 board-only controls. |
| 34 | [Nasal bridge feasibility interval for asymmetric pairs](strat34.md) · P2 | 9 generator | 9 constructs the bridge; this computes a feasible span interval before mesh generation. | Test 12 synthetic asymmetric contour pairs against exact polygon intersections. |
| 35 | [Morphological gap-closure sensitivity budget](strat35.md) · P2 | 3 detector; 2 rectification | 3 closes the rim ring; this measures dimension instability over closing-kernel choices. | Test 12 shapes with controlled gaps and hold out four outlines. |
| 36 | [Metrology golden-fixture separation](strat36.md) · P1 | 2 evaluator | 18 proposes a physical repeatability study; this separately seals new synthetic shape families and any physical control set. | Generate 20 new sealed shapes; keep existing 15 as regression only. |
| 37 | [Rectified-image sampling and pixel-phase floor](strat37.md) · P2 | 2 rectification | 2 uses 20 px/mm and subpixel edges; this isolates raster sampling/phase error and selects a stable minimum. | Sweep five resolutions and four pixel phases with four held-out shapes. |
| 38 | [Lens-edge bevel and silhouette convention audit](strat38.md) · P2 | 2; physical samples | 2 refines the image edge; this labels which physical bevel/silhouette edge corresponds to the chosen dimension convention before bias fitting. | Eight physical lenses, three edge-profile categories, leave-one-lens-out rule check. |
| 39 | [STL slicing orientation and support-volume preview](strat39.md) · P3 | 9 frame | 17 adds temples/hinges; this optimizes orientation/support for the existing frame front only. | Compare 24 orientations on 10 synthetic meshes, then five slicer comparisons. |
| 40 | [Camera-mode change sentinel](strat40.md) · P2 | 10 camera; 2 board | 10 tests a device matrix; this detects mid-session resolution/lens/FOV discontinuities in the same session. | Two phones, 20 stable and 10 deliberately changed capture sequences. |

## First picks

1. **21 — Tessellation budget:** strategy 9 already emits a valid mesh from synthetic contours; this measures geometry fidelity lost between detector contour and STL.
2. **25 — Board flatness:** the proposed rig places a transparent board on a screen, yet physical rig validation is absent; local sheet warp can invalidate planar mapping.
3. **36 — New sealed fixtures:** the current 15 cases were used during development; new shape families and separate physical controls would prevent those same cases from being mislabeled as independent evidence.

## Evidence note

No strategy 21–40 has been run. The OpenCV ChArUco pose method mentioned in strategy 33 is documented in the [official OpenCV 5.0 tutorial](https://docs.opencv.org/5.0/tutorials/objdetect/charuco_detection/charuco_detection.html); this does not validate the physical board or camera setup. See [integrated results overview](../RESULTS_OVERVIEW.md) for measured versus untested results. Do not represent synthetic metrics as physical accuracy.
