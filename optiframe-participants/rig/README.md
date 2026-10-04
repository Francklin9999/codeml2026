# rig: reference sheet and light-box

The printed sheet gives scale and perspective; a laptop or tablet screen showing `/lightbox.html` is the backlight.

## Generate

```
cd rig
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt      # Linux/macOS: .venv/bin/pip
.venv/Scripts/python make_board.py --fixtures
```

Writes `out/board_A4.pdf`, `out/board_Letter.pdf`, `out/board_spec.json`, a second copy `../app/public/board_spec.json`
(identical), and with `--fixtures` ten PNG + JSON pairs in `out/fixtures/` (git-ignored, regenerate with the same command; `--seed` changes the draw).

## The sheet

- Printed content: 180 x 150 mm, centred on the page, so it prints at 100 % on A4 and US Letter and lies on a 13-inch screen.
- Window 80 x 65 mm (cut line drawn at its exact size; cut it out, or leave it white on a transparent film).
- 18 ArUco markers, `DICT_4X4_50`, ids 0 to 17 clockwise from the top-left, side 15 mm (outer edge of the black border), 5 mm from the window.
- Board frame: origin = top-left corner of the window, x right, y down, mm. Markers left of or above the window have negative coordinates. Corner order in the JSON: TL, TR, BR, BL.
- 100 mm ruler with ticks every 10 mm, guide ticks at window mid-height on both sides, "HAUT", "ŒIL DROIT" (right) and "ŒIL GAUCHE" (left) labels. The arrows next to the eye labels are drawn as vectors (Helvetica has no arrow glyph).

## Print check (do this once per printer)

1. Print `board_A4.pdf` or `board_Letter.pdf` at **100 %**, "actual size", never "fit to page".
2. Measure the printed ruler with a calliper or a steel rule, in mm.
3. `python set_print_scale.py 99.0` sets `printScale = 0.99` in both copies of `board_spec.json` and prints it.
   Values outside 0.97 to 1.03 are rejected: fix the print settings and print again.
4. Rebuild and redeploy the app so that `app/public/board_spec.json` is served with the new value.

Running `make_board.py` again resets `printScale` to 1: run `set_print_scale.py` after it.

## Light-box

Open `https://<app>/lightbox.html` on the laptop or tablet, tap "Plein écran", set brightness to maximum, put the sheet flat on the screen with the window in the middle.
The page asks the Screen Wake Lock API to keep the screen on when the browser has it. Touch the screen to show or hide the instructions.

## Risks and backups

| Risk | What to do |
|---|---|
| Dim screen in a bright room (weak contrast at the lens rim) | brightness to maximum, dim the room, close the curtains; backup: a tablet, or a phone torch facing up behind a diffuser (tracing paper) under the window, or a daylight window with the sheet taped to the glass |
| Moire between the screen pixel grid and the camera | put a sheet of tracing paper between the screen and the printed sheet; or defocus slightly, or move the phone a little further back |
| Printer scales the page | print check above |
| Screen has uneven brightness | keep the lens near the window centre; the measurement does not depend on the absolute level |

Contrast and moire behaviour on real screens: TO MEASURE.

## Fixtures

`out/fixtures/fixture_NN_<name>.png` (1600 x 1200, BGR, grey content) with `fixture_NN_<name>.json`:

- `H`: 9 numbers, row-major, board mm to image pixel (pixel-index coordinates, pixel centre at integer coordinates). This is the exact homography used to draw the image.
- `shape` (`ellipse` or `rounded_rect`), `widthMm`, `heightMm`: outer size of the dark rim, axis-aligned in the board frame; `centreMm`, `rimMm`.
- `rimGrey`, `fillGrey`, `backgroundGrey`: grey levels (window background 252). The outer edge sits half-way between `backgroundGrey` and `rimGrey`.
- `tiltDeg` (3 to 20), `blurSigmaPx`, `noiseSigma`, `seed`.

Extremes for segmentation: `fixture_00` and `fixture_02` have a thick dark band (about 3 mm), `fixture_01` and `fixture_03` a faint rim (0.5 to 0.6 mm, grey 200 to 205 on 252).
The photos are synthetic: sharpness, glare and sensor noise of real phones are TO MEASURE.

## Tests

```
.venv/Scripts/python -m pytest tests -q
```

They regenerate everything in a temporary folder and never touch `out/` or `app/public/`.
