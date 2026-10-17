# Why Does Research Effort Grow at a Steady Pace? Ex-Ante Literature Review and Design

Written 17 October 2026, **before** running the analysis · @Manuel Antonio Sanchez Garcia · companion results paper: [paper_research_effort.md](paper_research_effort.md)

## The question

In Jones's semi-endogenous model, frontier growth of GDP per capita is roughly

$$
g_y \approx \frac{g_S}{\beta\,(1-\alpha)}
$$

with research-effort growth g_S ≈ 4% a year in the US (1930–2022), diminishing returns β ≈ 3, and a capital multiplier of 1/(1−α) ≈ 1.5. That gives about 2%. Paper 2 confirmed that US productivity follows research effort with a 5–10 year lag. The constancy question therefore becomes: **why does research effort itself grow so steadily?**

Effective research effort (Bloom et al. 2020) can be written as S = research spending ÷ nominal GDP per person = (R&D/GDP) × population. So its growth splits exactly:

$$
g_S = \underbrace{g_{R\&D/GDP}}_{\text{research intensity}} + \underbrace{n}_{\text{population growth}}
$$

## Hypotheses and what the literature says

### A. Coincidence of transitions
- **Jones (2002, 2022a).** About 80% of US growth over 1950–93 was transitional: rising research intensity and education. Steady growth "hides" falling population growth offset by rising intensity, and this cannot last.
- **Jones (2022b), "Empty Planet".** With a falling population, growth in ideas eventually stops.
- **Status: documented as a fact, never tested as coincidence vs. mechanism.**

### B. Balancing: research intensity responds to population or researcher supply
- **Theory.** Strulik, Prettner and Prskawetz (2013): falling fertility is offset by rising education per person, so knowledge growth persists.
- **Researcher supply in the short run is inelastic.** Goolsbee (1998): federal R&D raises scientists' wages, and 30–50% "goes to wages". Romer (2000) makes the same point.
- **Over the medium run it is elastic.** Freeman (1976) and Ryoo and Rosen (2004): engineering supply follows lagged salaries in cobweb cycles.
- **Selection.** Ekerdt and Wu (2024): as the research share rose, average researcher ability fell.
- **Market size and demography.**
  - Acemoglu and Linn (2004): market size drives drug innovation.
  - Aksoy et al. (2019): aging lowers R&D.
  - Karahan, Pugsley and Şahin (2024); Peters and Walsh (2021); Hopenhayn, Neira and Singhania (2022): slower population growth means less entry and dynamism.
- **Status: mostly open.** No paper estimates whether frontier research intensity responds to population or cohort growth.

### C. Negative feedback from past productivity growth to research
- **Business-cycle evidence says R&D is procyclical,** which destabilizes:
  - Barlevy (2007);
  - Ouyang (2011);
  - Fabrizio and Tsolmon (2014);
  - Comin and Gertler (2006);
  - Anzoategui et al. (2019).
  
  The exception is Aghion, Askenazy, Berman, Cette and Eymard (2012): firms without credit constraints are countercyclical.
- **Public R&D surges were driven by crises, not by productivity:**
  - WWII and the OSRD (Gross and Sampat 2023);
  - Sputnik and NASA (Kantor and Whalley 2025);
  - the post-Sputnik PhD boom and bust (Stephan 2015; Kaiser 2006).
- **Public R&D raises TFP with long lags.** Fieldhouse and Mertens (2023, 2025): nondefense R&D appropriation shocks raise TFP with lags of 8–15 years, while defense R&D does not.
- **Griliches (1980).** The 1970s R&D slowdown explains little of the TFP slowdown.
- **Status: open at low frequency.** No paper tests whether research effort responds to *past* productivity slowdowns over decades.

### D. Stable diminishing returns (β)
- **The case for constancy.** Bloom et al. (2020): research productivity falls about 5% a year across very different fields (β ≈ 3), and Moore's law shows a strikingly steady decline. Kortum (1997): Pareto-distributed idea quality gives a constant β.
- **Challenges:**
  - Fort et al. (2026): patents per unit of R&D are rising; it is *growth* that is getting harder to find.
  - Ekerdt and Wu (2024): part of the decline is transitional.
  - Philippon (2022); Jones, López-Salido and Philippon (2026): growth may be additive.
- **Status: contested.** No formal test of β's stability over 1930–2022.

## Pre-registered design (fixed before running)

**Data (no IPUMS yet).**
- **BEA NIPA R&D, 1929–2025:** total, private, federal defense, federal nondefense, and state and local; current dollars and quantity indexes.
- **OECD MSTI, 1981–2025:** researchers, real R&D spending (GERD) and its funders.
- **Long-run US data:** Lee–Lee tertiary attainment; Maddison population; Bergeaud–Cette–Lecat TFP.

