"""eng2 : same model / likelihood as engine.py, with an analytic gradient and a pluggable design matrix.

theta = [beta (K) , t , log_sigma , lambda (Ks : optional design for log sigma_i)]
u_i = (r_i + x_i.beta - t) * exp(-(log_sigma + zs_i.lambda)),  p = Phi(u)
log-lik = MVN(z ; W p , (W*v) W^T + tau2 I)      (identical to engine.log_lik)
Nothing here modifies engine.py ; engine globals are only read.
"""
import os, sys
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(_v, '1')
SC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SC not in sys.path:
    sys.path.insert(0, SC)
import numpy as np
from scipy.optimize import minimize
from scipy.special import ndtr, expit
from scipy.linalg import solve_triangular, cho_solve
import engine as E
from engine import N, g, r, h, li, fg, ld

SQ2PI = np.sqrt(2 * np.pi)
KLOG = np.pi / np.sqrt(3)
cand = E.cand
REGIONS = sorted(cand.region_administrative.unique())
reg = cand.region_administrative.to_numpy()
prog = cand.programme_etudes.to_numpy()
code = cand.code_postal_3.to_numpy()
CODES = sorted(cand.code_postal_3.unique())
inc = cand.revenu_familial_estime.to_numpy().astype(float)
dist = cand.distance_domicile_campus_km.to_numpy().astype(float)
wgc = E.wgc


def centre_in(x, labels):
    """centre x within each level of labels"""
    out = x.astype(float).copy()
    for lv in np.unique(labels):
        out[labels == lv] -= out[labels == lv].mean()
    return out


def blocks():
    """Dictionary of feature blocks : name -> (matrix N x k, prior mean, prior sd, column names)."""
    B = {}
    B['base5'] = (E.X[:, :5].copy(), E.PRIOR_M[:5].copy(), np.array([0.25, 1.2, 1.0, 1.2, 0.5]), E.NAMES[:5])
    B['prog'] = (E.X[:, 5:].copy(), np.zeros(4), np.full(4, 0.15), E.NAMES[5:])
    # region contrasts inside each group (orthogonal to g by construction)
    cols, nm = [], []
    for a_, b_ in [('Montreal', 'Capitale-Nationale')]:
        cols.append(wgc((reg == a_).astype(float))); nm.append('reg_mtl_vs_cap')
    for a_ in ['Bas-Saint-Laurent', 'Cote-Nord']:
        cols.append(wgc((reg == a_).astype(float))); nm.append('reg_' + a_[:6])
    B['region'] = (np.column_stack(cols), np.zeros(3), np.full(3, 0.5), nm)
    rc = r - r.mean()
    B['r_x_el'] = (wgc(rc * g)[:, None], np.zeros(1), np.full(1, 0.15), ['r_x_el'])
    B['h_x_el'] = (wgc(wgc(h) * g)[:, None], np.zeros(1), np.full(1, 0.15), ['h_x_el'])
    B['li_x_el'] = (wgc(wgc(li) * g)[:, None], np.zeros(1), np.full(1, 0.6), ['li_x_el'])
    B['fg_x_el'] = (wgc(wgc(fg) * g)[:, None], np.zeros(1), np.full(1, 0.5), ['fg_x_el'])
    # threshold-type terms : within-group quartile dummies (lowest / highest quarter), centred within group
    for nmv, x in [('h', h), ('li', li)]:
        lo = np.zeros(N); hi = np.zeros(N)
        for k in (0, 1):
            q1, q3 = np.quantile(x[g == k], [0.25, 0.75])
            lo[g == k] = x[g == k] <= q1
            hi[g == k] = x[g == k] >= q3
        B[nmv + '_q'] = (np.column_stack([wgc(lo), wgc(hi)]), np.zeros(2), np.full(2, 0.5), [nmv + '_low_q', nmv + '_high_q'])
    # postal-code offsets, centred within region (13 free contrasts, 18 columns with a ridge prior)
    Pc = np.column_stack([centre_in((code == c).astype(float), reg) for c in CODES])
    B['postal'] = (Pc, np.zeros(len(CODES)), np.full(len(CODES), 0.3), ['cp_' + c for c in CODES])
    return B


