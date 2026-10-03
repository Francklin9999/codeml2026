# EquiAlgo · Strategy 16: Predictive multiplicity audit (Rashomon set) and a borderline-decision policy

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Depends on** | strategy 1 (main model family), strategy 2 (simulator) |
| **Rubric lines** | Governance & ethics (25: human review, contestability), Diagnostic (25), Technical (35: a more stable submission) |
| **Differs from 1–10** | Other strategies pick one model. This measures how many applicants' decisions **flip across equally good models** (the "Rashomon set"), and defines a principled policy for those borderline applicants (human review band, stability-based tie-breaking) |
| **Work folder** | `equialgo-participants/work/strat16/` |

---

## 1. Context you need

- See strategy 1 §1. With 4,000 candidates and a hard budget of 1,600 grants, the applicants ranked around 1,500–1,700 are decided by tiny score differences that depend on arbitrary modelling choices (seed, regularisation, feature transform).
- Literature: Marx, Calmon & Ustun (2020), *Predictive Multiplicity in Classification*; Breiman's "Rashomon effect".

## 2. The idea

1. Build a **Rashomon set**: many models whose validation performance (vs the committee, after neutralisation) is within ε of the best: different seeds, regularisation strengths, feature transforms, bootstrap resamples, model families, and the plausible penalty range from strategy 12.
2. For each candidate, compute the **grant frequency** across the set (0–100%).
3. Classify: *stable grant* (≥ 95%), *stable refusal* (≤ 5%), *ambiguous* (between).
4. Policy for the submission: grant all stable grants; fill the remaining budget among ambiguous applicants by **highest grant frequency** (consensus ranking), which maximises expected agreement with whatever the "true" model is.
5. Governance policy for production: ambiguous applicants go to a **human review panel blind to region**; report the ambiguity rate by region (it should not be concentrated in remote regions after the fix).

## 3. Why it could score

It turns modelling uncertainty into a concrete governance mechanism (who gets human review and why), produces a more stable submission, and gives the jury an honest number ("X% of decisions are model-dependent").

## 4. Implementation plan

### 4.1 Files

```
work/strat16/
  rashomon.py          # trains the model set, stores candidate decisions matrix (n_models × 4000)
  multiplicity.py      # grant frequency, ambiguity stats by region
  consensus_submit.py  # policy above → predictions_16.csv
  report_16.md
```

### 4.2 Building the set

- 200 models: logistic with C ∈ {0.01…100}, with/without log transforms, 5 bootstrap resamples each, GBM with a few settings; neutralisation as in strategy 1; optionally penalty values sampled from strategy 12's posterior.
- Keep models with CV log-loss within ε (e.g. 1%) of the best.

### 4.3 Outputs

Histogram of grant frequency; ambiguity rate overall and by region; list size of the human-review band; consensus submission.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Set validity | all kept models within ε of the best CV loss |
| T2 | Ambiguity stats | ambiguity rate reported overall and by region with bootstrap CIs |
| T3 | Simulator | consensus submission vs single best model under H1–H6: equal or better mean, smaller variance |
| T4 | Fairness of ambiguity | ambiguity rate per region within ± 3 pts of each other after the fix (otherwise discuss) |
| T5 | Budget | exactly 1,600 grants; `validate_submission.py` passes |

## 6. Risks

ε choice drives everything; show results for 2–3 values.

## 7. Combines with

Strategy 1, 12 (penalty posterior), 10 (human-review design), 8 (robustness theme).

## 8. Results log

| Date | Who | Models kept | Ambiguous % (C / R) | Sim. mean / SD | Verdict |
|---|---|---|---|---|---|
| | | | | | |
