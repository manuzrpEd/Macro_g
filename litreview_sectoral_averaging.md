# Is Steady Growth an Average of Unsteady Industries? Ex-Ante Literature Review and Design

Written 17 October 2026, **before** running the analysis · @Manuel Antonio Sanchez Garcia · companion results paper: [paper_sectoral_averaging.md](paper_sectoral_averaging.md)

## The question

Our earlier work ruled out the usual candidates for keeping frontier growth steady:
- **Not offsetting between capital, hours and productivity** (paper 2).
- **Not steadily growing research** (Project 3).
- **Not policy:** Jones (1995) shows that trend growth did not move when policy changed massively.

And the frontier was in fact *not* very steady: about 1.1–1.4% a year before 1929, about 2% in 1929–2007, and about 1% since (exploration in `output/world_research/`).

One mechanism is left. **Aggregate productivity is a weighted sum of many industries', and if their booms are not synchronized, the sum is much steadier than any part.** Two versions:
- **Averaging (diversification).** Industry waves are independent or offsetting, so they cancel out in the aggregate.
- **Baumol reweighting.** When an industry's productivity booms, its relative price falls and, if demand is inelastic, its share of spending falls. The booming industry then gets *less* weight, which damps the aggregate (a built-in stabilizer).

The aggregation identity (Domar 1961; Hulten 1978) is

$$
g^{TFP}_{agg,t} = \sum_i d_{i,t}\, g^{TFP}_{i,t}, \qquad d_{i,t} = \frac{\text{nominal gross output}_i}{\text{nominal value added}_{agg}}
$$

With value-added productivity measures, the weights are value-added shares instead of Domar weights.

## What the literature says

All references below were verified by a literature search on 17 October 2026, except where noted.

### 1. Do industry shocks average out? (business-cycle evidence)
- **Fundamental volatility.** Carvalho and Gabaix (2013, *AER*) build aggregate volatility from industry volatilities and Domar weights alone. Its rise and fall tracks the Great Moderation and its undoing, so composition matters for volatility.
- **Sectoral shocks are large.**
  - Foerster, Sarte and Watson (2011, *JPE*): sector-specific shocks explain about half of quarterly industrial production after 1984.
  - Atalay (2017): at least half of aggregate volatility.
  - Garin, Pries and Sims (2018): the aggregate-shock share fell from about 70% to about 30% after 1983.
- **Averaging can fail.**
  - Gabaix (2011): firm sizes are fat-tailed, so idiosyncratic shocks don't average out at 1/√N.
  - Acemoglu, Carvalho, Ozdaglar and Tahbaz-Salehi (2012): input-output networks dominated by a few suppliers propagate shocks.
  - The classic debate is Horvath (2000) vs Dupor (1999).
- **Diversification as development.** Koren and Tenreyro (2007, 2013) and Acemoglu and Zilibotti (1997): richer economies diversify across more technologies, which lowers volatility.
- **Status:** all of this is about **business-cycle** volatility.

### 2. Low-frequency (trend) evidence by industry
- **Nearest precedent: Foerster, Hornstein, Sarte and Watson (2022, *JPE*).** Using post-1950 US sectoral trends:
  - sector-specific factors explain about three-quarters of the long-run changes in GDP growth;
  - construction (1950–80) and durables (2000–18) drove the decline in trend growth.

  **They explain the *decline*. They do not test whether sectoral trends offset each other** or how steady the aggregate is relative to its parts. No pre-war data.
- **Concentration and rotating leadership ("mushrooms, not yeast").**
  - Harberger (1998): productivity gains are concentrated in a few industries, and the leaders change from period to period.
  - Inklaar and Timmer (2007): concentration falls when aggregate growth is high (*confirmed only via a reference list*).
  - Napoletano, Roventini and Sapio (2004): concentration can also arise from one common driver.
- **Industry origins of the post-war episodes.**
  - Jorgenson, Ho and Stiroh (2005); Stiroh (2002); Jorgenson, Ho, Samuels and Stiroh (2007): the IT industries account for half of the post-1995 resurgence.
  - Fernald (2015): the slowdown since 2004 is in IT-producing and IT-using industries.
  - David, de Souza and Schommer (2025): IT is about 8% of value added but about 45% of TFP growth since 1988.
