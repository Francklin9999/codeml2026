"""Synthetic lens samples (800x650 px = the 80x65 mm window at 10 px/mm) with exact masks.

Families: superellipse, rounded rectangle, aviator, cat-eye. The lens is composited over a
background (team-supplied images, or procedural noise/gradients/stripes) with: thin-lens
magnification of the background inside the shape, a dark rim, a Fresnel-like brighter edge,
0-3 elliptical highlights, a soft shadow, blur, noise and JPEG compression.

Usage:  python synth.py --n 500 [--out DIR] [--seed 0] [--bg-dir DIR]
Output: DIR/images/synthNNNNNN_0_synth.jpg, DIR/masks/*.png (0/255), DIR/index.csv (source = synth).
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import cv2
import numpy as np

PX = 10                      # px per mm
W_PX, H_PX = 800, 650
WIN_W, WIN_H = W_PX / PX, H_PX / PX
SS = 4                       # supersampling of the shape mask
MARGIN_MM = 2.0              # shape stays this far from the window border
FAMILIES = ("superellipse", "rounded_rect", "aviator", "cat_eye")
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "_local" / "synth"


# ---------------------------------------------------------------- shapes (mm, centred on the origin)

def _superellipse(a: float, b: float, n: float, k: int = 360) -> np.ndarray:
    t = np.linspace(0, 2 * np.pi, k, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    return np.stack([a * np.sign(c) * np.abs(c) ** (2 / n), b * np.sign(s) * np.abs(s) ** (2 / n)], 1)


def _rounded_rect(a: float, b: float, r: float, k: int = 60) -> np.ndarray:
    pts = []
    for cx, cy, th0 in ((a - r, b - r, 0), (-(a - r), b - r, 90), (-(a - r), -(b - r), 180), (a - r, -(b - r), 270)):
        th = np.radians(np.linspace(th0, th0 + 90, k))
        pts.append(np.stack([cx + r * np.cos(th), cy + r * np.sin(th)], 1))
    return np.concatenate(pts)


def _fit_box(p: np.ndarray, w: float, h: float) -> np.ndarray:
    lo, hi = p.min(0), p.max(0)
    return (p - (lo + hi) / 2) * np.array([w / (hi[0] - lo[0]), h / (hi[1] - lo[1])])


def lens_polygon(rng: np.random.Generator, family: str | None = None) -> tuple[np.ndarray, dict]:
    """Random lens outline in mm, centred on the origin, rotated, fitted inside the window."""
    family = family or str(rng.choice(FAMILIES))
    w = rng.uniform(35, 65)
    h = w * rng.uniform(0.6, 0.95)
    a, b = w / 2, h / 2
    if family == "superellipse":
        p = _superellipse(a, b, rng.uniform(2.0, 3.6))
    elif family == "rounded_rect":
        p = _rounded_rect(a, b, rng.uniform(0.15, 0.5) * min(a, b))
    elif family == "aviator":                      # wide top, narrower bottom, slightly leaning
        p = _superellipse(a, b, rng.uniform(2.2, 2.8))
        ty = p[:, 1] / b
        p[:, 0] = p[:, 0] * (1 - rng.uniform(0.12, 0.28) * ty) + rng.uniform(-0.08, 0.08) * a * ty
        p[:, 1] = np.where(p[:, 1] > 0, p[:, 1] * 1.1, p[:, 1])
    else:                                          # cat-eye: outer upper corner pulled up and out
        p = _superellipse(a, b, rng.uniform(2.1, 2.6))
        q = (p[:, 0] > 0) & (p[:, 1] < 0)
        p[q, 1] -= rng.uniform(0.2, 0.45) * b * (p[q, 0] / a) * (-p[q, 1] / b)
        p[q, 0] *= 1 + rng.uniform(0.0, 0.1) * (-p[q, 1] / b)
        p[:, 1] = np.where(p[:, 1] > 0, p[:, 1] * 0.85, p[:, 1])
    asym = 0.0
    if rng.random() < 0.5:                         # optional asymmetry: height varies along x
        asym = rng.uniform(-0.12, 0.12)
        p[:, 1] *= 1 + asym * p[:, 0] / a
    p = _fit_box(p, w, h)
    if rng.random() < 0.5:
        p[:, 0] = -p[:, 0]
    rot = rng.uniform(-10, 10)
    r = np.radians(rot)
    p = p @ np.array([[np.cos(r), np.sin(r)], [-np.sin(r), np.cos(r)]])
    bw, bh = np.ptp(p[:, 0]), np.ptp(p[:, 1])
    scale = min(1.0, (WIN_W - 2 * MARGIN_MM) / bw, (WIN_H - 2 * MARGIN_MM) / bh)   # 65 mm x 0.95 rotated does not fit 65 mm
    p = (p - (p.min(0) + p.max(0)) / 2) * scale
    bw, bh = bw * scale, bh * scale
    centre = np.array([rng.uniform(MARGIN_MM + bw / 2, WIN_W - MARGIN_MM - bw / 2) if WIN_W - 2 * MARGIN_MM > bw else WIN_W / 2,
                       rng.uniform(MARGIN_MM + bh / 2, WIN_H - MARGIN_MM - bh / 2) if WIN_H - 2 * MARGIN_MM > bh else WIN_H / 2])
    info = {"family": family, "width_mm": float(w * scale), "aspect": float(h / w), "rotation_deg": float(rot), "asymmetry": float(asym)}
    return p + centre, info


def polygon_area(p: np.ndarray) -> float:
    x, y = p[:, 0], p[:, 1]
    return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2)


def rasterize(poly_mm: np.ndarray) -> np.ndarray:
    """Antialiased coverage in [0, 1], H_PX x W_PX."""
    big = np.zeros((H_PX * SS, W_PX * SS), np.uint8)
    cv2.fillPoly(big, [np.round(poly_mm * PX * SS).astype(np.int32)], 255)
    return cv2.resize(big, (W_PX, H_PX), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


# ---------------------------------------------------------------- backgrounds (float32 BGR in 0..1)

def _noise_field(rng: np.random.Generator, octaves=(3, 6, 12, 24, 48)) -> np.ndarray:
    f = np.zeros((H_PX, W_PX), np.float32)
    for i, n in enumerate(octaves):
        f += cv2.resize(rng.random((n, max(2, int(n * W_PX / H_PX))), dtype=np.float32), (W_PX, H_PX), interpolation=cv2.INTER_CUBIC) / (1.6 ** i)
    f -= f.min()
    return f / max(float(f.max()), 1e-6)


def procedural_background(rng: np.random.Generator) -> np.ndarray:
    c0, c1 = rng.uniform(0.05, 1.0, 3).astype(np.float32), rng.uniform(0.05, 1.0, 3).astype(np.float32)
    kind = rng.choice(["gradient", "noise", "stripes", "grid", "backlit"])
    yy, xx = np.mgrid[0:H_PX, 0:W_PX].astype(np.float32)
    if kind == "gradient":
        th = rng.uniform(0, 2 * np.pi)
        t = (xx * np.cos(th) + yy * np.sin(th))
        t = (t - t.min()) / (t.max() - t.min())
        t = t * 0.85 + 0.15 * _noise_field(rng)
    elif kind == "noise":
        t = _noise_field(rng)
    elif kind == "stripes":
        th, period = rng.uniform(0, np.pi), rng.uniform(6, 40)
        t = 0.5 + 0.5 * np.sin(2 * np.pi * (xx * np.cos(th) + yy * np.sin(th)) / period)
        t = t * 0.8 + 0.2 * _noise_field(rng)
    elif kind == "grid":
        p = rng.uniform(15, 60)
        t = (((xx % p) < 2) | ((yy % p) < 2)).astype(np.float32) * 0.9 + 0.1 * _noise_field(rng)
    else:                                          # backlit-like: bright, vignetted
        c0, c1 = np.full(3, rng.uniform(0.8, 1.0), np.float32), np.full(3, rng.uniform(0.55, 0.85), np.float32)
        r = np.hypot(xx - W_PX / 2, yy - H_PX / 2) / np.hypot(W_PX / 2, H_PX / 2)
        t = r ** 2
    return (c0[None, None] * (1 - t[..., None]) + c1[None, None] * t[..., None]).astype(np.float32)


def photo_background(rng: np.random.Generator, path: Path) -> np.ndarray | None:
    img = cv2.imdecode(np.fromfile(str(path), np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    h, w = img.shape[:2]
    ch = int(min(h, w * H_PX / W_PX) * rng.uniform(0.4, 1.0))
    cw = int(ch * W_PX / H_PX)
    if ch < 16 or cw < 16:
        return None
    y0, x0 = int(rng.integers(0, h - ch + 1)), int(rng.integers(0, w - cw + 1))
    crop = cv2.resize(img[y0:y0 + ch, x0:x0 + cw], (W_PX, H_PX), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    if rng.random() < 0.5:
        crop = crop[:, ::-1]
    return np.ascontiguousarray(np.clip(crop * rng.uniform(0.7, 1.2), 0, 1))


# ---------------------------------------------------------------- compositing

def generate_sample(rng: np.random.Generator, bg_files: list[Path] | None = None, family: str | None = None):
    """Returns (image BGR uint8, mask uint8 0/255, info). info['area_mm2'] is the exact area of the generated shape."""
    poly, info = lens_polygon(rng, family)
    alpha = rasterize(poly)
    mask = (alpha >= 0.5).astype(np.uint8) * 255
    info["polygon_mm"] = poly
    info["area_mm2"] = polygon_area(poly)

    bg = photo_background(rng, bg_files[int(rng.integers(len(bg_files)))]) if bg_files and rng.random() < 0.8 else None
    if bg is None:
        bg = procedural_background(rng)

    # thin-lens magnification of the background about the lens centre (m > 1 plus lens, m < 1 minus lens)
    m = rng.uniform(0.93, 1.10)
    cx, cy = poly[:, 0].mean() * PX, poly[:, 1].mean() * PX
    yy, xx = np.mgrid[0:H_PX, 0:W_PX].astype(np.float32)
    inside = cv2.remap(bg, (cx + (xx - cx) / m).astype(np.float32), (cy + (yy - cy) / m).astype(np.float32),
                       cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    inside = inside * (1 - rng.uniform(0, 0.12, 3).astype(np.float32))              # faint tint

    # soft shadow, only outside the lens
    d = rng.uniform(0, 0.35)
    dx, dy = rng.uniform(-2, 2) * PX, rng.uniform(0.3, 2.0) * PX
    sh = cv2.GaussianBlur(cv2.warpAffine(alpha, np.float32([[1, 0, dx], [0, 1, dy]]), (W_PX, H_PX)), (0, 0), rng.uniform(1, 3) * PX)
    bg = bg * (1 - d * sh)[..., None]

    # dark rim (inner band) and Fresnel-like brighter band just inside it
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5) - 0.5
    rim_w = rng.uniform(0.3, 1.5) * PX
    rim = np.clip(rim_w - dist + 0.5, 0, 1) * rng.uniform(0.3, 0.95)
    rim_col = rng.uniform(0.0, 0.2) * np.ones(3, np.float32)
    lens = inside * (1 - rim[..., None]) + rim_col * rim[..., None]
    fw = rng.uniform(0.2, 0.8) * PX
    fres = np.clip(dist - rim_w + 0.5, 0, 1) * np.clip(rim_w + fw - dist, 0, 1) * rng.uniform(0, 0.4)
    lens = lens + fres[..., None] * (1 - lens)

    # 0-3 elliptical highlights
    ys, xs = np.nonzero(mask)
    for _ in range(int(rng.integers(0, 4))):
        k = int(rng.integers(len(xs)))
        layer = np.zeros((H_PX, W_PX), np.float32)
        cv2.ellipse(layer, (int(xs[k]), int(ys[k])), (int(rng.uniform(2, 15) * PX), int(rng.uniform(0.5, 4) * PX)),
                    rng.uniform(0, 180), 0, 360, float(rng.uniform(0.3, 1.0)), -1)
        layer = cv2.GaussianBlur(layer, (0, 0), rng.uniform(1, 4))
        lens = lens + layer[..., None] * (1 - lens)

    img = bg * (1 - alpha[..., None]) + lens * alpha[..., None]
    sigma = rng.uniform(0, 1.2)
    if sigma > 0.1:
        img = cv2.GaussianBlur(img, (0, 0), sigma)
    img = np.clip(img + rng.normal(0, rng.uniform(0, 0.025), img.shape).astype(np.float32), 0, 1)
    ok, buf = cv2.imencode(".jpg", (img * 255 + 0.5).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, int(rng.integers(60, 96))])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR), mask, info


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="default training/_local/synth (git-ignored)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--bg-dir", type=Path, help="folder of background images (team-supplied, CC0 or own)")
    a = ap.parse_args(argv)
    rng = np.random.default_rng(a.seed)
    bgs = sorted(p for p in a.bg_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")) if a.bg_dir else None
    (a.out / "images").mkdir(parents=True, exist_ok=True)
    (a.out / "masks").mkdir(parents=True, exist_ok=True)
    with open(a.out / "index.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["file", "lensId", "pos", "cond", "source"])
        for i in range(a.n):
            img, mask, _ = generate_sample(rng, bgs)
            lens = f"synth{i:06d}"
            stem = f"{lens}_0_synth"
            for path, arr in ((a.out / "images" / (stem + ".jpg"), img), (a.out / "masks" / (stem + ".png"), mask)):
                ok, buf = cv2.imencode(path.suffix, arr)
                buf.tofile(str(path))
            wr.writerow([stem + ".jpg", lens, "0", "synth", "synth"])
    print(f"{a.n} synthetic samples in {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
