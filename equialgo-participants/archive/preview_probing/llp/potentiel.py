"""Sous l'a posteriori actuel : jusqu'où un modèle peut-il monter, et que vont apprendre les sondes du lot 1 ?"""
import numpy as np, pandas as pd
import engine as E, sim as S, lot1 as L
from engine import N, K, g
U = S.lire('U_9495')
ch = np.load('chaine.npy')[::10]
rows = []
for th in ch:
    p = E.proba(th)
    bayes = np.mean(np.maximum(p, 1 - p)); accU = np.mean(U * p + (1 - U) * (1 - p))
    eoU = (U * p)[g == 0].sum() / p[g == 0].sum() - (U * p)[g == 1].sum() / p[g == 1].sum()
    rows.append((bayes, accU, eoU, np.sum(p * (1 - p))))
d = pd.DataFrame(rows, columns=['acc_bayes', 'acc_U', 'eo_U', 'var_tot'])
print(d.describe(percentiles=[.05, .5, .95]).round(4).T[['mean', 'std', '5%', '50%', '95%']].to_string())
print('P(acc_bayes > 95.25 %) =', np.mean(d.acc_bayes > 0.9525).round(2), '| P(> 96 %) =', np.mean(d.acc_bayes > 0.96).round(2))
print('\nSondes du lot 1 : compte de positifs prédit (moyenne), incertitude a posteriori (signal) vs bruit intra-modèle')
for nom, cell in {**L.LOT, '11_U_eloignees': U * g}.items():
    mu = np.array([cell @ E.proba(th) for th in ch]); noise = np.sqrt(np.mean([cell @ (E.proba(th) * (1 - E.proba(th))) for th in ch]))
    print(f'  {nom:26s} taille {int(cell.sum()):5d} | positifs prédits {mu.mean():7.1f} ± {mu.std():5.1f} (bruit {noise:4.1f})')
