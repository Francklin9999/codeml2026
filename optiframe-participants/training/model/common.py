"""Shared code of train.py, evaluate.py and export.py: model, data loading, metrics."""
from __future__ import annotations

import csv
import random
from pathlib import Path

import cv2
import numpy as np
import torch

# Interface fixed with brief 13 (app/src/vision/segmentModel.ts): 1x3x320x384, NCHW, ImageNet normalisation.
INPUT_H, INPUT_W = 320, 384
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
PX_PER_MM = 10  # of the 800x650 rectified images
# Name checked in segmentation_models_pytorch 0.5.0: the library has no "mobilenet_v3_small" key, MobileNetV3
# comes through the timm universal encoder ("tu-" prefix). Weights: timm mobilenetv3_small_100.lamb_in1k.
ENCODER = "tu-mobilenetv3_small_100"
DECODER_CHANNELS = (128, 64, 32, 16, 16)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = PROJECT_ROOT / "training" / "_local" / "dataset"
DEFAULT_OUT = PROJECT_ROOT / "training" / "_local" / "model_out"


def refuse_app_dir(path: Path) -> Path:
    """A toy or unreviewed model must never land in the web app: weights are copied there by hand."""
    p = Path(path).resolve()
    if (PROJECT_ROOT / "app").resolve() in [p, *p.parents]:
        raise SystemExit(f"refusing to write under app/: {p}")
    return p


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def build_model(encoder_weights: str | None = "imagenet") -> torch.nn.Module:
    import segmentation_models_pytorch as smp

    return smp.Unet(ENCODER, encoder_weights=encoder_weights, classes=1, decoder_channels=DECODER_CHANNELS)


def load_checkpoint(path: str | Path) -> torch.nn.Module:
    ckpt = torch.load(path, map_location="cpu", weights_only=True)
    model = build_model(None)
    model.load_state_dict(ckpt["model"])
    return model.eval()


# ---------------------------------------------------------------- data

def _read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_samples(data_dir: str | Path, split: str, sources: str = "both") -> list[dict]:
    """Rows of index.csv joined with split.csv, for one split.

    index.csv: file, lensId, pos, cond, source (real|synth). split.csv: split (train|val|test) and file or lensId.
    sources filters the rows by their `source` column ("real", "synth" or "both").
    """
    data_dir = Path(data_dir)
    index = _read_csv(data_dir / "index.csv")
    split_rows = _read_csv(data_dir / "split.csv")
    by_file = {r["file"]: r["split"] for r in split_rows if "file" in r}
    by_lens = {r["lensId"]: r["split"] for r in split_rows if "lensId" in r}
    out = []
    for r in index:
        s = by_file.get(r["file"]) or by_lens.get(r["lensId"])
        if s != split:
            continue
        if sources != "both" and r["source"] != sources:
            continue
        stem = Path(r["file"]).stem
        mask = data_dir / "masks" / (stem + ".png")
        if not mask.exists():
            mask = data_dir / "masks" / r["file"]
        out.append({**r, "image_path": data_dir / "images" / r["file"], "mask_path": mask})
    return out


def read_image(path: Path) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(path)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def read_mask(path: Path) -> np.ndarray:
    m = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if m is None:
        raise FileNotFoundError(path)
    return (m > 127).astype(np.uint8)


def resize_pair(img: np.ndarray, mask: np.ndarray | None):
    # The image must be resized exactly like the app does (resizeBilinear in segmentModel.ts: plain bilinear, half-pixel
    # centres, no anti-aliasing), otherwise training and evaluation use inputs the browser never feeds the model.
    # cv2.INTER_LINEAR is that resampler; INTER_AREA would be a different (anti-aliased) filter at this 2.08x downscale.
    # The label is not an input of the app, so its box-filter (INTER_AREA) downscale is kept.
    img = cv2.resize(img, (INPUT_W, INPUT_H), interpolation=cv2.INTER_LINEAR)
    if mask is not None:
        mask = (cv2.resize(mask.astype(np.float32), (INPUT_W, INPUT_H), interpolation=cv2.INTER_AREA) > 0.5).astype(np.uint8)
    return img, mask


def to_tensor(img_rgb_u8: np.ndarray) -> torch.Tensor:
    x = (img_rgb_u8.astype(np.float32) / 255.0 - MEAN) / STD
    return torch.from_numpy(x.transpose(2, 0, 1).copy())


# ---------------------------------------------------------------- metrics (numpy masks, 0/1, model resolution)

def largest_component(mask: np.ndarray) -> np.ndarray:
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    if n <= 1:
        return mask.astype(np.uint8)
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return (labels == k).astype(np.uint8)


def iou(pred: np.ndarray, gt: np.ndarray) -> float:
    inter = float(np.logical_and(pred, gt).sum())
    union = float(np.logical_or(pred, gt).sum())
    return 1.0 if union == 0 else inter / union


def _boundary(mask: np.ndarray) -> np.ndarray:
    m = mask.astype(np.uint8)
    return (m - cv2.erode(m, np.ones((3, 3), np.uint8), borderType=cv2.BORDER_CONSTANT, borderValue=0)).astype(bool)


def boundary_f(pred: np.ndarray, gt: np.ndarray, tol_px: float) -> float:
    """F1 of boundary pixels matched within tol_px (pixels of the given masks)."""
    bp, bg = _boundary(pred), _boundary(gt)
    if not bp.any() and not bg.any():
        return 1.0
    if not bp.any() or not bg.any():
        return 0.0
    dist_to_gt = cv2.distanceTransform((~bg).astype(np.uint8), cv2.DIST_L2, 5)
    dist_to_pred = cv2.distanceTransform((~bp).astype(np.uint8), cv2.DIST_L2, 5)
    precision = float((dist_to_gt[bp] <= tol_px).mean())
    recall = float((dist_to_pred[bg] <= tol_px).mean())
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def extents_mm(mask: np.ndarray, mm_per_px_x: float, mm_per_px_y: float):
    """(A, B) in mm: bounding extents along x and y, or None for an empty mask."""
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        return None
    return (xs.max() - xs.min() + 1) * mm_per_px_x, (ys.max() - ys.min() + 1) * mm_per_px_y
