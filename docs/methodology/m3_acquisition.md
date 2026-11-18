# M3 Acquisition and finance

**Question.** Is buying Target Ship 1 at US\$28.45m good for the owners, can it be funded with a bank loan, and what is the most we should pay?

M2 asks what the ship is worth. M3 starts from the same ship cash and the same sale price, and adds the price paid, the loan and the owners' cash. Code: `src/shipping_valuation/models/acquisition.py`; inputs: `data/sample/acquisition_inputs.json` plus M2's `dcf_inputs.json`; demo: `examples/run_acquisition.py`. The code reproduces the workbook's **yearly** model (owners' cash, returns, bank tests, maximum bid, Table A) and agrees with the M3 Excel workbook (v3, recalculated in Excel) to at least 3 decimal places; the workbook's monthly cash budget, carbon module and sale-and-leaseback are not reproduced.

## Terms

| Term | Meaning | Value |
|---|---|---|
| Equity | The owners' own money, paid in on day 1 and paid last | US\$12.69m |
| WACC | Return lenders and owners together require; compared with the ship's own return | 7.30% (M2) |
| Cost of equity | Return the owners require at a 60% loan (CAPM) | 11.05% |
| Forecast IRR | Return the forecast cash gives at the price paid | equity −8.0%, project 0.7% |
| Debt service cover | Ship cash ÷ (interest + scheduled repayment) | lowest 1.14× |
| Headroom | How far the ship's value is above the bank's minimum (130% of what we owe) | 33.7% |

## Method

1. **Loan.** 60% × the lower of price and value today (M1 curve: US\$29.67m) = US\$17.07m. Repaid US\$1.707m a year (10-year profile); the 50% balloon is repaid from the sale. Interest at SOFR 3.55% + margin 1.80% = 5.35%; fee 1%.
2. **Owners' cash.** Day 1: −28.45 × 1.005 − 1.0 working capital + 17.07 − 0.17 fee = −12.693. Each year: ship cash (as M2) − interest − repayment. Year 5 also: + sale 11.375 (after 1% commission) + 1.0 working capital − balloon 8.535.
3. **Cost of equity.** Beta 0.75 (M2) without debt: 0.75 × (1 − 0.184) = 0.61; at our 60% loan: 0.61 ÷ 0.4 = 1.53; 4.56% + 1.53 × 4.24% = 11.05% (no tax both ways).
4. **Bank tests.** Value rule: ship value ≥ 130% of what we owe, every year. Debt service cover ≥ 1.20× every year (the balloon is excluded). Both minimums are assumptions, subject to confirmation.
5. **Maximum bid.** The deal is repeated at 41 prices (US\$18m–38m). Return bid: the price where the owners' NPV at 11.05% is zero, so the equity IRR equals 11.05% exactly. Value-rule bid and debt-service bid: highest grid price passing each test every year; a test that passes at US\$38m means no limit was found inside the grid. **Maximum bid = the lowest of the three**, then the whole deal is re-run at that price and all three tests are checked again. Monthly liquidity is tested separately in the workbook and is not part of the bid.
6. **No loan left.** In a year with no loan (no borrowing, or a loan repaid early) the debt service cover and the headroom are *not applicable*; the owners' cash and returns are still calculated.

## Results

| Year | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|---:|
| Owners' cash (US\$m) | −12.693 | 2.836 | 1.425 | 0.880 | 0.332 | 4.162 |
| Debt service cover | | 2.08 | 1.56 | 1.36 | 1.14 | 1.14 |

| Result | Value |
|---|---:|
| Equity IRR (cost of equity 11.05%) | **−8.0%** |
| Equity NPV at 11.05% | −US\$5.66m |
| Money multiple | 0.76× |
| Project IRR, no loan (WACC 7.30%) | 0.7% |
| Debt service cover below 1.20× | years 4 and 5 (lowest 1.14×) |
| Value-rule headroom / value can fall | 33.7% / 25.2% |
| Bids: return / value rule / debt service | US\$22.21m / no limit found up to US\$38m / US\$27.0m |
| **Maximum bid** | **US\$22.21m**, limited by the required return; US\$6.24m below the price tested; re-test passes all three tests |

**Why the deal fails.** The ship on its own earns 0.7% a year against the 7.30% WACC. The loan costs 5.35% plus fee, more than the ship earns, so borrowing turns 0.7% into −8.0% for the owners. Hire falls from US\$30,000 a day in year 1 to US\$16,000 from year 4, and the ship sells for US\$11.4m after five years against US\$28.45m paid. This is a result, not a model error.

## Sensitivities

Equity IRR, hire change in every year owned (rows) × sale value change (columns). Middle box = base case. n/a: no IRR exists – in the sale year the owners must pay money in, because the sale does not cover the loan still owed, so no rate makes the NPV zero (the NPV and the money multiple still apply).

| Hire change | −40% | −20% | 0 | +20% | +40% |
|---|---:|---:|---:|---:|---:|
| −US\$4,000/day | n/a | −67.6% | −30.7% | −19.2% | −11.9% |
| −US\$2,000/day | n/a | −34.0% | −18.5% | −10.2% | −4.3% |
| 0 | n/a | −17.4% | **−8.0%** | −1.8% | 3.0% |
| +US\$2,000/day | −15.7% | −5.3% | 1.2% | 6.1% | 10.1% |
| +US\$4,000/day | −1.7% | 4.9% | 9.7% | 13.6% | 17.0% |

The equity IRR reaches the 11.05% cost of equity only with hire about US\$4,000 a day higher and a sale value at least 20% higher. The 1.20× debt service cover holds at base hire only if the interest rate falls by more than 1 point.

## Limitations

- Loan-to-value, repayment profile, fee, the 130% value rule, the 1.20× cover and the transaction costs are assumptions for this deal, not sourced terms.
- Earnings and the sale price are M2's single forecast; the long-run US\$16,000 a day drives most of the result.
- SOFR is held flat; no tax; US dollars only.
- The workbook also has a sale-and-leaseback comparison and a monthly cash budget; their terms are placeholders and are not reproduced here.

## IRR calculation

The IRR is the rate at which the NPV of the cash flows is zero. With x = 1/(1 + r) the NPV is a polynomial in x, so every IRR is found as a root of that polynomial (then polished). One root: that is the IRR (for example −1 then +4 gives 300%; −100, +200, −100 gives 0%, where the NPV only touches zero). No root: *no IRR exists*. Several roots (cash flows that change sign more than once, for example −100, +230, −132 has IRRs of 10% and 20%): the IRR is reported as *needs further analysis* and the NPV and the money multiple are used instead.

## Input checks

Before calculating, the code checks every input against the same allowed ranges as the workbook (for example loan-to-value 0–90%, repayment profile at least 1 year, holding period a whole number of 1–10 years that ends by the 25-year economic life, a price-grid step above 0) and stops with a message naming each input that is out of range.
