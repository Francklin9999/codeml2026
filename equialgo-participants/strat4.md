# EquiAlgo · Strategy 4: Gap decomposition (Oaxaca–Blinder, Fairlie, matching)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 3 h |
| **Depends on** | `work/shared/data.py` |
| **Rubric lines** | Diagnostic rigour (25); goes into `audit_rapport.ipynb` |
| **Work folder** | `equialgo-participants/work/strat4/` |

---

## 1. Context you need

The brief: central applicants are granted at 48.4%, remote at 27.3% (gap ≈ 21 points); mean cote R 28.0 vs 27.3 *"accounts for part of the 21-point gap. The rest is unexplained."* Regional profile (analysis §7.3.3): remote applicants work more hours (≈ 13 vs 9 h/week), live ≈ 205 km from campus vs ≈ 17 km, and are more often first-generation (≈ 44% vs 26%).

## 2. The idea

Answer "how much of the gap is unexplained?" quantitatively, with confidence intervals, using three methods that should agree:
1. **Oaxaca–Blinder** on a linear probability model (two-fold, several reference coefficient sets);
2. **Fairlie** decomposition for the logit (non-linear);
3. **Coarsened exact matching** as a model-free cross-check.

## 3. Why it could score

25 jury points are on diagnostic rigour. Most teams will stop at group rates and a correlation matrix. A decomposition with CIs, cross-checked three ways, is the answer an auditor expects and gives the pitch's headline number.

## 4. Implementation plan

### 4.1 Files

```
work/strat4/
  decomposition.ipynb      # cells to paste into audit_rapport.ipynb
  oaxaca.py  fairlie.py  matching.py
  decomposition_table.csv
  fig_waterfall.png  fig_conditional_curves.png
```

### 4.2 Oaxaca–Blinder (linear probability model)

```python
# y = decision_octroi; X = legitimate characteristics (cote R, income, hours, programme, first-gen, [distance])
bC = OLS(y_C, X_C).fit().params; bR = OLS(y_R, X_R).fit().params; bP = OLS(y, X).fit().params  # pooled (Neumark)
xC, xR = X_C.mean(), X_R.mean()
gap = y_C.mean() - y_R.mean()
explained_pooled   = (xC - xR) @ bP
unexplained_pooled = gap - explained_pooled
detailed = (xC - xR) * bP           # contribution per variable (group dummies of programme together)
```

Report three versions: reference = central coefficients, remote coefficients, pooled (Neumark, with a group dummy in the pooled regression, per Jann 2008). Packages: `statsmodels` (OLS) is enough; `oaxaca` in Stata-like form is not needed.

### 4.3 Fairlie (logit)

Fit the logit on the pooled sample (without the group term) and use the random-matching / random-ordering algorithm: draw a remote subsample matched in size to central, sort by predicted probability, swap variables one group at a time, average over 100 random orderings. Gives a non-linear detailed decomposition.

### 4.4 Matching check

Coarsened exact matching on: cote R (0.5-point bins), income quintile, hours bins (0–5, 6–10, 11–15, 16–20, 21+), programme, first-gen. **Do not match on distance** (it is the region proxy). Within matched strata, weighted difference in grant rates = model-free estimate of the unexplained gap. Report the share of rows matched.

### 4.5 Conditional curves

Grant rate vs cote R (binned) for both groups, with Wilson CIs. The vertical distance between the curves at equal cote R is the most legible chart for a jury.

### 4.6 Uncertainty

Bootstrap (1,000 resamples, stratified by group) for every component in all three methods.

### 4.7 Sensitivity: is distance legitimate?

Run each method twice: distance in the "legitimate" set, and distance excluded. Report both; this is a governance choice (distance is both a need indicator and a region proxy) and connects to strategy 9.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Additivity | explained + unexplained = total gap (to rounding) in each method |
| T2 | Cross-method agreement | unexplained share from Oaxaca (pooled), Fairlie and matching within each other's 95% CIs; if not, explain why |
| T3 | Reference sensitivity | the three Oaxaca references differ by < 3 points, or the difference is reported |
| T4 | Synthetic check | on a simulated dataset with a known penalty (strategy 2's H6 generator, π known), the decomposition recovers π's effect within its CI |
| T5 | Headline | one sentence "≈ N of the 21.1 points are unexplained (95% CI [a, b])", robust across methods |

## 6. Risks

The decomposition is descriptive, not causal; say so. "Unexplained" is not automatically discrimination if variables are omitted, but with synthetic data and 9 features the argument is strong.

## 7. Combines with

Strategy 5 (proxies), 9 (legitimacy of distance), 10 (pitch headline and audit report).

## 8. Results log

| Date | Who | Method | Unexplained (pts) | 95% CI | Notes |
|---|---|---|---|---|---|
| | | | | | |
