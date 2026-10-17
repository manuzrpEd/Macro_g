"""Project 1: why doesn't schooling show up in productivity over the long run?

Tests (TFP: Bergeaud-Cette-Lecat, 23 countries, 1891-2022; schooling: Lee & Lee 2016,
plus Barro-Lee, Penn World Table and Madsen data when available):
 T1  Low-frequency (periods >= ~25 yrs) slope of TFP growth on the growth of schooling, by country
     and pooled across countries, for several schooling measures.
 T2  Lags: schooling growth 10, 20 and 30 years earlier (cohorts enter the workforce slowly).
 T3  Level instead of growth (Nelson-Phelps / Benhabib-Spiegel): TFP growth on the schooling level,
     and on level x distance to the frontier.
 T4  Frequency ladder: panel regressions on 1-, 5-, 10- and 25-year averages, with country fixed
     effects, with and without period fixed effects (common global shocks).
 T5  Errors in variables: instrument one schooling measure with an independent one.

Outputs: output/education/results.json, output/education/figures/*.png
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from frontier import config as C  # noqa: E402
from frontier import data, lowfreq, plots  # noqa: E402
from frontier import identification as ID  # noqa: E402

OUT = C.ROOT / "output" / "education"
FIG = OUT / "figures"
ALPHA = 0.3
MINCER = 0.08  # return per year of schooling, for the years-of-schooling measure
Y0, Y1 = 1891, 2022
RAWE = C.RAW / "education"

LL_NAMES = {"Australia": "AUS", "Austria": "AUT", "Belgium": "BEL", "Canada": "CAN", "Switzerland": "CHE",
            "Chile": "CHL", "Germany": "DEU", "Denmark": "DNK", "Spain": "ESP", "Finland": "FIN", "France": "FRA",
            "United Kingdom": "GBR", "Greece": "GRC", "Ireland": "IRL", "Italy": "ITA", "Japan": "JPN",
            "Mexico": "MEX", "Netherlands": "NLD", "Norway": "NOR", "New Zealand": "NZL", "Portugal": "PRT",
            "Sweden": "SWE", "USA": "USA", "United States": "USA", "United States of America": "USA"}


# ----------------------------------------------------------------------------- data
def annualize(s):
    s = s.dropna().astype(float)
    s = s[~s.index.duplicated()].sort_index()
    full = s.reindex(range(int(s.index.min()), int(s.index.max()) + 1))
    return np.exp(np.log(full).interpolate())


def schooling_measures():
    """Dict measure -> DataFrame (year x iso) of LEVELS used to build the education contribution.

    hc / hca: Lee-Lee human capital indices (contribution = (1-a) dlog hc)
    tyr:      average years of schooling -> Mincer index exp(r * tyr)
    pwt_hc:   Penn World Table human capital index (1950+)
    + Barro-Lee and Madsen data if present in data/raw/education
    """
    ll = pd.read_stata(C.RAW / "balancing" / "leelee2016" / "LeeLee_v1.dta")
    ll = ll[ll.sex == "MF"].copy()
    ll["iso"] = ll.country.str.strip().map(LL_NAMES)
    ll = ll.dropna(subset=["iso"])
    out = {}
    for var, name in [("hc", "leelee_hc"), ("hca", "leelee_hca"), ("tyr", "leelee_tyr_mincer")]:
        cols = {}
        for iso, d in ll.groupby("iso"):
            s = d.set_index(d.year.astype(int))[var]
            if var == "tyr":
                s = np.exp(MINCER * s)
            if s.dropna().size > 3:
                cols[iso] = annualize(s)
        out[name] = pd.DataFrame(cols)
    p = pd.read_stata(C.RAW / "pwt110.dta")
    out["pwt_hc"] = p.pivot_table(index="year", columns="countrycode", values="hc")
    out.update(extra_measures())
    return out


DFD_NAMES = {"Australia": "AUS", "Austria": "AUT", "Belgium": "BEL", "Canada": "CAN", "Switzerland": "CHE",
             "Germany": "DEU", "Denmark": "DNK", "Spain": "ESP", "Finland": "FIN", "France": "FRA",
             "UK": "GBR", "United Kingdom": "GBR", "Greece": "GRC", "Ireland": "IRL", "Italy": "ITA", "Japan": "JPN",
             "Mexico": "MEX", "Netherlands": "NLD", "Norway": "NOR", "New Zealand": "NZL", "Portugal": "PRT",
             "Sweden": "SWE", "USA": "USA", "US": "USA", "United States": "USA", "Chile": "CHL"}


def _mincer_cols(df, iso_col, year_col, val_col):
    cols = {}
    for iso, d in df.groupby(iso_col):
        s = d.set_index(d[year_col].astype(int))[val_col].astype(float)
        s = s[s > 0]
        if s.size > 3:
            cols[iso] = annualize(np.exp(MINCER * s))
    return pd.DataFrame(cols)


def extra_measures():
    """Madsen (2014), Barro-Lee v3, Cohen-Soto-Leker and de la Fuente-Domenech years of schooling,
    converted to Mincer indices exp(r * years) and annualized log-linearly."""
    out = {}
    m = pd.read_csv(RAWE / "madsen2014_restat" / "madsen2014_panel5y_tidy.csv")
    m = m[~m.iso3.str.startswith("EXCLUDED")]
    out["madsen_years"] = _mincer_cols(m, "iso3", "year", "eato0")
    b = pd.read_csv(RAWE / "barrolee_v3" / "BL_v3_MF1564.csv")
    out["barrolee_years"] = _mincer_cols(b, "WBcode", "year", "yr_sch")
    c = pd.read_stata(RAWE / "cohen_soto_leker" / "csl-data-base.dta")
    c = c[(c.agefrom == 25) & (c.ageto == 64)]
    c = c.melt(id_vars=["code"], value_vars=[f"edu_{y}" for y in range(1960, 2020, 10)], var_name="y", value_name="yrs")
    c["year"] = c.y.str[4:].astype(int)
    out["cohensoto_years"] = _mincer_cols(c, "code", "year", "yrs")
    x = pd.read_excel(RAWE / "delafuente_domenech" / "dt2014-14_datos_HCta_OECD.xls", sheet_name="years of schooling", header=None)
    hdr_row = x.index[x.apply(lambda r: r.astype(str).str.strip().eq("country").any(), axis=1)][0]
    hdr = x.loc[hdr_row].tolist()
    body = x.loc[hdr_row + 1:].copy()
    body.columns = hdr
    cc = [h for h in hdr if isinstance(h, (int, float)) and not pd.isna(h) and 1950 <= h <= 2020]
    body = body.dropna(subset=["country"])
    body["iso"] = body.country.astype(str).str.strip().map(DFD_NAMES)
    body = body.dropna(subset=["iso"]).melt(id_vars=["iso"], value_vars=cc, var_name="year", value_name="yrs")
    body["yrs"] = pd.to_numeric(body.yrs, errors="coerce")
    out["delafuente_years"] = _mincer_cols(body.dropna(), "iso", "year", "yrs")
    return out


def madsen_tfp_growth():
    m = pd.read_csv(RAWE / "madsen2014_restat" / "madsen2014_panel5y_tidy.csv")
    m = m[~m.iso3.str.startswith("EXCLUDED")]
    cols = {iso: annualize(d.set_index(d.year.astype(int))["tfpn"]) for iso, d in m.groupby("iso3")}
    return 100 * np.log(pd.DataFrame(cols)).diff()


def tfp_growth():
    b = data.load_bcl()
    b = b[~b.iso.isin(["ZE"]) & ~b.iso.str.startswith("Unnamed")]
    w = b.pivot(index="year", columns="iso", values="tfp").loc[1890:Y1]
    g = 100 * np.log(w).diff()
    lvl = b.pivot(index="year", columns="iso", values="gdppc_bcl").loc[1890:Y1]
    gap = np.log(lvl["USA"]).values[:, None] - np.log(lvl)
    return g, gap


def edu_contrib(levels):
    return 100 * (1 - ALPHA) * np.log(levels).diff()


# ----------------------------------------------------------------------------- tests
def lf_country_slopes(g, e, q_per_year=1 / 12.5, lag=0):
    out = {}
    for iso in g.columns:
        if iso not in e.columns:
            continue
        df = pd.DataFrame({"g": g[iso], "e": e[iso].shift(lag)}).dropna()
        if len(df) < 55:
            continue
        q = int(round(len(df) * q_per_year))
        Ly, Lx = lowfreq.project(df.g.values, q), lowfreq.project(df.e.values, q)
        out[iso] = {"slope": float(Ly @ Lx / (Lx @ Lx)), "years": [int(df.index[0]), int(df.index[-1])], "q": q,
                    "Ly": Ly.tolist(), "Lx": Lx.tolist()}
    return out


def pooled_lf(slopes):
    """Pooled low-frequency regression: stack each country's cosine coefficients (no constant),
    one common slope, standard error clustered by country."""
    Y = np.concatenate([np.array(v["Ly"]) for v in slopes.values()])
    X = np.concatenate([np.array(v["Lx"]) for v in slopes.values()])
    cl = np.concatenate([[k] * len(v["Ly"]) for k, v in slopes.items()])
    b = float(X @ Y / (X @ X))
    e = Y - b * X
    meat = sum((X[cl == c] @ e[cl == c]) ** 2 for c in np.unique(cl))
    G = len(np.unique(cl))
    se = float(np.sqrt(meat) / (X @ X) * np.sqrt(G / (G - 1)))
    from scipy import stats
    return {"slope": b, "se": se, "p": float(2 * stats.t.sf(abs(b / se), G - 1)), "countries": G,
            "median_country_slope": float(np.median([v["slope"] for v in slopes.values()])),
            "share_negative": float(np.mean([v["slope"] < 0 for v in slopes.values()]))}


def level_spec(g, levels, gap, q_per_year=1 / 12.5):
    """Pooled LF regression of TFP growth on the (country-demeaned) log schooling level, and level x gap."""
    Ys, X1s, X2s, cls = [], [], [], []
    for iso in g.columns:
        if iso not in levels.columns:
            continue
        df = pd.DataFrame({"g": g[iso], "lv": np.log(levels[iso]), "gap": gap[iso]}).dropna()
        if len(df) < 60:
            continue
        q = int(round(len(df) * q_per_year))
        Ys.append(lowfreq.project(df.g.values, q))
        X1s.append(lowfreq.project(df.lv.values - df.lv.mean(), q))
        X2s.append(lowfreq.project((df.lv.values - df.lv.mean()) * df.gap.values, q))
        cls += [iso] * q
    Y, X = np.concatenate(Ys), np.column_stack([np.concatenate(X1s), np.concatenate(X2s)])
    b, *_ = np.linalg.lstsq(X, Y, rcond=None)
    e = Y - X @ b
    cl = np.array(cls)
    XtXi = np.linalg.inv(X.T @ X)
    meat = sum(np.outer(X[cl == c].T @ e[cl == c], X[cl == c].T @ e[cl == c]) for c in np.unique(cl))
    V = XtXi @ meat @ XtXi
    se = np.sqrt(np.diag(V))
    return {"level": float(b[0]), "level_se": float(se[0]), "level_x_gap": float(b[1]), "level_x_gap_se": float(se[1]),
            "countries": int(len(np.unique(cl)))}


def frequency_ladder(g, e, years=(1891, 2010)):
    """TFP growth on schooling-growth contribution, averaged over non-overlapping blocks of k years."""
    out = {}
    for k in (1, 5, 10, 25):
        rows = []
        for iso in g.columns:
            if iso not in e.columns:
                continue
            df = pd.DataFrame({"g": g[iso], "e": e[iso]}).loc[years[0]:years[1]].dropna()
            df["blk"] = (df.index - years[0]) // k
            a = df.groupby("blk").mean()
            a = a[df.groupby("blk").size() == k]
            a["iso"] = iso
            a["period"] = a.index
            rows.append(a)
        d = pd.concat(rows)
        res = {}
        for fe_name, fe in [("country_fe", ("iso",)), ("country_and_period_fe", ("iso", "period"))]:
            r = ID.panel_iv(d, "g", ["e"], ["e"], fe=fe)  # instrument = itself -> OLS with clustered SE
            res[fe_name] = {"slope": r["coef"]["e"], "se": r["se"]["e"], "p": r["p"]["e"], "n": r["n"]}
        out[f"{k}y"] = res
    return out


def eiv(g, e_a, e_b, k=5, years=(1951, 2010)):
    """Errors in variables: instrument measure A's schooling growth with measure B's (5-year panel, FE)."""
    rows = []
    for iso in g.columns:
        if iso not in e_a.columns or iso not in e_b.columns:
            continue
        df = pd.DataFrame({"g": g[iso], "ea": e_a[iso], "eb": e_b[iso]}).loc[years[0]:years[1]].dropna()
        if len(df) < 2 * k:
            continue
        df["blk"] = (df.index - years[0]) // k
        a = df.groupby("blk").mean()
        a["iso"], a["period"] = iso, a.index
        rows.append(a)
    d = pd.concat(rows)
    out = {}
    for fe_name, fe in [("country_fe", ("iso",)), ("country_and_period_fe", ("iso", "period"))]:
        r = ID.panel_iv(d, "g", ["ea"], ["eb"], fe=fe)
        out[fe_name] = {"iv_slope": r["coef"]["ea"], "iv_se": r["se"]["ea"], "first_stage_F": r["first_stage_F"]["ea"],
                        "ols_slope": r["ols_coef"]["ea"], "ols_se": r["ols_se"]["ea"], "n": r["n"]}
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    g, gap = tfp_growth()
    meas = schooling_measures()
    R = {"settings": {"alpha": ALPHA, "mincer": MINCER, "years": [Y0, Y1]}, "measures": list(meas)}
    E = {m: edu_contrib(lv) for m, lv in meas.items()}
    R["T1_lowfreq"] = {}
    R["T2_lags"] = {}
    for m, e in E.items():
        sl = lf_country_slopes(g, e)
        if len(sl) < 5:
            continue
        R["T1_lowfreq"][m] = {"pooled": pooled_lf(sl), "by_country": {k: {kk: v[kk] for kk in ("slope", "years", "q")}
                                                                      for k, v in sl.items()}}
        R["T2_lags"][m] = {}
        for lag in (10, 20, 30):
            sl2 = lf_country_slopes(g, e, lag=lag)
            if len(sl2) >= 5:
                R["T2_lags"][m][lag] = pooled_lf(sl2)
    R["T3_level"] = {m: level_spec(g, meas[m], gap) for m in ("leelee_hc", "leelee_tyr_mincer", "madsen_years")}
    R["T4_frequency_ladder"] = {m: frequency_ladder(g, E[m]) for m in ("leelee_hc", "leelee_tyr_mincer", "madsen_years")}
    long_pairs = [("leelee_tyr_mincer", "madsen_years"), ("madsen_years", "leelee_tyr_mincer")]
    post_pairs = [("leelee_tyr_mincer", "barrolee_years"), ("barrolee_years", "cohensoto_years"),
                  ("leelee_tyr_mincer", "delafuente_years"), ("barrolee_years", "delafuente_years"),
                  ("leelee_hc", "pwt_hc")]
    R["T5_eiv"] = {}
    for a, b in long_pairs:
        R["T5_eiv"][f"{a}__by__{b}"] = {"years": [1891, 2009], **eiv(g, E[a], E[b], k=5, years=(1891, 2009))}
        R["T5_eiv"][f"{a}__by__{b}__25y"] = {"years": [1891, 2009], **eiv(g, E[a], E[b], k=25, years=(1891, 2009))}
    for a, b in post_pairs:
        R["T5_eiv"][f"{a}__by__{b}"] = {"years": [1951, 2010], **eiv(g, E[a], E[b], k=5, years=(1951, 2010))}
    # long-run reliability of schooling changes across datasets (Madsen vs Lee-Lee)
    rel = {}
    for k in (5, 25, 50):
        xs, ys = [], []
        for iso in E["madsen_years"].columns:
            if iso not in E["leelee_tyr_mincer"].columns:
                continue
            a = E["madsen_years"][iso].loc[1871:2009]
            b = E["leelee_tyr_mincer"][iso].loc[1871:2009]
            blk = (a.index - 1871) // k
            xs += list(a.groupby(blk).mean().values)
            ys += list(b.groupby(blk).mean().values)
        rel[f"{k}y"] = float(np.corrcoef(xs, ys)[0, 1])
    R["reliability_madsen_vs_leelee_changes"] = rel
    # T6: labour productivity (GDP per hour) instead of TFP, and Madsen's own TFP with Madsen's schooling
    b = data.load_bcl()
    b = b[~b.iso.isin(["ZE"]) & ~b.iso.str.startswith("Unnamed")]
    glp = 100 * np.log(b.pivot(index="year", columns="iso", values="gdp_per_hour").loc[1890:Y1]).diff()
    R["T6_alt_outcomes"] = {}
    for m in ("leelee_hc", "leelee_tyr_mincer", "madsen_years"):
        sl = lf_country_slopes(glp, E[m])
        R["T6_alt_outcomes"][f"gdp_per_hour__{m}"] = pooled_lf(sl)
    gm = madsen_tfp_growth()
    sl = lf_country_slopes(gm, E["madsen_years"])
    R["T6_alt_outcomes"]["madsen_tfp__madsen_years"] = pooled_lf(sl)
    R["T6_alt_outcomes"]["madsen_tfp__madsen_years_5y_panel"] = frequency_ladder(gm, E["madsen_years"], years=(1871, 2009))
    with open(OUT / "results.json", "w") as f:
        json.dump(R, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    figures(R)
    print("done: output/education/results.json")


def figures(R):
    P = plots
    src = "Sources: Bergeaud–Cette–Lecat v2.7 (TFP); Lee & Lee (2016); Madsen (2014); Barro–Lee v3; Penn World Table 11."
    names = {"leelee_hc": "Lee–Lee human capital index", "leelee_hca": "Lee–Lee alternative index",
             "leelee_tyr_mincer": "Lee–Lee years of schooling", "madsen_years": "Madsen (2014) years of schooling",
             "pwt_hc": "Penn World Table hc (1950+)", "barrolee_years": "Barro–Lee years (1950+)"}
    # E1 pooled low-frequency slope by dataset
    fig, ax = P.setup(figsize=(10, 5.2))
    items = [(names[m], R["T1_lowfreq"][m]["pooled"]) for m in names if m in R["T1_lowfreq"]]
    for k, (lab, p) in enumerate(items):
        col = P.RED if "Madsen" in lab else P.BLUE
        ax.errorbar(p["slope"], k, xerr=1.645 * p["se"], fmt="o", color=col, capsize=3)
        ax.text(p["slope"], k - 0.28, f"{p['slope']:.2f}", ha="center", fontsize=8, color="#444444")
    ax.axvline(0, color="#999999", lw=0.8)
    ax.axvline(1, color=P.DARK, lw=1, ls=(0, (4, 3)))
    ax.text(1.03, -0.45, "1 = schooling shows up\nas growth accounting assumes", fontsize=8, color="#555555", va="top")
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels([i[0] for i in items], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Pooled low-frequency slope of TFP growth on the schooling contribution (90% interval)", color="#555555")
    ax.grid(axis="x", color="#eeeeee")
    P.titles(fig, "No schooling dataset shows schooling in long-run TFP; Madsen's data show the opposite",
             "Within-country co-movement at periods ≥ ~25 years; slopes pooled across 21–23 rich countries, 1891–2022", src)
    P.save(fig, FIG / "e1_slopes_by_dataset.png")

    # E2 frequency ladder
    fig, ax = P.setup(figsize=(10, 5))
    ks = ["1y", "5y", "10y", "25y"]
    for j, (m, col) in enumerate([("leelee_hc", P.BLUE), ("madsen_years", P.RED)]):
        for fe, ls, mk in [("country_fe", "-", "o"), ("country_and_period_fe", (0, (4, 3)), "s")]:
            b = [R["T4_frequency_ladder"][m][k][fe]["slope"] for k in ks]
            ax.plot(np.arange(4) + (j - 0.5) * 0.1, b, color=col, ls=ls, marker=mk, ms=5,
                    label=f"{names[m]}, {'country effects' if fe == 'country_fe' else 'country + period effects'}")
    ax.axhline(0, color="#999999", lw=0.8)
    ax.axhline(1, color=P.DARK, lw=0.9, ls=(0, (2, 2)))
    ax.set_xticks(range(4))
    ax.set_xticklabels(["annual", "5-year", "10-year", "25-year"])
    ax.set_ylabel("Slope of TFP growth on schooling contribution", color="#555555")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    mp = R["T4_frequency_ladder"]["madsen_years"]["25y"]["country_and_period_fe"]
    P.titles(fig, "Only 25-year averages bring the slope near 1, and only imprecisely",
             f"Panel slopes on non-overlapping 1–25-year blocks · Madsen data, 25-year, period effects: "
             f"{mp['slope']:.2f} (s.e. {mp['se']:.2f}); short horizons are negative", src)
    P.save(fig, FIG / "e2_frequency_ladder.png")

    # E3 reliability of schooling changes across datasets
    fig, ax = P.setup(figsize=(8.5, 4.6))
    rel = R["reliability_madsen_vs_leelee_changes"]
    xs = list(rel)
    ax.bar(range(len(xs)), [rel[k] for k in xs], color=P.BLUE, width=0.55)
    for i, k in enumerate(xs):
        ax.text(i, rel[k] + 0.02, f"{rel[k]:.2f}", ha="center", fontsize=9)
    ax.set_xticks(range(len(xs)))
    ax.set_xticklabels(["5-year changes", "25-year changes", "50-year changes"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Correlation, Madsen vs Lee–Lee", color="#555555")
    P.titles(fig, "The two long-run datasets barely agree on how fast schooling grew",
             "Correlation of the schooling contribution averaged over blocks, 21 countries, 1871–2009 (levels agree at ~0.86)", src)
    P.save(fig, FIG / "e3_reliability.png")


if __name__ == "__main__":
    main()
