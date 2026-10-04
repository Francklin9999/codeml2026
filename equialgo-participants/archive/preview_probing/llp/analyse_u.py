"""Analyse du fichier de l'équipe (94,95 % sur HxBuddy = 3798 bons sur 4000)."""
import numpy as np, pandas as pd
import engine as E, sim as S
from engine import N, g, r, h, li, fg, ld
from sklearn.linear_model import LogisticRegression

U = S.lire('U_9495')
print('lignes', len(U), '| octrois', int(U.sum()), f'({U.mean():.2%}) | centres {U[g==0].mean():.3f} | eloignees {U[g==1].mean():.3f}')
print('par region :', pd.Series(U).groupby(E.cand.region_administrative.values).mean().round(3).to_dict())
for nom in ['P0_contrefactuel_40', 'P1_contrefactuel_44', 'P2_coteR_seule_40', 'P3_coteR_heures_40', 'P4_coteR_revenu_40', 'P5_premiere_gen_40', 'suivante_a0.0_b-1.0_c0.5_k1600']:
    p = S.lire(nom); print(f'  accord avec {nom:32s} {np.mean(p == U):.4f}')
print('  accord avec base (foret)                  %.4f' % np.mean(S.base == U))

# U est-il un seuil sur un score linéaire ?
feats = {'r': r, 'h': h, 'li': li, 'fg': fg, 'g': g, 'ld': ld}
X = np.column_stack(list(feats.values()) + [E.PD_])
names = list(feats) + [f'prog{i}' for i in range(4)]
mu, sd = X.mean(0), X.std(0)
for cols, lab in [(slice(0, 1), 'r seul'), (slice(0, 2), 'r,h'), (slice(0, 3), 'r,h,li'), (slice(0, 5), 'r,h,li,fg,g'), (slice(0, 6), '+ld'), (slice(0, 10), '+programmes')]:
    Xs = ((X - mu) / sd)[:, cols]
    m = LogisticRegression(C=1e6, max_iter=20000).fit(Xs, U)
    acc = m.score(Xs, U)
    coef = m.coef_[0] / sd[cols]
    print(f'{lab:14s} reproduit U a {acc:.4f} | coef / coef_r :', dict(zip(names[cols], np.round(coef / coef[0], 3))))
