"""EquiAlgo strategy 3: targeted variants around the best file (combined moves + structural tests).

Score = z(cote_r) + a*z(hours) + b*z(log income) + c*z(first-gen) + e*z(log distance) + d*remote
        + inter * z(cote_r)*z(hours);   grant the top k overall, or the top k/N within each
programme when quota="programme". Edit VARIANTS for the next round.

Run from equialgo-participants/:  python work/strat3/explore.py [round_label]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]  # equialgo-participants/
HERE = Path(__file__).parent
sys.path.insert(0, str(ROOT / "work" / "shared"))
from data import REMOTE  # noqa: E402

ROUND = sys.argv[1] if len(sys.argv) > 1 else "r6"
BEST_FILE = HERE / "batch" / "r4_16.csv"  # 94.70 % (212 errors)
BEST = dict(a=0.20, b=0.0, c=0.0, e=0.0, d=-0.05, k=1599, inter=0.0, quota=None, cote_norm=None, blend=0.0)
SPLINE_SCORES = ROOT / "work" / "codex_accuracy" / "model_B_spline_academic_hours_scores.npy"  # 94.68 %
ROUNDS = {
    "r5": [
        ("best + distance -0.05 (combine both winners)", dict(e=-0.05)),
        ("remote -0.10", dict(d=-0.10)),
        ("remote -0.10 + distance -0.05", dict(d=-0.10, e=-0.05)),
        ("best + income +0.04", dict(b=0.04)),
        ("income +0.06 instead of remote term", dict(b=0.06, d=0.0)),
        ("best, 40% within each programme", dict(quota="programme")),
        ("best, hours 0.18", dict(a=0.18)),
        ("best, hours 0.22", dict(a=0.22)),
        ("best, 1595 grants", dict(k=1595)),
        ("best, 1603 grants", dict(k=1603)),
        ("best + cote x hours interaction -0.05", dict(inter=-0.05)),
    ],
    "r6": [
        ("best + distance -0.05 (combine both winners)", dict(e=-0.05)),
        ("remote -0.10", dict(d=-0.10)),
        ("best + income +0.04", dict(b=0.04)),
        ("income +0.06 instead of remote term", dict(b=0.06, d=0.0)),
        ("best, 40% within each programme", dict(quota="programme")),
        ("best, cote R z-scored within programme", dict(cote_norm="programme")),
        ("best, hours 0.18", dict(a=0.18)),
        ("best, hours 0.22", dict(a=0.22)),
        ("best + first-gen +0.05", dict(c=0.05)),
        ("best + first-gen -0.05", dict(c=-0.05)),
        ("best, 1595 grants", dict(k=1595)),
        ("best, 1603 grants", dict(k=1603)),
        ("rank average: best formula 50% + teammate spline 50%", dict(blend=0.5)),
    ],
}
VARIANTS = ROUNDS[ROUND]


def zscore(v):
    return (v - v.mean()) / v.std()


candidates = pd.read_csv(ROOT / "data" / "candidats_evaluation.csv")
N = len(candidates)
programme = candidates.programme_etudes.to_numpy()
Z = {
    "cote": zscore(candidates.cote_r_equivalent.to_numpy()),
    "a": zscore(candidates.heures_travail_semaine.to_numpy()),
    "b": zscore(np.log(candidates.revenu_familial_estime.to_numpy())),
    "c": zscore(candidates.premiere_generation_universitaire.to_numpy().astype(float)),
    "e": zscore(np.log1p(candidates.distance_domicile_campus_km.to_numpy())),
    "d": candidates.region_administrative.isin(REMOTE).to_numpy().astype(float),
}


cote_raw = candidates.cote_r_equivalent.to_numpy()
cote_by_programme = np.empty(N)
for prog in np.unique(programme):
    m = programme == prog
    cote_by_programme[m] = zscore(cote_raw[m])
spline = np.load(SPLINE_SCORES)


def percentile(v):
    return (np.argsort(np.argsort(v, kind="stable"), kind="stable") + 1) / len(v)


def decisions(p):
    cote = cote_by_programme if p["cote_norm"] == "programme" else Z["cote"]
    score = cote + sum(p[name] * Z[name] for name in "abced") + p["inter"] * cote * Z["a"]
    if p["blend"]:
        score = (1 - p["blend"]) * percentile(score) + p["blend"] * percentile(spline)
    grant = np.zeros(N, dtype=int)
    if p["quota"] == "programme":
        for prog in np.unique(programme):
            idx = np.where(programme == prog)[0]
            n_prog = int(round(p["k"] / N * len(idx)))
            grant[idx[np.argsort(-score[idx], kind="stable")[:n_prog]]] = 1
    else:
        grant[np.argsort(-score, kind="stable")[:p["k"]]] = 1
    return grant


best = pd.read_csv(BEST_FILE).decision_octroi.to_numpy()
out_dir = HERE / "batch"
out_dir.mkdir(exist_ok=True)
for stale in out_dir.glob(f"{ROUND}_*.csv"):
    stale.unlink()
rows = []
for i, (label, change) in enumerate(VARIANTS, 1):
    params = {**BEST, **change}
    grant = decisions(params)
    name = f"{ROUND}_{i:02d}.csv"
    pd.DataFrame({"id_candidat": candidates.id_candidat, "decision_octroi": grant}).to_csv(out_dir / name, index=False)
    rows.append({"file": f"work/strat3/batch/{name}", "test": label, **params,
                 "grants": int(grant.sum()), "changed_vs_best": int((grant != best).sum())})
manifest = pd.DataFrame(rows)
manifest.to_csv(out_dir / f"manifest_{ROUND}.csv", index=False)
print(manifest.drop(columns="file").to_string(index=False))
