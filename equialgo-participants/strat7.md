# EquiAlgo · Strategy 7: Penalty-removal sweep (α-blend) Pareto front

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (required deliverable: Pareto front in `model_corrige`) |
| **Effort** | 2 h |
| **Depends on** | strategy 1 (committee model), 2 (scorer), 3 (weights) |
| **Rubric lines** | Pareto-front deliverable, Technical (35), Diagnostic |
| **Work folder** | `equialgo-participants/work/strat7/` |

---

## 1. Context you need

Deliverable: *"`model_corrige.py` or `.ipynb`. Your mitigation, with a Pareto front plot across several settings of the fairness constraint."* and *"A single model is not a Pareto front. Sweep the fairness constraint and plot the results."*

## 2. The idea

Use one interpretable knob: **α = fraction of the estimated regional penalty removed** from the committee score.

`logit_α(x) = logit_committee(x, region) − α · β_region(region)`

α = 0 reproduces the committee, α = 1 is full neutralisation (strategy 1), α > 1 over-corrects (useful if the reference also removes proxy-borne penalties). Grant the top 1,600 at every α.

## 3. Why it could score

The axis means something to a jury ("how much of the measured penalty do we remove?"), unlike an abstract ε, and plotted under each simulated hypothesis it shows where the optimum sits and how flat it is: the honest way to pick the final α.

## 4. Implementation plan

### 4.1 Files

```
work/strat7/
  alpha_sweep.py
  alpha_scores.csv
  pareto_alpha.png          # front per hypothesis
  total_vs_alpha.png        # weighted mixture score vs α
```

### 4.2 Sweep

```python
model = fit_committee_logit(hist, region_mode="remote_flag")      # strategy 1 V1
beta = model.coef_[0][col("remote")] / scaler.scale_[col("remote")]  # penalty on the logit scale (negative)
base_logit = model.decision_function(Xs_cand)                    # with the true region
for alpha in np.linspace(0, 1.5, 31):
    adj = base_logit - alpha * beta * cand_remote                # removes α of the penalty for remote applicants
    grant = top_k(adj, 1600, tiebreak=cand.cote_r_equivalent)
    record(alpha, grant)
```

For the 5-region model, apply α to each region coefficient relative to Montréal.

### 4.3 For each α, record

- group grant rates (central, remote) on candidates;
- EO gap and accuracy vs historical committee labels (in-sample and CV);
- equity, utility, total /35 under every hypothesis of strategy 2;
- the plausibility-weighted total using `work/strat3/hypothesis_weights.json`.

### 4.4 Plots

1. **Classic front:** x = EO gap (vs simulated reference), y = utility points; one curve per hypothesis, α annotated along the curves; fairlearn front (strategy 6) overlaid.
2. **Choice plot:** weighted total /35 vs α, with the per-hypothesis curves faded behind; mark the chosen α and the flat region (α where total ≥ max − 1).

### 4.5 Choice rule

Choose α maximising the weighted total; if the curve is flat, prefer the value closest to 1 (easiest to explain: "we remove the measured penalty").

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | α = 1 reproduces strategy 1 V1 exactly | identical predictions |
| T2 | α = 0 reproduces the committee model's top 1,600 | identical predictions |
| T3 | Smoothness | group rates monotone in α; if jagged, fix tie-breaking |
| T4 | Expected shape | under H1, utility peaks near α = 1; under H2/H4 the optimum shifts right |
| T5 | Deliverable | both plots render in `model_corrige.ipynb` with captions |

## 6. Risks

Over-reading small differences between α values. Report the flatness and prefer the explainable value.

## 7. Combines with

Strategy 1 (α = 1), 3 (weights), 6 (comparison curve), 10 (pitch figure).

## 8. Results log

| Date | Who | Best α (weighted) | Flat range | Total /35 at chosen α | Notes |
|---|---|---|---|---|---|
| | | | | | |
