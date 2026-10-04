"""Split a dataset by lens id (train / val / test, about 70/15/15). Synthetic samples go to train only.

Usage:  python split.py REAL/index.csv [SYNTH/index.csv ...] [--out split.csv] [--seed 0]
split.csv columns: file, lensId, pos, cond, source, split. `file` is relative to the common parent
of the index folders (e.g. real/images/L01_3_easy.jpg), so two datasets never collide.
"""
from __future__ import annotations

import argparse
import csv
import os
import random
import sys
from pathlib import Path


def assign_lenses(lens_ids: list[str], seed: int = 0, val: float = 0.15, test: float = 0.15) -> dict[str, str]:
    ids = sorted(set(lens_ids))
    random.Random(seed).shuffle(ids)
    n = len(ids)
    n_val = max(1, round(val * n)) if n >= 3 else 0
    n_test = max(1, round(test * n)) if n >= 3 else 0
    out = {}
    for i, lens in enumerate(ids):
        out[lens] = "test" if i < n_test else "val" if i < n_test + n_val else "train"
    return out


def split_rows(rows: list[dict], seed: int = 0) -> list[dict]:
    """rows need lensId and source. Raises ValueError if a lens id would land in two splits."""
    real = assign_lenses([r["lensId"] for r in rows if r["source"] != "synth"], seed)
    out = []
    for r in rows:
        out.append({**r, "split": "train" if r["source"] == "synth" else real[r["lensId"]]})
    seen: dict[str, str] = {}
    for r in out:
        if seen.setdefault(r["lensId"], r["split"]) != r["split"]:
            raise ValueError(f"lens id {r['lensId']} appears in two splits")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("index", nargs="+", type=Path, help="index.csv files from autolabel.py and synth.py")
    ap.add_argument("--out", type=Path, default=Path("split.csv"))
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)
    dirs = [p.resolve().parent for p in a.index]
    root = Path(os.path.commonpath(dirs)) if len(dirs) > 1 else dirs[0]
    rows = []
    for p, d in zip(a.index, dirs):
        with open(p, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                r["file"] = (d / "images" / r["file"]).relative_to(root).as_posix()
                rows.append(r)
    res = split_rows(rows, a.seed)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=["file", "lensId", "pos", "cond", "source", "split"])
        wr.writeheader()
        wr.writerows({k: r[k] for k in wr.fieldnames} for r in res)
    counts = {s: sum(r["split"] == s for r in res) for s in ("train", "val", "test")}
    print(f"{len(res)} images: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
