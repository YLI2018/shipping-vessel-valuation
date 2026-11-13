# Hedonic Ship Price Model (M1+)

**Which features drive second-hand ship prices, and by how much.** M1 values a ship from its age alone. M1+ explains the log of the sale price by age, size, yard country, survey timing, scrubber, eco design, en bloc sale and the market level, all at once, by ordinary least squares. The dataset is described as containing sales reported on or before 22 May 2026. Report dates are not included in the published CSV, so that cutoff cannot be independently verified from this file.

📄 **[Technical note (PDF)](M1plus_Hedonic_Technical_Note.pdf)** – specification, estimation step by step, valuation, leave-one-out validation, limitations and references.

## Model

$$\ln P_i = \beta_0 + \sum_k \beta_k x_{ik} + \varepsilon_i$$

A yes/no feature changes the price by $e^{\beta}-1$; for $\ln(\text{dwt})$, $\beta$ is the % change in price for 1% more deadweight. Coefficients come from $\hat\beta = (X'X)^{-1}X'y$ (checked by hand against the library), with robust (HC1) standard errors. Prices are taken back from logs with Duan's smearing factor.

| | Sales | Market level | Purpose |
|---|---:|---|---|
| Model A | 297 tankers and bulkers | ship type × quarter | Measure the feature effects |
| Model B | 45 MR tankers | quarter | Check on the target's own segment |

## What moves the price (model A)

![Feature effects](figures/hedonic_effects.png)

| Feature | Effect on price | Reliable |
|---|---:|:---:|
| Built in Japan (vs China) | +21.5% | Yes |
| Built in Korea (vs China) | +16.9% | Yes |
| Scrubber fitted | +8.9% | Yes |
| Special survey due within 12 months | −4.8% | Weak |
| 1% more deadweight (tankers, total) | +0.58% | Yes |
| Value lost per year of age (tankers, total) | 7.5% | Yes |

Tankers have their own age and size slopes in model A, so the tanker rows are totals: base slope + tanker extra, with the standard error from both. In model B (MR only) the size effect comes out **negative** (−0.33% per 1% DWT, p = 0.33). A bigger ship cannot be worth less, so this number is marked *wrong sign* and not relied on: within the narrow MR band, size barely varies and the data cannot measure it.

## Case: Target Ship 1 (MR product tanker, built 2012 in Korea), 22 May 2026

| | Model A | Model B | M1 age curve |
|---|---:|---:|---:|
| **Value** | **US\$29.22m** | US\$26.29m | US\$29.67m |
| 68% prediction interval (log scale) | 24.63 – 34.68 | 23.68 – 29.20 | 26.78 – 32.87 |
| Reported sale US\$28.45m vs value | −2.6% | +8.2% | −4.1% |
| Published leave-one-out validation: sales tested | 45 MR sales | 45 MR sales | 43 date-adjusted comparables |
| Leave-one-out validation: average miss | 12.3% | 8.7% | 7.5% |
| Leave-one-out validation: bias | +9.6% | +1.1% | +0.8% |

M1 records a 7.5% average absolute percentage error on 43 date-adjusted comparables. Models A and B record 12.3% and 8.7% on 45 MR sales. Because the samples and price treatment differ, these results do not establish which model performs best.

Leave-one-out validation fits the model on all other sales in the collected sample and predicts the omitted sale. Training may include sales reported after the omitted transaction, so this is not a historical forecasting test.

![Leave-one-out validation](figures/hedonic_backtest.png)

## Validation on the same sales

The published leave-one-out errors above use different samples (M1: 43 date-adjusted comparables; M1+: 45 MR sales), so they cannot rank the models. Here **all three models are scored on the same 43 MR sales** (M1's comparables), against the same prices.

- **Leave one sale out:** each sale is predicted by models fitted on all the others.
- **Leave one deal out:** ships sold together in one package (same report, build year, size and price, or flagged en bloc) are held out together, so a sister ship cannot give the answer away. 6 MR package deals cover 13 ships, 11 of them among the 43 test sales.
- **Earlier report weeks only:** each sale is predicted only from sales reported in earlier weeks, with the market benchmark known on its report day. Testing starts once the training data has at least 10 M1 comparables, 20 MR sales and 60 tanker and bulker sales, and the ship's yard country has been seen: 24 of the 43 sales qualify (the first on 2 Mar 2026). A quarter with no earlier sales uses the latest earlier quarter's market level (3 sales).
- **Prices at 22 May:** each reported price is moved to 22 May with M1's broker benchmark; M1+ predicts at the 2026 Q2 market level. **Prices at report date:** M1's prediction is moved back with the same benchmark, so M1's error is the same in both versions by construction.

| Test | Sales | M1 | M1+ A | M1+ B | A − M1 (95% interval) | B − M1 (95% interval) |
|---|---:|---:|---:|---:|---:|---:|
| Leave one sale out, prices at 22 May | 43 | 7.5% (+0.8%) | 8.9% (+5.4%) | 10.3% (−6.5%) | +1.4 (−0.5 to +3.4) | +2.8 (+0.6 to +5.1) |
| Leave one sale out, prices at report date | 43 | 7.5% (+0.8%) | 12.5% (+10.3%) | 8.5% (+1.6%) | +5.0 (+1.7 to +8.4) | +1.1 (−0.9 to +3.1) |
| Leave one deal out, prices at 22 May | 43 | 7.5% (+0.8%) | 9.0% (+5.5%) | 10.5% (−6.6%) | +1.5 (−0.5 to +3.5) | +3.0 (+0.7 to +5.2) |
| Leave one deal out, prices at report date | 43 | 7.5% (+0.8%) | 12.9% (+10.6%) | 9.1% (+1.9%) | +5.4 (+1.9 to +8.9) | +1.6 (−0.5 to +3.8) |
| Earlier report weeks only, prices at report date | 24 | 5.8% (−2.4%) | 8.1% (+4.2%) | 7.1% (−4.9%) | +2.3 (+0.0 to +5.0) | +1.3 (−0.9 to +3.6) |

Each cell: average miss (bias). Differences are in percentage points of average miss; the interval is a paired bootstrap (10,000 resamples of the test sales).

**Reading.** On identical sales, M1 has the lowest average miss in every test. The margin is clear in some comparisons (model A at report-date prices; model B at 22 May prices) and within noise in others (model A at 22 May; model B at report-date prices and in the time-ordered test). Holding out whole deals raises the M1+ errors slightly and barely moves M1's (7.45% to 7.49%). With 43 test sales, and 24 in the time-ordered test, gaps of one or two points are not conclusive. **The evidence supports using M1 for the value and M1+ to explain price differences, but only modestly.**

Tests 1 and 2 for all models, and test 3 for M1+, are reproduced by `examples/run_hedonic.py` from the public files (`m1_sale`, `deal` and `report_week` columns). Test 3 for M1 needs the licensed broker benchmark and is run privately. See [limitations](../limitations.md) for what the data and models cannot show.

**What the coefficients say.** Model A measures what moves prices precisely, but pooling all tankers and bulkers makes it lean high on MR tankers. Model B is unbiased but has too few sales for precise effects. Most M1 comparables are Korean-built, so the Korea premium is already in the curve; Target Ship 1 has a special survey due within a year and sold about 4% below the curve. The estimated survey-due discount is consistent with the target selling below the age curve, but this regression does not establish that survey timing caused the difference. The survey effect is weak (−4.8%, p = 0.08) and not reliable in model B.

## Files

| Path | Contents |
|---|---|
| [`data/sample/hedonic_sales.csv`](../../data/sample/hedonic_sales.csv) | 297 anonymised sales (H001–H297): type, age, size, yard country, features, package deal, quarter, report week, price; link to M1's sale label |
| [`src/shipping_valuation/models/hedonic.py`](../../src/shipping_valuation/models/hedonic.py) | Models A and B, fit, by-hand check, valuation, effects |
| [`src/shipping_valuation/evaluation/backtesting.py`](../../src/shipping_valuation/evaluation/backtesting.py) | Leave-one-out validation (shared with M1) |
| [`examples/run_hedonic.py`](../../examples/run_hedonic.py) | One run, step by step: fit, effects, value term by term, leave-one-out validation, charts |
| [`tests/test_hedonic.py`](../../tests/test_hedonic.py) | Checks the published results, including the same-sales and time-ordered validation |

```bash
python3 examples/run_hedonic.py
python3 -m unittest discover -s tests
```

---

*Author: Yan Li. Data from weekly broker sale-and-purchase reports, anonymised; only sales reported on or before 22 May 2026.*
