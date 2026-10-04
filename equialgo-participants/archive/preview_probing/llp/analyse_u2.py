"""Comment U est-il construit ? Meilleure règle linéaire, puis nature des écarts."""
import numpy as np, pandas as pd
import engine as E, sim as S
from engine import N, g, r, h, li, fg, ld
U = S.lire('U_9495')
best = None
for a in np.arange(0.10, 0.2501, 0.0025):
    s = r + a * h
    for k in range(1570, 1611):
        p = np.zeros(N); p[np.argsort(-s, kind='stable')[:k]] = 1
        acc = np.mean(p == U)
        if best is None or acc > best[0]:
            best = (acc, a, k, np.sort(s)[::-1][k - 1])
acc, a, k, t = best
print(f'meilleure règle r + {a:.4f}*h, top {k} (seuil {t:.3f}) : accord {acc:.4f} ({int(round((1-acc)*N))} écarts)')
s = r + a * h; lin = (s >= t).astype(float)
d = E.cand.assign(U=U, lin=lin, marge=s - t, eloignee=g, linc=li)[U != lin]
d['sens'] = np.where(d.U == 1, 'ajouté', 'retiré')
pd.set_option('display.width', 220)
print(d.groupby('sens').agg(n=('U', 'size'), marge_moy=('marge', 'mean'), marge_min=('marge', 'min'), marge_max=('marge', 'max'),
      eloignee=('eloignee', 'mean'), premgen=('premiere_generation_universitaire', 'mean'), revenu_med=('revenu_familial_estime', 'median'),
      heures=('heures_travail_semaine', 'mean'), coteR=('cote_r_equivalent', 'mean')).round(3).to_string())
print(d.sort_values('marge')[['id_candidat', 'cote_r_equivalent', 'heures_travail_semaine', 'revenu_familial_estime', 'region_administrative', 'premiere_generation_universitaire', 'programme_etudes', 'marge', 'sens']].to_string(index=False))
# U est-il mieux expliqué avec des seuils par groupe ?
for grp in (0, 1):
    m = g == grp; bestg = None
    for a2 in np.arange(0.10, 0.2501, 0.0025):
        s2 = (r + a2 * h)[m]
        for t2 in np.arange(t - 0.6, t + 0.6, 0.01):
            ac = np.mean((s2 >= t2) == (U[m] == 1))
            if bestg is None or ac > bestg[0]: bestg = (ac, a2, t2)
    print('groupe', grp, 'meilleur (accord, a, seuil):', np.round(bestg, 4))
