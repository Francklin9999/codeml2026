# EquiAlgo · Strategy 1: Counterfactual neutralisation (Pope–Sydnor)

| | |
|---|---|
| **Status** | NOT STARTED *(set to IN PROGRESS / DONE / ABANDONED with your name and the date)* |
| **Priority** | P1 (main bet for the automatic 35 points) |
| **Effort** | 2–3 h |
| **Depends on** | `work/shared/` from strategy 2 for evaluation (can start without it) |
| **Rubric lines** | Technical solution: equity 20 + utility 15 |
| **Work folder** | `equialgo-participants/work/strat1/` |

---

## 1. Context you need

- **Task:** decide grants for the 4,000 applicants in `data/candidats_evaluation.csv`; output `predictions.csv` (`id_candidat,decision_octroi`, 0/1).
- **Automatic scoring vs a hidden reference "built independently of the committee":** equity (20) = share of the baseline equal-opportunity gap **0.270** closed; utility (15) = agreement with the reference, scaled from a random budget-respecting draw (0) to perfect (15). **Both 0 if the grant rate is outside 36–44%** (1,440–1,760 grants).
- `decision_octroi` in `data/donnees_demandes.csv` (10,000 rows, 40% granted) is the **biased committee**, not the target.
- Groups: `Centre` = Montréal + Capitale-Nationale; `Eloignee` = Bas-Saint-Laurent, Côte-Nord, Gaspésie (as in `baseline_model.ipynb`). Candidates: 2,372 central, 1,628 remote.
- Verified: `code_postal_3` has 18 values and **each maps to exactly one region**, so it is a pure region proxy. Dropping region moves the parity gap only 0.188 → 0.181 (→ 0.173 without postal code).
- Analysis probe (`ANALYSE_CHALLENGES.md` §7.3.4): logistic regression on the committee, standardised coefficients cote R +4.13, hours +0.76, log income +0.74, remote −1.08; CV AUC 0.957. Neutralising remote and cutting at 40% gave in-sample grant rates 41.4% (central) vs 38.0% (remote), against 48.4% vs 27.3% historically.

## 2. The idea

Fit the committee's behaviour **with** the sensitive attribute, so the regional penalty is captured by the region term instead of leaking into proxies. At prediction time, **neutralise** region (everyone gets the same region value, or predictions are averaged over regions), rank, and grant exactly the top 1,600.

Reference: Pope & Sydnor (2011), *Implementing Anti-Discrimination Policies in Statistical Profiling Models*, AEJ: Economic Policy 3(3).

## 3. Why it could score

If the hidden reference is "the committee rule without the regional penalty" (the simplest way to build synthetic data independently of the committee), this reproduces it closely: high utility **and** most of the gap closed. Removing the column cannot do this because distance, hours, income and postal code re-learn the penalty.

## 4. Implementation plan

### 4.1 Setup

```bash
cd equialgo-participants
python -m venv ../.venv && ../.venv/Scripts/activate
pip install -r requirements.txt          # pandas, numpy, scikit-learn, fairlearn, matplotlib, jupyter, shap
mkdir -p work/strat1 work/shared
```

### 4.2 Files

```
work/strat1/
  neutralise.py         # fit, neutralise, rank, write predictions
  report_01.md
  predictions_01.csv    # candidate submission (copy to repo root only when chosen)
```

### 4.3 Feature construction (put it in `work/shared/data.py` so every strategy uses the same)

```python
REMOTE = ["Bas-Saint-Laurent", "Cote-Nord", "Gaspesie-Iles-de-la-Madeleine"]
def features(df, region_mode="remote_flag", include_postal=False):
    X = pd.DataFrame(index=df.index)
    X["cote_r"] = df.cote_r_equivalent
    X["log_rev"] = np.log(df.revenu_familial_estime); X["rev"] = df.revenu_familial_estime / 1e5
    X["heures"] = df.heures_travail_semaine
    X["log_dist"] = np.log1p(df.distance_domicile_campus_km); X["dist"] = df.distance_domicile_campus_km / 100
    X["premgen"] = df.premiere_generation_universitaire
    X = X.join(pd.get_dummies(df.programme_etudes, prefix="prog", drop_first=True).astype(float))
    if region_mode == "remote_flag":
        X["remote"] = df.region_administrative.isin(REMOTE).astype(float)
    else:  # five regions, Montreal as reference
        X = X.join(pd.get_dummies(df.region_administrative, prefix="reg").drop(columns="reg_Montreal").astype(float))
    if include_postal:
        X = X.join(pd.get_dummies(df.code_postal_3, prefix="cp", drop_first=True).astype(float))
    return X
```

