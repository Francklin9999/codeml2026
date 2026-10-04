"""Copy a training folder at the model resolution (384x320), images as lossless PNG.

train.py resizes every 800x650 image to 384x320 (common.resize_pair: bilinear for the image, box filter then
0.5 threshold for the mask) before anything else, on every epoch. Doing it once, with the same function,
gives the same training input and a data loader that decodes 4x fewer pixels and no JPEG. resize_pair
leaves an image that is already 384x320 unchanged, so train.py reads this folder as it is.
evaluate.py measures A and B in mm from the image size: run it on the full-resolution folder, not on this one.

Usage:  python preresize.py ../_local/ds_synth_v1 --out ../_local/ds_synth_v1_384 [--workers 12]
"""
from __future__ import annotations

import argparse
import csv
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
import common  # noqa: E402


def _one(args: tuple[str, str, str]) -> None:
    src, out, file = args
    cv2.setNumThreads(1)
    stem = Path(file).stem
    img = cv2.imdecode(np.fromfile(str(Path(src) / "images" / file), np.uint8), cv2.IMREAD_COLOR)
    mask = cv2.imread(str(Path(src) / "masks" / (stem + ".png")), cv2.IMREAD_GRAYSCALE)
    img, m = common.resize_pair(img, (mask > 127).astype(np.uint8))
    for path, arr in ((Path(out) / "images" / (stem + ".png"), img), (Path(out) / "masks" / (stem + ".png"), m * 255)):
        ok, buf = cv2.imencode(".png", arr)
        buf.tofile(str(path))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)
    (a.out / "images").mkdir(parents=True, exist_ok=True)
    (a.out / "masks").mkdir(parents=True, exist_ok=True)
    with open(a.folder / "index.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    jobs = [(str(a.folder), str(a.out), r["file"]) for r in rows]
    with ProcessPoolExecutor(a.workers) as ex:
        list(ex.map(_one, jobs, chunksize=32))
    for name in ("index.csv", "split.csv"):
        if not (a.folder / name).exists():
            continue
        with open(a.folder / name, newline="", encoding="utf-8") as f:
            table = list(csv.DictReader(f))
        if not table:
            continue
        for r in table:
            if "file" in r:
                r["file"] = Path(r["file"]).stem + ".png"
        with open(a.out / name, "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=list(table[0]))
            wr.writeheader()
            wr.writerows(table)
    print(f"{len(rows)} pairs at {common.INPUT_W}x{common.INPUT_H} in {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
