# EquiAlgo · Strategy 18: Counterfactual explanations and recourse parity per applicant

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (governance differentiator) |
| **Effort** | 3 h |
| **Depends on** | the chosen model (strategy 1 or 15) |
| **Rubric lines** | Governance & ethics (25: transparency, contestability, Law 25 explanation duty), Diagnostic (25: recourse gap by region), Pitch |
| **Differs from 1–10** | Strategy 10 describes governance at the system level. This produces **individual explanations** ("what would have changed the decision") and measures whether the **cost of recourse** differs by region before and after the fix |
| **Work folder** | `equialgo-participants/work/strat18/` |

---

## 1. Context you need

- See strategy 1 §1.
- Recourse literature: Ustun, Spangher & Liu (2019), *Actionable Recourse in Linear Classification*; Wachter et al. (2017) counterfactual explanations. Recourse must only use **actionable** features (a student can raise their cote R slightly or change hours worked; cannot change region, first-generation status, or past income).
- Québec privacy law (Law 25, s. 12.1, verify): people subject to an automated decision can be told the main factors and submit observations.

## 2. The idea

1. For every refused candidate, compute the **minimal actionable change** that would flip the decision under the final model (e.g. "+0.6 cote R" or "−4 h of work per week"), with a cost function in plain units.
2. Compare the **distribution of recourse cost by region** for the committee-like model vs our corrected model. A fair system should not require remote applicants to "do more" for the same outcome.
3. Generate a **plain-language explanation letter** template per decision: main factors, recourse, how to submit observations.

## 3. Why it could score

Recourse parity is a crisp, quantitative fairness argument the jury rarely sees, and explanation letters are a concrete governance deliverable.

## 4. Implementation plan

### 4.1 Files

```
work/strat18/
  recourse.py           # minimal flips under linear (exact) or general models (search)
  recourse_parity.py    # cost distributions by region, before/after
  letter_template.md    # FR explanation + recourse + review route
  report_18.md
```

### 4.2 Recourse computation

- **Linear / scorecard model (exact):** with score `w·x` and cut-off `c`, the minimal change along actionable feature j is `(c − w·x) / w_j`, capped by feasibility bounds (cote R ≤ 40, hours ≥ 0). Combine features with a weighted L1 cost; solve as a small integer / linear program (`scipy.optimize.linprog` or `pulp`).
- **Non-linear model:** DiCE (`dice-ml`) or a simple grid search over actionable features.
- Actionable set and costs (document them): cote R (cost per 0.1 point), hours worked (cost per hour reduced, bounded by a minimum need), programme (not actionable for the cycle).

### 4.3 Parity analysis

Median and 90th percentile recourse cost by region (5 regions and 2 blocks) for: committee-like model (with penalty), baseline RF (via search), corrected model. Plot CDFs.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Correctness | applying the recourse to each refused applicant flips the decision (100% of a 200-sample) |
| T2 | Minimality (linear) | no cheaper flip found by brute-force grid on a 50-sample |
| T3 | Parity result | remote vs central median recourse cost gap shrinks after the fix (report numbers) |
| T4 | Letters | 3 example letters reviewed by a teammate for clarity; no mention of region as a factor |

## 6. Risks

Recourse can look like advice to "work fewer hours" which may be unrealistic; frame it as explanation of the rule, and include a review route.

## 7. Combines with

Strategy 15 (scorecard makes recourse exact), 10 (governance), 1 (model).

## 8. Results log

| Date | Who | Model | Median cost C / R (before) | Median cost C / R (after) | Notes |
|---|---|---|---|---|---|
| | | | | | |
