"""Moteur : apprendre la règle de l'étalon à partir de comptes exacts (HxBuddy).

Chaque soumission renvoie un nombre exact de bonnes réponses, donc une fonctionnelle linéaire
des étiquettes cachées y : correct - (N - P) = somme_i (2*pred_i - 1) * y_i.
Modèle : y_i ~ Bernoulli(p_i), p_i = Phi((r_i + x_i.beta - t) / sigma).
Vraisemblance : gaussienne multivariée sur les fonctionnelles (apprentissage par proportions d'étiquettes).
"""
import os
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import ndtr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace(os.sep, '/') + '/'
cand = pd.read_csv(ROOT + 'data/candidats_evaluation.csv')
N = len(cand)
ELOIGNEES = ['Bas-Saint-Laurent', 'Cote-Nord', 'Gaspesie-Iles-de-la-Madeleine']
g = cand.region_administrative.isin(ELOIGNEES).to_numpy().astype(float)
r = cand.cote_r_equivalent.to_numpy()
h = cand.heures_travail_semaine.to_numpy().astype(float)
li = np.log(cand.revenu_familial_estime.to_numpy())
fg = cand.premiere_generation_universitaire.to_numpy().astype(float)
ld = np.log1p(cand.distance_domicile_campus_km.to_numpy())
PROGS = sorted(cand.programme_etudes.unique())
PD_ = np.column_stack([(cand.programme_etudes == p).to_numpy().astype(float) for p in PROGS[1:]])


def wgc(x):
    """Centrage intra-groupe : décorrèle les variables du groupe régional."""
    out = x.astype(float).copy()
    for k in (0, 1):
        out[g == k] -= x[g == k].mean()
    return out


DELTA = {  # différence de moyenne éloignées - centres
    'h': h[g == 1].mean() - h[g == 0].mean(), 'li': li[g == 1].mean() - li[g == 0].mean(),
    'fg': fg[g == 1].mean() - fg[g == 0].mean(), 'ld': ld[g == 1].mean() - ld[g == 0].mean(),
}
X = np.column_stack([wgc(h), wgc(li), wgc(fg), g - g.mean(), wgc(ld), PD_ - PD_.mean(0)])
NAMES = ['heures', 'log_revenu', 'prem_gen', 'eloignee_net', 'log_dist', *[f'prog_{p[:8]}' for p in PROGS[1:]]]
K = X.shape[1]
PRIOR_M = np.array([0.12, 0.5, 0.4, 0.4, 0.0, 0, 0, 0, 0])
PRIOR_S = np.array([0.25, 1.2, 1.0, 1.2, 0.5, 0.15, 0.15, 0.15, 0.15])
LS_M, LS_S = np.log(0.4), 1.2
BOUNDS = [(m - 4 * s, m + 4 * s) for m, s in zip(PRIOR_M, PRIOR_S)] + [(24.0, 33.0), (np.log(0.05), np.log(3.0))]


def score(theta):
    return r + X @ theta[:K]


def proba(theta):
    return ndtr((score(theta) - theta[K]) / np.exp(theta[K + 1]))


def log_prior(theta):
    return -0.5 * (((theta[:K] - PRIOR_M) / PRIOR_S) ** 2).sum() - 0.5 * ((theta[K + 1] - LS_M) / LS_S) ** 2


def log_lik(theta, W, z, tau2=0.25):
    p = proba(theta)
    v = p * (1 - p)
    C = (W * v) @ W.T
    C[np.diag_indices_from(C)] += tau2
    try:
        L = np.linalg.cholesky(C)
    except np.linalg.LinAlgError:
        return -1e12
    d = np.linalg.solve(L, z - W @ p)
    return -0.5 * d @ d - np.log(np.diag(L)).sum()


def neg_log_post(theta, W, z, tau2=0.25):
    return -(log_lik(theta, W, z, tau2) + log_prior(theta))


def obs_rows(preds, corrects, Q=None):
    """Convertit (prédiction, nb exact de bons) en lignes de la fonctionnelle linéaire."""
    W = np.array([2.0 * p - 1.0 for p in preds])
    z = np.array([c - (N - p.sum()) for p, c in zip(preds, corrects)], dtype=float)
    if Q is not None:
        W = np.vstack([W, np.ones(N)])
        z = np.append(z, Q)
    return W, z


def init_theta(rng, q=0.399):
    beta = PRIOR_M + PRIOR_S * rng.standard_normal(K) * 0.7
    s = r + X @ beta
    return np.r_[beta, np.quantile(s, 1 - q), rng.uniform(np.log(0.1), np.log(1.0))]


def fit(W, z, n_starts=12, seed=0, tau2=0.25, starts=None):
    rng = np.random.default_rng(seed)
    best = None
    inits = list(starts) if starts is not None else []
    inits += [init_theta(rng) for _ in range(n_starts)]
    for th0 in inits:
        res = minimize(neg_log_post, th0, args=(W, z, tau2), method='L-BFGS-B', bounds=BOUNDS,
                       options={'maxiter': 300, 'maxfun': 6000})
        if best is None or res.fun < best.fun:
            best = res
    return best.x, best.fun


def sample_posterior(W, z, theta0, n_walkers=40, n_steps=600, seed=0, tau2=0.25):
    """Échantillonneur d'ensemble (stretch move, Goodman & Weare)."""
    rng = np.random.default_rng(seed)
    D = len(theta0)
    lo, hi = np.array(BOUNDS).T
    pos = np.clip(theta0 + 0.02 * rng.standard_normal((n_walkers, D)) * np.r_[PRIOR_S, 0.3, 0.3], lo, hi)

    def lp(th):
        if np.any(th < lo) or np.any(th > hi):
            return -np.inf
        return log_lik(th, W, z, tau2) + log_prior(th)

    cur = np.array([lp(p) for p in pos])
    chain = []
    half = n_walkers // 2
    for step in range(n_steps):
        for first in (0, 1):
            idx = np.arange(half) + (0 if first == 0 else half)
            other = np.arange(half) + (half if first == 0 else 0)
            for i in idx:
                j = rng.choice(other)
                zz = ((1.0 + rng.random()) ** 2) / 2.0          # a = 2
                prop = pos[j] + zz * (pos[i] - pos[j])
                new = lp(prop)
                if np.log(rng.random()) < (D - 1) * np.log(zz) + new - cur[i]:
                    pos[i], cur[i] = prop, new
        if step >= n_steps // 2 and step % 5 == 0:
            chain.append(pos.copy())
    return np.concatenate(chain)


def describe(theta):
    """Paramètres lisibles : coefficients en points de cote R, bonus direct aux régions éloignées."""
    a, b, c, net, e = theta[:5]
    d_direct = net - a * DELTA['h'] - b * DELTA['li'] - c * DELTA['fg'] - e * DELTA['ld']
    out = {n: round(float(v), 3) for n, v in zip(NAMES, theta[:K])}
    out.update(eloignee_direct=round(float(d_direct), 3), seuil=round(float(theta[K]), 3),
               sigma=round(float(np.exp(theta[K + 1])), 3))
    return out
