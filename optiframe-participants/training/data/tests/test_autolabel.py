import csv
import json

import cv2
import numpy as np

import autolabel
from render import camera_view, make_spec, render_board, superellipse_mm


def iou(a, b):
    a, b = a > 0, b > 0
    return (a & b).sum() / (a | b).sum()


def build_group(folder, lens="L01", pos="1", shifted=None, conds=("easy", "lamp", "pattern")):
    poly = superellipse_mm(41, 33, 24, 18, 2.6, 7)
    gt = None
    for cond in conds:
        board, gt = render_board(poly, rim_mm=1.0, window="gradient" if cond == "easy" else "stripes")
        shift = (6.0, 4.0) if cond == shifted else (0.0, 0.0)
        photo = camera_view(board, shift=shift, noise=0 if cond == "easy" else 3)
        cv2.imwrite(str(folder / f"{lens}_{pos}_{cond}.jpg"), photo, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return gt


def test_reproduces_mask(tmp_path):
    photos, out = tmp_path / "photos", tmp_path / "out"
    photos.mkdir()
    gt = build_group(photos)
    res = autolabel.run(photos, make_spec(), out)
    assert res["accepted"] == 3 and res["groups_rejected"] == 0
    rows = list(csv.DictReader(open(out / "index.csv")))
    assert {r["cond"] for r in rows} == {"easy", "lamp", "pattern"} and all(r["source"] == "real" for r in rows)
    for r in rows:
        m = cv2.imread(str(out / "masks" / r["file"].replace(".jpg", ".png")), cv2.IMREAD_GRAYSCALE)
        im = cv2.imread(str(out / "images" / r["file"]))
        assert m.shape == (650, 800) and im.shape == (650, 800, 3)
        assert iou(m, gt) >= 0.97, (r["file"], iou(m, gt))


def test_rejects_group_with_shifted_photo(tmp_path):
    photos, out = tmp_path / "photos", tmp_path / "out"
    photos.mkdir()
    build_group(photos, lens="L01", pos="1", shifted="lamp")
    build_group(photos, lens="L02", pos="1")
    res = autolabel.run(photos, make_spec(), out)
    rows = list(csv.DictReader(open(out / "index.csv")))
    assert {r["lensId"] for r in rows} == {"L02"} and len(rows) == 3
    assert res["groups_rejected"] == 1 and "stand moved" in res["rejected"][0][2]


def test_small_drift_is_accepted(tmp_path):
    photos, out = tmp_path / "photos", tmp_path / "out"
    photos.mkdir()
    poly = superellipse_mm(41, 33, 24, 18)
    for cond, sh in (("easy", 0.0), ("lamp", 1.0)):
        board, _ = render_board(poly)
        cv2.imwrite(str(photos / f"L01_1_{cond}.jpg"), camera_view(board, shift=(sh, 0)), [cv2.IMWRITE_JPEG_QUALITY, 92])
    assert autolabel.run(photos, make_spec(), out)["accepted"] == 2


def test_qc_overlays(tmp_path):
    photos, out, spec = tmp_path / "photos", tmp_path / "out", tmp_path / "spec.json"
    photos.mkdir()
    build_group(photos)
    spec.write_text(json.dumps(make_spec()))
    assert autolabel.main([str(photos), "--spec", str(spec), "--out", str(out), "--qc", "2"]) == 0
    qc = sorted((out / "qc").glob("*.jpg"))
    assert len(qc) == 2 and all("easy" not in p.name for p in qc)
    assert cv2.imread(str(qc[0])).shape == (650, 800, 3)


def test_group_without_easy_shot_is_rejected(tmp_path):
    photos = tmp_path / "photos"
    photos.mkdir()
    build_group(photos, conds=("lamp",))
    res = autolabel.run(photos, make_spec(), tmp_path / "out")
    assert res["accepted"] == 0 and res["groups_rejected"] == 1


def test_print_scale_is_applied_like_the_app(tmp_path):
    """A sheet declared at 97 % has its markers closer together: the same photo then shows a larger lens in mm."""
    photos = tmp_path / "photos"
    photos.mkdir()
    build_group(photos, conds=("easy",))
    areas = []
    for scale in (1.0, 0.97):
        out = tmp_path / f"out{scale}"
        spec = dict(make_spec(), printScale=scale)
        assert autolabel.run(photos, spec, out)["accepted"] == 1
        m = cv2.imread(str(out / "masks" / "L01_1_easy.png"), cv2.IMREAD_GRAYSCALE)
        areas.append((m > 0).sum())
    assert abs(areas[1] / areas[0] - 0.97**2) < 0.01, areas


def test_validation_and_heic_files_are_listed_not_grouped(tmp_path):
    photos, out = tmp_path / "photos", tmp_path / "out"
    photos.mkdir()
    build_group(photos)
    (photos / "L01_Pixel-7_2.jpg").write_bytes((photos / "L01_1_easy.jpg").read_bytes())   # validation name
    (photos / "L01_1_lamp.heic").write_bytes(b"x")
    res = autolabel.run(photos, make_spec(), out)
    assert res["accepted"] == 3 and res["groups_rejected"] == 0
    reasons = {r[0]: r[2] for r in res["rejected"]}
    assert "name does not match" in reasons["L01_Pixel-7_2.jpg"]
    assert "not readable" in reasons["L01_1_lamp.heic"]
