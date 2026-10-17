# Research Labour Before R&D Statistics: Did It Grow Steadily, and Does It Explain the Frontier? Ex-Ante Literature Review and Design

Written 17 October 2026, **before** the analysis · @Manuel Antonio Sanchez Garcia · companion results paper: [paper_research_labor_history.md](paper_research_labor_history.md)

*Disclosure:* before writing this, we opened the IPUMS extracts only to check them. We confirmed which file is which, the occupation codes, and that the counts match Blank and Stigler's (1957) census tables. That check showed which source to use for levels (Section 3). No growth, productivity or lag analysis had been run.

## The question

Project 3 found that measured US research effort surged mid-century and then slowed, and that productivity growth followed with a roughly stable β. But R&D statistics start in 1929 (BEA backcast) or 1953 (NSF). For 1870–1930, when the frontier grew about 1.1–1.4% a year, we had only Blank and Stigler's engineer and chemist counts from 1890 and graduate counts. Those suggested research-type labour grew 5–7% a year while productivity grew slowly, an implied β of 5–7 against about 2.5 later.

**Questions:**
1. Using census microdata from 1850 to 2024, did US research labour grow steadily?
2. Does it explain frontier productivity with a stable β, as the semi-endogenous model requires? Or only with long lags, or not at all?

## What the literature says

### Counting research labour before R&D surveys
- **Blank and Stigler (1957, NBER):** census-consistent counts of engineers and chemists, 1890–1950. Supply grew fast, and earnings did not show shortages. This is our benchmark for validation.
- **Mowery (1983, *JEH* 43(4): 953–980); Mowery and Rosenberg (1989):** industrial research laboratories spread after 1900. National Research Council surveys counted research staff in labs from 1921, but the coverage is partial.
- **Nicholas (2010, *JEH* 70(1): 57–82):** independent inventors produced more than half of US patents as late as 1930. Much invention happened *outside* labs, so occupation counts miss it.
- **Akcigit, Grigsby and Nicholas (2017, NBER WP 23047):** they link patents to censuses for 1880–1940. Inventive activity was concentrated, and it predicts long-run state growth.
- **Maloney and Valencia Caicedo, "Engineering Growth"** (*UNVERIFIED citation details*): engineers per capita in 1880 census data predict later income across US counties and across the Americas. Engineers as "innovative capacity".
- **Murphy, Shleifer and Vishny (1991, *QJE* 106(2): 503–530):** countries with more engineering students grow faster.

### Research labour in growth theory and measurement
- **The semi-endogenous model:**
  - Jones (1995, 2002): productivity growth equals research growth divided by β.
  - Bloom, Jones, Van Reenen and Webb (2020): β ≈ 3, with research measured as IPP spending ÷ college wage, from 1930.
  - Kortum (1997): research labour and steady growth.
- **Corporate science:** Arora, Belenzon and Patacconi (2018, *SMJ* 39(1): 3–32) document the decline of science in corporate R&D after 1980. What counts as "research" changes over time.

### Lags between ideas and productivity
- **David (1990, *AER* 80(2): 355–361):** the dynamo took about 40 years to raise productivity. Factory electrification reached 50% only in the 1920s.
- **Comin and Hobijn (2010, *AER* 100(5): 2031–2059):** technologies are adopted on average about 45 years after invention.
- **Field (2011); Gordon (2016):** the 1920s–30s productivity surge rested on inventions from 1870–1900.
- **Implication:** research growth in 1870–1910 may show up in productivity only in 1920–1970.

### Status
- **Census-based research labour from 1850 has not been linked to frontier productivity in a semi-endogenous framework.**
  - Blank–Stigler cover 1890–1950 for supply questions only.
  - Bloom et al. start in 1930, and Jones (2002) in 1950.
  - Akcigit et al. study inventors, not research labour as a whole.
- **Honest flag:** the counts themselves partly replicate Blank and Stigler. The new parts are:
  - the 1850–1880 and 1950–2024 extensions from one consistent source;
  - the β-by-era and lag tests.

## Pre-registered design (fixed before running)

**Data.**
- **IPUMS USA:**
  - Extract A: full count 1850–1950 plus samples 1960–2024, restricted to science and engineering occupations (OCC1950).
  - Extract B: 1% samples of the labour force, 1850–2024.
- **Levels come from the 1% samples.** In the validation check they match Blank–Stigler within ±7% for 1900–1950, while the full count undercounts by 11–25% (automated coding).
- **The full count is used only for composition:** industry, class of worker and education, which are large-N shares.

**Research labour series:**
- **S1 (core): engineers + chemists** (OCC1950 41–49, 7). Consistently coded in every census.
- **S2 (broad): S1 + natural scientists + all college faculty** (61–69, 10–29). The 1940 census has no natural scientists in OCC1950, so 1940 is interpolated geometrically between 1930 and 1950.
- **S3 (industrial research-type):** S1 working in manufacturing, communications and utilities (IND1950), plus natural scientists, where IND1950 is available.
- **Per worker:** each series ÷ labour force.
- **Excluded:** surveyors (B&S include them; robustness only) and technicians (classification jump in 1940).

**Productivity:**
- US TFP from Bergeaud–Cette–Lecat (1891–), plus top-5 frontier TFP from paper 1 (1891–).
- GDP per capita (Maddison) from 1850, as a check.