| Hypothesis | Test | Supports the hypothesis if… |
| --- | --- | --- |
| A vs B | Long-run variance ratio of research-effort growth vs. population growth + intensity growth (US 1930–2022), against an independence null; within-country correlation in the OECD panel | B: the ratio is below the null (they offset). A: the ratio is about the null |
| B | Long-run regression of intensity growth on growth of the tertiary-educated population and on population growth | B: intensity responds to researcher supply or demography |
| C | Long-run regressions of research growth on TFP growth 0, 5, 10 and 15 years earlier, by funder (total, private, defense, nondefense); OECD panel of 5-year research growth on lagged 5-year TFP growth, with country and period effects; the implied loop gain (forward × backward) | C: negative response to past TFP growth (a stabilizing loop). Procyclical (destabilizing): positive |
| D | Rolling 30-year β (lagged research growth ÷ TFP growth); research productivity growth by decade | D: β flat and research productivity falling at a steady rate |

**Caveats fixed in advance.**
- **Few long cycles.** About 93 years give 3–4 independent long cycles, so all results will be suggestive.
- **Mechanical links.** Research intensity has GDP in its denominator, so faster growth mechanically lowers it. We therefore also use real R&D per person.
- **Pre-1953 data.** BEA's pre-1953 R&D is a backcast.

## References (verified by the literature agent on 17 October 2026)

- Acemoglu, D., and Linn, J. (2004). Market size in innovation: theory and evidence from the pharmaceutical industry. *QJE* 119(3): 1049–1090.
- Aghion, P., Askenazy, P., Berman, N., Cette, G., and Eymard, L. (2012). Credit constraints and the cyclicality of R&D investment: evidence from France. *JEEA* 10(5): 1001–1024.
- Aksoy, Y., Basso, H. S., Smith, R. P., and Grasl, T. (2019). Demographic structure and macroeconomic trends. *AEJ: Macro* 11(1): 193–222.
- Anzoategui, D., Comin, D., Gertler, M., and Martinez, J. (2019). Endogenous technology adoption and R&D as sources of business cycle persistence. *AEJ: Macro* 11(3): 67–110.
- Barlevy, G. (2007). On the cyclicality of research and development. *AER* 97(4): 1131–1164.
- Bloom, N., Jones, C. I., Van Reenen, J., and Webb, M. (2020). Are ideas getting harder to find? *AER* 110(4): 1104–1144.
- Comin, D., and Gertler, M. (2006). Medium-term business cycles. *AER* 96(3): 523–551.
- Ekerdt, L. K. F., and Wu, K.-J. (2024). Self-selection and the diminishing returns of research. Working paper.
- Fabrizio, K. R., and Tsolmon, U. (2014). An empirical examination of the procyclicality of R&D investment and innovation. *REStat* 96(4): 662–675.
- Fieldhouse, A. J., and Mertens, K. (2023). The returns to government R&D: evidence from U.S. appropriations shocks. Dallas Fed WP 2305; updated as "The social returns to public R&D," NBER WP 33780 (2025).
- Fort, T. C., Goldschlag, N., Liang, J., Schott, P. K., and Zolas, N. (2026). Growth is getting harder to find, not ideas. NBER WP 35182.
- Freeman, R. B. (1976). A cobweb model of the supply and starting salary of new engineers. *ILR Review* 29(2): 236–248.
- Goolsbee, A. (1998). Does government R&D policy mainly benefit scientists and engineers? *AER P&P* 88(2): 298–302.
- Griliches, Z. (1980). R&D and the productivity slowdown. NBER WP 434.
- Gross, D. P., and Sampat, B. N. (2023). America, jump-started: World War II R&D and the takeoff of the U.S. innovation system. *AER* 113(12): 3323–3356.
- Hopenhayn, H., Neira, J., and Singhania, R. (2022). From population growth to firm demographics. *Econometrica* 90(4): 1879–1914.
- Jones, C. I. (1995). R&D-based models of economic growth. *JPE* 103(4): 759–784.
- Jones, C. I. (2002). Sources of U.S. economic growth in a world of ideas. *AER* 92(1): 220–239.
- Jones, C. I. (2022a). The past and future of economic growth: a semi-endogenous perspective. *Annual Review of Economics* 14: 125–152.
- Jones, C. I. (2022b). The end of economic growth? Unintended consequences of a declining population. *AER* 112(11): 3489–3527.
- Kantor, S., and Whalley, A. (2025). Moonshot: public R&D and growth. *AER* 115(9): 2891–2925.
- Karahan, F., Pugsley, B., and Şahin, A. (2024). Demographic origins of the start-up deficit. *AER* 114(7): 1986–2023.
- Kortum, S. (1997). Research, patenting, and technological change. *Econometrica* 65(6): 1389–1419.
- Ouyang, M. (2011). On the cyclicality of R&D. *REStat* 93(2): 542–553.
- Peters, M., and Walsh, C. (2021). Population growth and firm dynamics. NBER WP 29424.
- Romer, P. M. (2000). Should the government subsidize supply or demand in the market for scientists and engineers? *Innovation Policy and the Economy* 1: 221–252.
- Ryoo, J., and Rosen, S. (2004). The engineering labor market. *JPE* 112(S1): S110–S140.
- Stephan, P. (2015). The endless frontier: reaping what Bush sowed? In *The Changing Frontier* (NBER).
- Strulik, H., Prettner, K., and Prskawetz, A. (2013). The past and future of knowledge-based growth. *Journal of Economic Growth* 18(4): 411–437.
