# Shipping Vessel Valuation

A Python research project for developing, validating and comparing
vessel valuation methods.

## Project status

Work in progress. Two models are published with their code, anonymised data, tests and technical notes: the **M1 vessel age curve** and the **M1+ hedonic price model**.

## Models

| Model | Question it answers | Status |
|---|---|---|
| [M1 Vessel age curve](docs/methodology/m1_age_curve.md) | What is a second-hand ship worth, from recent sales of similar ships? | Published |
| [M1+ Hedonic price model](docs/methodology/m1plus_hedonic.md) | How do size, yard, survey timing and scrubbers move the price beyond age? | Published |
| Discounted cash flow and others | What is the ship worth from the cash it can earn? | Planned |

## M1 headline result

![Fitted age curve](docs/methodology/figures/age_curve.png)

Target Ship 1, an MR product tanker built in 2012, valued on **22 May 2026** using only the 43 comparable sales reported on or before that date:

| Result | Value |
|---|---:|
| **Market value** | **US\$29.67m** (range US\$26.27m – 33.06m) |
| Value lost per year of age | 8.4% |
| Reported sale price | US\$28.45m: 4.1% below the curve, inside the range |
| Leave-one-out back-test | average miss 7.5%, bias +0.8% |

The Python results agree with an independent Excel implementation of the model to 9 decimal places.

📄 [M1 page](docs/methodology/m1_age_curve.md) · [Technical note (PDF)](docs/methodology/M1_Age_Curve_Technical_Note.pdf)

## M1+ headline result

On 297 tanker and bulker sales, ships built in Japan sell for **21.5%** and in Korea for **16.9%** more than Chinese-built ships of the same age and size; a scrubber adds **8.9%**. M1+ values Target Ship 1 at US\$29.22m, but its back-test on MR tankers (average miss 12.3%) is weaker than the age curve's (7.5%): **M1 values, M1+ explains.**

📄 [M1+ page](docs/methodology/m1plus_hedonic.md) · [Technical note (PDF)](docs/methodology/M1plus_Hedonic_Technical_Note.pdf)

## Research standards

- Traceable data and clearly stated assumptions.
- Reproducible calculations and automated tests.
- Validation that respects information availability: a valuation uses only data published on or before its date.
- Clear explanations of uncertainty and investment relevance.
- Data shared here is anonymised; broker data and ship names are not published.

## Run

```bash
python3 -m pip install -r requirements.txt
python3 examples/run_age_curve.py
python3 examples/run_hedonic.py
python3 -m unittest discover -s tests
```

## Structure

- src/shipping_valuation/data/ — Data-processing code.
- src/shipping_valuation/models/ — Valuation models.
- src/shipping_valuation/evaluation/ — Validation and sensitivity analysis.
- src/shipping_valuation/reporting/ — Report and chart generation.
- data/sample/ — Anonymised example data.
- docs/methodology/ — Model methodology: summary pages, technical notes (PDF) and charts.
- notebooks/ — Exploratory analysis.
- examples/ — Reproducible demonstrations.
- tests/ — Automated calculation and data checks.

---

*Author: Yan Li. Personal portfolio project.*
