"""Lot 3 : re-tests par petits groupes des cellules déjà mesurées (plans optimaux trouvés par recherche exhaustive, voir plans.py).

Chaque fichier = U avec un sous-ensemble S inversé ; HxBuddy renvoie 3798 + 2k - |S|, k = nb d'erreurs de U dans S (exact).
Plan à 3 tests pour une cellule de 7 : {0,1}, {0,2}, {1,2,3}. Gain garanti : +3 si la cellule a 4 erreurs, +2 si elle en a 3.
"""
import os
import numpy as np
import pandas as pd
import engine as E
import sim as S
from engine import N, r, h

U = S.lire('U_9495')
mU = r + 0.1525 * h - 30.195
idx_de = {c: i for i, c in enumerate(E.cand.id_candidat)}
cel2 = pd.read_csv(E.ROOT + 'sondes/lot2/cellules.csv')
PLAN3 = ([0, 1], [0, 2], [1, 2, 3])


def cellule_R(nom):
    ids = np.array([idx_de[c] for c in cel2[cel2.cellule == nom].id_candidat])
    return ids[np.argsort(np.abs(mU[ids]), kind='stable')]      # rôle 0 = le plus proche du seuil


def lot():
    L, j = {}, 1
    for nom in ('R02', 'R04', 'R08'):                           # 4, 3 et 3 erreurs sur 7
        ids = cellule_R(nom)
        for t in PLAN3:
            L[f'T{j:02d}'] = (f'{nom} rôles {t}', ids[t])
            j += 1
    L['T10'] = ('R03 rôle [0]', cellule_R('R03')[[0]])          # cellule à 2 erreurs : un candidat seul
    return L


if __name__ == '__main__':
    OUT = E.ROOT + 'sondes/lot3/'
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for nom, (desc, ids) in lot().items():
        F = U.copy()
        F[ids] = 1 - F[ids]
        pd.DataFrame({'id_candidat': E.cand.id_candidat, 'decision_octroi': F.astype(int)}).to_csv(OUT + nom + '.csv', index=False)
        chk = pd.read_csv(OUT + nom + '.csv')
        assert len(chk) == N and set(chk.decision_octroi) <= {0, 1} and chk.id_candidat.tolist() == E.cand.id_candidat.tolist()
        n = len(ids)
        scores = ', '.join(f'{100 * (3798 + 2 * k - n) / N:.3f}' for k in range(n + 1))
        print(f'{nom} ({desc:18s}) taille {n} | scores possibles : {scores}')
        rows += [dict(cellule=nom, description=desc, id_candidat=E.cand.id_candidat[i]) for i in ids]
    pd.DataFrame(rows).to_csv(OUT + 'cellules.csv', index=False)
