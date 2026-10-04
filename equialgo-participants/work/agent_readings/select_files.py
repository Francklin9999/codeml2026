"""Score a pool of rule-based files with the reference posterior, conditional on every exact reading.

1. Families kept by compare_families.py (best out-of-sample): probit with hours only, hours+remote,
   ridge-shrunk base5, ridge-shrunk regions. Each gets an adaptive-Metropolis posterior; families
   are mixed with pseudo-BMA weights from their leave-one-file-out log predictive density.
2. Pool of rule-based files, every one applied to all 4,000 candidates:
     top-k by z(cote) + a z(hours) + d remote                         (grid on a, d, k)
     top-k by z(cote) + a z(hours) + a2 (z(hours)^2 - 1) + d remote    (hours curvature)
     top-k by rank blend of the r4_16 score with a teammate model score (work/codex_accuracy)
     top-k by the MAP score / posterior-mean reference probability of each family and of the mixture
     top-k by the score of posterior draws of the ridge families
3. Every file gets the mixture predictive distribution of its error count given all readings.

Run from equialgo-participants/:  python work/agent_readings/select_files.py [hide_group]
hide_group = r7 reruns the whole procedure on the first 19 readings (backtest of the r7 flop).
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
from scipy.stats import rankdata  # noqa: E402

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from posterior import Predictor, adaptive_metropolis  # noqa: E402
from readings_lib import ROOT, N, N_GRANT_RANGE, Family, feature_matrix, load_board, log_post, top_k  # noqa: E402

warnings.filterwarnings("ignore")
BASE5 = ["z_hours", "z_loginc", "z_firstgen", "z_logdist", "remote"]
REG = ["reg_Cap", "reg_Bas", "reg_Cot", "reg_Gas"]
FAMILIES = {
    "probit_hours": dict(names=["z_hours"]),
    "probit_hours_remote": dict(names=["z_hours", "remote"]),
    "probit_base5_ridge.05": dict(names=BASE5, prior_sd=[0.5, 0.05, 0.05, 0.05, 0.05]),
    "probit_base4_regions": dict(names=BASE5[:4] + REG, prior_sd=[0.5] * 4 + [0.1] * 4),
}
CODEX = ["model_A_boosted_academic_hours", "model_B_spline_academic_hours", "model_C_extra_trees_academic_hours",
         "model_E_probit_academic_hours", "model_F_ensemble"]
MIN_DIFFERENT = 8
N_ITER, BURN, THIN = 12000, 3000, 18


def run_family(args):
    key, Y, E, seed = args
    fam = Family(label=key, **FAMILIES[key])
    f = lambda th: -log_post(fam, th, Y, E)
    th = minimize(f, fam.x0(), method="Powell", options=dict(maxiter=40000, xtol=1e-4, ftol=1e-7)).x
    th = minimize(f, th, method="L-BFGS-B").x
    draws, acc = adaptive_metropolis(fam, Y, E, th, N_ITER, BURN, THIN, seed=seed)
    return key, th, draws, acc


def fit_families(Y, E, pool=None, seed=0):
    jobs = [(k, Y, E, seed * 10 + i) for i, k in enumerate(FAMILIES)]
    out = pool.map(run_family, jobs) if pool is not None else list(map(run_family, jobs))
    return {key: (Family(label=key, **FAMILIES[key]), th, draws, acc) for key, th, draws, acc in out}


def loo_weights(equal=False):
    if equal:
        return {k: 1 / len(FAMILIES) for k in FAMILIES}
    lpd = pd.read_csv(HERE / "family_comparison.csv").set_index("family").loc[list(FAMILIES), "loo_lpd"]
    w = np.exp(29 * (lpd - lpd.max()))
    return (w / w.sum()).to_dict()


def fixed_rules():
    """Rules that do not depend on the fit (grids and teammate-score blends)."""
    zc, X = feature_matrix(["z_hours", "remote"])
    zh, rem = X[:, 0], X[:, 1]
    out = []
    for a in np.round(np.arange(0.12, 0.281, 0.01), 3):
        for d in np.round(np.arange(-0.20, 0.101, 0.02), 3):
            for k in (1595, 1597, 1599, 1601, 1603):
                out.append((f"linear a={a} d={d}", zc + a * zh + d * rem, k))
    for a in np.round(np.arange(0.17, 0.2301, 0.005), 3):
        for d in np.round(np.arange(-0.12, 0.0401, 0.01), 3):
            for k in range(1595, 1604):
                out.append((f"linear a={a} d={d}", zc + a * zh + d * rem, k))
    for a2 in (-0.04, -0.02, 0.02, 0.04):
        for a in np.round(np.arange(0.16, 0.241, 0.02), 3):
            for d in (-0.10, -0.05, 0.0):
                for k in (1595, 1599, 1603):
                    out.append((f"hours-curve a={a} a2={a2} d={d}", zc + a * zh + a2 * (zh ** 2 - 1) + d * rem, k))
    r4 = rankdata(zc + 0.20 * zh - 0.05 * rem)
    for name in CODEX:
        other = rankdata(np.load(ROOT / "work" / "codex_accuracy" / f"{name}_scores.npy"))
        for w in (0.25, 0.5, 0.75):
            for k in (1595, 1599, 1603):
                out.append((f"rank blend {w:.2f} x r4_16 score + {1 - w:.2f} x {name}", w * r4 + (1 - w) * other, k))
    return out


def fitted_rules(fits, weights, n_draws=60):
    out = []
    pbar_mix = np.zeros(N)
    rng = np.random.default_rng(1)
    for key, (fam, th, draws, _) in fits.items():
        sub = draws[np.linspace(0, len(draws) - 1, 200).astype(int)]
        pbar = np.mean([fam.probs(t)[0] for t in sub], axis=0)
        pbar_mix += weights[key] * pbar
        for k in range(1595, 1604):
            out.append((f"posterior-mean probability, {key}", pbar, k))
            out.append((f"MAP score, {key}", fam.score(th), k))
        if fam.m > 2:
            for t in draws[rng.choice(len(draws), n_draws, replace=False)]:
                w = " ".join(f"{n}={x:+.3f}" for n, x in zip(fam.names, t[:fam.m]))
                for k in (1595, 1599, 1603):
                    out.append((f"posterior draw {key}: {w}", fam.score(t), k))
    for k in range(1595, 1604):
        out.append(("posterior-mean probability, BMA mixture", pbar_mix, k))
    return out


def materialize(rules):
    desc = pd.DataFrame([dict(rule=r, k=k) for r, _, k in rules])
    files = np.array([top_k(s, k) for _, s, k in rules])
    _, first = np.unique(files, axis=0, return_index=True)
    first = np.sort(first)  # keep the first (simplest) description of each distinct file
    return desc.iloc[first].reset_index(drop=True), files[first]


def score_pool(fits, weights, Y, E, base, files, thresholds=(211.5, 207.5, 199.5)):
    per = {}
    for key, (fam, th, draws, _) in fits.items():
        pred = Predictor(Y, E, base, files)
        for t in draws:
            pred.add(*fam.probs(t), thresholds=thresholds)
        per[key] = pred.summary()
    mean = sum(weights[k] * per[k][0] for k in fits)
    sd = np.sqrt(sum(weights[k] * (per[k][1] ** 2 + per[k][0] ** 2) for k in fits) - mean ** 2)
    probs = {t: sum(weights[k] * per[k][2][t] for k in fits) for t in next(iter(per.values()))[2]}
    return mean, sd, probs, {k: v[0] for k, v in per.items()}


def main():
    hide = sys.argv[1] if len(sys.argv) > 1 else ""
    board, Y_all, E_all = load_board()
    names_all = board.file.str.split("/").str[-1].str.replace(".csv", "", regex=False).to_numpy()
    keep = np.array([not n.startswith(hide + "_") for n in names_all]) if hide else np.ones(len(E_all), bool)
    Y, E = Y_all[keep], E_all[keep]
    base = Y_all[list(names_all).index("r4_16")]
    weights = loo_weights(equal=bool(hide))  # backtest: no information from the hidden readings

    with Pool(len(FAMILIES)) as pool:
        fits = fit_families(Y, E, pool)
    for key, (fam, th, draws, acc) in fits.items():
        q = np.percentile(draws, [5, 50, 95], axis=0)
        desc = " ".join(f"{n}={q[1, i]:+.3f}[{q[0, i]:+.3f},{q[2, i]:+.3f}]" for i, n in enumerate(fam.names))
        print(f"{key:24s} acc={acc:.2f} sigma={np.exp(q[1, fam.m]):.3f} {desc}")
    print("family weights:", {k: round(v, 3) for k, v in weights.items()})

    rules, files = materialize(fixed_rules() + fitted_rules(fits, weights))
    grants = files.sum(1)
    d_scored = np.array([(files != y).sum(1) for y in Y_all]).min(0)  # vs ALL scored files
    mean, sd, probs, per = score_pool(fits, weights, Y, E, base, files)
    res = rules.copy()
    res["grants"] = grants
    res["min_diff_scored"] = d_scored
    res["changed_vs_r4_16"] = (files != base).sum(1)
    res["pred_err"] = mean
    res["pred_sd"] = sd
    res["P_beat_212"] = probs[211.5]
    res["P_le_207"] = probs[207.5]
    for key in fits:
        res["pred_" + key.replace("probit_", "")] = per[key]
    tag = hide or "all"
    res.to_csv(HERE / f"pool_predictions_{tag}.csv", index=False)
    np.savez_compressed(HERE / f"pool_files_{tag}.npz", bits=np.packbits(files.astype(bool), axis=1), n=files.shape[1])
    print(f"pool: {len(files)} distinct rule files")

    if hide:
        hm, hs, hp, _ = score_pool(fits, weights, Y, E, base, Y_all[~keep])
        print(f"\nHidden {hide} files (fit on {keep.sum()} readings):")
        print(pd.DataFrame({"file": names_all[~keep], "observed": E_all[~keep], "pred": hm.round(1),
                            "sd": hs.round(1), "P(<212)": hp[211.5].round(2)}).to_string(index=False))
        print(f"bias (observed - predicted) {np.mean(E_all[~keep] - hm):+.2f}")

    ok = (grants >= N_GRANT_RANGE[0]) & (grants <= N_GRANT_RANGE[1]) & (d_scored >= MIN_DIFFERENT)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 80)
    cols = ["rule", "k", "min_diff_scored", "changed_vs_r4_16", "pred_err", "pred_sd", "P_beat_212", "P_le_207"]
    print(f"\n{ok.sum()} eligible files; top 25 by P(err < 212):")
    print(res[ok].sort_values("P_beat_212", ascending=False).head(25)[cols].round(3).to_string())
    for kind in ["linear", "hours-curve", "rank blend", "MAP score", "posterior-mean"]:
        sub = res[ok & res.rule.str.startswith(kind)].sort_values("P_beat_212", ascending=False).head(3)
        print(f"\nbest '{kind}' rules:")
        print(sub[cols].round(3).to_string())


if __name__ == "__main__":
    main()
