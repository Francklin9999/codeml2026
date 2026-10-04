"""Rig-domain synthetic lens samples: what the rectified 80x65 mm window really looks like.

synth.py covers generic backgrounds. This generator targets the cases where the classical segmenter
gives up (NO_LENS) and the model is the fallback: a clear lens on the backlit sheet or on white paper,
with a faint, uneven or broken edge band, glare that crosses the edge, dust, moire and paper strips at the
window border. Same output format as synth.py (800x650 px at 10 px/mm, exact masks), so split.py,
train.py and evaluate.py read it unchanged.

Scene families (probabilities in SCENES):
  backlit   lens on the white screen seen through the window (the rig as designed)
  paper     lens on white paper under room light, no backlight
  table     lens on a speckled off-white table top (formica, granite), no backlight: the case a team showed on Discord
  tinted    sunglass lens on either background (high contrast, keeps the easy case in the data)
  mounted   lens still in its frame (the jury's own pair): label = the visible lens, frame is background
  pattern   generic procedural background from synth.py (colour screen, texture)
  empty     no lens at all: the target is an empty mask, so the model learns to say "nothing here"
  cut       lens crossing the window border (badly placed): the label is the visible part and touches the border, so
            the app answers LENS_OUT_OF_WINDOW instead of measuring a truncated lens (A_mm, B_mm left empty)

Usage:  python synth_rig.py --n 6000 [--out DIR] [--seed 0] [--workers 8]
Output: DIR/images/rigNNNNNN_0_<scene>.jpg, DIR/masks/*.png (0/255), DIR/index.csv (source = synth, cond = scene,
        plus A_mm and B_mm: exact extents of the outline along the window x and y axes, empty for "empty").
"""
from __future__ import annotations

import argparse
import csv
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cv2
import numpy as np

import synth

PX, W_PX, H_PX = synth.PX, synth.W_PX, synth.H_PX
SCENES = {"backlit": 0.45, "paper": 0.25, "tinted": 0.08, "mounted": 0.05, "pattern": 0.12, "empty": 0.05}
# Not drawn by default (keeps the seeds of the first data set reproducible): pass --scenes table, or mix it in.
EXTRA_SCENES = ("table", "cut")
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "_local" / "synth_rig"

_YY, _XX = np.mgrid[0:H_PX, 0:W_PX].astype(np.float32)


# ---------------------------------------------------------------- helpers

N_ANGLES = 720                                            # angle-dependent terms are tabulated, then looked up per pixel
_ANGLES = np.linspace(-np.pi, np.pi, N_ANGLES, endpoint=False).astype(np.float32)


def _periodic(rng: np.random.Generator, n_terms: int = 4, amp: float = 1.0) -> np.ndarray:
    """Smooth random periodic function of the angle (N_ANGLES samples), zero mean, roughly in [-amp, amp]."""
    out = np.zeros(N_ANGLES, np.float32)
    for k in range(1, n_terms + 1):
        out += rng.normal(0, 1) / k * np.cos(k * _ANGLES + rng.uniform(0, 2 * np.pi))
    return (amp * out / max(1e-6, float(np.abs(out).max()))).astype(np.float32)


def _arc_bumps(rng: np.random.Generator, n: int, width_deg: tuple[float, float]) -> np.ndarray:
    """Max of n wrapped gaussian bumps along the angle (N_ANGLES samples), each in [0, 1]."""
    out = np.zeros(N_ANGLES, np.float32)
    for _ in range(n):
        c = rng.uniform(-np.pi, np.pi)
        w = np.radians(rng.uniform(*width_deg))
        d = np.angle(np.exp(1j * (_ANGLES - c)))
        out = np.maximum(out, np.exp(-0.5 * (d / w) ** 2).astype(np.float32))
    return out


def _fine_texture(rng: np.random.Generator, sigma: float, amp: float) -> np.ndarray:
    n = rng.normal(0, 1, (H_PX, W_PX)).astype(np.float32)
    n = cv2.GaussianBlur(n, (0, 0), sigma)
    return amp * n / max(1e-6, float(n.std()))


