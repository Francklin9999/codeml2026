# OptiFrame · Strategy 16: Live AR overlay to validate the measured contour on the real lens

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (robustness evidence + bonus "cohérence contour/monture") |
| **Effort** | 3–4 h |
| **Depends on** | strategy 2 (homography, contour in board coordinates), strategy 10 (camera in the app) |
| **Rubric lines** | Robustness (10), Contour quality (5), Mobile app (15: clear UI), bonus coherence checks, Presentation (10) |
| **Differs from 1–10** | Strategy 7 compares numbers across shots; strategy 9 overlays contour and rim in a 2D view. This **projects the measured contour (and the generated rim) back onto the live camera feed**, registered by the board markers, so anyone can see instantly whether the outline hugs the physical lens |
| **Work folder** | `optiframe-participants/work/strat16/` |

---

## 1. Context you need

- The contour is stored in board coordinates (mm). Each live video frame gives a new board homography (ArUco / ChArUco detection), so the contour can be drawn on the frame at the right place even if the phone moves.
- Bonus in the brief: *"l'app superpose le contour mesuré et le cercle de la monture générée, et affiche l'écart en mm."* Contour quality is judged by printing the SVG and laying the lens on it; the AR overlay is the same check, live and without printing.

## 2. The idea

After measurement, switch to **"Vérifier"** mode: the camera feed shows the board with the measured contour (green) and the frame's seat outline (blue) drawn over the lens in real time. A per-sector error indicator highlights where the drawn contour and the live edge disagree (live edge detection along normals, as in strategy 2). The user can see and the app can quantify whether the measurement is right before generating the STL.

## 3. Why it could score

It is a visible proof of accuracy during the demo (very persuasive), an automatic second check (catches a bad measurement immediately), and it delivers the coherence bonus.

## 4. Implementation plan

### 4.1 Files

```
work/strat16/
  ar_overlay.js        # per-frame marker detection (downscaled), homography, draw contour on a canvas over <video>
  live_check.js        # edge sampling along contour normals in the live frame → per-sector error
  ui_verify.md         # UI states and messages
```

### 4.2 Performance

- Detect markers on a downscaled frame (e.g. 640 px wide) every frame or every other frame; smooth the homography over time (exponential filter) to avoid jitter.
- Draw with Canvas 2D: transform contour points with the homography (and the scale between downscaled and display resolution).
- Target ≥ 15 fps on a mid-range phone; if slower, update the overlay at 5 fps (still useful).

### 4.3 Live error measure

For 72 angular sectors, sample the live frame along the contour normal (±2 mm), find the edge (strongest gradient), and compute the offset in mm; show sectors with |offset| > 0.5 mm in red, display the median and max offset.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Registration accuracy | overlay of a printed known shape stays within 0.3 mm of its edge as the phone moves (measured in frames) |
| T2 | Error detection | deliberately wrong contour (scaled 2%) flagged in red across most sectors |
| T3 | Frame rate | ≥ 15 fps on one mid-range Android, ≥ 10 fps on an iPhone |
| T4 | Usability | a stranger understands "green = good, red = recheck" without explanation |

## 6. Risks

Performance of OpenCV.js marker detection per frame on low-end phones; fall back to a still-frame overlay (take a verification photo instead of live video).

## 7. Combines with

Strategy 2 (geometry), 7 (another consistency check), 9 (rim overlay), 10 (app), 18 (validation statistics).

## 8. Results log

| Date | Who | Device | fps | Overlay error | Notes |
|---|---|---|---|---|---|
| | | | | | |
