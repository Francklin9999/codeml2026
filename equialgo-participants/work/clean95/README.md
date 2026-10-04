# Seed-ensembled counterfactual merit model

Submission file: `upload_final/predictions.csv` (1,600 grants = 40%, inside the 36-44% envelope).
Reproduce: `python work/clean95/seeded_model.py predict` (about 10 s, deterministic; md5 identical across runs).
Evidence: `python work/clean95/seeded_model.py validate` writes `validation_report.json`.

## What it does
1. Fit a sparse additive-spline logistic model of the historical committee (`donnees_demandes.csv` only).
2. Score each applicant counterfactually. Their academic score and working hours are kept; income, region,
   distance, programme and first-generation status are replaced by a common reference profile, and the
   predicted probabilities are averaged. Merit (academic performance and effort) can drive the score;
   wealth and geography cannot.
3. Repeat for 30 seeds. Each seed has its own bootstrap resample of the history and its own 256 reference
   profiles. The final score is the mean, and the top 40% of the cohort is granted.

Not used: platform scores, correction files, reconstructed labels, applicant IDs.

## Evidence it generalises (5 repeated 80/20 splits, 10 seeds each)
| Check | Result |
|---|---|
| Committee-fit accuracy on held-out rows | 89.3% +/- 0.6 |
| Committee-fit AUC | 0.959 +/- 0.004 |
| Merit-only top-40% agreement with committee | 85.1% +/- 0.7 (lower by design: income and region removed) |
| Held-out grant rate, remote / centre | about 0.40 / 0.40 (committee: about 0.28 / 0.48) |

## Stability across seeds (evaluation cohort, 30 seeds)
- 97% of applicants get the same decision from all 30 seeds; 120 of 4,000 are split votes.
- A single seed differs from the ensemble on 21 applicants on average (max 54). This is the variance
  the seed ensemble removes.
- The remote vs centre grant rate is 40.0% vs 40.0%. The committee gap was 48.4% vs 27.3%.

## Limits (state these to the jury)
- The hidden reference is unknown. The committee-agreement numbers are diagnostics, not accuracy.
- The platform preview scored the single-seed version of this model at 94.88%. The ensemble differs from
  it on 4 of 4,000 applicants, so it is expected to behave the same, but it has not been previewed.
- Roughly 5% of reference labels look like irreducible noise (see `work/agent_dgp/README.md`), so about
  95% is near the ceiling for any model that uses only applicant features.
