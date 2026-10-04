"""Shared machinery for inferring the hidden EquiAlgo reference from exact HxBuddy readings.

Reference model family:  P(R_i = 1) = F((s_i - t) / sigma_i),   s = z(cote) + X_i . w,
with t solved (Newton) so that sum_i P(R_i = 1) = K.

Likelihood of the readings. Every two-decimal accuracy is an exact error count
err_j = n_j + K - 2 * TP_j,  TP_j = sum_i Y_ji R_i.  With R_i ~ Bernoulli(p_i) conditioned on
sum R = K, the vector of error counts of all scored files is approximately Gaussian with
    mean  mu_j = n_j + K - 2 Y_j . p
    cov   C_jl = 4 * (sum_i Y_ji Y_li v_i - (Y_j . v)(Y_l . v) / sum v),   v = p (1 - p).
Files share almost every decision, so their errors are strongly correlated: this is what the
earlier least-squares fit ignored. The same joint Gaussian gives, for any new file, the
predictive distribution of its error count CONDITIONAL on all readings (kriging), which is
how files are compared and how leave-one-out is scored.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit, ndtr

ROOT = Path(__file__).resolve().parents[2]  # equialgo-participants/
LEADERBOARD = ROOT / "work" / "strat3" / "leaderboard.csv"
REMOTE = ["Bas-Saint-Laurent", "Cote-Nord", "Gaspesie-Iles-de-la-Madeleine"]
N_GRANT_RANGE = (1595, 1603)
NUGGET = 1.0  # variance floor (in errors^2) for the Gaussian approximation of discrete counts

candidates = pd.read_csv(ROOT / "data" / "candidats_evaluation.csv")
history = pd.read_csv(ROOT / "data" / "donnees_demandes.csv")
ids = candidates.id_candidat
N = len(candidates)


def raw_features(df):
    f = pd.DataFrame(index=df.index)
    f["cote"] = df.cote_r_equivalent
    f["hours"] = df.heures_travail_semaine.astype(float)
    f["loginc"] = np.log(df.revenu_familial_estime)
    f["inc"] = df.revenu_familial_estime / 1e5
    f["firstgen"] = df.premiere_generation_universitaire.astype(float)
    f["logdist"] = np.log1p(df.distance_domicile_campus_km)
    f["dist"] = df.distance_domicile_campus_km / 100
    f["remote"] = df.region_administrative.isin(REMOTE).astype(float)
    for r in ["Capitale-Nationale", "Bas-Saint-Laurent", "Cote-Nord", "Gaspesie-Iles-de-la-Madeleine"]:
        f["reg_" + r[:3]] = (df.region_administrative == r).astype(float)
    for p, short in [("Genie", "gen"), ("Sciences", "sci"), ("Sciences sociales", "soc"), ("Sante", "san")]:
        f["prog_" + short] = (df.programme_etudes == p).astype(float)
    return f


def feature_matrix(names, standardize_on="candidates"):
    """Columns for the score. 'z_' prefix = z-scored; products/squares built from z-scores."""
    rc, rh = raw_features(candidates), raw_features(history)
    ref = rc if standardize_on == "candidates" else rh
    z = lambda col: (rc[col] - ref[col].mean()) / ref[col].std()
    cols = {}
    for name in names:
        if name.startswith("z_"):
            cols[name] = z(name[2:])
        elif name == "hours2":
            cols[name] = z("hours") ** 2 - 1
        elif name == "cote2":
            cols[name] = z("cote") ** 2 - 1
        elif name == "cotexhours":
            cols[name] = z("cote") * z("hours")
        elif name == "loginc2":
            cols[name] = z("loginc") ** 2 - 1
        elif name.startswith("hknot"):  # hinge on hours above a knot (in hours)
            cols[name] = np.maximum(rc["hours"] - float(name[5:]), 0) / ref["hours"].std()
        elif name.startswith("cknot"):  # hinge on cote above a knot
            cols[name] = np.maximum(rc["cote"] - float(name[5:]), 0) / ref["cote"].std()
        else:
            cols[name] = rc[name]
    X = np.column_stack([np.asarray(cols[n], float) for n in names]) if names else np.zeros((N, 0))
    return np.asarray(z("cote"), float), X


def load_board(path=LEADERBOARD):
    board = pd.read_csv(path, dtype=str).fillna("")
    board = board[board.accuracy.str.contains(r"\.")].reset_index(drop=True)
    Y = np.array([pd.read_csv(ROOT / f).set_index("id_candidat").loc[ids].decision_octroi.to_numpy()
                  for f in board.file], float)
    E = np.round(N * (1 - board.accuracy.astype(float).to_numpy() / 100))
    return board, Y, E


class Family:
    """A reference model family. theta = [w (m), log sigma, hetero (0/1), K offset (0/1)]."""

    def __init__(self, names, link="probit", hetero=None, free_k=False, k0=1599,
                 prior_sd=0.5, standardize_on="candidates", label=None):
        self.names, self.link, self.hetero, self.free_k, self.k0 = list(names), link, hetero, free_k, k0
        self.zc, self.X = feature_matrix(self.names, standardize_on)
        self.m = len(self.names)
        self.prior_sd = np.broadcast_to(np.asarray(prior_sd, float), (self.m,)).copy()
        self.label = label or f"{link}|{'+'.join(self.names)}|het={hetero}|freeK={free_k}"
        if hetero == "remote":
            self.g = raw_features(candidates)["remote"].to_numpy() - 0.5
        elif hetero == "hours":
            self.g = feature_matrix(["z_hours"])[1][:, 0]
        elif hetero == "cote":
            self.g = self.zc
        else:
            self.g = None
        self.cdf = ndtr if link == "probit" else expit
        self.dim = self.m + 1 + (self.g is not None) + free_k

    def unpack(self, th):
        w = th[:self.m]
        sigma = np.exp(th[self.m])
        i = self.m + 1
        h = 0.0
        if self.g is not None:
            h = th[i]
            i += 1
        k = self.k0 + (th[i] if self.free_k else 0.0)
        return w, sigma, h, k

    def x0(self):
        th = np.zeros(self.dim)
        th[self.m] = np.log(0.15)
        if "z_hours" in self.names:
            th[self.names.index("z_hours")] = 0.18
        return th

    def score(self, th):
        return self.zc + self.X @ th[:self.m]

    def probs(self, th):
        w, sigma, h, k = self.unpack(th)
        s = self.zc + self.X @ w
        sig = sigma * np.exp(h * self.g) if self.g is not None else sigma
        t = np.partition(s, N - int(round(k)))[N - int(round(k))]
        dens = (lambda u: np.exp(-0.5 * u * u) / np.sqrt(2 * np.pi)) if self.link == "probit" else \
            (lambda u: expit(u) * (1 - expit(u)))
        for _ in range(40):
            u = (s - t) / sig
            step = (self.cdf(u).sum() - k) / max((dens(u) / sig).sum(), 1e-9)
            t += step
            if abs(step) < 1e-8:
                break
        return self.cdf((s - t) / sig), k

    def log_prior(self, th):
        w, sigma, h, k = self.unpack(th)
        lp = -0.5 * np.sum((w / self.prior_sd) ** 2)
        lp += -0.5 * ((np.log(sigma) - np.log(0.15)) / 1.5) ** 2
        if self.g is not None:
            lp += -0.5 * (h / 1.0) ** 2
        if self.free_k:
            lp += -0.5 * ((k - self.k0) / 4.0) ** 2
        return lp


def moments(p, k, Y):
    """Mean vector and covariance of the error counts of the files in Y under reference probs p."""
    v = p * (1 - p)
    n = Y.sum(1)
    mu = n + k - 2 * Y @ p
    Yv = Y @ v
    C = 4 * ((Y * v) @ Y.T - np.outer(Yv, Yv) / v.sum())
    return mu, C


def gauss_ll(r, C):
    C = C + NUGGET * np.eye(len(r))
    L = np.linalg.cholesky(C)
    a = np.linalg.solve(L, r)
    return -0.5 * a @ a - np.log(np.diag(L)).sum() - 0.5 * len(r) * np.log(2 * np.pi)


def log_lik(fam, th, Y, E):
    p, k = fam.probs(th)
    mu, C = moments(p, k, Y)
    try:
        return gauss_ll(E - mu, C)
    except np.linalg.LinAlgError:
        return -1e12


def log_post(fam, th, Y, E):
    return log_lik(fam, th, Y, E) + fam.log_prior(th)


def conditional_prediction(p, k, Y_obs, E_obs, Y_new):
    """Predictive mean/sd of the error counts of Y_new given the observed readings (kriging)."""
    Y = np.vstack([Y_obs, Y_new])
    mu, C = moments(p, k, Y)
    J = len(Y_obs)
    Coo = C[:J, :J] + NUGGET * np.eye(J)
    Cno = C[J:, :J]
    sol = np.linalg.solve(Coo, np.c_[E_obs - mu[:J], Cno.T])
    mean = mu[J:] + Cno @ sol[:, 0]
    var = np.diag(C[J:, J:]) - np.einsum("ij,ji->i", Cno, sol[:, 1:]) + NUGGET
    return mean, np.sqrt(np.maximum(var, 1e-9))


def top_k(score, k):
    grant = np.zeros(N)
    grant[np.argsort(-score, kind="stable")[:k]] = 1
    return grant
