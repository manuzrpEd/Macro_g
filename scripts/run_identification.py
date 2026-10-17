"""Endogeneity checks for the main results (run after scripts/run_all.py).

Step 1  Trade costs instead of trade volumes: inverse-gravity (Novy) trade costs from
        CEPII TRADHIST bilateral flows, turned into an integration index.
Step 2  Integration shocks not caused by frontier growth: foreign tariffs (instrument),
        the 1967-75 Suez Canal closure, and the 1919-26 scientific boycott of German science.
Step 3  Controls for confounders: US unemployment (Depression), US military spending
        (war mobilization), US electricity per person (electrification wave).
Step 4  Drop the world wars and the 1940s.
Step 5  Lead-lag: does integration move before or after frontier growth?

Outputs: output/results_identification.json and output/figures/fig1x_*.png
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from frontier import config as C  # noqa: E402
from frontier import data, lowfreq, model, plots  # noqa: E402
from frontier import envelope as E  # noqa: E402
from frontier import identification as ID  # noqa: E402
from frontier import integration as I  # noqa: E402

WAR_WINDOWS = [(1914, 1919), (1939, 1949)]
SERIES = {"max": "Frontier GDP per capita", "us": "US GDP per capita", "tfp_us": "US TFP",
          "tfp_top5": "Top-5 TFP", "followers": "Followers' GDP per capita"}
RAW = C.RAW


def load_growth():
    g = pd.read_csv(C.PROCESSED / "frontier_growth.csv", index_col=0)
    p = pd.read_csv(C.PROCESSED / "integration_pool.csv", index_col=0)
    return g, p


# ----------------------------------------------------------------------------- controls (step 3)
def us_unemployment():
    j = pd.read_stata(RAW / C.SOURCES["jst"][0])
    return j[j.iso == "USA"].set_index("year")["unemp"].astype(float)


def us_electricity_per_capita(mad):
    chat = pd.read_csv(RAW / "chat.csv", low_memory=False)
    old = chat[chat.country_name == "United States"].set_index("year")["elecprod"].dropna() / 1e9  # TWh
    owid = pd.read_csv(RAW / "owid_electricity_generation.csv")
    new = owid[owid.code == "USA"].set_index("year").iloc[:, -1].astype(float)
    overlap = old.index.intersection(new.index)
    ratio = (new[overlap] / old[overlap]).mean()
    s = pd.concat([old[old.index < overlap.min()] * ratio, new]).sort_index()
    s = s[~s.index.duplicated()]
    s = s.reindex(range(int(s.index.min()), int(s.index.max()) + 1))
    s = np.exp(np.log(s).interpolate(limit_area="inside"))  # CHAT has a few missing years
    pop = mad[mad.iso == "USA"].set_index("year")["pop"]
    return (s / pop).dropna()


def us_military_share():
    """US military expenditure / GDP from Correlates of War NMC (milex, thousands of current USD)."""
    path = RAW / "cow_nmc" / "NMC-70-abridged.csv"
    if not path.exists():
        return None
    nmc = pd.read_csv(path)
    us = nmc[nmc.stateabb == "USA"].set_index("year")["milex"].astype(float)
    us = us[us >= 0] * 1e3
    # COW reports thousands of current GBP before 1914 and thousands of USD from 1914.
    us[us.index < 1914] *= 4.8665  # gold-standard parity, USD per GBP
    j = pd.read_stata(RAW / C.SOURCES["jst"][0])
    gdp = j[j.iso == "USA"].set_index("year")["gdp"].astype(float) * 1e9  # JST: billions of USD
    return (us / gdp).dropna()


# ----------------------------------------------------------------------------- main
def main():
    R = {}
    g, pool = load_growth()
    mad = data.load_maddison()
    yrs = np.arange(1871, C.END + 1)

    def series(k, years):
        y = g[k].reindex(years)
        return y

    # ---------------- Step 4: neutralize the wars and the 1940s
    R["step4_no_wars"] = {}
    for k in SERIES:
        y = series(k, yrs)
        ok = y.notna().values
        yy = yrs[ok]
        yn = ID.neutralize(y[ok], WAR_WINDOWS)
        Xn = np.column_stack([ID.neutralize(pool.loc[yy, c], WAR_WINDOWS) for c in ("g_scale", "g_int")])
        X = pool.loc[yy, ["g_scale", "g_int"]].values
        base = lowfreq.regression(y[ok].values, X, C.LF_Q, ["g_scale", "g_int"])
        neut = lowfreq.regression(yn.values, Xn, C.LF_Q, ["g_scale", "g_int"])
        R["step4_no_wars"][k] = {"baseline": base, "wars_neutralized": neut}
    # Episode means with the whole 1939-49 decade dropped as well as WWI.
    drop = [y for a, b in WAR_WINDOWS for y in range(a, b + 1)]
    R["step4_episode_means"] = {}
    for k in SERIES:
        y = g[k].dropna()
        y = y[(y.index > 1870) & ~y.index.isin(drop)]
        X = pd.DataFrame({"const": 1.0,
                          "Closure": ((y.index >= 1914) & (y.index <= 1949)).astype(float),
                          "Re-integration": ((y.index >= 1950) & (y.index <= 1994)).astype(float),
                          "Internet": (y.index >= 1995).astype(float)}, index=y.index)
        m = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
        R["step4_episode_means"][k] = {
            "baseline": float(m.params["const"]),
            **{n: {"diff": float(m.params[n]), "p": float(m.pvalues[n])} for n in X.columns if n != "const"}}

    # ---------------- Step 5: lead-lag
    R["step5_lead_lag"] = {}
    lags = list(range(-20, 21))
    for k in SERIES:
        y = series(k, yrs)
        ok = y.notna().values
        yy = yrs[ok]
        gi = pool.loc[yy, "g_int"].values
        ll = ID.lead_lag(y[ok].values, gi, C.LF_Q, lags)
        # Joint regression on integration 10 years earlier (lag) and 10 years later (lead).
        L = 10
        yv = y[ok].values[L:-L]
        Xj = np.column_stack([pool.loc[yy, "g_scale"].values[L:-L], gi[:-2 * L], gi[2 * L:]])
        reg = lowfreq.regression(yv, Xj, 10, ["g_scale", "g_int_10y_earlier", "g_int_10y_later"])
        R["step5_lead_lag"][k] = {"corr_by_k": ll, "peak_k": int(max(ll, key=lambda a: abs(ll[a]))),
                                  "joint_regression": reg}

    # ---------------- Step 3: controls for confounders (common window)
    u = us_unemployment()
    el = us_electricity_per_capita(mad)
    mil = us_military_share()
    ctrl = pd.DataFrame({"d_unemp": u.diff(), "g_elec": 100 * np.log(el).diff()})
    if mil is not None:
        ctrl["d_milshare"] = 100 * mil.diff()
    ctrl = ctrl.dropna()
    cy = np.arange(max(1903, int(ctrl.index.min())), min(2020, int(ctrl.index.max())) + 1)
    q3 = int(round(2 * len(cy) / 25))
    R["step3_controls"] = {"years": [int(cy[0]), int(cy[-1])], "q": q3, "controls": list(ctrl.columns)}
    for k in SERIES:
        y = g[k].reindex(cy)
        if y.isna().any():
            continue
        X0 = pool.loc[cy, ["g_scale", "g_int"]].values
        Xc = np.column_stack([X0, ctrl.loc[cy].values])
        names = ["g_scale", "g_int"] + list(ctrl.columns)
        R["step3_controls"][k] = {
            "no_controls": lowfreq.regression(y.values, X0, q3, ["g_scale", "g_int"]),
            "with_controls": lowfreq.regression(y.values, Xc, q3, names),
            "with_controls_wars_neutralized": lowfreq.regression(
                ID.neutralize(y, WAR_WINDOWS).values,
                np.column_stack([ID.neutralize(pd.Series(Xc[:, j], index=cy), WAR_WINDOWS).values
                                 for j in range(Xc.shape[1])]), q3, names)}

    # ---------------- Steps 1-2 (trade costs and exogenous shocks) are added by steps12()
    R.update(steps12(g, pool, mad))

    with open(C.ROOT / "output" / "results_identification.json", "w") as f:
        json.dump(R, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    figures(R, g, pool)
    print("done: output/results_identification.json")


def _share_weighted_change(M, P, i, t, exclude_self=True):
    """sum_j s_ij,t-1 * (M[t,i,j] - M[t-1,i,j]) with partner weights s from population P."""
    js = [j for j in range(M.shape[1]) if not (exclude_self and j == i)]
    prev, cur = M[t - 1, i, js], M[t, i, js]
    w = P[t - 1, js]
    ok = np.isfinite(prev) & np.isfinite(cur) & np.isfinite(w)
    if not ok.any():
        return np.nan
    return float((w[ok] / w[ok].sum()) @ (cur[ok] - prev[ok]))


def steps12(g, pool, mad):
    from frontier import tradecosts as TC
    out = {}
    cc = C.CORE
    yrs = np.arange(1870, 2015)
    panel = TC.bilateral_panel()
    panel.to_csv(C.PROCESSED / "bilateral_trade_costs.csv", index=False)
    jmn = TC.jmn_tau()
    chk = panel.merge(jmn, on=["i", "j", "year"]).dropna(subset=["ltau", "tc8"])
    out["step1_validation_vs_JMN"] = {"pairs_years": int(len(chk)),
                                      "corr_levels": float(np.corrcoef(np.expm1(chk.ltau), chk.tc8)[0, 1])}
    tar = TC.country_tariffs()
    pred, fey_coefs = TC.feyrer_prediction(panel)
    sea_changes = panel.sort_values(["i", "j", "year"]).groupby(["i", "j"])["sea"].apply(
        lambda s: (s.diff().abs() > 1).any())
    suez = TC.suez_first_stage(panel)
    suez["n_pairs_exposed"] = int(sea_changes.sum())
    out["step2_suez_first_stage"] = suez
    out["step2_feyrer_coefs"] = fey_coefs

    LT = TC.to_matrix(panel, "ltau")
    PR = TC.to_matrix(pred, "pred_ltau")
    SE = TC.to_matrix(panel.assign(lsea=np.log(panel.sea)), "lsea")
    pop = E.wide(mad, "pop", cc, yrs).values
    TF = np.log1p(tar.pivot(index="year", columns="iso", values="tariff").reindex(index=yrs, columns=cc).values)
    hub = cc.index(C.HUB)

    # ---- country-level annual series: integration growth and instruments (x100, log points)
    rows = []
    for t in range(1, len(yrs)):
        for i, iso in enumerate(cc):
            tf = np.broadcast_to(TF[:, None, :], (len(yrs), len(cc), len(cc)))
            rows.append({
                "iso": iso, "year": int(yrs[t]),
                "x_int": -100 * _share_weighted_change(LT, pop, i, t),
                "z_tariff": -100 * _share_weighted_change(tf, pop, i, t),
                "z_feyrer": -100 * _share_weighted_change(PR, pop, i, t),
                "z_suez": -100 * _share_weighted_change(SE, pop, i, t),
                "scale": 100 * _share_weighted_change(np.broadcast_to(np.log(pop)[:, None, :], LT.shape), pop, i, t),
            })
    cy = pd.DataFrame(rows)
    cy.to_csv(C.PROCESSED / "country_integration_instruments.csv", index=False)

    # ---- frontier pool with trade-cost weights: w_i = 1 / (1 + tau_i,US), hub = 1
    O_tc = pd.DataFrame(np.exp(-LT[:, :, hub]), index=yrs, columns=cc)
    O_tc[C.HUB] = 1.0
    S = E.wide(mad, "pop", cc, yrs)
    pool_tc = I.pool_growth(S, O_tc, 1.0)
    w = O_tc.values * S.values
    share = w / np.nansum(w, axis=1, keepdims=True)
    dtar = np.vstack([np.full(len(cc), np.nan), np.diff(TF, axis=0)])
    dpred = np.vstack([np.full(len(cc), np.nan), np.diff(PR[:, :, hub], axis=0)])
    nonhub = [k for k in range(len(cc)) if k != hub]
    z_front = pd.DataFrame(index=yrs)
    for name, D in [("z_tariff", dtar), ("z_feyrer", dpred)]:
        vals = []
        for t in range(len(yrs)):
            if t == 0:
                vals.append(np.nan)
                continue
            s_prev = share[t - 1, nonhub]
            d = D[t, nonhub]
            ok = np.isfinite(s_prev) & np.isfinite(d)
            vals.append(-100 * float((s_prev[ok] / s_prev[ok].sum()) @ d[ok]) if ok.any() else np.nan)
        z_front[name] = vals
    z_front["g_int_tc"] = pool_tc["g_int"]
    z_front["g_scale_tc"] = pool_tc["g_scale"]
    z_front.to_csv(C.PROCESSED / "frontier_tradecost_pool.csv")

    # ---- Step 1: frontier regressions with trade-cost integration
    fy = np.arange(1871, 2015)
    out["step1_frontier_tradecost"] = {}
    u, el, mil = us_unemployment(), us_electricity_per_capita(mad), us_military_share()
    ctrl = pd.DataFrame({"d_unemp": u.diff(), "g_elec": 100 * np.log(el).diff(),
                         "d_milshare": 100 * mil.diff()})
    for k in SERIES:
        y = g[k].reindex(fy)
        ok = y.notna().values
        yy = fy[ok]
        X = z_front.loc[yy, ["g_scale_tc", "g_int_tc"]].values
        res = {"ols": lowfreq.regression(y[ok].values, X, C.LF_Q, ["g_scale", "g_int_tc"]),
               "ols_wars_neutralized": lowfreq.regression(
                   ID.neutralize(y[ok], WAR_WINDOWS).values,
                   np.column_stack([ID.neutralize(z_front.loc[yy, c], WAR_WINDOWS).values
                                    for c in ("g_scale_tc", "g_int_tc")]), C.LF_Q, ["g_scale", "g_int_tc"])}
        # ---- Step 2: instrument trade-cost integration with foreign tariffs and Feyrer geography
        Z = z_front.loc[yy, ["z_tariff", "z_feyrer"]].values
        res["iv"] = ID.lf_iv(y[ok].values, z_front.loc[yy, "g_int_tc"].values, Z, C.LF_Q,
                             W=z_front.loc[yy, ["g_scale_tc"]].values, names=["g_int_tc", "g_scale"])
        # IV + controls + wars neutralized on the common control window
        cyrs = np.array([t for t in yy if t >= 1903 and t in ctrl.dropna().index])
        if len(cyrs) > 60:
            q = int(round(2 * len(cyrs) / 25))
            neu = lambda s: ID.neutralize(pd.Series(s, index=cyrs), WAR_WINDOWS).values  # noqa: E731
            Wc = np.column_stack([neu(z_front.loc[cyrs, "g_scale_tc"].values)] +
                                 [neu(ctrl.loc[cyrs, c].values) for c in ctrl.columns])
            res["iv_controls_wars_neutralized"] = ID.lf_iv(
                neu(g[k].reindex(cyrs).values), neu(z_front.loc[cyrs, "g_int_tc"].values),
                np.column_stack([neu(z_front.loc[cyrs, c].values) for c in ("z_tariff", "z_feyrer")]), q,
                W=Wc, names=["g_int_tc", "g_scale"] + list(ctrl.columns))
            res["iv_controls_wars_neutralized"]["years"] = [int(cyrs[0]), int(cyrs[-1])]
        out["step1_frontier_tradecost"][k] = res

    # ---- Step 2b: country panel, 5-year periods, country and period fixed effects
    bcl = data.load_bcl()
    lv = {"tfp": bcl.pivot(index="year", columns="iso", values="tfp").reindex(columns=cc),
          "gdppc": E.wide(mad, "gdppc", cc)}
    cy["period"] = (cy.year - 1871) // 5
    war_periods = cy[cy.year.isin([yr for a, b in WAR_WINDOWS for yr in range(a, b + 1)])].period.unique()
    agg = cy.groupby(["iso", "period"]).agg(start=("year", "min"), end=("year", "max"), n=("year", "size"),
                                            x_int=("x_int", "mean"), z_tariff=("z_tariff", "mean"),
                                            z_feyrer=("z_feyrer", "mean"), z_suez=("z_suez", "mean"),
                                            scale=("scale", "mean")).reset_index()
    agg = agg[(agg.n >= 4) & ~agg.period.isin(war_periods)]
    out["step2_panel"] = {"periods_dropped_for_wars": sorted(int(p) for p in war_periods)}
    for var, L in lv.items():
        d = agg.copy()
        logL = np.log(L)
        d["y"] = [100 * (logL.at[e, iso] - logL.at[s - 1, iso]) / (e - s + 1)
                  if (s - 1) in logL.index and e in logL.index else np.nan
                  for iso, s, e in zip(d.iso, d.start, d.end)]
        # Distance to the frontier: log GDP per capita of the US minus own, at the period start
        # (cross-country TFP levels are not reliably comparable, so GDP per capita is used for both).
        gdp_l = np.log(lv["gdppc"])
        d["gap"] = [gdp_l.at[s - 1, C.HUB] - gdp_l.at[s - 1, iso] if (s - 1) in gdp_l.index else np.nan
                    for iso, s in zip(d.iso, d.start)]
        d = d.dropna(subset=["y", "gap", "x_int", "z_tariff", "z_feyrer"])
        d["x_gap"] = d.x_int * d.gap
        d["zt_gap"], d["zf_gap"] = d.z_tariff * d.gap, d.z_feyrer * d.gap
        base = ID.panel_iv(d, "y", ["x_int"], ["z_tariff", "z_feyrer"], exog=["scale", "gap"])
        inter = ID.panel_iv(d, "y", ["x_int", "x_gap"], ["z_tariff", "z_feyrer", "zt_gap", "zf_gap"],
                            exog=["scale", "gap"])
        med_gap = float(d.loc[d.iso != C.HUB, "gap"].median())
        b, V = np.array([inter["coef"]["x_int"], inter["coef"]["x_gap"]]), np.array(inter["vcov"])[:2, :2]
        at = {}
        for label, gp in [("at_frontier_gap0", 0.0), ("at_median_follower_gap", med_gap)]:
            a = np.array([1.0, gp])
            est, se = float(a @ b), float(np.sqrt(a @ V @ a))
            at[label] = {"gap": gp, "effect": est, "se": se,
                         "p": float(2 * __import__("scipy").stats.t.sf(abs(est / se), inter["clusters"] - 1))}
        for r in (base, inter):
            r.pop("vcov", None)
        out["step2_panel"][var] = {"n_obs": base["n"], "years": [int(d.start.min()), int(d.end.max())],
                                   "pooled": base, "with_gap_interaction": inter, "effects": at}

    # ---- Step 2c: WWI scientific boycott of German science (1919-1926): size of the pool shock
    sh = pd.DataFrame(share, index=yrs, columns=cc)
    s_de = float(sh.loc[1918, "DEU"])
    out["step2_boycott"] = {"german_share_of_effective_pool_1918": s_de,
                            "pool_level_drop_log_points": float(100 * np.log(1 - s_de))}
    return out


def figures(R, g, pool):
    P = plots
    # F10 trade costs and foreign tariffs
    import matplotlib.pyplot as plt
    bp = pd.read_csv(C.PROCESSED / "bilateral_trade_costs.csv")
    med = bp.groupby("year").ltau.median().pipe(np.expm1) * 100
    us = bp[(bp.i == C.HUB) | (bp.j == C.HUB)].groupby("year").ltau.median().pipe(np.expm1) * 100
    from frontier import tradecosts as TC
    tar = TC.country_tariffs()
    ftar = tar[tar.iso != C.HUB].groupby("year").tariff.median() * 100
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), dpi=150)
    for ax in axes:
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        ax.grid(axis="y", color="#e6e6e6")
        ax.tick_params(colors="#555555", length=0)
        for a, b, lab in C.EPISODES[1:2]:
            ax.axvspan(a, b, color=P.LIGHT, zorder=0)
    axes[0].plot(med.index, med, color=P.GREY, lw=1.6, label="All pairs (median)")
    axes[0].plot(us.index, us, color=P.BLUE, lw=2, label="Pairs with the US (median)")
    axes[0].set_title("Bilateral trade costs, tariff equivalent %", fontsize=10, color="#333333", loc="left")
    axes[0].legend(frameon=False, fontsize=8.5)
    axes[1].plot(ftar.index, ftar, color=P.BLUE, lw=2)
    axes[1].set_title("Tariffs of the other 15 economies (median), %", fontsize=10, color="#333333", loc="left")
    P.titles(fig, "Trade costs and tariffs rose in the closure and fell after 1950",
             "Left: inverse-gravity trade costs (Novy), σ = 8. Right: customs revenue / imports (held flat after the data end, ~1996). Shaded: 1914–1949.",
             "Sources: CEPII TRADHIST v4; Jacks–Meissner–Novy (2011) incl. Clemens–Williamson tariffs.")
    P.save(fig, C.FIGURES / "fig10_trade_costs_tariffs.png")

    # F11 lead-lag
    fig, ax = P.setup()
    for k, name, col in [("max", "Frontier GDP per capita", P.BLUE), ("tfp_us", "US TFP", P.RED)]:
        ll = R["step5_lead_lag"][k]["corr_by_k"]
        kk = sorted(int(a) for a in ll)
        ax.plot(kk, [ll[a] for a in kk], color=col, lw=2, label=name)
    ax.axhline(0, color="#999999", lw=0.8)
    ax.axvline(0, color="#bbbbbb", lw=0.8)
    ax.text(-19.5, 0.88, "← growth moves first", fontsize=8.5, color="#555555")
    ax.text(19.5, 0.88, "integration moves first →", fontsize=8.5, color="#555555", ha="right")
    ax.set_ylim(-1, 1)
    ax.set_xlabel("k: years by which integration leads growth (negative: growth leads)", color="#555555")
    ax.set_ylabel("Long-run correlation", color="#555555")
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    P.titles(fig, "Frontier income leads integration by a decade; US TFP moves against it",
             "Correlation of low-frequency growth with the integration component k years earlier",
             "Population pool, κ = 1; cosine projections with q = 12.")
    P.save(fig, C.FIGURES / "fig11_lead_lag.png")

    # F12 coefficient summary for the frontier
    rows = []
    t90 = lambda dof: __import__("scipy").stats.t.ppf(0.95, dof)  # noqa: E731
    for k, name in [("max", "Frontier GDP per capita"), ("tfp_us", "US TFP")]:
        b0 = R["step4_no_wars"][k]["baseline"]
        rows.append((name, "Trade openness, OLS (main paper)", b0["coef"]["g_int"], b0["se"]["g_int"], b0["dof"]))
        nw = R["step4_no_wars"][k]["wars_neutralized"]
        rows.append((name, "Openness, wars neutralized", nw["coef"]["g_int"], nw["se"]["g_int"], nw["dof"]))
        tc = R["step1_frontier_tradecost"][k]
        rows.append((name, "Trade costs, OLS", tc["ols"]["coef"]["g_int_tc"], tc["ols"]["se"]["g_int_tc"], tc["ols"]["dof"]))
        rows.append((name, "Trade costs, IV", tc["iv"]["coef"]["g_int_tc"], tc["iv"]["se"]["g_int_tc"], tc["iv"]["dof"]))
        if "iv_controls_wars_neutralized" in tc:
            r = tc["iv_controls_wars_neutralized"]
            rows.append((name, "Trade costs, IV + controls, no wars", r["coef"]["g_int_tc"], r["se"]["g_int_tc"], r["dof"]))
    df = pd.DataFrame(rows, columns=["series", "spec", "b", "se", "dof"])
    specs = list(dict.fromkeys(df.spec))
    fig, ax = P.setup(figsize=(10, 5.8))
    for s_i, (sname, col) in enumerate([("Frontier GDP per capita", P.BLUE), ("US TFP", P.RED)]):
        d = df[df.series == sname]
        for r in d.itertuples():
            yv = specs.index(r.spec) + (0.15 if s_i == 0 else -0.15)
            h = t90(r.dof) * r.se
            ax.plot([r.b - h, r.b + h], [yv, yv], color=col, lw=1.6)
            ax.plot(r.b, yv, "o", color=col, ms=5, label=sname if r.spec == specs[0] else None)
    ax.axvline(0, color="#999999", lw=0.8)
    ax.set_yticks(range(len(specs)))
    ax.set_yticklabels(specs, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Response of growth to the integration component (90% interval)", color="#555555")
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    ax.grid(axis="x", color="#eeeeee")
    ax.set_xlim(-4.5, 6.5)
    P.titles(fig, "No specification finds that integration raises frontier productivity",
             "Low-frequency estimates of θ (90% intervals); IV rows instrument trade costs with foreign tariffs and Feyrer geography",
             "Openness and trade-cost rows are on different scales. IV intervals are wide: 9–12 effective long-run observations, weak first stages.")
    P.save(fig, C.FIGURES / "fig12_endogeneity_summary.png")


if __name__ == "__main__":
    main()
