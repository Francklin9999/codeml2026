# training/model: train and export the lens segmenter

U-Net with a MobileNetV3-Small encoder (1 output channel), input `1x3x320x384` (rectified 800x650 window resized with plain bilinear interpolation, half-pixel centres, no anti-aliasing, then ImageNet mean/std), exported to ONNX for the browser (brief 13).

All real-world metrics are `TO MEASURE`: they exist only as the output of `evaluate.py` on the dataset the team shoots. No number is quoted in this file.

## Preprocessing contract with the app

The image is downscaled 800x650 to 384x320 with bilinear interpolation (`cv2.INTER_LINEAR` in `common.resize_pair`), the same resampler as `resizeBilinear` in `app/src/vision/segmentModel.ts` (brief 13): half-pixel centres, edge clamped, no anti-aliasing. Training, `evaluate.py` and the export all use it, so the metrics describe the input the app really feeds the model. The only difference is that OpenCV rounds the result to uint8 while the app keeps floats (under one grey level). The label mask is downscaled with a box filter (`INTER_AREA`) and thresholded at 0.5: it is a target, not an app input. `tests/test_metrics.py::test_resize_matches_app_bilinear` guards this.

## Dataset format (from brief 11)

`images/`, `masks/` (800x650, mask 0/255, same stem as the image, `.png`), `index.csv` (`file, lensId, pos, cond, source` with `source` = `real` or `synth`), `split.csv` (`split` = train/val/test, joined on `file` or, if absent, on `lensId`). Default location `training/_local/dataset` (git-ignored).

## Commands

Run from `training/model/`.

```bash
python -m venv .venv
. .venv/Scripts/activate            # Windows Git Bash; on Linux/Colab: . .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu   # skip on Colab, torch is preinstalled
pip install -r requirements.txt

# smoke test (CPU, ~2 min): 16 synthetic samples, 2 epochs, export, parity check, evaluation
python -m pytest -q tests

# train (ImageNet encoder weights are downloaded once through timm / Hugging Face Hub)
python train.py --data ../_local/dataset --out ../_local/model_out --sources both   # real | synth | both
python export.py --ckpt ../_local/model_out/best.pt --out ../_local/model_out
python evaluate.py --data ../_local/dataset --ckpt ../_local/model_out/best.pt --out ../_local/model_out
```

- `train.py`: Albumentations (perspective, brightness/contrast, blur, noise, JPEG, random shadow), loss BCE + soft Dice, AdamW lr 1e-3 (weight decay 1e-4) with cosine schedule, 40 epochs, batch 16, seed 0, best checkpoint on validation IoU (threshold 0.5, model resolution). `--sources` is the ablation switch (strat6 E3): it filters the training rows by `source`. Validation always uses the whole val split. Run it three times with `real`, `synth`, `both` and compare the three `metrics.md`, each written to its own `--out`.
- `export.py`: ONNX opset 17, fixed input `input` `1x3x320x384`, output `logits` `1x1x320x384` (raw logits, apply a sigmoid), then onnxruntime parity against PyTorch (fails if the max absolute difference is >= 1e-3), then a dynamically quantised int8 copy. Writes `lens_seg.onnx`, `lens_seg.int8.onnx` and `export_report.json` (both file sizes, parity). The int8 file uses `ConvInteger`: whether onnxruntime-web runs it is not verified here, keep the fp32 file as the default in the app.
- `evaluate.py`: on the test split (`--split`), per condition and overall, for the model (`--ckpt`, or `--onnx` to score the exported file) and for an Otsu baseline on the grey image. Metrics: IoU, boundary F-score at 0.5 mm (5 px of the 800x650 image, scaled to the model resolution), mean absolute error in mm of A and B (bounding extents of the largest component of the predicted mask against the label). Writes `metrics.md` and `metrics.json`. The Otsu polarity rule is naive on purpose: the side that touches the image border least is the lens.
- Weights and models are never written under `app/` (the scripts refuse). After a real training run, copy `lens_seg.onnx` to the app by hand.
- Colab: `train_colab.ipynb` clones the repo, installs `requirements.txt`, unzips the dataset and calls the three scripts (`REPO_URL` and `DATA_ZIP` are `TO FILL`).
- `train.py --amp` trains in mixed precision on CUDA (about 20 % faster on an RTX 2070 Super here: the MobileNetV3 depthwise layers, not the data, set the pace); `--init best.pt` starts from a checkpoint (fine-tuning, a new cosine schedule). DataLoader workers are persistent (Windows re-imports torch in every new worker).

