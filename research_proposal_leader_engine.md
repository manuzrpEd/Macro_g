# Why Does the Leader's Growth Engine Run at a Steady Pace?

**Literature review and research proposal**

Draft of 17 October 2026 · @Manuel Antonio Sanchez Garcia

## 0. Where we stand

Our first paper ([paper_deglobalization_frontier.md](paper_deglobalization_frontier.md)) asked whether global idea flows keep frontier growth steady. They do not appear to: when the world closed in 1914–1949, productivity at the leading economies sped up, and the one link pointing the other way ran from growth to integration. That moves the puzzle from the world to the leader: **why does the leading economy's own engine run at such a steady pace?**

**What the first paper did and did not show about Jones's semi-endogenous model:**

| Claim | Status |
| --- | --- |
| Frontier growth depends on research effort, with diminishing returns to ideas (the core of Jones 1995) | **Not tested** and not falsified |
| The relevant research pool is the *world's*, and access to it depends on integration (our extension) | **Rejected**: integration weighting fits worse than an unweighted world pool or the leader's own pool |
| Unweighted world pool vs. leader-only pool | **Not distinguished**: both explain about 16–26% of long-run swings |
| Frontier productivity tracks research effort over time | **Under strain**: the 1930s–40s productivity surge came with modest research effort (pilot in Section 4) |

So we falsified our own *auxiliary* hypothesis, not Jones's model. A real case against Jones needs a direct test of his mechanism at the leader. That is one of the gaps below (P4).

## 0b. Update after the first attempt (17 October 2026)

The first attempt ran steps 1–4 of the plan (code: `scripts/run_balancing.py`; numbers: `output/balancing/results.json`). **It changed the question.**

**1. The obvious test is misleading.** In the standard per-hour accounting (TFP + capital *per hour* + hours), leading economies show strong offsetting: a variance ratio of 0.71, p = 0.008. But capital per hour = capital ÷ hours, and capital moves slowly, so it automatically falls when hours rise. That built-in link is the largest offsetting term everywhere (correlation about −0.6). The pilot in Section 4 used that split, so **the pilot overstated the case.**

**2. The fair test finds no long-run offsetting at the leader.** Splitting growth *per person* instead (TFP + capital per person + hours per person) removes the shared denominator. Over 1891–2022:

| Group | Variance ratio (per person) | Expected if independent | p (offsetting) |
| --- | --- | --- | --- |
| Leaders (8 closest to US) | 0.89 | 0.96 | 0.24 |
| Followers (8 farthest) | 1.08 | 0.96 | — (they amplify) |
| **United States** | **1.10** | 1.00 | 0.65 |

**3. In the US, hours amplify instead of balance.** US hours per person and TFP move *together* over the long run (correlation +0.28). Freezing hours would make US long-run growth 45% smoother, not rougher.

**4. Two patterns do survive.**
- **Followers amplify through investment booms.** TFP and capital per person move together in followers (correlation 0.49) but not in leaders (0.08); the permutation test gives p = 0.02.
- **After 1950, leaders offset and followers do not.** The ratios are 0.69 vs 1.06 (difference p = 0.03), but that rests on only about three independent long cycles.

**5. Division bias does not explain the remaining offsetting.** Where TFP and hours offset, measurement error alone would need to exceed hours' own measured variance in 9 of 23 countries, which is impossible. Penn World Table cannot serve as an independent check on hours: its hours are almost identical to Bergeaud–Cette–Lecat's (correlation about 1.00).

**Revised research question.** Steady growth at the leader is *not* produced by TFP, capital and hours offsetting each other over the century. Since TFP carries most of the long-run variation, the question moves **inside TFP**:
1. **Inside TFP:** do education and the rest of TFP offset each other? This is Jones's transition story: rising schooling and research intensity making up for ideas getting harder to find (step 5, P1').
2. **At the leader:** does productivity track research effort? This is the direct semi-endogenous test (step 6, P4).
3. **After 1950:** is the leaders' offsetting real, and is it a new regime (for example, hours falling as income rises, as in Boppart and Krusell 2020)?

## 0c. Final status after the full attempt (17 October 2026)

All steps were run. The results are written up in [paper_balancing_leader.md](paper_balancing_leader.md).

