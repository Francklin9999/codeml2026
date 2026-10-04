"""Lot 2 : 20 fichiers « U + une cellule de 7 retouches », triés par gain attendu. Écrit sondes/lot2/ et cellules.csv."""
import os, numpy as np, pandas as pd
import engine as E, retouches as R
from engine import N, g

n = 7
OUT = E.ROOT + 'sondes/lot2/'
os.makedirs(OUT, exist_ok=True)
cs = R.cellules(n)[:20]
rows = []
for j, (gain, side, grp, idx) in enumerate(cs, 1):
    F = R.U.copy(); F[idx] = 1 - F[idx]
    nom = f'R{j:02d}'
    pd.DataFrame({'id_candidat': E.cand.id_candidat, 'decision_octroi': F.astype(int)}).to_csv(OUT + nom + '.csv', index=False)
    chk = pd.read_csv(OUT + nom + '.csv')
    assert len(chk) == N and set(chk.decision_octroi) <= {0, 1} and chk.id_candidat.tolist() == E.cand.id_candidat.tolist()
    assert int((F != R.U).sum()) == n
    for i in idx:
        rows.append(dict(cellule=nom, id_candidat=E.cand.id_candidat[i], U=int(R.U[i]), eloignee=int(grp), p_erreur=round(float(R.perr[i]), 3)))
    print(f'{nom} : {"retraits" if side == 1 else "ajouts  "} | {"éloignées" if grp else "centres  "} | P(U faux) moyen {R.perr[idx].mean():.2f} | gain attendu {gain:+.2f} | octrois {int(F.sum())}')
pd.DataFrame(rows).to_csv(OUT + 'cellules.csv', index=False)
tot = [sum(c[0] for c in cs[:k]) for k in (9, 14, 20)]
print('gain attendu cumulé : 9 fichiers %.1f | 14 fichiers %.1f | 20 fichiers %.1f' % tuple(tot))
