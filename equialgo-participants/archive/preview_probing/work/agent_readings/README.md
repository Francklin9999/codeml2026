# agent_readings: inferring the hidden reference from the exact readings

This folder fits the reference to the 29 two-decimal HxBuddy readings with model families other than the team's, checks them out of sample, corrects for the winner's curse, and proposes 6 rule-based files (`ar_01` … `ar_06`, most promising first). Every file is a scoring rule applied to all 4,000 candidates. No individual decision was flipped from leaderboard feedback.

## What changed compared with `work/strat3/fit_reference.py`

1. **Likelihood.** Every scored file shares about 95% of its decisions with every other one, so their error counts are strongly correlated. strat3 fitted independent least squares. Here the vector of 29 counts is modelled as Gaussian with mean `n_j + K - 2 Y_j.p` and covariance `4 (Y diag(v) Yᵀ - (Yv)(Yv)ᵀ/Σv)`, where `v = p(1-p)` and the reference is conditioned on K positives (`readings_lib.py`).
2. **Prediction.** A file's error is predicted *conditional on all readings* (kriging with the same covariance), not from the model mean alone.
3. **Uncertainty.** Each family gets a posterior over its weights and σ (adaptive Metropolis, `posterior.py`). The families are mixed with pseudo-BMA weights taken from their leave-one-out log predictive density.
4. **Winner's curse.** It is measured directly: backtests on scored files (`backtest.py`) and a simulation of the whole procedure on synthetic truths, some of them outside the fitted families (`simulate_curse.py`).

## Which family fits best out of sample (`compare_families.py`, `family_comparison.csv`)

The score is z(cote) + Σ w·x, with P(ref = 1) = F((s - t)/σ). The table shows conditional leave-one-file-out prediction (RMSE in errors, mean log predictive density, mean z²) and leave-group-out tests: r7 hidden means fit on the first 19 readings; r6+r7 hidden means fit on the first 6.

