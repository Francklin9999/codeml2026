# OptiFrame: the challenge, decoded

> **Source of truth:** [`consignes.pdf`](consignes.pdf) (SN-SF, 5 pages, French only). Everything below is taken from it unless tagged otherwise.
> **Tags:** **[brief]** = stated in the PDF. **[assumption]** = our reading of an ambiguous sentence, to confirm with a mentor (see [§10](#10-ambiguities-to-clear-with-a-mentor-in-the-first-hour)). **[ours]** = our own target or advice.

---

## 1. The challenge in one paragraph

Partner: **Santé Numérique Sans Frontières (SN-SF)**. Recycled prescription lenses (donations, end-of-series, dismantled glasses) exist in places where opticians do not. Each recycled lens has its own shape, and a prescription can pair two lenses of **different shapes**, so a standard frame does not fit. An optician would trace the lens with an expensive tracer. The challenge is to replace the tracer with a smartphone: a **mobile web app** photographs a lens lying next to an object of known size, measures its outline **to about 1 mm**, and generates a **made-to-measure frame front as an STL file** that a consumer 3D printer can print for a few dollars of filament.

Nothing is provided except the brief: no light box, no jig, no photos, no labels. Teams invent the capture rig, build their own dataset and produce their own ground truth with a calliper.

## 2. The four tiers (paliers)

| Tier | Name | Status | What must exist |
|---|---|---|---|
| 1 | **Mesurer** | mandatory | In the app: take the photo, find the reference object, rectify the image to a top view, isolate the lens, display **width A, height B and perimeter in mm** with a **control image** |
| 2 | **Entraîner l'IA** | "fortement valorisé" | A good contour despite reflections, shadows, a tilted photo or a transparent lens, using a segmentation model **trained or fine-tuned** on data of our choice, running in the browser or on a server |
| 3 | **Concevoir** | mandatory | A **parametric frame front** from two contours (left and right, possibly different shapes) and the bridge width; **3D preview** in the app and **STL download** |
| 4 | **Valider** | bonus | Evidence that the frame matches the lenses: contour and rims overlaid, consistent measurements across photos, and if a printer is available, a printed front with the real lenses clipped in |

The brief states that a team completing **only tiers 1 and 3 can already get a good mark**, and that beginners are welcome.

The five processing steps named in the brief: **Redresser → Segmenter → Mesurer → Générer la monture → Mettre en ligne**. The first three are tier 1.

## 3. How the jury evaluates (and what each step implies)

The brief describes the protocol literally:

| # | What the jury does **[brief]** | What it implies for us **[ours]** |
|---|---|---|
| 1 | Opens the app **on their own phone** with the QR code | Unknown phone, unknown OS version, empty cache, possibly an in-app QR browser. The app must load and get camera access with zero help. |
| 2 | **Reassembles our capture rig** (must take under 2 minutes) | The rig is a kit with a one-page instruction sheet. No adjustment that needs judgement. |
| 3 | Photographs **the two sample lenses** brought by SN-SF | A non-expert takes the photo. The app must guide and refuse bad photos with a clear sentence. The samples **must not be modified or marked**. No manual annotation of evaluation photos: processing is automatic. |
| 4 | Compares our **A and B** with the calliper values (boxing system) | Our definition of A and B must match what a calliper measures, in the same lens orientation. |
| 5 | Downloads the **STL** | The download must work on iOS Safari and Android Chrome, and the file must open in a slicer. |

The demo itself: **5 minutes live on a phone, then 2 minutes of questions**.

## 4. Scoring grid

| Criterion | Points | How it is judged **[brief]** | What earns it **[ours]** |
|---|---|---|---|
| **Précision des mesures** | **30** | Mean absolute error on A and B of the two samples: 30 pts if ≤ 1 mm, then decreasing to 0 pt at 4 mm | Rig + metrology + calliper-checked definitions. Internal target: MAE ≤ 0.5 mm on our own lenses, on a phone we never tuned on. |
| Qualité du contour | 5 | Contour exported as SVG 1:1: the lens laid on the printed outline must match it | A true-scale export with a printed scale bar, tested on a real printer. |
| Robustesse | 10 | Consistent results over several shots (angle, lighting) **and on a pair of glasses brought by the jury**, no crash | Quality gates, multi-shot consistency, every failure mapped to a sentence. Never a stack trace. |
| **Données et IA** | **15** | Ingenuity of the dataset (collection, synthetic, augmentation), model choice and training, performance metrics, sources and licences cited | A real trained model, a documented dataset built without manual labelling, honest metrics on our own lenses, a licence table. |
| **Web app mobile** | **15** | Opens with one QR scan, works on Android and iOS without installation, clear interface, useful error messages | Static HTTPS app online from the first hour, tested all day on a real iPhone and a real Android. |
| Monture générée | 10 | Valid STL (closed mesh), rims consistent with the lenses (including two different shapes), bridge and hinge tenons present, printable without excessive supports | Layered 2D offsets extruded into a watertight solid; checked in a slicer. |
| Qualité du code | 5 | Readable code, clear README, reproducible results | Small modules, one command to run locally, results tables that anyone can regenerate. |
| Présentation | 10 | Clear demo on a phone, justified choices, limits acknowledged honestly | A rehearsed 5-minute script, a backup video, a slide of known limits. |
| **Total** | **100** | | |

### 4.1 The accuracy score as a function

**[assumption]** "Dégressif" read as linear, and the mean taken over the four values A₁, B₁, A₂, B₂:

```
MAE = (|A1 − A1_ref| + |B1 − B1_ref| + |A2 − A2_ref| + |B2 − B2_ref|) / 4
points = 30                          if MAE ≤ 1 mm
       = 30 × (4 − MAE) / 3          if 1 mm < MAE < 4 mm
       = 0                           if MAE ≥ 4 mm
```

| MAE (mm) | ≤ 1.0 | 1.5 | 2.0 | 2.5 | 3.0 | 3.5 | ≥ 4.0 |
|---|---|---|---|---|---|---|---|
| Points | 30 | 25 | 20 | 15 | 10 | 5 | 0 |

Past the 1 mm plateau, **each extra millimetre of mean error costs 10 points**, more than the whole "Monture générée" criterion. Only two lenses are measured, so one bad photo decides a third of the grade.

### 4.2 Where the points are, by tier

| Tier | Criteria it feeds | Points |
|---|---|---|
| 1 (measure) + delivery | accuracy 30, contour 5, robustness 10, web app 15, code 5, presentation 10 | 75 |
| 3 (frame) | generated frame 10 | 10 |
| 2 (AI) | data and AI 15 | 15 |
| 4 (validate) | bonuses only: they **break ties**, they add no points | 0 |

## 5. Imposed format: non-negotiable requirements

All **[brief]**. Each line is a pass/fail item in [`docs/RUBRIC_CHECKLIST.md`](docs/RUBRIC_CHECKLIST.md).

- **Public HTTPS URL** and a **QR code** of that URL shown during the demo. Browsers block the camera without HTTPS.
- **No installation, no account, no API key.** The test starts with one QR scan.
- **Mobile first:** usable with one hand on recent **Chrome (Android)** and **Safari (iOS)**, readable on a screen of about 6 inches.
- **Camera built into the app**, with a **file import fallback** if the camera is refused.
- **In-browser processing recommended** (JavaScript / WebAssembly): no server to maintain, data stays on the phone, works with little or no connection. A Python server is allowed **if its URL stays up until the end of deliberations**.
- **Free hosting advised:** GitHub Pages, Netlify, Vercel, Cloudflare Pages, Hugging Face Spaces or Render. A temporary tunnel (Cloudflare Tunnel, ngrok) is tolerated during evaluation.
- **No paid service and no closed API** in the final version.
- **Performance:** result in **under 30 seconds per pair of lenses** on a mid-range phone.
- **Contour export:** a button that exports the contour as **SVG at 1:1 scale**, so the jury can print the outline and lay the lens on it.
- **Clear message, not a technical error**, when the reference object is missing, the photo is blurry or the lens is badly placed.
- One page where the user photographs a **left lens and a right lens**, sets the **bridge width (18 mm by default)** and gets the measurements, the 3D preview and the STL.

Data rules:

- Any pre-trained model and any public dataset is allowed **if cited with its licence**.
- **No personal data** in our datasets (faces, names, prescriptions).
- **No manual annotation** of photos taken during evaluation.
- **WhatsApp photos are unusable** for measurement (resized and recompressed): use the app's camera or the original files.
- Convention: the **nasal side** of the lens faces the centre of the frame; the app lets the user choose the **eye (left or right)** for each lens.
- Mandatory technologies: none.

## 6. Deliverables

| Deliverable | Expected content **[brief]** | Tier | Where it lives in this project |
|---|---|---|---|
| Web app online | Public HTTPS URL + QR code, testable on a smartphone without installation | 1 | `app/` deployed; URL and QR in [`README.md`](README.md) |
| Source code | Public Git repository (or shared with the jury) with **local launch instructions** | 1 | [`README.md`](README.md) |
| "Données et IA" file | In the README or a notebook: datasets and models used (sources, licences), training method, **performance measured on our own lenses** | 2 | [`docs/DONNEES_ET_IA.md`](docs/DONNEES_ET_IA.md) |
| Trained model | Weights loaded by the app, plus a download link if they exceed 100 MB | 2 | `app/` assets; link in the README |
| "Pas à pas" page | In the app or the README: **one photo with its intermediate images** (reference, rectification, contour) | 1 | [`docs/PAS_A_PAS.md`](docs/PAS_A_PAS.md) and the app's step-by-step screen |
| 3D file | `monture.stl` downloadable from the app, for the demonstration pair of lenses | 3 | generated by the app |
| README | App link, capture rig, technical choices, known limits, **AI tools cited** | 1 | [`README.md`](README.md) |
| Demonstration | 5 minutes on a phone, live, then 2 minutes of questions | 1 | [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) |

Submission checklist from the brief's annex: URL that opens on a brand-new phone, QR code ready, rig that can be reassembled in 2 minutes, `monture.stl` downloadable, README with sources and licences, rehearsed demo, **every member can explain their part**.

## 7. Bonuses (tie-breakers only)

The brief says bonuses separate tied teams and none is needed for a good mark. All three are about consistency:

1. **Contour vs frame:** the app overlays the measured contour and the generated rim, and displays the gap in mm.
2. **Across shots:** for the same lens, the app compares at least two photos and displays the difference in A and in B.
3. **Real print:** print the frame front and show in the demo that the lenses clip in.

## 8. What is given, and what we must bring

| Item | Given? | Notes |
|---|---|---|
| Two real sample lenses | Yes, by SN-SF, **for the final demo and evaluation only** | Measured by the jury with a calliper (A and B). Not to be modified or marked. |
| Capture rig | No | Free design, must be reassembled by the jury in under 2 minutes. Ideas listed in the brief: a laptop's white screen as a light box, a window, a printed A4 sheet with ArUco markers (any dictionary), a bank card (85.60 × 53.98 mm), a coin. |
| Datasets | No | Free. Hints: photos of participants' own glasses, public datasets of object or transparent-object segmentation, synthetic images (3D rendering, augmentation), pre-trained models such as Segment Anything. Each one cited with its licence in the README. |
| Ground truth | No | We produce it: measure **our own lenses with a calliper** using the boxing system (the rectangle that encloses the lens). |

**[ours]** Physical kit to gather before or at the very start, because nothing can be validated without it:

| Item | Why |
|---|---|
| Digital calliper | Only source of ground truth. The brief: "ne croire aucun chiffre sans mesure au pied à coulisse". |
| 8 to 15 loose lenses (old glasses, cheap reading glasses and sunglasses with the lenses popped out) | Training data, validation set, demo pair. Include clear, tinted, thick-edged and thin-edged ones. |
| A printer, plain paper, scissors or a cutter, tape | The reference sheet and the 1:1 contour test. |
| A laptop or tablet | Backlight for the rig. |
| One recent iPhone and one mid-range Android | The grid requires both. Test on both from the first hour. |
| Optional: transparency film, a phone stand, a 3D printer and filament | Rig variants and the "real print" bonus. |

## 9. Advice given in the brief itself

- Make tier 1 work **end to end on a single photo** before training anything: "une mesure fiable sans IA vaut mieux qu'une IA sans mesure".
- Put the app **online in the first hour** and test it on a real phone all day.
- **Check the scale immediately:** the reference object measured in the rectified image must have its real size in mm.
- A transparent lens is seen better **by its edge than by its surface**: look at gradients, not only brightness.
- Little data? Generate some: varied backgrounds, lighting and shapes, simulated reflections, augmentation.
- Keep the contour as a **polygon (list of points in mm)**: it serves both the measurement and the 3D generation.
- Leave a **clearance of 0.1 to 0.3 mm** between lens and rim; a real lens is slightly curved.
- Suggested day: start (roles, Git repo, page online, rig, a test 3D model with two 50 × 36 mm ellipses); measure (tier 1 **frozen at mid-day**); train and build (model, frame); deliver (README, rehearsed demo, backup video).
- Coding with AI: one step at a time; give the context at the start of each conversation; demand a control image; commit as soon as a step works; be able to explain the code to the jury. Stuck for more than 20 minutes: call a mentor.

Recommended technologies **[brief]**: JavaScript or TypeScript for the app; OpenCV.js or js-aruco2 for markers; Clipper for polygon offsetting; three.js for the preview and STL export; manifold-3d or JSCAD for 3D geometry. For AI: training on Google Colab or Kaggle with PyTorch or TensorFlow, then ONNX or TensorFlow.js export to run in the browser. Documentation listed: OpenCV.js, js-aruco2, Clipper, three.js, manifold-3d, ONNX Runtime Web, TensorFlow.js, Segment Anything (Meta), ISO 8624 (boxing system: A, B, bridge).

Team roles suggested in the annex:

| Role | Responsible for | Steps |
|---|---|---|
| Team lead / integration | Git repo, deployment, schedule | Online, demo |
| Capture and vision | Capture rig, reference object, rectification, measurements | Rectify, measure |
| Data and AI | Dataset, training, exporting the model to the app | Segment |
| 3D and interface | STL frame, 3D preview, mobile screens | Frame |
| Presentation | README, demo, slides, backup video | Demo |

## 10. Ambiguities to clear with a mentor in the first hour

Each answer changes a design decision. Until answered, we build for the stricter reading.

**Answers received so far** (Discord, paraphrased): the organisers keep about ten pairs of *mounted* glasses at the SN-SF stand for testing segmentation (relevant to question 1), and the SN-SF mentor gives ±0.5 mm (ISO 12870) as the real tolerance on lens size **and bridge**. No answer yet on the other questions.

| # | Question | Why it matters |
|---|---|---|
| 1 | The robustness line mentions "une paire de lunettes apportée par le jury". Is that a pair of **loose lenses**, or **complete glasses with the lenses mounted**? | If mounted, the app must at least not crash and say something sensible, and ideally measure the visible lens opening. |
| 2 | Is the accuracy score **linear** between 1 mm and 4 mm, and is the mean taken over the four values (A and B of both samples)? | Tells us how much a single bad measurement costs. |
| 3 | In which **orientation** does the jury hold each sample for the calliper? Will they tell us which side is nasal and where the horizontal is, given that the samples cannot be marked? | A and B depend on the axis. For a sharp-cornered 52 × 38 mm rectangle, a 3° rotation inflates B by about 2.7 mm; real lenses with rounded corners are less sensitive, an ellipse almost not at all. |
| 4 | What are the samples like: clear or tinted, plus or minus power, size range, bevelled edge? | Decides which lenses we buy for validation. |
| 5 | May the jury take **several photos per lens**, and do they follow our on-screen instructions? | Multi-shot fusion is our main protection against one bad photo. |
| 6 | Who prints the **SVG 1:1** during evaluation, on which printer and paper size (A4 or US Letter)? | Print scaling is the main risk for the 5 contour points. |
| 7 | Does the jury bring anything for the rig (a laptop, a table lamp), or only use what we hand over? | Decides whether the rig may rely on a laptop screen as backlight. |
| 8 | Is a **3D printer** available on site, and by when must a print start to be shown? | Decides whether to attempt the "real print" bonus. |
| 9 | Until when must the **URL stay live**? | Hosting choice, and whether a temporary tunnel is acceptable. |
| 10 | Are prizes awarded **per challenge**, and how many teams chose OptiFrame? | Tells us whether to play for a safe complete entry or for differentiation. |

## 11. After the hackathon

- **October 2026:** the OptiFrame prototype is to be unveiled at the **INOVA** event, during the day on AI with social impact organised by the school of optometry of the Université de Montréal.
- **November 2026:** the team is to be invited to SN-SF's offices for a test with AI specialists.

**[ours]** The jury is therefore looking for something they can show to optometrists a few weeks later: reliability and honesty about limits will count for more than a feature list.

## 12. Glossary

| Term (FR in the brief) | Meaning |
|---|---|
| **Verre** | Spectacle lens. Here an *edged* lens: already cut to the shape of a frame. |
| **Monture / face de monture** | Frame / frame front: the two rims and the bridge, without the temples. |
| **Cercle** | Rim: the part of the frame that surrounds one lens. |
| **Pont** | Bridge: the part joining the two rims over the nose. Its width (default 18 mm) is the distance between the two lenses. |
| **Tenon** | Endpiece: the block on the temporal side of the frame front that carries the hinge of the temple. |
| **Branche** | Temple (arm). |
| **Rainure / jeu / clipsage** | Groove / clearance / snap-fit: how the lens is held in the rim. |
| **Côté nasal / temporal** | Side of the lens towards the nose / towards the ear. |
| **Système « boxing »** | The rectangle that encloses the lens, with sides parallel and perpendicular to the lens's horizontal. **A** = width of the rectangle, **B** = its height. Standard: ISO 8624. |
| **Périmètre** | Length of the lens outline. |
| **Pied à coulisse** | Calliper. |
| **Traceuse** | Lens tracer: the optician's machine that records the shape of a lens or frame. |
| **Dispositif de capture** | Capture rig: everything physical needed to take the photo (reference object, background, light). |
| **Objet de référence** | Object of known size in the photo that gives the scale and the perspective. |
| **Redresser** | Rectify: warp the photo into a top view with a known scale in pixels per mm. |
| **Image de contrôle** | Control image: the photo with the detected reference and contour drawn on it, so a human can check the result. |
| **ArUco / ChArUco** | Printed square fiducial markers that software detects precisely; ChArUco combines them with a chessboard for more accurate corners. |
| **STL** | Triangle-mesh file format used by 3D-printing slicers. "Maillage fermé" = closed (watertight) mesh. |
