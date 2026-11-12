# Hedonic Ship Price Model (M1+)

**Which features drive second-hand ship prices, and by how much.** M1 values a ship from its age alone. M1+ explains the log of the sale price by age, size, yard country, survey timing, scrubber, eco design, en bloc sale and the market level, all at once, by ordinary least squares. It uses only sales reported on or before the valuation date, the same data as M1.

📄 **[Technical note (PDF)](M1plus_Hedonic_Technical_Note.pdf)** – specification, estimation step by step, valuation, back-test, limitations and references.

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
| 1% more deadweight | +0.55% | Yes |
| Value lost per year of age (tankers) | 7.5% | Yes |

## Case: Target Ship 1 (MR product tanker, built 2012 in Korea), 22 May 2026

| | Model A | Model B | M1 age curve |
|---|---:|---:|---:|
| **Value** | **US\$29.22m** | US\$26.29m | US\$29.67m |
| 68% range | 24.63 – 34.68 | 23.68 – 29.20 | 26.78 – 32.87 |
| Reported sale US\$28.45m vs value | −2.6% | +8.2% | −4.1% |
| Back-test on 45 MR sales: average miss | 12.3% | 8.7% | 7.5% |
| Back-test on 45 MR sales: bias | +9.6% | +1.1% | +0.8% |

![Back-test](figures/hedonic_backtest.png)

**Reading.** Model A measures what moves prices precisely, but pooling all tankers and bulkers makes it lean high on MR tankers. Model B is unbiased but has too few sales for precise effects. For valuing an MR tanker the age curve (M1) has the lowest back-test error, so **M1 values and M1+ explains** a ship's position relative to the curve. Most M1 comparables are Korean-built, so the Korea premium is already in the curve; Target Ship 1's survey due within a year is the likely reason it sold about 4% below it.

## Files

| Path | Contents |
|---|---|
| [`data/sample/hedonic_sales.csv`](../data/sample/hedonic_sales.csv) | 297 anonymised sales (H001–H297): type, age, size, yard country, features, quarter, price |
| [`src/vessel_valuation/models/hedonic.py`](../src/vessel_valuation/models/hedonic.py) | Models A and B, fit, by-hand check, valuation, effects |
| [`src/vessel_valuation/analytics/backtest.py`](../src/vessel_valuation/analytics/backtest.py) | Leave-one-out back-test (shared with M1) |
| [`examples/run_hedonic.py`](../examples/run_hedonic.py) | One run, step by step: fit, effects, value term by term, back-test, charts |
| [`tests/test_hedonic.py`](../tests/test_hedonic.py) | Checks the published results |

```bash
python3 examples/run_hedonic.py
python3 -m unittest discover -s tests
```

---

*Author: Yan Li. Data from weekly broker sale-and-purchase reports, anonymised; only sales reported on or before 22 May 2026.*
