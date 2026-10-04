"""Backtests of the predictive procedure: calibration and winner's-curse optimism on files that were scored.

A. Leave-group-out with the full Bayesian procedure (MCMC per family, equal-weight mixture):
   hide a batch, fit on the rest, predict the hidden files conditional on the visible readings.
B. Random splits (plug-in MAP, 3 families mixed): hide 10 random files (never r4_16), pick the
   hidden file with the best predicted error, record observed - predicted. The mean over splits
   estimates how optimistic "the best-looking file" is, compared with the average hidden file.

Run from equialgo-participants/:  python work/agent_readings/backtest.py
"""
import os
import sys
import warnings
from multiprocessing import Pool
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.optimize import minimize  # noqa: E402
from scipy.special import ndtr  # noqa: E402

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from posterior import Predictor, adaptive_metropolis  # noqa: E402
from readings_lib import Family, load_board, log_post  # noqa: E402

warnings.filterwarnings("ignore")
board, Y_all, E_all = load_board()
names = board.file.str.split("/").str[-1].str.replace(".csv", "", regex=False).to_numpy()
BASE_IDX = list(names).index("r4_16")
FAMILIES = {
    "probit_hours": dict(names=["z_hours"]),
    "probit_hours_remote": dict(names=["z_hours", "remote"]),
    "probit_base5_ridge.05": dict(names=["z_hours", "z_loginc", "z_firstgen", "z_logdist", "remote"],
                                  prior_sd=[0.5, 0.05, 0.05, 0.05, 0.05]),
}
GROUPS = {
    "r7": np.array([n.startswith("r7_") for n in names]),
    "r6": np.array([n.startswith("r6_") for n in names]),
    "codex": np.array([n.startswith("model_") for n in names]),
    "early": np.isin(names, ["r2_11", "r3_11", "r4_14"]),
}


def map_fit(fam, Y, E):
    f = lambda th: -log_post(fam, th, Y, E)
    th = minimize(f, fam.x0(), method="Powell", options=dict(maxiter=40000, xtol=1e-4, ftol=1e-7)).x
    return minimize(f, th, method="L-BFGS-B").x


def mixture(preds):
    m = np.mean([p[0] for p in preds], 0)
    s = np.sqrt(np.mean([p[1] ** 2 + p[0] ** 2 for p in preds], 0) - m ** 2)
    pb = np.mean([p[2][211.5] for p in preds], 0)
    return m, s, pb


def group_out(group):
    hide = GROUPS[group]
    Y, E = Y_all[~hide], E_all[~hide]
    preds = []
    for i, (key, spec) in enumerate(FAMILIES.items()):
        fam = Family(label=key, **spec)
        draws, _ = adaptive_metropolis(fam, Y, E, map_fit(fam, Y, E), 9000, 2500, 13, seed=i)
        pr = Predictor(Y, E, Y_all[BASE_IDX], Y_all[hide])
        for t in draws:
            pr.add(*fam.probs(t))
        preds.append(pr.summary())
    m, s, pb = mixture(preds)
    return group, names[hide], E_all[hide], m, s, pb


def random_split(seed):
    rng = np.random.default_rng(seed)
    pool = np.delete(np.arange(len(E_all)), BASE_IDX)
    hide = np.zeros(len(E_all), bool)
    hide[rng.choice(pool, 10, replace=False)] = True
    Y, E = Y_all[~hide], E_all[~hide]
    preds = []
    for key, spec in FAMILIES.items():
        fam = Family(label=key, **spec)
        pr = Predictor(Y, E, Y_all[BASE_IDX], Y_all[hide])
        pr.add(*fam.probs(map_fit(fam, Y, E)))
        preds.append(pr.summary())
    m, s, _ = mixture(preds)
    obs = E_all[hide]
    best = np.argmin(m)
    return obs[best] - m[best], np.mean(obs - m), np.mean(((obs - m) / s) ** 2)


if __name__ == "__main__":
    with Pool(12) as pool:
        groups = pool.map(group_out, list(GROUPS))
        splits = pool.map(random_split, range(60))
    print("A. leave-group-out, full posterior mixture")
    for group, nm, obs, m, s, pb in groups:
        z = (obs - m) / s
        cover = np.mean(np.abs(z) < 1.2816)
        print(f"  {group:6s} n={len(obs):2d}  bias(obs-pred) {np.mean(obs - m):+.2f}  RMSE {np.sqrt(np.mean((obs - m) ** 2)):.2f}"
              f"  mean z^2 {np.mean(z ** 2):.2f}  80%-coverage {cover:.2f}  best-predicted: {nm[np.argmin(m)]} "
              f"pred {m.min():.1f} obs {obs[np.argmin(m)]:.0f}")
        print("        " + " ".join(f"{a}:{o:.0f}/{p:.1f}±{q:.1f}" for a, o, p, q in zip(nm, obs, m, s)))
    sp = np.array(splits)
    print("\nB. 60 random 10-file splits (plug-in MAP mixture)")
    print(f"  best-predicted hidden file: mean(obs - pred) {sp[:, 0].mean():+.2f} (se {sp[:, 0].std() / np.sqrt(len(sp)):.2f})")
    print(f"  all hidden files:           mean(obs - pred) {sp[:, 1].mean():+.2f};  mean z^2 {sp[:, 2].mean():.2f}")
