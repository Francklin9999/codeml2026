# EquiAlgo · Strategy 6: Fairlearn control arm (ThresholdOptimizer / ExponentiatedGradient)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (control: what most teams will submit) |
| **Effort** | 2–3 h |
| **Depends on** | strategy 2 (scorer) |
| **Rubric lines** | Technical (comparison), Pareto-front deliverable, Pitch ("why not just use the tool?") |
| **Work folder** | `equialgo-participants/work/strat6/` |

---

## 1. Context you need

The brief suggests `fairlearn.postprocessing.ThresholdOptimizer` ("adjusts decision thresholds after training and runs in seconds") and `fairlearn.reductions.ExponentiatedGradient` ("retrains under a constraint and takes minutes"), and requires a Pareto front over several constraint settings. Key weakness: fairlearn equalises rates **relative to the labels it is trained on**, here the biased committee decisions, not the hidden reference.

## 2. The idea

Implement both tools with equal-opportunity constraints, sweep the constraint, plot the front, and score every point in the simulator. Use the result as the **control arm**: if our main bet (strategy 1) does not beat it, we must know.

## 3. Why it matters

It gives a fair comparison, a quick Pareto front, and a strong pitch point when we show that "TPR parity measured against the committee" and "TPR parity against a plausible reference" disagree.

## 4. Implementation plan

### 4.1 Files

```
work/strat6/
  fairlearn_control.py
  pareto_fairlearn.png
  fairlearn_vs_simulator.csv
```

### 4.2 ThresholdOptimizer

```python
from fairlearn.postprocessing import ThresholdOptimizer
to = ThresholdOptimizer(estimator=base, constraints="true_positive_rate_parity",
                        objective="balanced_accuracy_score", predict_method="predict_proba",
                        prefit=True)
to.fit(X_hist, y_hist, sensitive_features=group_hist)
```

Its output rate is not controlled. Budget wrapper: extract the group-specific thresholds `t_g` from `to.interpolated_thresholder_`, then shift them jointly by a common offset δ (bisection) until exactly 1,600 candidates are granted; or convert to a score `s_i − t_{g(i)}` and rank-cut at 1,600. Randomised thresholds: fix `random_state` for reproducibility.

### 4.3 ExponentiatedGradient

```python
from fairlearn.reductions import ExponentiatedGradient, TruePositiveRateParity, EqualizedOdds
for eps in [0.005, 0.01, 0.02, 0.05, 0.1, 0.2]:
    eg = ExponentiatedGradient(LogisticRegression(max_iter=2000), TruePositiveRateParity(difference_bound=eps))
    eg.fit(X_hist, y_hist, sensitive_features=group_hist)
    s = eg._pmf_predict(X_cand)[:, 1]          # randomised classifier probabilities
    grant = top_k(s, 1600)
```

Also run `EqualizedOdds` for comparison. Base learner: logistic regression (fast); RF only if time allows.

### 4.4 Variants

Sensitive feature = 2 groups and = 5 regions; features with and without region/postal (fairlearn does not need region as a feature).

### 4.5 Two Pareto views

1. **What fairlearn sees:** x = EO gap vs committee labels, y = accuracy vs committee labels.
2. **What the grader would see (simulated):** x = EO gap vs simulated reference H1 (and others), y = utility points.
Plot strategy 1 (and strategy 7's α-curve) on the same axes.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Budget | every configuration passes `validate_submission.py` (exactly 1,600) |
| T2 | Front | ≥ 6 settings per tool, monotone-ish front |
| T3 | Simulator table | best fairlearn config vs strategy 1 under each hypothesis; verdict sentence |
| T4 | Diagnostic chart | view 1 vs view 2 disagreement visible |
| T5 | Runtime | ExponentiatedGradient ≤ 15 min per setting; otherwise restrict to ThresholdOptimizer |

## 6. Risks

Spending time tuning a control. Cap at the effort estimate.

## 7. Combines with

Strategy 2 (scoring), 7 (joint Pareto chart), 10 (pitch argument).

## 8. Results log

| Date | Who | Tool / ε | EO gap (committee) | Sim. total /35 (H1, H6) | Notes |
|---|---|---|---|---|---|
| | | | | | |
