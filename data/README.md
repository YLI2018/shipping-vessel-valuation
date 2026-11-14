# Sample data

Anonymised data used by the published models. Only sales reported on or before the valuation date of 22 May 2026 are included. Ship names, dates, buyers, sellers and broker details are not published.

- **Report week:** week 1 is the week starting Monday 15 Dec 2025; week 23 contains 22 May 2026. It lets anyone rerun the time-ordered validation without real dates.
- **Deal:** D01, D02, … mark ships sold together in one package (same report, build year, size and price, or flagged en bloc); blank for single sales. Validation holds out a whole deal at once.

- `comparables.csv`: the 43 MR tanker sales used by the M1 age curve (Sale 01–43): age at sale, price adjusted to 22 May 2026 (US$m), report week, package deal.
- `dcf_inputs.json`: M2 inputs for Target Ship 1 on 22 May 2026, each with its source (charter estimates, listed-owner earnings and costs, rates, beta, scrap).
- `hedonic_sales.csv`: the 297 tanker and bulker sales used by M1+ (H001–H297): segment, type, age (years), deadweight, yard country, survey due within 12 months, survey date unknown, scrubber, eco, en bloc, package deal, quarter of the report, report week, reported price (US$m); `m1_sale` links a row to its M1 sale label (43 rows).
