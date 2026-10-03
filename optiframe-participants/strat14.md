# OptiFrame · Strategy 14: Statistical shape model of lens outlines (shape priors for robust contours)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 2 (contours in mm), some lens outlines (own measurements + synthetic families) |
| **Rubric lines** | Measurement accuracy (30), Contour quality (5), Robustness (10), Data & AI (15) |
| **Differs from 1–10** | Strategies 3–6 segment pixels. This adds a **model of what lens outlines look like** (Fourier descriptors / PCA shape space) and fits it to noisy evidence, so reflections, dust or a missing edge segment cannot produce an impossible contour |
| **Work folder** | `optiframe-participants/work/strat14/` |

---

## 1. Context you need

- Lens outlines are smooth, closed, mostly convex shapes (ovals, rounded rectangles, "aviator", "cat-eye" with a nasal / temporal asymmetry), 35–70 mm wide. Drill holes and notches exist for rimless lenses but are rare in recycled lenses from full-rim frames.
- Segmentation errors are local (a glare spot eats part of the edge, a shadow adds a bump). A global shape prior can fill or reject them.

## 2. The idea

1. Represent an outline by its **radius function r(θ)** around the boxing centre (or elliptic Fourier descriptors), resampled at 360 angles and normalised by size and rotation.
2. Build a **shape space** with PCA from a training set: our measured lenses + synthetic families (superellipses, rounded rectangles, asymmetric ovals) + optionally public frame-shape datasets if licences allow.
3. **Fit** the model to edge evidence with a robust objective (Huber / RANSAC over angular sectors), allowing a few principal components plus a free low-order residual; flag sectors where the evidence disagrees strongly with the fit as "uncertain" instead of trusting them.
4. Output: smooth contour + per-sector confidence; A/B computed from the fitted contour where evidence is missing, from the evidence elsewhere.

## 3. Why it could score

It protects the 30 accuracy points against the most common failure (a locally wrong edge) and improves the SVG contour quality. The shape space itself is a nice "data and AI" artefact.

## 4. Implementation plan

### 4.1 Files

```
work/strat14/
  shapes_synth.py     # parametric families → r(θ)
  shape_space.py      # normalise, PCA, save mean + components
  fit_shape.py        # robust fit to edge points / gradient evidence
  eval_shape.py
```

### 4.2 Robust fit

```python
# edge evidence: for each angle θ_k, candidate edge radii ρ_k (from strategy 2's normal profiles) with strengths w_k
# model: r(θ) = s * (mean(θ) + Σ_j b_j φ_j(θ)), rotation α, centre (cx, cy)
# minimise Σ_k w_k * huber(ρ_k − r(θ_k − α)) + λ Σ_j b_j² / σ_j²
```

Use `scipy.optimize.least_squares(loss="huber")`; initialise from the raw contour's boxing rectangle.

### 4.3 Uncertainty

Sectors with residual > 0.5 mm are marked; if they cover > 15% of the outline, ask for another shot (strategy 7) rather than trusting the prior.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Reconstruction | shape space with ≤ 8 components reconstructs held-out own lenses within 0.2 mm RMS |
| T2 | Corruption robustness | remove 10–30% of the edge evidence or add a fake bump (synthetic): fitted A/B error ≤ 0.3 mm vs ≥ 1 mm for the raw contour |
| T3 | Real hard shots | MAE vs calliper on glare / shadow shots: with prior < without |
| T4 | No over-smoothing | on clean shots, fitted contour within 0.1 mm of the raw contour (the prior must not distort good evidence) |

## 6. Risks

Unusual shapes outside the shape space; the free residual term and per-sector evidence weighting keep the fit honest.

## 7. Combines with

Strategy 2 (edge evidence), 3 / 5 / 6 (masks), 7 (multi-shot), 9 (smooth contours for offsetting).

## 8. Results log

| Date | Who | Components | T1 RMS | T2 error | MAE gain | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
