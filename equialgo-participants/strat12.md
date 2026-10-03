# EquiAlgo · Strategy 12: Bayesian threshold test: does the committee hold remote applicants to a higher bar?

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (strong diagnostic; also yields an estimate of the penalty) |
| **Effort** | 3–4 h |
| **Depends on** | `work/shared/data.py` |
| **Rubric lines** | Diagnostic rigour (25), supports Technical (35) by estimating the penalty used in strategies 1 and 7 |
| **Differs from 1–10** | Strategy 4 decomposes the **grant-rate gap**. This tests **decision thresholds directly**: it estimates, for each region, the latent-merit threshold the committee applied, which is the cleanest definition of "held to a higher standard" |
| **Work folder** | `equialgo-participants/work/strat12/` |

---

## 1. Context you need

- Outcome tests and benchmark tests can mislead when groups differ in their distributions ("infra-marginality"). The **threshold test** (Simoiu, Corbett-Davies & Goel, 2017, *The problem of infra-marginality in outcome tests for discrimination*) models decisions as "grant if latent score > group-specific threshold" and estimates the thresholds.
- Here we do not observe an outcome after the decision (no "success" label), so we adapt the idea: assume a latent merit `m = f(x) + ε` common to all regions, and a committee rule `grant ⇔ m > t_region`. Differences in `t_region` = differential standards.
- The probe in the analysis already suggests a linear committee with a remote penalty (std. coefficient −1.08 on `remote`).

## 2. The idea

Fit an **ordered / threshold probit model** with shared slopes on legitimate features and **region-specific intercepts (thresholds)**, in a Bayesian framework (PyMC or NumPyro) to get credible intervals:

`P(grant_i) = Φ((β·x_i − t_{region(i)}) / σ)`

Report each region's threshold on the cote-R scale ("a Gaspésie applicant needs ~X more cote R points to have the same chance"). Then use the posterior of `t_remote − t_central` as the penalty to neutralise (feeds strategies 1 and 7), with uncertainty.

## 3. Why it could score

A threshold expressed in **cote-R points** is the most intuitive possible statement of the bias for a jury, comes with credible intervals, and directly quantifies the correction.

## 4. Implementation plan

### 4.1 Files

```
work/strat12/
  threshold_model.py     # PyMC (or NumPyro) model
  fit_threshold.ipynb    # sampling, diagnostics, plots
  thresholds.csv         # posterior summaries per region
  fig_thresholds.png     # threshold per region on the cote-R scale with 95% CI
```

### 4.2 Model

```python
import pymc as pm
with pm.Model() as m:
    beta = pm.Normal("beta", 0, 2, shape=X_legit.shape[1])      # cote R, log income, hours, programme, first-gen (distance? see variants)
    t    = pm.Normal("t", 0, 2, shape=n_regions)               # one threshold per region
    eta  = pm.math.dot(X_legit_std, beta) - t[region_idx]
    pm.Bernoulli("y", p=pm.math.invprobit(eta), observed=y)
    idata = pm.sample(1000, tune=1000, chains=4, target_accept=0.9)
```

Express thresholds on the cote-R scale: `t_r / beta_coteR` (with standardisation undone). Report pairwise differences with credible intervals.

### 4.3 Variants

- With and without distance in the legitimate set (distance is a near-perfect region proxy; with it, region thresholds are poorly identified: show this, it is itself an insight).
- 5 regions vs 2 groups.
- Logit link instead of probit (robustness).

### 4.4 Use for mitigation

Penalty = posterior mean of `t_remote − t_central`; neutralise by scoring everyone with the central threshold; also produce 2.5% / 97.5% versions to show how decisions change across the credible interval (feeds strategy 16's stability analysis).

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Sampler diagnostics | R-hat < 1.01, effective sample size > 400 for all parameters, no divergences |
| T2 | Posterior predictive | predicted grant rates by region match observed (48.4 / 27.3 etc.) within ± 1 pt |
| T3 | Simulation recovery | on strategy 2's H6 synthetic data with a known penalty, the posterior interval contains the true value |
| T4 | Agreement | penalty consistent with strategy 1's logistic coefficient (after scale conversion) |
| T5 | Headline | one sentence: "à profil égal, un candidat de région éloignée doit avoir ≈ X points de cote R de plus (IC 95 % [a, b])" |

## 6. Risks

Identification relies on the shared-slope assumption; test region-specific slopes for cote R as a robustness check.

## 7. Combines with

Strategy 4 (alternative diagnostic), 1 and 7 (penalty estimate), 10 (pitch headline), 16 (uncertainty in decisions).

## 8. Results log

| Date | Who | Variant | Penalty (cote-R points) | 95% CI | Diagnostics OK | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
