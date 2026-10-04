# OptiFrame: 24-hour plan

> **Purpose:** who does what, in which order, and the gates that decide whether we move on or cut scope.
> **Read first:** [`../CHALLENGE.md`](../CHALLENGE.md) (the rules) and [`WINNING_PLAN.md`](WINNING_PLAN.md) (why this order).
> **Time notation:** `H+n` = n hours after the official start. Replace with clock times once the schedule is known.

---

## 1. Roles

The brief suggests five roles. With four people, the team lead also owns the presentation.

| Code | Role | Owns | Specs to read |
|---|---|---|---|
| **L** | Lead, integration, presentation | Repo, deployment, app shell and screens, README, demo | [`WEBAPP_SPEC.md`](../agents/10_ui-flow.md), [`DEPLOYMENT.md`](../agents/01_app-scaffold-deploy.md), [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) |
| **V** | Capture and vision | Rig, reference sheet, rectification, segmentation without AI, measurement | [`DISPOSITIF_CAPTURE.md`](DISPOSITIF_CAPTURE.md), [`MEASUREMENT_SPEC.md`](../agents/04_rectify.md) |
| **D** | Data and AI | Calliper ground truth, dataset, training, model export, metrics | [`DONNEES_ET_IA.md`](DONNEES_ET_IA.md), [`TEST_PLAN.md`](TEST_PLAN.md) |
| **F** | 3D and interface | Frame generator, STL, 3D preview, SVG export, overlay | [`FRAME_SPEC.md`](../agents/08_frame-generator.md) |

- **Three people:** F also takes the app screens; L takes D's ground-truth and validation work; the trained model is time-boxed harder (see gate G4).
- **Five people:** split L into integration and presentation, as in the brief.
- Everyone reads [`ARCHITECTURE.md`](ARCHITECTURE.md) §"Data contracts" before writing code: the modules only meet through those contracts.

## 2. Before the start (anything done here is free time)