| Test | Question | Supports "research labour is the engine" if… |
| --- | --- | --- |
| T1. Decade growth of S1–S3, 1850s–2010s; SD of decade growth before vs after 1930 | Did research labour grow steadily? | Steady growth, especially when frontier growth was steady |
| T2. β by era: mean research growth (lagged one decade) ÷ mean TFP growth, for 1890–1930, 1930–1970 and 1970–2020 | Is diminishing returns stable? | β similar across eras (about 2–3) |
| T3. Correlation of decade research growth with TFP growth 0–4 decades later | Long lags (David; Comin–Hobijn)? | Peak at 2–4 decades |
| T4. T2–T3 with frontier (top-5) TFP | Frontier vs US | Same pattern |
| T5. Composition: share of S1 in manufacturing/communications/utilities, private wage work, college degree (1940+) | Were early engineers research workers? | Rising share in research-type industries and degrees |
| T6. Decade overlap with Project 3's BEA and Bloom et al. research measures, 1930–2020 | Does the census measure track R&D effort? | Positive correlation |

**What would answer the "1870–1930" puzzle:**
- **(a)** S grew about 3–4% a year before 1930 with β ≈ 2–3: steady research explains the period.
- **(b)** S grew much faster than that but β stabilizes with 2–4 decade lags: research explains it with diffusion lags.
- **(c)** Neither: early engineers were mostly not doing research (T5), and the engine before 1930 was something else.

**Caveats fixed in advance.**
1. **An occupation is not research.** Most engineers worked in construction, railroads, mining and operations.
2. **Census occupational coding changed across years** (OCC1950 harmonizes it imperfectly). 1940 lacks scientists, and 1890 is missing entirely.
3. **Few decades:** about 17 data points, and the lag tests are descriptive.
4. **US only.** The frontier was not the US before 1899.

## Addendum (17 October 2026, written before running): pre-registered hold-out test of the dynamic model

The dynamic semi-endogenous fit in the results paper was exploratory, chosen after the steady-state test failed. To test it properly:

**The model.** Productivity growth = θ · S^λ / A^β, where S is census research labour (main: S1, engineers and chemists; check: S2). The model is simulated annually.

**Two sample splits.**
- **Main:** fit θ and β on 1891–1970 (decades 1890s–1960s), then forecast 1971–2020 (decades 1970s–2010s).
- **Harder split:** fit on 1891–1950, forecast 1951–2020. Here the model must predict the mid-century peak *and* the decline.

**How the forecast is run.** It starts from the *actual* TFP level at the end of the fitting window and uses the actual census S. No parameter is re-estimated, and no post-split TFP data are used.
- **λ:** fixed at 1 (main) and 0.75 (check).
- **Outcomes:** US TFP (BCL) and frontier top-5 TFP.

**Benchmarks**, all using only fitting-window information:
- **(i) Constant growth:** the fitting-window mean. This is the "Kaldor" null.
- **(ii) Last decade's growth carried forward.**
- **(iii) The steady-state formula:** growth = research growth one decade earlier ÷ in-sample β.
- **(iv) Placebo:** the same dynamic model driven by the total labour force.

**Metrics.**
- Root-mean-square error of decade TFP growth over the forecast decades.
- Predicted vs actual mean growth over the forecast window.

**Success criterion, fixed now.** The model passes if, for the main split, all three hold for **both** US and frontier TFP:
1. it has a lower forecast error than constant growth (i);
2. it has a lower forecast error than the placebo (iv);
3. its predicted mean growth for 1971–2020 is below the *actual* mean growth of 1931–1970. In words: it forecasts the post-1970 slowdown without having seen it.

Anything less is reported as a failure or a partial pass.

## References

- Akcigit, U., Grigsby, J., and Nicholas, T. (2017). The rise of American ingenuity: innovation and inventors of the golden age. NBER WP 23047.
- Arora, A., Belenzon, S., and Patacconi, A. (2018). The decline of science in corporate R&D. *Strategic Management Journal* 39(1): 3–32.
- Bergeaud, A., Cette, G., and Lecat, R. (2016). Productivity trends in advanced countries between 1890 and 2012. *Review of Income and Wealth* 62(3): 420–444.
- Blank, D. M., and Stigler, G. J. (1957). *The Demand and Supply of Scientific Personnel*. NBER.
- Bloom, N., Jones, C. I., Van Reenen, J., and Webb, M. (2020). Are ideas getting harder to find? *AER* 110(4): 1104–1144.
- Comin, D., and Hobijn, B. (2010). An exploration of technology diffusion. *AER* 100(5): 2031–2059.
- David, P. A. (1990). The dynamo and the computer: an historical perspective on the modern productivity paradox. *AER* 80(2): 355–361.
- Field, A. J. (2011). *A Great Leap Forward*. Yale University Press.
- Gordon, R. J. (2016). *The Rise and Fall of American Growth*. Princeton University Press.
- Jones, C. I. (1995). R&D-based models of economic growth. *JPE* 103(4): 759–784.
- Jones, C. I. (2002). Sources of U.S. economic growth in a world of ideas. *AER* 92(1): 220–239.
- Kortum, S. (1997). Research, patenting, and technological change. *Econometrica* 65(6): 1389–1419.
- Maloney, W. F., and Valencia Caicedo, F. "Engineering growth." *(UNVERIFIED: venue and year to be confirmed.)*
- Mowery, D. C. (1983). Industrial research and firm size, survival, and growth in American manufacturing, 1921–1946: an assessment. *JEH* 43(4): 953–980.
- Mowery, D. C., and Rosenberg, N. (1989). *Technology and the Pursuit of Economic Growth*. Cambridge University Press.
- Murphy, K. M., Shleifer, A., and Vishny, R. W. (1991). The allocation of talent: implications for growth. *QJE* 106(2): 503–530.
- Nicholas, T. (2010). The role of independent invention in U.S. technological development, 1880–1930. *JEH* 70(1): 57–82.
- Ruggles, S., et al. IPUMS USA: Version 16.0 [dataset]. Minneapolis, MN: IPUMS. *(Cite the exact version shown on your extract page.)*
