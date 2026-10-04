import csv

import numpy as np
import pytest

import build_dataset
import make_bench
import synth
import synth_rig


@pytest.mark.parametrize("scene", list(synth_rig.SCENES))
def test_every_scene_gives_an_exact_mask(scene):
    rng = np.random.default_rng(11)
    for _ in range(3):
        img, mask, info = synth_rig.generate_rig_sample(rng, scene)
        assert img.shape == (650, 800, 3) and img.dtype == np.uint8
        assert mask.shape == (650, 800) and set(np.unique(mask)) <= {0, 255}
        if scene == "empty":
            assert not mask.any()
            continue
        mask_mm2 = (mask > 0).sum() / synth.PX ** 2
        assert abs(mask_mm2 - info["area_mm2"]) / info["area_mm2"] < 0.01
        # the label never reaches the window border (the app refuses such a mask: LENS_OUT_OF_WINDOW)
        assert not (mask[0].any() or mask[-1].any() or mask[:, 0].any() or mask[:, -1].any())


def test_same_seed_same_sample():
    a = synth_rig.generate_rig_sample(np.random.default_rng([3, 7]))
    b = synth_rig.generate_rig_sample(np.random.default_rng([3, 7]))
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])


def test_cli_build_and_bench(tmp_path):
    for name, seed in (("tr", 0), ("va", 1)):
        synth_rig.main(["--n", "4", "--seed", str(seed), "--out", str(tmp_path / name)])
    rows = list(csv.DictReader(open(tmp_path / "tr" / "index.csv")))
    assert len(rows) == 4 and all(r["source"] == "synth" for r in rows)
    for r in rows:
        if r["cond"] != "empty":
            assert 20 < float(r["A_mm"]) <= 76 and 15 < float(r["B_mm"]) <= 61
    counts = build_dataset.build({"train": [tmp_path / "tr"], "val": [tmp_path / "va"], "test": []}, tmp_path / "ds")
    assert counts == {"train": 4, "val": 4, "test": 0}
    split = list(csv.DictReader(open(tmp_path / "ds" / "split.csv")))
    assert {r["split"] for r in split} == {"train", "val"}
    assert all((tmp_path / "ds" / "images" / r["file"]).exists() for r in split)
    make_bench.main([str(tmp_path / "va"), "--out", str(tmp_path / "bench")])
    truth = list(csv.DictReader(open(tmp_path / "bench" / "truth.csv")))
    assert len(truth) == 4 and all((tmp_path / "bench" / t["file"]).exists() for t in truth)


def test_build_refuses_a_lens_in_two_splits(tmp_path):
    synth_rig.main(["--n", "2", "--seed", "5", "--out", str(tmp_path / "a")])
    with pytest.raises(SystemExit):
        build_dataset.build({"train": [tmp_path / "a"], "val": [tmp_path / "a"]}, tmp_path / "ds")
