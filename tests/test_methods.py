"""Sanity checks: each method recovers a known answer on simulated data.

Run with:  python -m pytest tests   (or  python tests/test_methods.py)
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from frontier import breaks, lowfreq, model  # noqa: E402


def test_bai_perron_finds_known_breaks():
    rng = np.random.default_rng(1)
    y = np.concatenate([np.full(50, 1.0), np.full(50, 3.0), np.full(50, 1.5)])
    y = y + rng.normal(0, 1.0, 150)
    res = breaks.bai_perron(y, np.arange(1870, 2020), max_breaks=3, reps=199)
    found = res["all_solutions"][2]["break_years"]
    assert abs(found[0] - 1919) <= 5 and abs(found[1] - 1969) <= 5
    assert res["p_UDmax"] < 0.05


def test_bai_perron_size_under_null():
    rng = np.random.default_rng(2)
    rejections = 0
    for s in range(20):
        y = rng.standard_t(4, 150)
        res = breaks.bai_perron(y, np.arange(150), max_breaks=3, reps=99, seed=s)
        rejections += res["p_UDmax"] < 0.05
    assert rejections <= 4  # nominal 5%: allow sampling noise in 20 draws


def test_lowfreq_regression_recovers_slope():
    rng = np.random.default_rng(3)
    T = 150
    x = np.cumsum(rng.normal(0, 0.3, T))  # persistent regressor
    y = 0.5 * x + rng.normal(0, 0.5, T)
    res = lowfreq.regression(y, x[:, None], q=12, names=["x"])
    assert abs(res["coef"]["x"] - 0.5) < 0.2


def test_model_recovers_kappa():
    rng = np.random.default_rng(4)
    T, N = 150, 4
    S = np.exp(np.cumsum(rng.normal(0.01, 0.002, (T, N)), axis=0))
    O = np.clip(0.4 + 0.25 * np.sin(np.linspace(0, 4, T))[:, None] + rng.normal(0, 0.01, (T, N)), 0.05, 1.5)
    m = model.Model(S, O, hub_idx=0, years=np.arange(T))
    y = m.path(0.012, 0.8, 1.0)
    fit = m.fit(y)
    assert abs(fit["kappa"] - 1.0) < 0.25


def test_lowfreq_iv_removes_endogeneity_bias():
    from frontier import identification as ID
    rng = np.random.default_rng(5)
    ols, iv = [], []
    for _ in range(200):
        z = np.cumsum(rng.normal(0, 0.3, 150))
        u = np.cumsum(rng.normal(0, 0.3, 150))
        x = 2 * z + u
        y = 0.5 * x - 1.0 * u + rng.normal(0, 0.3, 150)  # x is correlated with the error through u
        ols.append(lowfreq.regression(y, x[:, None], 12, ["x"])["coef"]["x"])
        iv.append(ID.lf_iv(y, x, z[:, None], 12)["coef"]["x"])
    assert abs(np.median(iv) - 0.5) < 0.1 < abs(np.median(ols) - 0.5)


def test_panel_iv_recovers_effect_with_fixed_effects():
    import pandas as pd
    from frontier import identification as ID
    rng = np.random.default_rng(6)
    rows = []
    shocks = rng.normal(0, 1, 30)
    for i in range(16):
        a = rng.normal()
        for t in range(30):
            z = rng.normal()
            u = rng.normal()
            x = z + u + shocks[t]
            y = a + 2 * shocks[t] + 0.7 * x - 1.0 * u + rng.normal(0, 0.5)
            rows.append({"iso": i, "period": t, "x": x, "z": z, "y": y})
    res = ID.panel_iv(pd.DataFrame(rows), "y", ["x"], ["z"])
    assert abs(res["coef"]["x"] - 0.7) < 0.15
    assert res["first_stage_F"]["x"] > 50


def _ar(rng, T, rho, s):
    x = np.zeros(T)
    for t in range(1, T):
        x[t] = rho * x[t - 1] + rng.normal(0, s)
    return x


def test_balancing_ratio_size_and_power():
    from frontier import balancing as Bl
    rng = np.random.default_rng(8)
    T, q = 132, 10
    rej_null = rej_alt = 0
    for _ in range(40):
        C = np.column_stack([_ar(rng, T, 0.7, 1), _ar(rng, T, 0.7, 0.5), _ar(rng, T, 0.7, 0.8)])
        nd = Bl.null_distribution(C, q, 199, rng, "phase")
        rej_null += (nd <= Bl.ratio(C, q)).mean() < 0.05
        p = _ar(rng, T, 0.9, 1)
        C2 = np.column_stack([p, _ar(rng, T, 0.7, 0.4), -0.6 * p + _ar(rng, T, 0.5, 0.3)])
        nd2 = Bl.null_distribution(C2, q, 199, rng, "phase")
        rej_alt += (nd2 <= Bl.ratio(C2, q)).mean() < 0.05
    assert rej_null <= 6 and rej_alt >= 35


def test_cross_source_correction_reduces_division_bias():
    from frontier import balancing as Bl
    rng = np.random.default_rng(9)
    T, q, a = 132, 10, 1 / 3
    err_obs, err_corr = [], []
    for _ in range(30):
        true = np.column_stack([_ar(rng, T, 0.8, 1), _ar(rng, T, 0.8, 0.5), _ar(rng, T, 0.8, 0.8)])

        def observed(err):
            return np.column_stack([true[:, 0] - (1 - a) * err, true[:, 1] - a * err, true[:, 2] + err])
        A, Bm = observed(_ar(rng, T, 0.8, 0.8)), observed(_ar(rng, T, 0.8, 0.8))
        r_true = Bl.ratio(true, q)
        err_obs.append(Bl.ratio(A, q) - r_true)
        err_corr.append(Bl.corrected_ratio(A, Bm, q)[0] - r_true)
    # measurement error biases the ratio down; the cross-source version removes most of the bias
    assert np.median(err_obs) < -0.1 and abs(np.median(err_corr)) < abs(np.median(err_obs)) / 2


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
