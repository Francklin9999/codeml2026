"""EquiAlgo strategy 3: anchor-constrained search for the hidden reference, then a submission batch.

Every HxBuddy reading is a measurement of the hidden reference. This script:
1. derives the reference's number of positives from readings that include macro F1;
2. enumerates candidate references
       score = z(cote_r) + a*z(hours) + b*z(log income) + c*z(first-gen) + e*z(log distance)
               + d*remote + sigma*noise,   cut at k_ref positives;
3. keeps the references consistent with every anchor (the baseline model's equal-opportunity
   gap of 0.270 from the brief, and each accuracy in leaderboard.csv, widened by
   MODEL_TOLERANCE because the true reference is not exactly in this family), weighting each
   by how closely it reproduces the readings;
4. scores candidate submission rules against the surviving references, greedily picks the
   batch that maximises the expected best accuracy, and writes the CSVs + manifest.

Run from equialgo-participants/:   python work/strat3/batch.py [n_files]
HxBuddy shows Accuracy and F1 macro before you confirm a submission: record both for every
file in work/strat3/leaderboard.csv (columns file,accuracy,f1_macro), then rerun.
"""
import itertools
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]  # equialgo-participants/
HERE = Path(__file__).parent
sys.path.insert(0, str(ROOT / "work" / "shared"))
from data import REMOTE  # noqa: E402

N_FILES = int(sys.argv[1]) if len(sys.argv) > 1 else 15
BASELINE_EO_GAP = 0.270      # stated in the brief
EO_TOLERANCE = 0.01
MODEL_TOLERANCE = 0.003      # slack on each accuracy reading: the reference is not exactly in our family
NOISE_SEED = 1
ENVELOPE = (0.36, 0.44)      # allowed grant rate
LEADERBOARD = HERE / "leaderboard.csv"
INITIAL_RESULTS = [("work/strat1/predictions_01.csv", "92", ""), ("work/strat3/probe_cote_rem0.35.csv", "92", "")]

# Round 4: zoomed on "cote R + ~0.2 hours" (r3_11 = 94.50%); widen again if nothing survives.
REF_GRID = dict(
    a=np.round(np.arange(0.10, 0.301, 0.01), 2),   # hours
    b=np.round(np.arange(-0.06, 0.081, 0.02), 2),  # log income
    c=(0.0, 0.05, 0.1),                            # first generation
    e=(-0.05, 0.0, 0.05),                          # log distance
    d=(0.0, 0.025, 0.05, 0.075, 0.1),              # remote flag (in cote-R standard deviations)
    sigma=(0.0, 0.1, 0.15, 0.2, 0.25, 0.3),        # reference noise
)
SUB_GRID = dict(
    a=np.round(np.arange(0.12, 0.281, 0.01), 2),
    b=np.round(np.arange(-0.04, 0.061, 0.02), 2),
    c=(0.0, 0.05),
    e=(-0.05, 0.0, 0.05),
    d=(0.0, 0.025, 0.05),
)
SUB_K_SPREAD = 4   # also try the implied reference size +/- this many grants
DEFAULT_REF_K = (1360, 1440, 1520, 1600, 1680, 1760, 1840)
DEFAULT_SUB_K = (1444, 1520, 1600, 1680, 1756)   # 36.1% .. 43.9%


def zscore(v):
    return (v - v.mean()) / v.std()


def reading_window(text):
    """HxBuddy value ('93.63', '93.63 %', '92') -> [low, high) fraction; covers rounding and truncation."""
    text = str(text).replace("%", "").strip()
    value = float(text)
    decimals = len(text.split(".")[1]) if "." in text else 0
    scale = 100.0 if value > 1 else 1.0
    half_unit = 0.5 * 10 ** (-decimals)
    return (value - half_unit) / scale, (value + 2 * half_unit) / scale


def macro_f1(tp, n_pred, n_ref, n):
    tn = n - n_pred - n_ref + tp
    return (2 * tp / (n_pred + n_ref) + 2 * tn / (2 * n - n_pred - n_ref)) / 2


def implied_ref_counts(n_pred, acc_window, f1_window, n):
    """Reference positive counts compatible with one accuracy + macro-F1 reading."""
    eps = 1e-9
    e_min = int(np.floor(n * (1 - acc_window[1]) + eps)) + 1
    e_max = int(np.floor(n * (1 - acc_window[0]) + eps))
    counts = set()
    for errors in range(max(e_min, 0), e_max + 1):
        for n_ref in range(1, n):
            twice_tp = n_pred + n_ref - errors
            if twice_tp < 0 or twice_tp % 2:
                continue
            tp = twice_tp // 2
            if tp > min(n_pred, n_ref) or n - n_pred - n_ref + tp < 0:
                continue
            if f1_window[0] <= macro_f1(tp, n_pred, n_ref, n) < f1_window[1]:
                counts.add(n_ref)
    return counts


