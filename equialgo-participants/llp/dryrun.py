"""Répétition générale : étalons simulés tirés de l'a posteriori actuel -> lot 1 (+ U) -> candidat. Bat-on U ?"""
import sys, time, numpy as np, pandas as pd
import engine as E, sim as S, lot1 as L
from engine import N, K, g
U = S.lire('U_9495')
ch = np.load('chaine.npy')
rng = np.random.default_rng(1)
probes = {'P1': S.P1, 'PNEED': S.PNEED, 'U': U, **L.LOT, '11_U_eloignees': U * g}
rows = []
for it in range(int(sys.argv[1]) if len(sys.argv) > 1 else 8):
    th_true = ch[rng.integers(len(ch))]
    s = E.score(th_true); lat = s + np.exp(th_true[K + 1]) * rng.standard_normal(N)
    y = (lat > th_true[K]).astype(float)
    bayes = (s > th_true[K]).astype(float)
    preds = list(probes.values()); corrects = [int((p == y).sum()) for p in preds]
    W, z = E.obs_rows(preds, corrects, Q=int(y.sum()))
    th, f = E.fit(W, z, n_starts=10, seed=it)
    C = (E.proba(th) > 0.5).astype(float)
    eo = lambda p: p[(y == 1) & (g == 0)].mean() - p[(y == 1) & (g == 1)].mean()
    rows.append(dict(sigma=np.exp(th_true[K + 1]), sigma_hat=np.exp(th[K + 1]), bons_U=int((U == y).sum()), bons_C=int((C == y).sum()),
                     bons_bayes=int((bayes == y).sum()), gain=int((C == y).sum() - (U == y).sum()), eo_U=eo(U), eo_C=eo(C), flips=int((C != U).sum())))
df = pd.DataFrame(rows); pd.set_option('display.width', 200)
print(df.round(3).to_string(index=False))
print('gain moyen du candidat sur U : %+.1f bons (min %+d, max %+d) | manque vs Bayes : %.1f' % (df.gain.mean(), df.gain.min(), df.gain.max(), (df.bons_bayes - df.bons_C).mean()))
