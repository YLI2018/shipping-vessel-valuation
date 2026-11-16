# Shipping Vessel Valuation

A Python research project for developing, validating and comparing
vessel valuation methods.

## Project status

Work in progress. Three models are published with their code, anonymised data and tests: the **M1 vessel age curve** and the **M1+ hedonic price model** (with technical notes), and the **M2 discounted cash flow model**.

## Models

| Model | Question it answers | Status |
|---|---|---|
| [M1 Vessel age curve](docs/methodology/m1_age_curve.md) | What is a second-hand ship worth, from recent sales of similar ships? | Published |
| [M1+ Hedonic price model](docs/methodology/m1plus_hedonic.md) | How do size, yard, survey timing and scrubbers move the price beyond age? | Published |
| [M2 Discounted cash flow](docs/methodology/m2_dcf.md) | What is the ship worth from the cash it can earn, and what is a price betting on? | Published |
| Financing and others | What does the owner earn after the loan? | Planned |

## M1 headline result

![Fitted age curve](docs/methodology/figures/age_curve.png)

Target Ship 1, an MR product tanker built in 2012, valued on **22 May 2026** from 43 comparable sales. The dataset is described as containing sales reported on or before 22 May 2026. Report dates are not included in the published CSV, so that cutoff cannot be independently verified from this file.

| Result | Value |
|---|---:|
| **Market value** | **US\$29.67m** (± 1 SD of residuals: US\$26.27m – 33.06m) |
| Value lost per year of age | 8.4% |
| Reported sale price | US\$28.45m: 4.1% below the curve, inside the range |
| Leave-one-out validation, 43 date-adjusted comparables | average miss 7.5%, bias +0.8% |

The Python results agree with an independent Excel implementation of the model to 9 decimal places.

📄 [M1 page](docs/methodology/m1_age_curve.md) · [Technical note (PDF)](docs/methodology/M1_Age_Curve_Technical_Note.pdf)

## M1+ headline result

![Feature effects](docs/methodology/figures/hedonic_effects.png)

Target Ship 1, valued on **22 May 2026**. The dataset is described as containing sales reported on or before 22 May 2026. Report dates are not included in the published CSV, so that cutoff cannot be independently verified from this file.

| Result | Model A: 297 tankers and bulkers | Model B: 45 MR tankers |
|---|---:|---:|
| **Market value** | **US\$29.22m** (68% interval US\$24.63m – 34.68m) | **US\$26.29m** (68% interval US\$23.68m – 29.20m) |
| Reported sale price US\$28.45m vs value | 2.6% below | 8.2% above |
| Leave-one-out validation, 45 MR sales | average miss 12.3%, bias +9.6% | average miss 8.7%, bias +1.1% |

On 297 tanker and bulker sales, ships built in Japan sell for **21.5%** and in Korea for **16.9%** more than Chinese-built ships of the same age and size; a scrubber adds **8.9%**. M1+ values Target Ship 1 at US\$29.22m.

M1 records a 7.5% average absolute percentage error on 43 date-adjusted comparables. Models A and B record 12.3% and 8.7% on 45 MR sales. Because the samples and price treatment differ, these results do not establish which model performs best.

**Same-sales check.** Scored on the same 43 MR sales, M1 has the lowest average miss in every test (M1 7.5%, model A 8.9%, model B 10.3% at 22 May prices; 5.8%, 8.1% and 7.1% when each sale is predicted only from earlier report weeks, 24 sales). Several gaps are within noise, so this supports M1 for the value and M1+ for explanation only modestly. Details: [validation on the same sales](docs/methodology/m1plus_hedonic.md#validation-on-the-same-sales).

Leave-one-out validation fits the model on all other sales in the collected sample and predicts the omitted sale. Training may include sales reported after the omitted transaction, so this is not a historical forecasting test.

📄 [M1+ page](docs/methodology/m1plus_hedonic.md) · [Technical note (PDF)](docs/methodology/M1plus_Hedonic_Technical_Note.pdf)

## M2 headline result

![Value against the long-run TCE](docs/methodology/figures/dcf_longrun_tce.png)

**How to read the chart.** The model assumes the ship earns **$16,000 a day from age 18 until it is scrapped at 25**. Nobody knows if that is right. So the chart asks: *if the ship earns a different amount per day, what is it worth today?* That daily amount, **L**, is the bottom axis; it is the number in the M2 workbook (M2_Valuation_Draft_v5.xlsx, sheet Inputs, cell B14, "Long-run earnings per day (TCE), year 4 onwards"). For each L the model is rerun: the dark line is the ship's worth today, the orange line the price it sells for at age 19. At $16,000 a day the ship is worth $23.12m; it reaches the $28.45m paid at $19,131 a day. Equations and a worked table: [M2 page](docs/methodology/m2_dcf.md#how-to-read-the-sensitivity-chart).

Target Ship 1, valued on **22 May 2026** from the cash it can earn over five years plus its sale at the end, discounted at a 7.30% WACC.

| Result | Value |
|---|---:|
| **DCF value** (sale priced from the earnings left) | **US\$23.12m** |
| DCF value with the sale at today's market (M1 curve) | US\$28.49m |
| Price tested US\$28.45m: forecast IRR (before any loan) | 1.0% a year, against the 7.30% WACC |
| Long-run earnings at which value = price | US\$19,131 a day (model: US\$16,000) |

The long-run earnings assumption sets both the later cash and the sale price, so it is the key input: each US\$1,000 a day moves the value by about US\$1.7m. Year 1 uses the broker 1-year time-charter estimate; year 2 is derived from the 1- and 2-year estimates (the 2-year rate is the average of both years); year 3 is a judgement. They are not FFA prices.

📄 [M2 page](docs/methodology/m2_dcf.md)

## Research standards

- Traceable data and clearly stated assumptions.
- Reproducible calculations and automated tests.
- A valuation uses only data published on or before its date. Leave-one-out validation is not a historical forecasting test; a time-ordered test (each sale predicted only from earlier report weeks) is reported separately and rests on 24 sales.
- Clear explanations of uncertainty and investment relevance: see [limitations](docs/limitations.md).
- Data shared here is anonymised; broker data and ship names are not published.

## Run

```bash
python3 -m pip install -r requirements.txt
python3 examples/run_age_curve.py
python3 examples/run_hedonic.py
python3 examples/run_dcf.py
python3 -m unittest discover -s tests
```

## Structure

- src/shipping_valuation/data/ — Data-processing code.
- src/shipping_valuation/models/ — Valuation models.
- src/shipping_valuation/evaluation/ — Validation and sensitivity analysis.
- src/shipping_valuation/reporting/ — Report and chart generation.
- data/sample/ — Anonymised example data.
- docs/methodology/ — Model methodology: summary pages, technical notes (PDF) and charts.
- docs/limitations.md — What the data and models can and cannot show.
- notebooks/ — Exploratory analysis.
- examples/ — Reproducible demonstrations.
- tests/ — Automated calculation and data checks.

---

*Author: Yan Li. Personal portfolio project.*
