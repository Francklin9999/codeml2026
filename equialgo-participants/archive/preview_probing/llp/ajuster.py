"""Ajuste la règle de l'étalon sur tous les retours HxBuddy (hxbuddy_resultats.csv)."""
import sys, time
import numpy as np, pandas as pd
from scipy.optimize import minimize
import engine as E, sim as S
from engine import N, K, g

ANCRE, ANCRE_SD = 0.270, 0.008          # écart d'égalité des chances officiel du modèle de base


def lire_pred(chemin):
    s = pd.read_csv(E.ROOT + chemin).set_index('id_candidat').loc[E.cand.id_candidat, 'decision_octroi']
    return s.to_numpy().astype(float)


def bons_exacts(acc):
    ks = [k for k in range(N + 1) if abs(100 * k / N - acc) <= 0.005 + 1e-9]
    assert len(ks) == 1, (acc, ks)
    return ks[0]


def q_compatibles(k, f1, P):
    out = set()
    for Q in range(1400, 1800):
        tp2 = k - N + P + Q
        if tp2 % 2 or tp2 < 0 or tp2 > 2 * min(P, Q):
            continue
        tp = tp2 // 2; tn = N - P - Q + tp
        f = 100 * (2 * tp / (P + Q) + 2 * tn / (2 * N - P - Q)) / 2
        if abs(f - f1) <= 0.005 + 1e-9:
            out.add(Q)
    return out


def charger():
    res = pd.read_csv(E.ROOT + 'hxbuddy_resultats.csv')
    preds, corrects, noms, Qs = [], [], [], None
    for row in res.itertuples():
        p = lire_pred(row.fichier); k = bons_exacts(row.accuracy)
        preds.append(p); corrects.append(k); noms.append(row.fichier.split('/')[-1][:-4])
        if not np.isnan(row.f1_macro):
            qs = q_compatibles(k, row.f1_macro, int(p.sum()))
            Qs = qs if Qs is None else Qs & qs
    return noms, preds, corrects, sorted(Qs)


def ecart_base(p):
    b = S.base
    return (b * p)[g == 0].sum() / p[g == 0].sum() - (b * p)[g == 1].sum() / p[g == 1].sum()


def construire(preds, corrects, Q, avec_ancre=True):
    W, z = E.obs_rows(preds, corrects, Q=Q)

    def lp(th):
        v = E.log_lik(th, W, z) + E.log_prior(th)
        if avec_ancre:
            v -= 0.5 * ((ecart_base(E.proba(th)) - ANCRE) / ANCRE_SD) ** 2
        return v
    return W, z, lp


def map_multi(lp, n=16, seed=0):
    rng = np.random.default_rng(seed); best = None
    for _ in range(n):
        res = minimize(lambda t: -lp(t), E.init_theta(rng), method='L-BFGS-B', bounds=E.BOUNDS, options={'maxiter': 300})
        if best is None or res.fun < best.fun:
            best = res
    return best.x, -best.fun


def echantillonner(lp, n_walkers=48, n_steps=700, seed=0):
    """Stretch move ; marcheurs initialisés largement (a priori) pour ne pas rester dans un pic étroit."""
    rng = np.random.default_rng(seed)
    lo, hi = np.array(E.BOUNDS).T
    D = len(lo)
    pos = np.array([np.clip(E.init_theta(rng), lo, hi) for _ in range(n_walkers)])
    f = lambda th: lp(th) if (np.all(th >= lo) and np.all(th <= hi)) else -np.inf
    cur = np.array([f(p) for p in pos])
    chain, half = [], n_walkers // 2
    for step in range(n_steps):
        for first in (0, 1):
            idx = np.arange(half) + (0 if first == 0 else half)
            other = np.arange(half) + (half if first == 0 else 0)
            for i in idx:
                j = rng.choice(other)
                zz = ((1.0 + rng.random()) ** 2) / 2.0
                prop = pos[j] + zz * (pos[i] - pos[j])
                new = f(prop)
                if np.log(rng.random()) < (D - 1) * np.log(zz) + new - cur[i]:
                    pos[i], cur[i] = prop, new
        if step >= n_steps // 2 and step % 5 == 0:
            chain.append(pos.copy())
    return np.concatenate(chain)


if __name__ == '__main__':
    t0 = time.time()
    noms, preds, corrects, Qs = charger()
    print('observations :', dict(zip(noms, corrects)), '| Q compatibles :', Qs)
    Q = Qs[len(Qs) // 2] if len(Qs) > 1 else Qs[0]
    W, z, lp = construire(preds, corrects, Q if len(Qs) == 1 else None)
    th, v = map_multi(lp)
    print('MAP', round(v, 2), E.describe(th))
    ch = echantillonner(lp)
    desc = pd.DataFrame([E.describe(t) for t in ch[::7]])
    print(desc.describe().loc[['mean', 'std', '5%' if '5%' in desc.describe().index else 'min', 'max']].round(3).T.to_string())
    print(desc.quantile([0.05, 0.5, 0.95]).round(3).T.to_string())
    np.save('chaine.npy', ch)
    print(f'{time.time() - t0:.0f} s')
