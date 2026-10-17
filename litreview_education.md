# Why Doesn't Schooling Show Up in Productivity Over the Long Run? Ex-Ante Literature Review and Design

Written 17 October 2026, **before** running the analysis · @Manuel Antonio Sanchez Garcia · companion results paper: [paper_education_productivity.md](paper_education_productivity.md)

## The question

In paper 2 ([paper_balancing_leader.md](paper_balancing_leader.md)) we tested whether productivity (TFP) grows faster when schooling grows faster. Data: Bergeaud–Cette–Lecat (BCL) TFP and Lee–Lee schooling, 23 rich countries, 1891–2010.
- **Expected:** a long-run slope of 1, if schooling raises productivity as growth accounting assumes.
- **Found:** a median of about 0.1 at leaders, and *negative* in 11 of 23 countries.
- **Contradiction:** Madsen (2014) reports that schooling raised productivity growth in nearly the same countries.

**Is our result real, or a known data or specification problem?**

## What the literature says

### The original puzzle (1990s)
- **Nelson and Phelps (1966).** The *level* of education speeds up adoption of frontier technology, so productivity growth depends on schooling × distance to the frontier.
- **Benhabib and Spiegel (1994).** Across about 78 countries, 1965–85, the *change* in human capital doesn't explain growth; the *level* does.
- **Pritchett (2001).** Across countries, 1960–87, growth in schooling is unrelated to output growth, so by construction it is *negatively* related to conventional TFP.

### The measurement-error answer (2000s): "largely resolved"
- **Krueger and Lindahl (2001).** First-differenced schooling data are very noisy, and reliability falls with shorter intervals. After correction the effect is at least the micro return.
- **de la Fuente and Doménech (2006); Cohen and Soto (2007).** Better data give schooling effects of about micro-return size.
- **Temple (2001).** The zero results are fragile to outliers and heterogeneity.

### Other lines
- **Quality, not quantity.** Hanushek and Woessmann (2008, 2012): test scores dominate years of schooling. Delgado, Henderson and Parmeter (2014): mean years of schooling are not a relevant growth variable.
- **The frontier matters.** Vandenbussche, Aghion and Meghir (2006): tertiary schooling matters more near the frontier.
- **Reverse causality.** Bils and Klenow (2000): expected growth may raise schooling.
- **Lags.** Krueger and Lindahl (2001); Topel (1999); Bassanini and Scarpetta (2002); Hanushek and Woessmann (2011): longer differences give larger effects, and reforms pay off over decades because cohorts replace each other slowly.
- **Systematic errors in long-run data.** Portela, Alessie and Teulings (2010): perpetual-inventory schooling series (the method behind Lee–Lee and Madsen) have *systematic*, not random, errors, and correcting them can lower the estimated effect.

### Madsen (2014) in detail (from his replication files)
- **Data:** 21 OECD countries, 5-year intervals 1875–2009. Schooling is rebuilt from enrolment by perpetual inventory.
- **Dependent variable:** *labour productivity* (GDP per hour) in the headline table; TFP only in one column.
- **Main schooling terms:**
  - the contemporaneous 5-year change in years of schooling;
  - the level;
  - level × distance to the frontier, which is the robust term.
- **A quick replication on his data:** the 5-year schooling change is small and insignificant (0.01–0.05). The 25-year change gives 0.044 log points per year of schooling (s.e. 0.028), roughly a slope of 1 in our units but imprecise.
- **Datasets disagree on changes.** Madsen vs. Lee–Lee, net of country and year effects:

  | | Correlation |
  | --- | --- |
  | Levels | 0.86 |
  | 5-year changes | 0.15 |
  | 25-year changes | 0.25 |
  | 50-year changes | 0.60 |

  **Implication.** If the errors were random and independent, a long-run reliability of about 0.25 would pull a true slope of 1 down to about 0.25.
- **Long-run growth accounting with education.** Bergeaud, Cette and Lecat (2018): education is the largest quality contributor, yet a large unexplained "wave" remains in mid-century productivity.

## What is resolved and what is open

- **Resolved (largely).** For post-1960 cross-country data, the zero result on schooling *changes* was mostly noisy data; better data recover micro-size effects.
- **Open.**
  - whether *within-country, long-run* swings in schooling growth line up with swings in TFP growth;
  - how reliable schooling *changes* before 1950 are;
  - the right lag structure;
  - reverse causality at low frequency.
- **A point specific to our setup.** BCL TFP does *not* subtract human capital. So random error in schooling growth pushes our slope toward **0**, not below 0. Negative slopes therefore need either systematic error or genuine offsetting.

