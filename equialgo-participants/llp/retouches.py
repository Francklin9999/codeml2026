"""Retouches de U : cellules de candidats où U a le plus de chances de se tromper, sous un mélange d'hypothèses.

Soumettre U avec une cellule S inversée donne : bons = 3798 + 2k - n, où k = nb d'erreurs de U dans S (exact).
"""
import numpy as np, pandas as pd
from scipy.special import ndtr
from scipy.optimize import brentq
import engine as E, sim as S
from engine import N, g, r, h, li, fg

U = S.lire('U_9495')
dist = E.cand.distance_domicile_campus_km.to_numpy()
HYP = {  # (score, sigma, poids) : hypothèses compatibles avec les 3 scores + l'ancre (analyse indépendante)
    'H1 eloignee -0.2': (r + 0.18 * h - 0.2 * g, 0.50, 0.70),
    'H1b ln(distance)': (r + 0.18 * h - 0.1 * np.log(dist), 0.50, 0.64),
    'H2 prem_gen -0.4': (r + 0.15 * h - 0.4 * fg, 0.45, 0.50),
    'H3 revenu +0.2': (r + 0.15 * h + 0.2 * li, 0.50, 0.32),
    'H4 pur': (r + 0.15 * h, 0.50, 0.10),
}
PH, WH = [], []
for nom, (s, sig, w) in HYP.items():
    t = brentq(lambda t: ndtr((s - t) / sig).sum() - 1595, 20, 45)
    PH.append(ndtr((s - t) / sig)); WH.append(w)
PH = np.array(PH); WH = np.array(WH) / np.sum(WH)
pbar = WH @ PH
perr_h = np.where(U == 1, 1 - PH, PH)          # P(U faux) par hypothèse
perr = WH @ perr_h


def gain_attendu(idx):
    """E[(2k - n)+] pour la cellule idx, mélange de Poisson-binomiales."""
    tot = 0.0
    for hyp in range(len(WH)):
        pmf = np.array([1.0])
        for e in perr_h[hyp, idx]:
            pmf = np.convolve(pmf, [1 - e, e])
        k = np.arange(len(pmf)); tot += WH[hyp] * (np.maximum(2 * k - len(idx), 0) * pmf).sum()
    return tot


def cellules(n, perr=perr):
    out = []
    for side in (0, 1):
        for grp in (0, 1):
            idx = np.where((U == side) & (g == grp))[0]
            idx = idx[np.argsort(-perr[idx], kind='stable')]
            for j in range(0, min(len(idx), 20 * n), n):
                c = idx[j:j + n]
                if len(c) == n:
                    out.append((gain_attendu(c), side, grp, c))
    out.sort(key=lambda x: -x[0])
    return out


if __name__ == '__main__':
    print('U : erreurs attendues', round(perr.sum(), 1), '(observé 202) | candidats avec P(U faux) > 0.5 :', int((perr > 0.5).sum()),
          '| > 0.45 :', int((perr > 0.45).sum()), '| > 0.40 :', int((perr > 0.40).sum()), '| > 0.30 :', int((perr > 0.30).sum()))
    for n in (5, 7, 9, 11, 13):
        cs = cellules(n)
        g14 = sum(c[0] for c in cs[:14]); g20 = sum(c[0] for c in cs[:20]); g9 = sum(c[0] for c in cs[:9])
        print(f'n={n:2d} : gain attendu 9 cellules {g9:5.1f} | 14 cellules {g14:5.1f} | 20 cellules {g20:5.1f} | meilleure cellule {cs[0][0]:.2f}, 14e {cs[13][0]:.2f}, 20e {cs[19][0]:.2f}')
