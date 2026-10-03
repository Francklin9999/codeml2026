# EquiAlgo · Strategy 11: Label-bias correction before training (reweighing and "massaging" the committee labels)

| | |
|---|---|
| **Status** | NOT STARTED *(set to IN PROGRESS / DONE / ABANDONED with your name and the date)* |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | `work/shared/` harness from strategy 2 (simulator + scorer) |
| **Rubric lines** | Technical (35), Pareto front (several correction strengths), Diagnostic (25: shows how biased the labels are) |
| **Differs from 1–10** | Strategies 1, 7 and 9 correct the **model's predictions**. This corrects the **training labels** themselves (pre-processing), then trains an ordinary model on the repaired data |
| **Work folder** | `equialgo-participants/work/strat11/` |

---

## 1. Context you need

- Data: `data/donnees_demandes.csv` (10,000 historical applications, `decision_octroi` = biased committee, 40% granted; central 48.4% vs remote 27.3%), `data/candidats_evaluation.csv` (4,000 to decide).
- Scoring: 35 automatic points vs a hidden reference built independently of the committee (equity 20 = share of the baseline EO gap 0.270 closed; utility 15 = agreement scaled between random and perfect; **0 if grant rate outside 36–44%**). Groups: `Centre` (Montréal, Capitale-Nationale) vs `Eloignee` (Bas-Saint-Laurent, Côte-Nord, Gaspésie).
- `code_postal_3` maps one-to-one to region (verified); distance, hours, income also carry region.

## 2. The idea

Two classic pre-processing methods (Kamiran & Calders, 2012):

1. **Reweighing:** give each (group, label) cell a weight `w = P(group)·P(label) / P(group, label)` so that, in the weighted data, label and group are independent; train with `sample_weight`.
2. **Massaging (label flipping):** rank applicants with a committee model that **excludes** region (and postal code); flip the labels of the remote applicants just *below* the boundary from 0 to 1 and of central applicants just *above* it from 1 to 0, until a target (e.g. equal conditional grant rates within cote-R bands, or parity) is met. Variant used here: **merit-conditional massaging**, flipping only within cote-R deciles so merit differences are preserved.

Then train a standard classifier on the repaired data, rank candidates, grant the top 1,600.

## 3. Why it could score

If the reference is "committee without the regional penalty", repairing the labels and training normally is another route to it, with different failure modes than strategy 1 (no need to model region explicitly at prediction time; the final model never sees region). The amount of flipping is also a clean **Pareto knob** and a vivid diagnostic ("N remote applicants would have been granted without the penalty").

## 4. Implementation plan

### 4.1 Files

```
work/strat11/
  reweigh.py
  massage.py
  train_repaired.py      # model on repaired data → candidate predictions (1,600 grants)
  sweep_flip.py          # amount of flipping as a Pareto parameter
  report_11.md
```

### 4.2 Massaging algorithm (merit-conditional)

```python
# 1) promotion/demotion ranker without region or postal code
ranker = LogisticRegression().fit(X_noregion, y)
s = ranker.predict_proba(X_noregion)[:, 1]
# 2) within each cote-R decile d: target = central grant rate in d
for d in deciles:
    R = idx[(remote) & (decile == d)]; C = idx[(~remote) & (decile == d)]
    gap = y[C].mean() - y[R].mean()
    n_flip = int(round(fraction * gap * len(R)))           # fraction ∈ [0, 1] = sweep parameter
    promote = R[(y[R] == 0)][np.argsort(-s[R][y[R] == 0])][:n_flip]   # best-scored refused remote
    y_rep[promote] = 1
    # keep total grants fixed: demote the lowest-scored granted central in the same decile
    demote = C[(y[C] == 1)][np.argsort(s[C][y[C] == 1])][:n_flip]
    y_rep[demote] = 0
```

Keep the overall historical grant rate at 40% after repair.

### 4.3 Training on repaired data

Logistic regression and gradient boosting **without** region and postal code (the labels already carry the correction); compare with versions that include them. Rank candidates, top 1,600, tie-break by cote R.

### 4.4 Sweep

`fraction` ∈ {0, 0.25, 0.5, 0.75, 1.0, 1.25}; record group rates and simulated scores for the Pareto chart (strategy 7 can overlay it).

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Repair sanity | after full massaging, conditional grant rates per cote-R decile are equal across groups (± 1 pt); total grant rate still 40% |
| T2 | Reweighing sanity | weighted P(label \| group) equal across groups |
| T3 | Simulator | equity + utility under hypotheses H1–H6 (strategy 2), for each `fraction` and for reweighing |
| T4 | Comparison | vs strategy 1 (counterfactual neutralisation) on the same table |
| T5 | Budget | `validate_submission.py` passes |

**Adopt** if it beats or ties strategy 1 under the plausible hypotheses (strategy 3's weights) or is more robust (smaller worst case). Otherwise keep it as a Pareto curve and a diagnostic figure.

## 6. Risks

The ranker used for massaging still learns proxy-borne penalties (it excludes region but not distance). Variant: use strategy 1's neutralised scores as the ranker.

## 7. Combines with

Strategy 2 (scoring), 7 (Pareto overlay), 4 (diagnostic: count of "missing" remote grants), 10 (pitch).

## 8. Results log

| Date | Who | Method / fraction | Group rates (C / R) | Sim. total /35 (weighted) | Verdict |
|---|---|---|---|---|---|
| | | | | | |
