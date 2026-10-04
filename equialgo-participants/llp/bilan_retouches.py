"""Assemble le meilleur fichier à partir des retouches mesurées : U + toutes les cellules qui gagnent. Score prédit exact."""
import sys
import numpy as np, pandas as pd
import engine as E, sim as S
from engine import N, g

BONS_U = 3798


def bilan(log=None, ecrire=True):
    res = pd.read_csv(log or E.ROOT + 'hxbuddy_resultats.csv')
    cel = pd.read_csv(E.ROOT + 'sondes/lot2/cellules.csv')
    U = S.lire('U_9495'); idx_de = {c: i for i, c in enumerate(E.cand.id_candidat)}
    F = U.copy(); total = BONS_U; lignes = []
    for row in res.itertuples():
        nom = row.fichier.split('/')[-1][:-4]
        if not row.fichier.startswith('sondes/lot2/R'):
            continue
        membres = cel[cel.cellule == nom]; n = len(membres)
        bons = [k for k in range(N + 1) if abs(100 * k / N - row.accuracy) <= 0.005 + 1e-9]
        assert len(bons) == 1, (nom, row.accuracy)
        delta = bons[0] - BONS_U
        assert (delta + n) % 2 == 0 and abs(delta) <= n, (nom, delta, n)   # incohérence = erreur de saisie
        k = (delta + n) // 2
        garde = delta > 0
        if garde:
            ids = [idx_de[c] for c in membres.id_candidat]
            F[ids] = 1 - F[ids]; total += delta
        lignes.append(dict(cellule=nom, n=n, erreurs_de_U=k, delta=delta, retenue=garde))
    t = pd.DataFrame(lignes)
    if ecrire and len(t):
        pd.DataFrame({'id_candidat': E.cand.id_candidat, 'decision_octroi': F.astype(int)}).to_csv(E.ROOT + 'sondes/lot2/U_plus.csv', index=False)
    return t, F, total


if __name__ == '__main__':
    t, F, total = bilan()
    print(t.to_string(index=False))
    print(f'\nU_plus.csv : {int((F != S.lire("U_9495")).sum())} retouches | score prédit EXACT : {total} bons = {100 * total / N:.2f} % | octrois {int(F.sum())} ({F.mean():.2%})')