def _moire(rng: np.random.Generator) -> np.ndarray:
    th, period = rng.uniform(0, np.pi), rng.uniform(2.5, 14)
    m = np.sin(2 * np.pi * (_XX * np.cos(th) + _YY * np.sin(th)) / period)
    if rng.random() < 0.4:
        th2 = th + rng.uniform(1.2, 1.9)
        m = 0.5 * (m + np.sin(2 * np.pi * (_XX * np.cos(th2) + _YY * np.sin(th2)) / rng.uniform(2.5, 14)))
    return m.astype(np.float32)


def _white_balance(rng: np.random.Generator, warm: float = 0.06) -> np.ndarray:
    return (1 + rng.uniform(-warm, warm, 3)).astype(np.float32)


# ---------------------------------------------------------------- backgrounds (float32 BGR, 0..1+)

def backlit_background(rng: np.random.Generator) -> np.ndarray:
    level = rng.uniform(0.82, 1.08)                       # > 1 clips: an overexposed backlight is common
    g = np.ones((H_PX, W_PX), np.float32)
    th = rng.uniform(0, 2 * np.pi)
    ramp = (_XX * np.cos(th) + _YY * np.sin(th)) / W_PX
    g *= 1 + rng.uniform(-0.08, 0.08) * (ramp - ramp.mean())
    r = np.hypot(_XX - rng.uniform(0.3, 0.7) * W_PX, _YY - rng.uniform(0.3, 0.7) * H_PX) / W_PX
    g *= 1 - rng.uniform(0, 0.12) * r ** 2
    if rng.random() < 0.5:                                # moire between the screen grid and the sensor
        g *= 1 + rng.uniform(0.005, 0.04) * _moire(rng)
    if rng.random() < 0.5:                                # tracing paper or the sheet itself over the screen
        g *= 1 + _fine_texture(rng, rng.uniform(0.6, 2.5), rng.uniform(0.005, 0.025))
    return level * g[..., None] * _white_balance(rng)[None, None]


def paper_background(rng: np.random.Generator) -> np.ndarray:
    level = rng.uniform(0.55, 0.95)
    g = np.ones((H_PX, W_PX), np.float32)
    lx, ly = rng.uniform(-0.5, 1.5) * W_PX, rng.uniform(-0.5, 1.5) * H_PX     # lamp falloff
    g *= 1 - rng.uniform(0, 0.25) * np.hypot(_XX - lx, _YY - ly) / (1.5 * W_PX)
    g *= 1 + _fine_texture(rng, rng.uniform(0.7, 2.0), rng.uniform(0.004, 0.02))
    if rng.random() < 0.35:                               # soft shadow of the phone or the hand
        blob = np.zeros((H_PX, W_PX), np.float32)
        cx, cy = rng.uniform(-0.3, 1.3) * W_PX, rng.uniform(-0.3, 1.3) * H_PX
        cv2.ellipse(blob, (int(cx), int(cy)), (int(rng.uniform(150, 500)), int(rng.uniform(100, 400))), rng.uniform(0, 180), 0, 360, 1.0, -1)
        blob = cv2.GaussianBlur(blob, (0, 0), rng.uniform(20, 80))
        g *= 1 - rng.uniform(0.1, 0.45) * blob
    return level * g[..., None] * _white_balance(rng, 0.08)[None, None]


def speckled_background(rng: np.random.Generator) -> np.ndarray:
    """Off-white table top with dark and coloured specks and a soft mottling, lit by the room."""
    base = paper_background(rng)
    layer = np.zeros((H_PX, W_PX, 3), np.float32)
    weight = np.zeros((H_PX, W_PX), np.float32)
    n = int(rng.integers(1500, 25000))
    xs, ys = rng.integers(0, W_PX, n), rng.integers(0, H_PX, n)
    rs = rng.choice([1, 1, 1, 2, 2, 3], n)
    palette = np.array(rng.choice([[0.15, 0.15, 0.15], [0.35, 0.3, 0.25], [0.5, 0.45, 0.4], [0.25, 0.3, 0.45], [0.6, 0.55, 0.5]],
                                  int(rng.integers(2, 5))), np.float32)
    for x, y, r in zip(xs, ys, rs):
        c = palette[int(rng.integers(len(palette)))]
        cv2.circle(layer, (int(x), int(y)), int(r), c.tolist(), -1)
        cv2.circle(weight, (int(x), int(y)), int(r), 1.0, -1)
    weight = cv2.GaussianBlur(weight, (0, 0), 0.6) * rng.uniform(0.4, 1.0)
    layer = cv2.GaussianBlur(layer, (0, 0), 0.6)
    level = float(np.median(base))
    mottling = 1 + rng.uniform(0, 0.06) * (synth._noise_field(rng, (6, 12, 24)) - 0.5)
    return (base * (1 - weight[..., None]) + layer * level * weight[..., None]) * mottling[..., None]


