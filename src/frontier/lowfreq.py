"""Low-frequency analysis in the spirit of Mueller and Watson (2008, 2018).

A series of length T is projected on the first q cosine functions
Psi_j(t) = sqrt(2) cos(j pi (t - 1/2) / T), j = 1..q. These keep only
fluctuations with periods longer than 2T/q years. Regressions on the q
projection coefficients give honest small-sample inference about long-run
co-movement: there are only q effective observations.
"""
import numpy as np
from scipy import stats


def basis(T, q):
    t = np.arange(T) + 0.5
    j = np.arange(1, q + 1)
    return np.sqrt(2) * np.cos(np.pi * np.outer(t, j) / T)


def project(x, q):
    x = np.asarray(x, float)
    return basis(len(x), q).T @ x / len(x)


def trend(x, q):
    """Low-frequency component: mean plus the first q cosine terms."""
    x = np.asarray(x, float)
    return x.mean() + basis(len(x), q) @ project(x, q)


def regression(y, X, q, names=None):
    """OLS of the q cosine coefficients of y on those of the columns of X (no constant).

    The constant is absorbed because cosine terms j >= 1 are orthogonal to the mean.
    t-statistics use q - k degrees of freedom.
    """
    X = np.atleast_2d(np.asarray(X, float))
    if X.shape[0] != len(y):
        X = X.T
    Y = project(y, q)
    P = np.column_stack([project(X[:, k], q) for k in range(X.shape[1])])
    beta, *_ = np.linalg.lstsq(P, Y, rcond=None)
    resid = Y - P @ beta
    k = P.shape[1]
    s2 = resid @ resid / (q - k)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(P.T @ P)))
    t = beta / se
    p_two = 2 * stats.t.sf(np.abs(t), q - k)
    r2 = 1 - (resid @ resid) / (Y @ Y)
    names = names or [f"x{k}" for k in range(X.shape[1])]
    return {"q": q, "dof": q - k, "r2": float(r2),
            "coef": dict(zip(names, beta.tolist())), "se": dict(zip(names, se.tolist())),
            "t": dict(zip(names, t.tolist())), "p": dict(zip(names, p_two.tolist()))}


def correlation(y, x, q):
    """Long-run correlation: correlation of the cosine coefficients."""
    a, b = project(y, q), project(x, q)
    return float(a @ b / np.sqrt((a @ a) * (b @ b)))
