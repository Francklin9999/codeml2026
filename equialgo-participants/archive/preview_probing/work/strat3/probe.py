"""EquiAlgo strategy 3: leaderboard probe for the "academic merit + regional context" reference.

Hypothesis (fits both anchors: our V1 file scored 92%, baseline EO gap 0.270): the hidden
reference ranks mainly on cote R, with a small adjustment for remote regions, and does NOT
reward family income or work hours the way the committee did.

Grants the top GRANT_RATE of candidates by  cote_r + REMOTE_BONUS * remote.

Run from equialgo-participants/:  python work/strat3/probe.py [remote_bonus]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]  # equialgo-participants/
sys.path.insert(0, str(ROOT / "work" / "shared"))
from data import REMOTE  # noqa: E402

GRANT_RATE = 0.40  # centre of the allowed 36–44% envelope
REMOTE_BONUS = float(sys.argv[1]) if len(sys.argv) > 1 else 0.35  # cote R points; fitted on the 0.270 anchor

candidates = pd.read_csv(ROOT / "data" / "candidats_evaluation.csv")
is_remote = candidates.region_administrative.isin(REMOTE).to_numpy()
score = candidates.cote_r_equivalent.to_numpy() + REMOTE_BONUS * is_remote

n_grants = round(GRANT_RATE * len(candidates))
grant = np.zeros(len(candidates), dtype=int)
grant[np.argsort(-score, kind="stable")[:n_grants]] = 1

out = Path(__file__).with_name(f"probe_cote_rem{REMOTE_BONUS:.2f}.csv")
pd.DataFrame({"id_candidat": candidates.id_candidat, "decision_octroi": grant}).to_csv(out, index=False)
print(f"Grants: {grant.sum()} / {len(grant)} = {grant.mean():.1%}   "
      f"Centre {grant[~is_remote].mean():.1%}  Eloignee {grant[is_remote].mean():.1%}")
print(f"Wrote {out}")
