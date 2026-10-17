"""Is world research, rather than US research, the engine of the frontier?

Exploration (not a pre-registered project). Questions:
  1. Did world research effort grow more steadily than US research effort?
  2. If so, is that because national swings offset each other across countries (diversification)?
  3. Does frontier TFP follow world research more closely than US research, with a more stable beta?

Measures of research effort:
  - Long run (1870-2010): population with completed tertiary education (Lee-Lee 2016, 111 countries),
    a proxy for potential research labour (Jones 2002 uses researchers; these are not researchers).
    Groups: US, 22 other rich economies (BCL sample), the rest of the world; plus a quality-weighted
    world in which each country's graduates count by its GDP per capita relative to the US (capped at 1).
  - US check on the proxy: census engineers and chemists 1890-1950 (Blank and Stigler 1957, Table B-1).
  - Short run (1981-2022): OECD MSTI researchers (FTE) and real GERD, 47 reporting economies, chain-linked.
Frontier productivity: Bergeaud-Cette-Lecat TFP, US and top-5 (paper 1, data/processed/frontier_growth.csv).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier import balancing as B  # noqa: E402
from frontier import config as C  # noqa: E402
from frontier import lowfreq, plots  # noqa: E402
import run_research_effort as RE  # noqa: E402

OUT = C.ROOT / "output" / "world_research"
FIG = OUT / "figures"
RICH = ["AUS", "AUT", "BEL", "CAN", "CHE", "CHL", "DEU", "DNK", "ESP", "FIN", "FRA", "GBR", "GRC", "IRL", "ITA",
        "JPN", "MEX", "NLD", "NOR", "NZL", "PRT", "SWE", "USA"]

# Blank and Stigler (1957), Appendix B, Table B-1: engineers and chemists incl. surveyors, and the labour force.
# 1890-1930 gainful workers 10+ (lines 1-5); 1930-1940 labour force 14+ (lines 6-7); 1940-1950 civilian labour force
# (lines 8-9). Growth is computed within each consistent definition and chained.
BS_SEGMENTS = [  # (year0, year1, engineers_and_chemists_0, _1, labour_force_0, _1)
    (1890, 1900, 32742, 52086, 23318183, 29073233),
    (1900, 1910, 52086, 105028, 29073233, 37870794),
    (1910, 1920, 105028, 189062, 37870794, 42433535),
    (1920, 1930, 189062, 273317, 42433535, 48829920),
    (1930, 1940, 276941, 337877, 47404000, 53299000),
    (1940, 1950, 363000, 636400, 53299000, 59071655),
]


def tertiary_panel(var="lhc"):
    ll = pd.read_stata(C.RAW / "balancing" / "leelee2016" / "LeeLee_v1.dta")
    ll = ll[ll.sex == "MF"].copy()
    codes = pd.read_csv(C.RAW / "education" / "barrolee_v3" / "BL_v3_MF1564.csv")[["BLcode", "WBcode"]].drop_duplicates()
    ll = ll.merge(codes, on="BLcode", how="left")
    ll["iso"] = ll.WBcode.fillna(ll.country)
    ll["ter"] = ll[var] / 100 * ll["pop"]
    return ll[(ll.year >= 1870) & (ll.year <= 2010)][["iso", "year", "ter"]].dropna()


def quality_weights(isos):
    m = pd.read_stata(C.RAW / "maddison2023_web.dta")[["countrycode", "year", "gdppc"]]
    w = m.pivot_table(index="year", columns="countrycode", values="gdppc")
    rel = w.div(w["USA"], axis=0).clip(upper=1.0)
    rel = rel.reindex(range(1870, 2011)).interpolate(limit_direction="both")
    return rel.reindex(columns=isos)


def annual_log(s5):
    """Annual log level, linear between 5-year points."""
    s5 = s5[s5 > 0]
    a = np.log(s5).reindex(range(int(s5.index.min()), int(s5.index.max()) + 1)).interpolate()
    return a


def growth(a):
    return 100 * a.diff()


def lf_sd(x, q):
    return float(np.std(B.lf_dev(np.asarray(x, float), q)))


def lagged(y, x, lag, q):
    y, x = np.asarray(y, float), np.asarray(x, float)
    if lag:
        y, x = y[lag:], x[:-lag]
    r = lowfreq.regression(y, x[:, None], q, ["x"])
    return {"slope": r["coef"]["x"], "se": r["se"]["x"], "p": r["p"]["x"], "r2": r["r2"], "q": q, "n": len(y)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(2031)
    R = {"note": "Exploration; tertiary-educated population is a proxy for potential research labour, not researchers."}

    # ------------------------------------------------------------------ long-run pools (1870-2010)
    T = tertiary_panel()
    P5 = T.pivot_table(index="year", columns="iso", values="ter")
    isos = list(P5.columns)
    others = [c for c in isos if c not in RICH]
    rich_ex_us = [c for c in RICH if c != "USA" and c in isos]
    qw = quality_weights(isos)
    Pann = np.exp(P5.apply(lambda s: annual_log(s.dropna())))  # annual levels by country
    pools_lvl = {
        "us": Pann["USA"],
        "rich_ex_us": Pann[rich_ex_us].sum(1),
        "rest_of_world": Pann[others].sum(1),
        "rich23": Pann[[c for c in RICH if c in isos]].sum(1),
        "world": Pann.sum(1),
        "world_quality_weighted": (Pann * qw.reindex(Pann.index).fillna(0)).sum(1),
    }
    G = pd.DataFrame({k: growth(np.log(v)) for k, v in pools_lvl.items()}).loc[1871:2010]
    R["coverage"] = {"countries": len(isos), "rich_ex_us": len(rich_ex_us), "rest_of_world": len(others)}
    R["us_share_of_world_graduates"] = {str(y): float(pools_lvl["us"].loc[y] / pools_lvl["world"].loc[y])
                                         for y in (1870, 1900, 1930, 1950, 1970, 1990, 2010)}
    R["us_share_quality_weighted"] = {str(y): float(pools_lvl["us"].loc[y] / pools_lvl["world_quality_weighted"].loc[y])
                                      for y in (1870, 1900, 1930, 1950, 1970, 1990, 2010)}

    # Q1 steadiness
    q = int(round(2 * len(G) / 25))
    dec = {}
    for a in range(1870, 2010, 10):
        dec[f"{a}s"] = {k: float(G[k].loc[a + 1:a + 10].mean()) for k in G}
    R["decade_growth"] = dec
    R["steadiness"] = {k: {"mean": float(G[k].mean()), "sd_decade_means": float(np.std([dec[d][k] for d in dec])),
                           "lf_sd": lf_sd(G[k].values, q)} for k in G}
    R["steadiness_q"] = q

    # Q2 diversification: do national swings offset across country groups?
    lvl = pd.DataFrame({k: pools_lvl[k] for k in ("us", "rich_ex_us", "rest_of_world")})
    sh = lvl.div(lvl.sum(1), axis=0).shift(1)
    contrib = (sh * pd.DataFrame({k: G[k] for k in lvl.columns})).loc[1871:2010].dropna()
    Cm = contrib.values
    r_obs = B.ratio(Cm, q)
    null = B.null_distribution(Cm, q, 1000, rng, kind="phase")
    R["diversification_tertiary"] = {"ratio": r_obs, "null_median": float(np.median(null)),
                                     "p_offset": float(np.mean(null <= r_obs)),
                                     "lf_corr_us_vs_rich_ex_us": lowfreq.correlation(G.us.values, G.rich_ex_us.values, q),
                                     "lf_corr_us_vs_rest": lowfreq.correlation(G.us.values, G.rest_of_world.values, q)}

    # US check on the proxy: engineers and chemists vs tertiary graduates, by decade
    bs = []
    for y0, y1, e0, e1, l0, l1 in BS_SEGMENTS:
        bs.append({"decade": f"{y0}s", "eng_chem": float(100 * np.log(e1 / e0) / 10),
                   "eng_chem_per_worker": float(100 * (np.log(e1 / e0) - np.log(l1 / l0)) / 10),
                   "us_tertiary": float(G.us.loc[y0 + 1:y1].mean())})
    R["us_proxy_check_blank_stigler"] = bs
    R["us_proxy_check_corr"] = float(np.corrcoef([b["eng_chem"] for b in bs], [b["us_tertiary"] for b in bs])[0, 1])

    # Q3 engine: frontier TFP on lagged research growth, low frequency, 1891-2010
    fg = pd.read_csv(C.ROOT / "data" / "processed" / "frontier_growth.csv").set_index("year")
    eng = {}
    for outcome in ("tfp_us", "tfp_top5"):
        eng[outcome] = {}
        for pool in ("us", "rich23", "world", "world_quality_weighted", "rich_ex_us"):
            eng[outcome][pool] = {}
            for lag in (0, 5, 10, 15):
                x = G[pool].shift(lag).loc[1891:2010]
                y = fg[outcome].loc[1891:2010]
                ok = x.notna() & y.notna()
                eng[outcome][pool][f"lag{lag}"] = lagged(y[ok].values, x[ok].values, 0, int(round(2 * ok.sum() / 25)))
        # horse race: US vs the rest of the rich world, 10-year lag
        x1, x2 = G.us.shift(10).loc[1891:2010], G.rich_ex_us.shift(10).loc[1891:2010]
        y = fg[outcome].loc[1891:2010]
        ok = x1.notna() & x2.notna() & y.notna()
        qq = int(round(2 * ok.sum() / 25))
        r = lowfreq.regression(y[ok].values, np.column_stack([x1[ok], x2[ok]]), qq, ["us", "rich_ex_us"])
        eng[outcome]["horse_race_lag10"] = r
    R["engine_lowfreq"] = eng

    # implied beta by era: lagged (5y) research growth / TFP growth
    eras = [(1891, 1930), (1931, 1970), (1971, 2010)]
    beta = {}
    for outcome in ("tfp_us", "tfp_top5"):
        beta[outcome] = {}
        for pool in ("us", "rich23", "world", "world_quality_weighted"):
            vals = {}
            for a, b_ in eras:
                gs = G[pool].shift(5).loc[a:b_].mean()
                ga = fg[outcome].loc[a:b_].mean()
                vals[f"{a}-{b_}"] = {"g_S": float(gs), "g_A": float(ga), "beta": float(gs / ga)}
            bb = [v["beta"] for v in vals.values()]
            vals["cv_beta"] = float(np.std(bb) / np.mean(bb))
            beta[outcome][pool] = vals
    R["implied_beta_by_era"] = beta

    # ------------------------------------------------------------------ short run: OECD MSTI 1981-2022
    msti = RE.msti_panel()
    msti = msti[msti.iso.str.len() == 3]

    def chain(df, col):
        piv = df.pivot_table(index="year", columns="iso", values=col).sort_index()
        out = {}
        for t in range(1, len(piv)):
            a, b_ = piv.iloc[t - 1], piv.iloc[t]
            ok = a.notna() & b_.notna() & (a > 0)
            out[piv.index[t]] = 100 * np.log(b_[ok].sum() / a[ok].sum()) if ok.any() else np.nan
        return pd.Series(out)

    groups = {"world47": msti, "world_ex_china": msti[msti.iso != "CHN"],
              "rich_ex_us": msti[msti.iso.isin(rich_ex_us)], "us": msti[msti.iso == "USA"]}
    ms = {}
    for col in ("researchers", "gerd_real"):
        ms[col] = {}
        for gname, df in groups.items():
            s = chain(df, col).loc[1982:2022]
            five = [float(s.loc[a:a + 4].mean()) for a in range(1983, 2023, 5) if s.loc[a:a + 4].notna().sum() >= 3]
            ms[col][gname] = {"mean": float(s.mean()), "sd_annual": float(s.std()), "sd_5y_means": float(np.std(five)),
                              "by_decade": {f"{a}s": float(s.loc[max(a, 1982):a + 9].mean()) for a in (1980, 1990, 2000, 2010)}}
    R["msti_1982_2022"] = ms
    # proxy check across countries: researcher growth vs graduate growth, 1991-2010
    rows = []
    for iso, m in msti.groupby("iso"):
        m = m.set_index("year").researchers.dropna()
        if iso not in P5.columns or m.empty or m.index.min() > 1995 or m.index.max() < 2010:
            continue
        m.index = m.index.astype(int)
        y0 = int(m.index[m.index >= 1991].min())
        if 2010 not in m.index or y0 > 2000:
            continue
        g_res = 100 * np.log(m.loc[2010] / m.loc[y0]) / (2010 - y0)
        a = annual_log(P5[iso].dropna())
        g_ter = float(100 * (a.loc[2010] - a.loc[y0]) / (2010 - y0))
        rows.append((iso, g_res, g_ter))
    cc = pd.DataFrame(rows, columns=["iso", "g_researchers", "g_tertiary"])
    R["cross_country_proxy_check"] = {"n": len(cc), "corr": float(cc.g_researchers.corr(cc.g_tertiary)),
                                      "mean_researchers": float(cc.g_researchers.mean()),
                                      "mean_tertiary": float(cc.g_tertiary.mean())}

    with open(OUT / "results.json", "w") as f:
        json.dump(R, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    figures(R, G, fg)
    print("done: output/world_research/results.json")


def figures(R, G, fg):
    P = plots
    src = "Sources: Lee & Lee (2016) tertiary attainment, 111 countries; Maddison 2023; Bergeaud–Cette–Lecat TFP; Blank & Stigler (1957)."
    # W1: decade growth of graduates, US vs rest of rich world vs quality-weighted world, with frontier TFP growth
    D = R["decade_growth"]
    decs = list(D)
    fig, ax = P.setup(figsize=(10.5, 5.2))
    x = np.arange(len(decs))
    ax.plot(x, [D[d]["us"] for d in decs], color=P.BLUE, lw=2.2, marker="o", label="US graduates")
    ax.plot(x, [D[d]["rich_ex_us"] for d in decs], color="#8db8ea", lw=2, marker="o", label="22 other rich economies")
    ax.plot(x, [D[d]["world_quality_weighted"] for d in decs], color=P.DARK, lw=1.6, ls=(0, (4, 3)), marker="s",
            label="World, quality-weighted (111 countries)")
    tf = [float(fg.tfp_top5.loc[int(d[:4]) + 1:int(d[:4]) + 10].mean()) if int(d[:4]) >= 1890 else np.nan for d in decs]
    ax.bar(x, tf, 0.45, color=P.RED, alpha=0.55, label="Frontier TFP growth (top 5)")
    ax.axhline(0, color="#999999", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(decs, fontsize=8.5)
    ax.set_ylabel("% per year (decade average)", color="#555555")
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    P.titles(fig, "Outside the US, graduates grew about twice as steadily, but frontier TFP did not follow",
             "Growth of the population with completed tertiary education, by decade, 1870s–2000s", src)
    P.save(fig, FIG / "w1_graduates_by_decade.png")

    # W2: implied beta by era, per pool
    Bt = R["implied_beta_by_era"]["tfp_top5"]
    eras = ["1891-1930", "1931-1970", "1971-2010"]
    pools = [("us", "US graduates", P.BLUE), ("rich23", "23 rich economies", "#8db8ea"),
             ("world", "World (111)", P.GREY), ("world_quality_weighted", "World, quality-weighted", P.DARK)]
    fig, ax = P.setup(figsize=(10, 4.8))
    xx = np.arange(len(eras))
    for j, (k, lab, col) in enumerate(pools):
        ax.bar(xx + (j - 1.5) * 0.2, [Bt[k][e]["beta"] for e in eras], 0.2, color=col, label=f"{lab} (CV {Bt[k]['cv_beta']:.2f})")
    ax.set_xticks(xx)
    ax.set_xticklabels(eras)
    ax.set_ylabel("β = graduate growth (5 yrs earlier) ÷ frontier TFP growth", color="#555555", fontsize=9)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    P.titles(fig, "No research pool gives a stable β: ~7 before 1930, ~2.3 in 1931–70, 3–5 after",
             "Implied diminishing returns by era, frontier (top-5) TFP; a stable β would mean equal bars", src)
    P.save(fig, FIG / "w2_beta_by_era.png")


if __name__ == "__main__":
    main()
