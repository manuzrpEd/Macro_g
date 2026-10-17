"""Exponential vs additive vs slowly declining growth of a level series y_t (e.g. GDP per capita).

Every model gives a one-step-ahead predictive density for z_t = dlog y_t given the past,
so all are scored on the same scale (log y). Models:

  EXP     z_t = g + e_t                                      constant growth (exponential)
  EXPDEC  z_t = g0 + g1 * (t - t0) + e_t                     linearly declining growth
  DRIFT   z_t = g_t + e_t, g_t estimated by exponential discounting of past growth
          (steady-state Kalman filter of a random-walk trend growth; discount lambda estimated)
  ADDH    y_t = y_{t-1} + b + u_t,  u_t ~ N(0, s^2)          additive, homoskedastic noise
  ADDP    y_t = y_{t-1} (1 + b / y_{t-1} + n_t), n ~ N(0,s^2) additive mean, proportional noise
  EXPB / ADDPB  the EXP / ADDP models with one break in g / b (date chosen by likelihood)

The additive models imply growth rates b / y_{t-1} that fall as income rises.
"""
import numpy as np
from scipy import optimize, stats

MIN_SEG = 20  # minimum years on each side of a break


# ----------------------------------------------------------------------------- fitting
def fit(model, y, t):
    """Estimate parameters on levels y (array) observed at years t. Returns a dict."""
    y = np.asarray(y, float)
    t = np.asarray(t, float)
    z = np.diff(np.log(y))
    tz = t[1:]
    ylag = y[:-1]
    if model == "EXP":
        return {"g": z.mean(), "s": z.std(ddof=1), "k": 2}
    if model == "EXPDEC":
        X = np.column_stack([np.ones_like(tz), tz - tz.mean()])
        b, *_ = np.linalg.lstsq(X, z, rcond=None)
        e = z - X @ b
        return {"g0": b[0], "g1": b[1], "tc": tz.mean(), "s": e.std(ddof=2), "k": 3}
    if model == "DRIFT":
        best = None
        for lam in np.linspace(0.80, 0.995, 40):
            m = _drift_means(z, lam)
            e = z[10:] - m[10:]
            s = e.std()
            ll = stats.norm.logpdf(e, 0, s).sum()
            if best is None or ll > best[0]:
                best = (ll, lam, s)
        lam, s = best[1], best[2]
        return {"lam": lam, "s": s, "g_last": _drift_means(np.append(z, 0.0), lam)[-1],
                "g_start": z[:10].mean(), "k": 2}
    if model == "ADDH":
        d = np.diff(y)
        return {"b": d.mean(), "s": d.std(ddof=1), "k": 2}
    if model == "ADDP":
        return _fit_addp(z, ylag)
    if model in ("EXPB", "ADDPB"):
        if len(z) < 2 * MIN_SEG + 1:  # too short for a break: same parameters on both sides
            base = fit("EXP" if model == "EXPB" else "ADDP", y, t)
            if model == "EXPB":
                return {"g1": base["g"], "g2": base["g"], "s": base["s"], "break_year": float(tz[-1] + 1), "k": 4}
            return {"b1": base["b"], "b2": base["b"], "s": base["s"], "break_year": float(tz[-1] + 1), "k": 4}
        best = None
        for j in range(MIN_SEG, len(z) - MIN_SEG):
            if model == "EXPB":
                m = np.where(np.arange(len(z)) < j, z[:j].mean(), z[j:].mean())
                e = z - m
                s = e.std()
                ll = stats.norm.logpdf(e, 0, s).sum()
                par = {"g1": z[:j].mean(), "g2": z[j:].mean(), "s": s}
            else:
                p1, p2 = _fit_addp(z[:j], ylag[:j]), _fit_addp(z[j:], ylag[j:])
                eta = np.concatenate([_addp_eta(z[:j], ylag[:j], p1["b"]), _addp_eta(z[j:], ylag[j:], p2["b"])])
                s = eta.std()
                ll = (stats.norm.logpdf(eta, 0, s) + z).sum()
                par = {"b1": p1["b"], "b2": p2["b"], "s": s}
            if best is None or ll > best[0]:
                best = (ll, j, par)
        par = best[2]
        par.update({"break_year": float(tz[best[1]]), "k": 4})
        return par
    raise ValueError(model)


