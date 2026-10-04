"""Compare reference model families by out-of-sample prediction of the exact error counts.

For every family: MAP fit on all readings, then
  * leave-one-file-out: refit without file j, predict err_j CONDITIONAL on the other readings
    (kriging with the model covariance) and also unconditionally (model mean only, like
    work/strat3/fit_reference.py did);
  * leave-group-out: hide the r7 batch (fit on the first 19 readings) and hide r6+r7
    (fit on the first 6), then predict the hidden files.
Reported: RMSE in errors, mean predictive log density (LPD), mean z^2 (calibration: ~1 is good),
bias (mean of observed - predicted; > 0 means the procedure is optimistic).

Run from equialgo-participants/:  python work/agent_readings/compare_families.py
"""
import os
import sys
import warnings

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).parent))
from readings_lib import Family, conditional_prediction, load_board, log_post, moments  # noqa: E402

warnings.filterwarnings("ignore")
board, Y, E = load_board()
J = len(E)
names = board.file.str.split("/").str[-1].str.replace(".csv", "", regex=False).to_numpy()
R7 = np.array([n.startswith("r7_") for n in names])
R6 = np.array([n.startswith("r6_") for n in names])

BASE = ["z_hours", "z_loginc", "z_firstgen", "z_logdist", "remote"]
REG = ["reg_Cap", "reg_Bas", "reg_Cot", "reg_Gas"]
PROG = ["prog_gen", "prog_sci", "prog_soc", "prog_san"]
NONLIN = ["hours2", "cotexhours", "cote2"]
SPEC = {
    "probit_base5": dict(names=BASE),
    "logit_base5": dict(names=BASE, link="logit"),
    "probit_base5_het_remote": dict(names=BASE, hetero="remote"),
    "probit_base5_het_hours": dict(names=BASE, hetero="hours"),
    "probit_base5_het_cote": dict(names=BASE, hetero="cote"),
    "probit_base5_freeK": dict(names=BASE, free_k=True),
    "probit_hours_remote": dict(names=["z_hours", "remote"]),
    "probit_hours": dict(names=["z_hours"]),
    "probit_base4_regions": dict(names=BASE[:4] + REG, prior_sd=[0.5] * 4 + [0.1] * 4),
    "probit_base5_progs_r.1": dict(names=BASE + PROG, prior_sd=[0.5] * 5 + [0.1] * 4),
    "probit_base5_nonlin_r.1": dict(names=BASE + NONLIN, prior_sd=[0.5] * 5 + [0.1] * 3),
    "probit_base5_raw_inc_dist_r.1": dict(names=BASE + ["z_inc", "z_dist"], prior_sd=[0.5] * 5 + [0.1] * 2),
    "probit_base5_hknots_r.1": dict(names=BASE + ["hknot8", "hknot12", "hknot16"], prior_sd=[0.5] * 5 + [0.1] * 3),
    "probit_rich_r.05": dict(names=BASE + REG[:1] + NONLIN + ["z_inc", "z_dist", "hknot12"],
                             prior_sd=[0.5] * 5 + [0.05] * 7),
    "probit_rich_r.1": dict(names=BASE + REG[:1] + NONLIN + ["z_inc", "z_dist", "hknot12"],
                            prior_sd=[0.5] * 5 + [0.1] * 7),
    "probit_base5_ridge.05": dict(names=BASE, prior_sd=[0.5, 0.05, 0.05, 0.05, 0.05]),
    "probit_base5_histz": dict(names=BASE, standardize_on="history"),
}


def make(key):
    return Family(label=key, **SPEC[key])


def fit(fam, rows, x0, polish_only=False):
    f = lambda th: -log_post(fam, th, Y[rows], E[rows])
    if not polish_only:
        x0 = minimize(f, x0, method="Powell", options=dict(maxiter=40000, xtol=1e-4, ftol=1e-7)).x
    r = minimize(f, x0, method="L-BFGS-B")
    return r.x, -r.fun


def evaluate(key):
    fam = make(key)
    allrows = np.arange(J)
    th_full, lp_full = fit(fam, allrows, fam.x0())
    p_full, k_full = fam.probs(th_full)
    out = dict(family=key, dim=fam.dim, logpost=lp_full, sigma=np.exp(th_full[fam.m]),
               ceiling_err=np.minimum(p_full, 1 - p_full).sum(),
               weights=" ".join(f"{n}={w:+.3f}" for n, w in zip(fam.names, th_full[:fam.m])))
    # leave one file out
    cm, cs, um = np.zeros(J), np.zeros(J), np.zeros(J)
    for j in range(J):
        rows = np.delete(allrows, j)
        th, _ = fit(fam, rows, th_full, polish_only=True)
        p, k = fam.probs(th)
        m, s = conditional_prediction(p, k, Y[rows], E[rows], Y[[j]])
        cm[j], cs[j] = m[0], s[0]
        um[j] = moments(p, k, Y[[j]])[0][0]
    z = (E - cm) / cs
    out.update(loo_rmse=np.sqrt(np.mean((E - cm) ** 2)), loo_lpd=np.mean(-0.5 * z ** 2 - np.log(cs) - 0.919),
               loo_z2=np.mean(z ** 2), loo_bias=np.mean(E - cm),
               loo_uncond_rmse=np.sqrt(np.mean((E - um) ** 2)))
    # leave group out
    for tag, hide in [("r7", R7), ("r6r7", R6 | R7)]:
        rows, new = np.where(~hide)[0], np.where(hide)[0]
        th, _ = fit(fam, rows, th_full, polish_only=True)
        p, k = fam.probs(th)
        m, s = conditional_prediction(p, k, Y[rows], E[rows], Y[new])
        z = (E[new] - m) / s
        out.update({f"{tag}_rmse": np.sqrt(np.mean((E[new] - m) ** 2)), f"{tag}_bias": np.mean(E[new] - m),
                    f"{tag}_z2": np.mean(z ** 2), f"{tag}_lpd": np.mean(-0.5 * z ** 2 - np.log(s) - 0.919)})
        if tag == "r7":
            out["r7_pred"] = " ".join(f"{a:.1f}" for a in m)
    return out


if __name__ == "__main__":
    keys = sys.argv[1:] or list(SPEC)
    with Pool(min(len(keys), 18)) as pool:
        res = pool.map(evaluate, keys)
    df = pd.DataFrame(res).sort_values("loo_lpd", ascending=False)
    pd.set_option("display.width", 250)
    cols = ["family", "dim", "logpost", "sigma", "ceiling_err", "loo_rmse", "loo_lpd", "loo_z2", "loo_bias",
            "loo_uncond_rmse", "r7_rmse", "r7_bias", "r7_z2", "r6r7_rmse", "r6r7_bias", "r6r7_z2"]
    print(df[cols].round(3).to_string(index=False))
    print()
    for _, r in df.iterrows():
        print(f"{r.family:32s} {r.weights}")
    print("\nr7 observed:", " ".join(f"{e:.0f}" for e in E[R7]))
    for _, r in df.iterrows():
        print(f"{r.family:32s} r7 predicted (fit on first 19): {r.r7_pred}")
    df.to_csv(Path(__file__).parent / "family_comparison.csv", index=False)
