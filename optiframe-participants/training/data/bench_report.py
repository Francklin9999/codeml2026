"""Summarise app/bench/seg_bench.test.ts output (bench_results.csv) per scene and per path.

For each of classic, model and pipeline (= what the app would do): share of images measured, share refused
with each error code, mean absolute error of A and B over the measured images, share within 0.5 and 1 mm
(the grid's full-marks threshold is a mean error of 1 mm). "empty" images have no lens: there, a refusal
is the right answer and a measurement is a false detection.

Usage:  python bench_report.py ../_local/bench_rig_test/bench_results.csv [--md out.md]
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path


def _f(v: str) -> float | None:
    return float(v) if v not in ("", None) else None


def summarise(rows: list[dict], path: str) -> dict:
    n = len(rows)
    codes = Counter(r[f"{path}_code"] for r in rows)
    lens = [r for r in rows if r["scene"] != "empty"]
    ok = [r for r in lens if r[f"{path}_code"] == "OK"]
    errs = []
    for r in ok:
        errs.append(max(abs(_f(r[f"{path}_A"]) - _f(r["A_true"])), abs(_f(r[f"{path}_B"]) - _f(r["B_true"]))))
    ab = [abs(_f(r[f"{path}_A"]) - _f(r["A_true"])) for r in ok] + [abs(_f(r[f"{path}_B"]) - _f(r["B_true"])) for r in ok]
    empty = [r for r in rows if r["scene"] == "empty"]
    return {
        "n": n,
        "measured": len(ok) / len(lens) if lens else None,
        "mae_ab": sum(ab) / len(ab) if ab else None,
        "within_0_5": sum(e <= 0.5 for e in errs) / len(lens) if lens else None,
        "within_1": sum(e <= 1.0 for e in errs) / len(lens) if lens else None,
        "false_detection": sum(r[f"{path}_code"] == "OK" for r in empty) / len(empty) if empty else None,
        "codes": dict(codes),
    }


def fmt(v, pct=False) -> str:
    if v is None:
        return "-"
    return f"{100 * v:.0f} %" if pct else f"{v:.2f}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results", type=Path)
    ap.add_argument("--md", type=Path)
    a = ap.parse_args(argv)
    with open(a.results, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    has_model = any(r["model_code"] not in ("NONE", "") for r in rows)
    paths = ["classic", "model", "pipe"] if has_model else ["classic"]
    by_scene = defaultdict(list)
    for r in rows:
        by_scene[r["scene"]].append(r)
    lines = [f"Source: `{a.results.name}`, {len(rows)} images. A lens counts as within 1 mm when both |dA| and |dB| are.", "",
             "| scene | n | path | measured | MAE A,B (mm) | within 0.5 mm | within 1 mm | false detection (empty) | refusals |",
             "|---|---|---|---|---|---|---|---|---|"]
    for scene in ["all"] + sorted(by_scene):
        group = rows if scene == "all" else by_scene[scene]
        for p in paths:
            s = summarise(group, p)
            refusals = ", ".join(f"{k} {v}" for k, v in sorted(s["codes"].items()) if k != "OK")
            lines.append(f"| {scene} | {s['n']} | {'pipeline' if p == 'pipe' else p} | {fmt(s['measured'], True)} | {fmt(s['mae_ab'])} | "
                         f"{fmt(s['within_0_5'], True)} | {fmt(s['within_1'], True)} | {fmt(s['false_detection'], True)} | {refusals or '-'} |")
    text = "\n".join(lines) + "\n"
    print(text)
    if a.md:
        a.md.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