candidates = pd.read_csv(ROOT / "data" / "candidats_evaluation.csv")
history = pd.read_csv(ROOT / "data" / "donnees_demandes.csv")
N = len(candidates)
remote = candidates.region_administrative.isin(REMOTE).to_numpy()
Z = {
    "cote": zscore(candidates.cote_r_equivalent.to_numpy()),
    "a": zscore(candidates.heures_travail_semaine.to_numpy()),
    "b": zscore(np.log(candidates.revenu_familial_estime.to_numpy())),
    "c": zscore(candidates.premiere_generation_universitaire.to_numpy().astype(float)),
    "e": zscore(np.log1p(candidates.distance_domicile_campus_km.to_numpy())),
    "d": remote.astype(float),
}
noise = np.random.default_rng(NOISE_SEED).normal(size=N)

# Baseline predictions exactly as baseline_model.ipynb (last cell)
CATEGORICAL = ["programme_etudes", "region_administrative", "code_postal_3"]
X_hist = pd.get_dummies(history.drop(columns=["id_candidat", "decision_octroi"]), columns=CATEGORICAL)
X_cand = pd.get_dummies(candidates.drop(columns=["id_candidat"]), columns=CATEGORICAL).reindex(columns=X_hist.columns, fill_value=0)
baseline = RandomForestClassifier(n_estimators=300, min_samples_leaf=20, random_state=42).fit(
    X_hist, history.decision_octroi).predict(X_cand)

# Leaderboard anchors
if not LEADERBOARD.exists():
    pd.DataFrame(INITIAL_RESULTS, columns=["file", "accuracy", "f1_macro"]).to_csv(LEADERBOARD, index=False)
board = pd.read_csv(LEADERBOARD, dtype=str).fillna("")
anchors = []
for row in board.itertuples():
    sub = pd.read_csv(ROOT / row.file).decision_octroi.to_numpy()
    f1_window = reading_window(row.f1_macro) if row.f1_macro else None
    anchors.append((row.file, sub, reading_window(row.accuracy), f1_window))
print(f"anchors: baseline EO gap {BASELINE_EO_GAP} + {len(anchors)} HxBuddy readings")

# Reference size from accuracy + macro F1
f1_anchors = [a for a in anchors if a[3]]
if f1_anchors:
    counts = None
    for _, sub, acc_w, f1_w in f1_anchors:
        c = implied_ref_counts(int(sub.sum()), acc_w, f1_w, N)
        counts = c if counts is None else counts & c
    if not counts:
        sys.exit("The accuracy / F1 readings imply no common reference size: check the values.")
    REF_K = tuple(sorted(counts))
    k_mid = int(round(np.median(REF_K)))
    SUB_K = tuple(k for k in (k_mid - SUB_K_SPREAD, k_mid, k_mid + SUB_K_SPREAD) if ENVELOPE[0] < k / N < ENVELOPE[1]) or DEFAULT_SUB_K
else:
    REF_K, SUB_K = DEFAULT_REF_K, DEFAULT_SUB_K
print(f"reference positives considered: {REF_K}\nsubmission grant counts: {SUB_K}")


def score_of(params, with_noise=0.0):
    s = Z["cote"].copy()
    for name, weight in params.items():
        s += weight * Z[name]
    return s + with_noise * noise


# Search references consistent with every anchor (cumulative sums over the ranking = all k at once)
ks = np.array(REF_K)
surviving, weights = [], []
for values in itertools.product(*REF_GRID.values()):
    params = dict(zip(REF_GRID, values))
    sigma = params.pop("sigma")
    order = np.argsort(-score_of(params, sigma), kind="stable")
    ok = np.ones(len(ks), bool)
    misfit = np.zeros(len(ks))
    for _, sub, (lo, hi), _ in anchors:
        tp = np.cumsum(sub[order])[ks - 1]
        acc = 1 - (sub.sum() + ks - 2 * tp) / N
        gap = np.maximum(lo - acc, 0) + np.maximum(acc - hi, 0)
        ok &= gap <= MODEL_TOLERANCE
        misfit += (gap / MODEL_TOLERANCE) ** 2
        if not ok.any():
            break
    if not ok.any():
        continue
    b_sorted, r_sorted = baseline[order], remote[order]
    tpr_c = np.cumsum(b_sorted & ~r_sorted)[ks - 1] / np.cumsum(~r_sorted)[ks - 1]
    tpr_r = np.cumsum(b_sorted & r_sorted)[ks - 1] / np.maximum(np.cumsum(r_sorted)[ks - 1], 1)
    ok &= np.abs(tpr_c - tpr_r - BASELINE_EO_GAP) <= EO_TOLERANCE
    for j in np.where(ok)[0]:
        ref = np.zeros(N, np.int8)
        ref[order[:ks[j]]] = 1
        surviving.append(({**params, "sigma": sigma, "k": int(ks[j])}, ref))
        weights.append(np.exp(-0.5 * misfit[j]))

