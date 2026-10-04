import csv

import numpy as np
import pytest

import synth


@pytest.mark.parametrize("family", synth.FAMILIES)
def test_size_and_area(family):
    rng = np.random.default_rng(7)
    for _ in range(5):
        img, mask, info = synth.generate_sample(rng, family=family)
        assert img.shape == (650, 800, 3) and img.dtype == np.uint8
        assert mask.shape == (650, 800) and set(np.unique(mask)) <= {0, 255}
        mask_mm2 = (mask > 0).sum() / synth.PX ** 2
        assert abs(mask_mm2 - info["area_mm2"]) / info["area_mm2"] < 0.01
        poly = info["polygon_mm"]
        assert poly[:, 0].min() >= 0 and poly[:, 0].max() <= 80 and poly[:, 1].min() >= 0 and poly[:, 1].max() <= 65


def test_shape_ranges():
    rng = np.random.default_rng(1)
    for _ in range(40):
        poly, info = synth.lens_polygon(rng)
        assert 0 < info["width_mm"] <= 65 and abs(info["rotation_deg"]) <= 10
        assert np.ptp(poly[:, 0]) <= 76 + 1e-6 and np.ptp(poly[:, 1]) <= 61 + 1e-6


def test_cli_writes_dataset(tmp_path):
    synth.main(["--n", "3", "--out", str(tmp_path), "--seed", "2"])
    rows = list(csv.DictReader(open(tmp_path / "index.csv")))
    assert len(rows) == 3 and all(r["source"] == "synth" for r in rows)
    for r in rows:
        assert (tmp_path / "images" / r["file"]).exists()
        assert (tmp_path / "masks" / r["file"].replace(".jpg", ".png")).exists()


def test_photo_background(tmp_path):
    import cv2
    cv2.imwrite(str(tmp_path / "bg.jpg"), np.random.default_rng(0).integers(0, 255, (900, 1200, 3), dtype=np.uint8))
    img, mask, _ = synth.generate_sample(np.random.default_rng(3), [tmp_path / "bg.jpg"])
    assert img.shape == (650, 800, 3) and mask.any()
