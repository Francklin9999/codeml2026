"""Assemble le meilleur fichier à partir de toutes les retouches mesurées (U avec un petit ensemble S inversé).

Chaque mesure donne k(S) = nb d'erreurs de U dans S. Par groupe de candidats liés par des mesures, on énumère toutes les
configurations d'erreurs compatibles ; on inverse chaque candidat dont la probabilité d'erreur dépasse 1/2.
Sortie : meilleur_fichier.csv, avec le gain garanti (pire configuration) et le gain espéré.
"""
import glob
import itertools
import os
import numpy as np
import pandas as pd
import engine as E
import sim as S
from engine import N

BONS_U = 3798
PETITE = 7


def charger_cellules():
    cells = {}
    for f in sorted(glob.glob(E.ROOT + 'sondes/lot*/cellules.csv')):
        lot = os.path.basename(os.path.dirname(f))
        for nom, grp in pd.read_csv(f).groupby('cellule'):
            cells[f'sondes/{lot}/{nom}.csv'] = grp.id_candidat.tolist()
    return cells


def mesures(log=None, bons_u=None):
    res = pd.read_csv(log or E.ROOT + 'hxbuddy_resultats.csv')
    cells = charger_cellules()
    idx_de = {c: i for i, c in enumerate(E.cand.id_candidat)}
    out = []
    for row in res.itertuples():
        if row.fichier not in cells:
            continue
        ids = np.array([idx_de[c] for c in cells[row.fichier]])
        n = len(ids)
        bons = [k for k in range(N + 1) if abs(100 * k / N - row.accuracy) <= 0.005 + 1e-9]
        assert len(bons) == 1, (row.fichier, row.accuracy)
        delta = bons[0] - (bons_u or BONS_U)
        assert (delta + n) % 2 == 0 and abs(delta) <= n, ('résultat incohérent', row.fichier, row.accuracy, delta, n)
        out.append(dict(fichier=row.fichier.split('/')[-1][:-4], ids=ids, n=n, k=(delta + n) // 2))
    return out


def assembler(ms, ecrire=None, bons_u=None):
    U = S.lire('U_9495')
    petites = [m for m in ms if m['n'] <= PETITE]
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for m in petites:
        a = find(int(m['ids'][0]))
        for i in m['ids'][1:]:
            parent[find(int(i))] = a
    comps = {}
    for x in list(parent):
        comps.setdefault(find(x), []).append(x)
    F = U.copy()
    base = bons_u or BONS_U
    esp, garanti, lignes = 0.0, 0, []
    for membres in comps.values():
        membres = sorted(membres)
        pos = {c: j for j, c in enumerate(membres)}
        tests = [(np.array([pos[int(i)] for i in t['ids']]), t['k'], t['fichier']) for t in petites if int(t['ids'][0]) in pos]
        ok = [cfg for cfg in itertools.product((0, 1), repeat=len(membres))
              if all(sum(cfg[j] for j in idx) == k for idx, k, _ in tests)]
        assert ok, ('mesures contradictoires', [t[2] for t in tests])
        A = np.array(ok)
        flip = A.mean(0) > 0.5
        gains = (2 * A[:, flip] - 1).sum(1) if flip.any() else np.zeros(len(A))
        if flip.any():
            cible = np.array(membres)[flip]
            F[cible] = 1 - F[cible]
        esp += gains.mean()
        garanti += int(gains.min())
        lignes.append(dict(groupe='+'.join(sorted({t[2] for t in tests})), candidats=len(membres), configurations=len(ok),
                           inverses=int(flip.sum()), gain_garanti=int(gains.min()), gain_espere=round(float(gains.mean()), 2),
                           gain_max=int(gains.max())))
    if ecrire:
        pd.DataFrame({'id_candidat': E.cand.id_candidat, 'decision_octroi': F.astype(int)}).to_csv(ecrire, index=False)
    return pd.DataFrame(lignes), F, base + garanti, base + esp


if __name__ == '__main__':
    ms = mesures()
    t, F, garanti, esp = assembler(ms, ecrire=E.ROOT + 'meilleur_fichier.csv')
    pd.set_option('display.width', 200)
    print(t.to_string(index=False))
    for m in ms:
        if m['n'] > PETITE:
            print(f'recensement {m["fichier"]} : {m["k"]} erreurs de U sur {m["n"]} ({m["k"] / m["n"]:.0%})')
    print(f'\nmeilleur_fichier.csv : {int((F != S.lire("U_9495")).sum())} retouches | score garanti {garanti} bons '
          f'({100 * garanti / N:.3f} %) | espéré {esp:.1f} | octrois {int(F.sum())} ({F.mean():.2%})')
