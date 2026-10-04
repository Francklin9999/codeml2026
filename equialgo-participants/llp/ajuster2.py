"""Ajustement sur toutes les mesures : fichiers complets (fonctionnelle ±1) + cellules de retouche (comptes exacts de positifs)."""
import sys, time
import numpy as np, pandas as pd
import engine as E, eng2, sim as S, ajuster as A, bilan_retouches as B
from engine import N, g, r, h, li, fg

TAU2 = 0.25


def observations():
    res = pd.read_csv(E.ROOT + 'hxbuddy_resultats.csv')
    U = S.lire('U_9495'); idx_de = {c: i for i, c in enumerate(E.cand.id_candidat)}
    cel = pd.read_csv(E.ROOT + 'sondes/lot2/cellules.csv')
    Wr, zr, noms = [], [], []
    for row in res.itertuples():
        nom = row.fichier.split('/')[-1][:-4]
        k = A.bons_exacts(row.accuracy)
        if row.fichier.startswith('sondes/lot2/R'):
            ids = np.array([idx_de[c] for c in cel[cel.cellule == nom].id_candidat]); n = len(ids)
            kerr = (k - B.BONS_U + n) // 2
            w = np.zeros(N); w[ids] = 1
            Wr.append(w); zr.append(n - kerr if U[ids[0]] == 1 else kerr); noms.append(nom)      # nb de positifs dans la cellule
        else:
            p = A.lire_pred(row.fichier)
            Wr.append(2 * p - 1); zr.append(k - (N - p.sum())); noms.append(nom[:12])
    return np.array(Wr), np.array(zr, float), noms


def ppc(M, th, W, z, noms):
    p = M.proba(th); v = p * (1 - p)
    mu = W @ p; sd = np.sqrt((W * W) @ v + TAU2)
    return pd.DataFrame({'obs': noms, 'observé': z, 'modèle': mu.round(1), 'sd': sd.round(1), 'z': ((z - mu) / sd).round(2)})


if __name__ == '__main__':
    W, z, noms = observations()
    for blocs in [('base5', 'prog'), ('base5', 'prog', 'h_q', 'li_q')]:
        M = eng2.Model(names=blocs)
        t0 = time.time(); th, f = M.fit(W, z, n_starts=24, seed=0, tau2=TAU2)
        print('\n=== blocs', blocs, '| nlp %.2f | %.0f s' % (f, time.time() - t0))
        print({n: round(float(v), 3) for n, v in zip(M.names, th)}, '| sigma', round(float(np.exp(th[M.K + 1])), 3))
        if blocs == ('base5', 'prog'):
            print('direct :', E.describe(th))
        print(ppc(M, th, W, z, noms).to_string(index=False))
        dr, w, ess = eng2.is_posterior(M, th, W, z, TAU2, n=4000, seed=0)
        sig = np.exp(dr[:, M.K + 1]); print('IS : ESS %.0f | sigma moyenne %.3f (5%%-95%% : %.3f-%.3f)' % (ess, w @ sig, *np.quantile(sig[w > 0], [0.05, 0.95])))
        m = w @ dr; s = np.sqrt(w @ (dr - m) ** 2)
        print('a posteriori (moyenne ± sd) :', {n: f'{a:.3f}±{b:.3f}' for n, a, b in zip(M.names, m, s)})
