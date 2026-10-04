import csv

import split


def rows(n_real=15, per=6, n_synth=20):
    r = [{"file": f"L{i}_{p}_easy.jpg", "lensId": f"L{i:02d}", "pos": str(p), "cond": "easy", "source": "real"}
         for i in range(n_real) for p in range(per)]
    r += [{"file": f"s{i}_0_synth.jpg", "lensId": f"synth{i:06d}", "pos": "0", "cond": "synth", "source": "synth"} for i in range(n_synth)]
    return r


def test_no_lens_in_two_splits_and_synth_only_in_train():
    out = split.split_rows(rows(), seed=3)
    by_lens = {}
    for r in out:
        by_lens.setdefault(r["lensId"], set()).add(r["split"])
    assert all(len(s) == 1 for s in by_lens.values())
    assert {r["split"] for r in out if r["source"] == "synth"} == {"train"}
    real = {s: {r["lensId"] for r in out if r["source"] == "real" and r["split"] == s} for s in ("train", "val", "test")}
    assert len(real["val"]) == 2 and len(real["test"]) == 2 and len(real["train"]) == 11
    assert not (real["train"] & real["val"] or real["train"] & real["test"] or real["val"] & real["test"])


def test_cli(tmp_path):
    for name, rs in (("real", rows(5, 2, 0)), ("synth", rows(0, 0, 4))):
        d = tmp_path / name
        (d / "images").mkdir(parents=True)
        with open(d / "index.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["file", "lensId", "pos", "cond", "source"])
            w.writeheader()
            w.writerows(rs)
    split.main([str(tmp_path / "real" / "index.csv"), str(tmp_path / "synth" / "index.csv"), "--out", str(tmp_path / "split.csv")])
    out = list(csv.DictReader(open(tmp_path / "split.csv")))
    assert len(out) == 14 and out[0]["file"].startswith("real/images/")
    seen = {}
    for r in out:
        assert seen.setdefault(r["lensId"], r["split"]) == r["split"]
