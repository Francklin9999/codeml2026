# OptiFrame · Strategy 1: Backlit capture rig (screen light box + printed ChArUco frame)

| | |
|---|---|
| **Status** | NOT STARTED *(set to IN PROGRESS / DONE / ABANDONED with your name and the date)* |
| **Priority** | P1 (everything else depends on good photos) |
| **Effort** | 3–4 h (design + build + validation) |
| **Depends on** | nothing |
| **Rubric lines** | Measurement accuracy (30), Robustness (10), Presentation (10: rig shown and reassembled) |
| **Work folder** | `optiframe-participants/work/strat1/` |

---

## 1. Context you need

- **Challenge (SN-SF OptiFrame):** a mobile web app photographs a recycled eyeglass lens next to a reference object, rectifies the image, segments the lens, measures **A (width), B (height), perimeter** in mm, and generates a 3D-printable frame (STL) for two possibly different lenses.
- **Rubric (100):** measurement accuracy **30** (mean absolute error on A and B of the jury's 2 lenses: 30 pts if ≤ 1 mm, decreasing to 0 at 4 mm); contour SVG 1:1 **5**; robustness (several shots, angles, lighting, a jury pair, no crash) **10**; data & AI **15**; mobile web app **15**; generated frame **10**; code **5**; presentation **10**.
- **Evaluation protocol:** the jury opens the app **on their own phone** via QR code, **reassembles our capture rig in < 2 minutes**, photographs the 2 sample lenses, compares A and B with calliper values (boxing system), downloads the STL. No manual annotation of evaluation photos. WhatsApp photos are unusable (recompressed).
- No data or equipment is provided. The brief's ideas: a laptop's white screen as a light box, a window, a printed A4 sheet with ArUco markers, a bank card (85.60 × 53.98 mm), a coin.

## 2. The idea

A transparent lens is hard to see in reflected light but becomes a crisp dark-edged silhouette **in transmitted light**. Build a rig the jury can set up in under 2 minutes:

1. **Light source:** a laptop (or tablet) screen showing a full-screen white page (served by our app at `/lightbox`, max brightness), laid flat or tilted back.
2. **Reference frame:** a **ChArUco board printed on transparency film** (or thin tracing paper) laid directly on the screen, with an empty central window where the lens goes. Transparency lets light through around the markers and gives scale + perspective in the lens plane.
3. **Lens placement guide:** a printed outline of the window with a horizontal reference line and an arrow for the nasal side; place the lens **concave (back) side down** so the rim touches the board (see strategy 2 for why).
4. **Phone position:** hand-held at ~30–40 cm, or a cheap phone stand / stack of books; the app's live overlay says when the board is fully visible and roughly fronto-parallel.

Fallback rig without a laptop: printed ChArUco on white paper + phone flashlight from below through a window pane, or the window itself as the light source.

## 3. Why it could score

Contrast is the root of accuracy. A backlit silhouette makes classical segmentation sub-pixel precise, reduces dependence on AI for the 30 accuracy points, and is easy to reproduce by the jury.

## 4. Implementation plan

### 4.1 Materials

| Item | Spec |
|---|---|
| Board | ChArUco, dictionary `DICT_5X5_100` (or `DICT_4X4_50`), squares 12 mm, markers 9 mm, 9×7 squares with a central cut-out window ~70×55 mm (enough for lenses up to ~65 mm wide); print at **100% scale** (disable "fit to page") |
| Media | transparency film for laser printers (preferred) or 80 g paper (then backlight only through the window) |
| Light | laptop/tablet screen, white page at max brightness; app route `/lightbox` with optional pattern modes for strategy 4 |
| Guide | printed horizontal line + "NASAL →" arrow inside the window |
| Optional | 3D-printed or cardboard frame that holds the board flat and the phone at a fixed height |
| Calliper | for our own ground truth (± 0.02 mm digital calliper) |

### 4.2 Files

```
work/strat1/
  make_board.py        # generates the ChArUco PDF at exact scale (OpenCV aruco module)
  board_spec.json      # dictionary, square size, layout (shared with the app)
  rig_instructions.md  # 6 steps with photos, for the jury (target < 2 min)
  scale_check.py       # measures known printed shapes to validate the board print
```

```python
import cv2
d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_100)
board = cv2.aruco.CharucoBoard((9, 7), squareLength=0.012, markerLength=0.009, dictionary=d)
img = board.generateImage((int(9*12/25.4*600), int(7*12/25.4*600)), marginSize=0, borderBits=1)  # 600 dpi
# then blank the central squares (the lens window) and write a PDF at exact physical size (e.g. with reportlab)
```

### 4.3 Print verification

Measure the printed square size with the calliper over 6 squares (≥ 70 mm span); printers often scale by 0.5–2%. Either fix the print settings or store the **measured** square size in `board_spec.json` (the app reads it). Document this in the rig instructions: "measure the 6-square span; it must be 72.0 ± 0.2 mm".

### 4.4 Rig instructions for the jury (draft)

1. Open `https://<app>/lightbox` on the laptop, full screen, brightness max.
2. Lay the laptop flat (or tilt the screen back) and place the board on the screen.
3. Put the lens in the window, concave side down, horizontal line aligned, nasal side towards the arrow.
4. Open the app on the phone (QR code), choose "œil gauche/droit".
5. Hold the phone above the board until the overlay turns green, then shoot (or let auto-capture fire).
6. Repeat for the second lens.

## 5. How to test it

| # | Test | How | Pass if |
|---|---|---|---|
| T1 | Print scale | calliper over 6 squares | within ± 0.2 mm of spec (or spec updated) |
| T2 | Contrast | photo a lens on the rig; edge contrast (intensity drop across the rim, in grey levels) | ≥ 60 grey levels on 3 different lenses (clear, tinted, high minus) |
| T3 | Scale accuracy | measure printed test shapes (circle Ø 50.00 mm, rectangle 55 × 40 mm) placed in the window, 10 photos from different angles | MAE ≤ 0.15 mm |
| T4 | Reassembly time | a person who never saw the rig follows `rig_instructions.md` | < 2 min, 3 different people |
| T5 | Ambient light | room lights on / off, window light, phone flash on / off | T2 still passes; note which settings fail |
| T6 | Phone diversity | 2 Android + 1 iPhone if available | T3 passes on each |

## 6. Risks

- Laptop screen too dim in a bright room: carry a backup (tablet, phone torch + diffuser, window).
- Moiré between the screen's pixel grid and the camera: defocus slightly or put tracing paper between screen and board as a diffuser.
- The jury's phone may have a different camera: T6.

## 7. Combines with

Strategy 2 (metrology on top of this rig), 3 and 4 (segmentation exploits backlight), 7 (multi-shot), 10 (`/lightbox` page and live overlay).

## 8. Results log

| Date | Who | Board print scale | Contrast | Scale MAE | Reassembly time | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
