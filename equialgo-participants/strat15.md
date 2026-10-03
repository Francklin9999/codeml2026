# EquiAlgo · Strategy 15: Transparent integer scorecard (explainable allocation rule)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (governance and pitch value; competitive if the reference is a simple rule) |
| **Effort** | 2–3 h |
| **Depends on** | strategy 1 (neutralised model) for the weights; strategy 2 for scoring |
| **Rubric lines** | Governance & ethics (25: explainability, contestability), Pitch (15), Technical (35) |
| **Differs from 1–10** | All other strategies output decisions from a statistical model. This converts the corrected model into a **points-based scorecard** that an applicant, a committee member or an auditor can compute by hand, like credit scorecards |
| **Work folder** | `equialgo-participants/work/strat15/` |

---

## 1. Context you need

- See strategy 1 §1 for data, scoring and groups.
- The governance criterion rewards explainability and accountability. Québec's private-sector privacy act (as amended by Law 25, s. 12.1, verify wording) requires that people subject to an exclusively automated decision can learn the main factors and submit observations to someone who can review it. A scorecard makes this trivial.
- The analysis probe: the committee is essentially linear (logistic AUC 0.957 vs GBM 0.951), so a scorecard loses little.

## 2. The idea

1. Start from the neutralised logistic model (strategy 1 V1, region removed).
2. **Bin** each legitimate feature into a few interpretable bands (cote R in 1-point bands; income quintiles; hours 0–5, 6–10, 11–15, 16–20, 21+; first-gen yes/no; programme).
3. Fit a logistic model on the binned features (or derive points from the continuous model), then **scale and round** the coefficients to integer points (e.g. 20 points = doubling of odds), as in standard scorecard practice (Siddiqi, *Credit Risk Scorecards*).
4. Total points → rank → grant top 1,600 (equivalently a cut-off score).
5. Publish the scorecard as one table.

Optional variant: a **sparse integer model** learned directly (e.g. RiskSLIM / FasterRisk-style) with at most 5–7 items.

## 3. Why it could score

It is the most defensible artefact for the governance jury ("here is the whole rule on one page"), easy to monitor and contest, and nearly as accurate as the model if the committee is linear.

## 4. Implementation plan

### 4.1 Files

```
work/strat15/
  binning.py           # bands per feature (monotonic where justified)
  scorecard.py         # binned logistic → points → cut-off
  scorecard_table.md   # the published rule
  report_15.md
```

### 4.2 Points scaling

```python
PDO, base_points, base_odds = 20, 600, 1/1.5      # 20 points doubles the odds
factor = PDO / np.log(2); offset = base_points - factor * np.log(base_odds)
points_band = np.round(-factor * coef_band)        # sign convention: higher points = more likely granted
```

Check monotonicity of points across ordered bands (e.g. more cote R never gives fewer points); merge bands that violate it.

### 4.3 Neutrality

Region, postal code and (in the main variant) distance are **not** in the scorecard. Variant: include distance as a need item if strategy 9 / 5 conclude it is legitimate.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Fidelity | agreement between scorecard decisions and strategy 1's decisions on candidates ≥ 95% |
| T2 | Simulator | equity / utility under H1–H6 within 1 point of strategy 1, or better |
| T3 | Monotonicity | all ordered features monotone in points |
| T4 | Hand-computation test | a teammate computes 5 applicants' scores by hand from the table, matches the code |
| T5 | Conditional parity | grant rates by group within cote-R deciles (as in strategy 1 §5.2) |

## 6. Risks

Rounding can create many ties at the cut-off: break ties by cote R and document it.

## 7. Combines with

Strategy 1 (weights), 10 (model card, Law 25 explanation route), 18 (recourse is simple with a scorecard).

## 8. Results log

| Date | Who | Items | Fidelity vs strat 1 | Sim. total /35 | Verdict |
|---|---|---|---|---|---|
| | | | | | |