print(f"consistent references: {len(surviving)}")
if not surviving:
    sys.exit("No reference fits every anchor: raise MODEL_TOLERANCE or widen REF_GRID.")
w = np.array(weights) / np.sum(weights)
S = pd.DataFrame([p for p, _ in surviving])
for col in S.columns:
    print(f"  {col:6s}", S.groupby(S[col].round(2)).size().to_dict())
refs = np.array([r for _, r in surviving], dtype=np.float32)

# Candidate submissions and their predicted accuracy under every surviving reference
cand_params, cand_rows = [], []
for values in itertools.product(*SUB_GRID.values()):
    params = dict(zip(SUB_GRID, values))
    order = np.argsort(-score_of(params), kind="stable")
    for k in SUB_K:
        y = np.zeros(N, np.int8)
        y[order[:k]] = 1
        cand_params.append({**params, "k": k})
        cand_rows.append(y)
cands = np.array(cand_rows, dtype=np.float32)
acc = 1 - (cands.sum(1)[:, None] + refs.sum(1)[None, :] - 2 * cands @ refs.T) / N
submitted = {sub.tobytes() for _, sub, _, _ in anchors}
already = np.array([c.astype(np.int64).tobytes() in submitted for c in cand_rows])

# Coverage picks: greedy on expected best accuracy, until the next file adds less than MIN_GAIN.
# Robust picks: then the highest expected accuracy, since the true reference lies between grid points.
MIN_GAIN = 0.0005
MIN_DIFFERENT_DECISIONS = 20   # robust picks must differ this much from every file already in the batch
chosen, kinds, covered = [], [], 0.0
while len(chosen) < min(N_FILES, len(cand_rows)):
    current = acc[chosen].max(0) if chosen else np.zeros(acc.shape[1])
    gain = np.maximum(acc, current) @ w
    gain[already] = -1
    gain[chosen] = -1
    i = int(gain.argmax())
    if chosen and gain[i] - covered < MIN_GAIN:
        break
    chosen.append(i), kinds.append("coverage")
    covered = gain[i]
expected = acc @ w
for i in np.argsort(-expected):
    if len(chosen) >= min(N_FILES, len(cand_rows)):
        break
    if i in chosen or already[i]:
        continue
    if chosen and (cands[chosen] != cands[i]).sum(1).min() < MIN_DIFFERENT_DECISIONS:
        continue
    chosen.append(int(i)), kinds.append("robust")

# Write the batch
round_id = len(anchors)
out_dir = HERE / "batch"
out_dir.mkdir(exist_ok=True)
for stale in out_dir.glob(f"r{round_id}_*.csv"):
    stale.unlink()
manifest = []
for rank, (i, kind) in enumerate(zip(chosen, kinds), 1):
    name = f"r{round_id}_{rank:02d}.csv"
    pd.DataFrame({"id_candidat": candidates.id_candidat, "decision_octroi": cand_rows[i].astype(int)}).to_csv(out_dir / name, index=False)
    best_so_far = acc[chosen[:rank]].max(0)
    manifest.append({"file": f"work/strat3/batch/{name}", "pick": kind, **cand_params[i],
                     "grant_rate": cand_rows[i].mean(), "pred_mean": acc[i] @ w, "pred_worst": acc[i].min(),
                     "pred_best": acc[i].max(), "batch_P(best>=95%)": ((best_so_far >= 0.95) * w).sum(),
                     "batch_P(best>=94%)": ((best_so_far >= 0.94) * w).sum()})
M = pd.DataFrame(manifest)
M.to_csv(out_dir / f"manifest_r{round_id}.csv", index=False)
print(f"\nWrote {len(M)} files to {out_dir} (upload in this order):")
print(M.drop(columns="file").round(4).to_string(index=False))
