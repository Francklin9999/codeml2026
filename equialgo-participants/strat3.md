# EquiAlgo · Strategy 3: Calibrate reference hypotheses on the 0.270 anchor (+ leaderboard probing if allowed)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (de-risks the choice of submission) |
| **Effort** | 2 h (anchor) + 1–2 h (probing) |
| **Depends on** | strategy 2 (hypotheses + scorer) |
| **Rubric lines** | Technical (35), indirectly: picks the right variant |
| **Work folder** | `equialgo-participants/work/strat3/` |

---

## 1. Context you need

- The brief publishes **one number measured against the hidden reference**: the baseline model's equal-opportunity gap = **0.270**.
- Other published numbers (88% accuracy, 48.4% vs 27.3%, parity gaps 0.188 / 0.181 / 0.173) are measured against the **committee**, not the reference.
- The English brief: *"HxBuddy only displays indicative F1 and accuracy metrics for this challenge. It does not calculate the 35 points."* The 4,000 candidates have no public labels, so those indicative metrics must be computed against some hidden label (most likely the reference, possibly a hidden committee decision).

## 2. The idea

**Part A:** under each hypothesis from strategy 2, recompute the baseline's EO gap and compare it with 0.270. Hypotheses that land near 0.270 become more plausible. **Part B (only if the rules allow several submissions):** use a few designed submissions whose indicative F1/accuracy discriminates between hypotheses.

## 3. Why it could score

It turns "the reference is unknown" into a small set of weighted hypotheses, which decides between strategies 1, 8 and 9 (and the α of strategy 7) on evidence instead of taste.

## 4. Implementation plan

### 4.1 Files

```
work/strat3/
  anchor_calibration.py
  anchor_table.csv
  hypothesis_weights.json      # consumed by strategies 7 and 8
  probing_plan.md
  probing_log.csv              # only if Part B is done
```

### 4.2 Part A: anchor calibration

1. Reproduce the notebook baseline exactly, in two settings:
   - **S-final:** cell 17 (RF trained on all 10k, predicts the 4k candidates).
   - **S-split:** cell 8 (70/30 split, `random_state=42`, stratified), predictions on the 3k test rows.
2. For each hypothesis H (and noise level) and each setting, compute `gap_H = |TPR_Centre − TPR_Eloignee|` of the baseline predictions vs the simulated reference. Also the 5-region max−min variant.
3. Bootstrap (1,000 resamples of candidates) → 95% CI of `gap_H`.
4. Plausibility weight: `w_H ∝ exp(−(gap_H − 0.270)² / (2σ_H²))`, normalised, with σ_H the bootstrap SD. Write `hypothesis_weights.json`.
5. For H6 (latent generator), also scan the penalty π and noise scales: which (π, noise) produce a baseline gap of 0.270 while reproducing the committee's 48.4 / 27.3 rates? That pins down how strong the "true" penalty is.

```python
for H in hypotheses:
    y_ref = H.reference(cand)
    g = eo_gap(y_ref, baseline_pred_cand, group_cand)
    boot = [eo_gap(y_ref[i], baseline_pred_cand[i], group_cand[i]) for i in bootstrap_indices(4000, 1000)]
    rows.append((H.id, g, np.percentile(boot, 2.5), np.percentile(boot, 97.5)))
```

### 4.3 Part B: leaderboard probing (only if allowed)

1. **Ask the organisers first:** how many submissions? Which label are HxBuddy's F1/accuracy computed against? Is probing acceptable? Document the answer in `probing_plan.md`. Never try to recover individual labels.
2. Designed submissions, each exactly 1,600 grants:
   - S1 baseline RF rescaled; S2 neutralised (strategy 1 V1); S3 merit-only (H2); S4 merit + need (H3, w = 0.5).
3. Predict, for each hypothesis, the F1/accuracy each submission would get (from the simulator). Compare the **observed ordering and gaps** with each hypothesis's predicted ones; update the weights (likelihood ∝ exp(−Σ (obs − pred)² / 2s²)).
4. Optional paired design (if submissions are plentiful): S2 vs S2′ that differ only on ~150 remote borderline candidates; the accuracy difference estimates the reference positive rate in that slice.
5. Always keep one submission slot for the final choice.

## 5. How to test it

| Output | Pass if |
|---|---|
| `anchor_table.csv` | gap per H × setting × grouping with CIs |
| Informativeness | at least one hypothesis family's CI contains 0.270 and at least one excludes it (otherwise the anchor is not informative: say so) |
| Reproduction | the baseline reproduced here gives the notebook's 88% accuracy and 0.188 parity gap on S-split |
| Decision | the recommended submission is best under the weighted mixture in strategy 2's scorer |

**Kill (Part A):** if every hypothesis gives ≈ 0.27, the anchor carries no information; fall back to strategy 8 (robust choice) and state it.

## 6. Risks

Burning allowed submissions or breaking a rule. Ask first; log every probe.

## 7. Combines with

Strategy 2 (simulator), 7 and 8 (use the weights), 1 and 9 (variant choice), 10 (governance: we state our uncertainty about the reference).

## 8. Results log

| Date | Who | Setting | Best-matching hypotheses | Weights | Probes used | Verdict |
|---|---|---|---|---|---|---|
| | | | | | | |
