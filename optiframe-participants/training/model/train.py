"""Train the U-Net / MobileNetV3-Small lens segmenter.

    python train.py --data ../_local/dataset --out ../_local/model_out --sources both
"""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import albumentations as A
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

import common


def make_augmentation(seed: int | None = None) -> A.Compose:
    # Albumentations 2.x keeps its own RNG: seed_everything() does not reach it, so it is seeded here
    return A.Compose([
        A.Perspective(scale=(0.02, 0.08), p=0.5),
        A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.7),
        A.OneOf([A.GaussianBlur(blur_limit=(3, 7), p=1), A.MotionBlur(blur_limit=(3, 7), p=1)], p=0.4),
        A.GaussNoise(std_range=(0.01, 0.06), p=0.4),
        A.ImageCompression(quality_range=(40, 95), p=0.4),
        A.RandomShadow(shadow_roi=(0, 0, 1, 1), num_shadows_limit=(1, 2), shadow_intensity_range=(0.3, 0.7), p=0.3),
    ], seed=seed)


class LensDataset(Dataset):
    def __init__(self, samples: list[dict], augment: bool, seed: int = 0):
        self.samples = samples
        self.aug = make_augmentation(seed) if augment else None

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, i: int):
        s = self.samples[i]
        img, mask = common.resize_pair(common.read_image(s["image_path"]), common.read_mask(s["mask_path"]))
        if self.aug is not None:
            out = self.aug(image=img, mask=mask)
            img, mask = out["image"], out["mask"]
        return common.to_tensor(img), torch.from_numpy(mask.astype(np.float32))[None]


def bce_dice_loss(logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    bce = F.binary_cross_entropy_with_logits(logits, target)
    p = torch.sigmoid(logits)
    inter = (p * target).sum(dim=(1, 2, 3))
    dice = 1 - (2 * inter + 1) / (p.sum(dim=(1, 2, 3)) + target.sum(dim=(1, 2, 3)) + 1)
    return bce + dice.mean()


@torch.no_grad()
def validate(model, loader, device) -> float:
    model.eval()
    scores = []
    for x, y in loader:
        pred = torch.sigmoid(model(x.to(device))).cpu() > 0.5
        gt = y > 0.5
        for p, g in zip(pred, gt):
            scores.append(common.iou(p.numpy(), g.numpy()))
    return float(np.mean(scores))


def _worker_init(worker_id: int) -> None:
    # torch.initial_seed() is base_seed + worker_id, and base_seed comes from the seeded loader generator
    seed = torch.initial_seed() % 2**32
    np.random.seed(seed)
    random.seed(seed)
    info = torch.utils.data.get_worker_info()
    if info is not None and getattr(info.dataset, "aug", None) is not None:
        info.dataset.aug.set_random_seed(seed)


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=str(common.DEFAULT_DATA), help="folder with images/, masks/, index.csv, split.csv")
    ap.add_argument("--out", default=str(common.DEFAULT_OUT), help="where best.pt and train_log.json go (never under app/)")
    ap.add_argument("--sources", choices=["real", "synth", "both"], default="both", help="training data (ablation)")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--encoder-weights", choices=["imagenet", "none"], default="imagenet")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--amp", action="store_true", help="mixed precision (float16) on CUDA: about 2x faster on tensor-core GPUs")
    ap.add_argument("--init", default=None, help="start from this checkpoint (fine-tuning) instead of the ImageNet encoder")
    args = ap.parse_args(argv)

    out = common.refuse_app_dir(Path(args.out))
    out.mkdir(parents=True, exist_ok=True)
    common.seed_everything(args.seed)

    train_s = common.load_samples(args.data, "train", args.sources)
    val_s = common.load_samples(args.data, "val", "both")
    if not train_s or not val_s:
        raise SystemExit(f"need train and val samples, got {len(train_s)} train ({args.sources}) and {len(val_s)} val")

    gen = torch.Generator().manual_seed(args.seed)
    # persistent workers: on Windows (spawn) re-creating them every epoch re-imports torch each time
    keep = args.workers > 0
    train_loader = DataLoader(LensDataset(train_s, True, args.seed), batch_size=args.batch, shuffle=True, drop_last=len(train_s) > args.batch,
                              num_workers=args.workers, worker_init_fn=_worker_init, generator=gen, persistent_workers=keep,
                              pin_memory=args.device.startswith("cuda"))
    val_loader = DataLoader(LensDataset(val_s, False), batch_size=args.batch, num_workers=args.workers, persistent_workers=keep)

    device = torch.device(args.device)
    amp = args.amp and device.type == "cuda"
    if device.type == "cuda":
        torch.backends.cudnn.benchmark = True      # fixed input size: let cuDNN pick its fastest kernels
    if args.init:
        model = common.load_checkpoint(args.init).to(device)
    else:
        model = common.build_model(None if args.encoder_weights == "none" else "imagenet").to(device)
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)

    log, best = [], -1.0
    for epoch in range(args.epochs):
        model.train()
        t0, losses = time.time(), []
        for x, y in train_loader:
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp):
                logits = model(x)
            loss = bce_dice_loss(logits.float(), y)
            opt.zero_grad()
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            losses.append(loss.item())
        sched.step()
        val_iou = validate(model, val_loader, device)
        log.append({"epoch": epoch + 1, "train_loss": float(np.mean(losses)), "val_iou": val_iou, "seconds": round(time.time() - t0, 1)})
        print(json.dumps(log[-1]), flush=True)
        if val_iou > best:
            best = val_iou
            torch.save({"model": model.state_dict(), "encoder": common.ENCODER, "val_iou": val_iou, "epoch": epoch + 1,
                        "sources": args.sources}, out / "best.pt")

    summary = {"sources": args.sources, "n_train": len(train_s), "n_val": len(val_s), "best_val_iou": best, "args": vars(args), "log": log}
    (out / "train_log.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    main()
