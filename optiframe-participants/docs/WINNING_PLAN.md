# OptiFrame: how we win

> **Purpose:** the reasoning behind every priority in [`PLAN_24H.md`](PLAN_24H.md). If a decision comes up at 3 a.m., the answer should follow from this page.
> **Read first:** [`../CHALLENGE.md`](../CHALLENGE.md).
> **Tags:** **[brief]** = from `consignes.pdf`. **[estimate]** = our judgement, not a measurement. **[to validate]** = must be confirmed by a test in the first hours.

---

## 1. Why this challenge

We picked OptiFrame because it is the challenge in this repository that the most teams will avoid **[estimate]**:

| Barrier | Why it deters teams |
|---|---|
| **No dataset, no starter notebook** | The brief provides nothing but two lenses on demo day. Machine-learning teams look for a CSV and a leaderboard. |
| **A physical rig to invent** | Calliper, lenses, printer, backlight: it cannot be done from a laptop alone. |
| **A mobile web app, on the jury's own phone** | JavaScript, camera permissions, iOS Safari. Outside the comfort zone of Python-first teams. |
| **Three disciplines at once** | Computer vision, model training and 3D geometry, each a single point of failure. |
| **30 points measured live** | No partial credit for a good notebook if the number on the phone is wrong. |

The cost of that choice is variance. Our own analysis ([`../../ANALYSE_CHALLENGES.md` §7.6](../../ANALYSE_CHALLENGES.md)) estimated 25 to 75 points with very high execution risk. **The whole plan below exists to turn that variance into reliability.** With few teams entered, the winner is likely to be the team whose app simply works on the jury's phone and gives a number within 1 mm.

One challenge would deter even more teams (L2C, plans versus shop drawings), but its data is confidential and absent from this repository, external AI services are forbidden on it, and its expected score was the lowest of all. Few competitors is only useful where a complete entry is achievable.

## 2. The win condition

> **On the jury's phone, with the rig rebuilt by the jury in under two minutes, both sample lenses are measured within 1 mm, a valid STL downloads, and nothing crashes.**

That single sentence is worth up to 65 points (accuracy 30, web app 15, frame 10, robustness 10). The remaining 35 (data and AI 15, presentation 10, contour 5, code 5) are earned by documentation, honesty and care, which are fully under our control.

Three consequences:

1. **The order of work is the order of risk, not the order of interest.** Deployment and camera first, measurement second, frame third, AI fourth.
2. **We optimise for a stranger with an unknown phone**, not for our own hands. Every hour spent on a stranger test is worth more than an hour of tuning.
3. **A reliable measurement without AI beats AI without a measurement** **[brief]**. The trained model must improve hard photos; it must never be able to break the easy ones.

## 3. Where teams lose points, and our answer

| Typical failure **[estimate]** | Points at stake | Our answer | Spec |
|---|---|---|---|
| The app does not open or cannot use the camera on the jury's iPhone | up to 65 | Online in HTTPS from the first hour; tested on a real iPhone and a real Android after every merge; file import as fallback | [`WEBAPP_SPEC.md`](../agents/03_capture.md), [`DEPLOYMENT.md`](../agents/01_app-scaffold-deploy.md) |
| Wrong scale: the printed reference was scaled by the printer | 10 to 30 | A ruler printed on the reference sheet, checked with the calliper; the app reads the true size | [`DISPOSITIF_CAPTURE.md`](DISPOSITIF_CAPTURE.md) |
| A and B measured along a different axis than the jury's calliper | 5 to 15 | Explicit boxing definition, a guide line on the rig, a warning when the lens looks rotated | [`MEASUREMENT_SPEC.md`](../agents/06_measure.md) |
| Perspective and parallax: the lens edge is a few mm above the reference plane | 3 to 8 | Camera held far enough, correction of the known bias, calibration on our own lenses | [`MEASUREMENT_SPEC.md`](../agents/06_measure.md) |
| The transparent lens is not segmented at all | up to 30 | A rig that makes the edge visible, so that segmentation is easy before any AI | [`DISPOSITIF_CAPTURE.md`](DISPOSITIF_CAPTURE.md) |
| One bad photo ruins one of only two measurements | 5 to 15 | Quality gates that refuse the photo with a clear sentence; several shots fused | [`MEASUREMENT_SPEC.md`](../agents/07_quality-fusion.md) |
| STL with holes or self-intersections | up to 10 | Frame built from 2D offsets extruded as solids, checked automatically and in a slicer | [`FRAME_SPEC.md`](../agents/08_frame-generator.md) |
| "We used a pre-trained model" with no data story and no metrics | up to 15 | A dataset built without manual labelling, a model we trained, metrics on lenses it never saw, a licence table | [`DONNEES_ET_IA.md`](DONNEES_ET_IA.md) |
| SVG not at true scale once printed | up to 5 | Dimensions in mm, a printed scale bar, a real print test | [`FRAME_SPEC.md`](../agents/08_frame-generator.md) |
| A demo that improvises and hides its limits | up to 10 | A rehearsed script, a backup video, limits stated before the jury finds them | [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) |

