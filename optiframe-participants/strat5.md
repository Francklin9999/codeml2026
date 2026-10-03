# OptiFrame · Strategy 5: Promptable foundation-model segmentation (SAM family) in the browser

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 4–5 h |
| **Depends on** | strategy 2 (rectified image, window position as prompt) |
| **Rubric lines** | Data & AI (15), Robustness (10), Measurement accuracy (30) when backlight is poor |
| **Work folder** | `optiframe-participants/work/strat5/` |

---

## 1. Context you need

The brief lists "modèles pré-entraînés comme Segment Anything" as allowed (cite licences). Processing in the browser is recommended (no server, data stays on the phone), and the result must arrive in **< 30 s per pair** on a mid-range phone. Pre-trained models are allowed if cited with their licence. No manual annotation is allowed on evaluation photos, so prompts must be automatic.

## 2. The idea

Run a lightweight promptable segmentation model in the browser (ONNX Runtime Web) and prompt it **automatically from the rig geometry**: the lens is always inside the board's window, so the window rectangle (or its centre point) is the prompt. Then refine the mask boundary with strategy 2's sub-pixel edge step.

## 3. Why it could score

It gives a robust mask in conditions where classical thresholds fail (front lighting, reflections, cluttered background), with zero training, and it is a legitimate "AI" component for the Data & AI criterion if we also measure it properly.

## 4. Implementation plan

### 4.1 Model candidates (check licences and sizes before choosing)

| Model | Why | Notes |
|---|---|---|
| SAM ViT-B (Meta, Apache-2.0) | reference quality | too heavy for phones; use only offline as a teacher |
| MobileSAM (Apache-2.0) | ~10 MB image encoder | known ONNX exports; browser-feasible |
| EfficientSAM / EdgeSAM / SAM 2 tiny | alternatives | verify licence and ONNX support |
| SlimSAM | pruned SAM | check |

Record the exact model, version, source URL and licence in the README.

### 4.2 Files

```
work/strat5/
  export_onnx.py         # export encoder + decoder to ONNX (or download official exports), quantise to int8 if needed
  sam_segment.py         # Python reference implementation
  web/sam.js             # ONNX Runtime Web (WebGPU if available, else WASM) inference
  eval_sam.py
```

### 4.3 Pipeline

1. Rectified window crop (strategy 2), resized to the encoder's input (e.g. 1024 longest side).
2. Prompt: box = window rectangle minus a 3 mm margin; plus a positive point at the window centre; optionally negative points on the board area.
3. Decoder → 3 candidate masks; choose by predicted IoU score + plausibility (area, solidity, not touching the window border).
4. Map the mask back to the rectified metric image; refine the boundary with strategy 2's normal-profile sub-pixel step (SAM masks are often ±2–3 px off at boundaries).
5. Timing budget on phone: encoder ≤ 8 s, decoder ≤ 0.5 s, per lens.

### 4.4 Teacher / student option

Use full SAM (ViT-H/B) offline on our own photos to produce masks, inspect them, and use them as training labels for strategy 6's small model.

## 5. How to test it

| # | Experiment | Metric | Target |
|---|---|---|---|
| E1 | Own lenses on the backlit rig | A/B MAE vs calliper | within 0.1 mm of strategy 3 (after refinement) |
| E2 | Own lenses, front light only, no backlight, patterned table | MAE, failure rate | clearly better than strategy 3 |
| E3 | Prompt variants (box / point / box+point) | IoU vs reference mask | pick the best |
| E4 | Browser latency on 2 phones (one mid-range Android, one iPhone) | seconds per lens | ≤ 10 s |
| E5 | Quantised vs float model | MAE difference | ≤ 0.05 mm |

**Kill:** if E4 cannot reach ≤ 15 s on a mid-range phone, run it server-side (allowed if the server stays up until deliberation ends) or keep it as offline teacher only.

## 6. Risks

Model size and memory on iOS Safari (WebGPU support varies; WASM fallback is slower). Download size: cache the model with a service worker.

## 7. Combines with

Strategy 2 (refinement), 3 (fusion and fallback), 6 (teacher labels), 10 (in-browser runtime).

## 8. Results log

| Date | Who | Model | Condition | MAE A / B | Latency | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
