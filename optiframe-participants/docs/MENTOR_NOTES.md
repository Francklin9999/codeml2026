# Mentor and organiser notes (Discord, OptiFrame channel)

> **Source:** screenshots of the event Discord pasted by the team on 2026-10-03, paraphrased. Only what an organiser or the SN-SF mentor said counts as an answer; other teams' messages are context.
> **Related:** [`../CHALLENGE.md`](../CHALLENGE.md) §10 lists the questions still open; [`COLLECTE_DONNEES.md`](COLLECTE_DONNEES.md) turns these notes into a data-collection list.

## Answers and hints received

| # | From | What was said | What we do with it |
|---|---|---|---|
| 1 | SN-SF technical assistant | For perspective, no need to find the camera. A flat object of known size next to the lenses (credit card 85.60 x 53.98 mm, or a printed ArUco marker) gives perspective correction and scale in mm through `cv2.findHomography`. | Matches the design: printed sheet with an ArUco ring, homography in `app/src/vision/rectify.ts`. |
| 2 | SN-SF technical assistant | Real target: ISO 12870 allows ±0.5 mm on lens size and on the distance between lenses. The lens/groove fit is even more sensitive, but a printed plastic frame is forgiving. "Aim for about 0.5 mm or better on width, height and bridge." | Our internal target (MAE ≤ 0.5 mm) is the same. **The bridge counts too:** the app lets the user set the bridge (default 18 mm) and the frame generator holds it to ±0.01 mm between nasal edges; measuring a bridge from a photo of complete glasses is parked (strat17). |
| 3 | SN-SF technical assistant | Be careful with point clouds, AR and phone depth sensors: not designed for this level of detail, and transparent surfaces are a weak spot. If the 2D method reaches 0.5 mm, spend the energy on the two lenses, the bridge and the 3D frame. | Confirms parking of the AR overlay (strat16) and the two-height capture (strat13). |
| 4 | SN-SF technical assistant | Validate by measuring a real lens with a ruler or calliper and comparing. | `tools/accuracy_report.py`, `app/eval.html`, the collection page. |
| 5 | Organiser | About ten pairs of glasses, of various sizes and colours, are at the SN-SF stand to test segmentation models during development. They must stay at the stand. | Complete glasses (not loose lenses) are available as test objects: shoot them at the stand in "Libre" mode. See also CHALLENGE.md §10 question 1. |
| 6 | Organiser | Teams took calipers from the measuring tables; SN-SF would like a few to stay at the tables for everyone. | Plan one long calliper session; do not walk away with a shared calliper. |

## Context only (other teams' questions, no official answer seen)

- A team showed a contour drawn on a transparent lens lying on a speckled off-white surface, with no backlight, with dust spots and specular highlights. This is the hard case for the classical segmenter and the reason the collection plan includes non-backlit shots.
- A team asked whether rotated lenses must be handled or users told to keep them straight. Our design: a guide line on the sheet, `rotationWarningDeg` and the `LENS_ROTATED` message. No official answer.
- A team found the lenses hard to pop into the sample frames at the SN-SF booth ("by design") and asked whether to ease the fit. No official answer; our default clearance is 0.2 mm with 0.5 mm lips, to be tuned on a real print.

## Channel rules

Do not post full solutions or complete code; share progress and ideas. Questions should say what was tried and include a screenshot of the result, the mask or the error.
