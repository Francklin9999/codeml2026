"""Turn a labelled folder into the input of the app-side benchmark (app/bench/seg_bench.test.ts).

The benchmark runs in Node, which reads PNG only (pngjs): each image is decoded once and written as a
lossless PNG, so the app sees exactly the pixels the model is evaluated on in Python. truth.csv carries
the exact A and B (synth_rig.py writes them) or, for folders without them, the extents of the label mask.

Usage:  python make_bench.py ../_local/rig_test --out ../_local/bench_rig_test [--limit 500]
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import cv2
import numpy as np

PX_PER_MM = 10


def mask_extents_mm(mask: np.ndarray) -> tuple[str, str]:
    ys, xs = np.nonzero(mask > 127)
    if xs.size == 0:
        return "", ""
    return f"{(xs.max() - xs.min() + 1) / PX_PER_MM:.4f}", f"{(ys.max() - ys.min() + 1) / PX_PER_MM:.4f}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path, help="images/, masks/, index.csv")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    with open(a.folder / "index.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if a.limit:
        rows = rows[: a.limit]
    with open(a.out / "truth.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["file", "scene", "A_mm", "B_mm"])
        for r in rows:
            img = cv2.imdecode(np.fromfile(str(a.folder / "images" / r["file"]), np.uint8), cv2.IMREAD_COLOR)
            stem = Path(r["file"]).stem
            if r.get("A_mm") is not None:
                A, B = r["A_mm"], r["B_mm"]
            else:
                A, B = mask_extents_mm(cv2.imread(str(a.folder / "masks" / (stem + ".png")), cv2.IMREAD_GRAYSCALE))
            ok, buf = cv2.imencode(".png", cv2.cvtColor(img, cv2.COLOR_BGR2BGRA))
            buf.tofile(str(a.out / (stem + ".png")))
            wr.writerow([stem + ".png", r["cond"], A, B])
    print(f"{len(rows)} images in {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
