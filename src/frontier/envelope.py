"""Frontier envelopes: the best (or top-k average) level among a fixed set of economies."""
import numpy as np
import pandas as pd


def wide(df, value, countries, years=None):
    w = df[df.iso.isin(countries)].pivot_table(index="year", columns="iso", values=value)
    if years is not None:
        w = w.reindex(years)
    return w


def envelope(df, value, countries, kind="max", k=5):
    """Return a DataFrame with the envelope level and, for kind='max', the leader's iso.

    kind='max' takes the highest level each year; kind='topk' takes the geometric
    mean of the k highest levels among the countries observed that year.
    """
    w = wide(df, value, countries)
    if kind == "max":
        level = w.max(axis=1)
        leader = w.idxmax(axis=1)
        return pd.DataFrame({"level": level, "leader": leader})
    logs = np.log(w)
    top = logs.apply(lambda r: r.dropna().nlargest(k).mean(), axis=1)
    return pd.DataFrame({"level": np.exp(top)})


def growth(level):
    """Annual log growth in percent."""
    return 100 * np.log(level).diff()


def leader_spells(leader):
    """Collapse a yearly leader series into (start, end, iso) spells."""
    spells, prev, start = [], None, None
    for year, iso in leader.items():
        if iso != prev:
            if prev is not None:
                spells.append((start, year - 1, prev))
            prev, start = iso, year
    spells.append((start, leader.index[-1], prev))
    return spells


def episode_growth(level, episodes):
    """Annualized log growth between episode endpoints (start-1 to end)."""
    rows = []
    for a, b, label in episodes:
        a0 = a - 1 if (a - 1) in level.index else a
        rows.append({"episode": label, "start": a, "end": b,
                     "growth": 100 * (np.log(level[b]) - np.log(level[a0])) / (b - a0)})
    return pd.DataFrame(rows)
