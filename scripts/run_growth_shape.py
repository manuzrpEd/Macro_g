"""Project 2: is long-run growth of GDP per capita exponential, additive, or slowly declining?

1  Full-sample fit (log-likelihood, AIC, BIC) for each model and series.
2  Prequential evaluation: each year from 1900, refit on the past and score the next
   year's outcome; cumulative scores give Bayesian model weights over time.
3  Long-horizon pseudo-out-of-sample forecasts (10 and 25 years): error and 90% coverage.
4  Power study: simulate data from each fitted model and ask how often each method
   picks the true model (can ~150 years tell the shapes apart?).
5  Robustness: wars neutralized, post-1950, other series (frontier envelope, BCL, UK).

Outputs: output/growth_shape/results.json, output/growth_shape/figures/*.png
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from frontier import config as C  # noqa: E402
from frontier import data, plots  # noqa: E402
from frontier import growthshape as G  # noqa: E402

OUT = C.ROOT / "output" / "growth_shape"
FIG = OUT / "figures"
MODELS = ["EXP", "EXPDEC", "DRIFT", "ADDH", "ADDP", "POW", "EXPB", "ADDPB"]
VT_MODELS = ["EXPVT", "ADDHVT", "ADDPVT", "POWVT"]
LABELS = {"EXP": "Exponential (constant growth)", "EXPDEC": "Exponential, linearly declining growth",
          "DRIFT": "Exponential, drifting growth", "ADDH": "Additive, homoskedastic noise",
          "ADDP": "Additive, proportional noise", "EXPB": "Exponential with one break",
          "ADDPB": "Additive (proportional noise) with one break",
          "POW": "Power: y^lambda linear in time (nests exponential and additive)",
          "EXPVT": "Exponential + volatility trend", "ADDHVT": "Additive homoskedastic + volatility trend",
          "ADDPVT": "Additive proportional + volatility trend", "POWVT": "Power + volatility trend"}


def fitm(m, y, t):
    if m == "POW":
        return G.fit_pow(y, t)
    if m.endswith("VT"):
        return G.fit_vt(m, y, t)
    return G.fit(m, y, t)


def llm(m, par, y, t):
    if m == "POW" or m.endswith("VT"):
        return G.loglik_ext(m, par, y, t)
    return G.loglik(m, par, y, t)


def scorem(m, par, yh, th, yn, tn):
    if m == "POW" or m.endswith("VT"):
        return G.one_step_ext(m, par, yh, tn, yn)
    return G.one_step_logscore(m, par, yh, th, yn, tn)


def pathsm(m, par, yh, th, h, n, rng):
    if m == "POW":
        return G.forecast_paths_pow(par, yh, h, n, rng)
    return G.forecast_paths(m, par, yh, th, h, n, rng)
FIRST_SCORED = 1900
WAR = [(1914, 1919), (1939, 1949)]


def series():
    mad = data.load_maddison()
    lv = pd.read_csv(C.PROCESSED / "frontier_levels.csv", index_col=0)
    bcl = data.load_bcl()
    out = {"US (Maddison)": mad[mad.iso == "USA"].set_index("year")["gdppc"],
           "Frontier envelope (max)": lv["max"].dropna(),
           "US (Bergeaud-Cette-Lecat)": bcl[(bcl.iso == "USA") & (bcl.year <= 2022)].set_index("year")["gdppc_bcl"],
           "US GDP per hour (Bergeaud-Cette-Lecat)": bcl[(bcl.iso == "USA") & (bcl.year <= 2022)].set_index("year")["gdp_per_hour"],
           "UK (Maddison)": mad[mad.iso == "GBR"].set_index("year")["gdppc"]}
    return {k: v.astype(float).sort_index() for k, v in out.items()}


def neutralize_levels(s, windows):
    """Replace growth inside windows by its window average (keeps the cumulative change)."""
    z = np.log(s).diff()
    for a, b in windows:
        idx = (z.index >= a) & (z.index <= b)
        z[idx] = z[idx].mean()
    lv = np.exp(np.log(s.iloc[0]) + z.fillna(0).cumsum())
    return lv


def full_sample(y, t, models=MODELS):
    res = {}
    n = len(y) - 1
    for m in models:
        par = fitm(m, y, t)
        ll = float(llm(m, par, y, t))
        k = par["k"]
        res[m] = {"loglik": ll, "aic": -2 * ll + 2 * k, "bic": -2 * ll + k * np.log(n),
                  "params": {kk: float(v) for kk, v in par.items() if kk != "profile"}}
        if m == "POW":
            prof = np.array(par["profile"])
            ok = 2 * (prof[:, 1].max() - prof[:, 1]) <= 3.84
            res[m]["lambda_ci95"] = [float(prof[ok, 0].min()), float(prof[ok, 0].max())]
            res[m]["lr_vs_exponential_lambda0"] = float(2 * (prof[:, 1].max() - prof[0, 1]))
            res[m]["lr_vs_additive_lambda1"] = float(2 * (prof[:, 1].max() - prof[np.argmin(abs(prof[:, 0] - 1)), 1]))
            res[m]["profile"] = prof.tolist()
    return res


def prequential(y, t, first=FIRST_SCORED, models=MODELS, refit_every=1):
    scores = {m: [] for m in models}
    years = []
    pars = {}
    for i in range(len(t)):
        if t[i] < first:
            continue
        if not pars or (len(years) % refit_every == 0):
            pars = {m: fitm(m, y[:i], t[:i]) for m in models}
        for m in models:
            scores[m].append(float(scorem(m, pars[m], y[:i], t[:i], y[i], t[i])))
        years.append(int(t[i]))
    S = pd.DataFrame(scores, index=years)
    cum = S.cumsum()
    w = np.exp(cum.sub(cum.max(axis=1), axis=0))
    w = w.div(w.sum(axis=1), axis=0)
    return S, w


def long_horizon(y, t, h, rng, models=MODELS, n=400):
    rows = []
    for i in range(len(t)):
        if t[i] < FIRST_SCORED or i + h >= len(t):
            continue
        actual = np.log(y[i + h])
        for m in models:
            par = fitm(m, y[:i + 1], t[:i + 1])
            paths = pathsm(m, par, y[:i + 1], t[:i + 1], h, n, rng)[:, -1]
            lo, hi = np.percentile(paths, [5, 95])
            rows.append({"origin": int(t[i]), "model": m, "err": float(np.median(paths) - actual),
                         "covered": bool(lo <= actual <= hi)})
    df = pd.DataFrame(rows)
    return df.groupby("model").agg(rmse=("err", lambda e: float(np.sqrt(np.mean(e ** 2)))),
                                   mean_err=("err", "mean"), coverage90=("covered", "mean"),
                                   n=("err", "size")).to_dict(orient="index")


def power_study(y, t, rng, reps=200):
    """Simulate from each fitted model; how often does BIC / prequential weight pick the truth?"""
    cands = ["EXP", "EXPDEC", "DRIFT", "ADDH", "ADDP", "POW"]
    dgps = {m: fitm(m, y, t) for m in cands}
    n = len(y) - 1
    out = {}
    for true_m, par in dgps.items():
        bic_w, pre_w, lams = {}, {}, []
        for _ in range(reps):
            ys = G.simulate_pow(par, y[0], t, rng) if true_m == "POW" else G.simulate(true_m, par, y[0], t, rng)
            fits = {m: fitm(m, ys, t) for m in cands}
            bic = {m: -2 * llm(m, fits[m], ys, t) + fits[m]["k"] * np.log(n) for m in cands}
            wb = min(bic, key=bic.get)
            bic_w[wb] = bic_w.get(wb, 0) + 1
            lams.append(fits["POW"]["lam"])
            S, _ = prequential(ys, t, models=[m for m in cands if m != "POW"], refit_every=10)
            wp = S.sum().idxmax()
            pre_w[wp] = pre_w.get(wp, 0) + 1
        lams = np.array(lams)
        out[true_m] = {"bic": {k: v / reps for k, v in bic_w.items()},
                       "prequential": {k: v / reps for k, v in pre_w.items()},
                       "lambda_hat": {"median": float(np.median(lams)), "p10": float(np.percentile(lams, 10)),
                                      "p90": float(np.percentile(lams, 90))},
                       "true_lambda": float(par.get("lam", 0.0 if true_m.startswith("EXP") or true_m == "DRIFT" else 1.0))}
    return out


def main(quick=False):
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(2027)
    R = {"models": LABELS, "first_scored": FIRST_SCORED}
    S = series()
    variants = {}
    for name, s in S.items():
        variants[name] = s
    variants["US (Maddison), wars neutralized"] = neutralize_levels(S["US (Maddison)"], WAR)
    variants["US (Maddison), 1950-2022"] = S["US (Maddison)"].loc[1950:]
    R["series"] = {}
    weights_store = {}
    for name, s in variants.items():
        t = s.index.values.astype(float)
        y = s.values
        first = FIRST_SCORED if t[0] < FIRST_SCORED - 25 else int(t[0]) + 25
        fs = full_sample(y, t)
        if name in ("US (Maddison)", "US GDP per hour (Bergeaud-Cette-Lecat)"):
            fs_vt = full_sample(y, t, models=VT_MODELS)
            fs.update(fs_vt)
            Svt, _ = prequential(y, t, first=first, models=VT_MODELS + ["EXP", "ADDP", "POW"], refit_every=5)
        Ssc, w = prequential(y, t, first=first)
        weights_store[name] = w
        entry = {"years": [int(t[0]), int(t[-1])], "full_sample": fs,
                 "best_bic": min(fs, key=lambda m: fs[m]["bic"]),
                 "prequential_total": Ssc.sum().to_dict(),
                 "prequential_by_period": {
                     f"{a}-{b}": Ssc.loc[a:b].sum().to_dict() for a, b in [(first, 1949), (1950, 1994), (1995, 2022)]
                     if len(Ssc.loc[a:b])},
                 "final_weights": w.iloc[-1].to_dict(), "weights_1950": w.loc[1950].to_dict() if 1950 in w.index else None}
        if name in ("US (Maddison)", "US GDP per hour (Bergeaud-Cette-Lecat)"):
            entry["prequential_total_with_vol_trend"] = Svt.sum().to_dict()
        if name in ("US (Maddison)", "Frontier envelope (max)", "US (Maddison), wars neutralized"):
            entry["long_horizon"] = {h: long_horizon(y, t, h, rng, n=200 if quick else 400) for h in (10, 25)}
        R["series"][name] = entry
        print("done", name)
    s = S["US (Maddison)"]
    R["power_us"] = power_study(s.values, s.index.values.astype(float), rng, reps=60 if quick else 200)
    pd.concat(weights_store, axis=1).to_csv(OUT / "model_weights.csv")
    with open(OUT / "results.json", "w") as f:
        json.dump(R, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    figures(R, S, weights_store)
    print("done: output/growth_shape/results.json")


def figures(R, S=None, W=None):
    P = plots
    src = "Sources: Maddison Project Database 2023; Bergeaud–Cette–Lecat v2.7; own calculations."
    # G1 profile likelihood of the curvature lambda
    fig, ax = P.setup(figsize=(10, 5.2))
    show = [("US (Maddison)", P.BLUE, "-"), ("Frontier envelope (max)", P.DARK, "-"),
            ("US GDP per hour (Bergeaud-Cette-Lecat)", P.RED, "-"), ("UK (Maddison)", P.GREY, "-"),
            ("US (Maddison), 1950-2022", "#8db8ea", (0, (4, 3)))]
    for name, col, ls in show:
        prof = np.array(R["series"][name]["full_sample"]["POW"]["profile"])
        ax.plot(prof[:, 0], 2 * (prof[:, 1].max() - prof[:, 1]), color=col, lw=2, ls=ls, label=name)
    ax.axhline(3.84, color="#999999", lw=0.9, ls=(0, (2, 2)))
    ax.text(1.48, 4.2, "95% cutoff", ha="right", fontsize=8, color="#555555")
    for x, lab in [(0.0, "exponential"), (2 / 3, "additive TFP"), (1.0, "additive GDP")]:
        ax.axvline(x, color="#cccccc", lw=0.8)
        ax.text(x + 0.01, 24, lab, fontsize=8, color="#555555", rotation=90, va="top")
    ax.set_ylim(0, 25)
    ax.set_xlim(0, 1.5)
    ax.set_xlabel("λ: curvature (y^λ grows linearly in time)", color="#555555")
    ax.set_ylabel("Likelihood-ratio statistic vs best λ", color="#555555")
    ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0.12, 1))
    P.titles(fig, "Over 150 years, the curvature points to exponential growth; pure additivity is rejected",
             "Profile likelihood of λ in the power model; values above the dashed line are rejected at 5%", src)
    P.save(fig, FIG / "g1_lambda_profile.png")

    # G2 prequential model weights over time (US)
    if W is None:
        W = pd.read_csv(OUT / "model_weights.csv", header=[0, 1], index_col=0)
    w = W["US (Maddison)"]
    fig, ax = P.setup(figsize=(10, 5))
    for m, col in [("EXP", P.BLUE), ("ADDPB", P.RED), ("ADDH", P.GREY), ("DRIFT", "#8db8ea"), ("ADDP", "#e3a08f")]:
        ax.plot(w.index.astype(int), w[m], color=col, lw=2 if m in ("EXP", "ADDPB") else 1.4, label=LABELS[m])
    ax.set_ylim(0, 1)
    ax.set_xlim(1900, 2022)
    ax.set_ylabel("Posterior model weight (equal priors)", color="#555555")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    P.titles(fig, "Real-time evidence keeps switching between models",
             "US GDP per capita: cumulative one-step predictive scores since 1900, refitting each year", src)
    P.save(fig, FIG / "g2_weights_us.png")

    # G3 power: how often each method picks the true model
    pw = R["power_us"]
    truths = ["EXP", "EXPDEC", "DRIFT", "ADDP", "ADDH"]
    fig, ax = P.setup(figsize=(10, 4.8))
    x = np.arange(len(truths))
    ax.bar(x - 0.18, [pw[t]["bic"].get(t, 0) for t in truths], 0.36, color=P.BLUE, label="BIC (full sample)")
    ax.bar(x + 0.18, [pw[t]["prequential"].get(t, 0) for t in truths], 0.36, color="#8db8ea", label="Prequential score")
    for i, t in enumerate(truths):
        ax.text(i - 0.18, pw[t]["bic"].get(t, 0) + 0.02, f"{pw[t]['bic'].get(t, 0):.0%}", ha="center", fontsize=8)
        ax.text(i + 0.18, pw[t]["prequential"].get(t, 0) + 0.02, f"{pw[t]['prequential'].get(t, 0):.0%}", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(["Exponential", "Declining" + chr(10) + "growth", "Drifting" + chr(10) + "growth", "Additive" + chr(10) + "(prop. noise)", "Additive" + chr(10) + "(level noise)"])
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Share of simulations picking the true model", color="#555555")
    ax.legend(frameon=False, fontsize=9, loc="upper center")
    P.titles(fig, "150 years can separate exponential from additive, but not constant from slowly declining",
             "Power study: 200 simulated US histories from each fitted model (true model on the x-axis)", src)
    P.save(fig, FIG / "g3_power.png")

    # G4 long-horizon forecast accuracy
    lh = R["series"]["US (Maddison)"]["long_horizon"]
    ms = ["EXP", "DRIFT", "EXPDEC", "POW", "ADDP", "ADDPB", "ADDH"]
    fig, ax = P.setup(figsize=(10, 4.8))
    x = np.arange(len(ms))
    for j, (h, col) in enumerate([("10", "#8db8ea"), ("25", P.BLUE)]):
        vals = [lh[h][m]["rmse"] for m in ms]
        ax.bar(x + (j - 0.5) * 0.36, vals, 0.36, color=col, label=f"{h}-year horizon")
        for xi, m, v in zip(x + (j - 0.5) * 0.36, ms, vals):
            ax.text(xi, v + 0.005, f"{100 * lh[h][m]['coverage90']:.0f}%", ha="center", fontsize=7, color="#555555")
    ax.set_xticks(x)
    short = {"EXP": "Exponential", "DRIFT": "Exp., drifting", "EXPDEC": "Exp., declining", "POW": "Power (λ)",
             "ADDP": "Additive", "ADDPB": "Additive," + chr(10) + "one break", "ADDH": "Additive," + chr(10) + "level noise"}
    ax.set_xticklabels([short[m] for m in ms], fontsize=8.5)
    ax.set_ylabel("RMSE of log GDP per capita forecast", color="#555555")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    P.titles(fig, "For long-horizon forecasting, plain exponential growth is hard to beat",
             "US GDP per capita, forecasts made each year 1900–2012; labels: coverage of 90% intervals", src)
    P.save(fig, FIG / "g4_long_horizon.png")


if __name__ == "__main__":
    if "--figures-only" in sys.argv:
        FIG.mkdir(parents=True, exist_ok=True)
        figures(json.load(open(OUT / "results.json")))
    else:
        main(quick="--quick" in sys.argv)
