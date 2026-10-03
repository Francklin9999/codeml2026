# EquiAlgo · Strategy 14: Merit-conditional score repair with optimal transport (post-processing on score distributions)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | a committee score (strategy 1's model without neutralisation, or the baseline RF probabilities); strategy 2 (simulator) |
| **Rubric lines** | Technical (35), Pareto front (repair strength t ∈ [0, 1]) |
| **Differs from 1–10** | Strategy 6 equalises **thresholds** (TPR) with fairlearn; strategy 9 maps **input features**. This maps **output scores**: within each cote-R band, the remote score distribution is transported onto the central one (fully or partially), so equally qualified applicants face the same score distribution regardless of region |
| **Work folder** | `equialgo-participants/work/strat14/` |

---

## 1. Context you need

See strategy 1 §1 for data, scoring and groups. Optimal transport in 1-D is just **quantile mapping**: a score at quantile q of its group's distribution is mapped to the quantile q of the target distribution.

## 2. The idea

1. Compute a committee score `s(x)` that includes all the committee's behaviour (biased).
2. Stratify applicants by **merit band** (cote-R deciles, optionally × programme).
3. Within each band, map remote scores onto the **central** score distribution of the same band (or the pooled band distribution) with strength `t`:
   `s'_i = (1 − t)·s_i + t·Q_target(F_remote,band(s_i))`
4. Rank all candidates by `s'`, grant the top 1,600.

At `t = 1`, remote and central applicants of the same merit band have identical score distributions: the regional penalty is removed **without** assuming a functional form for it, while ordering *within* each group (driven by income, hours, etc.) is preserved.

## 3. Why it could score

It is model-agnostic (works on the RF baseline's scores), robust to non-linear penalties, interpretable ("à mérite égal, même distribution de scores"), and naturally gives a Pareto knob `t`. It is the "geometric repair" idea of Feldman et al. (2015), applied to scores and conditioned on merit.

## 4. Implementation plan

### 4.1 Files

```
work/strat14/
  ot_repair.py        # fit band-wise quantile functions on history, apply to candidates
  sweep_t.py
  report_14.md
```

### 4.2 Details

- Fit the band quantile functions on the **historical** 10k scores (out-of-fold scores from 5-fold CV to avoid overfitting), apply them to candidate scores (bands defined with the historical decile edges).
- Target distribution options: central-band distribution (removes the penalty) or pooled-band distribution (meets halfway); report both.
- Bands: 10 cote-R deciles; check each band has ≥ 100 remote and ≥ 100 central applicants (merge bands if not).
- Smooth quantile functions (interpolate on 101 quantile points).

### 4.3 Sweep

`t` ∈ {0, 0.2, …, 1.0, 1.2} (t > 1 over-corrects; included for the Pareto picture).

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Repair check | at t = 1, KS test of remote vs central candidate scores within each band: p > 0.05 |
| T2 | Rank preservation | within-group, within-band ordering unchanged (Spearman = 1) |
| T3 | Simulator | equity / utility under H1–H6 per t; compare with strategy 1 and 6 |
| T4 | Base-score sensitivity | results with logistic vs RF base scores |
| T5 | Budget | `validate_submission.py` passes |

## 6. Risks

Band edges matter: too coarse leaves residual merit differences; too fine is noisy. Test 5, 10 and 20 bands.

## 7. Combines with

Strategy 2 (scoring), 7 (Pareto overlay), 8 (as another component), 10 (pitch: simple explanation).

## 8. Results log

| Date | Who | Base score / bands / target | t | Sim. total /35 (weighted) | Verdict |
|---|---|---|---|---|---|
| | | | | | |
