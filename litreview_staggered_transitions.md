# Do Productivity Humps Follow Research Build-Ups Across Countries? Ex-Ante Literature Review and Design

Written 17 October 2026, **before** the analysis · @Manuel Antonio Sanchez Garcia · companion results paper: [paper_staggered_transitions.md](paper_staggered_transitions.md)

*Disclosure:* before writing this, we ran two data-validity checks on the research series only. No productivity data were analysed.
- **Madsen's pre-1950 R&D intensity** is one common back-cast path. Its 1870–1913 log change is 0.703 in 19 of 21 countries, so it is unusable for timing before about 1963.
- **Lee–Lee graduate growth** is country-specific: the median cross-country correlation of 5-year growth over 1875–1950 is 0.07.

## The question

In the US, frontier productivity grew slowly, then fast, then slowly. That hump coincides with the US research build-up. A transition model fits the shape in sample but failed a pre-registered out-of-sample test (Project 5, T8). **A different test of the same idea:** countries built up their research capacity at different times. If research build-ups drive productivity humps, each country's hump should come *after its own* build-up. If not, the humps should follow something else:
- **a common global wave:** the same timing everywhere;
- **catch-up:** timing set by how far behind the leader a country was.

## What the literature says

All citations were verified by the literature search on 17 October 2026, except those marked otherwise.

### 1. Horse races between research-based growth models (well covered)
- **Semi-endogenous (Jones 1995, 2002):** productivity growth ∝ *growth* of research input.
- **Second-generation Schumpeterian (Aghion–Howitt 1998; Peretto 1998; Young 1998):** productivity growth ∝ research *intensity* (research per product line or per worker).
- **Tests, with split verdicts:**
  - **For Schumpeterian:**
    - Ha and Howitt (2007, *JMCB* 39(4)): US cointegration;
    - Madsen (2008, *JEG* 13(1)): 21 OECD countries, long-run patents and R&D;
    - Ang and Madsen (2011, *REStat* 93(4)): Asian miracle economies 1953–2006;
    - Laincz and Peretto (2006);
    - Zachariadis (2003).
  - **For semi-endogenous:**
    - Herzer (2022, *Review of Economics* 73(1)): critique of Madsen's tests plus a 19-country panel;
    - Kruse-Andersen (2023, *OBES* 85(5));
    - Bottazzi and Peri (2007, *EJ* 117).
- **Data caveats.**
  - Ang and Madsen impute Korea's R&D before 1967 and Taiwan's and Singapore's before 1970.
  - Madsen's 1870+ R&D series are back-cast before 1953.
  - Solarin, Gil-Alana and López (2022) find research intensity non-stationary, which undercuts the Schumpeterian tests.

### 2. Catch-up and diffusion
- **Coe and Helpman (1995); Coe, Helpman and Hoffmaister (2009):** foreign R&D raises domestic productivity.
- **Griffith, Redding and Van Reenen (2004):** R&D both innovates and builds absorptive capacity.
- **Madsen (2007, 2014); Madsen, Islam and Ang (2010):** imitation dominates outside the frontier.
- **Comin and Hobijn (2010):** technologies are adopted about 45 years after invention.
- **Jones (2022) warns** that the semi-endogenous model applies to the *world* frontier. For individual countries, own research and catch-up move together.

### 3. Common waves vs staggered waves
- **Gordon (2016):** one big wave of great inventions (US).
- **Bergeaud, Cette and Lecat (2016, *RIW* 62(3)):** the big productivity wave hit the **US first (interwar) and the others after WWII**. So humps are staggered, but nobody has linked the staggering to research inputs.
- **Awaworyi Churchill, Inekwe and Ivanovski (2020):** convergence clubs in R&D intensity before WWII, which is indirect evidence of staggered research build-ups (data provenance unverified).

### 4. East Asia
- **Kim and Lau (1994); Young (1995); Hsieh (2002):** Asian growth was mostly accumulation, and productivity timing is fragile to measurement.

## Gap

