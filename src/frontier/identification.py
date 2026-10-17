"""Tools for the endogeneity checks.

- lf_iv:          two-stage least squares on low-frequency (cosine) coefficients
- neutralize:     replace growth inside given windows by the window average
                  (equivalent to linear interpolation of log levels)
- lead_lag:       long-run correlation of y_t with x_{t-k} for a range of k
- novy_tau:       inverse-gravity bilateral trade costs (Novy 2013; Jacks, Meissner and Novy 2011)
"""
import numpy as np
import pandas as pd
from scipy import stats

from . import lowfreq


def _proj(M, q):
    M = np.atleast_2d(np.asarray(M, float))
    if M.shape[0] == 1:
        M = M.T
    return np.column_stack([lowfreq.project(M[:, k], q) for k in range(M.shape[1])])


def lf_ols(y, X, q, names):
    return lowfreq.regression(y, X, q, names)


def lf_iv(y, X_endog, Z, q, W=None, names=None):
    """2SLS on the q cosine coefficients. X_endog: (T,) one endogenous regressor.

    W: optional exogenous controls (T, kw). Z: instruments (T, kz).
    Returns the coefficient on X_endog, its standard error, the first-stage F and dof.
    """
    Y = lowfreq.project(y, q)
    Xe = _proj(X_endog, q)
    Zp = _proj(Z, q)
    Wp = _proj(W, q) if W is not None else np.empty((q, 0))
    Zfull = np.column_stack([Zp, Wp])
    Xfull = np.column_stack([Xe, Wp])
    # first stage
    b1, *_ = np.linalg.lstsq(Zfull, Xe[:, 0], rcond=None)
    fitted = Zfull @ b1
    resid1 = Xe[:, 0] - fitted
    # first-stage F for the excluded instruments
    if Wp.shape[1]:
        bw, *_ = np.linalg.lstsq(Wp, Xe[:, 0], rcond=None)
        rss_r = ((Xe[:, 0] - Wp @ bw) ** 2).sum()
    else:
        rss_r = (Xe[:, 0] ** 2).sum()
    rss_u = (resid1 ** 2).sum()
    kz = Zp.shape[1]
    dof1 = q - Zfull.shape[1]
    F = ((rss_r - rss_u) / kz) / (rss_u / dof1) if dof1 > 0 else np.nan
    # second stage
    Xhat = np.column_stack([fitted, Wp])
    b2, *_ = np.linalg.lstsq(Xhat, Y, rcond=None)
    e = Y - Xfull @ b2
    dof = q - Xfull.shape[1]
    s2 = e @ e / dof
    V = s2 * np.linalg.inv(Xhat.T @ Xhat)
    se = np.sqrt(np.diag(V))
    t = b2 / se
    names = names or ["x"] + [f"w{k}" for k in range(Wp.shape[1])]
    return {"q": q, "dof": dof, "first_stage_F": float(F), "first_stage_coef": b1[:kz].tolist(),
            "coef": dict(zip(names, b2.tolist())), "se": dict(zip(names, se.tolist())),
            "t": dict(zip(names, t.tolist())),
            "p": dict(zip(names, (2 * stats.t.sf(np.abs(t), dof)).tolist()))}


def neutralize(g, windows):
    """g: pandas Series of growth indexed by year. Inside each (a, b) window, growth is
    replaced by its window mean, so only the cumulative change across the window survives."""
    g = g.copy()
    for a, b in windows:
        idx = (g.index >= a) & (g.index <= b)
        g[idx] = g[idx].mean()
    return g


def lead_lag(y, x, q, lags):
    """Long-run correlation of y_t with x_{t-k}. Positive k: x leads y by k years."""
    y, x = np.asarray(y, float), np.asarray(x, float)
    out = {}
    for k in lags:
        if k >= 0:
            yy, xx = y[k:], x[:len(x) - k]
        else:
            yy, xx = y[:len(y) + k], x[-k:]
        out[int(k)] = lowfreq.correlation(yy, xx, q)
    return out


def _within(M, groups, iters=100):
    """Two-way (or more) fixed-effects demeaning by alternating projections."""
    M = np.asarray(M, float).copy()
    for _ in range(iters):
        for g in groups:
            M = M - pd.DataFrame(M).groupby(g).transform("mean").values
    return M


def panel_iv(df, y, endog, instruments, exog=(), fe=("iso", "period"), cluster="iso"):
    """2SLS with fixed effects (absorbed) and cluster-robust standard errors.

    Returns coefficients, clustered SEs, p-values (t with G-1 dof), first-stage
    cluster-robust F for the excluded instruments (one per endogenous regressor),
    and the OLS counterpart.
    """
    d = df.dropna(subset=[y, *endog, *instruments, *exog]).copy()
    groups = [d[f].values for f in fe]
    Y = _within(d[[y]].values, groups)[:, 0]
    X = _within(d[list(endog) + list(exog)].values, groups)
    Z = _within(d[list(instruments) + list(exog)].values, groups)
    cl = d[cluster].values
    G = len(np.unique(cl))
    n, k = X.shape

    def cluster_vcov(Xh, e, bread):
        meat = np.zeros((Xh.shape[1], Xh.shape[1]))
        for c in np.unique(cl):
            s = Xh[cl == c].T @ e[cl == c]
            meat += np.outer(s, s)
        adj = G / (G - 1) * (n - 1) / (n - Xh.shape[1])
        return adj * bread @ meat @ bread

    # first stages
    fs = {}
    PZ = Z @ np.linalg.pinv(Z.T @ Z) @ Z.T
    Xhat = PZ @ X
    kz = len(instruments)
    for m, name in enumerate(endog):
        g, *_ = np.linalg.lstsq(Z, X[:, m], rcond=None)
        e = X[:, m] - Z @ g
        V = cluster_vcov(Z, e, np.linalg.inv(Z.T @ Z))
        gi, Vi = g[:kz], V[:kz, :kz]
        fs[name] = float(gi @ np.linalg.pinv(Vi) @ gi / kz)
    # second stage
    b = np.linalg.solve(Xhat.T @ X, Xhat.T @ Y)
    e = Y - X @ b
    V = cluster_vcov(Xhat, e, np.linalg.inv(Xhat.T @ Xhat))
    se = np.sqrt(np.diag(V))
    names = list(endog) + list(exog)
    tstat = b / se
    # OLS for comparison
    bo = np.linalg.lstsq(X, Y, rcond=None)[0]
    eo = Y - X @ bo
    Vo = cluster_vcov(X, eo, np.linalg.inv(X.T @ X))
    return {"n": int(n), "clusters": int(G),
            "coef": dict(zip(names, b.tolist())), "se": dict(zip(names, se.tolist())),
            "p": dict(zip(names, (2 * stats.t.sf(np.abs(tstat), G - 1)).tolist())),
            "vcov": V.tolist(), "first_stage_F": fs,
            "ols_coef": dict(zip(names, bo.tolist())), "ols_se": dict(zip(names, np.sqrt(np.diag(Vo)).tolist()))}


def novy_tau(x_ij, x_ji, x_ii, x_jj, sigma=11.0):
    """Tariff-equivalent bilateral trade cost: ((x_ii x_jj)/(x_ij x_ji))^(1/(2(sigma-1))) - 1."""
    return np.power((x_ii * x_jj) / (x_ij * x_ji), 1.0 / (2.0 * (sigma - 1.0))) - 1.0
