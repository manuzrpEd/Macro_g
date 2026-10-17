# Macro_g: why is frontier growth so constant?

Research notes and code on the long-run constancy of GDP per capita growth: whether global idea flows, offsetting sources of growth, schooling or research effort sustain it, and whether it is really constant.

## Our answer

*Each claim below is stated in plain English, with the technical reason it holds and the command that reproduces it. The bracketed codes (A1, B4, …) point to [findings_register.md](findings_register.md), which records every claim's evidence, confidence level and change history. Last updated 17 October 2026.*

### The research question

Why does GDP per capita growth seem constant at about 2% in the long run?

### The answer

**Because yearly luck is far larger than any slow shift in the average growth rate, so even real shifts of about 1 point are nearly invisible in 150 years of data. And we found no force that holds growth at 2%.**

**In short:** statistically, 150 years of GDP per capita can't be told apart from a constant growth rate, not even for the leading economies, whose growth looks slow before the 1930s, fast until 2007 and slow since [A1, A5, A6]. A slowdown of more than a point would usually go unnoticed [A4], and the US looks especially steady because it was catching up to Britain before 1900 [A7].

Nothing we tested keeps growth on track:
- capital and hours don't make up for productivity swings [B1, B2];
- research effort doesn't rise when productivity slows [B4];
- industries' booms don't cancel out, and shifting weight between industries doesn't steady the total [B7, B9];
- trade-linked idea flows don't sustain it [B11].

Productivity data do show a mid-century wave [A8]. Our best candidate for driving it, the build-up of America's research workforce, fits the past but fails fair out-of-sample and cross-country tests [C6–C8]. Across countries, growth mostly reflects catching up to the leader and common world-wide waves [C9, C10]. The cause of the wave therefore remains open.