def window_border(rng: np.random.Generator, img: np.ndarray) -> np.ndarray:
    """Paper strips and the printed cut line where the window was cut a little off (backlit scenes)."""
    out = img.copy()
    for side in range(4):
        if rng.random() > 0.3:
            continue
        w = int(rng.integers(1, 16))
        paper = float(rng.uniform(0.45, 0.9))
        if side == 0:
            out[:w] = out[:w] * paper
        elif side == 1:
            out[-w:] = out[-w:] * paper
        elif side == 2:
            out[:, :w] = out[:, :w] * paper
        else:
            out[:, -w:] = out[:, -w:] * paper
        if rng.random() < 0.4:                            # the printed cut line itself
            t = int(rng.integers(1, 4))
            k = float(rng.uniform(0.05, 0.4))
            if side == 0:
                out[w:w + t] *= k
            elif side == 1:
                out[-w - t:-w] *= k
            elif side == 2:
                out[:, w:w + t] *= k
            else:
                out[:, -w - t:-w] *= k
    return out


# ---------------------------------------------------------------- lens rendering

def render_lens(rng: np.random.Generator, bg: np.ndarray, poly: np.ndarray, scene: str) -> np.ndarray:
    """Composite one lens (outline poly in mm) over bg. Returns float32 BGR."""
    alpha = synth.rasterize(poly)
    mask = (alpha >= 0.5).astype(np.uint8)
    cx, cy = poly[:, 0].mean() * PX, poly[:, 1].mean() * PX
    tidx = (((np.arctan2(_YY - cy, _XX - cx) + np.pi) / (2 * np.pi) * N_ANGLES).astype(np.int32)) % N_ANGLES
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5).astype(np.float32)        # px inside the outline
    level = float(np.median(bg[mask > 0])) if mask.any() else 1.0

    # interior: background seen through a thin lens (magnified or minified), transmission, tint
    m = rng.uniform(0.9, 1.12)
    inside = cv2.remap(bg, (cx + (_XX - cx) / m).astype(np.float32), (cy + (_YY - cy) / m).astype(np.float32),
                       cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if scene == "tinted":
        tint = rng.uniform(0.1, 0.65) * np.array(rng.choice([[1, 1, 1], [0.6, 0.8, 1.0], [0.6, 1.0, 0.7], [0.9, 0.8, 0.6]]), np.float32)
        inside = inside * tint
    else:
        inside = inside * rng.uniform(0.88, 0.99) * (1 - rng.uniform(0, 0.06, 3)).astype(np.float32)
    if rng.random() < 0.5:                                # anti-reflection coating sheen (green / purple)
        sheen = synth._noise_field(rng, (2, 4, 8))
        col = np.array(rng.choice([[0.4, 1.0, 0.5], [1.0, 0.4, 0.9], [1.0, 0.8, 0.3]]), np.float32)
        inside = inside + rng.uniform(0.01, 0.07) * level * sheen[..., None] * col
    if rng.random() < 0.4:                                # fingerprint smudge
        smudge = cv2.GaussianBlur(_fine_texture(rng, 3, 1.0) * synth._noise_field(rng, (3, 6)), (0, 0), 2)
        inside = inside * (1 + rng.uniform(0.01, 0.05) * smudge)[..., None]

    # the edge band: refraction at the bevel darkens a band just inside the outline. Width and darkness vary
    # along the perimeter, and some arcs nearly vanish (the faint, broken rim the classical path rejects).
    base_w = rng.uniform(0.15, 2.5) * PX
    w_theta = np.clip(base_w * (1 + _periodic(rng, 3, rng.uniform(0, 0.6))), 0.12 * PX, 3.5 * PX)
    if scene in ("paper", "table"):
        base_d = rng.uniform(0.02, 0.35)
    else:
        base_d = rng.choice([rng.uniform(0.03, 0.2), rng.uniform(0.2, 0.9)], p=[0.55, 0.45])
    d_theta = np.clip(base_d * (1 + _periodic(rng, 4, rng.uniform(0, 0.7))), 0.0, 0.95)
    if rng.random() < 0.6:
        d_theta = d_theta * (1 - rng.uniform(0.6, 1.0) * _arc_bumps(rng, int(rng.integers(1, 4)), (8, 40)))
    w_theta, d_theta = w_theta[tidx], d_theta[tidx]                # per pixel
    soft = rng.uniform(0.15, 0.6) * PX
    band = np.clip((w_theta - dist) / soft + 0.5, 0, 1) * d_theta
    band_col = np.float32(rng.uniform(0.0, 0.35) * level)
    lens = inside * (1 - band[..., None]) + band_col * band[..., None]

    if rng.random() < 0.5:                                # light piped through the edge: a thin bright line inside the band
        lw = rng.uniform(0.1, 0.5) * PX
        line = np.clip(dist - w_theta + 0.5, 0, 1) * np.clip(w_theta + lw - dist, 0, 1) * rng.uniform(0.05, 0.5)
        lens = lens + line[..., None] * (level * 1.1 - lens)
    if rng.random() < 0.45:                               # glint along part of the edge: bright arcs over the dark band
        arc = _arc_bumps(rng, int(rng.integers(1, 3)), (5, 35))[tidx]
        gw = rng.uniform(0.2, 1.2) * PX
        glint = arc * np.clip(gw - dist + 0.5, 0, 1) * rng.uniform(0.4, 1.0)
        lens = lens + glint[..., None] * (level * rng.uniform(1.0, 1.25) - lens)

    # specular highlights on the surface (room lights, a window): inside the lens only
    for _ in range(int(rng.integers(0, 4))):
        layer = np.zeros((H_PX, W_PX), np.float32)
        ys, xs = np.nonzero(mask)
        if xs.size == 0:
            break
        k = int(rng.integers(xs.size))
        if rng.random() < 0.5:
            cv2.ellipse(layer, (int(xs[k]), int(ys[k])), (int(rng.uniform(2, 18) * PX), int(rng.uniform(0.4, 4) * PX)),
                        rng.uniform(0, 180), 0, 360, 1.0, -1)
        else:
            w2, h2 = rng.uniform(3, 15) * PX, rng.uniform(2, 10) * PX
            box = cv2.boxPoints(((float(xs[k]), float(ys[k])), (w2, h2), rng.uniform(0, 90))).astype(np.int32)
            cv2.fillConvexPoly(layer, box, 1.0)
        layer = cv2.GaussianBlur(layer, (0, 0), rng.uniform(1, 10)) * rng.uniform(0.15, 1.0)
        lens = lens + layer[..., None] * (level * rng.uniform(1.0, 1.3) - lens)

    # outside the outline: drop shadow and caustic (strong without backlight, faint with it)
    sh_amt = rng.uniform(0.05, 0.35) if scene in ("paper", "table") else rng.uniform(0, 0.08)
    if sh_amt > 0.01:
        dx, dy = rng.uniform(-3, 3) * PX, rng.uniform(-3, 3) * PX
        shifted = cv2.warpAffine(alpha, np.float32([[1, 0, dx], [0, 1, dy]]), (W_PX, H_PX))
        sh = cv2.GaussianBlur(shifted, (0, 0), rng.uniform(0.5, 3) * PX)
        ring = np.clip(sh - cv2.GaussianBlur(shifted, (0, 0), rng.uniform(4, 8) * PX), 0, 1)
        bg = bg * (1 - sh_amt * sh)[..., None]
        if scene in ("paper", "table") and rng.random() < 0.5:
            bg = bg + rng.uniform(0.05, 0.25) * level * ring[..., None]                 # caustic crescent
    return bg * (1 - alpha[..., None]) + lens * alpha[..., None]


def mounted_frame(rng: np.random.Generator, img: np.ndarray, mask: np.ndarray, poly: np.ndarray) -> np.ndarray:
    """Opaque eyewire around the lens, with a bridge leaving the window on one side and an endpiece on the other."""
    fw = int(rng.uniform(1.5, 6) * PX)
    ring = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * fw + 1, 2 * fw + 1))) & (1 - mask)
    x0, x1 = poly[:, 0].min() * PX, poly[:, 0].max() * PX
    cy = int(poly[:, 1].mean() * PX)
    side = 1 if rng.random() < 0.5 else -1
    bridge_y = int(cy - rng.uniform(0.1, 0.4) * (np.ptp(poly[:, 1]) * PX))
    bx = int(x1 if side > 0 else x0)
    cv2.rectangle(ring, (bx, bridge_y - fw // 2), (W_PX if side > 0 else 0, bridge_y + fw // 2), 1, -1)
    ex = int(x0 if side > 0 else x1)
    cv2.rectangle(ring, (ex, cy - int(1.5 * fw)), (ex - side * int(rng.uniform(3, 8) * PX), cy - int(0.2 * fw)), 1, -1)
    ring = ring & (1 - mask)
    if rng.random() < 0.6:
        col = rng.uniform(0.02, 0.25) * np.ones(3, np.float32)
    else:                                                 # coloured or tortoiseshell acetate
        col = np.array(rng.uniform(0.05, 0.8, 3), np.float32)
    frame = col[None, None] * (0.7 + 0.6 * synth._noise_field(rng, (4, 16, 64)))[..., None]
    soft = cv2.GaussianBlur(ring.astype(np.float32), (0, 0), 0.7)
    return img * (1 - soft[..., None]) + frame * soft[..., None]


def dust(rng: np.random.Generator, img: np.ndarray, level: float) -> np.ndarray:
    out = img.copy()
    layer = np.zeros((H_PX, W_PX), np.float32)
    for _ in range(int(rng.integers(0, 40))):
        cv2.circle(layer, (int(rng.integers(W_PX)), int(rng.integers(H_PX))), int(rng.integers(1, 4)), float(rng.uniform(0.2, 1.0)), -1)
    for _ in range(int(rng.integers(0, 4))):                              # fibres and hairs
        pts = np.cumsum(rng.normal(0, 6, (int(rng.integers(5, 30)), 2)), 0) + rng.uniform([0, 0], [W_PX, H_PX])
        cv2.polylines(layer, [pts.astype(np.int32)], False, float(rng.uniform(0.3, 1.0)), 1, cv2.LINE_AA)
    layer = cv2.GaussianBlur(layer, (0, 0), 0.6)
    dark = rng.random() < 0.7
    return out * (1 - 0.6 * layer[..., None]) if dark else out + layer[..., None] * 0.5 * (level - out)


def camera(rng: np.random.Generator, img: np.ndarray) -> np.ndarray:
    """Phone capture and rectification losses: resolution, defocus, motion, exposure, noise, JPEG."""
    img = img * rng.uniform(0.85, 1.15)
    if rng.random() < 0.7:                                # the photo had fewer px/mm than the 10 px/mm window
        f = rng.uniform(0.4, 1.0)
        small = cv2.resize(img, (int(W_PX * f), int(H_PX * f)), interpolation=cv2.INTER_AREA)
        img = cv2.resize(small, (W_PX, H_PX), interpolation=cv2.INTER_LINEAR)
    s = rng.uniform(0, 1.8)
    if s > 0.2:
        img = cv2.GaussianBlur(img, (0, 0), s)
    if rng.random() < 0.1:
        k = int(rng.integers(3, 9))
        ker = np.zeros((k, k), np.float32)
        ker[k // 2] = 1 / k
        rot = cv2.getRotationMatrix2D((k / 2 - 0.5, k / 2 - 0.5), rng.uniform(0, 180), 1)
        img = cv2.filter2D(img, -1, cv2.warpAffine(ker, rot, (k, k)))
    img = np.clip(img, 0, 1) ** rng.uniform(0.8, 1.25)
    shot, read = rng.uniform(0, 0.003), rng.uniform(0, 0.0004)
    img = img + rng.normal(0, 1, img.shape).astype(np.float32) * np.sqrt(shot * img + read)
    img = np.clip(img, 0, 1)
    ok, buf = cv2.imencode(".jpg", (img * 255 + 0.5).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, int(rng.integers(55, 96))])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


# ---------------------------------------------------------------- sample

def generate_rig_sample(rng: np.random.Generator, scene: str | None = None):
    """Returns (image BGR uint8, mask uint8 0/255, info)."""
    scene = scene or str(rng.choice(list(SCENES), p=list(SCENES.values())))
    if scene == "pattern":
        bg = synth.procedural_background(rng)
    elif scene == "table":
        bg = speckled_background(rng)
    elif scene == "paper" or (scene in ("tinted", "mounted") and rng.random() < 0.4):
        bg = paper_background(rng)
    else:
        bg = backlit_background(rng)
    info: dict = {"scene": scene}
    if scene == "cut":
        bg = (backlit_background, paper_background, speckled_background)[int(rng.integers(3))](rng)
        poly, pinfo = synth.lens_polygon(rng)
        side, d = int(rng.integers(4)), rng.uniform(0.5, 15.0)          # mm of lens beyond the border
        lo, hi = poly.min(0), poly.max(0)
        shift = [np.array([-(lo[0] + d), 0]), np.array([synth.WIN_W - hi[0] + d, 0]),
                 np.array([0, -(lo[1] + d)]), np.array([0, synth.WIN_H - hi[1] + d])][side]
        poly = poly + shift
        info.update(pinfo)
        info["cut_mm"] = float(d)
        img = render_lens(rng, bg, poly, "backlit")
        mask = (synth.rasterize(poly) >= 0.5).astype(np.uint8) * 255
        info["area_mm2"] = float((mask > 0).sum()) / PX ** 2
    elif scene == "empty":
        img = bg
        mask = np.zeros((H_PX, W_PX), np.uint8)
        info["area_mm2"] = 0.0
    else:
        poly, pinfo = synth.lens_polygon(rng)
        info.update(pinfo)
        info["polygon_mm"] = poly
        info["area_mm2"] = synth.polygon_area(poly)
        img = render_lens(rng, bg, poly, scene)
        mask = (synth.rasterize(poly) >= 0.5).astype(np.uint8)
        if scene == "mounted":
            img = mounted_frame(rng, img, mask, poly)
        mask = mask * 255
    level = float(np.median(bg))
    if scene != "pattern" and rng.random() < 0.5:
        img = window_border(rng, img)
    if rng.random() < 0.6:
        img = dust(rng, img, level)
    return camera(rng, img), mask, info


def _init_worker() -> None:
    cv2.setNumThreads(1)                                  # one process per core: OpenCV's own threads only oversubscribe


def _write_one(args: tuple[int, int, str, tuple[str, ...]]) -> tuple[str, str, str, str, str]:
    i, seed, out, scenes = args
    rng = np.random.default_rng([seed, i])
    img, mask, info = generate_rig_sample(rng, str(rng.choice(list(scenes))) if scenes else None)
    lens = f"rig{seed:02d}{i:06d}"
    stem = f"{lens}_0_{info['scene']}"
    out_p = Path(out)
    for path, arr in ((out_p / "images" / (stem + ".jpg"), img), (out_p / "masks" / (stem + ".png"), mask)):
        params = [cv2.IMWRITE_JPEG_QUALITY, 97] if path.suffix == ".jpg" else []
        ok, buf = cv2.imencode(path.suffix, arr, params)
        buf.tofile(str(path))
    poly = info.get("polygon_mm")
    a, b = ("", "") if poly is None or info["scene"] == "cut" else (f"{np.ptp(poly[:, 0]):.4f}", f"{np.ptp(poly[:, 1]):.4f}")
    return stem + ".jpg", lens, info["scene"], a, b


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="default training/_local/synth_rig (git-ignored)")
    ap.add_argument("--seed", type=int, default=0, help="also part of every lensId, so two seeds never collide")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--scenes", nargs="*", default=[], help=f"draw only these scenes, uniformly ({', '.join([*SCENES, *EXTRA_SCENES])})")
    a = ap.parse_args(argv)
    (a.out / "images").mkdir(parents=True, exist_ok=True)
    (a.out / "masks").mkdir(parents=True, exist_ok=True)
    jobs = [(i, a.seed, str(a.out), tuple(a.scenes)) for i in range(a.n)]
    if a.workers > 1:
        with ProcessPoolExecutor(a.workers, initializer=_init_worker) as ex:
            rows = list(ex.map(_write_one, jobs, chunksize=16))
    else:
        rows = [_write_one(j) for j in jobs]
    with open(a.out / "index.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["file", "lensId", "pos", "cond", "source", "A_mm", "B_mm"])   # A, B: exact extents along x, y
        for file, lens, scene, a_mm, b_mm in rows:
            wr.writerow([file, lens, "0", scene, "synth", a_mm, b_mm])
    print(f"{a.n} rig-domain synthetic samples in {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