**No paper dates each country's research build-up and productivity hump and tests whether they line up across countries.** All existing tests are pooled regressions or cointegration. This timing test is our contribution.

**Honest flag:** the panel regressions we also run (T2, T3) replicate the Madsen / Herzer type of test and are secondary.

## Pre-registered design (fixed before running)

**Data.**
- **Productivity:** Bergeaud–Cette–Lecat TFP, 23 economies, 1891–2019. 2020–22 is excluded for dating because of COVID.
- **Research measure R1 (long run, 1870–2010):** population with completed tertiary education (Lee–Lee), 5-yearly, log-linearly interpolated to annual.
  - **Semi-endogenous input:** the growth of R1.
  - **Schumpeterian intensity:** R1 ÷ working-age population.
  - **Weak proxy:** it correlates only 0.34 with US engineers and chemists by decade, and 0.23 with researcher growth across countries.
- **Research measure R2 (1963–2009):** Madsen R&D intensity × population (R&D effort) and R&D intensity itself. The earlier, back-cast years are not used.
- **Catch-up:** gap to the frontier = ln(highest GDP per capita among the 23 ÷ own), Maddison. A robustness check uses Madsen's TFP distance to frontier.

**Dating.**
- **Productivity hump:** the year of maximum 21-year centred moving average of TFP growth, searched over 1901–2009.
- **Research build-up peak:** the year of maximum 21-year centred moving average of R1 growth, searched over 1880–2000.
- **Robustness:**
  - 31-year windows;
  - a low-frequency trend (periods of 25 years or more) instead of moving averages;
  - rich economies only (excluding Chile, Mexico, Greece, Portugal, Spain).

| Test | Statistic | Semi-endogenous transition predicts | Common wave (Gordon) predicts | Catch-up predicts | Schumpeterian predicts |
| --- | --- | --- | --- | --- | --- |
| **T1. Timing (main)** | Cross-country regression of the productivity-hump year on the research-peak year and the 1890 gap | slope on research peak **> 0**; productivity hump 0–40 years *after* research peak | slope ≈ 0; humps bunched in time | slope on gap > 0 (poorer → later) | humps late in the sample, where intensity is highest |
| T1b | Spread (SD) of hump years across countries | — | small | — | — |
| **T2. Panel, 10-year blocks 1890–2010** (secondary; Madsen/Herzer type) | TFP growth on lagged R1 growth (semi-endogenous), log intensity (Schumpeterian), log gap (catch-up), with country and period effects; also the share of variance explained by period effects alone | lagged growth > 0 | period effects explain most | gap > 0 | intensity > 0 |
| **T3. Panel, 5-year blocks 1965–2009, R&D (R2)** (secondary) | as T2 with R&D effort growth and R&D intensity | R&D effort growth > 0 | — | gap > 0 | R&D intensity > 0 |

**Success criterion for the transition story, fixed now.** In T1 (main specification):
- the slope on the research-peak year is **positive with one-sided p < 0.10**;
- the median lag (productivity hump minus research peak) is **between 0 and 40 years**.

A positive but insignificant slope counts as a partial pass. A slope of zero or below counts as a fail.

**Caveats fixed in advance.**
1. **Graduates are a weak proxy for researchers,** which biases the timing test toward zero.
2. **About 23 countries,** so the timing regression has very low power.
3. **Wars distort productivity** in 1914–19 and 1939–49; the 21-year averages smooth but do not remove this.
4. **Own research and catch-up move together** (Jones 2022). The gap control helps but does not solve identification.
5. **BCL productivity before 1950 is reconstructed** for many countries.

## References