def _drift_means(z, lam):
    """Predicted growth for each t from past growth only (discounted average):
    m[0] = mean of the first 10 growth rates; m[i+1] = lam * m[i] + (1 - lam) * z[i]."""
    from scipy.signal import lfilter
    z = np.asarray(z, float)
    g0 = z[:10].mean()
    # m[i] = lam^i g0 + (1-lam) sum_{j<i} lam^(i-1-j) z[j]
    filt = lfilter([0.0, 1 - lam], [1.0, -lam], z)
    return filt + g0 * lam ** np.arange(len(z))


def _addp_eta(z, ylag, b):
    return np.exp(z) - 1 - b / ylag


def _fit_addp(z, ylag):
    # E[exp(z) - 1] = b / ylag  ->  least squares for b, then s
    r = np.exp(z) - 1
    x = 1 / ylag
    b = float((x @ r) / (x @ x))
    s = float(np.std(r - b * x))
    return {"b": b, "s": s, "k": 2}


# ----------------------------------------------------------------------------- scoring
def loglik(model, par, y, t):
    """In-sample log-likelihood of z_t = dlog y_t (Jacobians included so all models are comparable)."""
    y = np.asarray(y, float)
    t = np.asarray(t, float)
    z = np.diff(np.log(y))
    tz = t[1:]
    ylag = y[:-1]
    s = par["s"]
    if model == "EXP":
        return stats.norm.logpdf(z, par["g"], s).sum()
    if model == "EXPDEC":
        return stats.norm.logpdf(z, par["g0"] + par["g1"] * (tz - par["tc"]), s).sum()
    if model == "DRIFT":
        m = _drift_means(z, par["lam"])
        return stats.norm.logpdf(z[10:], m[10:], s).sum() + stats.norm.logpdf(z[:10], z[:10].mean(), s).sum()
    if model == "ADDH":
        # density of y_t, converted to density of log y_t: f(log y) = f(y) * y
        return (stats.norm.logpdf(y[1:], ylag + par["b"], s) + np.log(y[1:])).sum()
    if model == "ADDP":
        eta = _addp_eta(z, ylag, par["b"])
        return (stats.norm.logpdf(eta, 0, s) + z).sum()
    if model == "EXPB":
        m = np.where(tz < par["break_year"], par["g1"], par["g2"])
        return stats.norm.logpdf(z, m, s).sum()
    if model == "ADDPB":
        b = np.where(tz < par["break_year"], par["b1"], par["b2"])
        eta = np.exp(z) - 1 - b / ylag
        return (stats.norm.logpdf(eta, 0, s) + z).sum()
    raise ValueError(model)


def one_step_logscore(model, par, y_hist, t_hist, y_next, t_next):
    """Log predictive density of log y_next given history (parameters fitted on history)."""
    y_hist = np.asarray(y_hist, float)
    z_next = np.log(y_next) - np.log(y_hist[-1])
    s = par["s"]
    if model == "EXP":
        return stats.norm.logpdf(z_next, par["g"], s)
    if model == "EXPDEC":
        return stats.norm.logpdf(z_next, par["g0"] + par["g1"] * (t_next - par["tc"]), s)
    if model == "DRIFT":
        z = np.diff(np.log(y_hist))
        m = _drift_means(np.append(z, 0.0), par["lam"])[-1]
        return stats.norm.logpdf(z_next, m, s)
    if model == "ADDH":
        return stats.norm.logpdf(y_next, y_hist[-1] + par["b"], s) + np.log(y_next)
    if model == "ADDP":
        eta = np.exp(z_next) - 1 - par["b"] / y_hist[-1]
        return stats.norm.logpdf(eta, 0, s) + z_next
    if model == "EXPB":
        return stats.norm.logpdf(z_next, par["g2"], s)
    if model == "ADDPB":
        eta = np.exp(z_next) - 1 - par["b2"] / y_hist[-1]
        return stats.norm.logpdf(eta, 0, s) + z_next
    raise ValueError(model)


