"""Tiny board renderer for tests: own spec (80x65 mm window, 4 ArUco markers), own lens shape, own camera."""
import cv2
import numpy as np

PX = 10
OFF = 250                      # canvas px of board origin (window top-left)
CANVAS = (1300, 1150)          # w, h: board x in [-25, 105] mm, y in [-25, 90] mm
MARKERS = {0: (-18, -18), 1: (86, -18), 2: (86, 71), 3: (-18, 71)}   # top-left of each 12 mm marker


def make_spec():
    mk = []
    for i, (x, y) in MARKERS.items():
        mk.append({"id": i, "corners": [[x, y], [x + 12, y], [x + 12, y + 12], [x, y + 12]]})
    return {"dictionary": "DICT_4X4_50", "markerMm": 12, "markers": mk, "windowMm": {"w": 80, "h": 65},
            "guideLineYMm": 60, "rulerMm": 100, "printScale": 1}


def superellipse_mm(cx, cy, a, b, n=2.6, rot_deg=0.0, k=360):
    t = np.linspace(0, 2 * np.pi, k, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    p = np.stack([a * np.sign(c) * np.abs(c) ** (2 / n), b * np.sign(s) * np.abs(s) ** (2 / n)], 1)
    r = np.radians(rot_deg)
    return p @ np.array([[np.cos(r), np.sin(r)], [-np.sin(r), np.cos(r)]]) + [cx, cy]


def render_board(poly_mm, rim_mm=1.0, window="gradient", seed=0):
    """Returns (canvas BGR uint8, ground-truth mask 650x800 bool). Rim is a dark band inside the outline."""
    rng = np.random.default_rng(seed)
    cv_w, cv_h = CANVAS
    img = np.full((cv_h, cv_w), 255, np.uint8)
    dico = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    for i, (x, y) in MARKERS.items():
        x0, y0 = int((x * PX) + OFF), int((y * PX) + OFF)
        img[y0:y0 + 120, x0:x0 + 120] = cv2.aruco.generateImageMarker(dico, i, 120)
    yy, xx = np.mgrid[0:650, 0:800]
    if window == "gradient":      # uneven backlight
        win = 200 + 55 * (xx / 800.0) * (0.5 + 0.5 * yy / 650.0)
    else:                         # stripes: a "hard" shot background
        win = 120 + 100 * (np.sin(xx / 7.0 + yy / 11.0) > 0) + rng.normal(0, 5, (650, 800))
    img[OFF:OFF + 650, OFF:OFF + 800] = np.clip(win, 0, 255).astype(np.uint8)

    ss = 4
    big = np.zeros((cv_h * ss, cv_w * ss), np.uint8)
    cv2.fillPoly(big, [np.round((poly_mm * PX + OFF) * ss).astype(np.int32)], 255)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(rim_mm * PX * ss) * 2 + 1,) * 2)
    inner = cv2.erode(big, k)
    outer = cv2.resize(big, CANVAS, interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    inn = cv2.resize(inner, CANVAS, interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    f = img.astype(np.float32)
    f = f * (1 - outer) + 25 * outer           # dark rim
    f = f * (1 - inn) + (f * 0 + 215) * inn    # lens interior, slightly darker than the backlight
    gt = outer[OFF:OFF + 650, OFF:OFF + 800] >= 0.5
    return cv2.cvtColor(np.clip(f, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR), gt


def camera_view(canvas, shift=(0.0, 0.0), size=(1600, 1300), noise=0.0, seed=0):
    dst = np.float32([[150, 120], [1450, 90], [1500, 1180], [100, 1200]]) + np.float32(shift)
    src = np.float32([[0, 0], [CANVAS[0], 0], [CANVAS[0], CANVAS[1]], [0, CANVAS[1]]])
    out = cv2.warpPerspective(canvas, cv2.getPerspectiveTransform(src, dst), size, borderValue=(255, 255, 255))
    if noise:
        out = np.clip(out + np.random.default_rng(seed).normal(0, noise, out.shape), 0, 255).astype(np.uint8)
    return out
