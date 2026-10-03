# EquiAlgo · Strategy 19: Allocation as a constrained optimisation (linear / integer programming)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | calibrated "deserving" probabilities (from strategy 1, 11 or 12); strategy 2 (simulator) |
| **Rubric lines** | Technical (35), Pareto front (constraint tightness), Governance (explicit objective and constraints) |
| **Differs from 1–10** | Other strategies rank by a score and cut at 1,600. This **optimises the 4,000 decisions directly**: maximise expected number of deserving applicants funded subject to the budget **and** an explicit equal-opportunity constraint, solved exactly with an LP / ILP |
| **Work folder** | `equialgo-participants/work/strat19/` |

---

## 1. Context you need

- See strategy 1 §1. Budget: 1,440–1,760 grants (target 1,600). Equity points measure the TPR gap between `Centre` and `Eloignee` with respect to the reference ("deserving").
- If we have, for each candidate, an estimate `p_i = P(deserving_i = 1)` (from a debiased model), then the expected TPR of group g is `Σ_{i∈g} p_i x_i / Σ_{i∈g} p_i`, which is **linear in the decisions x_i**.

## 2. The idea

Solve:

```
maximise   Σ_i p_i x_i                                  (expected deserving applicants funded)
subject to Σ_i x_i = 1600                               (budget)
           | TPR_C(x) − TPR_R(x) | ≤ δ                   (equal opportunity, linear with fixed denominators)
           x_i ∈ {0, 1}  (or [0, 1] relaxed, then rounded)
```

Sweep δ to get an exact Pareto front between expected utility and expected EO gap. Because the constraint uses `p_i` from a debiased model, the EO constraint targets the plausible reference, not the biased labels.

## 3. Why it could score

It makes the objective and the fairness constraint explicit and auditable ("we maximise expected merit funded under a budget and an equal-opportunity tolerance δ"), provides the optimal decisions for a given `p`, and gives an exact Pareto front.

## 4. Implementation plan

### 4.1 Files

```
work/strat19/
  probs.py             # calibrated p_i (isotonic on CV predictions) from the chosen debiased model
  allocate.py          # LP/ILP with pulp (CBC) or OR-Tools; δ sweep
  report_19.md
```

### 4.2 Formulation details

- Denominators `D_C = Σ_{i∈C} p_i`, `D_R = Σ_{i∈R} p_i` are constants → constraints `Σ_C p_i x_i / D_C − Σ_R p_i x_i / D_R ≤ δ` and `≥ −δ`.
- ILP with 4,000 binaries and 3 constraints solves in seconds with CBC; the LP relaxation is nearly integral (at most a couple of fractional variables), round them by cote R.
- Variants: maximise expected **accuracy** vs reference instead of expected TP (adds `(1 − p_i)(1 − x_i)` terms; still linear); 5-region constraints (pairwise or max-min).
- Calibration matters: use isotonic calibration on cross-validated predictions; check reliability.

### 4.3 Sources of p_i to compare

Strategy 1 neutralised model; strategy 11 repaired-label model; strategy 12 threshold-model posterior predictive.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Solver sanity | with δ = ∞ the solution equals "top 1,600 by p_i" |
| T2 | Constraint check | expected TPR gap of the solution ≤ δ (computed independently) |
| T3 | Simulator | equity / utility under H1–H6 across δ; compare with rank-and-cut of the same p |
| T4 | Calibration | ECE of p_i on held-out history ≤ 0.03 |
| T5 | Budget | exactly 1,600; `validate_submission.py` passes |

## 6. Risks

Everything rests on `p_i`; if it is biased, the constraint enforces the wrong thing. That is why three sources are compared.

## 7. Combines with

Strategy 1, 11, 12 (sources of p_i), 7 (Pareto overlay), 10 (explicit objective in governance).

## 8. Results log

| Date | Who | p source | δ | Expected TP | Sim. total /35 | Verdict |
|---|---|---|---|---|---|---|
| | | | | | | |