def forecast_paths(model, par, y_hist, t_hist, h, n, rng):
    """Simulated log-level paths h years ahead (shocks only; parameters held at estimates)."""
    y0 = float(y_hist[-1])
    t0 = float(t_hist[-1])
    s = par["s"]
    out = np.empty((n, h))
    if model in ("EXP", "EXPB", "EXPDEC", "DRIFT"):
        if model == "EXP":
            mu = np.full(h, par["g"])
        elif model == "EXPB":
            mu = np.full(h, par["g2"])
        elif model == "EXPDEC":
            mu = par["g0"] + par["g1"] * (t0 + np.arange(1, h + 1) - par["tc"])
        else:
            z = np.diff(np.log(y_hist))
            mu = np.full(h, _drift_means(np.append(z, 0.0), par["lam"])[-1])
        shocks = rng.normal(0, s, (n, h))
        return np.log(y0) + np.cumsum(mu + shocks, axis=1)
    if model == "ADDH":
        y = np.full(n, y0)
        for j in range(h):
            y = np.maximum(y + par["b"] + rng.normal(0, s, n), 1e-6)
            out[:, j] = np.log(y)
        return out
    if model in ("ADDP", "ADDPB"):
        b = par["b"] if model == "ADDP" else par["b2"]
        y = np.full(n, y0)
        for j in range(h):
            y = np.maximum(y * (1 + b / y + rng.normal(0, s, n)), 1e-6)
            out[:, j] = np.log(y)
        return out
    raise ValueError(model)


def simulate(model, par, y0, t, rng):
    """Simulate a level path of length len(t) starting at y0 from a fitted model (for power studies)."""
    T = len(t)
    y = np.empty(T)
    y[0] = y0
    s = par["s"]
    if model == "DRIFT":
        lam = par["lam"]
        q = s * (1 - lam) / np.sqrt(lam)  # steady-state Kalman: q/s = (1-lam)/sqrt(lam)
        g = par["g_start"]
    for i in range(1, T):
        if model == "EXP":
            z = par["g"] + rng.normal(0, s)
        elif model == "EXPDEC":
            z = par["g0"] + par["g1"] * (t[i] - par["tc"]) + rng.normal(0, s)
        elif model == "DRIFT":
            g = g + rng.normal(0, q)
            z = g + rng.normal(0, s)
        elif model == "ADDP":
            z = np.log(max(1 + par["b"] / y[i - 1] + rng.normal(0, s), 1e-3))
        elif model == "ADDH":
            z = np.log(max(y[i - 1] + par["b"] + rng.normal(0, s), 1e-3) / y[i - 1])
        else:
            raise ValueError(model)
        y[i] = y[i - 1] * np.exp(z)
    return y


# ----------------------------------------------------------------------------- power (Box-Cox) model and volatility trends
#   POW:   y^lam rises linearly in time:  dlog y_t = (1/lam) log(1 + lam * c * (y_{t-1}/y_0)^(-lam)) + e_t
#          lam -> 0: constant growth c (exponential); lam = 1: additive in levels (proportional noise);
#          lam ~ 2/3: what additive TFP implies for GDP per capita when capital follows TFP.
#   *VT:   same model with noise sd s_t = s * exp(f * (t - tc)) (a common volatility trend).
LAM_GRID = np.concatenate([[0.005], np.arange(0.05, 1.51, 0.05)])


def _pow_mean(lam, c, ylag, y0):
    x = np.maximum(1 + lam * c * (ylag / y0) ** (-lam), 1e-9)
    return np.log(x) / lam


def _fit_pow_given_lam(lam, z, ylag, y0, w=None):
    w = np.ones_like(z) if w is None else w
    def sse(logc):
        return float(np.sum(w * (z - _pow_mean(lam, np.exp(logc), ylag, y0)) ** 2))
    res = optimize.minimize_scalar(sse, bounds=(np.log(1e-5), np.log(5.0)), method="bounded")
    c = float(np.exp(res.x))
    e = z - _pow_mean(lam, c, ylag, y0)
    return c, e


def fit_pow(y, t):
    y = np.asarray(y, float)
    z = np.diff(np.log(y))
    ylag = y[:-1]
    y0 = y[0]
    prof = []
    best = None
    for lam in LAM_GRID:
        c, e = _fit_pow_given_lam(lam, z, ylag, y0)
        s = e.std()
        ll = stats.norm.logpdf(e, 0, s).sum()
        prof.append((float(lam), float(ll)))
        if best is None or ll > best[0]:
            best = (ll, lam, c, s)
    return {"lam": float(best[1]), "c": best[2], "s": float(best[3]), "y0": float(y0), "k": 3, "profile": prof}


def _vt_fit(resid_fn, n_mean_params, x0, tz):
    """Generic MLE with noise sd s * exp(f (t - tc)); resid_fn(theta) returns residuals in model units
    and a log-Jacobian term."""
    tc = tz.mean()
    def nll(theta):
        mean_par, logs, f = theta[:n_mean_params], theta[n_mean_params], theta[n_mean_params + 1]
        e, logjac = resid_fn(mean_par)
        st = np.exp(logs + f * (tz - tc))
        return -(stats.norm.logpdf(e, 0, st).sum() + logjac)
    res = optimize.minimize(nll, x0, method="Nelder-Mead", options={"maxiter": 4000, "xatol": 1e-7, "fatol": 1e-7})
    return res.x, -res.fun, tc


