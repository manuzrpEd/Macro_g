# Findings Register

Last audited 17 October 2026 · @Manuel Antonio Sanchez Garcia

**Purpose.** This is the single source of truth for what this project has found. Summaries and papers must not claim more than this register. Any change is logged at the bottom with its date and reason.

**Confidence levels**

| Level | Meaning |
| --- | --- |
| **Established** | Holds in the main test *and* in its robustness checks; or a descriptive fact from validated data |
| **Suggestive** | Significant in the main specification, but fragile, exploratory, not pre-registered, based on few long cycles, or from a single country |
| **Not established** | Tested and not supported (insignificant or failed) |
| **Not tested by us** | Taken from the literature only |

---

## A. Is long-run growth constant?

| # | Claim | Evidence | Level | Source |
| --- | --- | --- | --- | --- |
| A1 | Constant (exponential) growth is never statistically rejected for US, UK, frontier-envelope or US-per-hour GDP | Box–Cox λ ≈ 0–0.1; LR vs exponential ≤ 0.4; Bai–Perron break test on frontier growth p = 0.33 | **Established** | paper_growth_shape §3; paper_deglobalization_frontier, finding 1 |
| A2 | A single additive (fixed dollar increment) path since 1870 is rejected | LR vs additive 4.8–23.6 in every long series | **Established** | paper_growth_shape §3 |
| A3 | "Additive since the 1930s" predicts slightly better in real time | log Bayes factor 4.6 (US), 2.3 (envelope), 0.5 (UK); weights unstable over time | **Suggestive** | paper_growth_shape §4 |
| A4 | Slow declines in trend growth are hard to detect in 150 years of data | A 2.5% → 1.0% decline is detected 35% of the time; 2.0% → 1.5% only 10% | **Established** (simulation) | paper_growth_shape §5; output/growth_shape/power_calibrated.json |
| A5 | **Top-5 frontier average** has a slow–fast–slow pattern that is stronger than noise | With cut-offs chosen after looking at the data (1929/2007): 1.14% / 2.05% / 0.94%, HAC t = 2.1 and −2.6. **With break years chosen by the test (pre-registered E1):** 0.89% (1871–1933) / 2.32% (1934–2007) / 0.94% (2008–22), but p = 0.27 (robustness 0.26–0.27). Noise can produce this pattern | **Not established** | scripts/run_break_test_frontier.py; scripts/run_headline_numbers.py |
| A6 | For the **US alone** and the **single-leader envelope**, the era differences are within noise | US: rise t = 0.4, fall t = −1.2; break test p = 0.44. Envelope: rise t = 1.1, fall t = −1.6 to −2.0; break test p = 0.65 | **Established** (no significant hump) | scripts/run_headline_numbers.py; scripts/run_break_test_frontier.py |
| A7 | The US caught up to the leader before 1900 | 82% of the leading GDP per capita in 1870; leader for most years from 1899 (Switzerland led in 1931–34, 1971 and from 2006); US grew 1.74% vs frontier 1.07–1.11% in 1870–99 | **Established** (descriptive, Maddison) | scripts/run_headline_numbers.py |
| A8 | Independent productivity evidence shows a mid-century wave in the leading economies | Bergeaud–Cette–Lecat (2016); industry data show 95% of US industries improving in 1919–29 | **Established** (literature and our industry data) | paper_sectoral_averaging §4 |

## B. Is there a force that keeps growth at 2%?

