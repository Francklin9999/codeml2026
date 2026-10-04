"""Winner's-curse simulation: how optimistic is "pick the best-looking file of the pool"?

For several synthetic truths (some outside the fitted families), draw a reference
R = top-1599 of (truth score + sigma * noise), compute the synthetic exact readings of the 29
scored files, rerun the WHOLE procedure (posteriors, pool, conditional predictions), pick the
6-file batch with every selection strategy of make_batch.py, then measure their true errors.
Reports predicted vs realized gains, P(beat the best reading) vs realized frequency, per rule
kind and per strategy (the winner's-curse calibration used in make_batch.py comes from here).

Run from equialgo-participants/:  python work/agent_readings/simulate_curse.py [reps_per_truth]
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

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import make_batch as mb  # noqa: E402
import select_files as sf  # noqa: E402
from readings_lib import N, N_GRANT_RANGE, Family, candidates, load_board, log_post, top_k  # noqa: E402

warnings.filterwarnings("ignore")
sf.N_ITER, sf.BURN, sf.THIN = 8000, 2000, 12
REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 14
K_TRUE = 1599
board, Y_all, E_all = load_board()
names = board.file.str.split("/").str[-1].str.replace(".csv", "", regex=False).to_numpy()
BASE_IDX = list(names).index("r4_16")
BASE5 = sf.BASE5
PROG = ["prog_gen", "prog_sci", "prog_soc", "prog_san"]
TRUTH_SPECS = {
    "hours_remote (in family)": dict(names=["z_hours", "remote"]),
    "base5 unregularized": dict(names=BASE5),
    "base5 + programmes": dict(names=BASE5 + PROG, prior_sd=[0.5] * 5 + [0.1] * 4),
    "base5 + nonlinear": dict(names=BASE5 + ["hours2", "cotexhours", "cote2", "z_inc", "z_dist"],
                              prior_sd=[0.5] * 5 + [0.1] * 5),
    "hours_remote + postal effects": dict(names=["z_hours", "remote"]),
}


def truth_scores():
    out = {}
    for key, spec in TRUTH_SPECS.items():
        fam = Family(label=key, **spec)
        f = lambda th: -log_post(fam, th, Y_all, E_all)
        th = minimize(f, fam.x0(), method="Powell", options=dict(maxiter=40000, xtol=1e-4, ftol=1e-7)).x
        out[key] = (fam.score(th), float(np.exp(th[fam.m])))
    return out


TRUTHS = truth_scores()
FIXED = sf.fixed_rules()
POSTAL = candidates.code_postal_3.astype("category").cat.codes.to_numpy()


def replicate(args):
    truth, rep = args
    rng = np.random.default_rng(1000 * list(TRUTHS).index(truth) + rep)
    score, sigma = TRUTHS[truth]
    if "postal" in truth:
        score = score + rng.normal(0, 0.06, POSTAL.max() + 1)[POSTAL]
    R = top_k(score + sigma * rng.standard_normal(N), K_TRUE)
    E_syn = (Y_all != R[None, :]).sum(1).astype(float)
    base_err = E_syn.min()  # like reality: beat the best scored file (r4_16 = 212 is the min of 29)
    weights = sf.loo_weights(equal=True)
    fits = sf.fit_families(Y_all, E_syn, pool=None, seed=rep)
    rules, files = sf.materialize(FIXED + sf.fitted_rules(fits, weights))
    mean, sd, probs, _ = sf.score_pool(fits, weights, Y_all, E_syn, Y_all[BASE_IDX], files,
                                       thresholds=(base_err - 0.5,))
    res = rules.assign(grants=files.sum(1), min_diff_scored=np.array([(files != y).sum(1) for y in Y_all]).min(0),
                       pred_err=mean, sd=sd, P=probs[base_err - 0.5])
    realized = (files != R[None, :]).sum(1)
    ok = res.grants.between(*N_GRANT_RANGE) & (res.min_diff_scored >= sf.MIN_DIFFERENT)
    rows = []
    for strategy in mb.STRATEGIES:
        picks, _ = mb.choose(strategy, res, files, fits, weights, Y_all, E_syn, base_err - 1)
        S = mb.joint_samples(fits, weights, Y_all, E_syn, files[picks], n_draws=120, sims=100, seed=rep)
        p_any = np.mean(S.min(1) <= base_err - 1)
        for rank, i in enumerate(picks):
            rows.append(dict(truth=truth, rep=rep, strategy=strategy, rank=rank, rule=res.rule.iloc[i],
                             base_err=base_err, pred=mean[i], sd=sd[i], P=res.P.iloc[i], realized=realized[i],
                             P_any_pred=p_any, pool_best=realized[ok].min(), pool_median=np.median(realized[ok]),
                             bayes_rule=(top_k(score, K_TRUE) != R).sum()))
    return rows


if __name__ == "__main__":
    jobs = [(t, r) for t in TRUTHS for r in range(REPS)]
    with Pool(18) as pool:
        out = pool.map(replicate, jobs, chunksize=1)
    df = pd.DataFrame([row for rows in out for row in rows])
    df["gain_pred"] = df.base_err - df.pred
    df["gain_real"] = df.base_err - df.realized
    df["beat"] = (df.realized < df.base_err).astype(float)
    df["kind"] = df.rule.str.extract(r"^(posterior draw|posterior-mean|MAP score|linear|hours-curve|rank blend)")[0]
    df.to_csv(HERE / "simulate_curse.csv", index=False)
    pd.set_option("display.width", 200)
    one = df[df.strategy == "ind_all"]
    for label, sub in [("top-1 file (ind_all)", one[one["rank"] == 0]), ("all 6 batch files (ind_all)", one)]:
        print(f"\n{label}: predicted vs realized gain over the best synthetic reading")
        g = sub.groupby("truth").agg(n=("rep", "size"), pred_gain=("gain_pred", "mean"), real_gain=("gain_real", "mean"),
                                     P_pred=("P", "mean"), P_real=("beat", "mean"))
        g["optimism"] = g.pred_gain - g.real_gain
        print(g.round(2).to_string())
    print("\nper rule kind, every pick of every strategy:")
    k = df.drop_duplicates(["truth", "rep", "rule"]).assign(opt=lambda d: d.gain_pred - d.gain_real)
    print(k.groupby("kind").agg(n=("rep", "size"), optimism=("opt", "mean"),
                                se=("opt", lambda x: x.std() / np.sqrt(len(x))), P_pred=("P", "mean"),
                                P_real=("beat", "mean")).round(2).to_string())
    bat = df.groupby(["strategy", "truth", "rep"]).agg(any_beat=("beat", "max"), P_any_pred=("P_any_pred", "first"),
                                                       best_gain=("gain_real", "max"), mean_gain=("gain_real", "mean"))
    print("\nbatch level by strategy (mean over truths and replicates):")
    print(bat.groupby("strategy").agg(P_any_pred=("P_any_pred", "mean"), P_any_real=("any_beat", "mean"),
                                      best_gain_real=("best_gain", "mean"), mean_gain_real=("mean_gain", "mean"))
          .round(3).to_string())
    print("\nP(any of 6 beats the best reading), strategy x truth:")
    print(bat.any_beat.unstack("strategy").groupby("truth").mean().round(2).to_string())
    print("\nheadroom: best synthetic reading minus Bayes-rule error, and pool oracle gain:")
    one_rep = df.drop_duplicates(["truth", "rep"])
    print(one_rep.groupby("truth").apply(lambda d: pd.Series({"bayes_headroom": (d.base_err - d.bayes_rule).mean(),
                                                              "pool_oracle_gain": (d.base_err - d.pool_best).mean()}))
          .round(2).to_string())
