"""Calibrated power check for Project 2: can ~150 years detect a MEANINGFUL slow decline in trend growth?

The fitted 'declining growth' model on US data has an essentially zero slope, so the main power study
only asks whether a non-existent decline is detectable. Here we impose declines of plausible size and a
more variable drifting trend, keep the US noise level, and record how often each method detects them.
Output: output/growth_shape/power_calibrated.json
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier import growthshape as G  # noqa: E402
import run_growth_shape as RG  # noqa: E402


def main(reps=200):
    rng = np.random.default_rng(99)
    s = RG.series()["US (Maddison)"]
    t = s.index.values.astype(float)
    y = s.values
    sd = G.fit("EXP", y, t)["s"]
    tc = t[1:].mean()
    span = t[-1] - t[1]
    dgps = {
        "decline_2.5_to_1.0": {"g0": 0.0175, "g1": -0.015 / span, "tc": tc, "s": sd},
        "decline_2.0_to_1.5": {"g0": 0.0175, "g1": -0.005 / span, "tc": tc, "s": sd},
        "drift_lambda_0.95": {"lam": 0.95, "s": sd, "g_start": 0.018},
    }
    cands = ["EXP", "EXPDEC", "DRIFT", "ADDP", "POW"]
    n = len(y) - 1
    out = {"noise_sd": sd}
    for name, par in dgps.items():
        model = "EXPDEC" if name.startswith("decline") else "DRIFT"
        bic_w, pre_w, slope_sig = {}, {}, 0
        for _ in range(reps):
            ys = G.simulate(model, par, y[0], t, rng)
            fits = {m: RG.fitm(m, ys, t) for m in cands}
            bic = {m: -2 * RG.llm(m, fits[m], ys, t) + fits[m]["k"] * np.log(n) for m in cands}
            wb = min(bic, key=bic.get)
            bic_w[wb] = bic_w.get(wb, 0) + 1
            S, _ = RG.prequential(ys, t, models=[m for m in cands if m != "POW"], refit_every=10)
            wp = S.sum().idxmax()
            pre_w[wp] = pre_w.get(wp, 0) + 1
            # direct test: OLS slope of growth on time, HAC-free t (iid growth noise by construction)
            z = np.diff(np.log(ys))
            X = np.column_stack([np.ones(n), t[1:] - tc])
            b, *_ = np.linalg.lstsq(X, z, rcond=None)
            e = z - X @ b
            se = np.sqrt(e @ e / (n - 2) / ((t[1:] - tc) ** 2).sum())
            slope_sig += (b[1] / se) < -1.645
        out[name] = {"bic": {k: v / reps for k, v in bic_w.items()},
                     "prequential": {k: v / reps for k, v in pre_w.items()},
                     "share_slope_significantly_negative": slope_sig / reps}
        print(name, out[name])
    with open(RG.OUT / "power_calibrated.json", "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