## 4. Score projection

**[estimate]** Not measurements. "Floor" is what we keep if the night goes badly but gates G0 to G2 of [`PLAN_24H.md`](PLAN_24H.md) are passed. "Target" assumes every gate is passed.

| Criterion | Max | Floor | Target | What moves it from floor to target |
|---|---|---|---|---|
| Précision des mesures | 30 | 20 | 30 | MAE from about 2 mm to under 1 mm: axis definition, parallax, bias calibration, multi-shot |
| Qualité du contour | 5 | 3 | 5 | A print test passed before the demo |
| Robustesse | 10 | 5 | 9 | Quality gates, consistent repeated shots, a sensible answer on mounted glasses |
| Données et IA | 15 | 6 | 13 | A trained model with held-out metrics instead of a pre-trained model alone |
| Web app mobile | 15 | 10 | 14 | Works on iOS as well as Android, messages for every failure |
| Monture générée | 10 | 6 | 9 | Different shapes, visible groove and tenons, slicer-clean |
| Qualité du code | 5 | 3 | 5 | README that lets someone else reproduce the results table |
| Présentation | 10 | 6 | 9 | Rehearsed, honest about limits |
| **Total** | **100** | **59** | **94** | |

## 5. Priorities

Work is ordered by points protected per hour. Nothing in a lower band starts while a higher band has an open gate.

| Band | Content | Points it protects | Tier |
|---|---|---|---|
| **P0** | App online in HTTPS, opens by QR, camera and file import on iPhone and Android | everything | 1 |
| **P1** | Rig and reference sheet; rectification with a verified scale; segmentation without AI on the rig; A, B, perimeter; control image; calliper ground truth on our lenses | 30 + 10 | 1 |
| **P1** | Frame front for two shapes, watertight STL, 3D preview, download; SVG 1:1 | 10 + 5 | 3 |
| **P2** | Quality gates and clear messages; orientation rule; parallax and bias correction; fusion of several shots | 30 + 10 + 15 | 1 |
| **P2** | Dataset without manual labels, trained small model, metrics, export to the browser, licence table | 15 | 2 |
| **P3** | Validation study with a predicted score; overlay of contour and rim with the gap in mm; difference of A and B between shots | bonuses, presentation | 4 |
| **P3** | Real print with lenses clipped in | bonus, presentation | 4 |
| **Parked** | Everything in §7 | none on the grid | |

## 6. Which of the 20 strategy files we use

The files [`../strat1.md`](../strat1.md) to [`../strat20.md`](../strat20.md) each describe one testable idea with its own experiments and results log. This table says which ones form the product. A strategy's results log is filled in its own file; the consolidated numbers go to [`TEST_PLAN.md`](TEST_PLAN.md).

