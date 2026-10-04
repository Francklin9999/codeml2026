#!/usr/bin/env python3
"""OptiFrame reference sheet generator.

Board frame: origin = top-left corner of the lens window, x right, y down, mm.
Markers left of or above the window therefore have negative coordinates.

    python make_board.py              # PDFs + board_spec.json (two copies)
    python make_board.py --fixtures   # also 10 synthetic photos with ground truth
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
APP_SPEC = HERE.parent / "app" / "public" / "board_spec.json"

VERSION = "OptiFrame board v1"
DICT_NAME = "DICT_4X4_50"
MARKER_MM = 15.0
WINDOW_W, WINDOW_H = 80.0, 65.0
GAP_MM = 5.0                       # window edge to nearest marker edge (brief: >= 4)
RULER_MM = 100.0
GUIDE_Y = WINDOW_H / 2
# Printed content box in the board frame: 180 x 150 mm, centred on the window.
BOX = (WINDOW_W / 2 - 90.0, GUIDE_Y - 75.0, WINDOW_W / 2 + 90.0, GUIDE_Y + 75.0)
PAGES = {"A4": (297.0, 210.0), "Letter": (279.4, 215.9)}   # landscape, mm
PT = 72.0 / 25.4

LINE_W = 0.25                      # mm, ticks and ruler
OUTLINE_W = 0.15                   # mm, window cut line (centred on the window edge)
RULER_Y = 92.0
LABEL_FONT, LABEL_BOLD = "Helvetica", "Helvetica-Bold"


# --------------------------------------------------------------------------- layout

def marker_positions() -> list[tuple[int, float, float]]:
    """(id, left, top) of the 18 markers, clockwise from the top-left."""
    pitch = 21.0
    top, bottom = -GAP_MM - MARKER_MM, WINDOW_H + GAP_MM
    left, right = -GAP_MM - MARKER_MM, WINDOW_W + GAP_MM
    row_x = [left + pitch * i for i in range(6)]
    side_y = [GUIDE_Y - MARKER_MM / 2 + pitch * k for k in (-1, 0, 1)]
    cells = [(x, top) for x in row_x]
    cells += [(right, y) for y in side_y]
    cells += [(x, bottom) for x in reversed(row_x)]
    cells += [(left, y) for y in reversed(side_y)]
    return [(i, x, y) for i, (x, y) in enumerate(cells)]


def build_spec() -> dict:
    markers = []
    for mid, x, y in marker_positions():
        s = MARKER_MM
        markers.append({"id": mid, "corners": [[x, y], [x + s, y], [x + s, y + s], [x, y + s]]})
    return {
        "dictionary": DICT_NAME,
        "markerMm": MARKER_MM,
        "markers": markers,
        "windowMm": {"w": WINDOW_W, "h": WINDOW_H},
        "guideLineYMm": GUIDE_Y,
        "rulerMm": RULER_MM,
        "printScale": 1,
    }


def spec_text(spec: dict) -> str:
    """JSON with one marker per line (same content as json.dumps, easier to read)."""
    head = json.dumps({k: v for k, v in spec.items() if k != "markers"}, indent=2)
    rows = ",\n".join("    " + json.dumps(m) for m in spec["markers"])
    return head[:-2] + ",\n  \"markers\": [\n" + rows + "\n  ]\n}\n"


def aruco_dictionary():
    return cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, DICT_NAME))


def marker_modules(marker_id: int) -> np.ndarray:
    """6x6 boolean grid (True = black) including the one-module black border."""
    img = cv2.aruco.generateImageMarker(aruco_dictionary(), marker_id, 6, borderBits=1)
    return img < 128


def ruler_x0() -> float:
    return WINDOW_W / 2 - RULER_MM / 2


# --------------------------------------------------------------------------- PDF

def _arrow(c: canvas.Canvas, to_pdf, x_from: float, x_to: float, y: float) -> None:
    head = 1.1
    sign = 1 if x_to > x_from else -1
    for a, b, c2, d in [(x_from, y, x_to, y),
                        (x_to, y, x_to - sign * head, y - 0.8),
                        (x_to, y, x_to - sign * head, y + 0.8)]:
        c.line(*to_pdf(a, b), *to_pdf(c2, d))


def _side_label(c, to_pdf, title: str, text: str, right_side: bool) -> None:
    """Two-line label next to the marker ring at guide-line height; arrow drawn as a vector."""
    size = 7.5
    w_text = stringWidth(text, LABEL_FONT, size) / PT
    w_title = stringWidth(title, LABEL_BOLD, size) / PT
    arrow, gap = 4.5, 1.5
    span = max(w_title, w_text + gap + arrow)
    ring_edge = WINDOW_W + GAP_MM + MARKER_MM
    if right_side:
        x0 = ring_edge + 2.0
        if x0 + span > BOX[2]:
            raise ValueError("right label does not fit in the printed box")
        c.setFont(LABEL_BOLD, size); c.drawString(*to_pdf(x0, GUIDE_Y - 1.5), title)
        c.setFont(LABEL_FONT, size); c.drawString(*to_pdf(x0, GUIDE_Y + 3.0), text)
        _arrow(c, to_pdf, x0 + w_text + gap, x0 + w_text + gap + arrow, GUIDE_Y + 3.0 - 1.0)
    else:
        x1 = -GAP_MM - MARKER_MM - 2.0
        x0 = x1 - span
        if x0 < BOX[0]:
            raise ValueError("left label does not fit in the printed box")
        c.setFont(LABEL_BOLD, size); c.drawString(*to_pdf(x0, GUIDE_Y - 1.5), title)
        c.setFont(LABEL_FONT, size); c.drawString(*to_pdf(x0 + arrow + gap, GUIDE_Y + 3.0), text)
        _arrow(c, to_pdf, x0 + arrow, x0, GUIDE_Y + 3.0 - 1.0)


def write_pdf(path: Path, page_name: str, spec: dict) -> None:
    pw, ph = PAGES[page_name]
    off_x, off_y = (pw - (BOX[2] - BOX[0])) / 2, (ph - (BOX[3] - BOX[1])) / 2

    def to_pdf(x: float, y: float) -> tuple[float, float]:
        return (off_x + x - BOX[0]) * PT, (ph - (off_y + y - BOX[1])) * PT

    c = canvas.Canvas(str(path), pagesize=(pw * PT, ph * PT), pageCompression=0)
    c.setTitle(f"{VERSION} ({page_name})")
    c.setFillGray(0); c.setStrokeGray(0)

    # markers: all black modules of a marker in one path (no hairline seams between modules)
    module = MARKER_MM / 6
    for mid, x, y in marker_positions():
        grid = marker_modules(mid)
        path = c.beginPath()
        for r in range(6):
            for k in range(6):
                if grid[r, k]:
                    px, py = to_pdf(x + k * module, y + (r + 1) * module)
                    path.rect(px, py, module * PT, module * PT)
        c.drawPath(path, stroke=0, fill=1)

    # window cut line, exactly the window size
    c.setLineWidth(OUTLINE_W * PT)
    wx, wy = to_pdf(0, WINDOW_H)
    c.rect(wx, wy, WINDOW_W * PT, WINDOW_H * PT, stroke=1, fill=0)

    # guide line: short ticks on both window sides, nothing inside the window
    c.setLineWidth(LINE_W * PT)
    for a, b in [(-3.5, -0.5), (WINDOW_W + 0.5, WINDOW_W + 3.5)]:
        c.line(*to_pdf(a, GUIDE_Y), *to_pdf(b, GUIDE_Y))

    # 100 mm ruler
    x0 = ruler_x0()
    c.line(*to_pdf(x0, RULER_Y), *to_pdf(x0 + RULER_MM, RULER_Y))
    for i in range(11):
        h = 4.0 if i in (0, 5, 10) else 2.5
        c.line(*to_pdf(x0 + 10 * i, RULER_Y), *to_pdf(x0 + 10 * i, RULER_Y - h))
        c.setFont(LABEL_FONT, 5)
        c.drawCentredString(*to_pdf(x0 + 10 * i, RULER_Y + 3.6), str(10 * i))
    c.setFont(LABEL_BOLD, 7)
    c.drawCentredString(*to_pdf(WINDOW_W / 2, RULER_Y + 9.0),
                        "Imprimer à 100 % : cette règle doit mesurer 100 mm")
    c.setFont(LABEL_FONT, 5.5)
    c.drawCentredString(*to_pdf(WINDOW_W / 2, BOX[3] - 2.2),
                        f"{VERSION} - {DICT_NAME} - marker {MARKER_MM:g} mm - window "
                        f"{WINDOW_W:g}x{WINDOW_H:g} mm - {page_name}")

    # orientation labels
    c.setFont(LABEL_BOLD, 11)
    c.drawCentredString(*to_pdf(WINDOW_W / 2, -GAP_MM - MARKER_MM - 8.0), "HAUT")
    c.setLineWidth(0.3 * PT)
    _side_label(c, to_pdf, "ŒIL DROIT :", "nez de ce côté", right_side=True)
    _side_label(c, to_pdf, "ŒIL GAUCHE :", "nez de ce côté", right_side=False)
    c.showPage()
    c.save()


# --------------------------------------------------------------------------- raster

def render_board_ink(px_per_mm: int = 20) -> np.ndarray:
    """Coverage image (float32, 1 = ink) of markers, ruler and ticks over the whole box.

    Pixel index i has its centre at board mm BOX_origin + (i + 0.5) / px_per_mm.
    """
    s = px_per_mm
    w, h = int((BOX[2] - BOX[0]) * s), int((BOX[3] - BOX[1]) * s)
    ink = np.zeros((h, w), np.uint8)

    def px(mm_x: float, mm_y: float) -> tuple[int, int]:
        return round((mm_x - BOX[0]) * s), round((mm_y - BOX[1]) * s)

    cell = int(MARKER_MM / 6 * s)
    for mid, x, y in marker_positions():
        x0, y0 = px(x, y)
        ink[y0:y0 + 6 * cell, x0:x0 + 6 * cell] = np.kron(marker_modules(mid).astype(np.uint8),
                                                          np.ones((cell, cell), np.uint8))
    t = max(1, round(LINE_W * s))

    def hline(xa, xb, y):
        a, b = px(xa, y)[0], px(xb, y)[0]
        yy = px(0, y)[1]
        ink[yy - t // 2: yy - t // 2 + t, a:b + t] = 1

    def vline(x, ya, yb):
        xx = px(x, 0)[0]
        a, b = px(0, ya)[1], px(0, yb)[1]
        ink[a:b, xx - t // 2: xx - t // 2 + t] = 1

    hline(-3.5, -0.5, GUIDE_Y); hline(WINDOW_W + 0.5, WINDOW_W + 3.5, GUIDE_Y)
    hline(ruler_x0(), ruler_x0() + RULER_MM, RULER_Y)
    for i in range(11):
        vline(ruler_x0() + 10 * i, RULER_Y - (4.0 if i in (0, 5, 10) else 2.5), RULER_Y)
    return ink.astype(np.float32)


def board_to_raster_matrix(px_per_mm: float) -> np.ndarray:
    """mm (board frame) -> pixel index coordinates of the render_board_ink image."""
    return np.array([[px_per_mm, 0, -BOX[0] * px_per_mm - 0.5],
                     [0, px_per_mm, -BOX[1] * px_per_mm - 0.5],
                     [0, 0, 1]], float)


def _rounded_rect_poly(cx, cy, w, h, r, n=64) -> np.ndarray:
    pts = []
    for ox, oy, a0 in [(1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)]:
        ccx, ccy = cx + ox * (w / 2 - r), cy + oy * (h / 2 - r)
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
    return np.array(pts)


def _draw_shape(img: np.ndarray, kind: str, s: float, cx: float, cy: float, w: float, h: float,
                rim: float, rim_grey: float, fill_grey: float) -> None:
    """Draw the outer rim colour then the inner fill; (cx, cy, w, h) in mm, outer size."""
    sh = 4
    k = 1 << sh

    def to_idx(mx, my):
        return (mx * s + (-BOX[0] * s - 0.5), my * s + (-BOX[1] * s - 0.5))

    def fixed(p):
        return np.round(np.array(p) * k).astype(np.int32)

    for ww, hh, grey, radius in [(w, h, rim_grey, 8.0), (w - 2 * rim, h - 2 * rim, fill_grey, 8.0 - rim)]:
        if kind == "ellipse":
            ci = to_idx(cx, cy)
            cv2.ellipse(img, tuple(int(v) for v in fixed(ci)),
                        (int(round((ww / 2 * s - EDGE_PX) * k)), int(round((hh / 2 * s - EDGE_PX) * k))), 0, 0, 360,
                        float(grey), -1, cv2.LINE_AA, sh)
        else:
            poly = _rounded_rect_poly(cx, cy, ww - 2 * EDGE_PX / s, hh - 2 * EDGE_PX / s, max(radius, 1.0))
            idx = np.array([to_idx(px_, py_) for px_, py_ in poly])
            cv2.fillPoly(img, [fixed(idx)], float(grey), cv2.LINE_AA, sh)


# --------------------------------------------------------------------------- fixtures

PAPER, WINDOW_LIGHT, INK_GREY = 232.0, 252.0, 22.0
# OpenCV fills include the boundary pixels (about half a pixel too large); shrink so the drawn size is the declared size
EDGE_PX = 0.5
CAM_W, CAM_H, FOCAL = 1600, 1200, 1400.0

# (name, shape, rim mm, rim grey, fill grey, size mm (w, h), blur px, noise, tilt deg)
FIXTURES = [
    ("ellipse_thick_band", "ellipse", 3.0, 28, 232, (52.4, 41.6), 1.0, 2.0, 12),
    ("ellipse_faint_rim", "ellipse", 0.5, 205, 240, (50.0, 38.0), 0.9, 1.5, 8),
    ("rrect_thick_band", "rrect", 2.8, 35, 228, (54.2, 40.4), 1.1, 2.5, 18),
    ("rrect_faint_rim", "rrect", 0.6, 200, 240, (48.6, 36.2), 0.8, 1.5, 15),
    ("ellipse_medium", "ellipse", 1.5, 90, 236, (57.0, 45.0), 1.0, 2.0, 5),
    ("rrect_medium", "rrect", 1.5, 80, 236, (51.0, 33.4), 0.9, 2.0, 20),
    ("ellipse_small_tilted", "ellipse", 1.2, 60, 238, (44.0, 36.0), 1.2, 2.5, 19),
    ("rrect_wide", "rrect", 2.0, 50, 234, (64.0, 40.0), 1.0, 2.0, 10),
    ("ellipse_tall", "ellipse", 2.2, 40, 234, (46.0, 52.0), 0.7, 1.5, 3),
    ("ellipse_blurry_noisy", "ellipse", 2.0, 45, 234, (53.0, 43.0), 1.5, 3.0, 14),
]


def _camera_homography(rng: np.random.Generator, tilt_deg: float) -> np.ndarray:
    """Random board(mm) -> camera pixel homography from a pinhole pose; all markers must be visible."""
    cx_b, cy_b = (BOX[0] + BOX[2]) / 2, (BOX[1] + BOX[3]) / 2
    k = np.array([[FOCAL, 0, (CAM_W - 1) / 2], [0, FOCAL, (CAM_H - 1) / 2], [0, 0, 1]])
    corners = np.array([c for m in build_spec()["markers"] for c in m["corners"]])
    for _ in range(200):
        t = math.radians(tilt_deg)
        az = rng.uniform(0, 2 * math.pi)
        axis = np.array([math.cos(az), math.sin(az), 0.0])
        rot_t = cv2.Rodrigues(axis * t)[0]
        psi = math.radians(rng.uniform(-8, 8))
        rot_z = cv2.Rodrigues(np.array([0, 0, psi]))[0]
        rot = rot_t @ rot_z
        trans = np.array([rng.uniform(-10, 10), rng.uniform(-8, 8), rng.uniform(250, 310)])
        h = k @ np.column_stack([rot[:, 0], rot[:, 1], trans]) @ \
            np.array([[1, 0, -cx_b], [0, 1, -cy_b], [0, 0, 1]])
        p = h @ np.vstack([corners.T, np.ones(len(corners))])
        p = (p[:2] / p[2]).T
        if p.min() > 25 and p[:, 0].max() < CAM_W - 25 and p[:, 1].max() < CAM_H - 25:
            return h / h[2, 2]
    raise RuntimeError("could not place the board in the frame")


def render_fixture(idx: int, seed: int) -> tuple[np.ndarray, dict]:
    name, kind, rim, rim_grey, fill_grey, (sw, sh_), blur, noise, tilt = FIXTURES[idx]
    rng = np.random.default_rng([seed, idx])
    # board scene at 20 px/mm, shape drawn at full precision, then area-reduced to 10 px/mm
    s_hi = 20
    ink = render_board_ink(s_hi)
    scene = PAPER * (1 - ink) + INK_GREY * ink
    wx0, wy0 = round((0 - BOX[0]) * s_hi), round((0 - BOX[1]) * s_hi)
    scene[wy0:wy0 + int(WINDOW_H * s_hi), wx0:wx0 + int(WINDOW_W * s_hi)] = WINDOW_LIGHT
    # window cut line, centred on the window edge, like the PDF
    t = max(1, round(OUTLINE_W * s_hi))
    for (x, y, w, h) in [(wx0 - t // 2, wy0 - t // 2, int(WINDOW_W * s_hi) + t, t),
                         (wx0 - t // 2, wy0 + int(WINDOW_H * s_hi) - t // 2, int(WINDOW_W * s_hi) + t, t),
                         (wx0 - t // 2, wy0, t, int(WINDOW_H * s_hi)),
                         (wx0 + int(WINDOW_W * s_hi) - t // 2, wy0, t, int(WINDOW_H * s_hi))]:
        scene[y:y + h, x:x + w] = INK_GREY
    # shape position: random but fully inside the window with 4 mm margin
    mx, my = (WINDOW_W - sw) / 2 - 4.0, (WINDOW_H - sh_) / 2 - 4.0
    cx = WINDOW_W / 2 + rng.uniform(-min(mx, 3.0), min(mx, 3.0))
    cy = WINDOW_H / 2 + rng.uniform(-min(my, 3.0), min(my, 3.0))
    _draw_shape(scene, kind, s_hi, cx, cy, sw, sh_, rim, rim_grey, fill_grey)
    scene = cv2.resize(scene, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    s = s_hi // 2

    h_true = _camera_homography(rng, tilt)
    # raster (index) -> camera, rendered at 2x then area-reduced
    to_raster = board_to_raster_matrix(s)
    up = np.array([[2, 0, 0.5], [0, 2, 0.5], [0, 0, 1.0]])         # camera index -> 2x index
    m = up @ h_true @ np.linalg.inv(to_raster)
    cam2 = cv2.warpPerspective(scene, m, (CAM_W * 2, CAM_H * 2), flags=cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_CONSTANT, borderValue=PAPER * 0.8)
    cam = cv2.resize(cam2, (CAM_W, CAM_H), interpolation=cv2.INTER_AREA)
    cam = cv2.GaussianBlur(cam, (0, 0), blur)
    yy, xx = np.mgrid[0:CAM_H, 0:CAM_W]
    cam *= 1 + 0.03 * ((xx - CAM_W / 2) / CAM_W + 0.5 * (yy - CAM_H / 2) / CAM_H)
    cam += rng.normal(0, noise, cam.shape)
    img = np.clip(np.round(cam), 0, 255).astype(np.uint8)
    truth = {
        "name": name,
        "H": [float(v) for v in h_true.flatten()],          # row-major, board mm -> image pixel index
        "imageSize": [CAM_W, CAM_H],
        "shape": "ellipse" if kind == "ellipse" else "rounded_rect",
        "widthMm": sw, "heightMm": sh_,                     # outer size of the dark rim
        "centreMm": [cx, cy], "rimMm": rim,
        "rimGrey": rim_grey, "fillGrey": fill_grey, "backgroundGrey": WINDOW_LIGHT,
        "tiltDeg": tilt, "blurSigmaPx": blur, "noiseSigma": noise, "seed": seed,
    }
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR), truth


def write_fixtures(out_dir: Path, seed: int) -> list[Path]:
    fx = out_dir / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    written = []
    for i in range(len(FIXTURES)):
        img, truth = render_fixture(i, seed)
        stem = fx / f"fixture_{i:02d}_{truth['name']}"
        cv2.imwrite(str(stem) + ".png", img)
        Path(str(stem) + ".json").write_text(json.dumps(truth, indent=2) + "\n", encoding="utf-8")
        written.append(Path(str(stem) + ".png"))
    return written


# --------------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fixtures", action="store_true", help="also render 10 synthetic test photos")
    ap.add_argument("--out", type=Path, default=OUT_DIR, help="output directory (default rig/out)")
    ap.add_argument("--app-spec", type=Path, default=APP_SPEC,
                    help="second copy of board_spec.json (default app/public/board_spec.json)")
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    spec = build_spec()
    text = spec_text(spec)
    (args.out / "board_spec.json").write_text(text, encoding="utf-8")
    args.app_spec.parent.mkdir(parents=True, exist_ok=True)
    args.app_spec.write_text(text, encoding="utf-8")
    for name in PAGES:
        write_pdf(args.out / f"board_{name}.pdf", name, spec)
    print(f"wrote board_A4.pdf, board_Letter.pdf, board_spec.json (x2) in {args.out}")
    if args.fixtures:
        n = len(write_fixtures(args.out, args.seed))
        print(f"wrote {n} fixtures in {args.out / 'fixtures'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