| Planned item | Outcome |
| --- | --- |
| P1, offsetting among TFP, capital and hours | **No** over 1891–2022 once the per-hour artifact is removed; leaders offset only after 1950 (fragile) |
| P2, hours as a stabilizer | **No for the US:** hours amplify long-run swings (robust to Ramey–Francis hours) |
| H3, leaders balance, followers amplify | Followers' TFP and capital co-move, but **not robust** to the capital-to-output form |
| Inside TFP (Jones's transition), added after the first attempt | **Yes:** schooling and the rest of TFP offset (leaders 0.78, p < 0.001); robust to wars and to an alternative index; contradicted by Madsen (2014) |
| P4, Jones at the leader | **Supported:** US TFP follows research effort with a 5–10 year lag (BEA 1930–2022, NSF 1954–2022); implied β 2.2–3.3, close to Bloom et al. (2020). The earlier tension came from using patents |
| P5, measurement | 1919–41 TFP acceleration confirmed on Bakker–Crafts–Woltjer data (smaller); 1920s hours disagree across sources |

**Open questions this leaves.**
1. **Education vs Madsen (2014).** Why does schooling show up in productivity in panel regressions but not in low-frequency, within-country co-movement? Possible sources: data, frequency, or lags of a generation.
2. **The lag structure of research and productivity before 1953.** This needs quality-weighted patents (Kelly et al. 2021) or transcribed counts of research-lab employment.
3. **Is the post-1950 leader offsetting a new regime?** Possibly hours responding to income (Boppart–Krusell), visible only once the employment margin stabilized.

## 1. The question

The US has grown at about 2% a year for 150 years (Jones 2016, 2023). The usual explanation is growth accounting: education, research intensity, capital and population growth each contribute a share (Jones 2002; Fernald and Jones 2014). But growth accounting describes the pieces; it does not explain why they **add up to the same total decade after decade.** Jones (1995) stated the logic himself: if the determinants of growth move persistently while growth does not, then those persistent movements "must be offsetting." **No one has formally tested whether they do.**

## 2. Is the current explanation complete?

**No.** Each existing explanation accounts for one piece. None explains why the pieces sum to a constant.

| Explanation | What it explains | What it leaves unexplained |
| --- | --- | --- |
| Jones (2002, 2022): transitional forces (rising education and research intensity) | Why US growth ran above its long-run rate for 50+ years | Why the transitional forces happened to add up to a steady 2%; it needs a coincidence |
| Jones and Tonetti (2026): steady automation, with weak links between tasks | Why capital's share stayed stable while capital productivity grew fast | Why the flow of tasks to machines is itself steady |
| Nelson and Wright (1992): a large home market and national research system | Why the US *led* | Not why its growth *pace* was steady |
| Boppart and Krusell (2020): hours fall as productivity rises | A steady decline in hours | Whether that response is strong enough to stabilize GDP per capita growth |
| Comin and Gertler (2006); Barlevy (2007): R&D and adoption respond to the cycle | Medium-term fluctuations | They find R&D *amplifies* slowdowns, the opposite of stabilizing |
| Constancy as a measurement artifact (Romer 1986, 1989) | Smoothness of historical *cycles* | Whether the long-run *trend* is also an artifact (largely untested) |

**The missing piece** is a mechanism, or a test, showing whether the sources of growth **offset each other systematically** (balancing) or **just happened to** (coincidence).

## 3. Literature review

### 3.1 Stability as a fact, and Jones's offsetting condition
- **Jones (1995)** uses the absence of persistent changes in US growth to reject first-generation R&D models: persistent movements in growth's determinants "must be offsetting." He uses this as a test of models, not as an object of study.
- **Jones (2002); Fernald and Jones (2014):** more than three-quarters of US growth since 1950 comes from rising educational attainment and research intensity. Constancy is reconciled in a *calibrated* model, not tested.
- **Papell and Prodan (2014):** over 139+ years, only the US and Canada fit a constant-growth trend; Ben-David and Papell (1995) and Murray and Nelson (2000) debate trend stationarity.
- **Our first paper:** constant mean growth is not rejected at the frontier (break-test p = 0.33).
- **Lindsey (2013)**, a non-academic policy paper, sketches the offsetting story informally: hours, labor quality, capital deepening and TFP offset each other until the 2000s, when they all fell together.

### 3.2 Hours and labor supply
- **Boppart and Krusell (2020):** preferences consistent with balanced growth imply hours fall steadily as productivity rises (income effects).
- **Vandenbroucke (2009):** wage growth explains 82% of the 1900–1950 fall in US hours.
- **Ramey and Francis (2009):** prime-age hours were roughly flat over the century; the fall in hours per person comes from the young and the old.
- **Kopytov, Roussanov and Taschereau-Dumouchel (2023):** cheaper recreation explains much of the fall in hours.
- **Cette, Drapala and Lopez (2023):** on long-run country data (1890–2019, the same database we use), productivity and hours have a circular relationship, and the income effect dominates. **This is the closest prior work, and it must be cited and distinguished.**
- **Reif, Tesfaselassie and Wolters (2021):** a permanent fall in trend growth *lowers* steady-state hours, the opposite of a stabilizer. This is a useful tension.

### 3.3 Research effort, public R&D and crises
- **Gross and Sampat (2023):** the WWII research effort (OSRD) had lasting effects on US innovation clusters.
- **Kantor and Whalley (2025):** Cold War NASA spending raised manufacturing output.
- **Fieldhouse and Mertens (2023, working paper):** nondefense public R&D accounts for about one-fifth of US business TFP growth since WWII.
- **Moretti, Steinwender and Van Reenen (2025):** defense R&D crowds in private R&D.
- **Counterpoint:** Comin and Gertler (2006), Anzoategui et al. (2019) and Barlevy (2007) find private R&D and adoption are procyclical: they fall in slowdowns, amplifying them.

### 3.4 The 1930s–40s productivity debate
- **Field (2003, 2011):** 1929–41 was "the most technologically progressive decade" of the century.
- **Bakker, Crafts and Woltjer (2019):** new 1899–1941 estimates *reject* the claim that the 1930s had the century's highest TFP growth. **This disagrees with the productivity series we used, so the episode must be re-checked on their data.**
- **Higgs (1992); Field (2022):** wartime output in 1942–46 is badly measured under a command economy.

### 3.5 Research effort as the driver at the leader (direct tests of the semi-endogenous model)
- **Jones (1995); Kruse-Andersen (2023):** postwar US time-series tests (1950s onward) support semi-endogenous over fully endogenous models.
- **Madsen (2008, 2010):** a century of OECD data favor Schumpeterian models, in which R&D intensity matters.
- **Bloom et al. (2020):** research productivity falls about 5% a year. **Fort et al. (2026)** challenge this: growth, not ideas, is getting harder to find.
- **Historical US research effort:** Mowery and Rosenberg (1989), Mowery (1983), Nicholas (2011), Arora et al. (2025). Before 1953 there are only benchmark-year surveys.
- **Gap:** every formal test starts around 1950. **No one has confronted the 1930s–40s productivity surge with research-effort data as a test of the model.**

### 3.6 Measurement
- **Romer (1986, 1989); Balke and Gordon (1989):** pre-war volatility is sensitive to how historical GDP is built.
- **Prados de la Escosura (2016):** splicing methods bias *long-run growth rates* (for Spain).
- **Fang and Miller (2014):** US output 1875–2008 has one break in mean growth, in 1936.
- **Gap:** whether the US "2% line" survives the choice of historical series has not been tested.

### 3.7 Alternatives to constant exponential growth
- **Jones, López-Salido and Philippon (2026):** US TFP grows by roughly constant *amounts*, not constant *rates*, so percentage growth slowly declines. Any test of balancing must allow for this.

## 4. Gaps and pilot evidence

The literature check was done on 17 October 2026 using Google Scholar (partial), OpenAlex, Crossref and RePEc. Every reference marked as checked has a verified record.

| # | Puzzle | Open? | Pilot result (our data) | Feasibility |
| --- | --- | --- | --- | --- |
| **P1** | **Do the sources of growth offset each other?** | **Open.** Jones (1995) states the condition; nobody has tested it | Leaders offset, catch-up countries amplify (table below) | High: Bergeaud–Cette–Lecat database, 1890–2024 |
| **P2** | **Do hours act as a stabilizer?** | Partly open. The elasticity is estimated (Cette et al. 2023); its role in stabilizing GDP growth is not | In the 1914–49 closure, US productivity per hour rose 2.6% a year while hours per person fell 0.9% a year | High |
| P3 | Does the leader raise research effort after slowdowns? | Partly open. The effects of crisis R&D are studied; the *reaction* is not | Not run | Medium: R&D data from 1953, plus narrative coding |
| **P4** | **Does leader productivity track leader research effort before 1950?** | **Open.** This is the direct test of Jones at the leader | US productivity growth moves *against* US patenting growth over the long run (correlation −0.45; −0.62 with a 10-year lag) | Medium: pre-1953 research data are thin; patents are a crude measure |
| P5 | Is the 2% line partly a measurement artifact? | Open, but narrow | Not run | High, as a robustness module |

> **Caution (added after the first attempt):** the pilot below uses the per-hour split, whose offsetting is largely a definitional artifact. See Section 0b for the corrected per-person results.

**Pilot P1: is the long-run variance of GDP-per-capita growth smaller than its parts?** Growth is split into TFP, capital deepening and hours per person (Bergeaud–Cette–Lecat, 1891–2022), keeping only swings longer than about 25 years. The *ratio* is the variance of the total over the sum of the components' variances: below 1 means the components offset each other; about 1 means they are independent; above 1 means they amplify each other. The p-value is the share of 999 random re-alignments of the components, which keep each one's own persistence but break their timing links, that produce a ratio as low as the actual one.

| Economy | Ratio | p-value (independence) | Reading |
| --- | --- | --- | --- |
| Sweden | 0.50 | 0.05 | Offsetting |
| Switzerland | 0.61 | 0.08 | Offsetting |
| **United States** | **0.65** | 0.12 | Offsetting |
| France | 0.69 | 0.13 | Offsetting |
| United Kingdom | 0.70 | 0.21 | Offsetting |
| Netherlands | 0.84 | 0.33 | Weak |
| Denmark | 0.87 | 0.38 | Weak |
| Germany | 0.88 | 0.40 | Weak |
| Italy | 1.05 | 0.63 | None |
| **Japan** | **1.90** | 0.99 | **Amplifying** |

**Reading the pilot.**
- **The pattern is consistent but not yet proven.** Leading economies (US, UK, Switzerland, Sweden) offset; catch-up economies (Japan, Italy) amplify. Each single test is weak, so pooling across countries is the obvious next step.
- **The offsetting depends on the horizon.** Year to year, US productivity and hours move *together* (correlation +0.52); over the long run they move *apart*. Booms raise everything at once, but over decades the forces balance.

## 5. Proposed paper: "The Balancing Leader"

**Question.** Is the steady growth of the leading economy the result of its growth sources offsetting each other systematically, and through which channel (hours, capital, or productivity)?

**Hypotheses.**
- **H0, coincidence:** the components move independently; their sum is steady by chance.
- **H1, hours balance:** hours per person fall when productivity accelerates, and rise or fall less when it slows (P2).
- **H2, capital–productivity balance:** capital deepening and TFP move against each other (Jones and Tonetti 2026's automation channel; pilot: US correlation −0.50).
- **H3, leaders balance, followers amplify:** balancing is a property of the frontier, where growth comes from invention. Catch-up economies grow through adoption, which makes the forces reinforce each other.

**Design.**
1. **Decomposition.** Split GDP per capita growth into TFP, capital deepening, hours per person and, if long-run education data can be added, schooling. Use Bergeaud–Cette–Lecat for 23 countries, 1890–2024; Maddison and JST for cross-checks; the frontier envelope from our first paper as the "leader."
2. **Variance test (P1).** Compare the long-run variance ratio with an independence null: random re-alignment, plus phase-randomized simulations. Pool across leaders and across followers, and test H3 as the difference between them.
3. **Error-correction test.** When GDP per capita drifts above or below its long-run trend, which component brings it back? That identifies the balancing channel.
4. **Counterfactual paths (P2).** Freeze hours (and separately capital deepening) at their average growth, and measure how much more volatile long-run GDP per capita growth would have been. Use the productivity-to-hours elasticity from Cette et al. (2023) and the Boppart–Krusell model as discipline.
5. **The 1914–49 episode as a case study.** Does the closure-era combination (productivity up, hours down) fit the estimated balancing response, or is it an outlier? Re-check it on Bakker, Crafts and Woltjer's (2019) productivity estimates.
6. **Robustness (P5).** Alternative historical series for 1869–1929 (Kuznets–Kendrick, Romer, Balke–Gordon, Maddison), wars neutralized, and the additive-growth alternative (Jones, López-Salido and Philippon 2026).

**Companion test (P4): a direct test of Jones at the leader.** Assemble a US research-effort series back to the 1920s: benchmark surveys of industrial research labs, scientists and engineers, and patents as a fallback. Ask whether the 1930s–40s productivity surge matches the research effort that the semi-endogenous model, calibrated to Bloom et al., would require. This is where a genuine case for or against Jones would come from.

**What each outcome would mean for the original question.**

| Result | Meaning |
| --- | --- |
| H1 or H2 confirmed, stronger at leaders (H3) | Constancy is **produced by balancing at the frontier**: steady growth is an equilibrium outcome, not luck and not a property of the world's idea pool |
| H0 (no systematic offsetting) | Constancy is **partly coincidence**, which supports the "transition that happened to look straight" reading (Q1 of the literature review) and predicts future growth could drift |
| P4: leader productivity does not track leader research effort | A **direct challenge to the semi-endogenous model's** account of US growth before 1950 |
| P4: it does track, once lags and measurement are handled | **Support for Jones** at the leader, and the 1930s puzzle is resolved |

**Why it matters.**
- **It tests the condition Jones named but never tested,** in the leading economy, over 130 years.
- **It explains the steady 2% rather than describing its pieces.**
- **It has forecasting relevance.** If balancing exists, shocks to one source (AI, demographics) will be partly offset. If constancy is coincidence, they will not.

## 6. Data and next steps

- **Already in the repository:**
  - Bergeaud–Cette–Lecat (TFP, GDP per hour, hours per person, 23 countries, 1890–2024);
  - Maddison 2023 and JST R6;
  - frontier envelopes;
  - low-frequency and bootstrap tools.
- **To add:**
  - long-run education (Lee and Lee 2016 long-run dataset, to verify);
  - Bakker–Crafts–Woltjer TFP estimates;
  - alternative pre-1929 US GDP series (Romer; Balke–Gordon);
  - NSF R&D (1953 onward) and historical benchmark surveys of US research labs (P4).
- **First steps:**
  1. Pool the variance test across countries and add a phase-randomization null.
  2. Run the error-correction test.
  3. Build the hours-frozen counterfactual for the US.

## References

Checked on 17 October 2026 (Crossref, OpenAlex, RePEc, NBER or publisher), except † (from memory; verify before use).

- Anzoategui, D., Comin, D., Gertler, M., and Martinez, J. (2019). Endogenous technology adoption and R&D as sources of business cycle persistence. *AEJ: Macroeconomics* 11(3). †(title from memory; DOI checked)
- Arora, A., Belenzon, S., and Patacconi, A. (2018). The decline of science in corporate R&D. *Strategic Management Journal* 39(1).
- Arora, A., Belenzon, S., Kosenko, K., Suh, J., and Yafeh, Y. (2025). The rise of scientific research in corporate America. *Organization Science*.
- Bakker, G., Crafts, N., and Woltjer, P. (2019). The sources of growth in a technologically progressive economy: the United States, 1899–1941. *Economic Journal* 129.
- Balke, N. S., and Gordon, R. J. (1989). The estimation of prewar gross national product: methodology and new evidence. *JPE* 97(1).
- Barlevy, G. (2007). On the cyclicality of research and development. *AER* 97(4). †(title from memory; DOI checked)
- Ben-David, D., and Papell, D. H. (1995). The great wars, the great crash, and steady state growth. *JME* 36(3).
- Bloom, N., Jones, C. I., Van Reenen, J., and Webb, M. (2020). Are ideas getting harder to find? *AER* 110(4).
- Boppart, T., and Krusell, P. (2020). Labor supply in the past, present, and future: a balanced-growth perspective. *JPE* 128(1).
- Cette, G., Drapala, S., and Lopez, J. (2023). The circular relationship between productivity and hours worked: a long-term analysis. *Comparative Economic Studies*.
- Comin, D., and Gertler, M. (2006). Medium-term business cycles. *AER* 96(3).
- Fang, W., and Miller, S. M. (2014). Output growth and its volatility: the Gold Standard through the Great Moderation. *Southern Economic Journal* 80(3). †(title from memory; DOI checked)
- Fernald, J., and Jones, C. I. (2014). The future of US economic growth. *AER P&P* 104(5).
- Field, A. J. (2003). The most technologically progressive decade of the century. *AER* 93(4).
- Field, A. J. (2011). *A Great Leap Forward: 1930s Depression and U.S. Economic Growth*. Yale University Press.
- Field, A. J. (2022). *The Economic Consequences of U.S. Mobilization for the Second World War*. Yale University Press.
- Fieldhouse, A. J., and Mertens, K. (2023). The returns to government R&D: evidence from U.S. appropriations shocks. Federal Reserve Bank of Dallas WP 2305.
- Fort, T. C., Goldschlag, N., Liang, J., Schott, P. K., and Zolas, N. (2026). Growth is getting harder to find, not ideas. NBER WP 35182.
- Gordon, R. J. (2016). *The Rise and Fall of American Growth*. Princeton University Press.
- Gross, D. P., and Sampat, B. N. (2023). America, jump-started: World War II R&D and the takeoff of the U.S. innovation system. *AER* 113(12).
- Higgs, R. (1992). Wartime prosperity? A reassessment of the U.S. economy in the 1940s. *JEH* 52(1). †(title from memory; DOI checked)
- Jones, C. I. (1995). Time series tests of endogenous growth models. *QJE* 110(2).
- Jones, C. I. (2002). Sources of U.S. economic growth in a world of ideas. *AER* 92(1).
- Jones, C. I. (2016). The facts of economic growth. *Handbook of Macroeconomics* 2A. †
- Jones, C. I. (2022). The past and future of economic growth: a semi-endogenous perspective. *Annual Review of Economics* 14.
- Jones, C. I. (2023). The outlook for long-term economic growth. NBER WP 31648.
- Jones, C. I., and Tonetti, C. (2026). Past automation and future A.I.: how weak links tame the growth explosion. Working paper, Stanford GSB.
- Jones, C. J., López-Salido, D., and Philippon, T. (2026). Is growth additive? NBER WP 35415.
- Kantor, S., and Whalley, A. (2025). Moonshot: public R&D and growth. *AER*.
- Kopytov, A., Roussanov, N., and Taschereau-Dumouchel, M. (2023). Cheap thrills: the price of leisure and the global decline in work hours. *JPE Macroeconomics*. †(title from memory; DOI checked)
- Kruse-Andersen, P. K. (2023). Testing R&D-based endogenous growth models. *Oxford Bulletin of Economics and Statistics* 85(5).
- Lee, J.-W., and Lee, H. (2016). Human capital in the long run. *Journal of Development Economics* 122. †
- Lindsey, B. (2013). Why growth is getting harder. Cato Institute Policy Analysis 737.
- Madsen, J. B. (2008). Semi-endogenous versus Schumpeterian growth models. *Journal of Economic Growth* 13(1).
- Madsen, J. B. (2010). The anatomy of growth in the OECD since 1870. *JME* 57(6).
- Moretti, E., Steinwender, C., and Van Reenen, J. (2025). The intellectual spoils of war? Defense R&D, productivity, and international spillovers. *REStat*. †(title from memory; DOI checked)
- Mowery, D. C., and Rosenberg, N. (1989). *Technology and the Pursuit of Economic Growth*. Cambridge University Press.
- Murray, C. J., and Nelson, C. R. (2000). The uncertain trend in U.S. GDP. *JME* 46(1). †(title from memory; DOI checked)
- Nelson, R. R., and Wright, G. (1992). The rise and fall of American technological leadership. *JEL* 30(4).
- Nicholas, T. (2011). Did R&D firms used to patent? Evidence from the first innovation surveys. *JEH* 71(4). †(title from memory; DOI checked)
- Papell, D. H., and Prodan, R. (2014). Long run time series tests of constant steady-state growth. *Economic Modelling* 42.
- Prados de la Escosura, L. (2016). Mismeasuring long-run growth: the bias from splicing national accounts—the case of Spain. *Cliometrica* 10(3).
- Ramey, V. A., and Francis, N. (2009). A century of work and leisure. *AEJ: Macroeconomics* 1(2).
- Reif, M., Tesfaselassie, M. F., and Wolters, M. H. (2021). Technological growth and hours in the long run: theory and evidence. *Economica*. †(title from memory; DOI checked)
- Romer, C. D. (1986). Is the stabilization of the postwar economy a figment of the data? *AER* 76(3).
- Romer, C. D. (1989). The prewar business cycle reconsidered: new estimates of gross national product, 1869–1908. *JPE* 97(1).
- Vandenbroucke, G. (2009). Trends in hours: the U.S. from 1900 to 1950. *JEDC* 33(1).
