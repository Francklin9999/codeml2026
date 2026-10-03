# EquiAlgo · Strategy 8: Minimax-robust ensemble across reference hypotheses

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (hedge) |
| **Effort** | 3 h |
| **Depends on** | strategy 2 (simulator), 3 (weights); components from 1 and 9 |
| **Rubric lines** | Technical (35) |
| **Work folder** | `equialgo-participants/work/strat8/` |

---

## 1. Context you need

The reference is hidden. Strategies 1, 9 and a merit-only rule are each optimal under different hypotheses (H1, H4, H2/H3 in strategy 2). If strategy 3's anchor calibration is not decisive, betting on one hypothesis is risky.

## 2. The idea

Build the submission that maximises the **worst-case** (or the plausibility-weighted **expected**) simulated score across hypotheses, by combining hypothesis-specific rankings.

## 3. Why it could score

The 35 automatic points are the only objective part of the grade. A predictor that is near-best everywhere can beat one that is best under a single hypothesis and poor under others.

## 4. Implementation plan

### 4.1 Files

```
work/strat8/
  robust_blend.py
  blend_table.csv
  predictions_08.csv
```

### 4.2 Components (scores on the 4k candidates)

| ID | Score | Optimal under |
|---|---|---|
| R1 | neutralised committee logit (strategy 1 V1) | H1 |
| R2 | cote R | H2 |
| R3 | z(cote R) + 0.5 · [z(−log income) + z(hours) + z(first-gen)] | H3 |
| R4 | fully de-proxied committee score (strategy 9, path set P1 or P2) | H4 |

Convert each to ranks (or z-scores) on the candidate set.

### 4.3 Combination and optimisation

```python
import itertools
grid = [w for w in itertools.product(np.arange(0, 1.01, 0.1), repeat=4) if abs(sum(w) - 1) < 1e-9]
for w in grid:
    s = sum(wi * rank_i for wi, rank_i in zip(w, ranks))
    grant = top_k(s, 1600)
    scores = {H: official_like(grant, ref[H], group, baseline)["total"] for H in hypotheses}
    rows.append((w, np.mean(list(scores.values())), min(scores.values()),
                 sum(weights[H] * scores[H] for H in hypotheses)))
```

Pick two candidates: **expected-optimal** (max weighted mean) and **minimax** (max of the minimum).

### 4.4 Guard against fitting our own simulator

Leave-one-hypothesis-family-out: optimise weights without family F, evaluate on F. Report the held-out score of the blend vs the single components.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Table | for R1–R4 alone, expected-optimal blend, minimax blend: score under each H, mean, min |
| T2 | Held-out families | blend's held-out score ≥ best single component's held-out score in most folds |
| T3 | Adoption rule | adopt the blend only if its **minimum** is ≥ 3 points above the best single component's minimum while losing ≤ 1 point on the mean; otherwise submit the best single component and record why |
| T4 | Budget / format | `validate_submission.py` passes |

## 6. Risks

A blend is harder to explain. If adopted, frame it as "decision robust to our uncertainty about what *deserving* means" and show the table.

## 7. Combines with

Strategy 2, 3, 1 and 9 (components), 10 (governance: explicit uncertainty).

## 8. Results log

| Date | Who | Weights (R1..R4) | Mean /35 | Min /35 | Held-out | Verdict |
|---|---|---|---|---|---|---|
| | | | | | | |
