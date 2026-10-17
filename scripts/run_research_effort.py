"""Project 3: why does research effort grow at a steady pace, and why does that give ~2%?

Research effort ("effective researchers", Bloom et al. 2020 style):
    S = research spending / nominal GDP per person = (R&D / GDP) x population
so its growth splits exactly into   g_S = g_share + n.

Hypotheses
 A  Coincidence: population growth (n) and research-intensity growth (g_share) move
    independently; a steady g_S is luck.
 B  Balancing: research intensity responds to population growth or researcher supply,
    so n and g_share offset (variance ratio < 1) more than chance.
 C  Feedback: research effort responds to PAST productivity growth with a negative sign
    (slowdowns trigger research pushes), a stabilizing loop; procyclical R&D would be destabilizing.
 D  Stable diminishing returns: the ratio of research growth to TFP growth (beta) is constant over time.

Data: BEA NIPA R&D 1929-2025 (total, private, government; current and chained dollars),
NSF National Patterns 1953-2024, OECD MSTI 1981-2025 (researchers, GERD by funder), Lee-Lee
tertiary attainment, Bergeaud-Cette-Lecat TFP. No IPUMS (pre-1929 research labor) yet.

Outputs: output/research_effort/results.json, output/research_effort/figures/*.png
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
from frontier import identification as ID  # noqa: E402

OUT = C.ROOT / "output" / "research_effort"
FIG = OUT / "figures"
RAWB = C.RAW / "balancing"
RAWR = C.RAW / "research_effort"
REPS = 999
ALPHA = 0.3


# ----------------------------------------------------------------------------- data
def bea(codes):
    d = pd.read_csv(RAWB / "bea_nipa" / "NipaDataA.txt")
    d.columns = ["code", "year", "value"]
    d = d[d.code.isin(codes)].copy()
    d["value"] = pd.to_numeric(d.value.astype(str).str.replace(",", ""), errors="coerce")
    return d.groupby("year")["value"].sum(min_count=len(codes))


def us_series():
    mad = data.load_maddison()
    pop = mad[mad.iso == "USA"].set_index("year")["pop"].astype(float)
    gdp = bea(["A191RC"])
    rd = bea(["Y694RC"])
    rd_priv = bea(["Y006RC"])
    rd_real = bea(["Y694RX"])
    rd_priv_real = bea(["Y006RX"])
    b = data.load_bcl()
    tfp = b[b.iso == "USA"].set_index("year")["tfp"]
    yrs = range(1929, 2023)
    d = pd.DataFrame({"pop": pop, "gdp": gdp, "rd": rd, "rd_priv": rd_priv, "rd_real": rd_real,
                      "rd_priv_real": rd_priv_real, "tfp": tfp}).reindex(yrs)
    d["rd_gov"] = d.rd - d.rd_priv
    # funders (BEA codes identified by the data agent): federal defense Y076, federal nondefense Y069
    for code, name in [("Y076RC", "rd_def"), ("Y069RC", "rd_nondef"), ("Y073RC", "rd_state")]:
        d[name] = bea([code]).reindex(yrs)
    for code, name in [("Y694RA", "q_total"), ("Y006RA", "q_priv"), ("Y076RA", "q_def"), ("Y069RA", "q_nondef")]:
        d[name] = bea([code]).reindex(yrs)
    d["share"] = d.rd / d.gdp
    d["S"] = d.rd / (d.gdp / d["pop"])          # effective researchers
    g = pd.DataFrame({
        "n": 100 * np.log(d["pop"]).diff(),
        "g_share": 100 * np.log(d.share).diff(),
        "g_S": 100 * np.log(d.S).diff(),
        "g_rd_real_pc": 100 * np.log(d.rd_real / d["pop"]).diff(),
        "g_priv_real_pc": 100 * np.log(d.rd_priv_real / d["pop"]).diff(),
        "g_priv_share": 100 * np.log(d.rd_priv / d.gdp).diff(),
        "g_gov_share": 100 * np.log(d.rd_gov / d.gdp).diff(),
        "g_def_share": 100 * np.log(d.rd_def / d.gdp).diff(),
        "g_nondef_share": 100 * np.log(d.rd_nondef / d.gdp).diff(),
        "g_q_total_pc": 100 * np.log(d.q_total / d["pop"]).diff(),
        "g_q_priv_pc": 100 * np.log(d.q_priv / d["pop"]).diff(),
        "g_q_def_pc": 100 * np.log(d.q_def / d["pop"]).diff(),
        "g_q_nondef_pc": 100 * np.log(d.q_nondef / d["pop"]).diff(),
        "g_A": 100 * np.log(d.tfp).diff()})
    return d, g


def tertiary_us():
    ll = pd.read_stata(RAWB / "leelee2016" / "LeeLee_v1.dta")
    u = ll[(ll.sex == "MF") & (ll.country.str.strip().isin(["USA", "United States", "United States of America"]))]
    s = u.set_index(u.year.astype(int))["lh"].astype(float)  # % of population with completed tertiary
    s = s[s > 0]
    full = s.reindex(range(int(s.index.min()), int(s.index.max()) + 1))
    return np.exp(np.log(full).interpolate())


def msti_panel():
    p = RAWR / "msti_extract_2026-10-16.csv"
    o = pd.read_csv(p, low_memory=False, encoding="latin-1")
    pick = {("G", "USD_PPP", "Q"): "gerd_real", ("G", "PT_B1GQ", "_Z"): "gerd_share",
            ("T_RS", "FTE", "_Z"): "researchers", ("TOT_POP", None, None): "pop"}
    rows = []
    for (m, u, pb), name in pick.items():
        q = o[(o.MEASURE == m) & (o.TRANSFORMATION == "_Z")]  # levels only (drop growth-rate GY and index IX rows)
        if u is not None:
            q = q[(q.UNIT_MEASURE == u) & (q.PRICE_BASE == pb)]
        q = q.groupby(["REF_AREA", "TIME_PERIOD"])["OBS_VALUE"].mean().rename(name)
        rows.append(q)
    d = pd.concat(rows, axis=1).reset_index().rename(columns={"REF_AREA": "iso", "TIME_PERIOD": "year"})
    return d


# ----------------------------------------------------------------------------- tests
def lf_reg(y, X, names, q):
    return lowfreq.regression(np.asarray(y, float), np.column_stack(X), q, names)


def lagged_lf(y, x, lag, q_per_year=1 / 12.5):
    """LF regression of y_t on x_{t-lag}."""
    y, x = np.asarray(y, float), np.asarray(x, float)
    if len(y) - lag < 40:
        return None
    if lag > 0:
        y, x = y[lag:], x[:-lag]
    q = max(3, int(round(len(y) * q_per_year)))
    r = lowfreq.regression(y, x[:, None], q, ["x"])
    return {"slope": r["coef"]["x"], "se": r["se"]["x"], "t": r["t"]["x"], "p": r["p"]["x"], "q": q, "n": len(y)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(2028)
    R = {}
    d, g = us_series()
    gg = g.loc[1930:2022, ["n", "g_share", "g_S", "g_A", "g_rd_real_pc"]].dropna()
    yrs = gg.index.values
    q = int(round(len(gg) / 12.5))
    R["us_window"] = [int(yrs[0]), int(yrs[-1])]
    R["q"] = q

    # decade table: why ~2%?
    dec = []
    for a in range(1930, 2020, 10):
        s = gg.loc[a:a + 9]
        dec.append({"decade": f"{a}s", "n": s.n.mean(), "g_share": s.g_share.mean(), "g_S": s.g_S.mean(),
                    "g_A": s.g_A.mean()})
    R["decades"] = pd.DataFrame(dec).round(3).to_dict(orient="records")
    R["means"] = {c: float(gg[c].mean()) for c in ["n", "g_share", "g_S", "g_A"]}
    R["means"]["implied_beta"] = R["means"]["g_S"] / R["means"]["g_A"]
    R["means"]["implied_gy"] = R["means"]["g_A"] / (1 - ALPHA)

    # ---- A/B: do population growth and research-intensity growth offset?
    Cm = gg[["n", "g_share"]].values
    r = B.ratio(Cm, q)
    nd = np.array([B.ratio(B.surrogate_phase(Cm, rng), q) for _ in range(REPS)])
    L = B.lf_matrix(Cm, q)
    R["A_B_offset_us"] = {"ratio": r, "null_median": float(np.median(nd)), "p_offset": float((nd <= r).mean()),
                          "lf_corr_n_share": float(np.corrcoef(L[:, 0], L[:, 1])[0, 1]),
                          "lf_sd_n": float(L[:, 0].std()), "lf_sd_share": float(L[:, 1].std()),
                          "lf_sd_gS": float(L.sum(1).std())}
    # B: does research intensity respond to researcher supply (tertiary-educated population)?
    ter = tertiary_us()
    g_ter = 100 * np.log(ter * d["pop"].reindex(ter.index)).diff()
    jj = gg.loc[1931:2010, ["g_share", "n"]].join(g_ter.rename("g_ter")).dropna()
    qb = int(round(len(jj) / 12.5))
    R["B_supply_us"] = {"years": [int(jj.index[0]), int(jj.index[-1])],
                        "share_on_tertiary_and_n": lf_reg(jj.g_share, [jj.g_ter, jj.n], ["g_ter", "n"], qb)}

    # ---- C: feedback from past TFP growth to research growth
    R["C_feedback_us"] = {}
    for var in ["g_S", "g_share", "g_rd_real_pc", "g_q_total_pc", "g_q_priv_pc", "g_q_def_pc", "g_q_nondef_pc",
                "g_priv_share", "g_gov_share", "g_def_share", "g_nondef_share"]:
        s = g[[var, "g_A"]].loc[1930:2022].dropna()
        R["C_feedback_us"][var] = {f"tfp_lag{L}": lagged_lf(s[var].values, s.g_A.values, L) for L in (0, 5, 10, 15)}
    # forward link (research -> TFP) for the loop gain
    s = g[["g_S", "g_A"]].loc[1930:2022].dropna()
    fwd = {f"research_lag{L}": lagged_lf(s.g_A.values, s.g_S.values, L) for L in (0, 5, 10)}
    R["C_forward_us"] = fwd
    back = R["C_feedback_us"]["g_q_total_pc"]
    R["C_loop_gain"] = {"forward_5y": fwd["research_lag5"]["slope"], "backward_10y_realRDpc": back["tfp_lag10"]["slope"],
                        "loop_gain": fwd["research_lag5"]["slope"] * back["tfp_lag10"]["slope"]}

    # OECD panel: 5-year research growth on lagged 5-year TFP growth (country and period FE)
    msti = msti_panel()
    b = data.load_bcl()
    tfp = b[~b.iso.isin(["ZE"])].pivot(index="year", columns="iso", values="tfp")
    rows = []
    for iso, m in msti.groupby("iso"):
        if iso not in tfp.columns:
            continue
        m = m.set_index("year").sort_index()
        for k0 in range(1982, 2018, 5):
            k1 = k0 + 4
            if k0 - 5 < 1981 and False:
                continue
            def gr(s, a, b_):
                try:
                    return 100 * (np.log(s[b_]) - np.log(s[a - 1])) / (b_ - a + 1)
                except Exception:
                    return np.nan
            row = {"iso": iso, "period": k0,
                   "g_res": gr(m.researchers.dropna(), k0, k1) if "researchers" in m else np.nan,
                   "g_gerd": gr(m.gerd_real.dropna(), k0, k1), "g_share": gr(m.gerd_share.dropna(), k0, k1),
                   "n": gr(m["pop"].dropna(), k0, k1),
                   "g_A_lag": gr(tfp[iso].dropna(), k0 - 5, k0 - 1), "g_A": gr(tfp[iso].dropna(), k0, k1),
                   "g_res_lag": gr(m.researchers.dropna(), k0 - 5, k0 - 1) if "researchers" in m else np.nan,
                   "g_res_pc": gr((m.researchers / m["pop"]).dropna(), k0, k1) if "researchers" in m else np.nan,
                   "lvl_A": float(np.log(tfp[iso].get(k0 - 1, np.nan)))}
            rows.append(row)
    P = pd.DataFrame(rows)
    R["C_feedback_oecd_panel"] = {}
    for dep in ["g_res", "g_gerd", "g_share"]:
        dd = P.dropna(subset=[dep, "g_A_lag"])
        if len(dd) < 40:
            continue
        rr = ID.panel_iv(dd, dep, ["g_A_lag"], ["g_A_lag"], fe=("iso", "period"))
        R["C_feedback_oecd_panel"][dep] = {"slope": rr["coef"]["g_A_lag"], "se": rr["se"]["g_A_lag"],
                                           "p": rr["p"]["g_A_lag"], "n": rr["n"], "countries": rr["clusters"]}
    # robustness of the OECD feedback: common (no period FE) vs relative component, and confounders
    rob = {}
    specs = {"researchers_country_fe_only": ("g_res", ["g_A_lag"], ("iso",)),
             "researchers_plus_lagged_dep": ("g_res", ["g_A_lag", "g_res_lag"], ("iso", "period")),
             "researchers_plus_current_tfp": ("g_res", ["g_A_lag", "g_A"], ("iso", "period")),
             "researchers_plus_tfp_level": ("g_res", ["g_A_lag", "lvl_A"], ("iso", "period")),
             "researchers_per_person": ("g_res_pc", ["g_A_lag"], ("iso", "period")),
             "researchers_per_person_country_fe_only": ("g_res_pc", ["g_A_lag"], ("iso",)),
             "share_country_fe_only": ("g_share", ["g_A_lag"], ("iso",))}
    for name, (dep, xs, fe) in specs.items():
        dd = P.dropna(subset=[dep, *xs])
        rr = ID.panel_iv(dd, dep, xs[:1], xs[:1], exog=xs[1:], fe=fe)
        rob[name] = {"slope": rr["coef"]["g_A_lag"], "se": rr["se"]["g_A_lag"], "p": rr["p"]["g_A_lag"], "n": rr["n"]}
    R["C_feedback_oecd_robust"] = rob
    # OECD panel version of A/B: do population growth and intensity growth offset across country-periods?
    dd = P.dropna(subset=["n", "g_share"])
    within = dd.assign(n_w=dd.n - dd.groupby("iso").n.transform("mean"),
                       s_w=dd.g_share - dd.groupby("iso").g_share.transform("mean"))
    R["A_B_offset_oecd"] = {"corr_within_country": float(np.corrcoef(within.n_w, within.s_w)[0, 1]),
                            "n_obs": int(len(dd)), "countries": int(dd.iso.nunique())}

    # ---- D: is beta stable? rolling 30-year windows of research growth (lagged 5y) over TFP growth
    s = g[["g_S", "g_A"]].loc[1925:2022]
    roll = []
    for a in range(1935, 1994, 1):
        w = s.loc[a:a + 29]
        gs = g["g_S"].shift(5).loc[a:a + 29].mean()
        roll.append({"start": a, "end": a + 29, "beta": float(gs / w.g_A.mean()), "g_S_lag5": float(gs),
                     "g_A": float(w.g_A.mean())})
    R["D_rolling_beta"] = roll
    # research productivity (Bloom et al.): TFP growth per unit of effective research; its growth by decade
    rp = (g.g_A.rolling(10).mean() / d.S).dropna()
    R["D_research_productivity_growth_by_decade"] = {
        f"{a}s": float(100 * np.log(rp.loc[a + 9] / rp.loc[a]) / 9) for a in range(1940, 2020, 10)
        if a in rp.index and a + 9 in rp.index and rp.loc[a] > 0 and rp.loc[a + 9] > 0}

    # ---- Measurement robustness: Bloom et al.-style deflator (college-graduate wage) instead of GDP per person
    w = pd.read_excel(RAWB / "bjvw2020" / "extracted_aggregate" / "WageSci" / "WageSci.xls", sheet_name="Chad", header=None)
    w = w.iloc[8:, [1, 5]].copy()
    w.columns = ["year", "wage"]
    w["wage"] = pd.to_numeric(w.wage, errors="coerce")
    w = w.dropna().set_index(w.dropna().year.astype(int))["wage"]
    w = np.exp(np.log(w.reindex(range(w.index.min(), w.index.max() + 1))).interpolate())
    ipp = bea(["Y001RC", "Y055RC"])
    meas_b = {"rd_over_college_wage": d.rd.reindex(w.index) / w, "ipp_over_college_wage": ipp.reindex(w.index) / w,
              "rd_over_gdppc": d.S.reindex(w.index)}
    tab = {}
    for name, sv in meas_b.items():
        gsv = 100 * np.log(sv).diff()
        tab[name] = {f"{a}s": float(gsv.loc[max(a, 1940):a + 9].mean()) for a in range(1940, 2020, 10)}
        tab[name]["mean_1940_2015"] = float(gsv.loc[1940:2015].mean())
        tab[name]["sd_decade_means"] = float(np.std([v for k, v in tab[name].items() if k.endswith("s")]))
    R["measurement_bjvw_deflator"] = tab
    # rolling beta with the college-wage deflator
    gb = 100 * np.log(meas_b["ipp_over_college_wage"]).diff()
    roll_b = []
    for a in range(1945, 1987):
        gs = gb.shift(5).loc[a:a + 29].mean()
        ga = g.g_A.loc[a:a + 29].mean()
        roll_b.append({"start": a, "beta": float(gs / ga), "g_S_lag5": float(gs), "g_A": float(ga)})
    R["D_rolling_beta_bjvw_deflator"] = roll_b

    # ---- World vs US research effort (OECD MSTI, chain-linked sums across reporting economies)
    def chain(df, col):
        piv = df.pivot_table(index="year", columns="iso", values=col).sort_index()
        gr = []
        for t in range(1, len(piv)):
            a, b_ = piv.iloc[t - 1], piv.iloc[t]
            ok = a.notna() & b_.notna() & (a > 0)
            gr.append((piv.index[t], 100 * np.log(b_[ok].sum() / a[ok].sum()) if ok.any() else np.nan))
        return pd.Series(dict(gr))
    aggs = [c for c in msti.iso.unique() if len(c) == 3 and c not in ("OECD", "EU27", "EA20")]
    mw = msti[msti.iso.isin(aggs)]
    world = {"real_gerd": chain(mw, "gerd_real"), "researchers": chain(mw, "researchers")}
    us = {"real_gerd": chain(mw[mw.iso == "USA"], "gerd_real"), "researchers": chain(mw[mw.iso == "USA"], "researchers")}
    R["world_vs_us_research"] = {
        k: {"world": {f"{a}s": float(world[k].loc[a:a + 9].mean()) for a in (1980, 1990, 2000, 2010)},
            "us": {f"{a}s": float(us[k].loc[a:a + 9].mean()) for a in (1980, 1990, 2000, 2010)},
            "world_mean": float(world[k].loc[1982:2022].mean()), "us_mean": float(us[k].loc[1982:2022].mean()),
            "economies": int(mw.iso.nunique())} for k in world}

    with open(OUT / "results.json", "w") as f:
        json.dump(R, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    figures(R, g)
    print("done: output/research_effort/results.json")


def figures(R, g):
    P = plots
    src = "Sources: BEA NIPA R&D and IPP investment; Bloom et al. (2020) college-wage deflator; Bergeaud–Cette–Lecat TFP."
    # R1 research-effort growth by decade under two deflators vs TFP growth
    M = R["measurement_bjvw_deflator"]
    decs = [f"{a}s" for a in range(1940, 2020, 10)]
    tfp = {d["decade"]: d["g_A"] for d in R["decades"]}
    fig, ax = P.setup(figsize=(10, 5.2))
    x = np.arange(len(decs))
    ax.bar(x - 0.27, [M["ipp_over_college_wage"][d] for d in decs], 0.27, color=P.BLUE, label="Research effort: IPP ÷ college wage (Bloom et al.)")
    ax.bar(x, [M["rd_over_gdppc"][d] for d in decs], 0.27, color="#8db8ea", label="Research effort: R&D ÷ GDP per person")
    ax.bar(x + 0.27, [tfp.get(d, np.nan) for d in decs], 0.27, color=P.RED, label="TFP growth")
    ax.axhline(0, color="#999999", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(decs)
    ax.set_ylabel("% per year (decade average)", color="#555555")
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    P.titles(fig, "US research effort did not grow steadily: it surged mid-century, then slowed",
             "Average annual growth by decade, 1940s–2010s", src)
    P.save(fig, FIG / "r1_research_by_decade.png")

    # R2 rolling beta under two deflators
    fig, ax = P.setup(figsize=(10, 5))
    rb = pd.DataFrame(R["D_rolling_beta"])
    rbb = pd.DataFrame(R["D_rolling_beta_bjvw_deflator"])
    ax.plot(rbb.start + 15, rbb.beta, color=P.BLUE, lw=2.2, label="IPP ÷ college wage (Bloom et al. measure)")
    ax.plot(rb.start + 15, rb.beta, color=P.GREY, lw=1.6, ls=(0, (4, 3)), label="R&D ÷ GDP per person")
    ax.axhline(3, color=P.DARK, lw=0.8, ls=(0, (2, 2)))
    ax.text(rbb.start.min() + 15, 3.08, "β = 3 (Bloom et al. 2020)", fontsize=8, color="#555555")
    ax.set_ylim(0, 5.5)
    ax.set_xlabel("Centre of 30-year window", color="#555555")
    ax.set_ylabel("β = research growth (5 yrs earlier) ÷ TFP growth", color="#555555")
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    P.titles(fig, "With Bloom et al.'s measure, diminishing returns are stable at β ≈ 2.5–3",
             "Rolling 30-year ratio of lagged research-effort growth to TFP growth, US", src)
    P.save(fig, FIG / "r2_rolling_beta.png")

    # R3 feedback: response of research growth to TFP growth 15 years earlier, by funder
    C_ = R["C_feedback_us"]
    rows = [("Total (real, per person)", "g_q_total_pc"), ("Private (real, per person)", "g_q_priv_pc"),
            ("Federal defense (real, per person)", "g_q_def_pc"), ("Federal nondefense (real, per person)", "g_q_nondef_pc")]
    fig, ax = P.setup(figsize=(10, 4.8))
    for k, (lab, var) in enumerate(rows):
        for j, (L, col) in enumerate([("tfp_lag0", P.GREY), ("tfp_lag10", "#8db8ea"), ("tfp_lag15", P.BLUE)]):
            r = C_[var][L]
            if r is None:
                continue
            ax.errorbar(r["slope"], k + (j - 1) * 0.2, xerr=1.645 * r["se"], fmt="o", color=col, capsize=2,
                        label={"tfp_lag0": "same years", "tfp_lag10": "TFP 10 yrs earlier", "tfp_lag15": "TFP 15 yrs earlier"}[L] if k == 0 else None)
    ax.axvline(0, color="#999999", lw=0.8)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Response of research growth to TFP growth (90% interval); negative = stabilizing feedback", color="#555555")
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    ax.grid(axis="x", color="#eeeeee")
    P.titles(fig, "In the US, research follows past productivity booms; it does not lean against slowdowns",
             "Low-frequency regressions, US 1930–2022 (q ≈ 7; few long cycles)", src)
    P.save(fig, FIG / "r3_feedback.png")


if __name__ == "__main__":
    main()
