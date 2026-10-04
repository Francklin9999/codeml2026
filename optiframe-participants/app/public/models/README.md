# models/

The app loads exactly one file, at the fixed URL `models/lens_seg.onnx` (relative to the app root; the service worker serves it network-first, cached for offline use). Delete the file to turn the model off: `isModelAvailable()` then returns false and the pipeline uses the classical segmenter only.

## The file shipped here (v2, 2026-10-04)

| | |
|---|---|
| File | `lens_seg.onnx`, float32, 7 879 653 bytes, SHA-256 `f8392e0cb6c4973cfc7f082944b021b100959b1e15523b9e99550dfe03d4572a` |
| Trained on | 24 159 **synthetic** windows only (`training/data/synth_rig.py` and `synth.py`, no external image, no manual label); no real photo yet |
| Training | U-Net / MobileNetV3-Small, ImageNet encoder. v1: 1 epoch fp32 + 18 epochs mixed precision on 15 959 windows (validation IoU 0.9755). v2: 7 more epochs from v1 (`train.py --amp --init`, lr 3e-4) after adding speckled tables, mounted lenses, empty windows and lenses crossing the border; best validation IoU 0.9695 on a harder validation set where v1 scores 0.967. NVIDIA RTX 2070 Super |
| Export | `export.py`, opset 17, max abs difference with PyTorch 1.3e-4 |
| In the app | Fallback only: called when the classical segmenter says NO_LENS or LENS_OUT_OF_WINDOW, or scores under `LOW_MASK_SCORE`; a mask whose mean probability is under `MIN_MODEL_SCORE` (0.85) or that comes within `BORDER_MARGIN_MM` (1 mm) of the border is refused |
| Not shipped | `lens_seg.int8.onnx` (2.2 MB): on a noise input its sign agrees with float32 on 78 % of pixels only |

Metrics on held-out synthetic windows and through the app's own code: [`../../../docs/DONNEES_ET_IA.md`](../../../docs/DONNEES_ET_IA.md). Accuracy on real lenses: TO MEASURE.

## Where the weights come from

They are produced offline by `training/model/` (brief 12: `train.py`, then `export.py`). Trained on the dataset of `training/data/`. Nothing is downloaded at runtime and no third-party weights are shipped.

## Regenerate

```
cd training/model
python train.py ...            # see training/model/README.md for the exact arguments
python export.py ...           # writes lens_seg.onnx (float) and lens_seg.int8.onnx (dynamic int8)
cp lens_seg.onnx ../../app/public/models/lens_seg.onnx          # or the int8 copy, renamed to lens_seg.onnx
```

Then bump `VERSION` in `app/public/sw.js` so phones drop the old cached model.

Smoke-test weights (the toy model of the training tests) must never be copied here.

## Interface the app expects (`app/src/vision/segmentModel.ts`)

- input `input`, float32 `1x3x320x384` (N, C, H, W), RGB 0-1 then normalised with mean (0.485, 0.456, 0.406) and std (0.229, 0.224, 0.225)
- output `logits`, float32 `1x1x320x384`; sigmoid > 0.5 = lens
- runs on the WASM execution provider, single thread; the runtime files are in `public/vendor/ort/`

## Measured on real phones

Download size, load time and inference time on a mid-range Android and an iPhone (budget 3 s per lens): TO MEASURE.
