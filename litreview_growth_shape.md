# Is Long-Run Growth Constant, Additive or Slowly Declining? Ex-Ante Literature Review and Design

Written 17 October 2026, **before** looking at results · @Manuel Antonio Sanchez Garcia · companion results paper: [paper_growth_shape.md](paper_growth_shape.md)

## The question

US GDP per capita has grown about 2% a year for 150 years, which is what *exponential* growth looks like. There are two alternatives:
- **Additive growth.** Income rises by a roughly constant *dollar amount* each year, so the percentage rate slowly falls.
- **Exponential growth with a slowly declining trend.**

Which shape fits frontier GDP per capita best? And can roughly 150 years of data tell them apart at all? This is Q2 of our first literature review, still untested for GDP per capita.

## What the literature says

### The additive-growth papers (all about TFP, not GDP per capita)
- **Philippon (2022, NBER w29950).**
  - Data: US and 23-country TFP from the Bergeaud–Cette–Lecat (BCL) database.
  - A constant-increment (additive) model forecasts 10–20 years ahead 25–60% better than a geometric (exponential) one, with a break in 1933.
  - Its 2023 draft has the only Monte Carlo, and it checks size only.
- **Jones, López-Salido and Philippon (2026, NBER w35415).** This paper supersedes Philippon (2022).
  - Models: both are state-space models with a random-walk trend.
    - additive: A_t = A_{t−1} + b_t + noise;
    - geometric: A_t = A_{t−1}(1+g_t)·noise.
  - Data and scoring: US BCL TFP, 1890–2022, with the war years dropped. Comparison uses cumulative 10-year-ahead log scores, *tempered* weights and a 0.9 prior on the geometric model.
  - Result: the probability of additive growth is above 0.99 by 2022; additive wins in 22 of 23 countries.
  - Their only simulation is under the additive model.
- **Critiques.**
  - **Noise specification decides the result.** Erdil (2022) found a likelihood ratio of about 50 for linear TFP, which falls to about 1.6 once both models get a volatility trend.
  - **Parameter counts matter.** A two-piece linear model has 4 parameters against 2 for the exponential, and a fitted two-piece linear model beats a *true* exponential in simulations.
  - **GDP per capita is ambiguous.** Vollrath (2022) finds it looks exponential to 2008 and additive afterwards.
  - Sampi (2024) finds additive growth for most high-income countries' TFP.

### Constancy and trend tests
- **Jones (1995, 2016, 2023).**
  - US GDP per person sits on a ~2% log-linear line.
  - It grew *faster* after 1929 (1.76% → 2.23%), which a single constant-increment additive model cannot produce for GDP.
  - Theory predicts slowly declining trend growth.
- **Constancy survives for the US and Canada only.**
  - Papell and Prodan (2014): only the US and Canada fit a constant-growth trend over 139+ years.
  - Ben-David and Papell (1995): most countries show trend breaks after the wars.
- **Break and unit-root conclusions are fragile** to the Depression, wars and fat tails (Perron 1989; Murray and Nelson 2000; Russo and Foster-McGregor 2022).

### Low-frequency and long-horizon evidence
- **Müller and Watson (2008, 2016, 2017).** About 150 years hold only 10–15 independent long-run observations. Long-run uncertainty is large.
- **Müller, Stock and Watson (2022).** The frontier factor's trend growth is a persistent drift (about 1.9%), but "the data are largely uninformative" about how much it varies.
- **Lunsford and West (2026).** On 17 countries, growth of GDP per capita behaves like a stationary series at 10–25 years, and no model is well calibrated at 50 years.
- **Stock and Watson (1998).** The estimated variance of trend growth piles up at zero, so declines are hard to detect.

### Slowdown evidence
- Antolin-Diaz, Drechsel and Petrella (2017), Crump, Gospodinov and Wieman (2024), Eo and Morley (2022) and Fernald (2015) find a decline in US trend growth since the 1960s or before 2008.

### Older direct tests on GDP per capita
- **Kitov and Kitov (2012):** constant increments cannot be rejected, but the test uses regressions only.
- **Lange, Pütz and Kopp (2018):** linear growth is chosen for 11 of 18 countries over 1960–2013, but only 4 of 18 without 2008–13, so the result is very sample-dependent.
- **Lera and Sornette (2015):** growth alternates between bimodal regimes.

## The gap

- **No equal-flexibility comparison for GDP per capita.** No paper compares additive, exponential and slowly declining models on *GDP per capita* (US or the frontier envelope) with the same noise flexibility and properly sequential predictive scoring.
- **No two-sided power study.** No one shows the procedure recognizes *each* model when it is true.
- **The relevant middle case is untested.** Additive TFP implies GDP per capita that grows like y^(2/3) linearly in time (because capital follows TFP). That curvature has never been tested on GDP.

## Pre-registered design (fixed before seeing results)

