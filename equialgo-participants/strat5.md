# EquiAlgo · Strategy 5: Proxy audit (per-feature AUC, mutual information, SHAP, drop tests)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 2–3 h |
| **Depends on** | `work/shared/data.py` |
| **Rubric lines** | Diagnostic rigour (25); deliverable "the proxy variables you found" in `audit_rapport.ipynb` |
| **Work folder** | `equialgo-participants/work/strat5/` |

---

## 1. Context you need

The brief: *"Deleting `region_administrative` does not work. Dropping it moves the parity gap from 0.188 to 0.181. Dropping the postal code as well moves it to 0.173. Distance, hours worked, household income and postal code all carry regional information. Section 5 of the notebook measures this."* Verified: the 18 postal codes each map to exactly one region.

## 2. The idea

Measure feature by feature how much regional information each variable carries, show why dropping region cannot work, and rank proxies on two axes: **proxy strength** and **legitimacy** (is there a defensible reason to use it in a scholarship decision?). The result decides which features to neutralise (strategy 9).

## 3. Why it could score

The deliverable explicitly asks for the proxies found. A "strength × legitimacy" matrix is the bridge from diagnosis to mitigation, which juries reward.

## 4. Implementation plan

### 4.1 Files

```
work/strat5/
  proxy_audit.ipynb
  proxy_table.csv
  fig_proxy_auc.png  fig_shap_summary.png  fig_shap_dependence_distance.png
  psi_table.csv
```

### 4.2 Univariate proxy strength

For each feature: AUC of predicting `remote` from that feature alone (5-fold CV logistic regression; for categorical features one-hot), and mutual information with the 5-class region (`sklearn.feature_selection.mutual_info_classif`, discrete flags set correctly). Expected order (to verify): postal code (perfect) > distance > hours ≈ first-gen > income > programme ≈ cote R.

### 4.3 Multivariate leakage

1. AUC of predicting region (2-group and 5-class macro AUC) from **all non-region features** with a GBM.
2. Leave-one-feature-out: drop each feature in turn and measure the AUC drop → which features carry the information jointly.
3. Same with postal code and distance removed: how much regional signal remains in hours, income and first-gen?

### 4.4 Model attribution on the baseline

SHAP `TreeExplainer` on the notebook's RandomForest (all columns): mean |SHAP| per feature, by group; dependence plots for distance and hours coloured by group. Shows what the production model actually leans on.

### 4.5 Drop tests (reproduce, then extend)

Reproduce the notebook's section 5 exactly (same split, seed, RF) → 0.188 / 0.181 / 0.173. Then extend: drop distance; drop all proxies (region, postal, distance, hours, income); keep only cote R + programme. Report parity gap, EO gap vs committee labels, and accuracy vs committee for each.

### 4.6 Legitimacy column (write the argument, one line each)

| Feature | Proxy strength | Legitimacy argument | Proposed treatment |
|---|---|---|---|
| region | — (the attribute) | none for deciding | use in training only, neutralise (strategy 1) |
| postal code | perfect | none beyond region | drop |
| distance | very high | weak (cost of studying away could justify need-based aid, but it is mostly geography) | neutralise or drop (strategy 9 tests both) |
| hours worked | moderate | plausible need indicator | keep, or test neutralising its regional component |
| income | to measure | plausible need indicator (note: the committee rewards *higher* income, which is suspicious) | keep, flag the sign |
| first-gen | moderate | defensible equity factor | keep |
| cote R | low | merit, core criterion | keep |

### 4.7 Distribution shift (monitoring baseline)

PSI per feature, historical vs candidates, overall and per group (10 quantile bins from history). Becomes the baseline for strategy 10's monitoring plan.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Reproduction | the three drop-test gaps match the brief to 3 decimals (if not, find out why before continuing) |
| T2 | Postal check | postal code alone predicts region with AUC = 1.0 |
| T3 | Table complete | every feature has AUC, MI, mean \|SHAP\|, legitimacy line, treatment |
| T4 | Key chart | one figure showing "dropping region doesn't move the gap; distance + postal predict region almost perfectly" |

## 6. Risks

Mistaking correlation with region for illegitimacy. Keep the legitimacy column as an argued judgement, not a statistic.

## 7. Combines with

Strategy 4 (decomposition), 9 (which paths to neutralise), 10 (monitoring baseline, pitch slide 2).

## 8. Results log

| Date | Who | Reproduced 0.188/0.181/0.173? | Strongest proxies | Notes |
|---|---|---|---|---|
| | | | | |
