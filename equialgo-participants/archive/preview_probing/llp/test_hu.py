"""Test direct : 'étalon = top-Q de (coteR + a*heures) + bruit normal sigma' est-il compatible avec les 3 retours et l'ancre ?"""
import numpy as np, pandas as pd
import engine as E, sim as S
from engine import N, g, r, h, li, fg
U = S.lire('U_9495'); P1 = S.P1; PN = S.PNEED; base = S.base
rng = np.random.default_rng(0)
print('observé : P1 3677 | PNEED 3633 | U 3798 | écart base 0.270')
rows = []
for a in (0.13, 0.152, 0.18, 0.21):
    for sig in (0.35, 0.45, 0.55):
        out = []
        for _ in range(300):
            lat = r + a * h + sig * rng.standard_normal(N)
            y = np.zeros(N); y[np.argsort(-lat)[:1595]] = 1
            gap = base[(y == 1) & (g == 0)].mean() - base[(y == 1) & (g == 1)].mean()
            out.append(((P1 == y).sum(), (PN == y).sum(), (U == y).sum(), gap))
        o = np.array(out); m, s = o.mean(0), o.std(0)
        zs = [(3677 - m[0]) / s[0], (3633 - m[1]) / s[1], (3798 - m[2]) / s[2], (0.270 - m[3]) / s[3]]
        rows.append((a, sig, *np.round(m, 3), *np.round(zs, 1), round(float(np.sum(np.square(zs))), 1)))
df = pd.DataFrame(rows, columns=['a', 'sigma', 'P1', 'PNEED', 'U', 'ecart_base', 'z_P1', 'z_PNEED', 'z_U', 'z_ecart', 'chi2'])
pd.set_option('display.width', 200); print(df.to_string(index=False))
