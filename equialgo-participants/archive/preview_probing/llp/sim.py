"""Simulation : le lot de sondes + le moteur retrouvent-ils un étalon connu ?"""
import os, sys, time
import numpy as np, pandas as pd
import engine as E
from engine import N, g, r, h, li, fg, ld, X, K

SC = os.path.dirname(os.path.abspath(__file__)).replace(os.sep, '/') + '/'


def lire(nom):
    s = pd.read_csv(E.ROOT + f'sondes/{nom}.csv').set_index('id_candidat').loc[E.cand.id_candidat, 'decision_octroi']
    return s.to_numpy().astype(float)


def top_k(s, k):
    p = np.zeros(N)
    p[np.argsort(-s, kind='stable')[:k]] = 1
    return p


base = np.load(SC + 'base.npy').astype(float)
P1 = lire('P1_contrefactuel_44')
PNEED = lire('suivante_a0.0_b-1.0_c0.5_k1600')
choix = top_k(r + 0.14 * h + 0.44 * li + 0.64 * fg, 1600)


def med_haut(x):
    out = np.zeros(N)
    for k in (0, 1):
        out[g == k] = x[g == k] >= np.median(x[g == k])
    return out


def lot(bande=(26.5, 30.5), design='manuel7'):
    B = ((r >= bande[0]) & (r <= bande[1])).astype(float)
    mid = (bande[0] + bande[1]) / 2
    probes = {
        'eloignees': g.copy(), 'base': base, 'base_el': base * g, 'choix': choix, 'choix_el': choix * g,
        'bande': B, 'bande_el': B * g, 'bande_heures': B * med_haut(h), 'bande_revenu': B * med_haut(li),
        'bande_premgen': B * fg, 'bande_dist': B * med_haut(ld), 'bande_coteR': B * (r >= mid),
    }
    if design == 'manuel12':   # mêmes contrastes, séparés par groupe
        for nom, f in [('heures', med_haut(h)), ('revenu', med_haut(li)), ('premgen', fg), ('coteR', (r >= mid) * 1.0)]:
            probes[f'bande_{nom}_el'] = B * f * g
        for i, p in enumerate(E.PROGS[1:]):
            probes[f'bande_prog{i}'] = B * E.PD_[:, i]
    return probes


def verite(rng, variante='lineaire'):
    a = rng.uniform(0.0, 0.3); b = rng.uniform(-0.5, 1.5); c = rng.uniform(-0.3, 1.5)
    d = rng.uniform(-0.5, 1.5); e = rng.uniform(-0.2, 0.3)
    progs = rng.normal(0, 0.2, 4)
    sigma = rng.uniform(0.0, 0.9)
    s = r + a * h + b * li + c * fg + d * g + e * ld + E.PD_ @ progs
    if variante == 'seuil_revenu':
        s = s + 0.8 * (np.exp(li) < 45000)
    if variante == 'seuil_heures':
        s = s + 0.7 * (h >= 15)
    eps = rng.standard_normal(N) if variante != 'logistique' else rng.logistic(size=N) * np.sqrt(3) / np.pi
    lat = s + sigma * eps
    Q = int(rng.integers(1590, 1602))
    y = np.zeros(N); y[np.argsort(-lat)[:Q]] = 1
    t = np.sort(lat)[::-1][Q - 1]
    oracle = (s >= t).astype(float)
    return dict(y=y, Q=Q, oracle=oracle, sigma=sigma, par=dict(a=a, b=b, c=c, d=d, e=e))


def eo(pred, y):
    return pred[(y == 1) & (g == 0)].mean() - pred[(y == 1) & (g == 1)].mean()


def essai(seed, design, variante, n_starts=10, verbose=False):
    rng = np.random.default_rng(seed)
    V = verite(rng, variante)
    y = V['y']
    probes = {'P1': P1, 'PNEED': PNEED, **lot(design=design)}
    preds = list(probes.values())
    corrects = [int((p == y).sum()) for p in preds]
    W, z = E.obs_rows(preds, corrects, Q=V['Q'])
    th, f = E.fit(W, z, n_starts=n_starts, seed=seed)
    p = E.proba(th)
    pred = (p > 0.5).astype(float)
    res = dict(seed=seed, sigma=V['sigma'], acc=np.mean(pred == y), acc_oracle=np.mean(V['oracle'] == y),
               acc_choix=np.mean(choix == y), eo=eo(pred, y), eo_oracle=eo(V['oracle'], y),
               sigma_hat=np.exp(th[K + 1]), k=int(pred.sum()))
    if verbose:
        print(V['par'], E.describe(th))
    return res


if __name__ == '__main__':
    design = sys.argv[1] if len(sys.argv) > 1 else 'manuel7'
    variante = sys.argv[2] if len(sys.argv) > 2 else 'lineaire'
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    t0 = time.time()
    rows = [essai(s, design, variante) for s in range(n)]
    df = pd.DataFrame(rows)
    df['perte_vs_oracle'] = df.acc_oracle - df.acc
    pd.set_option('display.width', 200)
    print(f'design={design} variante={variante} ({time.time() - t0:.0f} s)')
    print(df.round(4).to_string(index=False))
    print('moyennes :', df[['acc', 'acc_oracle', 'acc_choix', 'perte_vs_oracle']].mean().round(4).to_dict())