| # | Claim | Evidence | Level | Source |
| --- | --- | --- | --- | --- |
| B1 | Capital, hours and productivity do not offset each other over the long run | Per-person variance ratio: leaders 0.89 (p = 0.24), US 1.10; the per-hour "offsetting" is a definitional artifact | **Established** | paper_balancing_leader §3–4 |
| B2 | At the US, hours *amplify* long swings | Without hours swings, long-run US growth would be 45% smoother; holds with Ramey–Francis hours | **Established** | paper_balancing_leader §4 |
| B3 | "Schooling and the rest of TFP offset each other" | Variance ratio 0.78, but this equals a TFP-on-schooling slope below 1, which measurement error alone produces | **Not established** | paper_balancing_leader §6 (correction note); paper_education_productivity §8 |
| B4 | US research effort does not lean against productivity slowdowns | All long-run responses are positive (strongest +2.8, 15-year lag, p = 0.008), driven by one Cold War episode | **Established** (no stabilizing sign); the positive feedback itself is **Suggestive** | paper_research_effort §5 |
| B5 | Across OECD countries there is a *relative* stabilizer | Researchers −0.78 (p = 0.016) with period effects; disappears without them (−0.11) | **Suggestive** (does not apply to the frontier as a whole) | paper_research_effort §5 |
| B6 | Population and research intensity do not offset each other | Variance ratio 1.05 (independence 1.00, p = 0.64); OECD within-country correlation −0.04 | **Established** (no offset detected; low power) | paper_research_effort §4 |
| B7 | Industries do not offset each other | Variance ratio R ≥ 1 in every sample and source (1.2–3.3) | **Established** | paper_sectoral_averaging §3 |
| B8 | Averaging across industries removes most industry noise | Aggregate swings 0.39 pp vs 1.90 if all industries moved together | **Established** (descriptive) | paper_sectoral_averaging §3 |
| B9 | Baumol reweighting does not stabilize growth | Pre-1941: fast industries *gain* share (+0.28, p = 0.002); post-1948: −0.08 (n.s.); freezing weights changes swings ≤ 9% | **Established** (not a stabilizer); the level drag of −0.13 pp/yr is **Suggestive** | paper_sectoral_averaging §5 |
| B10 | Policy (inflation targets, fiscal, pensions) does not set the long-run rate | Jones (1995): trend growth unchanged despite large policy changes | **Not tested by us** | literature |
| B11 | Integration-weighted world idea flows sustain frontier growth | Integration weighting fits worse (best κ = 0); income–integration link looks like reverse causality | **Not established** | paper_deglobalization_frontier |

## C. What drives the slow–fast–slow pattern (where it exists)?

| # | Claim | Evidence | Level | Source |
| --- | --- | --- | --- | --- |
| C1 | After 1930, US productivity follows research effort with a 5–10 year lag | Response 0.23 (p = 0.03); β ≈ 2.3–3.0 with Bloom et al.'s measure | **Suggestive** (one country, about 7 long cycles) | paper_balancing_leader §7; paper_research_effort §5–6 |
| C2 | US research effort did not grow steadily | About 8% a year before 1960, about 2–3% after (all measures) | **Established** (descriptive) | paper_research_effort §3 |
| C3 | β is stable over time | Stable (2.3–3.0) only when software and other intellectual property count as research; halves with R&D alone | **Not established** (measurement-dependent) | paper_research_effort §6 |
| C4 | US research labour grew about 6.6% a year in 1850–1930, about 2.9% after | IPUMS 1% samples, within ±7% of Blank & Stigler | **Established** (descriptive) | paper_research_labor_history §2–3 |
| C5 | Steady-state β is stable across eras | About 6 before 1930, 1.7–2.3 after | **Not established** | paper_research_labor_history §4 |
| C6 | The dynamic research-transition model reproduces the hump | In sample R² 0.38 (US), 0.43 (frontier); labour-force placebo ≈ 0 | **Suggestive** (exploratory, in sample only) | paper_research_labor_history §6 |
| C7 | The research-transition model predicts out of sample | Loses to constant growth (US 0.71 vs 0.68; frontier 0.90 vs 0.60); no frontier slowdown predicted; pre-1950 data cannot identify it | **Not established** (failed pre-registered test) | paper_research_labor_history §6b |
| C8 | Countries' productivity humps follow their own research build-ups | Main slope 0.15 (passes a badly designed rule), but 11 of 22 countries peak *before* their build-up; the pre-registered low-frequency robustness check fails (−0.02) | **Not established** | paper_staggered_transitions §3 |
| C9 | Across countries, catch-up and common world periods dominate productivity growth | Gap coefficient +2.2 (graduates panel) and +3.0 (R&D panel), both significant; period effects explain 32% of variance vs 5% for countries | **Established** (replicates Madsen; Griffith–Redding–Van Reenen) | paper_staggered_transitions §4 |
| C10 | Productivity humps bunch in time across countries (US and New World 1940s; Europe and Japan 1950s–60s) | 21 of 22 countries peak in 1942–63 (spread 8 years) | **Established** (descriptive) | paper_staggered_transitions §3 |
| C11 | Fast eras are broad-based; slow eras rest on a few industries | Correlation 0.85 between aggregate growth and the share of industries contributing (8 eras) | **Suggestive** (8 eras; replicates Inklaar–Timmer) | paper_sectoral_averaging §4 |
| C12 | Long-run schooling growth shows up in productivity | Low-frequency slopes −0.25 to +0.41 vs expected 1; datasets disagree on schooling changes (reliability 0.18–0.42) | **Not established** (could be measurement) | paper_education_productivity |
| C13 | World research (excluding China) grew faster than US research after 1982 | Researchers 2.8% vs 2.4%; real R&D 3.4% vs 3.7% | **Not established** | world-research exploration |