Align candidate columns with `reindex(columns=X_train.columns, fill_value=0)` (the notebook warns about this).

### 4.4 Variants to implement

| Variant | Model | Region encoding | Postal code | Neutralisation |
|---|---|---|---|---|
| V1 (main) | LogisticRegression (standardised, C tuned by CV) | remote flag | excluded | set `remote = 0` |
| V2 | LogisticRegression | 5 region dummies | excluded | set all region dummies to 0 (Montréal) |
| V3 | LogisticRegression | 5 region dummies | included | set region **and** postal dummies to a central reference, or average over codes (see below) |
| V4 | HistGradientBoostingClassifier | remote flag | excluded | **average** predictions over remote ∈ {0,1} weighted by population share |
| V5 | V1 with interactions `remote × cote_r`, `remote × heures` | | | set remote = 0 (interactions vanish) |

Why postal code is excluded in V1: with both region and postal dummies, the penalty splits between them (they are collinear), and neutralising region alone leaves the postal part. V3 tests the fix.

Why averaging for V4: in a non-additive model, "set everyone to Montréal" and "set everyone to Côte-Nord" can rank differently; averaging over the protected attribute is the Pope–Sydnor recommendation for that case.

### 4.5 Ranking and budget

```python
p = model.predict_proba(X_cand_neutral)[:, 1]
order = np.lexsort((-cand.cote_r_equivalent.values, -p))   # ties broken by cote R
grant = np.zeros(len(cand), int); grant[order[:1600]] = 1
pd.DataFrame({"id_candidat": cand.id_candidat, "decision_octroi": grant}).to_csv("work/strat1/predictions_01.csv", index=False)
```

Then `python work/shared/validate_submission.py work/strat1/predictions_01.csv` (from strategy 2).

## 5. How to test it

There is no reference, so use three independent checks.

### 5.1 Simulator (primary, strategy 2)

`python work/shared/score.py --pred work/strat1/predictions_01.csv --all-hypotheses` → equity points, utility points and total /35 under H1–H6. Run for V1–V5.

### 5.2 Conditional parity check

Within cote R deciles (computed on candidates), grant rate remote vs central, before (committee model, no neutralisation) and after. After neutralisation the two curves should overlap; a residual gap means a proxy still carries the penalty.

```python
cand["decile"] = pd.qcut(cand.cote_r_equivalent, 10, labels=False)
print(cand.assign(g=grant).groupby(["decile", "remote"]).g.mean().unstack())
```

### 5.3 Stability

5-fold refits (fit on 4/5 of history) × 5 seeds: Jaccard overlap of granted sets ≥ 0.95. A low overlap means the ranking is fragile near the threshold.

### 5.4 Report (`report_01.md`)

CV AUC of the committee model (should be ≈ 0.95), coefficient table, group grant rates on candidates, conditional parity table, stability, simulator table for V1–V5.

### 5.5 Acceptance / kill

- **Adopt** the best variant as the submission if, in the simulator, it is best or within 1 point of best under the hypotheses that strategy 3 rates plausible.
- **Reject** a variant if the conditional parity check shows a remaining remote penalty > 3 points in most deciles.

## 6. Risks and guardrails

- If the reference also treats the positive effect of income or hours as bias, this variant under-corrects: see strategies 8 and 9.
- Using region at training time must be explained in governance (strategy 10): it is used to *remove* its effect, never to decide.

## 7. Combines with

Strategy 2 and 3 (evaluation and choice), 7 (partial neutralisation sweep = Pareto front), 9 (path-specific extension), 10 (pitch).

## 8. Results log

| Date | Who | Variant | Simulator total /35 (per H) | Conditional gap | Stability | Verdict |
|---|---|---|---|---|---|---|
| | | | | | | |
