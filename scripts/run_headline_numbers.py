"""Headline numbers quoted in README.md and findings_register.md that are not produced by another script.

A5/A6  era growth (cut-offs 1929/2007 chosen after looking at the data; illustration only) with HAC t-statistics
A7     US catch-up to the leader before 1900
D2     Model A (constant average growth + noise) forecast and 90% ranges for 10- and 25-year average growth
D3     recent growth, 2007-2022
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from frontier import config as C  # noqa: E402
from frontier import growthshape as GS  # noqa: E402

OUT = C.ROOT / "output" / "headline"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    f = pd.read_csv(C.ROOT / "data" / "processed" / "frontier_levels.csv").set_index("year")
    R = {"era_growth_hac": {}, "model_A_forecast": {}, "recent_growth": {}}
    for c in ("us", "max", "top5"):
        z = (100 * np.log(f[c]).diff()).loc[1871:2022].dropna()
        X = pd.DataFrame({"const": 1.0, "e2": ((z.index >= 1930) & (z.index <= 2007)).astype(float),
                          "e3": (z.index >= 2008).astype(float)}, index=z.index)
        out = {"mean_1871_1929": float(z.loc[:1929].mean()), "mean_1930_2007": float(z.loc[1930:2007].mean()),
               "mean_2008_2022": float(z.loc[2008:].mean())}
        for L in (5, 10):
            r = sm.OLS(z, X).fit(cov_type="HAC", cov_kwds={"maxlags": L})
            t = r.t_test("e3 - e2 = 0")
            out[f"hac{L}_t_rise"] = float(r.params["e2"] / r.bse["e2"])
            out[f"hac{L}_t_fall"] = float(t.tvalue[0][0])
        R["era_growth_hac"][c] = out
        s = f[c].dropna().loc[1870:2022]
        e = GS.fit("EXP", s.values, s.index.values)
        fc = {"g_percent": 100 * e["g"], "annual_sd_percent": 100 * e["s"]}
        for h in (10, 25):
            half = 1.645 * e["s"] / np.sqrt(h)
            fc[f"range90_avg_growth_{h}y"] = [100 * (e["g"] - half), 100 * (e["g"] + half)]
        R["model_A_forecast"][c] = fc
        R["recent_growth"][c] = {"2007_2022": float(100 * np.log(s.loc[2022] / s.loc[2007]) / 15)}
    ratio = f.us / f["max"]
    lead = f.leader
    R["us_catch_up"] = {"us_over_leader_1870": float(ratio.loc[1870]), "first_year_us_leader_from_1899": 1899,
                        "leader_switches": {int(y): v for y, v in lead[lead != lead.shift()].items()},
                        "us_growth_1870_1899": float(100 * np.log(f.us.loc[1899] / f.us.loc[1870]) / 29),
                        "frontier_max_growth_1870_1899": float(100 * np.log(f["max"].loc[1899] / f["max"].loc[1870]) / 29),
                        "frontier_top5_growth_1870_1899": float(100 * np.log(f.top5.loc[1899] / f.top5.loc[1870]) / 29)}
    with open(OUT / "results.json", "w") as fh:
        json.dump(R, fh, indent=1)
    print(json.dumps(R, indent=1)[:3000])


if __name__ == "__main__":
    main()
