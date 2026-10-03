"""EquiAlgo strategy 1, variant V1: counterfactual neutralisation (Pope & Sydnor, 2011).

Fit the committee's decisions *with* a remote-region flag, so the regional penalty
lands on that flag instead of leaking into proxies (distance, hours, income). Then
predict with remote = 0 for every candidate and grant the top GRANT_RATE share.

Run from equialgo-participants/:  python work/strat1/neutralise.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegressionCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]  # equialgo-participants/
sys.path.insert(0, str(ROOT / "work" / "shared"))
from data import REMOTE, features  # noqa: E402

GRANT_RATE = 0.40  # centre of the allowed 36–44% envelope
CV_FOLDS = 5
C_GRID = np.logspace(-3, 2, 12)
DECILES = 10
OUT = Path(__file__).with_name("predictions_01.csv")


def grant_top(scores, tiebreak, n_grants):
    """1 for the n_grants highest scores, ties broken by the higher tiebreak value."""
    order = np.lexsort((-tiebreak, -scores))
    grant = np.zeros(len(scores), dtype=int)
    grant[order[:n_grants]] = 1
    return grant


history = pd.read_csv(ROOT / "data" / "donnees_demandes.csv")
candidates = pd.read_csv(ROOT / "data" / "candidats_evaluation.csv")

X_train = features(history)
committee_model = make_pipeline(
    StandardScaler(),
    LogisticRegressionCV(Cs=C_GRID, cv=CV_FOLDS, scoring="roc_auc", max_iter=5000),
)
committee_model.fit(X_train, history.decision_octroi)
logit = committee_model[-1]

X_cand = features(candidates).reindex(columns=X_train.columns, fill_value=0)
n_grants = round(GRANT_RATE * len(candidates))
cote_r = candidates.cote_r_equivalent.to_numpy()

p_committee = committee_model.predict_proba(X_cand)[:, 1]
p_neutral = committee_model.predict_proba(X_cand.assign(remote=0.0))[:, 1]
grant_committee = grant_top(p_committee, cote_r, n_grants)
grant_neutral = grant_top(p_neutral, cote_r, n_grants)

pd.DataFrame({"id_candidat": candidates.id_candidat, "decision_octroi": grant_neutral}).to_csv(OUT, index=False)

# Diagnostics for report_01.md
is_remote = candidates.region_administrative.isin(REMOTE)
print(f"CV AUC (committee model): {logit.scores_[1].mean(axis=0).max():.4f}   chosen C: {logit.C_[0]:.4g}")
print("Standardised coefficients:")
print(pd.Series(logit.coef_[0], X_train.columns).round(3).sort_values().to_string())
print(f"\nGrants: {grant_neutral.sum()} / {len(candidates)} = {grant_neutral.mean():.1%}")
rates = pd.DataFrame(
    {"committee_replica": grant_committee, "neutralised": grant_neutral, "remote": is_remote}
).groupby("remote").mean().rename(index={False: "Centre", True: "Eloignee"})
print("\nGrant rate by group (candidates):")
print(rates.round(3).to_string())
decile = pd.qcut(candidates.cote_r_equivalent, DECILES, labels=False)
cond = pd.DataFrame({"decile": decile, "remote": is_remote, "g": grant_neutral})
print("\nNeutralised grant rate by cote R decile (Centre vs Eloignee):")
print(cond.groupby(["decile", "remote"]).g.mean().unstack().rename(columns={False: "Centre", True: "Eloignee"}).round(3).to_string())
print(f"\nWrote {OUT}")