class Model:
    def __init__(self, names=('base5', 'prog'), prior_sd=None, sig_lo=0.05, sig_hi=3.0, hetero=False, hetero_sd=0.5,
                 extra=None, t_bounds=(24.0, 33.0), link='probit'):
        self.link = link
        B = blocks()
        if extra:
            B.update(extra)
        prior_sd = prior_sd or {}
        Xs, pm, ps, cn, bl = [], [], [], [], []
        for n in names:
            X_, m_, s_, c_ = B[n]
            if n in prior_sd:
                s_ = np.full(X_.shape[1], prior_sd[n]) if np.isscalar(prior_sd[n]) else np.asarray(prior_sd[n], float)
            Xs.append(X_); pm.append(m_); ps.append(s_); cn += list(c_); bl += [n] * X_.shape[1]
        self.X = np.column_stack(Xs)
        self.K = self.X.shape[1]
        self.pm, self.ps, self.cn, self.bl = np.concatenate(pm), np.concatenate(ps), cn, bl
        self.hetero = hetero
        self.Zs = (g - g.mean())[:, None] if hetero else np.zeros((N, 0))
        self.Ks = self.Zs.shape[1]
        self.hetero_sd = hetero_sd
        self.D = self.K + 2 + self.Ks
        self.bounds = [(m - 4 * s, m + 4 * s) for m, s in zip(self.pm, self.ps)] + [t_bounds, (np.log(sig_lo), np.log(sig_hi))] \
            + [(-4 * hetero_sd, 4 * hetero_sd)] * self.Ks
        self.names = cn + ['seuil', 'log_sigma'] + ['dlogsig_el'] * self.Ks

    # ---- model pieces
    def u(self, th):
        K = self.K
        eta = th[K + 1] + (self.Zs @ th[K + 2:] if self.Ks else 0.0)
        return (r + self.X @ th[:K] - th[K]) * np.exp(-eta)

    def F(self, u):
        """link : cdf and density of the unit-variance latent noise."""
        if self.link == 'probit':
            return ndtr(u), np.exp(-0.5 * u * u) / SQ2PI
        p = expit(KLOG * u)                     # logistic noise scaled to unit variance
        return p, KLOG * p * (1 - p)

    def proba(self, th):
        return self.F(self.u(th))[0]

    def log_prior(self, th):
        K = self.K
        lp = -0.5 * (((th[:K] - self.pm) / self.ps) ** 2).sum() - 0.5 * ((th[K + 1] - E.LS_M) / E.LS_S) ** 2
        if self.Ks:
            lp -= 0.5 * ((th[K + 2:] / self.hetero_sd) ** 2).sum()
        return lp

    def nlp(self, th, W, z, tau2):
        return self.nlp_grad(th, W, z, tau2)[0]

    def nlp_grad(self, th, W, z, tau2):
        K = self.K
        eta = th[K + 1] + (self.Zs @ th[K + 2:] if self.Ks else 0.0)
        inv_s = np.exp(-eta)
        u = (r + self.X @ th[:K] - th[K]) * inv_s
        p, phi = self.F(u)
        v = p * (1 - p)
        C = (W * v) @ W.T
        C[np.diag_indices_from(C)] += tau2
        try:
            L = np.linalg.cholesky(C)
        except np.linalg.LinAlgError:
            return 1e12, np.zeros_like(th)
        d = z - W @ p
        alpha = cho_solve((L, True), d)
        ll = -0.5 * d @ alpha - np.log(np.diag(L)).sum()
        a = W.T @ alpha
        LiW = solve_triangular(L, W, lower=True)
        q = np.einsum('ij,ij->j', LiW, LiW)
        dl_du = (a + (1 - 2 * p) * 0.5 * (a * a - q)) * phi
        gr = np.empty_like(th)
        w_ = dl_du * inv_s
        gr[:K] = self.X.T @ w_
        gr[K] = -w_.sum()
        gr[K + 1] = -(dl_du * u).sum()
        if self.Ks:
            gr[K + 2:] = -(self.Zs.T @ (dl_du * u))
        # prior
        lp = self.log_prior(th)
        gr[:K] -= (th[:K] - self.pm) / self.ps ** 2
        gr[K + 1] -= (th[K + 1] - E.LS_M) / E.LS_S ** 2
        if self.Ks:
            gr[K + 2:] -= th[K + 2:] / self.hetero_sd ** 2
        return -(ll + lp), -gr

    # ---- fitting
    def init_theta(self, rng, q=0.399, spread=0.7):
        K = self.K
        beta = self.pm + self.ps * rng.standard_normal(K) * spread
        s = r + self.X @ beta
        th = np.r_[beta, np.quantile(s, 1 - q), rng.uniform(np.log(0.1), np.log(1.0)), np.zeros(self.Ks)]
        lo, hi = np.array(self.bounds).T
        return np.clip(th, lo, hi)

    def fit(self, W, z, n_starts=12, seed=0, tau2=0.25, starts=None, maxiter=500, return_all=False):
        rng = np.random.default_rng(seed)
        inits = list(starts) if starts is not None else []
        inits += [self.init_theta(rng) for _ in range(n_starts)]
        res_all = []
        for th0 in inits:
            res = minimize(self.nlp_grad, th0, args=(W, z, tau2), jac=True, method='L-BFGS-B', bounds=self.bounds,
                           options={'maxiter': maxiter, 'maxfun': 4 * maxiter, 'ftol': 1e-12, 'gtol': 1e-7})
            res_all.append(res)
        best = min(res_all, key=lambda q_: q_.fun)
        if return_all:
            return best.x, best.fun, res_all
        return best.x, best.fun

    def hessian(self, th, W, z, tau2, eps=1e-4):
        D = len(th)
        H = np.zeros((D, D))
        for k in range(D):
            e = np.zeros(D); e[k] = eps
            H[k] = (self.nlp_grad(th + e, W, z, tau2)[1] - self.nlp_grad(th - e, W, z, tau2)[1]) / (2 * eps)
        return 0.5 * (H + H.T)

    def laplace_draws(self, th, W, z, tau2, n=200, seed=0, inflate=1.0):
        """Draws from N(theta_hat, H^-1) clipped to the box ; H regularised to be positive definite."""
        H = self.hessian(th, W, z, tau2)
        w_, V = np.linalg.eigh(H)
        prior_prec = 1.0 / np.r_[self.ps, 3.0, E.LS_S, np.full(self.Ks, self.hetero_sd)] ** 2
        w_ = np.maximum(w_, 1e-3 * prior_prec.min())
        cov = (V / w_) @ V.T * inflate
        rng = np.random.default_rng(seed)
        Lc = np.linalg.cholesky(cov + 1e-12 * np.eye(len(th)))
        dr = th + rng.standard_normal((n, len(th))) @ Lc.T
        lo, hi = np.array(self.bounds).T
        return np.clip(dr, lo, hi)

    def post_mean_proba(self, th, W, z, tau2, n=200, seed=0, weights=True):
        """Posterior mean of p_i with importance re-weighting of Laplace draws (self-normalised)."""
        dr = self.laplace_draws(th, W, z, tau2, n=n, seed=seed)
        P = np.array([self.proba(t_) for t_ in dr])
        if not weights:
            return P.mean(0)
        H = self.hessian(th, W, z, tau2)
        lw = np.array([-self.nlp(t_, W, z, tau2) + 0.5 * (t_ - th) @ H @ (t_ - th) for t_ in dr])
        lw -= lw.max()
        w_ = np.exp(np.clip(lw, -20, 0))
        w_ /= w_.sum()
        return w_ @ P


