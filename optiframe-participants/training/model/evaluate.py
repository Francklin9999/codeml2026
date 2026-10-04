"""Evaluate the segmenter and an Otsu baseline on a split, per condition and overall.

    python evaluate.py --ckpt ../_local/model_out/best.pt --data ../_local/dataset --out ../_local/model_out

Metrics (all at the model resolution 320x384, masks cleaned to their largest component):
IoU; boundary F-score with a 0.5 mm tolerance (5 px of the 800x650 image, scaled to the model resolution);
mean absolute error in mm of A and B, the bounding extents of the predicted mask against those of the label.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np
import torch

import common

TOL_MM = 0.5


def otsu_mask(img_rgb: np.ndarray) -> np.ndarray:
    """Baseline: Otsu on the grey image. Polarity: the side touching the image border least is the lens."""
    grey = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    _, hi = cv2.threshold(grey, 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    border = lambda m: float(np.concatenate([m[0], m[-1], m[:, 0], m[:, -1]]).mean())
    mask = hi if border(hi) <= border(1 - hi) else 1 - hi
    return common.largest_component(mask.astype(np.uint8))


def make_predictor(ckpt: str | None, onnx: str | None):
    if onnx:
        import onnxruntime as ort

        sess = ort.InferenceSession(onnx, providers=["CPUExecutionProvider"])
        return lambda x: sess.run(["logits"], {"input": x.numpy()})[0]
    model = common.load_checkpoint(ckpt)

    def run(x: torch.Tensor) -> np.ndarray:
        with torch.no_grad():
            return model(x).numpy()

    return run


def score(pred: np.ndarray, gt: np.ndarray, mm_x: float, mm_y: float) -> dict:
    tol_px = TOL_MM * common.PX_PER_MM * ((common.INPUT_W / 800 + common.INPUT_H / 650) / 2)
    ext_p, ext_g = common.extents_mm(pred, mm_x, mm_y), common.extents_mm(gt, mm_x, mm_y)
    ok = ext_p is not None and ext_g is not None
    return {"iou": common.iou(pred, gt), "boundary_f": common.boundary_f(pred, gt, tol_px),
            "err_A_mm": abs(ext_p[0] - ext_g[0]) if ok else None, "err_B_mm": abs(ext_p[1] - ext_g[1]) if ok else None}


def aggregate(rows: list[dict]) -> dict:
    def mean(k):
        v = [r[k] for r in rows if r[k] is not None]
        return float(np.mean(v)) if v else None

    return {"n": len(rows), "iou": mean("iou"), "boundary_f": mean("boundary_f"), "err_A_mm": mean("err_A_mm"),
            "err_B_mm": mean("err_B_mm"), "n_empty_prediction": sum(r["err_A_mm"] is None for r in rows)}


def _fmt(v, nd=3):
    return "n/a" if v is None else f"{v:.{nd}f}"


def markdown(result: dict) -> str:
    lines = [f"# Segmentation metrics ({result['split']} split, {result['n_images']} images)", "",
             f"Produced by `evaluate.py`; predictor: {result['predictor']}. Model resolution {common.INPUT_H}x{common.INPUT_W}, "
             f"boundary tolerance {TOL_MM} mm, A/B error = mean absolute difference of bounding extents in mm.", ""]
    for method in ("model", "otsu"):
        lines += [f"## {method}", "", "| condition | n | IoU | boundary F | err A (mm) | err B (mm) | empty |", "|---|---|---|---|---|---|---|"]
        entries = [("overall", result["overall"][method])] + sorted(result["per_condition"][method].items())
        for name, a in entries:
            lines.append(f"| {name} | {a['n']} | {_fmt(a['iou'])} | {_fmt(a['boundary_f'])} | {_fmt(a['err_A_mm'])} | "
                         f"{_fmt(a['err_B_mm'])} | {a['n_empty_prediction']} |")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=str(common.DEFAULT_DATA))
    ap.add_argument("--ckpt", default=str(common.DEFAULT_OUT / "best.pt"))
    ap.add_argument("--onnx", default=None, help="evaluate this ONNX file (fp32 or int8) instead of the checkpoint")
    ap.add_argument("--split", default="test", choices=["train", "val", "test"])
    ap.add_argument("--out", default=str(common.DEFAULT_OUT), help="folder for metrics.md and metrics.json")
    args = ap.parse_args(argv)

    out = common.refuse_app_dir(Path(args.out))
    out.mkdir(parents=True, exist_ok=True)
    samples = common.load_samples(args.data, args.split, "both")
    if not samples:
        raise SystemExit(f"no samples in split {args.split}")
    predict = make_predictor(args.ckpt, args.onnx)

    rows = {"model": [], "otsu": []}
    conds = []
    for s in samples:
        img_full, gt_full = common.read_image(s["image_path"]), common.read_mask(s["mask_path"])
        h, w = gt_full.shape
        img, gt = common.resize_pair(img_full, gt_full)
        mm_x, mm_y = (w / common.INPUT_W) / common.PX_PER_MM, (h / common.INPUT_H) / common.PX_PER_MM
        logits = predict(common.to_tensor(img)[None])
        pred = common.largest_component((logits[0, 0] > 0).astype(np.uint8))
        rows["model"].append(score(pred, gt, mm_x, mm_y))
        rows["otsu"].append(score(otsu_mask(img), gt, mm_x, mm_y))
        conds.append(s["cond"])

    result = {"split": args.split, "n_images": len(samples), "predictor": args.onnx or args.ckpt,
              "overall": {m: aggregate(r) for m, r in rows.items()}, "per_condition": {}}
    for m, r in rows.items():
        groups = defaultdict(list)
        for row, c in zip(r, conds):
            groups[c].append(row)
        result["per_condition"][m] = {c: aggregate(g) for c, g in groups.items()}
    (out / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (out / "metrics.md").write_text(markdown(result), encoding="utf-8")
    print(markdown(result))
    return result


if __name__ == "__main__":
    main()
