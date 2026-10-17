"""Is steady aggregate productivity growth an average of unsteady industries?

Pre-registered design: litreview_sectoral_averaging.md.
  H1 averaging: aggregate low-frequency SD vs 'independent' and 'synchronized' benchmarks; variance ratio
     R = Var(sum of contributions) / sum Var(contributions) with an independence (surrogate) null; common factor.
  H2 relay: rank correlation of industry TFP growth between consecutive eras; concentration of contributions.
  H3 Baumol stabilizer: (a) TFP growth in an era vs change in nominal share into the next era;
     (b) actual aggregate vs fixed-weight counterfactual: which swings more across eras / at low frequency.
  H4 broadness of the mid-century acceleration and of the later slowdowns.
Data:
  1899-1941  Bakker-Crafts-Woltjer (2019): 38 industries, value-added TFP, value-added shares (omega), 4 periods.
  1948-2014  Jorgenson-Ho-Samuels US KLEMS (2017 release): 61 private industries, gross-output TFP as a
             Tornqvist residual (K, L, intermediates), Domar weights GO_i / sum VA.
  2015-2024  Official BEA-BLS Integrated Industry-Level Production Account (April 2026): same 61 industries.
Domar-weighted gross-output TFP equals value-added-share-weighted value-added TFP, so contributions are comparable.
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
from frontier import lowfreq, plots  # noqa: E402

OUT = C.ROOT / "output" / "sectoral"
FIG = OUT / "figures"
RAW = C.RAW / "sectoral"
BCW = C.RAW / "balancing" / "bcw2019" / "extracted" / "Bakker Crafts & Woltjer Data S1 growth accounts 1899t1941 v2_07 28.08.2018.xlsx"

SECTORS = ["Agriculture", "Mining", "Utilities", "Construction", "Durable mfg", "Nondurable mfg", "Trade",
           "Transportation", "Communications/info", "FIRE", "Other services"]
JHS_SECTOR = {**{i: "Agriculture" for i in (1, 2)}, **{i: "Mining" for i in (3, 4, 5)}, 6: "Utilities",
              7: "Construction", **{i: "Durable mfg" for i in range(8, 19)},
              **{i: "Nondurable mfg" for i in range(19, 27)}, **{i: "Trade" for i in (27, 28)},
              **{i: "Transportation" for i in range(29, 37)}, **{i: "Communications/info" for i in range(37, 41)},
              **{i: "FIRE" for i in range(41, 47)}, **{i: "Other services" for i in range(47, 62)}}
BCW_SECTOR = {"_A": "Agriculture", **{k: "Mining" for k in ("_206", "_2161", "_2162", "_226", "_236")},
              **{k: "Utilities" for k in ("_581", "_582", "_583")}, "_C": "Construction",
              **{k: "Durable mfg" for k in ("_24", "_25", "_32", "_33", "_34", "_35", "_36", "_37", "_38t9")},
              **{k: "Nondurable mfg" for k in ("_20", "_21", "_22", "_23", "_31", "_26", "_27", "_28", "_29", "_30")},
              "_FtG": "Trade", **{k: "Transportation" for k in ("_50", "_51", "_52")},
              **{k: "Communications/info" for k in ("_571", "_572", "_573")}, "_H": "FIRE", "_857": "Other services"}
PRE_ERAS = ["1899-1909", "1909-1919", "1919-1929", "1929-1941"]
POST_ERAS = {"1948-1973": (1949, 1973), "1973-1995": (1974, 1995), "1995-2007": (1996, 2007), "2007-2024": (2008, 2024)}


# ----------------------------------------------------------------------------- data
def load_bcw():
    d = pd.read_excel(BCW, sheet_name="dat")
    cols = ["d1899t09", "d1909t19", "d1919t29", "d1929t41"]
    g = d[d["var"] == "TFP"].set_index("ind")[cols] * 100
    w = d[d["var"] == "omega"].set_index("ind")[cols]
    names = d[d["var"] == "TFP"].set_index("ind")["ind_desc"]
    g.columns = w.columns = PRE_ERAS
    pde = g.loc["_PDE"]
    g, w = g.drop("_PDE"), w.drop("_PDE")
    return g, w, pde, names.drop("_PDE")


def load_jhs():
    p = RAW / "worldklems_us" / "usa_wk_mar_2017.xlsx"
    d = pd.read_excel(p, sheet_name="KLEMdata", header=1)
    d = d[d.industry <= 61].sort_values(["industry", "year"])
    nom = {"go": "gross output", "k": "capital", "l": "labor", "ii": "intermediate"}
    out = []
    for ind, x in d.groupby("industry"):
        x = x.set_index("year")
        go_n = x[nom["go"]]
        shares = {j: x[nom[j]] / go_n for j in ("k", "l", "ii")}
        dl = {j: np.log(x[nom[j] + ".1"]).diff() for j in ("go", "k", "l", "ii")}
        tfp = 100 * (dl["go"] - sum(0.5 * (shares[j] + shares[j].shift(1)) * dl[j] for j in ("k", "l", "ii")))
        out.append(pd.DataFrame({"industry": ind, "year": x.index, "g": tfp.values, "go": go_n.values,
                                 "va": (x[nom["k"]] + x[nom["l"]]).values}))
    return _domar(pd.concat(out))


def load_official():
    p = RAW / "bea_bls_klems" / "industry-production-account-capital.xlsx"

    def wide(sheet):
        t = pd.read_excel(p, sheet_name=sheet, header=1).iloc[:61]
        t.columns = [str(c).strip() for c in t.columns]
        t["industry"] = range(1, 62)
        return t.melt(id_vars=["Industry Description", "industry"], var_name="year", value_name=sheet)

    t = wide("Integrated TFP Index").merge(wide("Gross Output"), on=["industry", "year", "Industry Description"]) \
        .merge(wide("Value Added"), on=["industry", "year", "Industry Description"])
    t = t[t.year.str.fullmatch(r"\d{4}")]
    t["year"] = t.year.astype(int)
    for c in ("Integrated TFP Index", "Gross Output", "Value Added"):
        t[c] = pd.to_numeric(t[c], errors="coerce")
    t = t.sort_values(["industry", "year"])
    t["g"] = 100 * np.log(t["Integrated TFP Index"]).groupby(t.industry).diff()
    t = t.rename(columns={"Gross Output": "go", "Value Added": "va"})[["industry", "year", "g", "go", "va"]]
    return _domar(t), pd.read_excel(p, sheet_name="Integrated TFP Index", header=1).iloc[:61, 0].tolist()


def load_beabls_experimental():
    """BEA-BLS experimental integrated account, 1963-2016 sheet: Tornqvist gross-output TFP (robustness)."""
    p = RAW / "bea_bls_klems" / "industry-production-account-experimental.xlsx"
    d = pd.read_excel(p, sheet_name="1963-2016", header=1)
    d = d[d.indnum <= 61].sort_values(["indnum", "yr"])
    pairs = [("ii.", "iiqi."), ("vkit.", "qkit."), ("vksoft.", "qks."), ("vkRD.", "qkrd."), ("vkart.", "qka."),
             ("vkoth.", "qko."), ("vlcol.", "qlindexcol_merge."), ("vln.", "qlindexn_merge.")]
    out = []
    for ind, x in d.groupby("indnum"):
        x = x.set_index("yr")
        go = x["go."]
        tfp = 100 * np.log(x["goqi."]).diff()
        for v, qn in pairs:
            sh = (x[v] / go).clip(lower=0)
            dl = np.log(x[qn].where(x[qn] > 0)).diff().fillna(0)
            tfp = tfp - 100 * 0.5 * (sh + sh.shift(1)) * dl
        va = go - x["ii."]
        out.append(pd.DataFrame({"industry": ind, "year": x.index, "g": tfp.values, "go": go.values, "va": va.values}))
    return _domar(pd.concat(out))


def _domar(t):
    tot = t.groupby("year").va.transform("sum")
    t = t.assign(d=t.go / tot, w=t.va / tot)
    t = t.sort_values(["industry", "year"])
    t["dbar"] = 0.5 * (t.d + t.groupby("industry").d.shift(1))
    t["wbar"] = 0.5 * (t.w + t.groupby("industry").w.shift(1))
    t["c"] = t.dbar * t.g
    return t


# ----------------------------------------------------------------------------- statistics
def averaging_stats(Cm, q, rng, reps=1000, low_freq=True):
    """Cm: T x N matrix of contributions. Returns aggregate SD, independent and synchronized benchmarks, R, null."""
    L = B.lf_matrix(Cm, q) if low_freq else Cm - Cm.mean(0)
    sd_parts = L.std(0)
    sd_agg = float(L.sum(1).std())
    sd_ind = float(np.sqrt((sd_parts ** 2).sum()))
    sd_syn = float(sd_parts.sum())
    R = (sd_agg / sd_ind) ** 2
    if low_freq:
        null = B.null_distribution(Cm, q, reps, rng, kind="phase")
    else:  # era data: independent permutation of each column's era order
        null = np.array([((np.column_stack([rng.permutation(Cm[:, k]) for k in range(Cm.shape[1])]).sum(1).std()) ** 2)
                         / (sd_parts ** 2).sum() for _ in range(reps)])
    corr = np.corrcoef(L.T)
    iu = np.triu_indices_from(corr, 1)
    return {"sd_aggregate": sd_agg, "sd_independent": sd_ind, "sd_synchronized": sd_syn,
            "position_0ind_1sync": (sd_agg - sd_ind) / (sd_syn - sd_ind), "R": float(R),
            "R_null_median": float(np.median(null)), "R_null_p05": float(np.quantile(null, 0.05)),
            "R_null_p95": float(np.quantile(null, 0.95)), "p_above_null": float(np.mean(null >= R)),
            "p_below_null": float(np.mean(null <= R)), "mean_pairwise_corr": float(np.nanmean(corr[iu])),
            "n_parts": int(Cm.shape[1]), "T": int(Cm.shape[0])}


def first_pc_share(G, q, rng, reps=500):
    """Share of low-frequency variance of (standardized) industry TFP growth explained by the first PC, vs a null."""
    def share(M):
        P = np.column_stack([lowfreq.project(M[:, k], q) for k in range(M.shape[1])])
        P = (P - P.mean(0)) / P.std(0)
        ev = np.linalg.svd(P, compute_uv=False) ** 2
        return float(ev[0] / ev.sum())
    obs = share(G)
    null = np.array([share(B.surrogate_phase(G, rng)) for _ in range(reps)])
    return {"share": obs, "null_median": float(np.median(null)), "p": float(np.mean(null >= obs))}


def era_table(t, eras):
    rows = []
    for e, (a, b) in eras.items():
        x = t[(t.year >= a) & (t.year <= b)].groupby("industry")
        rows.append(pd.DataFrame({"era": e, "g": x.g.mean(), "c": x.c.mean(), "w": x.wbar.mean(), "d": x.dbar.mean()}))
    return pd.concat(rows).reset_index()


def concentration(c):
    c = c.sort_values(ascending=False)
    agg = c.sum()
    return {"aggregate": float(agg), "top5_share": float(c.iloc[:5].sum() / agg) if agg else np.nan,
            "top5": list(c.index[:5]), "n_positive": int((c > 0).sum()), "n": int(len(c)),
            "sum_negative": float(c[c < 0].sum())}


def rank_persistence(G):
    """Spearman rank correlation of industry TFP growth between consecutive eras (columns)."""
    out = {}
    for a, b in zip(G.columns[:-1], G.columns[1:]):
        ok = G[a].notna() & G[b].notna()
        r, p = stats.spearmanr(G.loc[ok, a], G.loc[ok, b])
        out[f"{a} -> {b}"] = {"rho": float(r), "p": float(p), "n": int(ok.sum())}
    return out


def baumol(G, W):
    """Pooled correlation of TFP growth in era e with log change in nominal share from e to e+1."""
    xs, ys = [], []
    for a, b in zip(G.columns[:-1], G.columns[1:]):
        ok = G[a].notna() & W[a].notna() & W[b].notna() & (W[a] > 0) & (W[b] > 0)
        xs.append(G.loc[ok, a] - G.loc[ok, a].mean())
        ys.append(np.log(W.loc[ok, b] / W.loc[ok, a]) - np.log(W.loc[ok, b] / W.loc[ok, a]).mean())
    x, y = pd.concat(xs), pd.concat(ys)
    r, p = stats.pearsonr(x, y)
    slope = float(np.polyfit(x, y, 1)[0])
    return {"corr": float(r), "p": float(p), "slope_dlogshare_per_pp_tfp": slope, "n": int(len(x))}


def fixed_weight(G, W):
    """Era aggregates with actual weights vs weights frozen at the first era (renormalized to covered industries)."""
    w0 = W.iloc[:, 0]
    act = (G * W).sum() / W.sum()
    fix = (G.mul(w0, axis=0)).sum() / w0[G.notna().all(1)].sum()
    return {"actual": act.round(3).to_dict(), "fixed_first_era": fix.round(3).to_dict(),
            "sd_actual": float(act.std(ddof=0)), "sd_fixed": float(fix.std(ddof=0))}


# ----------------------------------------------------------------------------- main
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(2032)
    R = {}

    # --- data and validation
    gB, wB, pde, bnames = load_bcw()
    jhs = load_jhs()
    off, off_names = load_official()
    R["coverage_bcw_share_sum"] = wB.sum().round(3).to_dict()
    R["bcw_sum_vs_pde"] = {"sum_of_contributions": ((gB * wB).sum()).round(3).to_dict(), "pde_tfp": pde.round(3).to_dict()}
    ov = jhs[(jhs.year >= 1998) & (jhs.year <= 2014)].merge(off[(off.year >= 1998) & (off.year <= 2014)],
                                                           on=["industry", "year"], suffixes=("_jhs", "_off"))
    agg_ov = ov.groupby("year")[["c_jhs", "c_off"]].sum()
    ind_mean = ov.groupby("industry")[["g_jhs", "g_off"]].mean()
    R["validation_jhs_vs_official_1998_2014"] = {
        "aggregate_annual_corr": float(agg_ov.corr().iloc[0, 1]),
        "aggregate_mean_jhs": float(agg_ov.c_jhs.mean()), "aggregate_mean_official": float(agg_ov.c_off.mean()),
        "industry_mean_growth_corr": float(ind_mean.corr().iloc[0, 1])}

    post = pd.concat([jhs[(jhs.year >= 1949) & (jhs.year <= 2014)], off[(off.year >= 2015) & (off.year <= 2024)]])
    post["sector"] = post.industry.map(JHS_SECTOR)
    aggA = post.groupby("year").c.sum()
    R["post_aggregate_by_era"] = {e: float(aggA.loc[a:b].mean()) for e, (a, b) in POST_ERAS.items()}

    # --- H1 annual low frequency, 1949-2024
    Cind = post.pivot(index="year", columns="industry", values="c").sort_index()
    Gind = post.pivot(index="year", columns="industry", values="g").sort_index()
    q = int(round(2 * len(Cind) / 25))
    Csec = post.groupby(["year", "sector"]).c.sum().unstack()[SECTORS]
    R["H1_lowfreq"] = {"q": q,
                       "industries_61": averaging_stats(Cind.values, q, rng),
                       "sectors_11": averaging_stats(Csec.values, q, rng),
                       "first_pc_industry_tfp": first_pc_share(Gind.values, q, rng)}
    # sub-periods and a no-splice check (Jorgenson-Ho-Samuels only)
    for lab, (a, b) in {"1949-1986": (1949, 1986), "1987-2024": (1987, 2024), "1949-2014_jhs_only": (1949, 2014)}.items():
        sub = Cind.loc[a:b].values
        R["H1_lowfreq"][f"industries_{lab}"] = averaging_stats(sub, int(round(2 * len(sub) / 25)), rng, reps=500)

    # --- era panels
    E = era_table(post, POST_ERAS)
    gP = E.pivot(index="industry", columns="era", values="g")[list(POST_ERAS)]
    wP = E.pivot(index="industry", columns="era", values="w")[list(POST_ERAS)]
    dP = E.pivot(index="industry", columns="era", values="d")[list(POST_ERAS)]
    cP = E.pivot(index="industry", columns="era", values="c")[list(POST_ERAS)]
    gPva = cP / wP  # value-added TFP (Domar-weighted gross-output TFP = VA-share-weighted VA TFP)
    # broad sectors across all 8 eras: contributions and VA shares
    cB = (gB * wB)
    secB_c = cB.groupby(cB.index.map(BCW_SECTOR)).sum().reindex(SECTORS)
    secB_w = wB.groupby(wB.index.map(BCW_SECTOR)).sum().reindex(SECTORS)
    secP_c = cP.groupby(cP.index.map(JHS_SECTOR)).sum().reindex(SECTORS)
    secP_w = wP.groupby(wP.index.map(JHS_SECTOR)).sum().reindex(SECTORS)
    sec_c = pd.concat([secB_c, secP_c], axis=1)
    sec_w = pd.concat([secB_w, secP_w], axis=1)
    sec_g = sec_c / sec_w
    # aggregate of the covered economy in each era (contributions / covered share)
    agg_era = sec_c.sum() / sec_w.sum()
    R["eras"] = {"aggregate_tfp_covered": agg_era.round(3).to_dict(), "covered_share": sec_w.sum().round(3).to_dict(),
                 "sector_tfp": sec_g.round(2).to_dict(), "sector_contribution": sec_c.round(3).to_dict(),
                 "sector_share": sec_w.round(3).to_dict()}
    # H1 across eras (normalize contributions by covered share so pre/post are comparable)
    secN = (sec_c / sec_w.sum()).T.values  # eras x sectors
    R["H1_eras"] = {"all_8_eras_11_sectors": averaging_stats(np.nan_to_num(secN), None, rng, reps=5000, low_freq=False),
                    "prewar_4_eras_38_industries": averaging_stats((gB * wB).T.values, None, rng, reps=5000, low_freq=False),
                    "postwar_4_eras_61_industries": averaging_stats(cP.T.values, None, rng, reps=5000, low_freq=False)}

    # --- H2 relay
    R["H2_rank_persistence"] = {"prewar_industries": rank_persistence(gB), "postwar_industries": rank_persistence(gPva),
                                "postwar_industries_gross_output_tfp": rank_persistence(gP),
                                "sectors_all_eras": rank_persistence(sec_g)}
    R["H2_concentration"] = {**{e: concentration(cB[e].rename(index=bnames)) for e in PRE_ERAS},
                             **{e: concentration(cP[e].rename(index=dict(enumerate(off_names, 1)))) for e in POST_ERAS}}

    conc = pd.DataFrame(R["H2_concentration"]).T
    conc["share_positive"] = conc.n_positive / conc.n
    R["H2_concentration_vs_aggregate"] = {
        "corr_aggregate_top5share": float(np.corrcoef(conc["aggregate"].astype(float), conc.top5_share.astype(float))[0, 1]),
        "corr_aggregate_share_positive": float(np.corrcoef(conc["aggregate"].astype(float), conc.share_positive.astype(float))[0, 1]),
        "share_positive_by_era": conc.share_positive.astype(float).round(2).to_dict()}

    # --- H3 Baumol
    R["H3_baumol_share_response"] = {"prewar_va_shares": baumol(gB, wB), "postwar_va_shares": baumol(gPva, wP),
                                     "postwar_domar_gross_output_tfp": baumol(gP, dP), "sectors_all_eras": baumol(sec_g, sec_w)}
    R["H3_fixed_weights"] = {"prewar": fixed_weight(gB, wB), "postwar": fixed_weight(gPva, wP)}
    # annual low-frequency version: actual vs weights frozen at 1949
    d49 = post[post.year == 1949].set_index("industry").dbar
    fixed_ann = Gind.mul(d49, axis=1).sum(1)
    R["H3_lowfreq_fixed_1949_weights"] = {
        "lf_sd_actual": float(B.lf_dev(aggA.values, q).std()), "lf_sd_fixed": float(B.lf_dev(fixed_ann.values, q).std()),
        "mean_actual": float(aggA.mean()), "mean_fixed": float(fixed_ann.mean())}
    # annual LF: do industries with faster TFP growth see falling Domar weights? pooled LF slope
    dlogd = np.log(post.pivot(index="year", columns="industry", values="d")).diff().loc[1950:]
    gg = Gind.loc[1950:]
    sl = []
    for k in gg.columns:
        r = lowfreq.regression(dlogd[k].values * 100, gg[k].values[:, None], q, ["g"])
        sl.append(r["coef"]["g"])
    R["H3_lowfreq_share_response"] = {"median_slope": float(np.median(sl)), "share_negative": float(np.mean(np.array(sl) < 0)),
                                      "n": len(sl)}

    # --- H4 broadness of accelerations / slowdowns (broad sectors; shift-share)
    def change(e0, e1):
        dg = sec_g[e1] - sec_g[e0]
        wm = 0.5 * (sec_w[e0] / sec_w[e0].sum() + sec_w[e1] / sec_w[e1].sum())
        within = (wm * dg)
        total = float(agg_era[e1] - agg_era[e0])
        return {"aggregate_change": total, "within_sum": float(within.sum()),
                "share_of_sectors_moving_with_aggregate": float(np.mean(np.sign(dg.dropna()) == np.sign(total))),
                "within_by_sector": within.round(3).to_dict(),
                "top2_share_of_within": float(within.reindex(within.abs().sort_values(ascending=False).index).iloc[:2].sum()
                                              / within.sum())}
    R["H4_changes"] = {"1909-1919 -> 1919-1929": change("1909-1919", "1919-1929"),
                       "1899-1909 -> 1919-1929": change("1899-1909", "1919-1929"),
                       "1919-1929 -> 1929-1941": change("1919-1929", "1929-1941"),
                       "1929-1941 -> 1948-1973": change("1929-1941", "1948-1973"),
                       "1909-1919 -> 1948-1973": change("1909-1919", "1948-1973"),
                       "1948-1973 -> 1973-1995": change("1948-1973", "1973-1995"),
                       "1973-1995 -> 1995-2007": change("1973-1995", "1995-2007"),
                       "1995-2007 -> 2007-2024": change("1995-2007", "2007-2024")}

    ex = load_beabls_experimental()
    ex = ex[(ex.year >= 1964) & (ex.year <= 2016)]
    Cex = ex.pivot(index="year", columns="industry", values="c").sort_index()
    qx = int(round(2 * len(Cex) / 25))
    ov2 = ex.merge(post, on=["industry", "year"], suffixes=("_ex", "_main"))
    R["robustness_beabls_experimental_1964_2016"] = {
        "q": qx, "industries_61": averaging_stats(Cex.values, qx, rng, reps=500),
        "main_same_years": averaging_stats(Cind.loc[1964:2016].values, qx, rng, reps=500),
        "aggregate_annual_corr_with_main": float(ov2.groupby("year")[["c_ex", "c_main"]].sum().corr().iloc[0, 1]),
        "aggregate_mean_ex": float(Cex.sum(1).mean()), "aggregate_mean_main": float(Cind.loc[1964:2016].sum(1).mean())}

    with open(OUT / "results.json", "w") as f:
        json.dump(R, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    figures(R, sec_c, sec_w, Cind, q)
    print("done: output/sectoral/results.json")


def figures(R, sec_c, sec_w, Cind, q):
    P = plots
    src = "Sources: Bakker–Crafts–Woltjer (2019); Jorgenson–Ho–Samuels US KLEMS (2017); BEA–BLS integrated industry accounts (2026)."
    eras = list(sec_c.columns)
    # S1: era aggregate TFP growth, stacked sector contributions (normalized to covered economy)
    N = sec_c / sec_w.sum()
    cols = ["#1f4e79", "#2e75b6", "#8db8ea", "#c55a11", "#f4b183", "#7f7f7f", "#bfbfbf", "#548235", "#a9d18e", "#7030a0", "#d9b3ff"]
    fig, ax = P.setup(figsize=(11, 5.6))
    x = np.arange(len(eras))
    pos = np.zeros(len(eras))
    neg = np.zeros(len(eras))
    for s, col in zip(SECTORS, cols):
        v = N.loc[s].fillna(0).values
        ax.bar(x, np.where(v > 0, v, 0), 0.62, bottom=pos, color=col, label=s)
        ax.bar(x, np.where(v < 0, v, 0), 0.62, bottom=neg, color=col)
        pos += np.where(v > 0, v, 0)
        neg += np.where(v < 0, v, 0)
    ax.plot(x, N.sum().values, color="black", marker="o", lw=1.6, label="Aggregate")
    ax.axhline(0, color="#999999", lw=0.8)
    ax.axvline(3.5, color="#999999", lw=0.8, ls=(0, (3, 3)))
    ax.text(3.55, ax.get_ylim()[1] * 0.92, "value-added TFP (BCW) | gross-output TFP, Domar (KLEMS)", fontsize=8, color="#555555")
    ax.set_xticks(x)
    ax.set_xticklabels(eras, fontsize=9)
    ax.set_ylabel("Contribution to aggregate TFP growth, % per year", color="#555555")
    ax.legend(frameon=False, fontsize=7.5, ncol=2, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    P.titles(fig, "Fast eras were broad-based; slow eras rested on a few industries", "US industry contributions to aggregate TFP growth by era, 1899–2024", src)
    P.save(fig, FIG / "s1_contributions_by_era.png")

    # S2: aggregate SD vs independent and synchronized benchmarks
    H = R["H1_lowfreq"]
    He = R["H1_eras"]
    rows = [("61 industries, annual 1949–2024\n(low frequency)", H["industries_61"]),
            ("11 sectors, annual 1949–2024\n(low frequency)", H["sectors_11"]),
            ("38 industries, 4 pre-war eras", He["prewar_4_eras_38_industries"]),
            ("61 industries, 4 post-war eras", He["postwar_4_eras_61_industries"]),
            ("11 sectors, all 8 eras", He["all_8_eras_11_sectors"])]
    fig, ax = P.setup(figsize=(10.5, 5.2))
    y = np.arange(len(rows))
    for k, (lab, h) in enumerate(rows):
        ax.plot([h["sd_independent"], h["sd_synchronized"]], [k, k], color="#cccccc", lw=6, solid_capstyle="round")
        ax.plot(h["sd_independent"], k, "|", color=P.GREY, ms=18, mew=2)
        ax.plot(h["sd_synchronized"], k, "|", color=P.DARK, ms=18, mew=2)
        ax.plot(h["sd_aggregate"], k, "o", color=P.RED, ms=9)
    ax.plot([], [], "|", color=P.GREY, ms=12, mew=2, label="If industries were independent")
    ax.plot([], [], "|", color=P.DARK, ms=12, mew=2, label="If all industries moved together")
    ax.plot([], [], "o", color=P.RED, ms=8, label="Actual aggregate")
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel("Standard deviation of aggregate TFP growth (pp)", color="#555555")
    ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    P.titles(fig, "Aggregate swings sit near the independent-industries benchmark, and never below it", "Swings in aggregate TFP growth vs two benchmarks built from the industries' own swings", src)
    P.save(fig, FIG / "s2_averaging_benchmarks.png")


if __name__ == "__main__":
    main()