def blup(p, W, z, tau2):
    """E[y | z] under the Gaussian approximation : p + v * W^T C^-1 (z - W p)."""
    v = p * (1 - p)
    C = (W * v) @ W.T
    C[np.diag_indices_from(C)] += tau2
    return p + v * (W.T @ np.linalg.solve(C, z - W @ p))


def is_posterior(M, th, W, z, tau2, n=2000, seed=0, df=5, inflate=1.5):
    """Importance sampling of the posterior with a multivariate-t proposal centred at the MAP (Laplace covariance).

    Returns draws (n x D), normalised weights, effective sample size. Out-of-box draws get weight 0."""
    D = len(th)
    H = M.hessian(th, W, z, tau2)
    w_, V = np.linalg.eigh(H)
    prior_prec = 1.0 / np.r_[M.ps, 3.0, E.LS_S, np.full(M.Ks, M.hetero_sd)] ** 2
    w_ = np.maximum(w_, 0.05 * prior_prec.min())
    cov = (V / w_) @ V.T * inflate
    Lc = np.linalg.cholesky(cov + 1e-12 * np.eye(D))
    rng = np.random.default_rng(seed)
    zn = rng.standard_normal((n, D))
    chi = rng.chisquare(df, n) / df
    dr = th + (zn @ Lc.T) / np.sqrt(chi)[:, None]
    dr[0] = th
    lo, hi = np.array(M.bounds).T
    inside = np.all((dr >= lo) & (dr <= hi), axis=1)
    # log q (up to a constant)
    maha = np.einsum('ij,ij->i', zn, zn) / chi
    maha[0] = 0.0
    logq = -0.5 * (df + D) * np.log1p(maha / df)
    logp = np.full(n, -np.inf)
    for i in np.where(inside)[0]:
        logp[i] = -M.nlp(dr[i], W, z, tau2)
    lw = logp - logq
    lw -= lw[inside].max()
    w = np.where(inside, np.exp(np.maximum(lw, -700)), 0.0)
    w /= w.sum()
    ess = 1.0 / (w ** 2).sum()
    return dr, w, ess


def log_evidence(M, th, W, z, tau2):
    """Laplace approximation of the log marginal likelihood (comparable across models sharing t / log-sigma priors)."""
    H = M.hessian(th, W, z, tau2)
    w_ = np.linalg.eigvalsh(H)
    w_ = np.maximum(w_, 1e-6)
    K = M.K + M.Ks
    log_norm_prior = -np.log(M.ps).sum() - (M.Ks * np.log(M.hetero_sd) if M.Ks else 0.0) - 0.5 * K * np.log(2 * np.pi)
    return -M.nlp(th, W, z, tau2) + log_norm_prior + 0.5 * M.D * np.log(2 * np.pi) - 0.5 * np.log(w_).sum()