For the future, the best tested forecast is the long-run average, about 1.6% a year, with a wide range (roughly 0.2–3.1% for the next 25 years' average in the US). Recent growth of about 1% is at the low end, and we have no validated model that says why [D1–D4].

**Why it *seems* constant**

| Claim (plain English) | Why it holds (technical) | Reproduce |
| --- | --- | --- |
| **Constant growth is never statistically rejected** [A1] | Box–Cox curvature λ ≈ 0–0.1 (exponential) in US, UK, frontier and per-hour series; likelihood ratio vs exponential ≤ 0.4. Bai–Perron tests (up to 4 breaks, block bootstrap) find no break in frontier growth: p = 0.33 (leader), 0.25 (top-5), 0.28 (US) | `python scripts/run_growth_shape.py` → `output/growth_shape/results.json` (`series.*.full_sample`); `python scripts/run_all.py` → `output/results.json` (`breaks`) |
| **Even the most hump-like series is not stronger than noise.** The top-5 leading economies grew about 0.9% → 2.3% → 0.9% (breaks in 1933 and 2007), but noise alone can produce that [A5] | Pre-registered Bai–Perron test letting the data choose the break years (≤ 2 breaks, 15-year minimum regime, block bootstrap): p = 0.27, and 0.26–0.27 in both robustness checks. With cut-offs picked by eye, HAC t ≈ 2–2.8; the difference is the cost of choosing dates after seeing the data | `python scripts/run_break_test_frontier.py` → `output/break_test_frontier/results.json`; `python scripts/run_headline_numbers.py` → `output/headline/results.json` (`era_growth_hac`) |
| **For the US alone, the eras don't differ beyond noise** [A6] | 1871–1929 / 1930–2007 / 2008–22: 1.55% / 1.86% / 0.93%; HAC t = 0.4 (rise) and −1.2 (fall); break test p = 0.44 | same two scripts (`info_us`, `era_growth_hac.us`) |
| **Slow shifts are nearly invisible.** A fall in trend growth from 2.5% to 1% over 150 years is detected only about a third of the time [A4] | Monte Carlo with the US noise level (200 simulated histories): a slope test detects the decline in 35%; model selection mistakes it for additive growth in 31%. A 2.0% → 1.5% fall is detected in 10% | `python scripts/run_growth_shape_power2.py` → `output/growth_shape/power_calibrated.json` |
| **The US looks steadier than the frontier because it was catching up before 1900** [A7] | US GDP per capita was 82% of the leader's in 1870 and the highest for most years from 1899 (Switzerland led in 1931–34, 1971 and from 2006). In 1870–99 the US grew 1.74% a year against 1.07–1.11% for the frontier | `python scripts/run_headline_numbers.py` → `output/headline/results.json` (`us_catch_up`) |
| **A mid-century wave does show up in *productivity* data** [A8], though not beyond noise in GDP per capita [A5] | Bergeaud–Cette–Lecat (2016): the big productivity wave hit the US first, others after WWII. In 1919–29, 95% of US industries contributed positively to productivity growth | `python scripts/run_sectoral.py` → `output/sectoral/results.json` (`H2_concentration_vs_aggregate`) |

**Why we found no force holding it at 2%**

| Claim (plain English) | Why it holds (technical) | Reproduce |
| --- | --- | --- |
| **Capital and hours don't offset productivity; hours even amplify swings** [B1, B2] | Low-frequency variance ratio of the per-person growth components, against an independence null: leaders 0.89 (p = 0.24), US 1.10. Without hours swings, long-run US growth would be 45% smoother (also with Ramey–Francis hours) | `python scripts/run_balancing.py` → `output/balancing/results.json` (`per_person`, `counterfactual_frozen`) |
| **Research doesn't lean against slowdowns** [B4] | Long-run (Müller–Watson) regressions of US research growth on past TFP growth, by funder, 1930–2022: every response is positive (strongest +2.8 at a 15-year lag, p = 0.008) | `python scripts/run_research_effort.py` → `output/research_effort/results.json` (`C_feedback_us`) |
| **Industries don't offset each other; averaging only removes random noise** [B7, B8] | Variance ratio of 61 industries' contributions R ≥ 1 in every sample (1.2–3.3; independence ≈ 0.9). Aggregate long-run swings 0.39 pp vs 1.90 pp if all industries moved together | `python scripts/run_sectoral.py` → `output/sectoral/results.json` (`H1_lowfreq`, `H1_eras`) |
| **Baumol reweighting doesn't stabilize** [B9] | Before 1941, fast-growing industries *gained* share (correlation +0.28, p = 0.002); after 1948 no response (−0.08). Freezing industry weights changes swings by at most 9% | `python scripts/run_sectoral.py` → `output/sectoral/results.json` (`H3_*`) |
| **World idea flows weighted by trade integration don't sustain it** [B11] | In the semi-endogenous model, integration weighting fits worse (best weight κ = 0); integration follows growth by about ten years (reverse causality) | `python scripts/run_all.py`; `python scripts/run_identification.py` → `output/results*.json` |
| **Policy doesn't set the long-run rate** [B10] | Jones (1995): trend growth stayed flat while taxes, government size and investment policy changed massively | literature only; not tested by us |

*One exception, not relevant to the frontier as a whole:* across OECD countries, a country that grew faster than the others later expands research more slowly than the others (−0.78, p = 0.016). This vanishes for the OECD as a whole [B5].

### Link to the global picture

| Part of the question | Status | Reproduce |
| --- | --- | --- |
| Is growth really constant? | **Can't be rejected** [A1]. Not even the leading economies' slow–fast–slow pattern beats noise [A5]; nor does the US [A6] | `run_growth_shape.py`, `run_break_test_frontier.py` |
| Why does it *seem* constant? | **Answered:** large yearly noise hides shifts of about 1 point [A4], and the US caught up before 1900 [A7] | `run_growth_shape_power2.py`, `run_headline_numbers.py` |
| Is there a force keeping it at 2%? | **Answered: we found none.** Every candidate we tested failed [B1–B9, B11] | `run_balancing.py`, `run_research_effort.py`, `run_sectoral.py`, `run_all.py` |
| What drove the mid-century productivity wave? | **Not answered.** The build-up of US research workers fits it in sample [C6] but fails an out-of-sample test [C7] and a cross-country timing test [C8]. Across countries, catch-up to the leader and common world waves dominate [C9, C10] | `run_research_labor_history.py` (needs your own IPUMS extracts), `run_staggered_transitions.py` |
| What happens next? | **Statistical forecast only:** "constant average growth plus noise" is the best long-horizon forecaster we tested [D1]. It gives about 1.6% a year; the 90% range for the next 25 years' average is about 0.2–3.1% (US) or 0.8–2.3% (top-5 leaders) [D2]. Recent growth (about 0.9–1.0%, 2007–22) is below it but inside the range [D3]. No validated causal model [D4] | `run_growth_shape.py` (`long_horizon`), `run_headline_numbers.py` (`model_A_forecast`) |

**Caveat.** The "why it seems constant" part rests on robust facts and simulations. Whether the mid-century productivity wave is real for GDP per capita, and what drove it, can't be settled with public data before about 1960, because research counts by country don't exist outside the US.

## Documents

**Start here:** [findings_register.md](findings_register.md) lists every finding with its evidence, confidence level and change log. Summaries and papers must not claim more than the register.

| File | What it is |
| --- | --- |
| [literature_review_constant_growth.md](literature_review_constant_growth.md) | Literature review: the stylized fact, the models, post-2022 work, open questions |
| [research_proposal_global_idea_flows.md](research_proposal_global_idea_flows.md) | Research proposal: does deglobalization slow the world's frontier? |
| [paper_deglobalization_frontier.md](paper_deglobalization_frontier.md) | Results: the proposal carried out, written as a short paper |
| [research_proposal_leader_engine.md](research_proposal_leader_engine.md) | Second proposal: why does the leader's engine run at a steady pace? (updated after the first attempt) |
| [paper_balancing_leader.md](paper_balancing_leader.md) | Results of the second proposal, written as a short paper |
| [litreview_growth_shape.md](litreview_growth_shape.md) → [paper_growth_shape.md](paper_growth_shape.md) | Project 2: is the 2% constant, additive, or slowly declining? (ex-ante review → results) |
| [litreview_education.md](litreview_education.md) → [paper_education_productivity.md](paper_education_productivity.md) | Project 1: why doesn't schooling show up in long-run productivity? Pritchett vs Madsen (ex-ante review → results) |
| [litreview_research_effort.md](litreview_research_effort.md) → [paper_research_effort.md](paper_research_effort.md) | Project 3: does research effort grow steadily, and is that why growth is steady? (ex-ante review → results) |
| [litreview_sectoral_averaging.md](litreview_sectoral_averaging.md) → [paper_sectoral_averaging.md](paper_sectoral_averaging.md) | Project 4: is steady growth an average of unsteady industries? US industries 1899–2024 (ex-ante review → results) |
| [litreview_research_labor_history.md](litreview_research_labor_history.md) → [paper_research_labor_history.md](paper_research_labor_history.md) | Project 5: US research labour from census microdata (IPUMS), 1850–2024, and the slow–fast–slow frontier (ex-ante review → results) |
| [litreview_staggered_transitions.md](litreview_staggered_transitions.md) → [paper_staggered_transitions.md](paper_staggered_transitions.md) | Project 6: do countries' productivity humps follow their own research build-ups? 23 economies (ex-ante review → results) |

## Reproducing the results

Requires Python 3.10+.

```bash
pip install -r requirements.txt
python tests/test_methods.py      # checks each method on simulated data (~15 s)
python scripts/run_all.py         # downloads data if missing, runs the main results (~1 min)
python scripts/run_all.py --quick # fewer bootstrap and Monte Carlo replications
python scripts/run_identification.py  # endogeneity checks, paper Section 9 (~15 s)
python scripts/run_balancing.py       # second paper: the balancing leader (~1 min)
python scripts/run_growth_shape.py    # Project 2: model comparison, prequential scores, power study (several minutes)
python scripts/run_growth_shape_power2.py  # Project 2: calibrated power for realistic declines
python scripts/run_education.py       # Project 1: schooling vs productivity across datasets
python scripts/run_research_effort.py # Project 3: research effort hypotheses A–D
python scripts/run_world_research.py  # exploration: is world research (not US research) the engine? (output/world_research/)
python scripts/run_sectoral.py        # Project 4: industry averaging and Baumol reweighting (data/raw/sectoral/, output/sectoral/)
python scripts/run_research_labor_history.py  # Project 5: needs your own IPUMS extracts in data/raw/ipums/ (not redistributable; git-ignored)
python scripts/run_staggered_transitions.py   # Project 6: cross-country timing test (output/staggered_transitions/)
python scripts/run_break_test_frontier.py    # pre-registered break test E1 for the answer above (output/break_test_frontier/)
python scripts/run_headline_numbers.py       # era growth, US catch-up, Model A forecast quoted above (output/headline/)
```

Projects 1–3 use extra files in `data/raw/education/` and `data/raw/research_effort/` (Madsen 2014 replication data, Barro–Lee, Cohen–Soto, de la Fuente–Doménech, BEA NIPA R&D, OECD MSTI extract), each listed in that folder's `SOURCES.csv`; Project 3 also reads the Bloom et al. (2020) replication files in `data/raw/balancing/bjvw2020/`. Outputs go to `output/growth_shape/`, `output/education/` and `output/research_effort/` (`results.json` plus `figures/`).

`run_balancing.py` uses extra files in `data/raw/balancing/`, listed with their URLs in `data/raw/balancing/SOURCES.csv`:
- Lee–Lee human capital;
- Ramey–Francis hours;
- Bakker–Crafts–Woltjer growth accounts;
- NSF and BEA R&D;
- Penn World Table 11 (`data/raw/pwt110.dta`).

`run_identification.py` needs the extra raw files listed under "Data sources" (TRADHIST, Jacks–Meissner–Novy, Correlates of War, OWID electricity). Unlike the main sources, these are not downloaded automatically.

Outputs:
- `output/results.json` and `output/results_identification.json`: every number quoted in the paper
- `output/figures/`: the figures
- `output/tables/`: episode growth, country decompositions, model profiles
- `data/processed/`: frontier envelopes, research pool, growth series

## Code layout

| Module | Role |
| --- | --- |
| `src/frontier/config.py` | Country samples, episodes, war years, data URLs |
| `src/frontier/data.py` | Download and tidy Maddison, JST, Bergeaud–Cette–Lecat, WIPO and World Bank data |
| `src/frontier/envelope.py` | Frontier envelopes (max, top-k) and episode growth |
| `src/frontier/integration.py` | Integration weights and the effective world research pool |
| `src/frontier/breaks.py` | Bai–Perron multiple structural breaks with block-bootstrap p-values |
| `src/frontier/lowfreq.py` | Müller–Watson low-frequency (cosine) projections and regressions |
| `src/frontier/model.py` | Semi-endogenous growth model with an integration-weighted pool, estimated by minimum distance |
| `src/frontier/tradecosts.py` | Inverse-gravity trade costs, country tariffs, Suez sea distances, Feyrer-style geography instrument |
| `src/frontier/identification.py` | Low-frequency IV, panel IV with fixed effects and clustered errors, lead–lag, window neutralization |
| `src/frontier/plots.py` | Figure style |
| `scripts/run_all.py` | The main pipeline |
| `scripts/run_identification.py` | The endogeneity checks (steps 1–5) |
| `src/frontier/balancing.py` | Low-frequency variance ratios, surrogate-data nulls, cross-source correction for division bias |
| `scripts/run_balancing.py` | The balancing-leader analysis (outputs in `output/balancing/`) |
| `src/frontier/growthshape.py` | Growth-path models (exponential, declining, drifting, additive, power/Box–Cox, breaks, volatility trends), prequential scores, simulation |
| `scripts/run_growth_shape.py`, `scripts/run_growth_shape_power2.py` | Project 2 |
| `scripts/run_education.py` | Project 1 |
| `scripts/run_research_effort.py` | Project 3 |
| `scripts/run_world_research.py` | Exploration: world vs US research pools, 1870–2022 |
| `scripts/run_sectoral.py` | Project 4: industry averaging, relay of leaders, Baumol reweighting |
| `scripts/run_research_labor_history.py` | Project 5: census research labour, β by era, dynamic semi-endogenous fit |
| `tests/test_methods.py` | Checks that each method recovers known answers on simulated data |

## Data sources

Raw files go in `data/raw/`, which is not tracked: WIPO's terms do not allow redistributing its historical data. `scripts/run_all.py` downloads everything automatically.

| Dataset | Source |
| --- | --- |
| Maddison Project Database 2023 | <https://dataverse.nl/dataset.xhtml?persistentId=doi:10.34894/INZBF2> |
| Jordà–Schularick–Taylor Macrohistory Database R6 | <https://www.macrohistory.net/database/> |
| Bergeaud–Cette–Lecat Long-Term Productivity Database v2.7 | <https://www.longtermproductivity.com/> |
| WIPO historical patent statistics, 1883–1979 | <https://www.wipo.int/en/web/ip-statistics> |
| World Bank WDI: patents, trade/GDP | <https://data.worldbank.org/> |
| CEPII TRADHIST v4: bilateral trade, GDP, sea distances (`data/raw/tradhist/`) | <http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=32> |
| Jacks–Meissner–Novy trade costs and tariffs (`data/raw/jmn_tradecosts/`) | Archived copy of David Jacks' data page (web.archive.org, sfu.ca/~djacks/data/publications/) |
| Correlates of War NMC v7: military spending (`data/raw/cow_nmc/`) | <https://correlatesofwar.org/wp-content/uploads/NMCv7.zip> |
| CERDI sea distances; CEPII GeoDist (`data/raw/seadistance/`, `data/raw/cepii_geodist/`) | Zenodo record 240493; <https://www.cepii.fr/DATA_DOWNLOAD/geodist/dist_cepii.dta> |
| CHAT technology adoption; OWID electricity (`data/raw/chat.csv`, `data/raw/owid_electricity_generation.csv`) | <https://www.nber.org/research/data/cross-country-historical-adoption-technology>; <https://ourworldindata.org/grapher/electricity-generation> |
