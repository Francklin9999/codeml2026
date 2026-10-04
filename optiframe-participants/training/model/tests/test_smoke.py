"""End-to-end smoke test on CPU: 16 synthetic samples, 2 epochs, ONNX export with parity check, evaluation.

The model trained here is a toy: everything is written to pytest's tmp dir, never under app/.
"""
import csv
import json

import cv2
import numpy as np
import pytest

import common
import evaluate
import export
import train

W, H = 800, 650


def make_dataset(root, seed=0):
    """16 samples: 8 'real' (4 lenses x 2 shots), 8 'synth'. Ellipses and rectangles with noise, exact masks."""
    rng = np.random.default_rng(seed)
    (root / "images").mkdir(parents=True)
    (root / "masks").mkdir()
    index, split = [], []
    plan = [(f"L{i}", p, "easy" if p == 0 else "lamp", "real", ["train", "train", "val", "test"][i]) for i in range(4) for p in range(2)]
    plan += [(f"S{i}", 0, "synth", "synth", "train") for i in range(8)]
    for k, (lens, pos, cond, source, sp) in enumerate(plan):
        mask = np.zeros((H, W), np.uint8)
        cx, cy = rng.integers(300, 500), rng.integers(250, 400)
        ax, ay = rng.integers(120, 220), rng.integers(100, 170)
        if k % 2:
            cv2.rectangle(mask, (cx - ax, cy - ay), (cx + ax, cy + ay), 255, -1)
        else:
            cv2.ellipse(mask, (int(cx), int(cy)), (int(ax), int(ay)), 0, 0, 360, 255, -1)
        bg = rng.uniform(150, 230)
        img = np.full((H, W, 3), bg, np.float32)
        img[mask > 0] = bg - rng.uniform(50, 90)
        img += rng.normal(0, 8, img.shape)
        name = f"{lens}_{pos}_{cond}"
        cv2.imwrite(str(root / "images" / (name + ".jpg")), np.clip(img, 0, 255).astype(np.uint8))
        cv2.imwrite(str(root / "masks" / (name + ".png")), mask)
        index.append({"file": name + ".jpg", "lensId": lens, "pos": pos, "cond": cond, "source": source})
        split.append({"lensId": lens, "split": sp})
    for fname, rows in (("index.csv", index), ("split.csv", {r["lensId"]: r for r in split}.values())):
        rows = list(rows)
        with open(root / fname, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)


def test_train_export_evaluate(tmp_path):
    data, out = tmp_path / "data", tmp_path / "out"
    make_dataset(data)
    assert len(list((data / "images").glob("*.jpg"))) == 16

    summary = train.main(["--data", str(data), "--out", str(out), "--sources", "both", "--epochs", "2", "--batch", "4",
                          "--encoder-weights", "none", "--workers", "0", "--device", "cpu"])
    assert summary["n_train"] == 12 and len(summary["log"]) == 2
    assert (out / "best.pt").exists()

    report = export.main(["--ckpt", str(out / "best.pt"), "--out", str(out)])
    assert report["fp32_max_abs_diff_vs_torch"] < 1e-3
    assert (out / "lens_seg.onnx").stat().st_size > 0 and (out / "lens_seg.int8.onnx").stat().st_size > 0

    result = evaluate.main(["--data", str(data), "--ckpt", str(out / "best.pt"), "--out", str(out)])
    assert (out / "metrics.md").exists() and (out / "metrics.json").exists()
    assert json.loads((out / "metrics.json").read_text())["n_images"] == 2
    assert set(result["overall"]) == {"model", "otsu"}
    assert set(result["per_condition"]["otsu"]) == {"easy", "lamp"}
    # the Otsu baseline must be sane on this trivial data, which also checks the metric code end to end
    assert result["overall"]["otsu"]["iou"] > 0.9

    # the ONNX file is evaluable too
    evaluate.main(["--data", str(data), "--onnx", str(out / "lens_seg.onnx"), "--out", str(out)])


def test_training_is_reproducible(tmp_path):
    make_dataset(tmp_path / "d")
    losses = []
    for k in range(2):
        summary = train.main(["--data", str(tmp_path / "d"), "--out", str(tmp_path / f"o{k}"), "--epochs", "1", "--batch", "4",
                              "--encoder-weights", "none", "--workers", "0", "--device", "cpu", "--seed", "0"])
        losses.append(summary["log"][0]["train_loss"])
    assert losses[0] == losses[1]


@pytest.mark.parametrize("sources,expected", [("real", 4), ("synth", 8), ("both", 12)])
def test_sources_switch(tmp_path, sources, expected):
    make_dataset(tmp_path / "d")
    assert len(common.load_samples(tmp_path / "d", "train", sources)) == expected
    assert all(s["source"] == "synth" for s in common.load_samples(tmp_path / "d", "train", "synth"))


def test_nothing_written_under_app(tmp_path):
    with pytest.raises(SystemExit):
        common.refuse_app_dir(common.PROJECT_ROOT / "app" / "public" / "models")
    assert common.refuse_app_dir(tmp_path) == tmp_path.resolve()
    with pytest.raises(SystemExit):
        export.main(["--out", str(common.PROJECT_ROOT / "app" / "public")])