| Done | Task | Who |
|---|---|---|
| ☐ | Gather the kit listed in [`../CHALLENGE.md` §8](../CHALLENGE.md#8-what-is-given-and-what-we-must-bring): calliper, 8 to 15 loose lenses, laptop or tablet, one iPhone, one Android | all |
| ☐ | Find a printer and check it prints at 100 % (measure the ruler on the reference sheet with the calliper) | V |
| ☐ | Find out whether a 3D printer is reachable during the event | F |
| ☐ | Create the Git repository and the hosting project; confirm an empty page opens in HTTPS on both phones | L |
| ☐ | Read the rules of the event on outside preparation, and respect them | L |

## 3. Hour by hour

Each cell is the deliverable of that block, not a list of activities.

| Block | L (integration) | V (vision) | D (data and AI) | F (frame) |
|---|---|---|---|---|
| **H+0 → H+1** | Ask a mentor the 10 questions of [`../CHALLENGE.md` §10](../CHALLENGE.md#10-ambiguities-to-clear-with-a-mentor-in-the-first-hour). "Hello camera" page **online in HTTPS**, QR code generated, opened on the iPhone and the Android. | Reference sheet printed; print scale checked with the calliper; rig v0 standing; 5 first photos. | Every lens given an ID (written on its bag, never on the lens). Calliper A and B, three readings each, in `data/own_lenses.csv`. | Frame spike: two 50 × 36 mm ellipses → STL → opens in a slicer with no error. |
| **G0 at H+1** | *Page reachable by QR on both phones, camera opens.* If not: nothing else matters until it does. | | | |
| **H+1 → H+4** | App shell: screens, state, camera and file import, worker, message framework. Auto-deploy on push. | Marker detection, homography, rectified image. **Scale check:** a printed 50.0 mm test shape measures 50.0 ± 0.2 mm in the app. Rig v1 decided (backlit or not) from measured contrast. | Paired-capture protocol rehearsed on rig v1; first 100 image pairs; synthetic-lens generator. | Parametric generator: clearance, rim, groove, bridge, tenons; watertight check; 3D preview component. |
| **H+4 → H+8** | End-to-end flow wired on both phones. Step-by-step screen with intermediate images. | Segmentation without AI, sub-pixel edge, A / B / perimeter, control image. First MAE on 5 lenses. | Auto-labels checked by eye on 50 pairs. Training run 1 on a free GPU. First ONNX export and its metrics on held-out lenses. | SVG 1:1 export, printed and checked with the calliper. Frame generated from real contours. |
| **G1 at H+8** | *One photo of a real lens gives A, B, perimeter and a control image, on both phones.* If not: D and F drop everything and help V. | | | |
| **H+8 → H+12** | Every failure condition mapped to a sentence; none shows a technical error. README skeleton filled. | Orientation rule, parallax and bias calibration, quality gates, multi-shot fusion. | Model running in the app as the fallback path; latency measured on both phones. | Two different shapes in one frame; contour-versus-rim overlay with the gap in mm; slicer validation. Start a test print if a printer is available. |
| **G2 at H+12** | ***Tier 1 frozen*** (the brief: "palier 1 figé à mi-journée"). MAE ≤ 1.0 mm on our own lenses, on both phones. `monture.stl` downloads for a real pair. From now on, measurement code changes only with a failing test as evidence. | | | |
| **H+12 → H+16** | Stranger test 1: someone outside the team sets up the rig from the instruction sheet and gets a result alone. Fix what blocked them. **Rest rota starts:** two awake, two asleep, 2-hour shifts. | Validation study: every lens × 2 phones × 3 repetitions. Predicted accuracy score. | Training run 2 with the full dataset; ablation table (real only, synthetic only, both). | Fit test on a printed rim; adjust the default clearance. UI polish for one-handed use. |
| **H+16 → H+20** | README complete. Demo script drafted. Licences and AI-tools table complete. | Fix the single largest error source shown by the study, nothing else. Limits written down. | "Données et IA" file complete with measured numbers. Decision at G4. | Frame defaults final. Printed front photographed for the README if it exists. |
| **G4 at H+18** | *Is the trained model better than the non-AI path on hard photos, and fast enough on a phone?* Yes: it ships as the fallback. No: it stays documented in the data file with its honest metrics, and the app keeps the non-AI path. Either way the 15 points are defended with real numbers. | | | |
| **G5 at H+20** | ***Feature freeze.*** Tag the commit as last known good. Only bug fixes after this, each tested on both phones. | | | |
| **H+20 → H+23** | Three timed rehearsals of the 5-minute demo. Backup video recorded. Stranger test 2 on a phone that has never opened the app. | Two complete rig kits packed, each with its instruction sheet. | Slide with the metrics and the dataset story. | Demo pair of lenses chosen; its STL and its print (if any) ready. |
| **H+23 → H+24** | Submission checklist of [`RUBRIC_CHECKLIST.md`](RUBRIC_CHECKLIST.md) ticked line by line. No deployment in the last 30 minutes. | | | |

## 4. Gates at a glance

| Gate | When | Pass condition | If it fails |
|---|---|---|---|
| G0 | H+1 | HTTPS page opens by QR on iPhone and Android, camera works | All hands on it |
| G1 | H+8 | End-to-end tier 1 on one real lens, both phones | D and F help V; AI and frame polish wait |
| G2 | H+12 | MAE ≤ 1.0 mm on own lenses; STL for a real pair; tier 1 frozen | Extend to H+14 at most, then freeze whatever is most accurate |
| G3 | H+16 | A stranger completes the flow alone in under 2 minutes of setup | Simplify the rig and the instructions, not the code |
| G4 | H+18 | Trained model beats the non-AI path on hard photos and runs within the time budget | Document it, do not ship it |
| G5 | H+20 | Feature freeze, last-known-good tag | No exception |

## 5. Working rules

Taken from the brief's annex, plus what a live phone demo needs.

1. **One step at a time, with a control image.** No step is "done" without an image that shows it worked.
2. **No number is believed without the calliper.** Every accuracy claim points to a row in the results tables of [`TEST_PLAN.md`](TEST_PLAN.md).
3. **Commit as soon as a step works.** Small commits, the main branch always deployable.
4. **Test on a real phone after every merge**, alternating iPhone and Android.
5. **Stuck for 20 minutes: call a mentor.** Say what was tried.
6. **Everyone can explain their part.** The jury may ask any member. Code written with an AI assistant is read and understood before it is merged.
7. **Declare AI tools as they are used**, in [`LICENCES_ET_OUTILS_IA.md`](LICENCES_ET_OUTILS_IA.md), not from memory at the end.
8. **Scope is cut at the gates, never in between.** Ideas that appear during the night go to the "parked" list in [`WINNING_PLAN.md`](WINNING_PLAN.md).

## 6. Demo-day kit

| Item | Quantity | Check |
|---|---|---|
| Rig kit (reference sheet, instruction sheet, backlight device and its charger) | 2 | Assembled by a stranger in under 2 minutes |
| Reference sheets, spare | 4 | Print scale verified on each |
| Printed QR code of the final URL | 2 | Scanned with a phone camera, opens the app |
| Demo pair of lenses, with their calliper values | 1 | Values in the README |
| Calliper | 1 | For questions |
| Phones for the live demo, charged, screen timeout disabled | 2 | iPhone and Android |
| Mobile hotspot | 1 | In case the venue network fails |
| Backup video on a phone and on a laptop, playable offline | 1 | Under 2 minutes |
| Printed frame front with lenses clipped in | if it exists | |
