"""Project-wide settings: paths, samples, episodes and data sources."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "output" / "figures"
TABLES = ROOT / "output" / "tables"

START, END = 1870, 2022

# Fixed set of leading economies, chosen ex ante: the Jorda-Schularick-Taylor
# sample (which carries trade data back to 1870) minus Norway (oil rents after
# the 1970s) and Ireland (multinational profit shifting after the 2010s).
CORE = ["AUS", "BEL", "CAN", "CHE", "DEU", "DNK", "ESP", "FIN",
        "FRA", "GBR", "ITA", "JPN", "NLD", "PRT", "SWE", "USA"]
# Broader Maddison set used only for envelope robustness checks.
BROAD = CORE + ["AUT", "NZL", "NOR", "IRL"]

# The frontier research hub: its own research counts fully toward the frontier.
HUB = "USA"

EPISODES = [
    (1870, 1913, "Globalization wave"),
    (1914, 1949, "Closure"),
    (1950, 1994, "Re-integration"),
    (1995, 2022, "Internet"),
]
# Years dropped from annual tests: the world wars plus the first demobilization year.
WAR_YEARS = list(range(1914, 1920)) + list(range(1939, 1947))
PEACETIME_CLOSURE = (1929, 1938)

# Leaders that lost international links in 1914-45 without large-scale war damage at home.
UNDAMAGED = ["USA", "CHE", "SWE"]
DAMAGED = ["BEL", "DEU", "FRA", "ITA", "JPN", "NLD"]

CAPITAL_SHARE = 1 / 3  # output per person grows at g_A / (1 - capital share)
LF_Q = 12  # Mueller-Watson cosine terms: keeps periods of 2T/q ~ 25 years and longer

WDI_COUNTRIES = CORE + ["NOR", "IRL", "AUT", "NZL"]

SOURCES = {
    "maddison": ("maddison2023_web.dta",
                 "https://dataverse.nl/api/access/datafile/421303"),
    "jst": ("JSTdatasetR6.dta",
            "https://www.macrohistory.net/app/download/9834512469/JSTdatasetR6.dta?t=1720600177"),
    "bcl": ("BCLDatabase_online_v2.7.xlsx",
            "https://www.longtermproductivity.com/download/BCLDatabase_online_v2.7.xlsx"),
    "wipo": ("wipo_ip_historical_data.zip",
             "https://www.wipo.int/documents/2948119/3215563/wipo_ip_historical_data.zip"),
}
WDI_INDICATORS = {
    "pat_res": "IP.PAT.RESD",      # patent applications, residents
    "pat_nonres": "IP.PAT.NRES",   # patent applications, nonresidents
    "trade_gdp": "NE.TRD.GNFS.ZS",  # trade, % of GDP
}

# WIPO two-letter office codes to ISO3.
ISO2_TO_3 = {
    "AU": "AUS", "AT": "AUT", "BE": "BEL", "CA": "CAN", "CH": "CHE", "DE": "DEU",
    "DK": "DNK", "ES": "ESP", "FI": "FIN", "FR": "FRA", "GB": "GBR", "IE": "IRL",
    "IT": "ITA", "JP": "JPN", "NL": "NLD", "NO": "NOR", "NZ": "NZL", "PT": "PRT",
    "SE": "SWE", "US": "USA",
}
