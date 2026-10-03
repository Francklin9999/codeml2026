# OptiFrame · Strategy 6: Paired-capture dataset + synthetic lenses → fine-tuned lightweight segmenter

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (main "Palier 2" story; 15 points) |
| **Effort** | 6–8 h |
| **Depends on** | strategy 1 (rig), 3 (auto labels on backlit shots); 5 optional (teacher) |
| **Rubric lines** | Data & AI (15: dataset ingenuity, model training, metrics, licences), Robustness (10) |
| **Work folder** | `optiframe-participants/work/strat6/` |

---

## 1. Context you need

Palier 2 (*"fortement valorisé"*): get a good contour despite reflections, shadows, a tilted photo or a transparent lens, with a segmentation model trained or fine-tuned on data of our choice, running in the browser or on a server. Data & AI rubric: *"Ingéniosité du jeu de données (collecte, synthétique, augmentation), choix et entraînement du modèle, mesures de performance, sources et licences citées."* No personal data in datasets (faces, names, prescriptions). Free training: Google Colab / Kaggle; export to ONNX or TensorFlow.js.

## 2. The idea

The hard part is labels. Solve it with **paired capture**: the phone stays on a stand, the lens stays put, and we take (a) an **easy shot** (backlit, strategy 3 gives a near-perfect mask automatically) and (b) several **hard shots** of the identical scene (front light, lamp reflections, patterned background, shadows, phone flash). The easy shot's mask labels all hard shots for free. Add synthetic composites for variety, then fine-tune a small segmentation network and export it for the browser.

## 3. Why it could score

It is a genuinely ingenious, documented dataset with zero manual annotation, measured performance and a deployable model: exactly what the 15-point criterion describes.

## 4. Implementation plan

### 4.1 Files

```
work/strat6/
  capture_protocol.md     # how to shoot pairs (stand, sequence, lighting list)
  autolabel.py            # backlit shot → mask (strategy 3) → propagate to paired shots
  synth_composite.py      # synthetic lenses on varied backgrounds
  dataset_card.md         # sources, licences, counts, splits
  train.ipynb             # Colab/Kaggle notebook
  export.py               # ONNX (+ int8) / TF.js
  metrics.md
```

Raw images and the generated dataset go in `work/_local/` (git-ignored) or a release asset; keep only a small sample in Git.

### 4.2 Paired-capture protocol

- Phone on a stand (fixed), board + lens on the laptop screen.
- Sequence per lens position: 1 backlit shot (screen white) → screen off + room light → desk lamp at 3 angles (specular reflections) → phone flash → patterned background printed under the board (wood, fabric, text) → coloured screen (pink, blue).
- Move or rotate the lens, repeat. Target: 15 lenses × 6 positions × 8 conditions ≈ 700 labelled images in ~2 hours of shooting.
- Augmentation at training time: perspective (simulating tilted shots, applied to image + mask), blur, noise, colour jitter, JPEG, random shadows.

### 4.3 Synthetic composites (cheap variety)

Generate lens shapes (parametric families: ellipses, rounded rectangles, "aviator", "cat-eye", superellipses; 35–65 mm wide), render a transparent-looking lens over a background photo by: slight magnification / displacement of the background inside the shape (thin-lens refraction approximation), a dark rim band (1–3 px), specular highlights (random ellipses), Fresnel-like edge brightening. Optional: Blender Cycles with a glass material for physically based renders (heavier). Use CC0 / own backgrounds only.

### 4.4 Model

| Option | Size | Notes |
|---|---|---|
| U-Net with MobileNetV3-Small encoder (`segmentation_models_pytorch`, ImageNet weights) | ~2–5 MB | simple, fast in ONNX Runtime Web |
| DeepLabV3-MobileNetV3 (torchvision) | ~11 MB | good boundaries |
| YOLOv8n-seg / YOLO11n-seg (Ultralytics, **AGPL-3.0**: check licence implications) | ~6 MB | easy training |

Input: rectified window crop 512×512 (from strategy 2's homography) so the model always sees the lens at a known scale. Loss: BCE + Dice + boundary loss (or Lovász). Train 30–50 epochs on Colab T4.

### 4.5 Splits (avoid leakage)

Split **by lens**, not by image: test lenses never appear in training. Report on (a) held-out lenses in hard conditions, (b) synthetic-only training vs real-only vs both.

### 4.6 Export

ONNX opset 17, dynamic quantisation to int8; check output equality vs PyTorch (max abs diff); measure browser latency.

## 5. How to test it

| # | Experiment | Metric | Target |
|---|---|---|---|
| E1 | Label quality | propagate masks, overlay on hard shots, inspect 50 random pairs | ≥ 95% visually correct (else check the stand moved) |
| E2 | Held-out lenses, hard conditions | IoU, boundary F-score at 0.5 mm tolerance, A/B MAE after strategy 2 refinement | IoU ≥ 0.97, MAE ≤ 0.7 mm |
| E3 | Ablation | synthetic only / real only / both | both best, or report honestly |
| E4 | vs baselines | strategy 3 and 5 on the same hard test set | better than 3 in hard conditions |
| E5 | Browser | latency on 2 phones; output parity with PyTorch | ≤ 3 s per lens; IoU parity ≥ 0.99 |

## 6. Risks

Time: shooting + training + export can eat the day. Fix a cut-off: if E2 is not met by hour 18, present the dataset and metrics honestly and use strategy 3 / 5 in the app.

## 7. Combines with

Strategy 3 (auto-labels), 5 (teacher), 2 (refinement), 10 (deployment), presentation (dataset card is a strong slide).

## 8. Results log

| Date | Who | Train set | IoU | Boundary F | MAE A / B | Latency | Notes |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
