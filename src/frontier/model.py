"""Semi-endogenous growth with an integration-weighted world research pool.

    dA/A = a * Seff_t^lambda * A_t^(phi - 1),   lambda = 1 (normalization), beta = 1 - phi
    Seff_t = sum_i w_it S_it,   w_it = min(1, open_it^kappa), hub weight = 1
    g_y = g_A / (1 - capital share)

Parameters (a, beta, kappa) are estimated by minimum distance: the model's
annual frontier growth path must match the low-frequency moments (mean and the
first q cosine coefficients) of observed frontier growth. kappa = 0 is the
conventional unweighted pool; kappa > 0 means integration matters.
"""
import numpy as np
from scipy import optimize

from . import config as C
from . import lowfreq


def eff_growth(S, O, kappa, hub_idx):
    """Chain-linked log growth of the effective pool (array of length T, first = nan)."""
    w = np.minimum(1.0, np.power(O, kappa))
    w[:, hub_idx] = 1.0
    eff = w * S
    prev, cur = eff[:-1], eff[1:]
    ok = np.isfinite(prev) & np.isfinite(cur) & (prev > 0)
    prev0 = np.where(ok, prev, 0.0)
    share = prev0 / prev0.sum(axis=1, keepdims=True)
    lg = np.where(ok, np.log(np.where(ok, cur, 1.0) / np.where(ok, prev, 1.0)), 0.0)
    g = (share * lg).sum(axis=1)
    return np.concatenate([[np.nan], g])


def eff_level(S, O, kappa, hub_idx):
    g = eff_growth(S, O, kappa, hub_idx)
    return np.exp(np.concatenate([[0.0], np.cumsum(g[1:])]))


def simulate(level, a, beta):
    """Frontier output growth path (percent) implied by an effective-pool level path."""
    T = len(level)
    gA = np.empty(T)
    logA = 0.0
    for t in range(T):
        gA[t] = a * level[t] * np.exp(-beta * logA)
        logA += gA[t]
    return 100 * gA / (1 - C.CAPITAL_SHARE)


def moments(x, q):
    return np.concatenate([[np.mean(x)], lowfreq.project(x, q)])


class Model:
    def __init__(self, S, O, hub_idx, years, q=C.LF_Q):
        self.S, self.O, self.hub, self.years, self.q = S, O, hub_idx, np.asarray(years), q

    def path(self, a, beta, kappa, O=None, S=None):
        O = self.O if O is None else O
        S = self.S if S is None else S
        return simulate(eff_level(S, O, kappa, self.hub), a, beta)

    def fit(self, y, kappa=None):
        """Estimate (a, beta[, kappa]) to match low-frequency moments of y (aligned with years)."""
        target = moments(y, self.q)

        def loss(theta):
            a, beta = np.exp(theta[0]), np.exp(theta[1])
            k = kappa if kappa is not None else theta[2]
            m = moments(self.path(a, beta, k), self.q)
            return float(((m - target) ** 2).sum())

        best = None
        starts = [(a0, b0, k0) for a0 in (0.005, 0.015) for b0 in (0.3, 1.5)
                  for k0 in ((0.0, 0.7, 2.0) if kappa is None else (None,))]
        for a0, b0, k0 in starts:
            x0 = [np.log(a0), np.log(b0)] + ([] if kappa is not None else [k0])
            bounds = [(np.log(1e-4), np.log(0.2)), (np.log(0.02), np.log(20))]
            if kappa is None:
                bounds.append((0.0, 4.0))
            res = optimize.minimize(loss, x0, method="L-BFGS-B", bounds=bounds)
            if best is None or res.fun < best.fun:
                best = res
        a, beta = np.exp(best.x[0]), np.exp(best.x[1])
        k = kappa if kappa is not None else float(best.x[2])
        return {"a": float(a), "beta": float(beta), "kappa": float(k), "loss": float(best.fun),
                "fitted": self.path(a, beta, k)}
