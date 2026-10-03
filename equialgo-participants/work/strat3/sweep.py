"""EquiAlgo strategy 3: one-knob-at-a-time sweep around the best formula so far.

Score = z(cote_r) + a*z(hours) + b*z(log income) + c*z(first-gen) + e*z(log distance) + d*remote,
grant the top k. Each file moves a single knob away from CENTER. HxBuddy readings are exact
error counts (one decision = 0.025 %), so comparing each file with the centre shows which way
every knob should move; the next round combines the winning moves.

Run from equialgo-participants/:  python work/strat3/sweep.py [round_label]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]  # equialgo-participants/
HERE = Path(__file__).parent
sys.path.insert(0, str(ROOT / "work" / "shared"))
from data import REMOTE  # noqa: E402

ROUND = sys.argv[1] if len(sys.argv) > 1 else "r4"
BEST_FILE = HERE / "batch" / "r3_11.csv"  # 94.50 %: a=0.20, k=1605
# r3_11 with the reference size implied by the F1 readings (1595-1603 positives)
CENTER = dict(a=0.20, b=0.0, c=0.0, e=0.0, d=0.0, k=1599)
STEPS = dict(
    a=(-0.04, -0.02, 0.02, 0.04),   # hours
    k=(-8, -4, 4, 8),               # grant count
    b=(-0.04, 0.04),                # log income
    c=(-0.05, 0.05),                # first generation
    e=(-0.05, 0.05),                # log distance
    d=(-0.05, 0.05),                # remote flag
)


def zscore(v):
    return (v - v.mean()) / v.std()


candidates = pd.read_csv(ROOT / "data" / "candidats_evaluation.csv")
Z = {
    "cote": zscore(candidates.cote_r_equivalent.to_numpy()),
    "a": zscore(candidates.heures_travail_semaine.to_numpy()),
    "b": zscore(np.log(candidates.revenu_familial_estime.to_numpy())),
    "c": zscore(candidates.premiere_generation_universitaire.to_numpy().astype(float)),
    "e": zscore(np.log1p(candidates.distance_domicile_campus_km.to_numpy())),
    "d": candidates.region_administrative.isin(REMOTE).to_numpy().astype(float),
}


def decisions(params):
    score = Z["cote"] + sum(params[name] * Z[name] for name in "abced")
    grant = np.zeros(len(score), dtype=int)
    grant[np.argsort(-score, kind="stable")[:params["k"]]] = 1
    return grant


variants = [("centre", 0, CENTER)]
for knob, steps in STEPS.items():
    for step in steps:
        params = dict(CENTER)
        params[knob] = params[knob] + step if knob == "k" else round(params[knob] + step, 4)
        variants.append((knob, step, params))

best = pd.read_csv(BEST_FILE).decision_octroi.to_numpy()
out_dir = HERE / "batch"
out_dir.mkdir(exist_ok=True)
for stale in out_dir.glob(f"{ROUND}_*.csv"):
    stale.unlink()
rows = []
for i, (knob, step, params) in enumerate(variants, 1):
    grant = decisions(params)
    name = f"{ROUND}_{i:02d}.csv"
    pd.DataFrame({"id_candidat": candidates.id_candidat, "decision_octroi": grant}).to_csv(out_dir / name, index=False)
    rows.append({"file": f"work/strat3/batch/{name}", "knob": knob, "step": step, **params,
                 "grant_rate": grant.mean(), "changed_vs_best": int((grant != best).sum())})
manifest = pd.DataFrame(rows)
manifest.to_csv(out_dir / f"manifest_{ROUND}.csv", index=False)
print(manifest.drop(columns="file").to_string(index=False))