## Pre-registered design (fixed before running)

| Test | What it answers | Prediction if "it's just data" |
| --- | --- | --- |
| T1. Same low-frequency test on several schooling datasets: Lee–Lee (hc, hca, years), **Madsen**, Barro–Lee (1950+), Penn World Table (1950+), Cohen–Soto–Leker, de la Fuente–Doménech | Is the near-zero slope specific to one dataset? | Slopes vary a lot across datasets |
| T2. Cross-dataset errors-in-variables: instrument one dataset's schooling growth with another's | How much attenuation does random error explain? | The IV slope moves toward 1 |
| T3. Lags of 10, 20 and 30 years | Do cohorts take a generation to matter? | Lagged slopes are larger |
| T4. Level and level × distance-to-frontier (Nelson–Phelps), at low frequency | Is the *level* specification the one that works, as Benhabib–Spiegel and Madsen suggest? | Level × gap is positive |
| T5. Frequency ladder: 1-, 5-, 10- and 25-year panels with country effects, with and without period effects | Does the sign depend on frequency or on common global shocks? | Positive at 5 years with period effects (Madsen-like), near zero at long horizons |
| T6. Labour productivity instead of TFP | Does using GDP per hour (Madsen's variable) reproduce his positive result? | Positive for GDP per hour, since it includes the direct effect of schooling |

**What would count as a genuine, new puzzle:** a near-zero or negative low-frequency slope that survives all of the following:
- several datasets;
- the errors-in-variables correction;
- lags;
- Madsen's own data.

**What would count as "already solved":** the slope recovers toward 1 with Madsen's data, with the errors-in-variables correction, or with lags.

## References (verified by the literature agent on 17 October 2026)

- Bassanini, A., and Scarpetta, S. (2002). Does human capital matter for growth in OECD countries? *Economics Letters* 74(3): 399–405.
- Barro, R. J., and Lee, J.-W. (2013). A new data set of educational attainment in the world, 1950–2010. *JDE* 104: 184–198.
- Benhabib, J., and Spiegel, M. M. (1994). The role of human capital in economic development. *JME* 34(2): 143–173.
- Bergeaud, A., Cette, G., and Lecat, R. (2018). The role of production factor quality and technology diffusion in twentieth-century productivity growth. *Cliometrica* 12(1): 61–97.
- Bils, M., and Klenow, P. J. (2000). Does schooling cause growth? *AER* 90(5): 1160–1183.
- Cohen, D., and Soto, M. (2007). Growth and human capital: good data, good results. *Journal of Economic Growth* 12(1): 51–76.
- de la Fuente, A., and Doménech, R. (2006). Human capital in growth regressions: how much difference does data quality make? *JEEA* 4(1): 1–36.
- Delgado, M. S., Henderson, D. J., and Parmeter, C. F. (2014). Does education matter for economic growth? *OBES* 76(3): 334–359.
- Hanushek, E. A., and Woessmann, L. (2008). The role of cognitive skills in economic development. *JEL* 46(3): 607–668.
- Hanushek, E. A., and Woessmann, L. (2012). Do better schools lead to more growth? *Journal of Economic Growth* 17(4): 267–321.
- Krueger, A. B., and Lindahl, M. (2001). Education for growth: why and for whom? *JEL* 39(4): 1101–1136.
- Lee, J.-W., and Lee, H. (2016). Human capital in the long run. *JDE* 122: 147–169.
- Madsen, J. B. (2014). Human capital and the world technology frontier. *REStat* 96(4): 676–692. Replication data: Harvard Dataverse doi:10.7910/DVN/27088.
- Madsen, J. B., and Murtin, F. (2017). British economic growth since 1270: the role of education. *Journal of Economic Growth* 22(3): 229–272.
- Nelson, R. R., and Phelps, E. S. (1966). Investment in humans, technological diffusion, and economic growth. *AER* 56(1/2): 69–75.
- Portela, M., Alessie, R., and Teulings, C. (2010). Measurement error in education and growth regressions. *Scandinavian Journal of Economics* 112(3).
- Pritchett, L. (2001). Where has all the education gone? *World Bank Economic Review* 15(3): 367–391.
- Temple, J. (2001). Generalizations that aren't? Evidence on education and growth. *EER* 45(4–6): 905–918.
- Topel, R. (1999). Labor markets and economic growth. *Handbook of Labor Economics* 3C, ch. 44.
- Vandenbussche, J., Aghion, P., and Meghir, C. (2006). Growth, distance to frontier and composition of human capital. *Journal of Economic Growth* 11(2): 97–127.
