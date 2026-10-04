import numpy as np

import common


def disc(r, cx=60, cy=50, shape=(100, 120)):
    yy, xx = np.mgrid[: shape[0], : shape[1]]
    return ((xx - cx) ** 2 + (yy - cy) ** 2 <= r * r).astype(np.uint8)


def test_iou():
    a = disc(20)
    assert common.iou(a, a) == 1.0
    assert common.iou(a, np.zeros_like(a)) == 0.0
    assert common.iou(np.zeros_like(a), np.zeros_like(a)) == 1.0


def test_boundary_f_tolerance():
    gt = disc(30)
    assert common.boundary_f(gt, gt, 2.0) == 1.0
    assert common.boundary_f(disc(31), gt, 2.0) == 1.0   # 1 px off, inside tolerance
    assert common.boundary_f(disc(38), gt, 2.0) < 0.1    # 8 px off, outside
    assert common.boundary_f(np.zeros_like(gt), gt, 2.0) == 0.0


def test_extents_and_largest_component():
    m = disc(20)
    a, b = common.extents_mm(m, 0.5, 0.25)
    assert (a, b) == (41 * 0.5, 41 * 0.25)
    assert common.extents_mm(np.zeros_like(m), 1, 1) is None
    noisy = m.copy()
    noisy[2, 2] = 1
    assert common.largest_component(noisy)[2, 2] == 0


def _bilinear_reference(src, dw, dh):
    """Same algorithm as resizeBilinear in app/src/vision/segmentModel.ts (half-pixel centres, edge clamped)."""
    sh, sw, ch = src.shape
    out = np.zeros((dh, dw, ch), dtype=np.float64)
    for y in range(dh):
        sy = min(max((y + 0.5) * sh / dh - 0.5, 0), sh - 1)
        y0 = int(np.floor(sy)); y1 = min(y0 + 1, sh - 1); wy = sy - y0
        for x in range(dw):
            sx = min(max((x + 0.5) * sw / dw - 0.5, 0), sw - 1)
            x0 = int(np.floor(sx)); x1 = min(x0 + 1, sw - 1); wx = sx - x0
            top = src[y0, x0] * (1 - wx) + src[y0, x1] * wx
            bot = src[y1, x0] * (1 - wx) + src[y1, x1] * wx
            out[y, x] = top * (1 - wy) + bot * wy
    return out


def test_resize_matches_app_bilinear():
    rng = np.random.default_rng(0)
    img = rng.integers(0, 256, (650, 800, 3), dtype=np.uint8)
    got, _ = common.resize_pair(img, None)
    ref = _bilinear_reference(img.astype(np.float64), common.INPUT_W, common.INPUT_H)
    assert got.shape == (common.INPUT_H, common.INPUT_W, 3)
    assert np.abs(got.astype(np.float64) - ref).max() <= 1.0   # uint8 rounding only
    x = common.to_tensor(got)
    assert tuple(x.shape) == (3, common.INPUT_H, common.INPUT_W)
