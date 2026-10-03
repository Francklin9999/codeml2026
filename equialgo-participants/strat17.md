# EquiAlgo · Strategy 17: Intersectional fairness audit (region × first-generation × income × programme)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | the chosen mitigation's predictions; strategy 2's references for EO estimates |
| **Rubric lines** | Diagnostic rigour (25), Governance & ethics (25: "limites", intersectionality), Pitch |
| **Differs from 1–10** | Every other strategy looks at the two region blocks. This checks that our fix does not **hide or create** unfairness for subgroups (e.g. first-generation students from Côte-Nord, low-income students in Montréal), with multicalibration-style checks |
| **Work folder** | `equialgo-participants/work/strat17/` |

---

## 1. Context you need

- See strategy 1 §1. Historical profile: remote applicants are more often first-generation (≈ 44% vs 26%) and work more hours; historical grant rate is 37.4% for first-generation vs 41.3% otherwise. Five programmes with historical grant rates 36.5–42.8%.
- The analysis lists "intersectionality with first-gen / income" as a documented limit; a jury will likely ask.

## 2. The idea

Audit selection rates, conditional rates (within cote-R bands) and simulated EO / calibration across **intersections**: 5 regions × first-gen × income tercile × programme (only cells with enough people), for (a) the historical committee, (b) the baseline RF, (c) our corrected decisions. Flag cells where the correction makes things worse, and decide whether to act.

## 3. Why it could score

It shows rigour beyond the headline metric and pre-empts the question "did you just move the bias somewhere else?".

## 4. Implementation plan

### 4.1 Files

```
work/strat17/
  intersections.py     # cell definitions, minimum size, metrics
  report_17.md
  fig_heatmap_rates.png  fig_heatmap_delta.png
```

### 4.2 Metrics per cell

- Selection rate; selection rate conditional on cote-R decile (averaged with a common weighting, so cells are comparable).
- Under each simulated reference (strategy 2): TPR (equal opportunity) and precision.
- **Multicalibration-style check:** within each cell, compare the mean model score with the mean simulated-reference rate (bins of score); large deviations signal mis-calibration for that subgroup.
- Change vs baseline (delta heatmap).

### 4.3 Rules

- Minimum cell size: 100 historical / 40 candidate applicants, otherwise merge (e.g. income tercile → halves).
- Bonferroni or FDR correction when flagging significant differences (many cells).

### 4.4 If a problem appears

Options to test: adding an interaction to the neutralised model; per-region correction (5 regions instead of 2 blocks, strategy 1 V2); document as a limit if not fixable.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Coverage | ≥ 90% of applicants fall in reportable cells |
| T2 | Regression check | no cell's conditional selection rate decreases by > 5 pts vs the committee **unless** explained by removing an advantage the cell had from the penalty (e.g. central applicants) |
| T3 | Multicalibration | max cell calibration gap under H1 ≤ 0.05 (or documented) |
| T4 | Report | heatmaps + 3 findings in plain language for the audit notebook |

## 6. Risks

Small cells produce noise; keep minimum sizes and CIs.

## 7. Combines with

Strategy 10 (limits, monitoring by subgroup), 5 (proxies), 1 / 9 (possible refinements).

## 8. Results log

| Date | Who | Cells | Flags | Action taken | Notes |
|---|---|---|---|---|---|
| | | | | | |