## D. What happens next?

| # | Claim | Evidence | Level | Source |
| --- | --- | --- | --- | --- |
| D1 | The best tested long-horizon forecast is "constant average growth plus noise" (Model A) | Lowest 10- and 25-year forecast errors; coverage of 90% bands 92% and 89% (US) | **Established** | paper_growth_shape §6 |
| D2 | Model A's forecast: about 1.6% a year for GDP per capita | US 1.64%, envelope 1.57%, top-5 1.59%. 90% range for the 25-year average: US 0.2–3.1%, top-5 0.8–2.3% | **Established** (as a statistical forecast, not a mechanism) | scripts/run_headline_numbers.py |
| D3 | Recent growth (2007–2022, about 0.9–1.0%) is below Model A's forecast | Inside its range; Project 2 shows such gaps can't yet be told apart from noise | **Established** (descriptive) | scripts/run_headline_numbers.py |
| D4 | Any causal projection (AI, ageing, research slowdown) | No validated causal model (C7, C8) | **Not established** | — |

---

## Pre-registered test E1: break test for A5 (rules written 17 Oct 2026, before running)

**Purpose.** A5 used era cut-offs chosen after looking at the data. This test lets the data choose the break years.

**Data.** Annual growth of GDP per capita of the top-5 frontier average (`data/processed/frontier_levels.csv`, column `top5`), 1871–2022. The single-leader envelope and the US are reported for information only; they do not decide A5.

**Method.** Bai–Perron test for breaks in mean growth (`src/frontier/breaks.py`):
- at most 2 breaks;
- minimum regime length 10% of the sample (15 years), so that a post-2007 regime can be detected;
- p-values from a moving-block bootstrap under the null of no break (blocks of 5 years, 1,999 replications).

**Main statistic.** The sup-F test of 2 breaks against none.

**Robustness checks:** blocks of 10 years; minimum regime length 15% (22 years).

**Result (run 17 Oct 2026): A5 is Not established.**
- **Main test:** p = 0.265. The data-chosen breaks are 1933 and 2007 (0.89% / 2.32% / 0.94%), so the pattern is slow–fast–slow, but not significant.
- **Robustness:** p = 0.271 (10-year blocks) and p = 0.258 (22-year minimum regime).
- **For information:** envelope p = 0.651; US p = 0.435.
- Output: `output/break_test_frontier/results.json`.

**Decision rule for A5 (as written before running):**
- **Established** if all three hold:
  1. p < 0.05 in the main test;
  2. the estimated two-break solution is slow–fast–slow (the middle regime has the highest mean);
  3. p < 0.10 in both robustness checks.
- **Suggestive** if 0.05 ≤ p < 0.10, or if p < 0.05 but the pattern or the robustness checks fail.
- **Not established** if p ≥ 0.10.

---

## Change log

| Date | Item | Change | Reason |
| --- | --- | --- | --- |
| 17 Oct 2026 | B3 | "Offsetting inside TFP" → Not established | Project 1: the test is equivalent to a slope < 1, which measurement error produces |
| 17 Oct 2026 | B5 | "No stabilizing feedback anywhere" → relative OECD stabilizer (Suggestive) | Data bug fixed (MSTI levels mixed with growth rates) |
| 17 Oct 2026 | C13 | "World research grew faster and steadier than US" → Not established | Splitting out China |
| 17 Oct 2026 | C6/C7 | "Transition explains the hump" → in sample only (C6 Suggestive); out of sample fails (C7) | Pre-registered hold-out test |
| 17 Oct 2026 | C8 | Country timing of research → Not established | Pre-registered timing test; its "pass" rule was too weak |
| 17 Oct 2026 | A5/A6 | "Growth is not constant: solid" → hump Suggestive for the top-5 frontier only; not significant for US or single-leader envelope | The claim had never been tested against noise; audit test with HAC standard errors |
| 17 Oct 2026 | D2 | "Future growth about 1–1.5%" → about 1.6% (Model A) | The earlier figure did not come from any model |
| 17 Oct 2026 | A5 | Suggestive → **Not established** | Pre-registered break test E1: p = 0.27 when the data choose the break years |
| 17 Oct 2026 | A7 | "Leader from 1899" → "leader for most years from 1899" | Switzerland led in 1931–34, 1971 and from 2006 |
| 17 Oct 2026 | B-summary | "No stabilizing force exists" → "We found no stabilizing force" | Some tests have low power (e.g. B6); B5 is a between-country exception |