| Decision | Strategy | Role in the product |
|---|---|---|
| **Core** | [1](../strat1.md) Backlit rig and reference sheet | The rig. Final design chosen at H+4 from measured edge contrast. |
| **Core** | [2](../strat2.md) Metrology pipeline | Homography, sub-pixel edge, parallax, error budget. |
| **Core** | [3](../strat3.md) Edge-based segmentation | The default segmenter on the rig. Also produces the labels for training. |
| **Core** | [8](../strat8.md) Boxing, orientation, bias | The definition of A and B, and the calibration against the calliper. |
| **Core** | [9](../strat9.md) Parametric frame generator | Tier 3. |
| **Core** | [10](../strat10.md) In-browser web app | The delivery vehicle. |
| **Tier 2** | [6](../strat6.md) Paired capture, synthetic lenses, small fine-tuned model | The "Données et IA" story and the fallback segmenter. |
| **Tier 2, helper** | [5](../strat5.md) Promptable foundation model | Offline teacher to check or produce labels; shipped in the browser only if it passes the latency test. |
| **Multiplier** | [7](../strat7.md) Multi-shot fusion | Accuracy, robustness, and bonus 2 with the same code. |
| **Multiplier** | [18](../strat18.md) Validation study | The numbers for the data file and the pitch; tells us where to spend the last hours. |
| **Multiplier** | [16](../strat16.md) Overlay check | Only its 2D part: contour over rim with the gap in mm (bonus 1). The live camera overlay is parked. |
| **Cheap extra** | [15](../strat15.md) Exports | Only the 1:1 PDF, if the SVG print test fails on the jury's printer. |
| **Plan B** | [19](../strat19.md) Server-side path | Activated only if in-browser processing fails gate G1 on one of the two phones. |
| **Plan B** | [11](../strat11.md) Mechanical fixture | A cardboard phone stand, only if hand-held shots fail the repeatability target. |
| **Parked** | [4](../strat4.md) Refraction pattern, [12](../strat12.md) Cross-polarisation, [13](../strat13.md) Two-height capture, [14](../strat14.md) Shape model, [17](../strat17.md) Complete eyewear, [20](../strat20.md) Lens power | Good ideas for the INOVA follow-up; mention them as perspectives in the pitch. |

## 7. What we deliberately do not build

- **AI first.** No training before gate G1. The brief says so itself.
- **A backend.** A server is a second thing that can be down during deliberations. Static hosting unless plan B is triggered.
- **Support for several reference objects.** One reference sheet, done well. A bank card is a weaker reference (four points, rounded corners, raised numbers) and is personal data in a photo.
- **A UI framework or a design system.** Five screens, large buttons, plain language.
- **Temples, hinges that move, size presets, material profiles.** The grid asks for a frame front with a bridge and tenons.
- **Lens power estimation, optical-lab file formats, live AR overlay.** Not on the grid.
- **Manual touch-up of a contour.** Forbidden on evaluation photos **[brief]**, so not worth building at all.

## 8. Kill criteria

| If, at this time | Then |
|---|---|
| H+3: marker detection does not run in the browser on both phones | Switch marker library, or trigger plan B (server path). Decide in 30 minutes. |
| H+4: the backlit rig gives no better edge contrast than a plain background **[to validate]** | Take the simpler rig. Simplicity wins the two-minute setup. |
| H+8: no end-to-end measurement on a real lens | D and F stop and help V. |
| H+14: MAE still above 1.5 mm | Stop adding features to measurement. Find the largest term of the error budget with printed test shapes, fix that one. |
| H+18: the trained model is not better than the non-AI path on hard photos, or is too slow on a phone | It is documented, not shipped. |
| H+18: no print started | Drop the "real print" bonus. |
| H+20: any feature not merged | It does not exist. |

## 9. What makes the entry memorable

The grid rewards a working product. The jury also has to choose between products that work. These cost little once the core exists:

1. **Metrology, not a guess:** an error budget, a validation study on our own lenses, and the predicted accuracy score with its uncertainty, shown before the jury measures.
2. **A dataset with zero manual labels:** the same scene shot once in easy light and several times in hard light, so the easy shot labels the hard ones.
3. **A rig a stranger rebuilds in two minutes**, with a printed ruler that proves the scale.
4. **Proof on screen:** the measured contour drawn over the generated rim, with the gap in mm, and the spread of A and B across shots.
5. **Limits stated first:** which lenses fail, how the app says so, what we would do next for SN-SF's field test.
6. **A printed front with the lenses clipped in**, if a printer is reachable.

## 10. Demo-day protocol

1. Before the jury arrives: app open on both team phones, rig kit on the table, QR code printed, backup video ready.
2. Hand the instruction sheet to the jury member and say nothing while they set up. That is the test.
3. If their phone fails to load the app: switch to the mobile hotspot, then to a team phone, then to the video. Never debug live.
4. State the measurement convention before they compare numbers: "boxing system, horizontal axis along the guide line".
5. Download the STL on their phone and open it; show the printed front if it exists.
6. Close on the limits and on what SN-SF could test in November.

Full script: [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md).
