"""The Balancing Leader: do the sources of growth offset each other at low frequency?

Two additive decompositions of GDP per capita growth (Bergeaud-Cette-Lecat, 1891-2022):

  per hour   g_y = g_tfp + g_kd + g_h          kd = alpha * dlog(K/H): capital per HOUR
  per person g_y = g_tfp + g_k  + g_l          k  = alpha * dlog(K/N), l = (1-alpha) * dlog(H/N)

In the per-hour split, capital per hour = K / H mechanically falls when hours rise
(capital moves slowly), so offsetting between kd and h is partly definitional. The
per-person split has no shared denominator between capital and hours and is the
main test; the per-hour split is reported to show the artifact.

Steps
 1  Variance-ratio test by country and pooled (leaders vs followers), against
    independence nulls (phase randomization, circular shifts).
 2  Division bias: measurement-error variance needed to produce the observed
    offsetting; post-1950 subsample; second source (Penn World Table 11).
 3  Channels: which covariance terms matter.
 4  Counterfactual paths with one component frozen.
 5  Inside TFP: education (Lee-Lee long-run human capital) vs the rest (if available).
 6  The 1914-49 episode and a direct semi-endogenous test at the leader
    (US TFP vs US research effort) with the data available.

Outputs: output/balancing/results.json, output/balancing/figures/*.png
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from frontier import balancing as B  # noqa: E402
from frontier import config as C  # noqa: E402
from frontier import data, lowfreq, plots  # noqa: E402

OUT = C.ROOT / "output" / "balancing"
FIG = OUT / "figures"
Y0, Y1 = 1891, 2022
Q = int(round(2 * (Y1 - Y0 + 1) / 25))  # keep periods of ~25 years and longer
REPS = 999
ALPHA = 0.3  # capital share used to split capital per hour into per-person terms
RAWB = C.RAW / "balancing"
DECOMPS = {"per_person": ("tfp", "k", "l"), "per_hour": ("tfp", "kd", "h")}


# ----------------------------------------------------------------------------- data
def bcl_parts(alpha=ALPHA):
    b = data.load_bcl()
    b = b[~b.iso.isin(["ZE"]) & ~b.iso.str.startswith("Unnamed")]
    out = {}
    for iso, d in b.groupby("iso"):
        d = d.set_index("year").sort_index()
        g = pd.DataFrame({
            "y": 100 * np.log(d.gdppc_bcl).diff(),
            "tfp": 100 * np.log(d.tfp).diff(),
            "lp": 100 * np.log(d.gdp_per_hour).diff(),
            "h": 100 * np.log(d.hours_pc).diff()})
        g["kd"] = g.lp - g.tfp                 # alpha * dlog(K/H)
        g["k"] = g.kd + alpha * g.h            # alpha * dlog(K/N)
        g["l"] = (1 - alpha) * g.h             # (1 - alpha) * dlog(H/N)
        out[iso] = g.loc[Y0:Y1].dropna()
    return out, b


def pwt_parts(isos, alpha=ALPHA):
    p = pd.read_stata(C.RAW / "pwt110.dta")
    out = {}
    for iso in isos:
        d = p[p.countrycode == iso].set_index("year").sort_index()
        d = d[["rgdpna", "pop", "emp", "avh", "rnna"]].dropna()
        if len(d) < 50:
            continue
        H = d.emp * d.avh
        g = pd.DataFrame({"y": 100 * np.log(d.rgdpna / d["pop"]).diff(),
                          "h": 100 * np.log(H / d["pop"]).diff(),
                          "kn": 100 * np.log(d.rnna / d["pop"]).diff()})
        g["k"] = alpha * g.kn
        g["l"] = (1 - alpha) * g.h
        g["tfp"] = g.y - g.k - g.l
        g["kd"] = alpha * (g.kn - g.h)
        out[iso] = g.dropna()
    return out


def M(g, names):
    return g[list(names)].values


def geo(x):
    return float(np.exp(np.mean(np.log(np.asarray(x, float)))))


# ----------------------------------------------------------------------------- analysis
def country_table(parts, names, rng, reps=REPS):
    rows, nulls = {}, {}
    for iso, g in parts.items():
        Cm = M(g, names)
        r = B.ratio(Cm, Q)
        nd_p = B.null_distribution(Cm, Q, reps, rng, "phase")
        nd_s = B.null_distribution(Cm, Q, reps, rng, "shift")
        nulls[iso] = nd_p
        cs = B.cov_shares(Cm, Q, names)
        rows[iso] = {"ratio": r, "p_phase": float((nd_p <= r).mean()), "p_shift": float((nd_s <= r).mean()),
                     "p_phase_amplify": float((nd_p >= r).mean()), "null_median": float(np.median(nd_p)),
                     **{k: v for k, v in cs.items() if k != "corr"}, **{f"corr_{k}": v for k, v in cs["corr"].items()}}
    return pd.DataFrame(rows).T.apply(pd.to_numeric), nulls


def pooled(tab, nulls, leaders, followers, rng):
    def group(members):
        obs = float(np.mean(np.log(tab.loc[members, "ratio"])))
        null = np.mean([np.log(nulls[i]) for i in members], axis=0)
        return {"geo_mean_ratio": float(np.exp(obs)), "null_geo_median": float(np.exp(np.median(null))),
                "p_offset": float((null <= obs).mean()), "p_amplify": float((null >= obs).mean())}
    out = {"leaders": group(leaders), "followers": group(followers), "all": group(list(tab.index))}
    lr = np.log(tab.loc[leaders + followers, "ratio"]).values
    k = len(leaders)
    d_obs = lr[:k].mean() - lr[k:].mean()
    perm = np.array([(lambda s: s[:k].mean() - s[k:].mean())(rng.permutation(lr)) for _ in range(9999)])
    out["leaders_minus_followers"] = {"diff_log_ratio": float(d_obs), "p_one_sided": float((perm <= d_obs).mean())}
    return out


def slope(tab, x):
    X = np.column_stack([np.ones(len(tab)), x])
    yv = np.log(tab["ratio"].values)
    bh, *_ = np.linalg.lstsq(X, yv, rcond=None)
    e = yv - X @ bh
    n = len(yv)
    XtXi = np.linalg.inv(X.T @ X)
    V = XtXi @ (X.T * e ** 2) @ X @ XtXi * n / (n - 2)
    se = float(np.sqrt(V[1, 1]))
    return {"slope": float(bh[1]), "se": se, "p": float(2 * stats.t.sf(abs(bh[1] / se), n - 2)), "n": n}


def corr_test(tab, col, leaders, followers, rng):
    a, b_ = tab.loc[leaders, col].values, tab.loc[followers, col].values
    allv = np.concatenate([a, b_])
    d = a.mean() - b_.mean()
    perm = np.array([(lambda s: s[:len(a)].mean() - s[len(a):].mean())(rng.permutation(allv)) for _ in range(9999)])
    return {"leaders_mean": float(a.mean()), "followers_mean": float(b_.mean()), "diff": float(d),
            "p_two_sided": float((np.abs(perm) >= abs(d)).mean())}


# ----------------------------------------------------------------------------- main
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(2026)
    R = {"settings": {"years": [Y0, Y1], "q": Q, "min_period_years": round(2 * (Y1 - Y0 + 1) / Q, 1),
                      "reps": REPS, "alpha": ALPHA}}
    parts, bcl = bcl_parts()
    isos = sorted(parts)

    lvl = bcl.pivot(index="year", columns="iso", values="gdppc_bcl")
    gap_avg = (np.log(lvl["USA"]).values[:, None] - np.log(lvl)).loc[Y0:Y1].mean()[isos]
    gap_1890 = (np.log(lvl.loc[1890, "USA"]) - np.log(lvl.loc[1890]))[isos]
    order = gap_avg.sort_values()
    leaders, followers = list(order.index[:8]), list(order.index[-8:])
    R["groups"] = {"leaders": leaders, "followers": followers, "gap_avg": order.round(3).to_dict(),
                   "gap_1890": gap_1890.round(3).to_dict(),
                   "definition": "8 smallest / 8 largest average log gap to US GDP per capita, 1891-2022"}

    # ---- Step 1 (+3): both decompositions
    tabs, nullss = {}, {}
    for dname, names in DECOMPS.items():
        tab, nulls = country_table(parts, names, rng)
        tab["gap_avg"], tab["gap_1890"] = gap_avg, gap_1890
        tab = tab.sort_values("gap_avg")
        tabs[dname], nullss[dname] = tab, nulls
        tab.round(3).to_csv(OUT / f"ratios_{dname}.csv")
        corr_cols = [c for c in tab.columns if c.startswith("corr_")]
        R[dname] = {"by_country": tab.round(4).to_dict(orient="index"),
                    "pooled": pooled(tab, nulls, leaders, followers, rng),
                    "slope_on_gap_avg": slope(tab, tab.gap_avg.values),
                    "slope_on_gap_1890": slope(tab, tab.gap_1890.values),
                    "corr_leaders_vs_followers": {c: corr_test(tab, c, leaders, followers, rng) for c in corr_cols}}
    # pooled with leaders/followers defined by the 1890 gap (ex ante)
    o1890 = gap_1890.sort_values()
    R["per_person"]["pooled_ex_ante_1890"] = pooled(tabs["per_person"], nullss["per_person"],
                                                    list(o1890.index[:8]), list(o1890.index[-8:]), rng)

    # ---- Step 2: division bias (per-person split: an hours error e moves tfp by -(1-a)e, l by +(1-a)e)
    tp = tabs["per_person"]
    need = {}
    for iso in isos:
        L = B.lf_matrix(M(parts[iso], DECOMPS["per_person"]), Q)
        cov_tl = np.mean(L[:, 0] * L[:, 2])
        var_l = np.var(L[:, 2])
        # error variance (in l units) that alone would create the observed tfp-l covariance: Cov = -Var(err_l)
        need[iso] = {"cov_tfp_l": float(cov_tl), "var_l": float(var_l),
                     "error_share_of_var_l_needed": float(max(0.0, -cov_tl) / var_l) if var_l > 0 else None}
    R["division_bias"] = {"per_person_tfp_l": need}
    post = {}
    for dname, names in DECOMPS.items():
        post[dname] = {}
        for iso in isos:
            g = parts[iso].loc[1951:Y1]
            post[dname][iso] = B.ratio(M(g, names), int(round(2 * len(g) / 25)))
        post[dname]["geo_leaders"] = geo([post[dname][i] for i in leaders])
        post[dname]["geo_followers"] = geo([post[dname][i] for i in followers])
    R["division_bias"]["post1950"] = post
    # post-1950 pooled tests against the same independence null (shorter window, fewer cosine terms)
    post_parts = {iso: parts[iso].loc[1951:Y1] for iso in isos}
    q_post = int(round(2 * len(post_parts["USA"]) / 25))
    R["post1950_pooled"] = {"q": q_post}
    for dname, names in DECOMPS.items():
        rows, nulls = {}, {}
        for iso, g in post_parts.items():
            Cm = M(g, names)
            r = B.ratio(Cm, q_post)
            nd = np.array([B.ratio(B.surrogate_phase(Cm, rng), q_post) for _ in range(REPS)])
            rows[iso], nulls[iso] = {"ratio": r, "null_median": float(np.median(nd))}, nd
        t = pd.DataFrame(rows).T.apply(pd.to_numeric)
        R["post1950_pooled"][dname] = pooled(t, nulls, leaders, followers, rng)
        R["post1950_pooled"][dname]["by_country"] = t.round(3).to_dict(orient="index")
    pwt = pwt_parts(isos)
    two = {}
    for iso in isos:
        if iso not in pwt:
            continue
        a, b_ = parts[iso].loc[1951:2019], pwt[iso].loc[1951:2019]
        yrs = a.index.intersection(b_.index)
        if len(yrs) < 60:
            continue
        q2 = int(round(2 * len(yrs) / 25))
        A, Bm = M(a.loc[yrs], DECOMPS["per_person"]), M(b_.loc[yrs], DECOMPS["per_person"])
        LA, LB = B.lf_matrix(A, q2), B.lf_matrix(Bm, q2)
        two[iso] = {"ratio_bcl": B.ratio(A, q2), "ratio_pwt": B.ratio(Bm, q2),
                    "ratio_cross_source": B.corrected_ratio(A, Bm, q2)[0],
                    "hours_lf_corr_between_sources": float(np.corrcoef(LA[:, 2], LB[:, 2])[0, 1]),
                    "capital_lf_corr_between_sources": float(np.corrcoef(LA[:, 1], LB[:, 1])[0, 1])}
    R["division_bias"]["pwt_1951_2019"] = two

    # ---- Step 4: counterfactuals (per-person split)
    cf = {}
    for iso in isos:
        g = parts[iso]
        base = np.var(B.lf_dev(g.y.values, Q))
        cf[iso] = {f"sd_ratio_frozen_{c}": float(np.sqrt(np.var(B.lf_dev(g.y.values - g[c].values + g[c].mean(), Q)) / base))
                   for c in DECOMPS["per_person"]}
        cf[iso]["lf_sd_gdppc"] = float(np.sqrt(base))
        L = B.lf_matrix(M(g, DECOMPS["per_person"]), Q)
        cf[iso]["lf_var_share_tfp"] = float(np.var(L[:, 0]) / np.var(L.sum(1)))
    R["counterfactual_frozen"] = cf

    R["steps_5_6"] = extra_steps(parts, leaders, followers, rng)

    with open(OUT / "results.json", "w") as f:
        json.dump(R, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    figures(R, parts, tabs, nullss, leaders, followers)
    print("done: output/balancing/results.json")
    return R


LEELEE_NAMES = {"Australia": "AUS", "Austria": "AUT", "Belgium": "BEL", "Canada": "CAN", "Switzerland": "CHE",
                "Chile": "CHL", "Germany": "DEU", "Denmark": "DNK", "Spain": "ESP", "Finland": "FIN", "France": "FRA",
                "United Kingdom": "GBR", "Greece": "GRC", "Ireland": "IRL", "Italy": "ITA", "Japan": "JPN",
                "Mexico": "MEX", "Netherlands": "NLD", "Norway": "NOR", "New Zealand": "NZL", "Portugal": "PRT",
                "Sweden": "SWE", "USA": "USA", "United States": "USA", "United States of America": "USA"}


def lee_lee_hc():
    """Lee and Lee (2016) human capital index, ages 15-64, 5-yearly 1870-2010 -> annual (log-linear)."""
    x = pd.read_excel(RAWB / "leelee2016" / "LeeLee_HC_MF1564.xls", header=None)
    x = x.iloc[8:, [0, 1, 4]]
    x.columns = ["country", "year", "hc"]
    x["country"] = x["country"].ffill()
    x = x.dropna(subset=["year", "hc"])
    x["iso"] = x.country.str.strip().map(LEELEE_NAMES)
    x = x.dropna(subset=["iso"])
    out = {}
    for iso, d in x.groupby("iso"):
        s = d.set_index(d.year.astype(int))["hc"].astype(float)
        s = s.reindex(range(int(s.index.min()), int(s.index.max()) + 1))
        out[iso] = np.exp(np.log(s).interpolate())
    return out


def ramey_hours_pc():
    d = pd.read_excel(RAWB / "ramey" / "aej_extracted" / "Main_Data.xls", sheet_name="Main_data", header=None)
    hdr = d.iloc[4].tolist()
    d = d.iloc[5:].copy()
    d.columns = hdr
    d = d[pd.to_numeric(d.year, errors="coerce").notna()]
    d.index = d.year.astype(int)
    return pd.to_numeric(d.mkthours, errors="coerce") / pd.to_numeric(d.poptot, errors="coerce")


def nsf_research():
    t = pd.read_excel(RAWB / "nsf_national_patterns" / "extracted" / "nsf26313-tab001.xlsx", header=None).iloc[6:]
    t = t[[0, 1, 4, 5]]
    t.columns = ["year", "gdp_nom", "rd_nom", "rd_real"]
    t["year"] = pd.to_numeric(t.year.astype(str).str[:4], errors="coerce")
    t = t.dropna(subset=["year"]).set_index(t.year.dropna().astype(int)).drop(columns="year").astype(float)
    return t


def bea_series(codes):
    """Annual BEA NIPA series (current dollars) from the flat file, summed across codes."""
    d = pd.read_csv(RAWB / "bea_nipa" / "NipaDataA.txt")
    d.columns = ["code", "year", "value"]
    d = d[d.code.isin(codes)].copy()
    d["value"] = pd.to_numeric(d.value.astype(str).str.replace(",", ""), errors="coerce")
    d["year"] = pd.to_numeric(d.year, errors="coerce")
    return d.groupby("year")["value"].sum(min_count=len(codes))


def bjvw_researchers():
    """Aggregate effective researchers from Bloom, Jones, Van Reenen and Webb (2020), if the
    replication archive is present and contains a readable spreadsheet with that series."""
    import zipfile
    path = RAWB / "bjvw2020" / "IdeaPFPrograms.zip"
    try:
        z = zipfile.ZipFile(path)
    except Exception:
        return None, "replication archive not available (download incomplete)"
    return None, "archive present; aggregate series not parsed: " + ", ".join(
        n for n in z.namelist() if "aggregate" in n.lower() or "us_" in n.lower())[:300]


def extra_steps(parts, leaders, followers, rng):
    out = {}
    # ---- Step 2d: a second US hours series (Ramey-Francis), 1901-2005
    hr = ramey_hours_pc()
    g_hr = 100 * np.log(hr).diff()
    u = parts["USA"]
    yrs = np.arange(1901, 2006)
    q = int(round(2 * len(yrs) / 25))
    A = M(u.reindex(yrs), DECOMPS["per_person"])
    lB = (1 - ALPHA) * g_hr.reindex(yrs).values
    kB = u.k.reindex(yrs).values
    Bm = np.column_stack([u.y.reindex(yrs).values - kB - lB, kB, lB])
    out["us_two_hours_sources"] = {
        "years": [1901, 2005], "q": q,
        "hours_lf_corr": float(np.corrcoef(B.lf_dev(u.h.reindex(yrs).values, q), B.lf_dev(g_hr.reindex(yrs).values, q))[0, 1]),
        "ratio_bcl": B.ratio(A, q), "ratio_ramey_hours": B.ratio(Bm, q),
        "ratio_cross_source": B.corrected_ratio(A, Bm, q)[0]}

    # ---- Step 5: inside TFP — education vs the rest
    hc = lee_lee_hc()
    edu = {}
    rows, nulls = {}, {}
    for iso, g in parts.items():
        if iso not in hc:
            continue
        e = 100 * (1 - ALPHA) * np.log(hc[iso]).diff()
        gg = g.loc[:2010].copy()
        gg["e"] = e.reindex(gg.index)
        gg = gg.dropna()
        gg["tfp_res"] = gg.tfp - gg.e
        if len(gg) < 100:
            continue
        q5 = int(round(2 * len(gg) / 25))
        pair = gg[["tfp_res", "e"]].values
        four = gg[["tfp_res", "e", "k", "l"]].values
        r2 = B.ratio(pair, q5)
        nd = np.array([B.ratio(B.surrogate_phase(pair, rng), q5) for _ in range(REPS)])
        L = B.lf_matrix(pair, q5)
        cov = np.mean(L[:, 0] * L[:, 1])
        # slope of measured TFP on the education contribution at low frequency:
        # 1 = education raises TFP as assumed and the rest is independent; 0 = no visible effect;
        # < 0 = the rest of TFP moves against schooling (offsetting beyond "no effect")
        Lt = B.lf_matrix(gg[["tfp", "e"]].values, q5)
        slope_te = float(np.mean(Lt[:, 0] * Lt[:, 1]) / np.var(Lt[:, 1]))
        # war-neutralized version (1914-1919, 1939-1949 replaced by window averages)
        from frontier import identification as ID
        wn = gg[["tfp_res", "e"]].apply(lambda s: ID.neutralize(s, [(1914, 1919), (1939, 1949)]))
        r_nowar = B.ratio(wn.values, q5)
        rows[iso] = {"ratio_tfp_split": r2, "p_offset": float((nd <= r2).mean()), "null_median": float(np.median(nd)),
                     "corr_e_tfpres": float(np.corrcoef(L[:, 0], L[:, 1])[0, 1]),
                     "slope_tfp_on_edu": slope_te, "ratio_wars_neutralized": r_nowar,
                     "ratio_four_parts": B.ratio(four, q5),
                     "edu_contrib_mean": float(gg.e.mean()), "tfp_res_mean": float(gg.tfp_res.mean()),
                     # hc error enters e (+) and tfp_res (-): error variance needed to create the covariance alone
                     "error_share_of_var_e_needed": float(max(0.0, -cov) / np.var(L[:, 1]))}
        nulls[iso] = nd
    t = pd.DataFrame(rows).T.apply(pd.to_numeric)
    t["ratio"] = t["ratio_tfp_split"]
    edu["by_country"] = t.round(4).to_dict(orient="index")
    lead = [i for i in leaders if i in t.index]
    foll = [i for i in followers if i in t.index]
    edu["pooled"] = pooled(t, nulls, lead, foll, rng)
    edu["years"] = [Y0, 2010]
    edu["geo_ratio_wars_neutralized"] = {"leaders": geo(t.loc[lead, "ratio_wars_neutralized"]),
                                         "followers": geo(t.loc[foll, "ratio_wars_neutralized"]),
                                         "all": geo(t["ratio_wars_neutralized"])}
    edu["median_slope_tfp_on_edu"] = {"leaders": float(t.loc[lead, "slope_tfp_on_edu"].median()),
                                      "followers": float(t.loc[foll, "slope_tfp_on_edu"].median()),
                                      "share_negative_all": float((t.slope_tfp_on_edu < 0).mean())}
    out["education_inside_tfp"] = edu

    # ---- Step 6: direct test at the leader — US TFP vs US research effort
    nsf = nsf_research()
    mad = data.load_maddison()
    pop = mad[mad.iso == "USA"].set_index("year")["pop"]
    gdppc_nom = nsf.gdp_nom / pop.reindex(nsf.index)
    meas = {"real_rd": nsf.rd_real, "rd_over_gdppc": nsf.rd_nom / gdppc_nom}
    # BEA, 1929 onward: "effective researchers" = research spending / nominal GDP per person
    # (Bloom-Jones-Van Reenen-Webb use IPP investment over a scientist-wage deflator; Jones's own
    # note in their files suggests nominal GDP per person as the simpler deflator)
    gdp_bea = bea_series(["A191RC"])
    gdppc_bea = gdp_bea / pop.reindex(gdp_bea.index)
    meas["bea_rd_over_gdppc"] = bea_series(["Y694RC"]) / gdppc_bea
    meas["bea_ipp_over_gdppc"] = bea_series(["Y001RC", "Y055RC"]) / gdppc_bea
    pat = data.load_patents()
    meas_long = {"us_patent_filings": pat[pat.iso == "USA"].set_index("year")["patents"]}
    tfp = 100 * np.log(data.load_bcl().query("iso == 'USA'").set_index("year").tfp).diff()
    sem = {}
    for name, s in {**meas, **meas_long}.items():
        gS = 100 * np.log(s.astype(float)).diff()
        yy = np.array([y for y in range(1885, 2023) if y in gS.dropna().index and y in tfp.dropna().index])
        qq = int(round(2 * len(yy) / 25))
        y_, x_ = tfp.reindex(yy).values, gS.reindex(yy).values
        lags = {L: lowfreq.correlation(y_[L:], x_[:len(x_) - L], qq) if L >= 0
                else lowfreq.correlation(y_[:L], x_[-L:], qq) for L in (-15, -10, -5, 0, 5, 10, 15)}
        lagreg = {}
        for L in (0, 5, 10):
            yl, xl = y_[L:], x_[:len(x_) - L]
            ql = int(round(2 * len(yl) / 25))
            r_ = lowfreq.regression(yl, xl[:, None], ql, ["g_research"])
            lagreg[L] = {"slope": r_["coef"]["g_research"], "se": r_["se"]["g_research"],
                         "t": r_["t"]["g_research"], "p": r_["p"]["g_research"], "q": ql}
        sem[name] = {"years": [int(yy[0]), int(yy[-1])], "q": qq, "mean_research_growth": float(np.mean(x_)),
                     "mean_tfp_growth": float(np.mean(y_)), "implied_beta_from_means": float(np.mean(x_) / np.mean(y_)),
                     "lf_regression_by_lag": lagreg, "lf_corr_by_lag": {int(k): float(v) for k, v in lags.items()},
                     "predicted_slope_if_beta3": 1 / 3}
    sem["bjvw_aggregate"] = bjvw_researchers()[1]
    out["semi_endogenous_at_leader"] = sem

    # ---- Robustness A: capital in the K/Y form (capital accumulation induced by TFP is credited to TFP)
    #   g_y = g_tfp/(1-a) + a/(1-a) g_(K/Y) + g_(H/N)
    ky = {}
    for iso, g in parts.items():
        g_kn = g.k / ALPHA
        g_ky = g_kn - g.y
        Cm = np.column_stack([g.tfp / (1 - ALPHA), ALPHA / (1 - ALPHA) * g_ky, g.h])
        L = B.lf_matrix(Cm, Q)
        ky[iso] = {"ratio": B.ratio(Cm, Q), "corr_tfp_ky": float(np.corrcoef(L[:, 0], L[:, 1])[0, 1])}
    kyt = pd.DataFrame(ky).T
    out["ky_form"] = {"by_country": kyt.round(4).to_dict(orient="index"),
                      "geo_ratio": {"leaders": geo(kyt.loc[leaders, "ratio"]), "followers": geo(kyt.loc[followers, "ratio"])},
                      "corr_tfp_ky": corr_test(kyt.rename(columns={"corr_tfp_ky": "c"}), "c", leaders, followers, rng)}

    # ---- Robustness B: education with Lee-Lee's alternative human capital index (column 'Human Capital Alternative')
    x = pd.read_excel(RAWB / "leelee2016" / "LeeLee_HC_MF1564.xls", header=None).iloc[8:, [0, 1, 5]]
    x.columns = ["country", "year", "hca"]
    x["country"] = x.country.ffill()
    x = x.dropna(subset=["year", "hca"])
    x["iso"] = x.country.str.strip().map(LEELEE_NAMES)
    alt = {}
    for iso, d in x.dropna(subset=["iso"]).groupby("iso"):
        s = d.set_index(d.year.astype(int))["hca"].astype(float)
        s = np.exp(np.log(s.reindex(range(int(s.index.min()), int(s.index.max()) + 1))).interpolate())
        g = parts.get(iso)
        if g is None:
            continue
        gg = g.loc[:2010].copy()
        gg["e"] = (100 * (1 - ALPHA) * np.log(s).diff()).reindex(gg.index)
        gg = gg.dropna()
        gg["tfp_res"] = gg.tfp - gg.e
        q5 = int(round(2 * len(gg) / 25))
        Lt = B.lf_matrix(gg[["tfp", "e"]].values, q5)
        alt[iso] = {"ratio": B.ratio(gg[["tfp_res", "e"]].values, q5),
                    "slope_tfp_on_edu": float(np.mean(Lt[:, 0] * Lt[:, 1]) / np.var(Lt[:, 1]))}
    at = pd.DataFrame(alt).T
    out["education_alt_index"] = {"geo_ratio": {"leaders": geo(at.loc[[i for i in leaders if i in at.index], "ratio"]),
                                                "followers": geo(at.loc[[i for i in followers if i in at.index], "ratio"]),
                                                "all": geo(at["ratio"])},
                                  "median_slope": float(at.slope_tfp_on_edu.median()),
                                  "share_negative_slope": float((at.slope_tfp_on_edu < 0).mean())}

    # ---- Step 5b: the 1919-41 surge on Bakker-Crafts-Woltjer estimates
    bw = pd.read_excel(RAWB / "bcw2019" / "extracted" /
                       "Bakker Crafts & Woltjer Data S1 growth accounts 1899t1941 v2_07 28.08.2018.xlsx", sheet_name="dat")
    pde = bw[bw.ind == "_PDE"].set_index("var")
    ub = data.load_bcl().query("iso == 'USA'").set_index("year")
    per = [(1899, 1909), (1909, 1919), (1919, 1929), (1929, 1941)]
    out["tfp_1899_1941"] = {f"{a}-{b}": {
        "bcw_net_tfp": float(100 * pde.loc["TFP", f"d{a}t{str(b)[2:]}"]),
        "bcw_hours": float(100 * pde.loc["H", f"d{a}t{str(b)[2:]}"]),
        "bcl_tfp": float(100 * (np.log(ub.tfp[b]) - np.log(ub.tfp[a])) / (b - a)),
        "bcl_hours_total": float(100 * (np.log(ub.hours_pc[b] * mad.query("iso=='USA'").set_index('year')['pop'][b])
                                      - np.log(ub.hours_pc[a] * mad.query("iso=='USA'").set_index('year')['pop'][a])) / (b - a))}
        for a, b in per}
    return out


def figures(R, parts, tabs, nullss, leaders, followers):
    import matplotlib.pyplot as plt
    P = plots
    src = "Source: Bergeaud–Cette–Lecat Long-Term Productivity Database v2.7; own calculations."

    # B1 per-hour vs per-person ratios by country, ordered by distance to the US
    tp, th = tabs["per_person"], tabs["per_hour"]
    order = tp.sort_values("gap_avg").index
    fig, ax = P.setup(figsize=(10, 6.2))
    y = np.arange(len(order))
    for k, iso in enumerate(order):
        nd = nullss["per_person"][iso]
        ax.plot([np.percentile(nd, 5), np.percentile(nd, 95)], [k, k], color="#e2e2e2", lw=6, solid_capstyle="butt")
    ax.scatter(th.loc[order, "ratio"], y, color=P.GREY, s=26, label="Per-hour split (capital per hour vs hours)", zorder=3)
    ax.scatter(tp.loc[order, "ratio"], y, color=P.BLUE, s=34, label="Per-person split (main test)", zorder=4)
    ax.axvline(1, color="#999999", lw=0.8)
    ax.set_xscale("log")
    from matplotlib.ticker import FixedLocator, NullFormatter, NullLocator
    ax.xaxis.set_major_locator(FixedLocator([0.25, 0.5, 1, 2]))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticklabels(["0.25", "0.5", "1", "2"])
    ax.set_yticks(y)
    ax.set_yticklabels([f"{i}{'  (leader)' if i in leaders else ('  (follower)' if i in followers else '')}" for i in order], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel("Low-frequency variance of GDP per capita growth ÷ sum of the parts' variances (<1: offsetting)", color="#555555")
    ax.legend(frameon=False, fontsize=8.5, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    ax.grid(axis="x", color="#eeeeee")
    P.titles(fig, "Most of the apparent offsetting comes from how capital per hour is defined",
             "Countries ordered by average distance to US GDP per capita · grey band: 90% range if the parts were independent",
             src)
    P.save(fig, FIG / "b1_ratios_two_splits.png")

    # B2 US low-frequency components (per person)
    g = parts["USA"]
    yrs = g.index.values
    fig, ax = P.setup()
    for c, name, col, lw in [("y", "GDP per capita", P.DARK, 2.4), ("tfp", "TFP", P.RED, 1.8),
                             ("k", "Capital per person (α·Δk)", P.GREY, 1.5), ("l", "Hours per person ((1−α)·Δh)", P.BLUE, 1.8)]:
        ax.plot(yrs, lowfreq.trend(g[c].values, Q), color=col, lw=lw, label=name)
    ax.axhline(0, color="#bbbbbb", lw=0.8)
    ax.set_xlim(yrs[0], yrs[-1])
    ax.set_ylabel("% per year (low-frequency trend)", color="#555555")
    ax.legend(frameon=False, fontsize=8.5, loc="upper right", ncol=2)
    cf = R["counterfactual_frozen"]["USA"]
    P.titles(fig, "In the US, hours swing with TFP and add to long-run swings in growth",
             f"Low-frequency components of US GDP per capita growth (periods ≥ {R['settings']['min_period_years']:.0f} yrs) · "
             f"freezing hours would make long-run growth {100 * (1 - cf['sd_ratio_frozen_l']):.0f}% smoother", src)
    P.save(fig, FIG / "b2_us_components.png")

    # B3 TFP-capital co-movement: leaders vs followers
    fig, ax = P.setup(figsize=(9, 5))
    col = "corr_tfp_k"
    for k, (grp, name, c) in enumerate([(leaders, "Leaders", P.BLUE), (followers, "Followers", P.GREY)]):
        vals = tp.loc[grp, col]
        ax.scatter(np.full(len(vals), k) + np.linspace(-0.12, 0.12, len(vals)), vals, color=c, s=40, zorder=3)
        for xi, (iso, v) in zip(np.full(len(vals), k) + np.linspace(-0.12, 0.12, len(vals)), vals.items()):
            ax.text(xi + 0.03, v, iso, fontsize=7.5, color="#555555", va="center")
        ax.hlines(vals.mean(), k - 0.25, k + 0.25, color=c, lw=2.5)
    ax.axhline(0, color="#999999", lw=0.8)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Leaders (8 closest to US)", "Followers (8 farthest)"])
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylabel("Long-run correlation of TFP and capital-per-person growth", color="#555555")
    t = R["per_person"]["corr_leaders_vs_followers"][col]
    P.titles(fig, "Followers' capital and TFP surge together; leaders' do not",
             f"Bars: group means ({t['leaders_mean']:.2f} vs {t['followers_mean']:.2f}; permutation p = {t['p_two_sided']:.2f})", src)
    P.save(fig, FIG / "b3_tfp_capital_corr.png")

    # B4 full sample vs post-1950 pooled ratios (per person)
    fig, ax = P.setup(figsize=(9, 5))
    labels = ["Full sample 1891–2022", "Post-1950"]
    for k, (grp, name, c) in enumerate([("leaders", "Leaders", P.BLUE), ("followers", "Followers", P.GREY)]):
        vals = [R["per_person"]["pooled"][grp]["geo_mean_ratio"], R["post1950_pooled"]["per_person"][grp]["geo_mean_ratio"]]
        nullv = [R["per_person"]["pooled"][grp]["null_geo_median"], R["post1950_pooled"]["per_person"][grp]["null_geo_median"]]
        xs = np.arange(2) + (k - 0.5) * 0.35
        ax.bar(xs, vals, 0.35, color=c, label=name)
        ax.scatter(xs, nullv, marker="_", s=400, color=P.DARK, zorder=4, label="Expected if independent" if k == 0 else None)
        for xi, v in zip(xs, vals):
            ax.text(xi, v - 0.06, f"{v:.2f}", ha="center", fontsize=9, color="white", fontweight="bold")
    ax.axhline(1, color="#999999", lw=0.8)
    ax.set_xticks(range(2))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.3)
    ax.set_ylabel("Variance ratio (geometric mean; <1: offsetting)", color="#555555")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    pp = R["post1950_pooled"]["per_person"]
    P.titles(fig, "Leaders offset only after 1950; followers amplify",
             f"Per-person split · post-1950 leaders vs followers: p = {pp['leaders_minus_followers']['p_one_sided']:.2f} "
             f"(one-sided permutation); only ~3 independent long cycles", src)
    P.save(fig, FIG / "b4_full_vs_post1950.png")

    S = R.get("steps_5_6", {})
    # B5 education vs the rest of TFP
    if "education_inside_tfp" in S:
        t = pd.DataFrame(S["education_inside_tfp"]["by_country"]).T.apply(pd.to_numeric)
        gaps = tabs["per_person"]["gap_avg"]
        t = t.loc[[i for i in gaps.sort_values().index if i in t.index]]
        fig, ax = P.setup(figsize=(10, 6.2))
        yv = np.arange(len(t))
        cols = [P.BLUE if i in leaders else (P.GREY if i in followers else "#9bbbe3") for i in t.index]
        ax.barh(yv, t["slope_tfp_on_edu"], color=cols)
        ax.axvline(0, color="#999999", lw=0.8)
        ax.axvline(1, color=P.DARK, lw=1, ls=(0, (4, 3)))
        ax.text(1.03, len(t) - 0.6, "1 = education shows up in TFP\nas growth accounting assumes", fontsize=8, color="#555555", va="bottom")
        ax.set_yticks(yv)
        ax.set_yticklabels(t.index, fontsize=8.5)
        ax.invert_yaxis()
        ax.set_xlabel("Low-frequency slope of measured TFP growth on the education contribution", color="#555555")
        ep = S["education_inside_tfp"]["pooled"]
        P.titles(fig, "Measured TFP does not speed up when schooling does; in half the countries it slows",
                 f"Ordered by distance to the US (blue: leaders, light blue: middle, grey: followers) · variance ratio education vs rest of TFP: "
                 f"leaders {ep['leaders']['geo_mean_ratio']:.2f} (p<0.01), all {ep['all']['geo_mean_ratio']:.2f}",
                 "Sources: Bergeaud–Cette–Lecat v2.7; Lee & Lee (2016) human capital index; 1891–2010.")
        P.save(fig, FIG / "b5_education_tfp.png")

    # B6 US TFP vs research effort, lags
    if "semi_endogenous_at_leader" in S:
        sem = S["semi_endogenous_at_leader"]
        fig, ax = P.setup(figsize=(9.5, 5.2))
        for k, (name, lab, col) in enumerate([("real_rd", "Real R&D (NSF, 1954–2022)", P.BLUE),
                                              ("rd_over_gdppc", "R&D ÷ GDP per person (NSF, 1954–2022)", "#8db8ea"),
                                              ("bea_rd_over_gdppc", "R&D ÷ GDP per person (BEA, 1930–2022)", P.RED),
                                              ("us_patent_filings", "Patent filings (WIPO, 1891–2021)", P.GREY)]):
            lr = sem[name]["lf_regression_by_lag"]
            Ls = sorted(int(x) for x in lr)
            b = [lr[str(L)]["slope"] if str(L) in lr else lr[L]["slope"] for L in Ls]
            se = [lr[str(L)]["se"] if str(L) in lr else lr[L]["se"] for L in Ls]
            xs = np.array(Ls) + (k - 1.5) * 0.8
            ax.errorbar(xs, b, yerr=1.645 * np.array(se), fmt="o", color=col, capsize=3, label=lab)
        ax.axhline(0, color="#999999", lw=0.8)
        ax.axhline(1 / 3, color=P.DARK, lw=0.9, ls=(0, (4, 3)))
        ax.text(6.2, 1 / 3 + 0.015, "Jones's model with β = 3", fontsize=8, color="#555555")
        ax.set_xticks([0, 5, 10])
        ax.set_xticklabels(["same years", "research 5 yrs earlier", "research 10 yrs earlier"])
        ax.set_ylabel("Response of US TFP growth to research growth (90% interval)", color="#555555")
        ax.legend(frameon=False, fontsize=8, loc="upper left", ncol=2)
        ax.set_ylim(-0.4, 0.62)
        P.titles(fig, "US productivity follows research effort with a lag, as Jones predicts",
                 "Low-frequency regressions of US TFP growth on research-effort growth",
                 "Sources: Bergeaud–Cette–Lecat v2.7; NSF National Patterns of R&D (NSF 26-313); WIPO. Few effective observations (q = 5–10).")
        P.save(fig, FIG / "b6_us_research_lags.png")


if __name__ == "__main__":
    main()
