"""Do the sources of growth offset each other at low frequency?

Growth of GDP per capita is split into three additive parts (Bergeaud-Cette-Lecat):
    g_y = g_tfp + g_kd + g_h
    g_tfp  TFP growth
    g_kd   capital deepening contribution = growth of GDP per hour - TFP growth
    g_h    growth of hours worked per person

Low-frequency balancing statistic (periods longer than 2T/q years):
    R = Var_LF(g_y) / sum_k Var_LF(g_k)
R < 1: the parts offset; R = 1: independent; R > 1: they reinforce each other.

Inference uses surrogate data that keep each component's own persistence but make
components independent: random circular shifts and phase randomization.

Division bias: hours (and capital) errors enter the parts with opposite signs and
leave g_y unchanged, so they push R below 1 mechanically. With two independent
measurements of the parts (A and B), cross-source covariances remove classical,
source-specific errors: Var_true(c) ~ Cov(c_A, c_B).
"""
import numpy as np

from . import lowfreq

PARTS = ("tfp", "kd", "h")


def lf_dev(x, q):
    """Low-frequency component of x, demeaned."""
    x = np.asarray(x, float)
    return lowfreq.trend(x, q) - x.mean()


def lf_matrix(C, q):
    return np.column_stack([lf_dev(C[:, k], q) for k in range(C.shape[1])])


def ratio(C, q):
    L = lf_matrix(C, q)
    return float(np.var(L.sum(1)) / np.var(L, axis=0).sum())


def cov_shares(C, q, names=PARTS):
    """Contribution of each variance and covariance term to Var_LF(sum), as shares of sum of variances."""
    L = lf_matrix(C, q)
    V = np.cov(L.T, bias=True)
    denom = np.trace(V)
    out = {f"var_{n}": float(V[i, i] / denom) for i, n in enumerate(names)}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            out[f"2cov_{names[i]}_{names[j]}"] = float(2 * V[i, j] / denom)
    out["corr"] = {f"{names[i]}_{names[j]}": float(V[i, j] / np.sqrt(V[i, i] * V[j, j]))
                   for i in range(len(names)) for j in range(i + 1, len(names))}
    return out


def surrogate_shift(C, rng):
    T = C.shape[0]
    return np.column_stack([np.roll(C[:, k], rng.integers(0, T)) for k in range(C.shape[1])])


def surrogate_phase(C, rng):
    """Independent phase randomization of each column (keeps each spectrum, kills cross-spectra)."""
    T = C.shape[0]
    out = np.empty_like(C, dtype=float)
    for k in range(C.shape[1]):
        x = C[:, k] - C[:, k].mean()
        F = np.fft.rfft(x)
        ph = rng.uniform(0, 2 * np.pi, len(F))
        ph[0] = 0.0
        if T % 2 == 0:
            ph[-1] = 0.0
        out[:, k] = np.fft.irfft(np.abs(F) * np.exp(1j * ph), n=T) + C[:, k].mean()
    return out


def null_distribution(C, q, reps, rng, kind="phase"):
    f = surrogate_phase if kind == "phase" else surrogate_shift
    return np.array([ratio(f(C, rng), q) for _ in range(reps)])


def corrected_ratio(A, B, q):
    """Ratio from cross-source covariances of two independent measurements of the parts.

    A, B: (T, 3) arrays of the parts from two sources over the same years.
    Classical errors independent across sources drop out of cross-products.
    """
    LA, LB = lf_matrix(A, q), lf_matrix(B, q)
    T, k = LA.shape
    V = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            V[i, j] = 0.5 * (np.mean(LA[:, i] * LB[:, j]) + np.mean(LB[:, i] * LA[:, j]))
    return float(V.sum() / np.trace(V)), V


def error_variance_needed(C, q, alpha=1 / 3, source="hours"):
    """Low-frequency variance of measurement-error growth that alone would produce the observed R
    if the true parts were independent (true R = 1).

    Hours error e: g_h += de, g_tfp -= (1-alpha) de, g_kd -= alpha de  -> sum of variances rises by
    c * Var(de), c = 1 + (1-alpha)^2 + alpha^2.  Capital error u: g_kd += alpha du, g_tfp -= alpha du
    -> c = 2 alpha^2.
    """
    L = lf_matrix(C, q)
    var_sum = np.var(L.sum(1))
    sum_var = np.var(L, axis=0).sum()
    c = 1 + (1 - alpha) ** 2 + alpha ** 2 if source == "hours" else 2 * alpha ** 2
    needed = (sum_var - var_sum) / c
    own = np.var(L[:, 2]) if source == "hours" else np.var(L[:, 1]) / alpha ** 2
    return {"error_var_needed": float(needed), "as_share_of_observed_own_var": float(needed / own)}
