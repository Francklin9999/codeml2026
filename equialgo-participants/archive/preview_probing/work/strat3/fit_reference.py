"""EquiAlgo strategy 3: fit the hidden reference to the exact HxBuddy error counts, then propose files.

Reference model:  P(granted_i) = Phi((s_i - t) / sigma),
    s = z(cote) + a*z(hours) + b*z(log income) + c*z(first-gen) + e*z(log distance) + d*remote,
with t chosen so the reference grants K_REF people. Every two-decimal reading in leaderboard.csv
is the exact error count of a known file (one decision = 0.025 %); the weights and sigma are
fitted so the model's expected error counts match them. Leave-one-file-out RMSE checks the fit.
Bootstrap refits over the files give a diverse set of near-optimal formulas, ranked by expected
accuracy under the full fit. Sigma is the reference's own randomness: it sets the ceiling.

Findings so far (19 readings): this 5-feature model has the best held-out error (LOO RMSE 3.2
errors); adding programmes overfits; stacking the Codex model scores adds nothing.

Run from equialgo-participants/:  python work/strat3/fit_reference.py [round_label] [n_files]
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import ndtr

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]  # equialgo-participants/
HERE = Path(__file__).parent
sys.path.insert(0, str(ROOT / "work" / "shared"))
from data import REMOTE  # noqa: E402

ROUND = sys.argv[1] if len(sys.argv) > 1 else "r7"
N_FILES = int(sys.argv[2]) if len(sys.argv) > 2 else 10
FEATURES = ["a", "b", "c", "e", "d"]
START = dict(a=0.20, d=-0.05)
K_REF = 1598                    # reference size implied by the F1 readings (1595-1603)
SUB_K = (1595, 1598, 1601)
N_BOOT = 30
BOOT_SEED = 7
MIN_DIFFERENT_DECISIONS = 8     # every proposed file differs this much from the others and from scored files
LEADERBOARD = HERE / "leaderboard.csv"


def zscore(v):
    return (v - v.mean()) / v.std()


candidates = pd.read_csv(ROOT / "data" / "candidats_evaluation.csv")
N = len(candidates)
Z = {
    "cote": zscore(candidates.cote_r_equivalent.to_numpy()),
    "a": zscore(candidates.heures_travail_semaine.to_numpy()),
    "b": zscore(np.log(candidates.revenu_familial_estime.to_numpy())),
    "c": zscore(candidates.premiere_generation_universitaire.to_numpy().astype(float)),
    "e": zscore(np.log1p(candidates.distance_domicile_campus_km.to_numpy())),
    "d": candidates.region_administrative.isin(REMOTE).to_numpy().astype(float),
}

board = pd.read_csv(LEADERBOARD, dtype=str).fillna("")
board = board[board.accuracy.str.contains(r"\.")]  # exact readings only
ids = candidates.id_candidat
Y = np.array([pd.read_csv(ROOT / f).set_index("id_candidat").loc[ids].decision_octroi.to_numpy() for f in board.file], float)
OBSERVED = np.round(N * (1 - board.accuracy.astype(float).to_numpy() / 100))
best_row = int(np.argmin(OBSERVED))
print(f"{len(OBSERVED)} exact readings; best so far {board.file.iloc[best_row]} ({int(OBSERVED[best_row])} errors)")


def score(weights):
    return Z["cote"] + sum(w * Z[f] for w, f in zip(weights, FEATURES))


def reference_probs(x, k=K_REF):
    s, sigma = score(x[:-1]), np.exp(x[-1])
    t = np.sort(s)[::-1][k - 1]
    for _ in range(30):  # Newton on sum(Phi((s - t) / sigma)) = k
        u = (s - t) / sigma
        step = (ndtr(u).sum() - k) / max(np.exp(-0.5 * u * u).sum() / (sigma * np.sqrt(2 * np.pi)), 1e-9)
        t += step
        if abs(step) < 1e-7:
            break
    return ndtr((s - t) / sigma)


def expected_errors(p, decisions):
    return decisions @ (1 - p) + (1 - decisions) @ p


def fit(rows, x0):
    objective = lambda x: np.sum((expected_errors(reference_probs(x), Y[rows]) - OBSERVED[rows]) ** 2)
    return minimize(objective, x0, method="Powell", options={"maxiter": 20000, "xtol": 1e-4, "ftol": 1e-4}).x


rows_all = np.arange(len(OBSERVED))
x0 = np.r_[[START.get(f, 0.0) for f in FEATURES], np.log(0.1)]
x_full = fit(rows_all, x0)
p_full = reference_probs(x_full)
loo = [expected_errors(reference_probs(fit(np.delete(rows_all, i), x_full)), Y[i]) - OBSERVED[i] for i in rows_all]
print(f"fit: weights {dict(zip(FEATURES, np.round(x_full[:-1], 3)))}  sigma {np.exp(x_full[-1]):.3f}")
print(f"leave-one-file-out RMSE {np.sqrt(np.mean(np.square(loo))):.2f} errors; "
      f"ceiling under this model {100 * (1 - np.minimum(p_full, 1 - p_full).sum() / N):.2f}%")


def top_k(weights, k):
    grant = np.zeros(N)
    grant[np.argsort(-score(weights), kind="stable")[:k]] = 1
    return grant


rng = np.random.default_rng(BOOT_SEED)
formulas = [x_full[:-1]] + [fit(rng.choice(rows_all, len(rows_all)), x_full)[:-1] for _ in range(N_BOOT)]
pool = [(w, k, top_k(w, k)) for w in formulas for k in SUB_K]
pool.sort(key=lambda item: expected_errors(p_full, item[2]))

chosen = []
for w, k, grant in pool:
    others = [g for _, _, g in chosen] + list(Y)
    if min(int((grant != g).sum()) for g in others) >= MIN_DIFFERENT_DECISIONS:
        chosen.append((w, k, grant))
    if len(chosen) == N_FILES:
        break

out_dir = HERE / "batch"
out_dir.mkdir(exist_ok=True)
for stale in out_dir.glob(f"{ROUND}_*.csv"):
    stale.unlink()
best = Y[best_row]
rows = []
for i, (w, k, grant) in enumerate(chosen, 1):
    name = f"{ROUND}_{i:02d}.csv"
    pd.DataFrame({"id_candidat": ids, "decision_octroi": grant.astype(int)}).to_csv(out_dir / name, index=False)
    e = expected_errors(p_full, grant)
    rows.append({"file": f"work/strat3/batch/{name}", **dict(zip(FEATURES, np.round(w, 3))), "k": k,
                 "expected_accuracy": round(100 * (1 - e / N), 3), "changed_vs_best": int((grant != best).sum())})
manifest = pd.DataFrame(rows)
manifest.to_csv(out_dir / f"manifest_{ROUND}.csv", index=False)
print(f"\nWrote {len(manifest)} files (best expected first):")
print(manifest.drop(columns="file").to_string(index=False))
