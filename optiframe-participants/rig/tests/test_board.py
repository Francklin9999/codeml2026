import json
import re

import cv2
import numpy as np
import pytest
from pypdf import PdfReader

import make_board as mb

MM = 72 / 25.4


def spec_of(built):
    return json.loads((built[0] / "board_spec.json").read_text(encoding="utf-8"))


def ops(page):
    """(re-rects, line segments) in mm from the page content stream; the PDF is drawn without cm."""
    data = page.get_contents().get_data().decode("latin-1")
    num = r"(-?\d+\.?\d*)"
    rects = [tuple(float(v) / MM for v in m) for m in re.findall(
        rf"{num} {num} {num} {num} re", data)]
    segs = [tuple(float(v) / MM for v in m) for m in re.findall(
        rf"{num} {num} m {num} {num} l", data)]
    return rects, segs


@pytest.mark.parametrize("name,size", [("A4", (297.0, 210.0)), ("Letter", (279.4, 215.9))])
def test_page_size(built, name, size):
    page = PdfReader(str(built[0] / f"board_{name}.pdf")).pages[0]
    assert float(page.mediabox.width) / MM == pytest.approx(size[0], abs=0.02)
    assert float(page.mediabox.height) / MM == pytest.approx(size[1], abs=0.02)


@pytest.mark.parametrize("name", ["A4", "Letter"])
def test_window_ruler_and_guide_from_json(built, name):
    spec = spec_of(built)
    page = PdfReader(str(built[0] / f"board_{name}.pdf")).pages[0]
    rects, segs = ops(page)
    w, h = spec["windowMm"]["w"], spec["windowMm"]["h"]

    window = [r for r in rects if abs(r[2] - w) < 0.02 and abs(r[3] - h) < 0.02]
    assert len(window) == 1
    wx, wy_bottom = window[0][0], window[0][1]          # PDF y axis points up
    page_h = float(page.mediabox.height) / MM
    wy_top = page_h - (wy_bottom + h)                   # distance of the window top from the page top

    # ruler: one horizontal segment of rulerMm, 11 ticks every 10 mm
    horiz = [s for s in segs if abs(s[1] - s[3]) < 1e-3]
    ruler = [s for s in horiz if abs(abs(s[2] - s[0]) - spec["rulerMm"]) < 0.02]
    assert len(ruler) == 1
    rx0, ry = min(ruler[0][0], ruler[0][2]), ruler[0][1]
    ticks = sorted(s[0] for s in segs if abs(s[0] - s[2]) < 1e-3 and abs(s[1] - ry) < 1e-3)
    assert len(ticks) == 11
    assert np.diff(ticks) == pytest.approx(10.0, abs=0.02)
    assert ticks[0] == pytest.approx(rx0, abs=0.02)

    # guide ticks: on the window centre line, outside the window, none inside
    gy = page_h - (wy_top + spec["guideLineYMm"])
    guide = [s for s in horiz if abs(s[1] - gy) < 0.02 and abs(s[2] - s[0]) < 10]
    assert len(guide) == 2
    for s in guide:
        xs = sorted((s[0], s[2]))
        assert xs[1] <= wx + 1e-3 or xs[0] >= wx + w - 1e-3

    # printed content (every drawn element) fits in 180 x 150 mm
    xs = [r[0] for r in rects] + [r[0] + r[2] for r in rects] + [s[i] for s in segs for i in (0, 2)]
    ys = [r[1] for r in rects] + [r[1] + r[3] for r in rects] + [s[i] for s in segs for i in (1, 3)]
    assert max(xs) - min(xs) <= 180.0 and max(ys) - min(ys) <= 150.0


def test_labels_in_pdf_text(built):
    text = PdfReader(str(built[0] / "board_A4.pdf")).pages[0].extract_text()
    for needle in ["HAUT", "IL DROIT", "IL GAUCHE", "nez de ce c", "Imprimer", "100 mm", mb.VERSION]:
        assert needle in text


def test_spec_matches_contract_and_brief(built):
    spec = spec_of(built)
    assert spec["dictionary"] == "DICT_4X4_50" and spec["markerMm"] == 15
    assert spec["windowMm"] == {"w": 80, "h": 65} and spec["rulerMm"] == 100
    assert spec["guideLineYMm"] == 32.5 and spec["printScale"] == 1
    assert set(spec) == {"dictionary", "markerMm", "markers", "windowMm", "guideLineYMm", "rulerMm", "printScale"}
    markers = spec["markers"]
    assert len(markers) >= 12 and len({m["id"] for m in markers}) == len(markers)
    assert (built[1]).read_text(encoding="utf-8") == (built[0] / "board_spec.json").read_text(encoding="utf-8")
    w, h = 80, 65
    for m in markers:
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = m["corners"]
        assert (x1 - x0, y1 - y0) == (15, 0) and (x3 - x0, y3 - y0) == (0, 15)   # TL, TR, BR, BL
        # axis-aligned distance from the window rectangle
        dx = max(-x1 if x1 < 0 else 0, x0 - w if x0 > w else 0)
        dy = max(-y2 if y2 < 0 else 0, y0 - h if y0 > h else 0)
        assert max(dx, dy) >= 4 - 1e-9
        assert 0 <= max(dx, dy)
    cs = np.array([c for m in markers for c in m["corners"]])
    assert cs.min() < 0                                  # ring has negative coordinates
    assert np.ptp(cs[:, 0]) <= 180 and np.ptp(cs[:, 1]) <= 150


def test_marker_ids_decode_from_raster():
    """The vector pattern and the raster agree with cv2.aruco on every marker."""
    ink = mb.render_board_ink(20)
    gray = (255 - 200 * ink).astype(np.uint8)
    det = cv2.aruco.ArucoDetector(mb.aruco_dictionary(), cv2.aruco.DetectorParameters())
    corners, ids, _ = det.detectMarkers(gray)
    assert sorted(ids.flatten().tolist()) == [m["id"] for m in mb.build_spec()["markers"]]
