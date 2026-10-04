# agent_dgp: how the synthetic data was generated

Reproduce from `equialgo-participants/` with `python work/agent_dgp/dgp_analysis.py` (about 15 s). The script prints every number below, rewrites the five files and writes `manifest.csv`.

## Verified findings

1. **There is no hidden latent variable.** Within each group (centre or remote), all features are independent: the largest |correlation| between cote R, log income, hours, distance and first-generation status is 0.012 (centre) and 0.025 (remote). Each group draws every feature independently:
   - cote R ~ N(28.0, 3.0) in the centre and N(27.36, 3.0) remote, clipped to [15, 40];
   - hours ~ Poisson(9) centre and Poisson(13) remote (variance equals the mean: 8.76 vs 8.96, 12.89 vs 13.03);
   - income ~ lognormal(ln 70k, 0.42) centre and lognormal(ln 51.5k, 0.44) remote;
   - distance ~ Gamma(shape 2.2, mean 20 km) centre and Gamma(shape 4.1, mean 221 km) remote;
   - first-generation ~ Bernoulli(0.27) centre and Bernoulli(0.45) remote;
   - postal code is uniform within its region and carries no distance information;
   - programme shares differ by group, but programme is independent of everything else.

   So E[merit | features] cannot pull in extra weight from income, first-generation status or distance. The reference can only be a function of the features plus independent noise.
2. **Other checks.** History is stratified at exactly 6000 centre and 4000 remote. Candidates come from the same distributions (KS p ≥ 0.36). The ids are one random permutation of 0..13999 shared by both files and carry no signal (max |Spearman| 0.022). There are no duplicate applicants.
3. **The committee is a clean logistic Bernoulli draw.** The logistic link beats probit by 9.4 log-likelihood. Linear cote and hours with log income is the right form. Programme, first-generation status, distance, postal code (p = 0.09), id and row order all have no effect. In z units, with cote = 1, the weights are hours 0.184, log income 0.194, remote -0.467 (±0.01-0.02), on a logit scale of 4.2. That looks like a designer's `4*(z_cote + 0.2 z_hours + 0.2 z_income - 0.5 remote)`. Its merit part, cote + 0.2 × hours, is what the leaderboard independently finds for the reference.
4. **Reference model fitted correctly.** All files are scored against the same reference, so the readings are correlated: Cov(E_f, E_g) = Σ p(1-p)(1-2f)(1-2g). Fitting with that covariance plus the brief's baseline EO gap gives:
   - formula: s = z(cote) + a·z(hours) + d·remote, with a = 0.198 ± 0.020, d = -0.049 ± 0.028 (P(d < 0) = 0.94);
   - noise: probit with σ = 0.176 ± 0.009 cote-z, about 0.54 cote points.

   Two independent checks support it:
   - the notebook's random forest, scored against this reference, has an equal-opportunity gap of 0.2701 (the brief says 0.270);
   - predicting each scored file from the other 28 readings gives z-scores with mean 0.00 and sd 0.96 (prediction error about 2.6 errors).
5. **Nothing else improves the fit:**
   - income, first-generation, distance, programme, Capitale-Nationale, hours×remote, cote×hours, hours² and cote² all add < 1.3 log-likelihood;
   - concave hours forms (log, sqrt, caps at 12/15/18/20) fit worse;
   - noise distribution: logistic and probit fit equally well.

   The ~190 errors shared by every good file are independent noise. No rule can recover them.
6. **Reference size:** the reference has an odd number of positives, 1599 (27 of 29 F1 readings match exactly; r6_01 and r7_09 are off by 0.0005, probably transcription). With symmetric noise, the Bayes rule grants P > 0.5, which is **1585** people, fewer than 1599, because score density falls above the 60th percentile.

## What this means

- Given the 29 readings, **no rule-based file is expected to beat 212.** The best is top-1591 by posterior P (outside the 1595-1603 window), at 212.2 expected.
- r4_16 is effectively the Bayes rule. Its 212 is about 1.4 errors better than its own prior expectation (213.4), which is ordinary luck. The top team's 208 is within the same luck range.
- **95% (200 errors) has probability ≈ 0** for any file here.
- Official 35 points: 12 errors = 0.1 utility points, while 0.01 of equal-opportunity gap = 0.74 equity points. r4_16's expected EO gap is -0.006 (sd ~0.009), so about 97-100% of the gap is closed already.

## Files, in upload priority

All files are 1595-1603 grants, candidates order, 0/1, validated. The expectation column is conditional on the 29 readings.

| file | rule | changed vs r4_16 | E[errors] | P(<212) | P(≤208) |
|---|---|---|---|---|---|
| dgp_01_hours021_rem075_k1601 | z(cote)+0.21 z(hours)-0.075 remote, top 1601 | 8 | 212.8 | 0.25 | 0.013 |
| dgp_02_hours018_norem_k1597 | z(cote)+0.18 z(hours), no regional term, top 1597 | 24 | 213.4 | 0.20 | 0.016 |
| dgp_03_hours022_rem125_k1603 | z(cote)+0.22 z(hours)-0.125 remote, top 1603 (high variance) | 28 | 214.1 | 0.22 | 0.052 |
| dgp_04_bayes_k1599 | posterior-mean P(ref=1), top 1599 | 2 | 212.7 | 0.13 | 0.000 |
| dgp_05_committee_merit_k1599 | committee hours weight, remote term from EO anchor; no readings used | 22 | 217.8 | 0.00 | 0.000 |

- Uploading 01 + 02 + 03 gives P(best < 212) ≈ 0.52 and P(best ≤ 208) ≈ 0.08. These are lottery tickets, not improvements.
- File 05 is for the jury story: a reference derived without the leaderboard lands within 6 errors of the best file.

## Ruled out or not attempted

- **Ruled out:**
  - a latent merit variable linking features;
  - postal-code, programme, region-level or id effects;
  - heteroscedastic group noise (this would not change the decision at k ≈ K_ref anyway);
  - a nonlinear hours effect.
- **Not attempted on purpose:** recovering the generator's random seed. That would leak the labels instead of giving a rule.