def fit_vt(model, y, t):
    y = np.asarray(y, float)
    t = np.asarray(t, float)
    z = np.diff(np.log(y))
    tz, ylag = t[1:], y[:-1]
    if model == "EXPVT":
        th, ll, tc = _vt_fit(lambda p: (z - p[0], 0.0), 1, [z.mean(), np.log(z.std()), 0.0], tz)
        return {"g": th[0], "s": float(np.exp(th[1])), "f": th[2], "tc": tc, "k": 3, "ll": ll}
    if model == "ADDPVT":
        b0 = _fit_addp(z, ylag)
        th, ll, tc = _vt_fit(lambda p: (np.exp(z) - 1 - p[0] / ylag, z.sum()), 1, [b0["b"], np.log(b0["s"]), 0.0], tz)
        return {"b": th[0], "s": float(np.exp(th[1])), "f": th[2], "tc": tc, "k": 3, "ll": ll}
    if model == "ADDHVT":
        d = np.diff(y)
        th, ll, tc = _vt_fit(lambda p: (d - p[0], np.log(y[1:]).sum()), 1, [d.mean(), np.log(d.std()), 0.0], tz)
        return {"b": th[0], "s": float(np.exp(th[1])), "f": th[2], "tc": tc, "k": 3, "ll": ll}
    if model == "POWVT":
        y0 = y[0]
        best = None
        for lam in LAM_GRID:
            c0, e0 = _fit_pow_given_lam(lam, z, ylag, y0)
            th, ll, tc = _vt_fit(lambda p, lam=lam: (z - _pow_mean(lam, np.exp(p[0]), ylag, y0), 0.0), 1,
                                 [np.log(c0), np.log(e0.std()), 0.0], tz)
            if best is None or ll > best[0]:
                best = (ll, lam, th, tc)
        ll, lam, th, tc = best
        return {"lam": float(lam), "c": float(np.exp(th[0])), "s": float(np.exp(th[1])), "f": th[2], "tc": tc,
                "y0": float(y0), "k": 4, "ll": ll}
    raise ValueError(model)


def vt_sd(par, t):
    return par["s"] * np.exp(par["f"] * (t - par["tc"]))


def loglik_ext(model, par, y, t):
    y = np.asarray(y, float)
    t = np.asarray(t, float)
    z = np.diff(np.log(y))
    ylag = y[:-1]
    if model == "POW":
        return stats.norm.logpdf(z - _pow_mean(par["lam"], par["c"], ylag, par["y0"]), 0, par["s"]).sum()
    return par["ll"]


def one_step_ext(model, par, y_hist, t_next, y_next):
    y_hist = np.asarray(y_hist, float)
    ylag = y_hist[-1]
    z = np.log(y_next) - np.log(ylag)
    if model == "POW":
        return stats.norm.logpdf(z, _pow_mean(par["lam"], par["c"], ylag, par["y0"]), par["s"])
    s = vt_sd(par, t_next)
    if model == "EXPVT":
        return stats.norm.logpdf(z, par["g"], s)
    if model == "ADDPVT":
        return stats.norm.logpdf(np.exp(z) - 1 - par["b"] / ylag, 0, s) + z
    if model == "ADDHVT":
        return stats.norm.logpdf(y_next, ylag + par["b"], s) + np.log(y_next)
    if model == "POWVT":
        return stats.norm.logpdf(z, _pow_mean(par["lam"], par["c"], ylag, par["y0"]), s)
    raise ValueError(model)


def forecast_paths_pow(par, y_hist, h, n, rng):
    y = np.full(n, float(y_hist[-1]))
    out = np.empty((n, h))
    for j in range(h):
        y = y * np.exp(_pow_mean(par["lam"], par["c"], y, par["y0"]) + rng.normal(0, par["s"], n))
        out[:, j] = np.log(y)
    return out


def simulate_pow(par, y0, t, rng):
    y = np.empty(len(t))
    y[0] = y0
    for i in range(1, len(t)):
        y[i] = y[i - 1] * np.exp(_pow_mean(par["lam"], par["c"], np.array([y[i - 1]]), par["y0"])[0] + rng.normal(0, par["s"]))
    return y