## The runs behind the shipped model (2026-10-04, local NVIDIA RTX 2070 Super, `training/.venv`, torch 2.6.0+cu124)

Data built with `training/data/` (`synth_rig.py`, `synth.py`, `build_dataset.py`, `preresize.py`, all synthetic, no real photo yet); validation and test are synthetic too, drawn with their own seeds. Full log: `docs/JOURNAL_POSTE2.md`.

```bash
# v1: 15 959 training windows, 600 validation
python train.py --data ../_local/ds_v1_384 --out ../_local/model_v1 --epochs 30 --workers 8          # stopped after epoch 1 (326 s/epoch)
python train.py --data ../_local/ds_v1_384 --out ../_local/model_v1 --epochs 18 --workers 8 --amp --init ../_local/model_v1_fp32_ep.pt
# v2 (shipped): + speckled tables, mounted lenses, empty windows, lenses crossing the border = 24 159 windows, 800 validation
python train.py --data ../_local/ds_v2_384 --out ../_local/model_v2 --epochs 7 --lr 3e-4 --workers 8 --amp --init ../_local/model_v1/best.pt
python export.py --ckpt ../_local/model_v2/best.pt --out ../_local/model_v2_export
```

Best validation IoU: v1 0.9755 (its own validation set), v2 0.9695 on the harder v2 validation set where v1 scores 0.967. Held-out synthetic metrics and the app-side benchmark: `docs/DONNEES_ET_IA.md` §6.0 and §7.1. Real-photo metrics: TO MEASURE.

Encoder name: `segmentation_models_pytorch` 0.5.0 has no `mobilenet_v3_small` key (its own list has `mobilenet_v2` and `mobileone_*`). MobileNetV3-Small comes through the timm universal encoder as `tu-mobilenetv3_small_100`, whose `imagenet` weights are timm's `mobilenetv3_small_100.lamb_in1k`. The smoke test uses `encoder_weights=None` (no download).

## Versions used for the smoke test

Python 3.13.7, Windows 11, CPU. torch 2.14.1+cpu, segmentation_models_pytorch 0.5.0, timm 1.0.30, albumentations 2.0.8, onnx 1.23.1, onnxruntime 1.30.0, numpy 2.5.3, opencv-python-headless 5.0.0.93, pytest 9.1.1.

## Licences

Read in the metadata of the installed packages (`pip show`, `*.dist-info/METADATA`) on the date of the smoke test, and in timm's pretrained config for the weights.

| Component | Version | Licence | Where read |
|---|---|---|---|
| PyTorch (torch) | 2.14.1 | BSD-3-Clause and others (Apache-2.0, MIT, BSL-1.0 for bundled parts) | `pip show torch`, License-Expression field |
| torchvision (dependency of smp) | 0.29.1 | BSD | `pip show torchvision` |
| segmentation_models_pytorch | 0.5.0 | MIT | `pip show` |
| timm | 1.0.30 | Apache-2.0 | `pip show` |
| huggingface_hub (weights download) | 2.1.1 | Apache-2.0 | `pip show` |
| safetensors | 0.8.0 | Apache-2.0 | METADATA classifier |
| albumentations (and albucore) | 2.0.8 (0.0.24) | MIT | `pip show` |
| onnx | 1.23.1 | Apache-2.0 | `pip show` |
| onnxruntime | 1.30.0 | MIT | `pip show` |
| numpy | 2.5.3 | BSD-3-Clause (plus 0BSD, MIT, Zlib, CC0 for bundled parts) | `pip show` |
| scipy (dependency of smp/albumentations) | 1.18.1 | BSD-3-Clause | METADATA classifier and LICENSE.txt |
| opencv-python-headless | 5.0.0.93 | Apache-2.0 | `pip show` |
| pytest | 9.1.1 | MIT | `pip show` |
| Pre-trained weights `mobilenetv3_small_100.lamb_in1k` | n/a | Apache-2.0 declared by timm | `timm.models.get_pretrained_cfg('mobilenetv3_small_100.lamb_in1k').license` (timm 1.0.30) |

The weights were trained by their authors on ImageNet-1k. The ImageNet dataset terms were not checked by us: say in the jury document that the encoder is initialised from ImageNet weights, and fine-tuned on our own dataset. The int8 and fp32 ONNX files we export are derived from these weights.

Not used on purpose: Ultralytics YOLO (AGPL-3.0), SAM export, boundary loss.

## TO MEASURE

IoU, boundary F-score and A/B error of the model and of the Otsu baseline on real test lenses, the three-way ablation (`real`, `synth`, `both`), latency in the browser, int8 behaviour in onnxruntime-web.
