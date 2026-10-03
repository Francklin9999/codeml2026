# EquiAlgo · Strategy 2: Synthetic-reference simulator and official-like scorer

| | |
|---|---|
| **Status** | IN PROGRESS — Codex, 2026-10-03; shared scorer and nine hypotheses tested; registry, H6 and calibration report unfinished |
| **Priority** | P1 (foundation: every other strategy is compared with it) |
| **Effort** | 3–4 h |
| **Depends on** | nothing |
| **Rubric lines** | makes the Technical section (35) measurable; feeds the Pareto front |
| **Work folder** | `equialgo-participants/work/shared/` (shared code) + `work/strat2/` (outputs) |

---

## 1. Context you need

- The 35 automatic points are scored against a **hidden reference built independently of the committee**. Equity (20) = share of the baseline equal-opportunity gap (0.270) closed; utility (15) = agreement, scaled between a random budget-respecting draw and perfect; both 0 outside 36–44% grant rate.
- The brief also says HxBuddy shows only "indicative F1 and accuracy" and does not compute the 35 points.
- We do not know: the reference's construction, the exact agreement metric, whether the EO gap is computed on 2 groups or 5 regions. Treat each as a parameter.

## 2. The idea

Enumerate the plausible ways the organisers built the reference, generate each one on our data, and score every strategy against all of them with a scorer that mimics the official one. Output: a **robustness matrix** (strategies × hypotheses → equity, utility, total /35).

## 3. Why it matters

Without it, comparisons between strategies are opinions. With it, we choose the submission that wins across plausible worlds and can show the jury a principled evaluation despite the hidden label.

## 4. Implementation plan

### 4.1 Files

```
work/shared/
  data.py                  # loaders + features() (see strategy 1 §4.3)
  validate_submission.py   # format + budget check
  reference_sim.py         # hypothesis generators
  score.py                 # official-like scorer + CLI
  registry.py              # strategies expose predict() / score()
  test_score.py
work/strat2/
  robustness_matrix.csv  robustness_heatmap.png
```

### 4.2 `validate_submission.py`

Checks: header `id_candidat,decision_octroi`; 4,000 rows; IDs equal (as a set and in order) to `candidats_evaluation.csv`; values in {0,1}; rate in [0.36, 0.44]. Exit non-zero and **warn below 0.38 or above 0.42** (safety margin).

### 4.3 Reference hypotheses (`reference_sim.py`)

Each function returns a 0/1 array for the 10k historical rows and the 4k candidates (positive rate 40% unless stated). Seeded.

| ID | Construction | Rationale |
|---|---|---|
| H1 | Fit committee logit with `remote`; reference = top 40% of the score with `remote = 0` | "committee minus the regional penalty" |
| H1n5 / H1n10 | H1, then flip 5% / 10% of labels at random | noisy generator |
| H2 | Top 40% by `cote_r_equivalent` only | pure merit |
| H3w | score = z(cote R) + w·[z(−log income) + z(hours) + z(first-gen)], w ∈ {0.25, 0.5, 1}; top 40% | merit + need |
| H4 | H1, but distance and postal code also set to central-region values (quantile mapping within region) | all regional signal removed |
| H5 | GBM fitted on the committee without region, scored with region effect removed by averaging | non-linear world |
| H6 | Latent generator: `latent = f(x) + ε`, `committee = 1[latent − π·remote + ε' > q]`, reference = `1[latent > q']`; fit f, π, noise scales so the simulated committee reproduces the real one (grant rates by region 48.4 / 27.3, AUC ≈ 0.957) | closest to how such a dataset is usually generated |

### 4.4 Scorer (`score.py`)

```python
def eo_gap(y_ref, y_pred, group):          # group in {"Centre","Eloignee"} (variant: 5 regions → max-min)
    tpr = {g: y_pred[(group == g) & (y_ref == 1)].mean() for g in np.unique(group)}
    return max(tpr.values()) - min(tpr.values())

def official_like(y_pred, y_ref, group, baseline_pred, metric="accuracy", n_random=200, rng=0):
    rate = y_pred.mean()
    if not (0.36 <= rate <= 0.44): return dict(equity=0, utility=0, total=0)
    gap0 = eo_gap(y_ref, baseline_pred, group)            # also report with the fixed 0.270
    equity = 20 * np.clip((gap0 - eo_gap(y_ref, y_pred, group)) / gap0, 0, 1)
    m = METRICS[metric](y_ref, y_pred)                     # accuracy | f1 | balanced_accuracy
    m_rand = np.mean([METRICS[metric](y_ref, random_draw(len(y_ref), 1600, rng+i)) for i in range(n_random)])
    utility = 15 * np.clip((m - m_rand) / (1 - m_rand), 0, 1)
    return dict(equity=equity, utility=utility, total=equity + utility)
```

`baseline_pred` = the notebook's final-cell baseline (RandomForest 300 trees, `min_samples_leaf=20`, `random_state=42`, all columns, trained on all 10k), rescaled to 1,600 grants by its probabilities if its native rate differs (record its native rate too).

CLI: `python work/shared/score.py --pred file.csv --all-hypotheses --metric accuracy,f1,balanced_accuracy --grouping 2,5`.

### 4.5 Registry

Every strategy exposes `predict(candidates_df) -> np.ndarray[int]` (and optionally `score(...)` for sweeps). `python work/shared/registry.py --matrix` runs all registered strategies × hypotheses and writes `work/strat2/robustness_matrix.csv` + a heatmap.

## 5. How to test it

### 5.1 Sanity tests (`test_score.py`)

| Test | Expected |
|---|---|
| perfect predictor (`y_pred = y_ref`) | 35/35 under every hypothesis |
| random 1,600-draws | utility ≈ 0 (± small noise) |
| baseline predictions | equity = 0 by construction |
| rate 0.30 or 0.50 | 0/35 |
| deterministic seeds | identical scores across runs |

### 5.2 Calibration hook (for strategy 3)

Report, for each hypothesis, the baseline's EO gap on the 4k candidates and on the notebook's 30% test split, next to the official 0.270.

### 5.3 Performance

Whole matrix (≈ 10 strategies × ≈ 12 hypotheses × 3 metrics) in < 2 minutes.

### 5.4 Acceptance

All sanity tests pass; matrix and heatmap regenerate with one command.

## 6. Risks

The real reference may be none of these. The hypothesis set is deliberately broad, and strategy 3 weights it with the one published anchor.

## 7. Combines with

Every strategy (1, 3, 6, 7, 8, 9 are scored here); strategy 7 draws Pareto curves per hypothesis.

## 8. Results log

| Date | Who | Hypotheses implemented | Sanity tests | Notes |
|---|---|---|---|---|
| 2026-10-03 | Codex | H1, H1n5, H1n10, H2, H3w0.25, H3w0.5, H3w1, H4, H5 | 6 unittest cases pass; smoke test yields 1,600 grants for each hypothesis and 35/35 for a perfect simulated predictor | Paused when user prioritized OptiFrame. H6, registry, heatmap and notebook-split calibration remain unimplemented. See work/shared/README.md. |