- Aghion, P., and Howitt, P. (1998). *Endogenous Growth Theory*. MIT Press.
- Ang, J. B., and Madsen, J. B. (2011). Can second-generation endogenous growth models explain the productivity trends and knowledge production in the Asian miracle economies? *REStat* 93(4): 1360–1373.
- Awaworyi Churchill, S., Inekwe, J., and Ivanovski, K. (2020). Convergence of R&D intensity in OECD countries: evidence since 1870. *Empirical Economics* 59(1): 295–306.
- Bergeaud, A., Cette, G., and Lecat, R. (2016). Productivity trends in advanced countries between 1890 and 2012. *Review of Income and Wealth* 62(3): 420–444.
- Bottazzi, L., and Peri, G. (2007). The international dynamics of R&D and innovation in the long run and in the short run. *Economic Journal* 117(518): 486–511.
- Coe, D. T., and Helpman, E. (1995). International R&D spillovers. *EER* 39(5): 859–887.
- Coe, D. T., Helpman, E., and Hoffmaister, A. W. (2009). International R&D spillovers and institutions. *EER* 53(7): 723–741.
- Comin, D., and Hobijn, B. (2010). An exploration of technology diffusion. *AER* 100(5): 2031–2059.
- Gordon, R. J. (2016). *The Rise and Fall of American Growth*. Princeton University Press.
- Griffith, R., Redding, S., and Van Reenen, J. (2004). Mapping the two faces of R&D. *REStat* 86(4): 883–895.
- Ha, J., and Howitt, P. (2007). Accounting for trends in productivity and R&D: a Schumpeterian critique of semi-endogenous growth theory. *JMCB* 39(4): 733–774.
- Herzer, D. (2022). Semi-endogenous versus Schumpeterian growth models: a critical review of the literature and new evidence. *Review of Economics* 73(1): 1–55.
- Hsieh, C.-T. (2002). What explains the industrial revolution in East Asia? *AER* 92(3): 502–526.
- Jones, C. I. (1995). R&D-based models of economic growth. *JPE* 103(4): 759–784.
- Jones, C. I. (2002). Sources of U.S. economic growth in a world of ideas. *AER* 92(1): 220–239.
- Jones, C. I. (2022). The past and future of economic growth: a semi-endogenous perspective. *Annual Review of Economics* 14: 125–152.
- Kim, J.-I., and Lau, L. J. (1994). The sources of economic growth of the East Asian newly industrialized countries. *JJIE* 8(3): 235–271.
- Kruse-Andersen, P. K. (2023). Testing R&D-based endogenous growth models. *OBES* 85(5): 1083–1110.
- Laincz, C., and Peretto, P. (2006). Scale effects in endogenous growth theory: an error of aggregation not specification. *JEG* 11(3): 263–288.
- Lee, J.-W., and Lee, H. (2016). Human capital in the long run. *JDE* 122: 147–169.
- Madsen, J. B. (2007). Technology spillover through trade and TFP convergence: 135 years of evidence for the OECD countries. *JIE* 72(2): 464–480.
- Madsen, J. B. (2008). Semi-endogenous versus Schumpeterian growth models: testing the knowledge production function using international data. *JEG* 13(1): 1–26.
- Madsen, J. B. (2014). Human capital and the world technology frontier. *REStat* 96(4): 676–692.
- Madsen, J. B., and Ang, J. B. (2016). Finance-led growth in the OECD since the nineteenth century. *REStat* (replication data, Harvard Dataverse doi:10.7910/DVN/27665).
- Madsen, J. B., Islam, M. R., and Ang, J. B. (2010). Catching up to the technology frontier: the dichotomy between innovation and imitation. *CJE* 43(4): 1389–1411.
- Peretto, P. (1998). Technological change and population growth. *JEG* 3(4): 283–311. *(Citation details not re-verified.)*
- Solarin, S. A., Gil-Alana, L. A., and López, C. (2022). Persistence analysis of research intensity in OECD countries since 1870. *Australian Economic Papers* 61(4): 738–750.
- Young, A. (1995). The tyranny of numbers. *QJE* 110(3): 641–680.
- Young, A. (1998). Growth without scale effects. *JPE* 106(1): 41–63. *(Citation details not re-verified.)*
- Zachariadis, M. (2003). R&D, innovation, and technological progress: a test of the Schumpeterian framework without scale effects. *CJE* 36(3): 566–586.
