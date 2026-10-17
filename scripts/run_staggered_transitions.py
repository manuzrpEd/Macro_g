"""Do productivity humps follow research build-ups across countries? (pre-registered: litreview_staggered_transitions.md)

T1  timing: cross-country regression of the TFP-hump year on the research-peak year and the 1890 gap to the frontier
T1b dispersion of hump years
T2  panel, 10-year blocks 1891-2010: TFP growth on lagged graduate growth, log graduate intensity, log gap; FE
T3  panel, 5-year blocks 1965-2009: TFP growth on lagged R&D-effort growth, log R&D intensity, log gap; FE
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from frontier import balancing as B  # noqa: E402
from frontier import config as C  # noqa: E402
from frontier import data, plots  # noqa: E402
from frontier import identification as ID  # noqa: E402

OUT = C.ROOT / "output" / "staggered_transitions"
FIG = OUT / "figures"
COUNTRIES = ["AUS", "AUT", "BEL", "CAN", "CHE", "CHL", "DEU", "DNK", "ESP", "FIN", "FRA", "GBR", "GRC", "IRL", "ITA",
             "JPN", "MEX", "NLD", "NOR", "NZL", "PRT", "SWE", "USA"]
NOT_RICH = ["CHL", "MEX", "GRC", "PRT", "ESP"]
MADSEN = {"AUD": "AUS", "AUT": "AUT", "BEL": "BEL", "CAN": "CAN", "DEN": "DNK", "FIN": "FIN", "FRA": "FRA", "GER": "DEU",
          "GRE": "GRC", "IRE": "IRL", "ITL": "ITA", "JAP": "JPN", "NET": "NLD", "NOR": "NOR", "NZ": "NZL", "POR": "PRT",
          "SPA": "ESP", "SWE": "SWE", "SWZ": "CHE", "UK": "GBR", "USA": "USA"}


# ----------------------------------------------------------------------------- data
def load():
    b = data.load_bcl()
    tfp = b[b.iso.isin(COUNTRIES)].pivot(index="year", columns="iso", values="tfp").sort_index()
    ll = pd.read_stata(C.RAW / "balancing" / "leelee2016" / "LeeLee_v1.dta")
    ll = ll[ll.sex == "MF"]
    codes = pd.read_csv(C.RAW / "education" / "barrolee_v3" / "BL_v3_MF1564.csv")[["BLcode", "WBcode"]].drop_duplicates()
    ll = ll.merge(codes, on="BLcode", how="left")
    ll = ll[ll.WBcode.isin(COUNTRIES) & (ll.year >= 1870) & (ll.year <= 2010)]
    grad5 = ll.assign(g=ll.lhc / 100 * ll["pop"]).pivot_table(index="year", columns="WBcode", values="g")
    share5 = ll.assign(s=ll.lhc / 100).pivot_table(index="year", columns="WBcode", values="s")
    yrs = range(1870, 2011)
    grad = np.exp(np.log(grad5).reindex(yrs).interpolate())
    share = np.exp(np.log(share5.clip(lower=1e-6)).reindex(yrs).interpolate())
    m = pd.read_stata(C.RAW / "maddison2023_web.dta")
    m = m[m.countrycode.isin(COUNTRIES)]
    gdppc = m.pivot(index="year", columns="countrycode", values="gdppc")
    pop = m.pivot(index="year", columns="countrycode", values="pop")
    md = pd.read_excel(C.RAW / "education" / "madsen_ang2016_restat" / "data.xlsx")
    md["iso"] = md.country.map(MADSEN)
    xq = md.pivot(index="year", columns="iso", values="xq")
    dtf = md.pivot(index="year", columns="iso", values="dtftfp")
    return tfp, grad, share, gdppc, pop, xq, dtf


def smooth(g, window, method="ma"):
    if method == "ma":
        return g.rolling(window, center=True, min_periods=int(0.7 * window)).mean()
    out = pd.Series(np.nan, index=g.index)
    x = g.dropna()
    q = int(round(2 * len(x) / 25))
    out.loc[x.index] = B.lf_dev(x.values, q) + x.mean()
    return out


def peaks(tfp, grad, window=21, method="ma"):
    rows = {}
    for c in COUNTRIES:
        if c not in tfp or c not in grad:
            continue
        gt = smooth(100 * np.log(tfp[c]).diff().loc[1891:2019], window, method)
        gr = smooth(100 * np.log(grad[c]).diff().loc[1871:2010], window, method)
        gt, gr = gt.loc[1901:2009].dropna(), gr.loc[1880:2000].dropna()
        if gt.empty or gr.empty:
            continue
        rows[c] = {"tfp_peak": int(gt.idxmax()), "tfp_peak_growth": float(gt.max()),
                   "research_peak": int(gr.idxmax()), "research_peak_growth": float(gr.max())}
    return pd.DataFrame(rows).T


def timing_reg(P, gap, sample=None):
    d = P.join(gap.rename("gap1890")).dropna()
    if sample is not None:
        d = d.loc[d.index.isin(sample)]
    X = sm.add_constant(d[["research_peak", "gap1890"]].astype(float))
    r = sm.OLS(d.tfp_peak.astype(float), X).fit(cov_type="HC1")
    b, p2 = r.params["research_peak"], r.pvalues["research_peak"]
    lag = (d.tfp_peak - d.research_peak).astype(float)
    return {"n": int(len(d)), "slope_research_peak": float(b), "se": float(r.bse["research_peak"]),
            "p_one_sided_positive": float(p2 / 2 if b > 0 else 1 - p2 / 2),
            "slope_gap1890": float(r.params["gap1890"]), "se_gap": float(r.bse["gap1890"]), "p_gap": float(r.pvalues["gap1890"]),
            "r2": float(r.rsquared), "median_lag": float(lag.median()), "share_lag_0_40": float(((lag >= 0) & (lag <= 40)).mean()),
            "sd_tfp_peak": float(d.tfp_peak.astype(float).std()), "sd_research_peak": float(d.research_peak.astype(float).std()),
            "corr_peaks": float(np.corrcoef(d.tfp_peak.astype(float), d.research_peak.astype(float))[0, 1])}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    R = {}
    tfp, grad, share, gdppc, pop, xq, dtf = load()
    gap = np.log(gdppc.loc[1890].max() / gdppc.loc[1890])
    gap_madsen = np.log(dtf.loc[1890]) if 1890 in dtf.index else None

    # --- T1 timing
    P = peaks(tfp, grad)
    R["T1_peaks"] = P.to_dict(orient="index")
    rich = [c for c in COUNTRIES if c not in NOT_RICH]
    R["T1_main"] = timing_reg(P, gap)
    R["T1_robust"] = {"window31": timing_reg(peaks(tfp, grad, 31), gap),
                      "lowfreq_trend": timing_reg(peaks(tfp, grad, method="lf"), gap),
                      "rich_only": timing_reg(P, gap, rich),
                      "madsen_gap": timing_reg(P, gap_madsen) if gap_madsen is not None else None,
                      "no_gap_control": None}
    d = P.astype(float)
    r0 = sm.OLS(d.tfp_peak, sm.add_constant(d[["research_peak"]])).fit(cov_type="HC1")
    R["T1_robust"]["no_gap_control"] = {"slope": float(r0.params["research_peak"]), "se": float(r0.bse["research_peak"]),
                                        "p_two_sided": float(r0.pvalues["research_peak"])}
    # exploratory (NOT pre-registered): is the slope a New-World vs war-hit-Europe/Japan split?
    war = ["AUT", "BEL", "DEU", "DNK", "FRA", "GRC", "ITA", "JPN", "NLD", "NOR"]  # occupied or defeated in WWII
    dd = P.astype(float).join(gap.rename("gap1890")).dropna()
    dd["war"] = dd.index.isin(war).astype(float)
    rw = sm.OLS(dd.tfp_peak, sm.add_constant(dd[["research_peak", "gap1890", "war"]])).fit(cov_type="HC1")
    lag = dd.tfp_peak - dd.research_peak
    R["T1_exploratory_war_control"] = {
        "slope_research_peak": float(rw.params["research_peak"]), "se": float(rw.bse["research_peak"]),
        "p_two_sided": float(rw.pvalues["research_peak"]), "war_coef": float(rw.params["war"]), "war_se": float(rw.bse["war"]),
        "within_war_corr": float(np.corrcoef(dd[dd.war == 1].research_peak, dd[dd.war == 1].tfp_peak)[0, 1]),
        "within_nonwar_corr": float(np.corrcoef(dd[dd.war == 0].research_peak, dd[dd.war == 0].tfp_peak)[0, 1]),
        "n_negative_lag": int((lag < 0).sum()), "n_lag_over_40": int((lag > 40).sum()), "n": int(len(dd))}
    b = R["T1_main"]
    R["T1_verdict"] = ("pass" if b["slope_research_peak"] > 0 and b["p_one_sided_positive"] < 0.10 and 0 <= b["median_lag"] <= 40
                       else "partial" if b["slope_research_peak"] > 0 else "fail")

    # --- T2 panel, 10-year blocks
    rows = []
    for c in COUNTRIES:
        if c not in tfp or c not in grad:
            continue
        lt, lg = np.log(tfp[c]), np.log(grad[c])
        for a in range(1891, 2002, 10):
            e = a + 9
            if a - 11 < 1870:
                continue
            rows.append({"iso": c, "period": a,
                         "g_tfp": 100 * (lt.get(e, np.nan) - lt.get(a - 1, np.nan)) / 10,
                         "g_grad_lag": 100 * (lg.get(a - 1, np.nan) - lg.get(a - 11, np.nan)) / 10,
                         "ln_share": float(np.log(share[c].get(a - 1, np.nan))),
                         "ln_gap": float(np.log(gdppc.loc[a - 1].max() / gdppc.loc[a - 1, c])) if a - 1 in gdppc.index else np.nan})
    Pn = pd.DataFrame(rows).dropna()
    rr = ID.panel_iv(Pn, "g_tfp", ["g_grad_lag"], ["g_grad_lag"], exog=["ln_share", "ln_gap"], fe=("iso", "period"))
    R["T2_panel_10y"] = {k: {v: float(rr[k][v]) for v in ("g_grad_lag", "ln_share", "ln_gap")} for k in ("coef", "se", "p")}
    R["T2_panel_10y"]["n"] = rr["n"]
    rr2 = ID.panel_iv(Pn, "g_tfp", ["g_grad_lag"], ["g_grad_lag"], exog=["ln_share", "ln_gap"], fe=("iso",))
    R["T2_panel_10y_country_fe_only"] = {k: {v: float(rr2[k][v]) for v in ("g_grad_lag", "ln_share", "ln_gap")} for k in ("coef", "se", "p")}
    # variance shares: period effects (common waves) vs country effects
    def r2_dummies(col):
        X = pd.get_dummies(Pn[col], drop_first=False).astype(float).values
        yv = Pn.g_tfp.values
        bb, *_ = np.linalg.lstsq(X, yv, rcond=None)
        return float(1 - ((yv - X @ bb) ** 2).sum() / ((yv - yv.mean()) ** 2).sum())
    R["T2_variance_shares"] = {"period_effects_r2": r2_dummies("period"), "country_effects_r2": r2_dummies("iso")}

    # --- T3 panel, 5-year blocks 1965-2009 with Madsen R&D (post-1963 only)
    rows = []
    for c in COUNTRIES:
        if c not in xq or c not in tfp:
            continue
        S = xq[c] * pop[c]
        for a in range(1970, 2006, 5):
            e = a + 4
            rows.append({"iso": c, "period": a,
                         "g_tfp": 100 * (np.log(tfp[c].get(e, np.nan)) - np.log(tfp[c].get(a - 1, np.nan))) / 5,
                         "g_S_lag": 100 * (np.log(S.get(a - 1, np.nan)) - np.log(S.get(a - 6, np.nan))) / 5,
                         "ln_xq": float(np.log(xq[c].get(a - 1, np.nan))),
                         "ln_gap": float(np.log(gdppc.loc[a - 1].max() / gdppc.loc[a - 1, c]))})
    P3 = pd.DataFrame(rows).replace([np.inf, -np.inf], np.nan).dropna()
    r3 = ID.panel_iv(P3, "g_tfp", ["g_S_lag"], ["g_S_lag"], exog=["ln_xq", "ln_gap"], fe=("iso", "period"))
    R["T3_panel_5y_RD"] = {k: {v: float(r3[k][v]) for v in ("g_S_lag", "ln_xq", "ln_gap")} for k in ("coef", "se", "p")}
    R["T3_panel_5y_RD"]["n"] = r3["n"]

    with open(OUT / "results.json", "w") as f:
        json.dump(R, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    figures(R, P, tfp, grad)
    print("done: output/staggered_transitions/results.json")


def figures(R, P, tfp, grad):
    Pl = plots
    src = "Sources: Bergeaud–Cette–Lecat TFP; Lee & Lee (2016) tertiary attainment; Maddison 2023."
    d = P.astype(float)
    fig, ax = Pl.setup(figsize=(9.5, 6))
    ax.scatter(d.research_peak, d.tfp_peak, color=Pl.BLUE, s=40, zorder=3)
    for c, r in d.iterrows():
        ax.annotate(c, (r.research_peak, r.tfp_peak), fontsize=8, xytext=(3, 3), textcoords="offset points", color="#333333")
    lo, hi = 1880, 2010
    for lag, ls in ((0, "-"), (20, (0, (4, 3))), (40, (0, (1, 2)))):
        ax.plot([lo, hi - lag], [lo + lag, hi], color="#999999", lw=0.9, ls=ls)
        ax.text(hi - lag - 5, hi - 2, f"lag {lag}", fontsize=7.5, color="#777777", ha="right")
    ax.set_xlim(lo, 2005)
    ax.set_ylim(1895, 2012)
    ax.set_xlabel("Year research build-up peaked (fastest growth of graduates, 21-yr average)", color="#555555")
    ax.set_ylabel("Year productivity growth peaked (21-yr average)", color="#555555")
    m = R["T1_main"]
    Pl.titles(fig, "Productivity humps bunch in 1942–63 whatever the timing of research build-ups", f"23 economies · slope {m['slope_research_peak']:.2f} (s.e. {m['se']:.2f}), controlling for the 1890 gap · "
              f"median lag {m['median_lag']:.0f} years", src)
    Pl.save(fig, FIG / "st1_timing.png")


if __name__ == "__main__":
    main()
