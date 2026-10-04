#!/usr/bin/env python3
"""Record the measured length of the printed 100 mm ruler.

    python set_print_scale.py 99.0     # sets printScale = 0.99

Writes app/public/board_spec.json and rig/out/board_spec.json.
Rejects a printScale outside 0.97 .. 1.03 (re-print instead of correcting a bad print).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_FILES = [HERE.parent / "app" / "public" / "board_spec.json", HERE / "out" / "board_spec.json"]
NOMINAL_MM = 100.0
MIN_SCALE, MAX_SCALE = 0.97, 1.03


def set_scale(measured_mm: float, files: list[Path]) -> float:
    scale = round(measured_mm / NOMINAL_MM, 6)
    if not (MIN_SCALE <= scale <= MAX_SCALE):
        raise ValueError(f"printScale {scale} is outside {MIN_SCALE}..{MAX_SCALE}: "
                         "check the print dialog (100 %, no 'fit to page') and print again")
    missing = [str(f) for f in files if not f.is_file()]
    if missing:
        raise FileNotFoundError("run make_board.py first, missing: " + ", ".join(missing))
    for f in files:
        text = f.read_text(encoding="utf-8")
        json.loads(text)
        # in-place edit keeps the file layout (one marker per line) untouched
        text, n = re.subn(r'("printScale"\s*:\s*)[-+0-9.eE]+', lambda m: m.group(1) + repr(scale), text)
        if n != 1:
            raise ValueError(f"{f}: no single printScale field")
        f.write_text(text, encoding="utf-8")
    return scale


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("measured_ruler_mm", type=float, help="length of the printed ruler, in mm")
    ap.add_argument("--files", nargs="+", type=Path, default=DEFAULT_FILES, help="spec files to update")
    args = ap.parse_args(argv)
    try:
        scale = set_scale(args.measured_ruler_mm, args.files)
    except (ValueError, FileNotFoundError) as e:
        print("error:", e, file=sys.stderr)
        return 1
    print(f"printScale = {scale}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
