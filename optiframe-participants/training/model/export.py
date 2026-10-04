"""Export best.pt to ONNX (fp32 and dynamically quantised int8) and check parity with PyTorch.

    python export.py --ckpt ../_local/model_out/best.pt --out ../_local/model_out
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch

import common

OPSET = 17
PARITY_TOL = 1e-3


def _run(path: Path, x: np.ndarray) -> np.ndarray:
    sess = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    return sess.run(["logits"], {"input": x})[0]


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ckpt", default=str(common.DEFAULT_OUT / "best.pt"))
    ap.add_argument("--out", default=str(common.DEFAULT_OUT), help="folder for lens_seg.onnx and lens_seg.int8.onnx (never under app/)")
    args = ap.parse_args(argv)

    out = common.refuse_app_dir(Path(args.out))
    out.mkdir(parents=True, exist_ok=True)
    fp32, int8 = out / "lens_seg.onnx", out / "lens_seg.int8.onnx"

    model = common.load_checkpoint(args.ckpt)
    dummy = torch.zeros(1, 3, common.INPUT_H, common.INPUT_W)
    # Legacy tracer: fixed shapes, one self-contained file (the dynamo exporter writes external data by default).
    torch.onnx.export(model, dummy, str(fp32), input_names=["input"], output_names=["logits"], opset_version=OPSET,
                      dynamo=False, do_constant_folding=True)

    # Parity on a few inputs: noise in the normalised range and a smooth gradient.
    rng = np.random.default_rng(0)
    xs = [rng.normal(0, 1, (1, 3, common.INPUT_H, common.INPUT_W)).astype(np.float32),
          np.broadcast_to(np.linspace(-2, 2, common.INPUT_W, dtype=np.float32), (1, 3, common.INPUT_H, common.INPUT_W)).copy()]
    with torch.no_grad():
        refs = [model(torch.from_numpy(x)).numpy() for x in xs]
    max_diff = max(float(np.abs(_run(fp32, x) - r).max()) for x, r in zip(xs, refs))

    from onnxruntime.quantization import QuantType, quantize_dynamic

    quantize_dynamic(str(fp32), str(int8), weight_type=QuantType.QInt8)
    int8_out = _run(int8, xs[0])
    int8_diff = float(np.abs(int8_out - refs[0]).max())
    int8_agree = float(((int8_out > 0) == (refs[0] > 0)).mean())

    report = {
        "opset": OPSET, "input": "input 1x3x%dx%d" % (common.INPUT_H, common.INPUT_W), "output": "logits 1x1x%dx%d" % (common.INPUT_H, common.INPUT_W),
        "fp32_bytes": fp32.stat().st_size, "int8_bytes": int8.stat().st_size,
        "fp32_max_abs_diff_vs_torch": max_diff, "parity_tolerance": PARITY_TOL,
        "int8_max_abs_diff_vs_torch": int8_diff, "int8_pixel_sign_agreement_on_noise_input": int8_agree,
    }
    (out / "export_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if max_diff >= PARITY_TOL:
        raise SystemExit(f"ONNX parity failed: max abs diff {max_diff:.2e} >= {PARITY_TOL}")
    return report


if __name__ == "__main__":
    main()
