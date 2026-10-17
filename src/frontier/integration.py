"""Integration weights and the effective world research pool.

The effective pool is S_eff = sum_i w_i S_i with w_i = min(1, (open_i / OPEN_REF)^kappa)
for every country except the research hub, whose own research always counts fully.
kappa = 0 gives the conventional unweighted world pool (the null hypothesis).
Pool growth is chain-linked so that countries entering the data do not create jumps.
"""
import numpy as np
import pandas as pd

from . import config as C

OPEN_REF = 1.0  # trade worth 100% of GDP counts as fully connected


def weights(open_w, kappa, hub=C.HUB, ref=OPEN_REF):
    w = np.minimum(1.0, (open_w / ref) ** kappa)
    if hub in w.columns:
        w[hub] = 1.0
    return w


def pool_growth(S, open_w, kappa, hub=C.HUB):
    """Chain-linked growth (log points x 100) of the effective pool and its two parts.

    Returns a DataFrame with:
      g_eff   growth of sum_i w_i S_i
      g_scale sum_i s_i dlog S_i   (growth of research itself, at last year's shares)
      g_int   sum_i s_i dlog w_i   (integration component)
    """
    S = S.reindex(columns=open_w.columns)
    w = weights(open_w.reindex(S.index), kappa, hub)
    eff = w * S
    rows = []
    for t in range(1, len(S.index)):
        y0, y1 = S.index[t - 1], S.index[t]
        ok = eff.loc[y0].notna() & eff.loc[y1].notna() & (eff.loc[y0] > 0)
        if ok.sum() == 0:
            rows.append((y1, np.nan, np.nan, np.nan))
            continue
        share = eff.loc[y0, ok] / eff.loc[y0, ok].sum()
        g_s = np.log(S.loc[y1, ok] / S.loc[y0, ok])
        g_w = np.log(w.loc[y1, ok] / w.loc[y0, ok])
        rows.append((y1, 100 * (share * (g_s + g_w)).sum(),
                     100 * (share * g_s).sum(), 100 * (share * g_w).sum()))
    out = pd.DataFrame(rows, columns=["year", "g_eff", "g_scale", "g_int"]).set_index("year")
    out["level"] = np.exp(out["g_eff"].fillna(0).cumsum() / 100)
    return out


def world_openness(open_w, gdp_w, exclude=(C.HUB,)):
    """GDP-weighted mean openness of the non-hub economies."""
    cols = [c for c in open_w.columns if c not in exclude]
    wts = gdp_w.reindex(index=open_w.index, columns=cols)
    return (open_w[cols] * wts).sum(axis=1) / wts.where(open_w[cols].notna()).sum(axis=1)
