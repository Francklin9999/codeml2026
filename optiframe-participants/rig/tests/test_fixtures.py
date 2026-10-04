"""Re-detect the markers in each fixture, fit a homography from board_spec.json and measure the shape."""
import json

import cv2
import numpy as np
import pytest

PX_PER_MM = 10
TOL_MM = 0.1


def fit_homography(gray, spec):
    params = cv2.aruco.DetectorParameters()
    params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    det = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50), params)
    corners, ids, _ = det.detectMarkers(gray)
    assert ids is not None
    by_id = {m["id"]: m["corners"] for m in spec["markers"]}
    src, dst = [], []
    for c, i in zip(corners, ids.flatten()):
        src += by_id[int(i)]
        dst += c.reshape(4, 2).tolist()
    src, dst = np.float32(src), np.float32(dst)
    _, inl = cv2.findHomography(src, dst, cv2.RANSAC, 3.0)
    keep = inl.ravel() == 1
    h, _ = cv2.findHomography(src[keep], dst[keep], 0)          # least squares on inliers
    return h, len(ids)


def rectify(gray, h, spec):
    w, hh = spec["windowMm"]["w"] * PX_PER_MM, spec["windowMm"]["h"] * PX_PER_MM
    m = h @ np.diag([1 / PX_PER_MM, 1 / PX_PER_MM, 1.0])
    return cv2.warpPerspective(gray, m, (int(w), int(hh)), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP).astype(np.float32)


def crossings(profile, thr):
    """Sub-pixel positions of the first down-crossing and the last up-crossing of thr."""
    below = np.flatnonzero(profile < thr)
    i, j = below[0], below[-1]
    a = (i - 1) + (profile[i - 1] - thr) / (profile[i - 1] - profile[i])
    b = j + (thr - profile[j]) / (profile[j + 1] - profile[j])
    return a, b


def measure(rect, truth):
    thr = (truth["backgroundGrey"] + truth["rimGrey"]) / 2
    m = 40                                                     # ignore the window cut line near the edges
    inner = rect[m:-m, m:-m]
    ys, xs = np.nonzero(inner < thr)
    cy, cx = int(round((ys.min() + ys.max()) / 2)) + m, int(round((xs.min() + xs.max()) / 2)) + m
    row = rect[cy - 1:cy + 2].mean(axis=0)
    col = rect[:, cx - 1:cx + 2].mean(axis=1)
    xa, xb = (v + m for v in crossings(row[m:-m], thr))
    ya, yb = (v + m for v in crossings(col[m:-m], thr))
    return (xb - xa) / PX_PER_MM, (yb - ya) / PX_PER_MM


def test_ten_fixtures_exist(built):
    pngs = sorted((built[0] / "fixtures").glob("*.png"))
    assert len(pngs) == 10 and all(p.with_suffix(".json").exists() for p in pngs)
    names = " ".join(p.name for p in pngs)
    assert "thick" in names and "faint" in names


@pytest.mark.parametrize("idx", range(10))
def test_shape_size_recovered(built, idx):
    spec = json.loads((built[0] / "board_spec.json").read_text())
    png = sorted((built[0] / "fixtures").glob("*.png"))[idx]
    truth = json.loads(png.with_suffix(".json").read_text())
    gray = cv2.cvtColor(cv2.imread(str(png)), cv2.COLOR_BGR2GRAY)
    h, n = fit_homography(gray, spec)
    assert n == len(spec["markers"])
    # fitted homography agrees with the truth used to draw the image
    ht = np.array(truth["H"]).reshape(3, 3)
    p = np.array([[0, 0, 1], [80, 0, 1], [80, 65, 1], [0, 65, 1]], float).T
    a, b = (ht @ p), (h @ p)
    assert np.abs(a[:2] / a[2] - b[:2] / b[2]).max() < 1.0      # pixels

    a_mm, b_mm = measure(rectify(gray, h, spec), truth)
    assert abs(a_mm - truth["widthMm"]) < TOL_MM, (png.name, a_mm, truth["widthMm"])
    assert abs(b_mm - truth["heightMm"]) < TOL_MM, (png.name, b_mm, truth["heightMm"])