| family | LOO RMSE | LOO LPD | z² | r7 hidden: RMSE / bias | r6+r7 hidden: RMSE / bias |
|---|---|---|---|---|---|
| probit, hours only | **2.67** | **-2.489** | 0.76 | 4.4 / +3.8 | 4.9 / +0.2 |
| probit, base5 with ridge sd 0.05 on the extras | 2.73 | -2.492 | 0.76 | 5.3 / +4.7 | 4.6 / +0.7 |
| probit, hours + remote | 2.70 | -2.496 | 0.77 | **2.7 / +1.6** | **4.6 / -0.3** |
| probit, base5 unregularised (strat3's family) | 2.93 | -2.512 | 0.81 | 7.3 / +6.8 | 23.0 / -14.0 |
| logit, base5 | 3.03 | -2.515 | 0.82 | 7.8 / +7.3 | 21.1 / -12.8 |
| heteroscedastic σ (by remote / cote / hours) | 2.92-3.61 | ≤ -2.512 | | no gain | |
| free K | identical to fixed K (K is pinned at about 1599) | | | | |
| z-scores computed on the history file | identical: this is only a reparametrisation | | | | |
| regions, programmes, nonlinear terms, splines, raw income and distance (ridge) | 2.9-3.2 | -2.54 to -2.63 | | worse | worse |
| strat3's least-squares method, unconditional prediction, 29 readings | 3.21 | | | r7 predicted at about 208, **bias +9.7** | |

- **The best families are the simplest.** The fitted reference is z(cote) + 0.19 z(hours), with a remote term between -0.05 and 0 (posterior -0.046 ± 0.044) and noise σ = 0.174 [0.159, 0.190] in cote-z units. r4_16 is essentially the MAP rule of this family.
- **σ is sharply identified.** In the profile likelihood, σ = 0.14 loses 9 log-likelihood points and σ → 0.03 loses 740. Most of the ~210 errors are therefore noise in the reference that no rule using these features can recover. `work/agent_dgp` reached the same model independently.

## Would this procedure have predicted the r7 flop?

Mostly yes. Fitted on the first 19 readings (posterior mixture, equal family weights), it predicted r7_01..10 at 213.0-215.8 errors (mean 214.6, sd about 6), with P(beat 212) between 0.28 and 0.41 each. It ranked them as *worse* than r4_16. The strat3 model had predicted about 208. The observed mean was 217.8, so this procedure was still optimistic by **+3.2 to +3.7 errors** on that batch.

## Winner's-curse estimates

| test | optimism (observed - predicted) |
|---|---|
| Leave-group-out, full posterior: r7 / r6 / codex / early files | +3.2 / -0.2 / -4.5 / 0.0 (the average hidden file is unbiased) |
| 60 random 10-file splits (plug-in fit) | average hidden file -0.02 (z² 0.85); **best-predicted hidden file +2.1 ± 0.5** |
| Simulation, 60 synthetic truths, selection strategy used here (`joint_raw`) | each pick **+1.7 ± 0.25**. Predicted P(beat best reading) 0.35 vs 0.21 realized. Batch P(any of 6 beats it) 0.72 predicted vs **0.62 realized**; P(≤ best - 5) 0.18; P(≤ best - 12) 0.02 |
| Simulation, by rule kind | random posterior draws +2.1 (excluded from the batch), linear grid +2.0, posterior-mean rules +3.0, rank blends -0.7, hours-curve -0.3 |

The "calibrated" columns of `manifest.csv` add δ = 2.46 errors and widen the sd by λ = 1.5. These two values have the best Brier score on the simulated picks.

## Files (`manifest.csv`)

Picks are greedy: each one maximises the model's P(min error of the batch ≤ 211), so any prefix of the list is the best upload set of that size. The first two files carry most of the chance.

Every file is at least 8 decisions away from every scored file, from every pending teammate file (`upload_r8`, `upload_codex_v2`, `work/agent_dgp`) and from the other picks. The `upload_r8` rule files are treated as uploaded anyway.

| file | rule | grants | changed vs r4_16 | model: errors (P<212) | calibrated: errors (P<212) |
|---|---|---|---|---|---|
| ar_01 | rank blend 0.25 × r4_16 score + 0.75 × codex spline score | 1595 | 24 | 211.0 ± 2.4 (0.51) | 213.4 ± 3.6 (0.30) |
| ar_02 | z(cote) + 0.194 z(h) + 0.015 z(log inc) - 0.010 z(first-gen) - 0.003 z(log dist) - 0.015 remote (MAP of the ridge base5 family) | 1602 | 17 | 211.8 ± 3.0 (0.40) | 214.2 ± 4.5 (0.28) |
| ar_03 | z(cote) + 0.18 z(h) + 0.02 (z(h)² - 1) - 0.05 remote | 1595 | 28 | 212.9 ± 3.6 (0.29) | 215.4 ± 5.4 (0.23) |
| ar_04 | z(cote) + 0.195 z(h) - 0.07 remote | 1603 | 10 | 212.9 ± 2.5 (0.22) | 215.4 ± 3.7 (0.15) |
| ar_05 | rank blend 0.5 × r4_16 score + 0.5 × codex ensemble score | 1595 | 16 | 212.8 ± 2.4 (0.22) | 215.3 ± 3.7 (0.15) |
| ar_06 | posterior-mean P(ref = 1), probit with regions (ridge) | 1603 | 20 | 212.4 ± 3.2 (0.33) | 214.9 ± 4.7 (0.24) |

For the batch, P(at least one < 212) is 0.88 under the model and 0.68 calibrated; the simulation of this strategy realised 0.62. P(at least one ≤ 207) is about 0.18. P(≤ 200) is about 0.

Rank blends were the best-calibrated kind in simulation, so ar_01's real chance may sit between its two columns. A low k (1595) is favoured because the Bayes count under this model is about 1585, below the window.

## Caveat for the team (evaluation only, no file written here)

The same posterior predicts the pending `upload_codex_v2` files at about 203 ± 4 errors (P(<212) ≈ 0.97). Those files condition on the 29 readings *at the level of individual applicants*. In a simulation with the 5 synthetic truths above, label-level conditioning beat the best reading by about 11 errors in 97-100% of replicates. The gain is probably real. However, it uses leaderboard feedback on individual candidates of the fixed evaluation set, which this folder's brief forbids, and which a jury may judge as overfitting the evaluation rather than as a model. That decision belongs to the team.

## Reproduce (from `equialgo-participants/`, about 3 minutes on 20 cores without the simulation)

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python work/agent_readings/compare_families.py     # family table, ~35 s
python work/agent_readings/select_files.py r7      # r7 backtest of the whole procedure
python work/agent_readings/select_files.py         # posterior + pool of 3,640 rule files -> pool_predictions_all.csv, pool_files_all.npz
python work/agent_readings/backtest.py             # leave-group-out + random-split curse, ~40 s
python work/agent_readings/simulate_curse.py 12    # winner's-curse simulation, ~10 min
python work/agent_readings/make_batch.py           # joint selection, writes ar_*.csv + manifest.csv, validates
```

`make_batch.py` validates each file: header, 4,000 rows in candidate order, 0/1 values, 1595-1603 grants, and at least 8 decisions from every scored file, every pending teammate file and the other picks. Rerunning the pipeline reproduces the same files byte for byte.
