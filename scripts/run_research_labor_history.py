"""Research labour before R&D statistics (IPUMS USA, 1850-2024).

Pre-registered design: litreview_research_labor_history.md.
  T1 decade growth and steadiness of research labour (S1 engineers+chemists; S2 + natural scientists + college
     faculty; S3 industrial research-type) and per worker
  T2 implied beta by era (research growth lagged one decade / TFP growth)
  T3 lag profile: research growth vs TFP growth 0-4 decades later
  T4 the same with frontier (top-5) TFP and GDP per capita
  T5 composition of engineers and chemists (industry, class of worker, college degree)
  T6 overlap with Project 3's R&D-based measures, 1940s-2010s
Data (never redistributed; data/raw/ipums is git-ignored): usa_00001 = Extract A (full count 1850-1950 + samples
1960-2024, S&E occupations); usa_00002 = Extract B (1% samples, labour force). Levels from Extract B (validated
against Blank and Stigler 1957 within +-7%); composition from Extract A for 1850-1950. Only aggregates are written.
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from frontier import config as C  # noqa: E402
from frontier import data, plots  # noqa: E402

OUT = C.ROOT / "output" / "research_labor_history"
FIG = OUT / "figures"
RAW = C.RAW / "ipums"
COLS = ["YEAR", "PERWT", "OCC1950", "IND1950", "CLASSWKR", "EDUC", "LABFORCE"]
BS = {1890: 32742, 1900: 52086, 1910: 105028, 1920: 189062, 1930: 276941, 1940: 337877, 1950: 636400}  # incl. surveyors


def categories(d):
    o, ind = d.OCC1950, d.IND1950
    eng_chem = (o == 7) | o.between(41, 49)
    natsci = o.between(61, 69)
    faculty = o.between(10, 29)
    research_ind = ind.between(306, 499) | ind.between(578, 579) | ind.between(586, 598)  # mfg, communications, utilities
    return d.assign(S1=eng_chem, natsci=natsci, faculty=faculty, surv=(o == 92),
                    S3=(eng_chem & research_ind) | natsci,
                    college=d.EDUC >= 10, wage=d.CLASSWKR == 2, research_ind=research_ind)


def read(f):
    return pd.concat(categories(c) for c in pd.read_csv(RAW / f, usecols=COLS, chunksize=3_000_000))


def levels(d):
    w = d.PERWT
    g = d.assign(**{k: d[k] * w for k in ("S1", "natsci", "faculty", "S3", "surv")}).groupby("YEAR")
    L = g[["S1", "natsci", "faculty", "S3", "surv"]].sum()
    L["lf"] = g.PERWT.sum()
    # 1940: no natural scientists coded in OCC1950 -> geometric interpolation 1930-1950
    if 1940 in L.index and L.loc[1940, "natsci"] == 0:
        L.loc[1940, "natsci"] = np.sqrt(L.loc[1930, "natsci"] * L.loc[1950, "natsci"])
        L.loc[1940, "S3"] = L.loc[1940, "S3"] + L.loc[1940, "natsci"]
    L["S2"] = L.S1 + L.natsci + L.faculty
    L.loc[L.index < 1910, "S3"] = np.nan  # industry not asked before 1910 (IPUMS imputes it from occupation)
    return L


def composition(d):
    s = d[d.S1]
    g = s.groupby("YEAR")
    tot = g.PERWT.sum()
    out = pd.DataFrame({
        "share_research_industries": (s.PERWT * s.research_ind).groupby(s.YEAR).sum() / tot,
        "share_wage_workers": (s.PERWT * s.wage).groupby(s.YEAR).sum() / tot,
        "share_college": (s.PERWT * s.college).groupby(s.YEAR).sum()
        / s[(s.EDUC > 0) & (s.EDUC < 99)].groupby("YEAR").PERWT.sum()})  # 1950: education asked of sample line only
    out.loc[out.index < 1910, "share_research_industries"] = np.nan  # industry imputed from occupation before 1910
    out.loc[out.index < 1940, "share_college"] = np.nan  # education first asked in 1940
    out.loc[out.index < 1910, "share_wage_workers"] = np.nan  # CLASSWKR not available
    return out


def interval_growth(s):
    """Annualized log growth (%) between consecutive census years, indexed by the interval start."""
    s = s.dropna()
    y = s.index.values
    return pd.Series(100 * np.diff(np.log(s.values)) / np.diff(y), index=pd.Index(y[:-1], name="start")), \
        dict(zip(y[:-1], y[1:]))


def decade_grid(gr, ends):
    """Map interval growth onto decades 1850s..2010s (an interval spanning several decades fills each)."""
    out = {}
    for a, g in gr.items():
        b = ends[a]
        for dec in range(1850, 2020, 10):
            if dec >= a and dec < b:
                out[dec] = g
    return pd.Series(out).sort_index()


def annual_decades(series, first=1850):
    """Decade-average annual log growth (%) from an annual level series."""
    g = 100 * np.log(series).diff()
    return pd.Series({d: g.loc[d + 1:d + 10].mean() for d in range(first, 2020, 10) if g.loc[d + 1:d + 10].notna().sum() >= 5})


def dynamic_fit(S_census, A_level, target_dec, lam_fixed=None):
    """Fit dlnA = theta * S^lam * A^-beta (S, A normalized to 1950 = 1) to decade TFP growth 1890s-2010s."""
    from scipy.optimize import minimize
    years = np.arange(1891, 2025)
    lnS = np.log(S_census.dropna())
    lnS = lnS.reindex(range(int(lnS.index.min()), int(lnS.index.max()) + 1)).interpolate().reindex(years).ffill()
    lnS = lnS - lnS.loc[1950]
    A = np.log(A_level.dropna())
    A = A - A.loc[1950]
    a0 = A.loc[1891]
    tgt = target_dec.loc[1890:2010].dropna()

    def sim(par):
        lth, lam, beta = par
        lnA = np.empty(len(years))
        lnA[0] = a0
        for t in range(1, len(years)):
            lnA[t] = lnA[t - 1] + np.exp(lth) * np.exp(lam * lnS.iloc[t - 1] - beta * lnA[t - 1])
        return pd.Series(lnA, index=years)

    def dec_growth(lnA):
        g = 100 * lnA.diff()
        return pd.Series({d: g.loc[d + 1:d + 10].mean() for d in tgt.index})

    def loss(par):
        if lam_fixed is not None:
            par = [par[0], lam_fixed, par[2]]
        if not (0.05 <= par[1] <= 1.5 and 0.0 <= par[2] <= 10):
            return 1e6
        return float(((dec_growth(sim(par)) - tgt) ** 2).sum())

    best = None
    for lam0 in (0.3, 0.7, 1.0):
        for b0 in (0.5, 2.0, 4.0):
            r = minimize(loss, [np.log(0.015), lam0, b0], method="Nelder-Mead", options={"maxiter": 4000, "xatol": 1e-5, "fatol": 1e-8})
            if best is None or r.fun < best.fun:
                best = r
    if lam_fixed is not None:
        best.x = np.array([best.x[0], lam_fixed, best.x[2]])
    fit = dec_growth(sim(best.x))
    sst = float(((tgt - tgt.mean()) ** 2).sum())
    # benchmark: research growth / beta with the same beta (steady-state formula) and a constant
    return {"theta": float(np.exp(best.x[0])), "lambda": float(best.x[1]), "beta": float(best.x[2]),
            "beta_over_lambda": float(best.x[2] / best.x[1]), "sse": float(best.fun),
            "r2_vs_constant": float(1 - best.fun / sst), "fitted_decades": fit.round(2).to_dict(),
            "target_decades": tgt.round(2).to_dict()}


def holdout(S_census, A_level, target_dec, fit_last_decade, lam=1.0):
    """Pre-registered hold-out test: fit theta, beta on decades <= fit_last_decade; forecast later decades from the
    actual TFP level at the split, with actual S. Returns forecasts and benchmark errors."""
    from scipy.optimize import minimize
    split = fit_last_decade + 10                       # last year of the fitting window (e.g. 1970)
    years = np.arange(1891, 2025)
    lnS = np.log(S_census.dropna())
    lnS = lnS.reindex(range(int(lnS.index.min()), int(lnS.index.max()) + 1)).interpolate().reindex(years).ffill()
    lnS = lnS - lnS.loc[1950]
    A = np.log(A_level.dropna())
    A = A - A.loc[1950]
    tgt = target_dec.loc[1890:2010].dropna()
    fit_dec = tgt.loc[:fit_last_decade]
    fc_dec = tgt.loc[fit_last_decade + 10:]

    def sim(par, y0, y1, a_start):
        lth, beta = par
        yy = np.arange(y0, y1 + 1)
        lnA = np.empty(len(yy))
        lnA[0] = a_start
        for t in range(1, len(yy)):
            lnA[t] = lnA[t - 1] + np.exp(lth) * np.exp(lam * lnS.loc[yy[t - 1]] - beta * lnA[t - 1])
        return pd.Series(lnA, index=yy)

    def dec_growth(lnA, decs):
        g = 100 * lnA.diff()
        return pd.Series({d: g.loc[d + 1:d + 10].mean() for d in decs})

    def loss(par):
        if not (0 <= par[1] <= 10):
            return 1e6
        return float(((dec_growth(sim(par, 1891, split, A.loc[1891]), fit_dec.index) - fit_dec) ** 2).sum())

    best = min((minimize(loss, [np.log(0.015), b0], method="Nelder-Mead", options={"maxiter": 3000})
                for b0 in (0.5, 1.5, 3.0, 5.0)), key=lambda r: r.fun)
    fc = dec_growth(sim(best.x, split, 2020, A.loc[split]), fc_dec.index)
    # benchmarks using only fitting-window information
    g_ann = 100 * A.diff()
    const = pd.Series(g_ann.loc[1892:split].mean(), index=fc_dec.index)
    last = pd.Series(g_ann.loc[split - 9:split].mean(), index=fc_dec.index)
    gS_dec = pd.Series({d: 100 * (lnS.loc[d] - lnS.loc[max(d - 10, 1891)]) / (d - max(d - 10, 1891))
                        for d in range(1900, 2021, 10)})
    beta_ss = lam * gS_dec.loc[1900:split].mean() / g_ann.loc[1892:split].mean()
    ss = pd.Series({d: lam * gS_dec.loc[d] / beta_ss for d in fc_dec.index})  # research growth in the decade before
    rmse = lambda f: float(np.sqrt(((f - fc_dec) ** 2).mean()))
    return {"theta": float(np.exp(best.x[0])), "beta": float(best.x[1]), "lambda": lam,
            "forecast": fc.round(2).to_dict(), "actual": fc_dec.round(2).to_dict(),
            "rmse_model": rmse(fc), "rmse_constant": rmse(const), "rmse_last_decade": rmse(last), "rmse_steady_state": rmse(ss),
            "mean_forecast": float(fc.mean()), "mean_actual": float(fc_dec.mean()),
            "mean_actual_prior_40y": float(g_ann.loc[split - 39:split].mean()), "mean_constant_benchmark": float(const.iloc[0])}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    R = {}
    B = read("usa_00002.csv.gz")
    A = read("usa_00001.csv.gz")
    L = levels(B)
    LA = levels(A)
    L["S1_per_1000_workers"] = 1000 * L.S1 / L.lf
    L["S2_per_1000_workers"] = 1000 * L.S2 / L.lf
    R["levels_1pct"] = L.round(0).to_dict()
    R["validation_vs_blank_stigler"] = {str(y): {"blank_stigler": v, "ipums_1pct": float(L.S1.get(y, np.nan) + L.surv.get(y, np.nan)),
                                                 "ipums_fullcount": float(LA.S1.get(y, np.nan) + LA.surv.get(y, np.nan))}
                                        for y, v in BS.items() if y in L.index}

    # --- T1: interval and decade growth, steadiness
    series = {"S1": L.S1, "S2": L.S2, "S3": L.S3, "S1_per_worker": L.S1 / L.lf, "S2_per_worker": L.S2 / L.lf, "labour_force": L.lf}
    G, ENDS, DEC = {}, None, {}
    for k, s in series.items():
        gr, ENDS = interval_growth(s)
        G[k] = gr
        DEC[k] = decade_grid(gr, ENDS)
    R["interval_growth"] = {k: {f"{a}-{ENDS[a]}": float(v) for a, v in g.items()} for k, g in G.items()}
    Dg = pd.DataFrame(DEC)
    # productivity: BCL US TFP, frontier top-5 TFP (paper 1), Maddison US GDP per capita
    b = data.load_bcl()
    us = b[b.iso == "USA"].set_index("year").sort_index()
    fg = pd.read_csv(C.ROOT / "data" / "processed" / "frontier_levels.csv").set_index("year")
    tfp_us = annual_decades(us.tfp)
    tfp_top5 = annual_decades(fg.tfp_top5.dropna()) if "tfp_top5" in fg else None
    gdppc = annual_decades(fg.us)
    Dg["tfp_us"], Dg["tfp_top5"], Dg["gdppc_us"] = tfp_us, tfp_top5, gdppc
    R["decade_growth"] = Dg.round(3).to_dict()
    st = {}
    for k in ("S1", "S2", "S3", "S1_per_worker"):
        x = G[k]
        pre, post = x[x.index < 1930], x[x.index >= 1930]
        st[k] = {"mean_pre1930": float(pre.mean()), "sd_pre1930": float(pre.std(ddof=0)),
                 "mean_post1930": float(post.mean()), "sd_post1930": float(post.std(ddof=0)),
                 "mean_1870_1930": float(x.loc[1870:1920].mean()), "mean_1930_1970": float(x.loc[1930:1960].mean()),
                 "mean_1970_2024": float(x.loc[1970:].mean())}
    R["T1_steadiness"] = st

    # --- T2: beta by era, research growth lagged one decade (and 0, 2 decades)
    eras = {"1890-1930": (1890, 1930), "1930-1970": (1930, 1970), "1970-2020": (1970, 2020)}
    def era_mean(s, a, b):
        return float(s.loc[a:b - 10].mean())
    beta = {}
    for out_name, out_s in (("tfp_us", tfp_us), ("tfp_top5", tfp_top5), ("gdppc_us", gdppc)):
        beta[out_name] = {}
        for k in ("S1", "S2", "S3"):
            beta[out_name][k] = {}
            for lag in (0, 1, 2):
                vals = {}
                for e, (a, b_) in eras.items():
                    gs = era_mean(Dg[k], a - 10 * lag, b_ - 10 * lag)
                    ga = era_mean(out_s, a, b_)
                    vals[e] = {"g_S": gs, "g_out": ga, "beta": gs / ga if ga else np.nan}
                bb = np.array([v["beta"] for v in vals.values()])
                vals["cv_beta"] = float(np.std(bb) / np.mean(bb))
                beta[out_name][k][f"lag{lag}_decades"] = vals
    R["T2_beta_by_era"] = beta

    # --- T3/T4: lag profile of correlations (decade grid)
    lagp = {}
    for out_name in ("tfp_us", "tfp_top5", "gdppc_us"):
        lagp[out_name] = {}
        for k in ("S1", "S2", "S1_per_worker"):
            prof = {}
            for lag in range(0, 5):
                x = Dg[k].shift(lag)  # research growth `lag` decades earlier
                ok = x.notna() & Dg[out_name].notna()
                if ok.sum() >= 5:
                    prof[lag] = {"corr": float(np.corrcoef(x[ok], Dg.loc[ok, out_name])[0, 1]), "n": int(ok.sum())}
            lagp[out_name][k] = prof
    R["T3_T4_lag_profile"] = lagp

    # --- T5 composition (full count to 1950, samples after)
    comp = pd.concat([composition(A).loc[:1950], composition(B).loc[1960:]])
    comp_b = composition(B)
    R["T5_composition_S1"] = {"main": comp.round(3).to_dict(), "from_1pct_samples": comp_b.round(3).to_dict()}

    # --- T6: overlap with Project 3 measures
    try:
        p3 = json.load(open(C.ROOT / "output" / "research_effort" / "results.json"))["measurement_bjvw_deflator"]
        rows = []
        for dec in range(1940, 2020, 10):
            key = f"{dec}s"
            rows.append({"decade": dec, "ipp_over_college_wage": p3["ipp_over_college_wage"].get(key),
                         "rd_over_gdppc": p3["rd_over_gdppc"].get(key), "S1": Dg.S1.get(dec), "S2": Dg.S2.get(dec),
                         "S3": Dg.S3.get(dec)})
        T6 = pd.DataFrame(rows).set_index("decade").astype(float)
        R["T6_overlap_project3"] = {"table": T6.round(2).to_dict(), "corr": T6.corr().round(2).to_dict()}
    except Exception as e:  # pragma: no cover
        R["T6_overlap_project3"] = {"error": str(e)}

    # robustness: growth 1850-1900 from the full count (larger N; coding bias roughly constant before 1900)
    gA, endsA = interval_growth(LA.S1.loc[:1950])
    R["robustness_fullcount_S1_growth"] = {f"{a}-{endsA[a]}": float(v) for a, v in gA.items()}

    # --- T7 (exploratory, NOT pre-registered): dynamic semi-endogenous model
    #     dlnA_t = theta * S_t^lam * A_t^(-beta), simulated annually from the 1891 TFP level, fitted to decade TFP growth
    R["T7_dynamic_model_exploratory"] = {}
    for out_name, lev in (("tfp_us", us.tfp), ("tfp_top5", fg.tfp_top5.dropna())):
        for k in ("S1", "S2"):
            R["T7_dynamic_model_exploratory"][f"{out_name}__{k}"] = dynamic_fit(L[k], lev, Dg[out_name])
            for lf_ in (1.0, 0.75):
                R["T7_dynamic_model_exploratory"][f"{out_name}__{k}__lambda{lf_}"] = dynamic_fit(L[k], lev, Dg[out_name], lam_fixed=lf_)
        # placebo: the same model driven by the labour force (population-type pool) instead of research labour
        R["T7_dynamic_model_exploratory"][f"{out_name}__placebo_labour_force"] = dynamic_fit(L.lf, lev, Dg[out_name])
        R["T7_dynamic_model_exploratory"][f"{out_name}__placebo_labour_force__lambda1.0"] = dynamic_fit(L.lf, lev, Dg[out_name], lam_fixed=1.0)

    # --- T8: pre-registered hold-out test (addendum in litreview_research_labor_history.md)
    T8 = {}
    for out_name, lev in (("tfp_us", us.tfp), ("tfp_top5", fg.tfp_top5.dropna())):
        for split_dec, lab in ((1960, "fit1891_1970"), (1940, "fit1891_1950")):
            for k in ("S1", "S2"):
                for lam in (1.0, 0.75):
                    T8[f"{out_name}__{lab}__{k}__lambda{lam}"] = holdout(L[k], lev, Dg[out_name], split_dec, lam)
            T8[f"{out_name}__{lab}__placebo_labour_force__lambda1.0"] = holdout(L.lf, lev, Dg[out_name], split_dec, 1.0)
    for key, v in T8.items():
        if "placebo" in key:
            continue
        pl = T8[key.split("__S")[0] + "__placebo_labour_force__lambda1.0"]
        v["rmse_placebo"] = pl["rmse_model"]
        v["pass_criteria"] = {"beats_constant": v["rmse_model"] < v["rmse_constant"],
                              "beats_placebo": v["rmse_model"] < pl["rmse_model"],
                              "predicts_slowdown": v["mean_forecast"] < v["mean_actual_prior_40y"]}
    R["T8_holdout_preregistered"] = T8

    with open(OUT / "results.json", "w") as f:
        json.dump(R, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    figures(R, Dg, G, ENDS)
    print("done: output/research_labor_history/results.json")


def figures(R, Dg, G, ENDS):
    P = plots
    src = "Sources: IPUMS USA (1% samples 1850–2024; full count for composition); Bergeaud–Cette–Lecat TFP; Blank & Stigler (1957)."
    # H1: interval growth of research labour vs TFP by decade
    fig, ax = P.setup(figsize=(11, 5.2))
    for k, col, lab in (("S1", P.BLUE, "Engineers + chemists"), ("S2", P.DARK, "+ scientists + college faculty"),
                        ("S1_per_worker", "#8db8ea", "Engineers + chemists per worker")):
        g = G[k]
        xs = [(a + ENDS[a]) / 2 for a in g.index]
        ax.plot(xs, g.values, marker="o", color=col, lw=2 if k == "S1" else 1.5, label=lab)
    t = Dg.tfp_us.dropna()
    ax.bar(t.index + 5, t.values, 7, color=P.RED, alpha=0.5, label="US TFP growth (decade average)")
    ax.axhline(0, color="#999999", lw=0.8)
    ax.set_ylabel("% per year", color="#555555")
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    P.titles(fig, "Research labour grew fastest before 1930, when productivity grew slowest", "Growth of US research labour between censuses, 1850–2024, and US TFP growth", src)
    P.save(fig, FIG / "h1_research_labour_growth.png")

    # H2: beta by era
    Bt = R["T2_beta_by_era"]["tfp_us"]
    eras = ["1890-1930", "1930-1970", "1970-2020"]
    fig, ax = P.setup(figsize=(10, 4.8))
    xx = np.arange(3)
    for j, (k, lag, col, lab) in enumerate((("S1", "lag0_decades", "#8db8ea", "Engineers + chemists, no lag"),
                                            ("S1", "lag1_decades", P.BLUE, "Engineers + chemists, 1-decade lag"),
                                            ("S1", "lag2_decades", P.DARK, "Engineers + chemists, 2-decade lag"),
                                            ("S2", "lag1_decades", P.GREY, "Broad (S2), 1-decade lag"))):
        v = Bt[k][lag]
        ax.bar(xx + (j - 1.5) * 0.2, [v[e]["beta"] for e in eras], 0.2, color=col, label=f"{lab} (CV {v['cv_beta']:.2f})")
    ax.axhline(3, color=P.DARK, lw=0.8, ls=(0, (2, 2)))
    ax.set_xticks(xx)
    ax.set_xticklabels(eras)
    ax.set_ylabel("β = research-labour growth ÷ US TFP growth", color="#555555")
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    P.titles(fig, "In steady-state arithmetic, β is ~6 before 1930 and ~2 after: no stable engine", "Implied diminishing returns by era; equal bars would mean a stable research engine", src)
    P.save(fig, FIG / "h2_beta_by_era.png")

    # H3: lag profile
    fig, ax = P.setup(figsize=(9, 4.6))
    for out_name, col, lab in (("tfp_us", P.BLUE, "US TFP"), ("tfp_top5", P.DARK, "Frontier TFP (top 5)"), ("gdppc_us", P.GREY, "US GDP per capita")):
        prof = R["T3_T4_lag_profile"][out_name]["S1"]
        ks = sorted(int(k) for k in prof)
        ax.plot(ks, [prof[k]["corr"] if k in prof else prof[str(k)]["corr"] for k in ks], marker="o", color=col, lw=2, label=lab)
    ax.axhline(0, color="#999999", lw=0.8)
    ax.set_xticks(range(5))
    ax.set_xlabel("Decades between research-labour growth and productivity growth", color="#555555")
    ax.set_ylabel("Correlation across decades", color="#555555")
    ax.legend(frameon=False, fontsize=9)
    P.titles(fig, "No simple lag (0–40 years) lines up research labour with productivity", "Correlation of engineer-and-chemist growth with later productivity growth", src)
    P.save(fig, FIG / "h3_lag_profile.png")

    # H4: dynamic semi-endogenous model vs data (exploratory)
    T7 = R["T7_dynamic_model_exploratory"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    for ax, out_name, lab in zip(axes, ("tfp_us", "tfp_top5"), ("US TFP", "Frontier TFP (top 5)")):
        P.style(ax) if hasattr(P, "style") else None
        m, pl = T7[f"{out_name}__S1__lambda1.0"], T7[f"{out_name}__placebo_labour_force__lambda1.0"]
        def v(dct, x):
            return dct[x] if x in dct else dct[str(x)]
        xs = sorted(int(k) for k in m["target_decades"])
        ax.bar(xs, [v(m["target_decades"], x) for x in xs], 7, color=P.RED, alpha=0.5, label="Actual (decade average)")
        ax.plot(xs, [v(m["fitted_decades"], x) for x in xs], color=P.BLUE, lw=2.4, marker="o",
                label=f"Model with engineers + chemists (R² {m['r2_vs_constant']:.2f}, β/λ {m['beta_over_lambda']:.1f})")
        ax.plot(xs, [v(pl["fitted_decades"], x) for x in xs], color=P.GREY, lw=1.6, ls=(0, (4, 3)),
                label=f"Placebo: model with total labour force (R² {pl['r2_vs_constant']:.2f})")
        ax.axhline(0, color="#999999", lw=0.8)
        ax.set_title(lab, fontsize=10, color="#333333", loc="left")
        ax.legend(frameon=False, fontsize=7.5, loc="upper right")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("% per year", color="#555555")
    P.titles(fig, "In sample, the semi-endogenous model with census research labour reproduces the slow–fast–slow path",
             "Exploratory (not pre-registered): TFP growth = θ·S(t) / A(t)ᵝ (λ = 1), fitted to decade TFP growth 1890s–2010s", src)
    P.save(fig, FIG / "h4_dynamic_model.png")


if __name__ == "__main__":
    main()
