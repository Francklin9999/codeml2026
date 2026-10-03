# EquiAlgo · Strategy 20: Reverse-engineering the synthetic data-generating process

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (high information value, low cost) |
| **Effort** | 2–3 h |
| **Depends on** | nothing |
| **Rubric lines** | Technical (35, indirectly: tells us what the reference most likely is), Diagnostic (25) |
| **Differs from 1–10** | Strategy 3 calibrates hypotheses with the one published number (0.270). This studies the **data itself** forensically: marginal distributions, rounding, functional forms and noise level, to recover how the organisers generated features and decisions, and therefore how they most likely generated the reference |
| **Work folder** | `equialgo-participants/work/strat20/` |

---

## 1. Context you need

- The data is explicitly synthetic (*"All data is synthetic. The institution is fictional."*). Synthetic generators usually follow simple recipes: features drawn from parametric distributions per region, a latent score that is a linear combination, a regional penalty, Gaussian or logistic noise, a threshold at a quantile.
- Facts already verified: 18 postal codes, each in exactly one region; IDs `C000000–C013999` split between the two files with no grant-rate pattern by ID; programme grant rates 36.5–42.8%; first-gen 37.4% vs 41.3%; income from 13,364 to 293,879; hours 1–29; cote R 16.78–38.41.

## 2. The idea

Recover the generator step by step:

1. **Feature distributions by region:** fit candidate families (normal, log-normal, gamma, truncated normal, Poisson for hours) per region and compare fits (AIC, Q-Q plots). Check rounding (cote R to 2 decimals, distance to 1 decimal, income integers) and truncation bounds (cote R "15 to 40").
2. **Dependencies:** are features independent given region? (correlation matrices per region; if near-zero, the generator drew them independently, which means the "proxies" carry region only through their region-specific means.)
3. **Decision rule:** fit the committee decision with flexible models (GAM / splines per feature) to see whether effects are linear in the original or log scale; estimate the noise level from the best achievable AUC (0.957 suggests substantial but not huge noise); test for interactions; test whether the penalty is a constant shift (same for all three remote regions?) or region-specific.
4. **Infer the reference:** a typical generator computes `latent = Σ β_k f(x_k) + ε`, then `committee = 1[latent − π·remote + ε' > q]` and `reference = 1[latent > q']`. Our recovered `β`, `f`, `π` and noise give the most probable reference → plug into strategy 2 as hypothesis **H7 (recovered generator)**.

## 3. Why it could score

If the generator is simple (very common in hackathon datasets), recovering it makes our choice of submission close to optimal and our diagnostic exceptionally precise ("the committee applies a constant penalty of π, identical across the three remote regions").

## 4. Implementation plan

### 4.1 Files

```
work/strat20/
  marginals.ipynb      # per-region fits, Q-Q plots, rounding/truncation checks
  dependence.ipynb     # within-region correlations, mutual information
  decision_form.ipynb  # GAM (pygam) / spline logistic; penalty structure; noise estimate
  generator_h7.py      # recovered generator → reference hypothesis H7 for strategy 2
  findings.md
```

### 4.2 Checks list

- Distribution of `cote_r_equivalent` per region: same shape shifted (27.3 vs 28.0 means) or different variances?
- Is `distance` region-specific with almost no overlap? (Explains its AUC as a proxy.)
- Do the three remote regions share one penalty? Fit region dummies in the committee logit and test equality of the three remote coefficients.
- Is the income effect really positive (as in the probe) or an artefact of log vs raw scale or of correlation with region?
- Is the decision a hard threshold at the 60th percentile of a latent (exactly 40% granted overall)?

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Re-simulation | data simulated from the recovered generator reproduces: region grant rates (± 1 pt), committee-model AUC (± 0.01), feature marginals (KS p > 0.05) |
| T2 | Anchor | the notebook baseline's EO gap under H7 is close to 0.270 (cross-check with strategy 3) |
| T3 | Penalty structure | equality test result for the three remote regions reported |
| T4 | Hand-off | H7 added to strategy 2's simulator; robustness matrix rerun |

## 6. Risks

Over-fitting a story to the data. T1 (re-simulation) is the guard: a recovered generator must reproduce the data, not just look plausible.

## 7. Combines with

Strategy 2 (H7), 3 (anchor cross-check), 12 (penalty estimate), 4 (diagnostic).

## 8. Results log

| Date | Who | Finding | Evidence | Impact on choice of submission |
|---|---|---|---|---|
| | | | | |
