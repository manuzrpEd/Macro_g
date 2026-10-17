"""Bai-Perron (1998, 2003) multiple structural breaks in the mean of a series.

Model: y_t = mu_j + e_t within each of m+1 regimes. Break dates minimize the total
sum of squared residuals by dynamic programming. Because annual growth rates are
fat-tailed and serially correlated, p-values come from a moving-block bootstrap
of regime-demeaned residuals under the null of a constant mean, rather than from
the asymptotic tables.
"""
import numpy as np


class _Segments:
    def __init__(self, y):
        self.c1 = np.concatenate([[0.0], np.cumsum(y)])
        self.c2 = np.concatenate([[0.0], np.cumsum(y * y)])

    def ssr(self, i, j):
        """SSR of y[i..j] (inclusive) around its own mean; i, j may be arrays."""
        n = j - i + 1
        s1 = self.c1[j + 1] - self.c1[i]
        s2 = self.c2[j + 1] - self.c2[i]
        return s2 - s1 * s1 / n


def optimal_partitions(y, max_breaks, h):
    """Global SSR minimizers for 0..max_breaks breaks.

    Returns (ssr[m], ends[m]) where ends[m] lists the last index of each of the
    first m regimes.
    """
    T = len(y)
    seg = _Segments(np.asarray(y, float))
    INF = np.inf
    dp = np.full((max_breaks + 1, T), INF)
    arg = np.zeros((max_breaks + 1, T), dtype=int)
    j_all = np.arange(T)
    ok0 = j_all >= h - 1
    dp[0, ok0] = seg.ssr(np.zeros(ok0.sum(), int), j_all[ok0])
    for m in range(1, max_breaks + 1):
        for j in range((m + 1) * h - 1, T):
            i = np.arange(m * h - 1, j - h + 1)
            cand = dp[m - 1, i] + seg.ssr(i + 1, np.full(len(i), j))
            k = np.argmin(cand)
            dp[m, j], arg[m, j] = cand[k], i[k]
    ssr, ends = [], []
    for m in range(max_breaks + 1):
        ssr.append(dp[m, T - 1])
        e, j = [], T - 1
        for mm in range(m, 0, -1):
            j = arg[mm, j]
            e.append(j)
        ends.append(sorted(e))
    return np.array(ssr), ends


def _stats(y, max_breaks, h):
    T = len(y)
    ssr, ends = optimal_partitions(y, max_breaks, h)
    supf = np.array([((T - k - 1) / k) * (ssr[0] - ssr[k]) / ssr[k]
                     for k in range(1, max_breaks + 1)])
    seg = _Segments(np.asarray(y, float))
    seq = []
    for l in range(1, max_breaks):
        bounds = [-1] + ends[l] + [T - 1]
        best = 0.0
        for a, b in zip(bounds[:-1], bounds[1:]):
            lo, hi = a + 1, b
            if hi - lo + 1 < 2 * h:
                continue
            base = seg.ssr(lo, hi)
            cut = np.arange(lo + h - 1, hi - h + 1)
            gain = base - (seg.ssr(np.full(len(cut), lo), cut) + seg.ssr(cut + 1, np.full(len(cut), hi)))
            best = max(best, gain.max())
        seq.append(best / (ssr[l] / (T - l - 1)))
    return ssr, ends, supf, np.array(seq)


def block_bootstrap(x, block, rng):
    T = len(x)
    n_blocks = int(np.ceil(T / block))
    starts = rng.integers(0, T - block + 1, n_blocks)
    return np.concatenate([x[s:s + block] for s in starts])[:T]


def bai_perron(y, years, max_breaks=4, trim=0.15, reps=999, block=5, seed=0, resid="null"):
    """Estimate breaks and test them. Returns a dict of results.

    Number of breaks is selected by BIC; sup-F, UDmax and sequential sup-F(l+1|l)
    p-values come from a moving-block bootstrap of the demeaned series.
    """
    y = np.asarray(y, float)
    years = np.asarray(years)
    T = len(y)
    h = max(2, int(np.floor(trim * T)))
    ssr, ends, supf, seq = _stats(y, max_breaks, h)
    bic = [np.log(ssr[m] / T) + (2 * m + 1) * np.log(T) / T for m in range(max_breaks + 1)]
    m_bic = int(np.argmin(bic))

    rng = np.random.default_rng(seed)
    # resid="null": resample the demeaned series (conservative when breaks exist).
    # resid="bic": resample residuals from the BIC-selected break model (more power,
    # but over-rejects in simulations; reported only as a sensitivity check).
    e = y.copy()
    m_res = 0 if resid == "null" else m_bic
    bounds = [-1] + ends[m_res] + [T - 1]
    for a, b in zip(bounds[:-1], bounds[1:]):
        e[a + 1:b + 1] -= y[a + 1:b + 1].mean()
    boot_supf = np.zeros((reps, max_breaks))
    boot_ud = np.zeros(reps)
    boot_seq = np.zeros((reps, max_breaks - 1))
    for r in range(reps):
        yb = block_bootstrap(e, block, rng)
        _, _, sf, sq = _stats(yb, max_breaks, h)
        boot_supf[r], boot_ud[r], boot_seq[r] = sf, sf.max(), sq
    p_supf = (boot_supf >= supf).mean(axis=0)
    p_ud = (boot_ud >= supf.max()).mean()
    p_seq = (boot_seq >= seq).mean(axis=0)

    # Sequential selection at 5%: start from UDmax, add breaks while sup-F(l+1|l) rejects.
    m_seq = 0
    if p_ud < 0.05:
        m_seq = 1
        for l, p in enumerate(p_seq, start=1):
            if p < 0.05:
                m_seq = l + 1
            else:
                break

    def describe(m):
        bounds = [-1] + ends[m] + [T - 1]
        regimes = []
        for a, b in zip(bounds[:-1], bounds[1:]):
            regimes.append({"from": int(years[a + 1]), "to": int(years[b]),
                            "mean": float(y[a + 1:b + 1].mean()), "n": int(b - a)})
        return {"break_years": [int(years[i]) for i in ends[m]], "regimes": regimes}

    return {
        "T": T, "h": h, "supF": supf.tolist(), "p_supF": p_supf.tolist(),
        "UDmax": float(supf.max()), "p_UDmax": float(p_ud),
        "seqF": seq.tolist(), "p_seqF": p_seq.tolist(),
        "m_bic": m_bic, "m_seq": m_seq,
        "bic_solution": describe(m_bic), "seq_solution": describe(m_seq),
        "all_solutions": {m: describe(m) for m in range(max_breaks + 1)},
    }
