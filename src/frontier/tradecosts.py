"""Trade costs, tariffs and geography-based instruments.

- Bilateral trade costs (tariff equivalents) by inverse gravity (Novy 2013), computed
  from CEPII TRADHIST v4 flows, GDP and total exports, sigma = 8 as in Jacks, Meissner
  and Novy (2011). Validated against the published JMN series.
- Country tariffs (customs revenue / imports): Jacks-Meissner-Novy file, which carries
  the Clemens-Williamson series; TRADHIST TARIFF as a fallback.
- Sea distances that change with the Suez Canal (opened 1869, closed 1967-75) from TRADHIST.
- A Feyrer (2019)-style instrument: the part of trade costs predicted by fixed geography
  (sea and air distance) interacted with decade-specific distance elasticities.
"""
import numpy as np
import pandas as pd

from . import config as C

TH = C.RAW / "tradhist" / "TRADHIST_v4_extract_16origins.csv.gz"
JMN = C.RAW / "jmn_tradecosts" / "tbtbtc.dta"
JMN_CODES = {"SWI": "CHE", "GER": "DEU", "DEN": "DNK", "SPA": "ESP", "UK": "GBR", "JAP": "JPN",
             "NET": "NLD", "POR": "PRT"}
SIGMA = 8.0
YEARS = range(1870, 2015)


def _load_tradhist(countries=C.CORE):
    cols = ["iso_o", "iso_d", "year", "FLOW", "GDP_o", "XPTOT_o", "TARIFF_o", "SeaDist_SHRT", "Dist_coord"]
    t = pd.read_csv(TH, usecols=cols)
    return t[t.iso_o.isin(countries) & t.iso_d.isin(countries) & t.year.between(1870, 2014)]


def _interp_pairs(df, value, keys=("i", "j")):
    out = []
    for k, g in df.groupby(list(keys)):
        s = g.set_index("year")[value].reindex(YEARS)
        s = s.interpolate(limit_area="inside")
        out.append(pd.DataFrame({keys[0]: k[0], keys[1]: k[1], "year": list(YEARS), value: s.values}))
    return pd.concat(out, ignore_index=True)


def bilateral_panel(countries=C.CORE):
    """Pair-year panel (i < j): trade cost tau, sea distance and great-circle distance."""
    t = _load_tradhist(countries)
    flows = t.set_index(["iso_o", "iso_d", "year"])["FLOW"]
    own = t.groupby(["iso_o", "year"])[["GDP_o", "XPTOT_o"]].first()
    dom = (own["GDP_o"] - own["XPTOT_o"]).rename("dom")
    rows = []
    for (i, j, y), x_ij in flows.items():
        if i >= j:
            continue
        x_ji = flows.get((j, i, y), np.nan)
        xii, xjj = dom.get((i, y), np.nan), dom.get((j, y), np.nan)
        ok = all(np.isfinite(v) and v > 0 for v in (x_ij, x_ji, xii, xjj))
        tau = ((xii * xjj) / (x_ij * x_ji)) ** (1 / (2 * (SIGMA - 1))) - 1 if ok else np.nan
        rows.append((i, j, y, tau))
    tau = pd.DataFrame(rows, columns=["i", "j", "year", "tau"])
    tau["ltau"] = np.log1p(tau["tau"])
    tau = _interp_pairs(tau, "ltau")  # wartime gaps filled linearly in log(1 + tau)
    geo = t[t.iso_o < t.iso_d].rename(columns={"iso_o": "i", "iso_d": "j"})
    geo = geo.groupby(["i", "j", "year"])[["SeaDist_SHRT", "Dist_coord"]].first().reset_index()
    sea = _interp_pairs(geo.rename(columns={"SeaDist_SHRT": "sea"}), "sea")
    air = geo.groupby(["i", "j"])["Dist_coord"].first().rename("air").reset_index()
    out = tau.merge(sea, on=["i", "j", "year"], how="left").merge(air, on=["i", "j"], how="left")
    # Sea distance is missing for the landlocked CHE-ITA pair; use road/air distance there.
    out["sea"] = out["sea"].fillna(out["air"])
    return out


def jmn_tau():
    j = pd.read_stata(JMN)
    j["a"], j["b"] = j.ctry1.replace(JMN_CODES), j.ctry2.replace(JMN_CODES)
    j["i"], j["j"] = j[["a", "b"]].min(axis=1), j[["a", "b"]].max(axis=1)
    return j[["i", "j", "year", "tc8"]]