- **Pre-war.**
  - Bakker, Crafts and Woltjer (2019, *EJ*): TFP growth of 1.3% a year over 1899–1941, broadly based. In the 2015 working paper, industry rankings barely persist between benchmarks (rank correlations of 0.4, 0.0 and 0.2; *to confirm in the published version*).
  - Field (2003, 2011): the 1930s were the most technologically progressive decade.
  - David and Wright (2003): manufacturing's 1920s surge from electrification.
- **Gordon (2016): "one big wave."** A few great inventions arrived together and lifted productivity in 1920–70. That is a *synchronized* view, the opposite of averaging.
- **Burns (1934):** individual industries decelerate while new ones keep aggregate output growing. This is the earliest statement of our hypothesis, for output rather than productivity.
- **Status:** rotation of leadership is documented (concentration). **Whether industry waves cancel out at low frequency has not been tested** (Carvalho–Gabaix's decomposition has not been applied at decadal frequency or before 1947).

### 3. Baumol reweighting: drag or stabilizer?
- **A drag on trend growth.**
  - Baumol (1967): spending shifts to stagnant sectors.
  - Nordhaus (2008): confirmed for US industries, 1948–2001.
  - Hartwig (2011): the same in EU KLEMS data.
  - Baqaee and Farhi (2019): beyond Hulten's first-order formula, cost disease lowers US TFP growth over 1948–2014.
  - Duernecker, Herrendorf and Valentinyi (2024): a significant contributor to the post-war slowdown.
  - Sarte and Taylor (2025): with the 1947 sector mix, growth would have been 1.72% instead of 1.48%.
- **A stabilizer of *volatility*.**
  - Moro (2012, 2015): the shift to services lowers TFP volatility, explaining about 28% of the Great Moderation.
  - Burren and Neusser (2013): about 30%.

  Both work at cyclical frequency.
- **Theory.** Different industry growth rates are compatible with balanced aggregate growth:
  - Ngai and Pissarides (2007);
  - Acemoglu and Guerrieri (2008);
  - León-Ledesma and Moro (2020).

  Oulton (2001) shows that if the stagnant industries supply inputs to others, aggregate growth need not fall.
- **Status:** **nobody tests whether reweighting damps the *low-frequency* swings of aggregate productivity.**

### 4. Theory of steady growth from many ideas
- Kortum (1997) and Jones (2005): with Pareto-distributed ideas, aggregate productivity grows steadily even though each technology does not.
- Comin and Gertler (2006): medium-term cycles of 8–50 years exist in the aggregate.
- Müller and Watson (2018): methods for long-run covariances (our tool).

## Gap

The literature has three pieces we can build on:
- the decomposition of aggregate volatility into industry parts (Carvalho–Gabaix), at business-cycle frequency;
- rotating industry leadership (Harberger; BCW), measured as concentration;
- Baumol as a drag on growth (Nordhaus; Baqaee–Farhi).

**Not done:** the low-frequency, 1899–present version, which asks (i) whether industry productivity waves cancel in the aggregate, and (ii) whether Baumol reweighting stabilizes aggregate trend growth. **Honest flag:** each piece is close to existing work. The novelty is the frequency band, the 120-year span, and the two questions combined.

## Pre-registered design (fixed before running)

**Data.**
- **1899–1941:** Bakker–Crafts–Woltjer, 38 industries of the private domestic economy. Value-added TFP and value-added shares, four periods (1899–1909, 1909–19, 1919–29, 1929–41).
- **1948–2014:** Jorgenson–Ho–Samuels US KLEMS (World KLEMS release of 2017), 61 private industries (government excluded). Gross-output TFP is computed as a Törnqvist residual from real and nominal gross output, capital, labor and intermediates. Contributions use Domar weights. Note that Domar-weighted gross-output TFP equals value-added-share-weighted value-added TFP, so the aggregate is comparable to BCW's.
- **2015–2024:** the official BEA–BLS Integrated Industry-Level Production Account (release of April 2026), same 61 industries, "Integrated TFP Index" with gross output and value added. Its 1998–2014 overlap with Jorgenson–Ho–Samuels is used as a validation check.
- **Robustness:** the BEA–BLS experimental account for 1947–2016.
- **Bridge:** 11 broad sectors harmonized across both. They give 8 eras: four pre-war, plus 1948–73, 1973–95, 1995–2007 and 2007–24.
  - **The 11 sectors:** agriculture, mining, utilities, construction, durable manufacturing, nondurable manufacturing, trade, transportation, communications/information, finance/insurance/real estate, other services.
- **Annual low-frequency tests:** 1949–2024, q = 6.

| Hypothesis | Test | Supports the hypothesis if… |
| --- | --- | --- |
| **H1. Averaging** | Low-frequency SD of aggregate TFP growth vs two benchmarks: *synchronized* (Σ wᵢ sdᵢ, every industry booms together) and *independent* (√Σ wᵢ² sdᵢ²). Variance ratio R = Var(Σ contributions) / Σ Var(contributions), with a surrogate null of independent industries. Share of industry low-frequency variance explained by the first common factor. | Aggregate SD near the *independent* benchmark and far below *synchronized*; R ≤ 1; weak common factor |
| **H1 alternative: common waves (Gordon)** | Same statistics | Aggregate SD near *synchronized*; R well above 1; strong common factor |
| **H2. Relay of leaders** | Rank correlation of industry TFP growth between consecutive eras; concentration (share of aggregate TFP growth from the top 5 industries) | Low persistence (rank correlation ≈ 0) and different leaders in each era |
| **H3. Baumol stabilizer** | (a) Correlation of industry TFP growth in an era with the change in its nominal share in the next era. (b) Swings across eras in actual aggregate TFP growth vs a fixed-weight counterfactual (weights frozen at the start) | (a) negative; (b) the actual aggregate swings *less* than the fixed-weight one |
| **H4. Can averaging explain the frontier's path?** | Was the mid-century acceleration broad (share of industries accelerating; common-factor share 1929–73) or concentrated? | Concentrated in a few industries → averaging is the mechanism that failed. Broad → a common wave (Gordon/Field) |

**Caveats fixed in advance.**
1. **Pre-war measure differs from post-war.** BCW is value-added TFP for the private domestic economy (little government or services), while post-war accounts are gross-output TFP with Domar weights. Cross-era comparisons use broad sectors and are read qualitatively.
2. **Few eras.** About eight eras and 4–6 annual low-frequency cycles after 1947, so results are suggestive.
3. **Classification breaks.** SIC 1957 → SIC 1987 → NAICS.
4. **Services output is hard to measure,** which can manufacture Baumol effects.
5. **Aggregate TFP here is the industry aggregate,** not the BCL economy-wide series used in earlier papers.

## References

- Acemoglu, D., Carvalho, V. M., Ozdaglar, A., and Tahbaz-Salehi, A. (2012). The network origins of aggregate fluctuations. *Econometrica* 80(5): 1977–2016.
- Acemoglu, D., and Guerrieri, V. (2008). Capital deepening and nonbalanced economic growth. *JPE* 116(3): 467–498.
- Acemoglu, D., and Zilibotti, F. (1997). Was Prometheus unbound by chance? Risk, diversification, and growth. *JPE* 105(4): 709–751.
- Atalay, E. (2017). How important are sectoral shocks? *AEJ: Macro* 9(4): 254–280.
- Bakker, G., Crafts, N., and Woltjer, P. (2019). The sources of growth in a technologically progressive economy: the United States, 1899–1941. *Economic Journal* 129(622): 2267–2294.
- Baqaee, D. R., and Farhi, E. (2019). The macroeconomic impact of microeconomic shocks: beyond Hulten's theorem. *Econometrica* 87(4): 1155–1203.
- Baumol, W. J. (1967). Macroeconomics of unbalanced growth: the anatomy of urban crisis. *AER* 57(3): 415–426.
- Burns, A. F. (1934). *Production Trends in the United States since 1870*. NBER.
- Burren, D., and Neusser, K. (2013). The role of sectoral shifts in the decline of real GDP volatility. *Macroeconomic Dynamics* 17(3): 477–500.
- Carvalho, V. M., and Gabaix, X. (2013). The great diversification and its undoing. *AER* 103(5): 1697–1727.
- Comin, D., and Gertler, M. (2006). Medium-term business cycles. *AER* 96(3): 523–551.
- David, J., de Souza, G., and Schommer, A. (2025). Concentrated growth: the role of the IT sector. *Chicago Fed Letter* 515.
- David, P. A., and Wright, G. (2003). General purpose technologies and surges in productivity. In David and Thomas (eds.), *The Economic Future in Historical Perspective*. OUP.
- Domar, E. D. (1961). On the measurement of technological change. *Economic Journal* 71(284): 709–729.
- Duernecker, G., Herrendorf, B., and Valentinyi, Á. (2024). Structural change within the services sector and the future of cost disease. *JEEA* 22(1): 428–473.
- Dupor, B. (1999). Aggregation and irrelevance in multi-sector models. *JME* 43(2): 391–409.
- Fernald, J. G. (2015). Productivity and potential output before, during, and after the Great Recession. *NBER Macroeconomics Annual 2014* 29.
- Field, A. J. (2003). The most technologically progressive decade of the century. *AER* 93(4): 1399–1413.
- Field, A. J. (2011). *A Great Leap Forward: 1930s Depression and U.S. Economic Growth*. Yale University Press.
- Foerster, A. T., Hornstein, A., Sarte, P.-D. G., and Watson, M. W. (2022). Aggregate implications of changing sectoral trends. *JPE* 130(12): 3286–3333.
- Foerster, A. T., Sarte, P.-D. G., and Watson, M. W. (2011). Sectoral versus aggregate shocks: a structural factor analysis of industrial production. *JPE* 119(1): 1–38.
- Gabaix, X. (2011). The granular origins of aggregate fluctuations. *Econometrica* 79(3): 733–772.
- Garin, J., Pries, M. J., and Sims, E. R. (2018). The relative importance of aggregate and sectoral shocks and the changing nature of economic fluctuations. *AEJ: Macro* 10(1): 119–148.
- Gordon, R. J. (2016). *The Rise and Fall of American Growth*. Princeton University Press.
- Harberger, A. C. (1998). A vision of the growth process. *AER* 88(1): 1–32.
- Hartwig, J. (2011). Testing the Baumol–Nordhaus model with EU KLEMS data. *Review of Income and Wealth* 57(3): 471–489.
- Horvath, M. (2000). Sectoral shocks and aggregate fluctuations. *JME* 45(1): 69–106.
- Hulten, C. R. (1978). Growth accounting with intermediate inputs. *REStud* 45(3): 511–518.
- Inklaar, R., and Timmer, M. P. (2007). Of yeast and mushrooms: patterns of industry-level productivity growth. *German Economic Review* 8(2): 174–187. *(Confirmed only via a reference list.)*
- Jones, C. I. (1995). Time series tests of endogenous growth models. *QJE* 110(2): 495–525.
- Jones, C. I. (2005). The shape of production functions and the direction of technical change. *QJE* 120(2): 517–549.
- Jorgenson, D. W., Gollop, F. M., and Fraumeni, B. M. (1987). *Productivity and U.S. Economic Growth*. Harvard University Press.
- Jorgenson, D. W., Ho, M. S., Samuels, J. D., and Stiroh, K. J. (2007). Industry origins of the American productivity resurgence. *Economic Systems Research* 19(3): 229–252.
- Jorgenson, D. W., Ho, M. S., and Stiroh, K. J. (2005). *Information Technology and the American Growth Resurgence*. MIT Press.
- Kendrick, J. W. (1961). *Productivity Trends in the United States*. Princeton University Press for NBER.
- Koren, M., and Tenreyro, S. (2007). Volatility and development. *QJE* 122(1): 243–287.
- Koren, M., and Tenreyro, S. (2013). Technological diversification. *AER* 103(1): 378–414.
- Kortum, S. (1997). Research, patenting, and technological change. *Econometrica* 65(6): 1389–1419.
- León-Ledesma, M., and Moro, A. (2020). The rise of services and balanced growth in theory and data. *AEJ: Macro* 12(4): 109–146.
- Moro, A. (2012). The structural transformation between manufacturing and services and the decline in the US GDP volatility. *RED* 15(3): 402–415.
- Moro, A. (2015). Structural change, growth, and volatility. *AEJ: Macro* 7(3): 259–294.
- Müller, U. K., and Watson, M. W. (2018). Long-run covariability. *Econometrica* 86(3): 775–804.
- Napoletano, M., Roventini, A., and Sapio, S. (2004). Yeast vs. mushrooms: a note on Harberger's "A vision of the growth process". LEM WP 2004/03.
- Ngai, L. R., and Pissarides, C. A. (2007). Structural change in a multisector model of growth. *AER* 97(1): 429–443.
- Nordhaus, W. D. (2008). Baumol's diseases: a macroeconomic perspective. *B.E. Journal of Macroeconomics* 8(1), Art. 9.
- Oulton, N. (2001). Must the growth rate decline? Baumol's unbalanced growth revisited. *Oxford Economic Papers* 53(4): 605–627.
- Sarte, P.-D., and Taylor, J. (2025). *Richmond Fed Economic Brief* 25-08.
- Stiroh, K. J. (2002). Information technology and the U.S. productivity revival: what do the industry data say? *AER* 92(5): 1559–1576.