| Element | Choice | Reason (pitfall addressed) |
| --- | --- | --- |
| Series | US GDP per capita (Maddison 2023, 1870–2022; BCL 1890–2022); frontier envelope (max of 16); UK; **US GDP per hour (BCL)** | US vs frontier; per capita vs per hour (demography) |
| Models | Exponential; exponential with linearly declining growth; exponential with drifting growth (discounted learning); additive with level noise; additive with proportional noise; **power model y^λ linear in time (λ = 1 additive, λ → 0 exponential, λ ≈ 2/3 additive TFP)**; one-break versions of exponential and additive | Nests the hypotheses; tests the intermediate curvature |
| Noise | Same variance law across exponential and additive-proportional models; robustness with a **volatility trend** in every model | Erdil's critique |
| Scoring | **One-step prequential log scores** with parameters re-estimated each year from 1900 (a true sequential marginal likelihood), plus BIC | Avoids the tempering problem of overlapping h-step scores |
| Long horizon | Pseudo-out-of-sample 10- and 25-year forecasts: error and 90% coverage | Comparison with JLP and Lunsford–West |
| Power | Simulate from each fitted model (200 paths) and record how often each method picks the true model | No two-sided power study exists |
| Wars | Main series as is; robustness with 1914–19 and 1939–49 growth neutralized; post-1950 subsample | Murray–Nelson; JLP drop 1942–46 |

**What would count as an answer:**
- the power model's λ estimated with a confidence interval that excludes 0 or 1;
- prequential weights that converge in favour of one model;
- a power study showing the procedure could have told the models apart.

**What would count as "the data cannot tell":** wide λ intervals, weights that keep switching, and low power.

## References (verified by the literature agent on 17 October 2026)

- Antolin-Diaz, J., Drechsel, T., and Petrella, I. (2017). Tracking the slowdown in long-run GDP growth. *REStat* 99(2): 343–356.
- Ben-David, D., and Papell, D. H. (1995). The great wars, the great crash, and steady state growth. *JME* 36(3): 453–475.
- Crump, R. K., Gospodinov, N., and Wieman, H. (2024). Sparse trend estimation. *REStat* (online); FRBNY Staff Report 1049.
- Eo, Y., and Morley, J. (2022). Why has the U.S. economy stagnated since the Great Recession? *REStat* 104(2): 246–258.
- Erdil, E. (2022). Comments on "Is growth linear, not exponential?" and "Report likelihood ratios," LessWrong (blog posts).
- Fernald, J. G. (2015). Productivity and potential output before, during, and after the Great Recession. *NBER Macroeconomics Annual* 29: 1–51.
- Jones, C. I. (1995). Time series tests of endogenous growth models. *QJE* 110(2): 495–525.
- Jones, C. I. (2016). The facts of economic growth. *Handbook of Macroeconomics* 2: 3–69.
- Jones, C. I. (2023). The outlook for long-term economic growth. NBER WP 31648.
- Jones, C. J., López-Salido, D., and Philippon, T. (2026). Is growth additive? NBER WP 35415.
- Kitov, I., and Kitov, O. (2012). Real GDP per capita since 1870. arXiv:1205.5671.
- Lange, S., Pütz, P., and Kopp, T. (2018). Do mature economies grow exponentially? *Ecological Economics* 147: 123–133.
- Lera, S. C., and Sornette, D. (2017). Evidence of a bimodal US GDP growth rate distribution: a wavelet approach. *Quantitative Finance and Economics* 1.
- Lunsford, K. G., and West, K. D. (2026). An empirical evaluation of some long-horizon macroeconomic forecasts. *Journal of Econometrics* 255: 106221.
- Müller, U. K., and Watson, M. W. (2008). Testing models of low-frequency variability. *Econometrica* 76(5): 979–1016.
- Müller, U. K., and Watson, M. W. (2016). Measuring uncertainty about long-run predictions. *REStud* 83(4): 1711–1740.
- Müller, U. K., Stock, J. H., and Watson, M. W. (2022). An econometric model of international growth dynamics for long-horizon forecasting. *REStat* 104(5): 857–876.
- Murray, C. J., and Nelson, C. R. (2000). The uncertain trend in U.S. GDP. *JME* 46(1): 79–95.
- Papell, D. H., and Prodan, R. (2014). Long run time series tests of constant steady-state growth. *Economic Modelling* 42: 464–474.
- Perron, P. (1989). The Great Crash, the oil price shock, and the unit root hypothesis. *Econometrica* 57(6): 1361–1401.
- Philippon, T. (2022). Additive growth. NBER WP 29950.
- Russo, E., and Foster-McGregor, N. (2022). Characterizing growth instability. *Journal of Evolutionary Economics* 32(2): 713–756.
- Sampi, J. (2024). Additive growth? Not always. *Economics Letters* 235: 111568.
- Stock, J. H., and Watson, M. W. (1998). Median unbiased estimation of coefficient variance in a time-varying parameter model. *JASA* 93: 349–358.
- Vollrath, D. (2022). Implications of additive growth. Growth Economics Blog.
