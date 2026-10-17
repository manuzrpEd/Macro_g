"""Pre-registered break test E1 (findings_register.md): is there a slow-fast-slow pattern in frontier growth
when the data choose the break years?

Bai-Perron test of breaks in mean annual growth of top-5 frontier GDP per capita, 1871-2022:
max 2 breaks, minimum regime 10% of the sample, moving-block bootstrap p-values under the null.
Robustness: 10-year blocks; minimum regime 15%. Envelope (max) and US reported for information only.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from frontier import breaks  # noqa: E402
from frontier import config as C  # noqa: E402

OUT = C.ROOT / "output" / "break_test_frontier"


def run(series, trim, block, reps=1999):
    z = (100 * np.log(series).diff()).loc[1871:2022].dropna()
    r = breaks.bai_perron(z.values, z.index.values, max_breaks=2, trim=trim, reps=reps, block=block, seed=7, resid="null")
    two = r["all_solutions"][2]
    means = [g["mean"] for g in two["regimes"]]
    return {"trim": trim, "block": block, "min_regime_years": r["h"],
            "supF_1break": r["supF"][0], "p_1break": r["p_supF"][0],
            "supF_2breaks": r["supF"][1], "p_2breaks": r["p_supF"][1],
            "UDmax": r["UDmax"], "p_UDmax": r["p_UDmax"], "p_seq_2given1": r["p_seqF"][0],
            "two_break_solution": two, "slow_fast_slow": bool(means[1] > means[0] and means[1] > means[2]),
            "one_break_solution": r["all_solutions"][1]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    f = pd.read_csv(C.ROOT / "data" / "processed" / "frontier_levels.csv").set_index("year")
    R = {"main": run(f.top5, 0.10, 5), "robust_block10": run(f.top5, 0.10, 10), "robust_trim15": run(f.top5, 0.15, 5),
         "info_envelope_max": run(f["max"], 0.10, 5), "info_us": run(f.us, 0.10, 5)}
    m, b10, t15 = R["main"], R["robust_block10"], R["robust_trim15"]
    if m["p_2breaks"] < 0.05 and m["slow_fast_slow"] and b10["p_2breaks"] < 0.10 and t15["p_2breaks"] < 0.10:
        verdict = "Established"
    elif m["p_2breaks"] < 0.10:
        verdict = "Suggestive"
    else:
        verdict = "Not established"
    R["verdict_A5"] = verdict
    with open(OUT / "results.json", "w") as fh:
        json.dump(R, fh, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    for k, v in R.items():
        if k == "verdict_A5":
            continue
        regs = "; ".join(f"{g['from']}-{g['to']}: {g['mean']:.2f}%" for g in v["two_break_solution"]["regimes"])
        print(f"{k:18s} p(2 breaks)={v['p_2breaks']:.3f} p(1 break)={v['p_1break']:.3f} p(UDmax)={v['p_UDmax']:.3f} | {regs}")
    print("verdict A5:", verdict)


if __name__ == "__main__":
    main()
