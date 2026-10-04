# models/

The app loads exactly one file, at the fixed URL `models/lens_seg.onnx` (relative to the app root, so the service worker caches it cache-first: it matches `/models/`). **The file is not in the repository yet.** Until it is deployed, `isModelAvailable()` returns false and the pipeline uses the classical segmenter only.

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
