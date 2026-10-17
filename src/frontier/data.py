"""Download and load the raw datasets into tidy (iso, year, value) frames."""
import io
import zipfile

import numpy as np
import pandas as pd
import requests

from . import config as C

HEADERS = {"User-Agent": "Mozilla/5.0 (research; frontier-growth project)"}


def download_all(force=False):
    """Fetch every raw file that is not already in data/raw."""
    C.RAW.mkdir(parents=True, exist_ok=True)
    for name, (fname, url) in C.SOURCES.items():
        path = C.RAW / fname
        if path.exists() and not force:
            continue
        print(f"downloading {name} ...")
        r = requests.get(url, headers=HEADERS, timeout=180)
        r.raise_for_status()
        path.write_bytes(r.content)
    wdi_path = C.RAW / "wdi.csv"
    if force or not wdi_path.exists():
        print("downloading World Bank WDI series ...")
        fetch_wdi().to_csv(wdi_path, index=False)


def fetch_wdi():
    rows = []
    countries = ";".join(C.WDI_COUNTRIES)
    for var, code in C.WDI_INDICATORS.items():
        url = (f"https://api.worldbank.org/v2/country/{countries}/indicator/{code}"
               f"?format=json&per_page=20000&date=1960:2024")
        payload = requests.get(url, headers=HEADERS, timeout=120).json()
        for obs in payload[1] or []:
            if obs["value"] is not None:
                rows.append({"iso": obs["countryiso3code"], "year": int(obs["date"]),
                             "var": var, "value": float(obs["value"])})
    return pd.DataFrame(rows)


def load_wdi():
    df = pd.read_csv(C.RAW / "wdi.csv")
    return df.pivot_table(index=["iso", "year"], columns="var", values="value").reset_index()


def load_maddison(countries=C.BROAD):
    m = pd.read_stata(C.RAW / C.SOURCES["maddison"][0])
    m = m.rename(columns={"countrycode": "iso"})
    m = m[m.iso.isin(countries) & m.year.between(C.START, C.END)]
    return m[["iso", "year", "gdppc", "pop"]].astype({"year": int}).reset_index(drop=True)


def _interpolate_log(s):
    """Log-linear interpolation of interior gaps in a positive series indexed by year."""
    return np.exp(np.log(s).interpolate(method="index", limit_area="inside"))


def load_openness():
    """Trade openness (exports + imports) / GDP, 1870-2022.

    Jorda-Schularick-Taylor R6 for 1870-2020 (gaps filled log-linearly);
    2021-2022 extended with World Bank trade-to-GDP growth.
    """
    j = pd.read_stata(C.RAW / C.SOURCES["jst"][0])
    j = j[j.iso.isin(C.CORE + ["NOR", "IRL"])].copy()
    j["open"] = (j["imports"] + j["exports"]) / j["gdp"]
    j.loc[~np.isfinite(j["open"]) | (j["open"] <= 0), "open"] = np.nan
    wdi = load_wdi()
    out = []
    for iso, g in j.groupby("iso"):
        s = g.set_index("year")["open"].reindex(range(C.START, C.END + 1))
        s = _interpolate_log(s)
        w = wdi[wdi.iso == iso].set_index("year")["trade_gdp"] / 100
        for y in (2021, 2022):
            if np.isnan(s.get(y, np.nan)) and y - 1 in w.index and y in w.index:
                s[y] = s[y - 1] * w[y] / w[y - 1]
        s = s.bfill().ffill()  # only touches leading/trailing gaps (e.g. Ireland pre-1922)
        out.append(pd.DataFrame({"iso": iso, "year": s.index, "open": s.values}))
    return pd.concat(out, ignore_index=True)


def load_bcl():
    """Bergeaud-Cette-Lecat: GDP per capita, GDP per hour and TFP (2020 PPP $), 1890-2024."""
    path = C.RAW / C.SOURCES["bcl"][0]
    sheets = {"gdppc_bcl": "GDP per capita", "gdp_per_hour": "Labor Productivity",
              "tfp": "TFP", "hours_pc": "L per capita"}
    frames = []
    for var, sheet in sheets.items():
        df = pd.read_excel(path, sheet_name=sheet, header=0)
        df = df.rename(columns={df.columns[0]: "year"}).dropna(subset=["year"])
        df = df.melt(id_vars="year", var_name="iso", value_name=var)
        df["year"] = df["year"].astype(int)
        frames.append(df.set_index(["iso", "year"]))
    out = pd.concat(frames, axis=1).reset_index()
    for col in sheets:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def load_patents():
    """Patent applications by national office, 1883-2021.

    WIPO historical statistics (office totals) for 1883-1979, World Bank WDI
    (resident + nonresident applications, sourced from WIPO) from 1980.
    Interior gaps (e.g. Germany 1944-48) are filled log-linearly.
    """
    with zipfile.ZipFile(C.RAW / C.SOURCES["wipo"][0]) as z:
        name = [n for n in z.namelist() if "filed" in n and n.endswith(".csv")][0]
        text = z.read(name).decode("latin-1")
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("filing_year"))
    h = pd.read_csv(io.StringIO("\n".join(lines[start:])))
    h["iso"] = h["office_code"].map(C.ISO2_TO_3)
    h = h.dropna(subset=["iso"])
    h["filings"] = pd.to_numeric(h["filings"], errors="coerce")
    tot = h[h.origin_code == "ZZ"].groupby(["iso", "filing_year"])["filings"].sum()
    parts = h[h.origin_code != "ZZ"].groupby(["iso", "filing_year"])["filings"].sum()
    hist = tot.combine_first(parts).rename("patents").reset_index()
    hist = hist.rename(columns={"filing_year": "year"})
    hist = hist[hist.year <= 1979]

    wdi = load_wdi()
    wdi = wdi[wdi.year >= 1980].copy()
    wdi["patents"] = wdi[["pat_res", "pat_nonres"]].sum(axis=1, min_count=1)
    modern = wdi[["iso", "year", "patents"]].dropna()

    both = pd.concat([hist, modern], ignore_index=True)
    out = []
    for iso, g in both.groupby("iso"):
        s = g.groupby("year")["patents"].sum()
        s = s[s > 0].reindex(range(s.index.min(), min(s.index.max(), 2021) + 1))
        s = _interpolate_log(s)
        out.append(pd.DataFrame({"iso": iso, "year": s.index, "patents": s.values}))
    return pd.concat(out, ignore_index=True).dropna()
