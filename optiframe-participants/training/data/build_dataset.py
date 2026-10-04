"""Assemble one training folder from several generated or labelled folders, with an explicit split.

train.py, evaluate.py and export.py read a single folder (images/, masks/, index.csv, split.csv). split.py
splits real photos by lens id and sends every synthetic sample to train; with no real photos yet, the
validation and test sets have to be synthetic too, drawn with their own seeds. This script does that:
every folder is given its split on the command line, files are hard-linked (copied if the file system
refuses), and lens ids must be unique across folders.

Usage:  python build_dataset.py --train ../_local/rig_train ../_local/generic_train --val ../_local/rig_val
                                --test ../_local/rig_test --out ../_local/ds_synth_v1
Once real photos exist, give the real folders to split.py instead and keep this for the synthetic part.
"""
from __future__ import annotations

import argparse
import csv
import os
import shutil
import sys
from pathlib import Path


def _link(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def build(groups: dict[str, list[Path]], out: Path) -> dict[str, int]:
    (out / "images").mkdir(parents=True, exist_ok=True)
    (out / "masks").mkdir(parents=True, exist_ok=True)
    rows, seen = [], {}
    for split, folders in groups.items():
        for folder in folders:
            with open(folder / "index.csv", newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    if seen.setdefault(r["lensId"], split) != split:
                        raise SystemExit(f"lens id {r['lensId']} is in two splits")
                    stem = Path(r["file"]).stem
                    _link(folder / "images" / r["file"], out / "images" / r["file"])
                    _link(folder / "masks" / (stem + ".png"), out / "masks" / (stem + ".png"))
                    rows.append({**r, "split": split})
    fields = ["file", "lensId", "pos", "cond", "source"]
    extra = [k for k in ("A_mm", "B_mm") if any(k in r for r in rows)]
    with open(out / "index.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=fields + extra, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)
    with open(out / "split.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=["file", "lensId", "split"], extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)
    return {s: sum(r["split"] == s for r in rows) for s in groups}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--train", nargs="+", type=Path, required=True)
    ap.add_argument("--val", nargs="+", type=Path, required=True)
    ap.add_argument("--test", nargs="*", type=Path, default=[])
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    counts = build({"train": a.train, "val": a.val, "test": a.test}, a.out)
    print(f"{sum(counts.values())} samples in {a.out}: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
