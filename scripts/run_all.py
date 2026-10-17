"""Full pipeline: data -> frontier envelopes -> integration pool -> tests -> figures.

Usage (from the repository root):
    python scripts/run_all.py            # uses cached raw data, downloads what is missing
    python scripts/run_all.py --quick    # fewer bootstrap / Monte Carlo replications

Outputs: data/processed/*.csv, output/tables/*.csv, output/results.json, output/figures/*.png
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from frontier import breaks, data, lowfreq, model, plots  # noqa: E402
from frontier import config as C  # noqa: E402
from frontier import envelope as E  # noqa: E402
from frontier import integration as I  # noqa: E402

YEARS = np.arange(C.START, C.END + 1)
GYEARS = YEARS[1:]  # years with a growth rate


# ----------------------------------------------------------------------------- helpers
def episode_dummies(index):
    X = pd.DataFrame(index=index)
    X["closure"] = ((index >= 1914) & (index <= 1949)).astype(float)
    X["reintegration"] = ((index >= 1950) & (index <= 1994)).astype(float)
    X["internet"] = (index >= 1995).astype(float)
    return X


def episode_test(g, split_peacetime=False):
    """Mean growth by episode relative to 1870-1913, war years dropped, HAC(5) errors."""
    y = g.dropna()
    y = y[(y.index > C.START) & (y.index <= C.END) & ~y.index.isin(C.WAR_YEARS)]
    X = episode_dummies(y.index)
    if split_peacetime:
        a, b = C.PEACETIME_CLOSURE
        X["peacetime_closure"] = ((y.index >= a) & (y.index <= b)).astype(float)
    res = sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    out = {"baseline_1870_1913": float(res.params["const"]), "n": int(res.nobs)}
    for c in X.columns:
        out[c] = {"diff": float(res.params[c]), "se": float(res.bse[c]), "p": float(res.pvalues[c])}
    return out


def lf_inputs(g, pool):
    """Align a growth series with pool regressors over the years where both exist."""
    y = g.reindex(GYEARS)
    ok = y.notna().values & pool.reindex(GYEARS)[["g_scale", "g_int"]].notna().all(axis=1).values
    yrs = GYEARS[ok]
    return yrs, y.values[ok], pool.loc[yrs, ["g_scale", "g_int"]].values


def fmt(x, d=2):
    return float(np.round(x, d))


# ----------------------------------------------------------------------------- main
def main(quick=False):
    reps_bp = 199 if quick else 999
    reps_boot = 99 if quick else 499
    reps_mc = 100 if quick else 400
    for d in (C.PROCESSED, C.FIGURES, C.TABLES):
        d.mkdir(parents=True, exist_ok=True)
    R = {"settings": {"core": C.CORE, "hub": C.HUB, "episodes": C.EPISODES, "war_years_dropped": C.WAR_YEARS,
                      "lf_q": C.LF_Q, "reps_bp": reps_bp, "reps_boot": reps_boot, "reps_mc": reps_mc}}

    # --- 1. data
    data.download_all()
    mad = data.load_maddison()
    opn = data.load_openness()
    bcl = data.load_bcl()
    bcl = bcl[bcl.year <= C.END]
    pat = data.load_patents()

    # --- 2. frontier envelopes
    rich1870 = (mad[mad.year == 1870].dropna().nlargest(8, "gdppc").iso.tolist())
    rich2022 = (mad[mad.year == 2022].dropna().nlargest(8, "gdppc").iso.tolist())
    env = {
        "max": E.envelope(mad, "gdppc", C.CORE, "max"),
        "top5": E.envelope(mad, "gdppc", C.CORE, "topk"),
        "max_broad": E.envelope(mad, "gdppc", C.BROAD, "max"),
        "max_exante": E.envelope(mad, "gdppc", rich1870, "max"),
        "max_expost": E.envelope(mad, "gdppc", rich2022, "max"),
    }
    us = mad[mad.iso == "USA"].set_index("year")
    levels = pd.DataFrame({k: v["level"] for k, v in env.items()})
    levels["us"] = us["gdppc"]
    levels["leader"] = env["max"]["leader"]
    prod = {
        "tfp_top5": E.envelope(bcl, "tfp", C.CORE, "topk")["level"],
        "lp_top5": E.envelope(bcl, "gdp_per_hour", C.CORE, "topk")["level"],
        "tfp_us": bcl[bcl.iso == "USA"].set_index("year")["tfp"],
        "lp_us": bcl[bcl.iso == "USA"].set_index("year")["gdp_per_hour"],
    }
    levels = levels.join(pd.DataFrame(prod), how="left")
    levels.to_csv(C.PROCESSED / "frontier_levels.csv")
    growth = pd.DataFrame({k: E.growth(levels[k]) for k in levels.columns if k != "leader"})
    R["leader_spells"] = [(int(a), int(b), c) for a, b, c in E.leader_spells(env["max"]["leader"])]
    R["sets"] = {"exante_1870": rich1870, "expost_2022": rich2022}

    # --- 3. integration and the effective research pool
    S_pop = E.wide(mad, "pop", C.CORE, YEARS)
    O = E.wide(opn, "open", C.CORE, YEARS)
    gdp = E.wide(mad.assign(gdp=mad.gdppc * mad["pop"]), "gdp", C.CORE, YEARS)
    pool1 = I.pool_growth(S_pop, O, 1.0)
    pool0 = I.pool_growth(S_pop, O, 0.0)
    world_open = I.world_openness(O, gdp)
    pd.DataFrame({"world_openness": world_open, "us_openness": O[C.HUB],
                  "g_eff_k1": pool1.g_eff, "g_scale": pool1.g_scale, "g_int": pool1.g_int,
                  "g_eff_k0": pool0.g_eff}).to_csv(C.PROCESSED / "integration_pool.csv")
    R["integration"] = {
        "world_openness": {str(y): fmt(world_open[y], 3) for y in (1870, 1913, 1929, 1938, 1950, 1994, 2022)},
        "pool_by_episode": {lab: {c: fmt(pool1.loc[a:b, c].mean()) for c in ("g_eff", "g_scale", "g_int")}
                            for a, b, lab in [(1871, 1913, "Globalization wave"), (1914, 1949, "Closure"),
                                              (1950, 1994, "Re-integration"), (1995, 2022, "Internet")]},
    }

    # --- 4. Fact 1: is frontier growth constant across episodes?
    ep = {}
    for k in ["max", "top5", "max_broad", "max_exante", "max_expost", "us", "tfp_top5", "lp_top5", "tfp_us", "lp_us"]:
        lv = levels[k].dropna()
        eps = [(max(a, int(lv.index.min()) + 1), b, lab) for a, b, lab in C.EPISODES]
        ep[k] = E.episode_growth(lv, eps).set_index("episode")["growth"].round(2).to_dict()
    pd.DataFrame(ep).to_csv(C.TABLES / "episode_growth.csv")
    R["episode_growth"] = ep

    R["episode_tests"] = {k: episode_test(growth[k]) for k in
                          ["max", "top5", "us", "tfp_top5", "lp_top5", "tfp_us", "lp_us"]}
    R["episode_tests_peacetime"] = {k: episode_test(growth[k], split_peacetime=True) for k in
                                    ["max", "us", "tfp_top5", "tfp_us"]}

    R["breaks"] = {}
    for k in ["max", "top5", "us", "tfp_top5", "tfp_us"]:
        y = growth[k].reindex(GYEARS)
        keep = y.notna().values & ~np.isin(GYEARS, C.WAR_YEARS)
        R["breaks"][k] = breaks.bai_perron(y.values[keep], GYEARS[keep], max_breaks=4, reps=reps_bp, seed=1)
        R["breaks"][k].pop("all_solutions_raw", None)

    # --- 5. Long-run co-movement with integration (Mueller-Watson cosine regressions)
    R["lowfreq"] = {}
    for k in ["max", "top5", "us", "tfp_top5", "lp_top5", "tfp_us"]:
        yrs, y, X = lf_inputs(growth[k], pool1)
        reg = lowfreq.regression(y, X, C.LF_Q, ["g_scale", "g_int"])
        reg["corr_int"] = lowfreq.correlation(y, X[:, 1], C.LF_Q)
        reg["years"] = [int(yrs[0]), int(yrs[-1])]
        R["lowfreq"][k] = reg
    # world openness growth as the integration regressor
    wog = 100 * np.log(world_open).diff()
    yrs, y, X = lf_inputs(growth["max"], pool1)
    R["lowfreq"]["max_world_openness"] = lowfreq.regression(
        y, np.column_stack([X[:, 0], wog.reindex(yrs).values]), C.LF_Q, ["g_scale", "g_world_open"])

    # --- 6. Followers placebo: catch-up growth should respond more to integration
    fol = [c for c in C.CORE if c != C.HUB]
    fol_g = E.wide(mad, "gdppc", fol, YEARS).pipe(lambda w: 100 * np.log(w).diff()).mean(axis=1)
    growth["followers"] = fol_g
    yrs, y, X = lf_inputs(fol_g, pool1)
    R["lowfreq"]["followers"] = lowfreq.regression(y, X, C.LF_Q, ["g_scale", "g_int"])
    R["lowfreq"]["followers"]["corr_int"] = lowfreq.correlation(y, X[:, 1], C.LF_Q)
    R["episode_tests"]["followers"] = episode_test(fol_g)

    # --- 7. Identification: GDP vs productivity, undamaged vs damaged leaders
    eps_bcl = [(1891, 1913, "Globalization wave"), (1914, 1949, "Closure"),
               (1950, 1994, "Re-integration"), (1995, 2022, "Internet")]
    decomp = {}
    for iso in C.CORE:
        b = bcl[bcl.iso == iso].set_index("year")
        row = {}
        for var in ["gdppc_bcl", "gdp_per_hour", "hours_pc", "tfp"]:
            g_ep = E.episode_growth(b[var].dropna(), eps_bcl).set_index("episode")["growth"]
            for lab, v in g_ep.items():
                row[(var, lab)] = v
        decomp[iso] = row
    decomp = pd.DataFrame(decomp).T
    decomp.columns = pd.MultiIndex.from_tuples(decomp.columns)
    decomp.round(2).to_csv(C.TABLES / "decomposition_by_country.csv")
    groups = {"United States": ["USA"], "Undamaged (USA, CHE, SWE)": C.UNDAMAGED,
              "War-damaged (BEL, DEU, FRA, ITA, JPN, NLD)": C.DAMAGED}
    R["decomposition"] = {g: {f"{var}|{lab}": fmt(decomp.loc[isos, (var, lab)].mean())
                              for var in ["gdppc_bcl", "gdp_per_hour", "hours_pc", "tfp"]
                              for _, _, lab in eps_bcl} for g, isos in groups.items()}

    # --- 8. Structural model: is integration weighting supported?
    hub = list(S_pop.columns).index(C.HUB)
    struct_targets = {"max": growth["max"], "top5": growth["top5"],
                      "tfp_top5": growth["tfp_top5"] / (1 - C.CAPITAL_SHARE)}
    R["structural"] = {}
    kappas = [0, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4]
    for k, g in struct_targets.items():
        first = int(g.first_valid_index())
        yy = np.arange(first, C.END + 1)
        mod = model.Model(S_pop.reindex(yy).values, O.reindex(yy).values, hub, yy)
        gv = g.reindex(yy).values.copy()
        gv[0] = gv[1] if np.isnan(gv[0]) else gv[0]
        free = mod.fit(gv)
        profile = {str(kp): mod.fit(gv, kappa=kp)["loss"] for kp in kappas}
        # Three research pools: H0 unweighted world pool, H1 integration-weighted (kappa = 1),
        # H2 the leader's own research only.
        leader_only = model.Model(S_pop.reindex(yy)[[C.HUB]].values, O.reindex(yy)[[C.HUB]].values, 0, yy)
        # Benchmark: constant growth fits only the mean, so its loss is the data's
        # low-frequency variation.
        lf_var = float((model.moments(gv, C.LF_Q)[1:] ** 2).sum())
        comp = {"H0 world pool, unweighted (kappa=0)": mod.fit(gv, kappa=0.0)["loss"],
                "H1 integration-weighted (kappa=1)": mod.fit(gv, kappa=1.0)["loss"],
                "H2 leader's own research only": leader_only.fit(gv, kappa=0.0)["loss"],
                "Constant growth (benchmark)": lf_var}
        R["structural"][k] = {
            "years": [int(yy[0]), int(yy[-1])], "kappa_hat": fmt(free["kappa"], 3),
            "a": fmt(free["a"], 4), "beta": fmt(free["beta"], 3), "profile": profile,
            "model_comparison_loss": comp,
            "model_comparison_lf_r2": {m: fmt(1 - v / lf_var, 3) for m, v in comp.items()},
        }
        if k == "max":
            main_mod, main_g = mod, gv
    pd.DataFrame({k: v["profile"] for k, v in R["structural"].items()}).to_csv(C.TABLES / "kappa_profile.csv")

    # --- 9. Robustness of the long-run evidence
    rob = {}
    # (a) patent-based research pool, before the European Patent Office (1978)
    S_pat = E.wide(pat, "patents", C.CORE, YEARS)
    pp = I.pool_growth(S_pat.loc[:1977], O.loc[:1977], 1.0)
    yrs, y, X = lf_inputs(growth["max"].loc[:1977], pp)
    yrs, y, X = yrs[yrs >= 1885], y[yrs >= 1885], X[yrs >= 1885]
    rob["patent_pool_1885_1977"] = lowfreq.regression(y, X, 8, ["g_scale", "g_int"])
    yy = np.arange(1884, 1978)
    mod_p = model.Model(S_pat.reindex(yy).values, O.reindex(yy).values, hub, yy, q=8)
    gv = growth["max"].reindex(yy).values
    rob["patent_pool_structural"] = {"kappa_hat": fmt(mod_p.fit(gv)["kappa"], 3),
                                     "profile": {str(kp): mod_p.fit(gv, kappa=kp)["loss"] for kp in kappas}}
    # (b) Netherlands dropped (its openness series breaks in 1914-20)
    keep = [c for c in C.CORE if c != "NLD"]
    pn = I.pool_growth(S_pop[keep], O[keep], 1.0)
    yrs, y, X = lf_inputs(growth["max"], pn)
    rob["pool_without_NLD"] = lowfreq.regression(y, X, C.LF_Q, ["g_scale", "g_int"])
    # (c) hub weighted by its own openness too (no special status for the US)
    Wsym = O.copy()
    psym = I.pool_growth(S_pop, Wsym, 1.0, hub="none")
    yrs, y, X = lf_inputs(growth["max"], psym)
    rob["symmetric_hub"] = lowfreq.regression(y, X, C.LF_Q, ["g_scale", "g_int"])
    # (d) coarser / finer low-frequency cutoffs
    for q in (8, 16):
        yrs, y, X = lf_inputs(growth["max"], pool1)
        rob[f"lf_q{q}"] = lowfreq.regression(y, X, q, ["g_scale", "g_int"])
    R["robustness"] = rob

    # --- 10. How big an integration effect do the data allow, and could we detect it?
    # With fast transitional dynamics, frontier output growth responds to the integration
    # component of pool growth with coefficient theta = kappa / (beta (1 - capital share)).
    # theta = 0.5 corresponds to kappa = 1 with beta = 3 (Bloom et al. 2020).
    tcrit90 = stats.t.ppf(0.95, C.LF_Q - 2)
    R["theta_ci90"] = {}
    for k in ["max", "top5", "us", "tfp_top5", "lp_top5", "tfp_us", "followers"]:
        reg = R["lowfreq"][k]
        b, se = reg["coef"]["g_int"], reg["se"]["g_int"]
        R["theta_ci90"][k] = {"theta_hat": fmt(b), "lo": fmt(b - tcrit90 * se), "hi": fmt(b + tcrit90 * se)}

    rng = np.random.default_rng(11)
    gi = pool1["g_int"].reindex(GYEARS).values
    power = {}
    for k in ["max", "tfp_top5"]:
        y = growth[k].reindex(GYEARS)
        ok = y.notna().values
        yv, giv, yrs_k = y.values[ok], gi[ok], GYEARS[ok]
        e = yv - yv.mean()
        Xlf = pool1.reindex(yrs_k)[["g_scale", "g_int"]].values
        keep_ep = ~np.isin(yrs_k, C.WAR_YEARS)
        Xep = sm.add_constant(episode_dummies(pd.Index(yrs_k[keep_ep])))
        power[k] = {}
        for theta in [0.0, 0.25, 0.5, 0.75, 1.0]:
            rej_lf = rej_ep = 0
            for _ in range(reps_mc):
                yb = yv.mean() + theta * (giv - giv.mean()) + breaks.block_bootstrap(e, 10, rng)
                rej_lf += lowfreq.regression(yb, Xlf, C.LF_Q, ["s", "i"])["t"]["i"] > tcrit90
                o = sm.OLS(yb[keep_ep], Xep).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
                rej_ep += (o.params["closure"] < 0) and (o.pvalues["closure"] / 2 < 0.05)
            slow = theta * (giv[(yrs_k >= 1914) & (yrs_k <= 1949)].mean() - giv[yrs_k <= 1913].mean())
            power[k][str(theta)] = {"lowfreq_t": rej_lf / reps_mc, "closure_dummy": rej_ep / reps_mc,
                                    "implied_closure_slowdown_pp": fmt(slow)}
    R["power"] = power

    # --- 11. Counterfactuals with the structural model
    cf = {}
    yrs_m = main_mod.years
    O_m = main_mod.O.copy()
    i1913 = int(np.where(yrs_m == 1913)[0][0])
    O_noclose = O_m.copy()
    win = (yrs_m >= 1914) & (yrs_m <= 1949)
    O_noclose[win] = O_m[i1913]
    # Forward scenario: extend 2023-2062 with recent population growth.
    H = 40
    fut = np.arange(C.END + 1, C.END + H + 1)
    g_pop = np.log(main_mod.S[-1] / main_mod.S[-11]) / 10
    S_ext = np.vstack([main_mod.S, main_mod.S[-1] * np.exp(np.outer(np.arange(1, H + 1), g_pop))])
    O_base = np.vstack([O_m, np.repeat(O_m[-1:], H, axis=0)])
    r = float(world_open[1938] / world_open[1913])
    phase = np.clip(np.arange(1, H + 1) / 10, 0, 1)
    factor = 1 - (1 - r) * phase
    O_frag = O_base.copy()
    nonhub = [j for j in range(O_m.shape[1]) if j != hub]
    O_frag[len(yrs_m):, nonhub] = O_base[len(yrs_m):, nonhub] * factor[:, None]
    yrs_ext = np.concatenate([yrs_m, fut])
    ext = model.Model(S_ext, O_base, hub, yrs_ext)
    scen_paths = {}
    for label, kap in [("kappa_hat", R["structural"]["max"]["kappa_hat"]),
                       ("kappa_0.5", 0.5), ("kappa_1", 1.0)]:
        f = main_mod.fit(main_g, kappa=kap)
        a, beta = f["a"], f["beta"]
        base_hist = main_mod.path(a, beta, kap)
        noclose = main_mod.path(a, beta, kap, O=O_noclose)
        base_f = ext.path(a, beta, kap, O=O_base)
        frag_f = ext.path(a, beta, kap, O=O_frag)
        fwin = yrs_ext > C.END
        cf[label] = {
            "kappa": fmt(kap, 3),
            "closure_growth_model": fmt(base_hist[win].mean()), "closure_growth_noclosure": fmt(noclose[win].mean()),
            "level_gap_1949_pct": fmt(100 * (np.exp((base_hist[win].sum() - noclose[win].sum()) / 100) - 1)),
            "frag_growth_2023_2042": fmt(frag_f[fwin][:20].mean()), "base_growth_2023_2042": fmt(base_f[fwin][:20].mean()),
            "frag_level_gap_2042_pct": fmt(100 * (np.exp((frag_f[fwin][:20].sum() - base_f[fwin][:20].sum()) / 100) - 1)),
            "frag_level_gap_2062_pct": fmt(100 * (np.exp((frag_f[fwin].sum() - base_f[fwin].sum()) / 100) - 1)),
        }
        scen_paths[label] = {"hist": base_hist, "noclose": noclose, "base_f": base_f, "frag_f": frag_f}
    cf["openness_ratio_1938_1913"] = fmt(r, 3)
    R["counterfactuals"] = cf

    # --- 12. figures
    make_figures(levels, growth, pool1, world_open, O, R, main_mod, main_g, scen_paths, yrs_ext, decomp)

    growth.to_csv(C.PROCESSED / "frontier_growth.csv")
    with open(C.ROOT / "output" / "results.json", "w") as f:
        json.dump(R, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    print("done: output/results.json, output/figures/, output/tables/")


# ----------------------------------------------------------------------------- figures
def make_figures(levels, growth, pool, world_open, O, R, main_mod, main_g, scen, yrs_ext, decomp):
    from matplotlib.ticker import FixedLocator, NullLocator
    P = plots
    src_mad = "Source: Maddison Project Database 2023; 16 leading economies (JST sample excl. Norway, Ireland)."

    # F1 frontier envelope levels
    fig, ax = P.setup()
    ax.plot(levels.index, levels["max"], color=P.BLUE, lw=2, label="Frontier envelope (max of 16)")
    ax.plot(levels.index, levels["top5"], color=P.BLUE, lw=1.2, alpha=0.45, label="Top-5 average")
    ax.plot(levels.index, levels["us"], color=P.DARK, lw=1.1, ls=(0, (4, 3)), label="United States")
    ax.set_yscale("log")
    ax.set_ylim(2500, 150000)
    ax.yaxis.set_major_locator(FixedLocator([5000, 10000, 20000, 40000]))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_yticklabels(["$5k", "$10k", "$20k", "$40k"])
    P.shade_episodes(ax, C.EPISODES, ymax_text=140000)
    for (a, b, lab) in C.EPISODES:
        gval = R["episode_growth"]["max"][lab]
        ax.text((a + b) / 2, 105000, f"{gval:.1f}%/yr", ha="center", va="top", fontsize=9, color=P.BLUE)
    ax.set_xlim(1870, 2022)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    P.titles(fig, "Frontier GDP per capita grew at different speeds in different eras",
             "GDP per capita, 2011 PPP $, log scale · labels: annualized growth of the max envelope per episode", src_mad)
    P.save(fig, C.FIGURES / "fig1_envelope_levels.png")

    # F2 frontier growth: annual, low-frequency trend and Bai-Perron regimes
    fig, ax = P.setup()
    g = growth["max"].loc[1871:]
    war = g.index.isin(C.WAR_YEARS)
    ax.scatter(g.index[~war], g[~war], s=9, color=P.GREY, alpha=0.6, label="Annual growth")
    ax.scatter(g.index[war], g[war], s=9, color=P.GREY, alpha=0.25, marker="x", label="War years (dropped from tests)")
    ax.plot(g.index, lowfreq.trend(g.values, C.LF_Q), color=P.BLUE, lw=2.2, label="Low-frequency trend (periods ≥ 25 yrs)")
    sol = R["breaks"]["max"]["all_solutions"][1]
    for reg in sol["regimes"]:
        ax.hlines(reg["mean"], reg["from"], reg["to"], color=P.DARK, lw=1.4, ls=(0, (5, 3)))
    ax.text(1872, sol["regimes"][0]["mean"] + 0.6, f"best single break: {sol['break_years'][0]}  "
            f"(p = {R['breaks']['max']['p_supF'][0]:.2f})", fontsize=8.5, color=P.DARK)
    ax.axhline(0, color="#bbbbbb", lw=0.8)
    ax.set_ylim(-12, 12)
    ax.set_xlim(1870, 2022)
    ax.set_ylabel("% per year", color="#555555")
    ax.legend(loc="lower right", frameon=False, fontsize=8.5, ncol=2)
    P.titles(fig, "Year-to-year noise hides a slow swing in frontier growth",
             "Growth of the frontier envelope (max), % per year · dashed: best one-break model (Bai–Perron)", src_mad)
    P.save(fig, C.FIGURES / "fig2_frontier_growth.png")

    # F3 integration
    fig, ax = P.setup()
    ax.plot(world_open.index, 100 * world_open, color=P.BLUE, lw=2, label="Other 15 leading economies (GDP-weighted)")
    ax.plot(O.index, 100 * O[C.HUB], color=P.DARK, lw=1.2, ls=(0, (4, 3)), label="United States")
    P.shade_episodes(ax, C.EPISODES, ymax_text=88)
    ax.set_ylim(0, 90)
    ax.set_xlim(1870, 2022)
    ax.set_ylabel("Exports + imports, % of GDP", color="#555555")
    ax.legend(loc="upper left", bbox_to_anchor=(0, 0.9), frameon=False, fontsize=9)
    P.titles(fig, "Integration rose, collapsed and recovered",
             "Trade openness (exports + imports) / GDP, %",
             "Source: Jordà–Schularick–Taylor Macrohistory Database R6 (1870–2020), World Bank WDI (2021–22).")
    P.save(fig, C.FIGURES / "fig3_integration.png")

    # F4 long-run co-movement: frontier growth vs the integration component of the pool
    fig, ax = P.setup()
    yrs = np.arange(1871, 2023)
    ax.plot(yrs, lowfreq.trend(growth["max"].reindex(yrs).values, C.LF_Q), color=P.BLUE, lw=2.2,
            label="Frontier GDP per capita growth")
    tfp = growth["tfp_us"].reindex(np.arange(1891, 2023))
    ax.plot(tfp.index, lowfreq.trend(tfp.values, C.LF_Q), color=P.RED, lw=1.6,
            label="US TFP growth (BCL)")
    gi = pool["g_int"].reindex(yrs).values
    ax.plot(yrs, lowfreq.trend(gi, C.LF_Q), color=P.DARK, lw=1.4, ls=(0, (4, 3)),
            label="Integration component of research-pool growth")
    P.shade_episodes(ax, C.EPISODES, ymax_text=5.3)
    ax.axhline(0, color="#bbbbbb", lw=0.8)
    ax.set_ylim(-4.6, 5.5)
    ax.set_xlim(1870, 2022)
    ax.set_ylabel("% per year (low-frequency trend)", color="#555555")
    ax.legend(loc="lower right", frameon=False, fontsize=8.5)
    r_gdp = R["lowfreq"]["max"]["corr_int"]
    r_tfp = R["lowfreq"]["tfp_us"]["corr_int"]
    P.titles(fig, "Frontier income moves loosely with integration; US productivity moves against it",
             f"Low-frequency trends (periods ≥ 25 yrs) · long-run correlation with the integration component: "
             f"frontier GDP per capita {r_gdp:.2f}, US TFP {r_tfp:.2f}",
             "Sources: Maddison 2023; Bergeaud–Cette–Lecat v2.7; JST R6. Integration component at κ = 1.")
    P.save(fig, C.FIGURES / "fig4_longrun_comovement.png")

    # F5 decomposition: GDP per capita vs productivity vs hours, US and groups
    labs = [lab for _, _, lab in C.EPISODES]
    fig, ax = P.setup()
    vars_ = [("gdppc_bcl", "GDP per capita", P.GREY), ("gdp_per_hour", "GDP per hour", P.BLUE),
             ("tfp", "TFP", P.RED), ("hours_pc", "Hours per person", "#bbbbbb")]
    x = np.arange(len(labs))
    wbar = 0.2
    for i, (v, name, col) in enumerate(vars_):
        vals = [R["decomposition"]["Undamaged (USA, CHE, SWE)"][f"{v}|{lab}"] for lab in labs]
        ax.bar(x + (i - 1.5) * wbar, vals, wbar, color=col, label=name)
        for xi, val in zip(x + (i - 1.5) * wbar, vals):
            ax.text(xi, val + (0.08 if val >= 0 else -0.25), f"{val:.1f}", ha="center", fontsize=7.5, color="#444444")
    ax.axhline(0, color="#999999", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labs)
    ax.set_ylabel("% per year", color="#555555")
    ax.legend(frameon=False, fontsize=8.5, ncol=4, loc="upper left")
    ax.set_ylim(-1.2, 3.4)
    P.titles(fig, "In the closure, productivity kept growing while hours per person fell",
             "Undamaged leaders (USA, Switzerland, Sweden), average annualized growth by episode",
             "Source: Bergeaud–Cette–Lecat Long-Term Productivity Database v2.7 (episode 1 starts in 1890).")
    P.save(fig, C.FIGURES / "fig5_decomposition_undamaged.png")

    # F6 undamaged vs damaged TFP
    fig, ax = P.setup()
    groups = [("Undamaged (USA, CHE, SWE)", P.BLUE), ("War-damaged (BEL, DEU, FRA, ITA, JPN, NLD)", P.GREY)]
    for i, (gname, col) in enumerate(groups):
        vals = [R["decomposition"][gname][f"tfp|{lab}"] for lab in labs]
        ax.bar(x + (i - 0.5) * 0.35, vals, 0.35, color=col, label=gname)
        for xi, val in zip(x + (i - 0.5) * 0.35, vals):
            ax.text(xi, val + 0.06, f"{val:.1f}", ha="center", fontsize=8, color="#444444")
    ax.axhline(0, color="#999999", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labs)
    ax.set_ylabel("TFP growth, % per year", color="#555555")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.set_ylim(0, 4.2)
    P.titles(fig, "Leaders untouched by war saw no productivity slowdown in the closure",
             "Average annualized TFP growth by episode",
             "Source: Bergeaud–Cette–Lecat Long-Term Productivity Database v2.7.")
    P.save(fig, C.FIGURES / "fig6_tfp_undamaged_vs_damaged.png")

    # F7 structural profile of kappa
    fig, ax = P.setup()
    names = {"max": ("GDP per capita, max envelope", P.BLUE), "top5": ("GDP per capita, top-5", "#8db8ea"),
             "tfp_top5": ("TFP, top-5", P.RED)}
    for k, (name, col) in names.items():
        prof = R["structural"][k]["profile"]
        kk = np.array([float(a) for a in prof])
        ll = np.array(list(prof.values()))
        rel = 100 * (ll / ll[0] - 1)
        ax.plot(kk, rel, color=col, lw=2, marker="o", ms=4, label=name)
    ax.axhline(0, color="#999999", lw=0.8)
    ax.set_xlabel("κ: elasticity of a country's research weight to its trade openness", color="#555555")
    ax.set_ylabel("Misfit vs. κ = 0, %", color="#555555")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    P.titles(fig, "Weighting research by integration never beats the unweighted world pool",
             "Misfit of low-frequency moments relative to κ = 0 · as κ grows, the pool shrinks toward US research alone",
             "Semi-endogenous model with population-based research pool; a and β re-estimated at each κ.")
    P.save(fig, C.FIGURES / "fig7_kappa_profile.png")

    # F8 power
    fig, ax = P.setup()
    for k, name, col in [("max", "GDP per capita frontier", P.BLUE), ("tfp_top5", "TFP frontier (top-5)", P.RED)]:
        pw = R["power"][k]
        th = [float(t) for t in pw]
        ax.plot(th, [100 * pw[t]["lowfreq_t"] for t in pw], color=col, lw=2, marker="o", ms=4,
                label=f"{name}: low-frequency test")
        ax.plot(th, [100 * pw[t]["closure_dummy"] for t in pw], color=col, lw=1.3, ls=(0, (4, 3)), marker="o", ms=3,
                label=f"{name}: closure-mean test")
    ax.axhline(5, color="#bbbbbb", lw=0.8, ls=(0, (3, 3)))
    ax.axvline(0.5, color="#bbbbbb", lw=0.8)
    ax.text(0.51, 37, "θ = 0.5:\nκ = 1 with β = 3", fontsize=8, color="#777777", va="top")
    ax.set_ylim(0, 100)
    ax.set_xlabel("θ: response of frontier growth to the integration component of research-pool growth", color="#555555")
    ax.set_ylabel("Rejection rate, %", color="#555555")
    ax.legend(frameon=False, fontsize=8, loc="center right")
    P.titles(fig, "Detecting an integration effect needs it to be large",
             "Monte Carlo rejection rates at 5% (one-sided): simulated growth = mean + θ × integration component + resampled noise",
             "Noise: 10-year block bootstrap of each series' own deviations from its mean.")
    P.save(fig, C.FIGURES / "fig8_power.png")

    # F9 forward fragmentation scenario
    fig, ax = P.setup()
    fut_mask = yrs_ext > C.END
    fy = yrs_ext[fut_mask]
    for label, name, col in [("kappa_1", "If κ = 1", P.BLUE), ("kappa_0.5", "If κ = 0.5", "#8db8ea"),
                             ("kappa_hat", f"Best fit (κ = {R['counterfactuals']['kappa_hat']['kappa']:g})", P.GREY)]:
        sp = scen[label]
        gap = 100 * (np.exp(np.cumsum(sp["frag_f"][fut_mask] - sp["base_f"][fut_mask]) / 100) - 1)
        ax.plot(fy, gap, color=col, lw=2, label=name)
    ax.axhline(0, color="#999999", lw=0.8)
    ax.set_xlim(fy[0], fy[-1])
    ax.set_ylabel("Frontier GDP per capita vs. no fragmentation, %", color="#555555")
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    P.titles(fig, "A 1913–38-sized fragmentation: no cost at the best fit, about −7% by 2042 if κ = 1",
             f"Scenario: other economies' openness falls to {100 * R['counterfactuals']['openness_ratio_1938_1913']:.0f}% "
             f"of today's level over 2023–32 (the 1913→1938 ratio)",
             "Structural model projections; population grows at its 2012–22 rate.")
    P.save(fig, C.FIGURES / "fig9_fragmentation_scenario.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    main(**vars(ap.parse_args()))
