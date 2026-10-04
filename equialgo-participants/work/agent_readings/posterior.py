"""Posterior sampling (adaptive Metropolis) for the reference families that predict best out of sample,
plus fast predictive scoring of many candidate files conditional on every reading.

A candidate file F is stored as a sparse difference from a base scored file (r4_16), so the
cross-covariances with the scored files cost O(changed decisions) per posterior draw.
"""
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np  # noqa: E402
from scipy import sparse  # noqa: E402
from scipy.special import ndtr  # noqa: E402

from readings_lib import NUGGET, log_post  # noqa: E402


def adaptive_metropolis(fam, Y, E, th0, n_iter=12000, burn=3000, thin=10, seed=0):
    rng = np.random.default_rng(seed)
    d = len(th0)
    th, lp = th0.copy(), log_post(fam, th0, Y, E)
    cov = np.diag(np.r_[np.full(fam.m, 0.01), 0.1, np.full(d - fam.m - 1, 0.1)] ** 2)
    hist, keep, acc = [], [], 0
    for it in range(n_iter):
        if it > 500 and it % 200 == 0:
            cov = np.cov(np.array(hist[-4000:]).T) * 2.38 ** 2 / d + 1e-8 * np.eye(d)
        prop = rng.multivariate_normal(th, cov)
        lp_prop = log_post(fam, prop, Y, E)
        if np.log(rng.random()) < lp_prop - lp:
            th, lp = prop, lp_prop
            if it >= burn:
                acc += 1
        hist.append(th.copy())
        if it >= burn and (it - burn) % thin == 0:
            keep.append(th.copy())
    return np.array(keep), acc / (n_iter - burn)


class Predictor:
    """Predictive distribution of err(F) for many files F given the readings (Y_obs, E_obs)."""

    def __init__(self, Y_obs, E_obs, base, files):
        self.Y, self.E = Y_obs, E_obs
        self.base = base
        files = np.asarray(files, float)
        self.n = files.sum(1)
        self.D = sparse.csr_matrix(files - base[None, :])
        self.sum_m = np.zeros(len(files))
        self.sum_m2s2 = np.zeros(len(files))
        self.cdf = {}
        self.draws = 0

    def add(self, p, k, thresholds=(211.5, 207.5, 199.5)):
        Y, E, b, D = self.Y, self.E, self.base, self.D
        v = p * (1 - p)
        sv = v.sum()
        Yv = Y @ v
        mu_o = Y.sum(1) + k - 2 * Y @ p
        Coo = 4 * ((Y * v) @ Y.T - np.outer(Yv, Yv) / sv) + NUGGET * np.eye(len(E))
        Fv = b @ v + D @ v
        Fp = b @ p + D @ p
        cross = (b * v) @ Y.T + D @ (Y * v).T          # (n_files, J): F . (v * Y_j)
        Cno = 4 * (cross - np.outer(Fv, Yv) / sv)
        var_f = 4 * (Fv - Fv ** 2 / sv)
        mu_f = self.n + k - 2 * Fp
        sol = np.linalg.solve(Coo, np.c_[E - mu_o, Cno.T])
        m = mu_f + Cno @ sol[:, 0]
        s2 = np.maximum(var_f - np.einsum("ij,ji->i", Cno, sol[:, 1:]), 1e-9) + NUGGET
        self.sum_m += m
        self.sum_m2s2 += m ** 2 + s2
        for t in thresholds:
            self.cdf[t] = self.cdf.get(t, 0) + ndtr((t - m) / np.sqrt(s2))
        self.draws += 1

    def summary(self):
        mean = self.sum_m / self.draws
        sd = np.sqrt(np.maximum(self.sum_m2s2 / self.draws - mean ** 2, 0))
        return mean, sd, {t: c / self.draws for t, c in self.cdf.items()}


def joint_conditional(p, k, Y_obs, E_obs, F):
    """Joint predictive mean and covariance of the error counts of files F given the readings."""
    v = p * (1 - p)
    sv = v.sum()
    Yall = np.vstack([Y_obs, F])
    Yv = Yall @ v
    mu = Yall.sum(1) + k - 2 * Yall @ p
    C = 4 * ((Yall * v) @ Yall.T - np.outer(Yv, Yv) / sv)
    J = len(Y_obs)
    Coo = C[:J, :J] + NUGGET * np.eye(J)
    Cno = C[J:, :J]
    sol = np.linalg.solve(Coo, np.c_[E_obs - mu[:J], Cno.T])
    mean = mu[J:] + Cno @ sol[:, 0]
    cov = C[J:, J:] - Cno @ sol[:, 1:] + NUGGET * np.eye(len(F))
    return mean, cov