def country_tariffs(countries=C.CORE):
    """Customs revenue / imports, country-year, 1870-2014 (interpolated inside, held flat outside)."""
    j = pd.read_stata(JMN)
    parts = []
    for side in ("1", "2"):
        d = j[["year", f"ctry{side}", f"cwtar{side}", f"tar{side}"]].copy()
        d.columns = ["year", "iso", "cw", "tar"]
        parts.append(d)
    d = pd.concat(parts)
    d["iso"] = d.iso.replace(JMN_CODES)
    d["tariff"] = d["cw"].fillna(d["tar"])
    tar = d.groupby(["iso", "year"])["tariff"].mean()
    th = _load_tradhist(countries).groupby(["iso_o", "year"])["TARIFF_o"].first() / 100
    out = []
    for iso in countries:
        s = tar.get(iso, pd.Series(dtype=float))
        if isinstance(s, pd.Series) and len(s):
            s = s.reindex(YEARS)
        else:
            s = pd.Series(np.nan, index=list(YEARS))
        if iso in th.index.get_level_values(0):
            s = s.fillna(th.loc[iso].reindex(YEARS))
        s = s.interpolate(limit_area="inside").ffill().bfill()
        out.append(pd.DataFrame({"iso": iso, "year": list(YEARS), "tariff": s.values}))
    return pd.concat(out, ignore_index=True)


def feyrer_prediction(panel):
    """Predicted log(1 + tau) from geography x decade elasticities, with pair and year effects.

    log(1+tau_ijt) = a_ij + d_t + sum_D 1[t in D] (b_D log sea_ijt + c_D log air_ij) + e
    The prediction keeps only the geography terms, so its changes over time come from
    shifting distance elasticities (transport technology) and the Suez Canal.
    """
    df = panel.dropna(subset=["ltau", "sea", "air"]).copy()
    df["dec"] = (df.year // 10) * 10
    decades = sorted(df.dec.unique())
    base = decades[0]
    Xcols = []
    for d in decades:
        if d == base:
            continue
        df[f"sea_{d}"] = (df.dec == d) * np.log(df.sea)
        df[f"air_{d}"] = (df.dec == d) * np.log(df.air)
        Xcols += [f"sea_{d}", f"air_{d}"]
    df["lsea"] = np.log(df.sea)  # Suez-driven changes within the base decade
    Xcols.append("lsea")
    # two-way within transformation (pair, year) by alternating projections
    Y = df["ltau"].values.copy()
    X = df[Xcols].values.astype(float).copy()
    pair = df.i + "_" + df.j
    for _ in range(50):
        for key in (pair, df.year):
            Y = Y - pd.Series(Y).groupby(key.values).transform("mean").values
            X = X - pd.DataFrame(X).groupby(key.values).transform("mean").values
    beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
    pred = df[Xcols].values @ beta
    out = df[["i", "j", "year"]].copy()
    out["pred_ltau"] = pred
    coefs = dict(zip(Xcols, beta.tolist()))
    return out, coefs


def suez_first_stage(panel, years=(1950, 1990)):
    """Elasticity of log(1 + tau) to log sea distance, pair and year effects (Suez closure years)."""
    df = panel[(panel.year >= years[0]) & (panel.year <= years[1])].dropna(subset=["ltau", "sea"]).copy()
    y = df["ltau"].values.copy()
    x = np.log(df["sea"].values).copy()
    pair = (df.i + "_" + df.j).values
    for _ in range(50):
        for key in (pair, df.year.values):
            y = y - pd.Series(y).groupby(key).transform("mean").values
            x = x - pd.Series(x).groupby(key).transform("mean").values
    b = (x @ y) / (x @ x)
    e = y - b * x
    # cluster-robust SE by pair
    sc = pd.Series(x * e).groupby(pair).sum()
    se = np.sqrt((sc ** 2).sum()) / (x @ x)
    exposed = df.assign(dx=x).groupby(pair)["dx"].apply(lambda v: np.abs(v).max() > 1e-6).sum()
    return {"elasticity": float(b), "se": float(se), "t": float(b / se), "n_pairs_exposed": int(exposed),
            "years": list(years)}


def to_matrix(panel, value, countries=C.CORE):
    """Symmetric country x country x year array of a pair variable."""
    idx = {c: k for k, c in enumerate(countries)}
    yrs = list(YEARS)
    M = np.full((len(yrs), len(countries), len(countries)), np.nan)
    for r in panel[["i", "j", "year", value]].itertuples(index=False):
        if r.i in idx and r.j in idx and r.year in yrs:
            t = r.year - yrs[0]
            M[t, idx[r.i], idx[r.j]] = M[t, idx[r.j], idx[r.i]] = getattr(r, value)
    return M
