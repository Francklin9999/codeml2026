"""Pick the submission batch from the scored pool, write the CSVs and manifest.csv, validate them.

The joint predictive distribution of the shortlisted files' error counts, conditional on every
reading, is sampled per posterior draw (mixture of the families). Selection strategies (all keep
every file >= 8 decisions from each other and from every scored file):
  ind_all      greedy by each file's own P(err <= 211), random posterior-draw rules allowed
  ind_nodraw   same without random posterior-draw rules (the most curse-prone kind)
  joint_raw    greedy maximisation of P(min error of the batch <= 211), raw model samples
  joint_shift  same on samples shifted by the winner's-curse optimism DELTA
  mean_nodraw  lowest predicted error first
simulate_curse.py compares them on synthetic truths; STRATEGY picks the one used here.
Reported predictions: raw model, and calibrated (mean + DELTA, sd * LAMBDA) from that simulation.

Run from equialgo-participants/ after select_files.py:  python work/agent_readings/make_batch.py
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
from scipy.special import ndtr  # noqa: E402

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import select_files as sf  # noqa: E402
from posterior import joint_conditional  # noqa: E402
from readings_lib import N_GRANT_RANGE, ROOT, ids, load_board  # noqa: E402

warnings.filterwarnings("ignore")
N_FILES = 6
SHORTLIST = 150
DELTA = float(os.environ.get("DELTA", 2.46))     # winner's-curse shift in errors (simulate_curse.py)
LAMBDA = float(os.environ.get("LAMBDA", 1.5))    # predictive spread inflation (simulate_curse.py)
STRATEGY = os.environ.get("STRATEGY", "joint_raw")
STRATEGIES = ("ind_all", "ind_nodraw", "joint_raw", "joint_shift", "mean_nodraw")
# Teammates' files not yet scored: picks stay >= MIN_DIFFERENT decisions away from all of them; the
# rule-based ones (dgp_01..03, staged in the since-removed upload_r8) are treated as uploaded anyway
# when maximising P(any beats 212).
PENDING_RULE = sorted(str(p) for p in (ROOT / "work" / "agent_dgp").glob("dgp_0[123]_*.csv"))
PENDING_OTHER = sorted(str(p) for p in list((ROOT / "upload_codex_v2").glob("0[1-9]*.csv")) +
                       list((ROOT / "work" / "agent_dgp").glob("dgp_*.csv")))


def load_file(path):
    return pd.read_csv(path).set_index("id_candidat").loc[ids].decision_octroi.to_numpy().astype(float)


def joint_samples(fits, weights, Y, E, F, n_draws=300, sims=100, seed=3):
    rng = np.random.default_rng(seed)
    out = []
    for key, (fam, th, draws, _) in fits.items():
        n = int(round(n_draws * weights[key]))
        for t in draws[rng.choice(len(draws), n, replace=True)]:
            m, C = joint_conditional(*fam.probs(t), Y, E, F)
            L = np.linalg.cholesky(C + 1e-6 * np.eye(len(F)))
            out.append(m[None, :] + rng.standard_normal((sims, len(F))) @ L.T)
    return np.vstack(out)


def greedy(order_or_samples, F, threshold, n=N_FILES, min_diff=sf.MIN_DIFFERENT, fixed=None):
    """order (1-D index array): take in order with diversity; samples (2-D): maximise P(batch min <= thr).
    fixed: joint samples of files that will be uploaded anyway (their min starts the batch)."""
    chosen = []
    if np.ndim(order_or_samples) == 1:
        for i in order_or_samples:
            if all((F[i] != F[j]).sum() >= min_diff for j in chosen):
                chosen.append(i)
            if len(chosen) == n:
                break
        return chosen
    S = order_or_samples
    for _ in range(n):
        cur = np.full(len(S), np.inf) if fixed is None else fixed.min(1)
        if chosen:
            cur = np.minimum(cur, S[:, chosen].min(1))
        best_i, best_p = None, -1.0
        for i in range(S.shape[1]):
            if i in chosen or any((F[i] != F[j]).sum() < min_diff for j in chosen):
                continue
            p = np.mean(np.minimum(cur, S[:, i]) <= threshold)
            if p > best_p:
                best_i, best_p = i, p
        if best_i is None:
            break
        chosen.append(best_i)
    return chosen


def choose(strategy, res, files, fits, weights, Y, E, threshold, pending=None):
    """Return pool indices of the batch and the shortlist joint samples (for reporting).
    pending: files teammates will upload anyway; picks keep >= MIN_DIFFERENT decisions from them and
    the joint strategies maximise P(min over pending + batch <= threshold)."""
    eligible = res.grants.between(*N_GRANT_RANGE).to_numpy() & (res.min_diff_scored >= sf.MIN_DIFFERENT).to_numpy()
    if pending is not None and len(pending):
        eligible &= np.array([(files != f).sum(1) for f in pending]).min(0) >= sf.MIN_DIFFERENT
    nodraw = eligible & ~res.rule.str.startswith("posterior draw").to_numpy()
    if strategy == "ind_all":
        idx = np.where(eligible)[0]
        return idx[_ordered(idx, -res.P.to_numpy()[idx], files, threshold)], None
    if strategy == "ind_nodraw":
        idx = np.where(nodraw)[0]
        return idx[_ordered(idx, -res.P.to_numpy()[idx], files, threshold)], None
    if strategy == "mean_nodraw":
        idx = np.where(nodraw)[0]
        return idx[_ordered(idx, res.pred_err.to_numpy()[idx], files, threshold)], None
    idx = np.where(nodraw)[0]
    short = idx[np.argsort(-res.P.to_numpy()[idx], kind="stable")[:SHORTLIST]]
    n_pend = 0 if pending is None else len(pending)
    S = joint_samples(fits, weights, Y, E, np.vstack([files[short]] + ([pending] if n_pend else [])))
    shift = DELTA if strategy == "joint_shift" else 0.0
    S, fixed = S[:, :len(short)], (S[:, len(short):] if n_pend else None)
    picks = greedy(S + shift, files[short], threshold, fixed=None if fixed is None else fixed + shift)
    return short[picks], S[:, picks]


def _ordered(idx, key, files, threshold):
    """Positions (within idx) of the batch taken in increasing order of key."""
    return greedy(np.argsort(key, kind="stable"), files[idx], threshold)


def write_batch(res, files, picks, S, base):
    rows = []
    best = 212
    for col, i in enumerate(picks):
        rank = col + 1
        grant = files[i].astype(int)
        name = f"ar_{rank:02d}.csv"
        pd.DataFrame({"id_candidat": ids, "decision_octroi": grant}).to_csv(HERE / name, index=False)
        r = res.loc[i]
        s = S[:, col]
        mean, sd = s.mean(), s.std()
        model = r.rule.split(",")[-1].strip() if r.rule.startswith(("MAP", "posterior-mean")) else \
            " ".join(r.rule.split(" ")[:2]) if r.rule.startswith("rank") else r.rule.split(" ")[0]
        rows.append({
            "file": f"work/agent_readings/{name}",
            "model": model,
            "rule": f"top {int(r.k)} by {r.rule}",
            "grants": int(grant.sum()),
            "pred_errors_model": round(mean, 1),
            "pred_sd_model": round(sd, 1),
            "P_beat_212_model": round(np.mean(s <= best - 1), 3),
            "pred_errors_calibrated": round(mean + DELTA, 1),
            "pred_sd_calibrated": round(LAMBDA * sd, 1),
            "P_beat_212_calibrated": round(float(ndtr((best - 0.5 - mean - DELTA) / (LAMBDA * sd))), 3),
            "changed_vs_r4_16": int((grant != base).sum()),
            "min_diff_scored_files": int(r.min_diff_scored),
        })
    return pd.DataFrame(rows)


def validate(man, Y_scored):
    cand_ids = pd.read_csv(ROOT / "data" / "candidats_evaluation.csv").id_candidat
    grants = []
    for f in man.file:
        df = pd.read_csv(ROOT / f)
        assert list(df.columns) == ["id_candidat", "decision_octroi"], f
        assert len(df) == 4000 and (df.id_candidat.to_numpy() == cand_ids.to_numpy()).all(), f
        assert set(df.decision_octroi.unique()) <= {0, 1}, f
        g = df.decision_octroi.to_numpy()
        assert N_GRANT_RANGE[0] <= g.sum() <= N_GRANT_RANGE[1], f
        assert min(int((g != y).sum()) for y in Y_scored) >= sf.MIN_DIFFERENT, f
        grants.append(g)
    for a in range(len(grants)):
        for b in range(a + 1, len(grants)):
            assert (grants[a] != grants[b]).sum() >= sf.MIN_DIFFERENT, (a, b)
    print(f"validated {len(grants)} files: header, 4000 rows in candidate order, 0/1, "
          f"{N_GRANT_RANGE[0]}-{N_GRANT_RANGE[1]} grants, >= {sf.MIN_DIFFERENT} decisions from every scored file, "
          f"every pending teammate file and each other")


def main():
    board, Y_all, E_all = load_board()
    names = board.file.str.split("/").str[-1].str.replace(".csv", "", regex=False).to_numpy()
    base = Y_all[list(names).index("r4_16")]
    res = pd.read_csv(HERE / "pool_predictions_all.csv").rename(columns={"P_beat_212": "P"})
    packed = np.load(HERE / "pool_files_all.npz")
    files = np.unpackbits(packed["bits"], axis=1, count=int(packed["n"])).astype(float)
    pend_rule = [load_file(f) for f in PENDING_RULE]
    pend_all = np.array(pend_rule + [load_file(f) for f in PENDING_OTHER])
    weights = sf.loo_weights()
    with Pool(len(sf.FAMILIES)) as pool:
        fits = sf.fit_families(Y_all, E_all, pool, seed=7)
    far = np.array([(files != f).sum(1) for f in pend_all]).min(0) >= sf.MIN_DIFFERENT
    res_far = res.assign(min_diff_scored=np.where(far, res.min_diff_scored, 0))  # drop near-duplicates of pending
    picks, _ = choose(STRATEGY, res_far, files, fits, weights, Y_all, E_all, 211,
                      pending=np.array(pend_rule) if pend_rule else None)
    S_all = joint_samples(fits, weights, Y_all, E_all, np.vstack([files[picks]] + pend_rule), n_draws=400,
                          sims=150, seed=11)
    S, S_pend = S_all[:, :len(picks)], S_all[:, len(picks):]
    man = write_batch(res, files, picks, S, base)
    man["min_diff_team_pending"] = [int(np.array([(files[i] != f).sum() for f in pend_all]).min()) for i in picks]
    for key, (fam, th, _, _) in fits.items():  # spell out the fitted rules
        terms = " ".join(f"{w:+.3f} {n}" for n, w in zip(fam.names, th[:fam.m]))
        man["rule"] = man.rule.str.replace(f"MAP score, {key}", f"z_cote {terms} (MAP of {key})", regex=False)
        man["rule"] = man.rule.str.replace(f"posterior-mean probability, {key}",
                                           f"posterior-mean P(ref=1) over 200 draws of {key} "
                                           f"[z_cote + w.({', '.join(fam.names)}), sigma]", regex=False)
    man.to_csv(HERE / "manifest.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 90)
    print(f"strategy {STRATEGY}")
    print(man.drop(columns=["file"]).to_string(index=False))
    Sc = S.mean(0) + DELTA + LAMBDA * (S - S.mean(0))
    print(f"\nP(at least one beats 212): model {np.mean(S.min(1) <= 211):.3f}, calibrated {np.mean(Sc.min(1) <= 211):.3f}")
    print(f"P(at least one <= 207):    model {np.mean(S.min(1) <= 207):.3f}, calibrated {np.mean(Sc.min(1) <= 207):.3f}")
    if pend_rule:
        print(f"with the teammates' pending rule files ({', '.join(Path(f).name for f in PENDING_RULE)}): "
              f"P(any beats 212) model {np.mean(np.minimum(S.min(1), S_pend.min(1)) <= 211):.3f} "
              f"vs pending alone {np.mean(S_pend.min(1) <= 211):.3f}")
    print("pairwise differences between chosen files:")
    print(np.array([[int((files[i] != files[j]).sum()) for j in picks] for i in picks]))
    validate(man, np.vstack([Y_all, pend_all]))


if __name__ == "__main__":
    main()
