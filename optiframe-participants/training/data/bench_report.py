"""Summarise app/bench/seg_bench.test.ts output (bench_results.csv) per scene and per path.

For each of classic, model and pipeline (= what the app would do, recomputed here from the classic and model
columns with worker.ts's rule; --fallback-on adds classic codes that also let the model try): share of images measured, share refused
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


LOW_MASK_SCORE = 0.3   # worker.ts


def pipeline(r: dict, fallback_on: set[str]) -> tuple[str, str, str]:
    """(code, A, B) the app returns, from the classic and model outcomes (worker.ts segment()).

    classic mask scoring >= LOW_MASK_SCORE wins; else the model is tried when the classic answer is a low-score mask or a
    refusal whose code is in fallback_on; a model refusal falls back to the low-score classic mask if there is one."""
    cc, mc = r["classic_code"], r["model_code"]
    classic_mask = cc == "OK"
    if classic_mask and r["classic_score"] and float(r["classic_score"]) >= LOW_MASK_SCORE:
        return cc, r["classic_A"], r["classic_B"]
    if not classic_mask and cc not in fallback_on:
        return cc, "", ""
    if mc == "OK":
        return mc, r["model_A"], r["model_B"]
    if classic_mask:
        return cc, r["classic_A"], r["classic_B"]
    if mc in ("NONE", "LOAD_FAILED", "") or cc == "LENS_OUT_OF_WINDOW":   # the classic "past the border" stands
        return cc, "", ""
    return mc, "", ""


def fmt(v, pct=False) -> str:
    if v is None:
        return "-"
    return f"{100 * v:.0f} %" if pct else f"{v:.2f}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results", type=Path)
    ap.add_argument("--md", type=Path)
    ap.add_argument("--fallback-on", nargs="*", default=["NO_LENS", "LENS_OUT_OF_WINDOW"],
                    help="classic refusal codes that let the model try (worker.ts: NO_LENS and LENS_OUT_OF_WINDOW)")
    a = ap.parse_args(argv)
    with open(a.results, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:   # the pipe_* columns of older bench runs used a looser rule: recompute them
        r["pipe_code"], r["pipe_A"], r["pipe_B"] = pipeline(r, set(a.fallback_on))
    has_model = any(r["model_code"] not in ("NONE", "") for r in rows)
    paths = ["classic", "model", "pipe"] if has_model else ["classic"]
    by_scene = defaultdict(list)
    for r in rows:
        by_scene[r["scene"]].append(r)
    lines = [f"Source: `{a.results.name}`, {len(rows)} images. A lens counts as within 1 mm when both |dA| and |dB| are. "
             f"Pipeline: model tried after classic {', '.join(a.fallback_on)}.", "",
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
