"""Que disent les 10 retouches ? Composition des cellules, erreurs observées vs prédites sous plusieurs hypothèses."""
import numpy as np, pandas as pd
from scipy.special import ndtr
from scipy.optimize import brentq
import engine as E, sim as S, retouches as R, bilan_retouches as B
from engine import N, g, r, h, li, fg
U = R.U
t, F, total = B.bilan(ecrire=False)
cel = pd.read_csv(E.ROOT + 'sondes/lot2/cellules.csv'); idx_de = {c: i for i, c in enumerate(E.cand.id_candidat)}
mU = r + 0.1525 * h - 30.195                       # marge selon la règle de U
def p_hyp(s, sig):
    tt = brentq(lambda x: ndtr((s - x) / sig).sum() - 1595, 20, 45); return ndtr((s - tt) / sig)
ALT = {'melange': None,
       'U-regle s=.50': p_hyp(r + 0.1525 * h, 0.50), 'U-regle s=.35': p_hyp(r + 0.1525 * h, 0.35), 'U-regle s=.25': p_hyp(r + 0.1525 * h, 0.25),
       'a=.13 s=.5': p_hyp(r + 0.13 * h, 0.5), 'a=.11 s=.5': p_hyp(r + 0.11 * h, 0.5),
       'H1': R.PH[0], 'H2': R.PH[2], 'H3': R.PH[3]}
rows = []
for row in t.itertuples():
    ids = np.array([idx_de[c] for c in cel[cel.cellule == row.cellule].id_candidat])
    d = dict(cellule=row.cellule, sens='retrait' if U[ids[0]] == 1 else 'ajout', el=int(g[ids[0]]), k_obs=row.erreurs_de_U,
             marge_U=round(float(mU[ids].mean()), 2), coteR=round(float(r[ids].mean()), 2), heures=round(float(h[ids].mean()), 1),
             revenu_k=round(float(np.exp(li[ids]).mean() / 1000), 0), premgen=round(float(fg[ids].mean()), 2))
    for nom, p in ALT.items():
        pe = R.perr[ids] if p is None else np.where(U[ids] == 1, 1 - p[ids], p[ids])
        d[nom] = round(float(pe.sum()), 1)
    rows.append(d)
df = pd.DataFrame(rows); pd.set_option('display.width', 250)
print(df.to_string(index=False))
print('total k_obs', df.k_obs.sum(), '| prédits :', {c: round(float(df[c].sum()), 1) for c in ALT})
# log-vraisemblance des 10 comptes (Poisson-binomiale) sous chaque hypothèse
def ll(p):
    tot = 0
    for row in t.itertuples():
        ids = np.array([idx_de[c] for c in cel[cel.cellule == row.cellule].id_candidat])
        pe = np.where(U[ids] == 1, 1 - p[ids], p[ids]); pmf = np.array([1.0])
        for e in pe: pmf = np.convolve(pmf, [1 - e, e])
        tot += np.log(pmf[row.erreurs_de_U])
    return tot
for nom, p in ALT.items():
    if p is not None: print(f'log-vraisemblance des 10 comptes sous {nom:14s}: {ll(p):7.2f}')
