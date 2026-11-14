# Limitations: what the data and models can and cannot show

These apply to M1 (vessel age curve) and M1+ (hedonic price model). They are stated so a reader can judge how far to
rely on each result.

## Data

1. **Short window.** Sales reported 16 Dec 2025 to 22 May 2026, about five months, in a rising MR market. The models
   describe that market, not a full cycle.
2. **Reported prices.** Prices come from weekly broker sale-and-purchase reports. They are reported prices, not
   verified contract prices. Sales with only a range ("low", "region", "excess") are excluded. A few report pages were
   typed in from screenshots.
3. **Report date, not sale date.** The date known is when a sale was reported; the sale date itself is unknown.
4. **Features from report text.** Scrubber and eco design are recorded only when a broker mentions them, so they are
   under-recorded (eco is rare). Survey dates are missing for many sales (handled with a "survey unknown" flag).
5. **Age from build year only.** M1 uses report year minus build year; M1+ assumes a mid-year build date.
6. **Package deals.** 18 deals (40 ships, 6 deals and 13 ships among MR tankers) were sold as packages. Most were priced
   per ship at the same price; in one MR deal the per-ship price is an equal split of the total. For fitting, M1 keeps
   one ship per deal flagged en bloc and keeps the others as separate sales; M1+ keeps every ship with an en bloc flag.
   This is why M1 has 43 MR sales and M1+ has 45. Sister ships at the same price give their deal extra weight.
7. **Related-party sales** are excluded only when identified (one so far).
8. **Information as first recorded.** Later corrections to a sale are not tracked.
9. **Small samples.** M1: 43 comparables. M1+ model B: 45 MR sales. M1+ model A: 297 tanker and bulker sales.
10. **Anonymised public data.** The CSVs carry no ship names or dates, only a report week (week 1 = week starting
    Monday 15 Dec 2025). The 22 May cutoff and the matching between files rest on the private database.

## Models

11. **M1 uses age only.** Log price on age, after moving each price to the valuation date with a broker benchmark for
    the nearest age point (5, 10 or 15 years). The benchmark nearest a sale's report date may be a few days after it.
12. **M1+ model A pools tankers and bulkers.** Yard, scrubber and survey effects are assumed the same for both; tankers
    get their own age and size slopes. It leans high on MR tankers.
13. M1+ model B has a small sample. Most feature estimates are not statistically significant. Its negative size coefficient is statistically uncertain and should not be interpreted as evidence that larger ships are worth less.
14. **Market level by quarter is coarse** in a rising market. A value at 22 May uses the 2026 Q2 level, an average of
    April and May sales.
15. **Associations, not causes.** A regression shows what goes with higher or lower prices. It does not show that a
    feature causes the difference. The survey-due discount is weak (p about 0.08).
16. **Many features are tested at once,** so one significant result may be chance.
17. **Ranges.** M1's range on the front page is ± 1 standard deviation of residuals in dollars (26.27–33.06); the M1+
    page shows 68% prediction intervals on the log scale (M1: 26.78–32.87). Both assume past misses describe the next sale.

## Validation

18. **Leave-one-out validation is within the collected sample.** Training may include sales reported after the held-out
    sale, so on its own it is not a historical forecasting test.
19. **Same-sales comparison.** On M1's 43 sales, M1 has the lowest average miss in every test, but several gaps are
    within the bootstrap interval. Gaps of one or two points are not conclusive with 43 sales.
20. **Package deals in validation.** Holding out whole deals (rather than one ship) removes help from sister ships. It
    raises the M1+ errors slightly and barely moves M1's.
21. **Time-ordered test.** Only 24 of 43 sales can be tested (the earliest have too little earlier data); 3 of them
    use the previous quarter's market level. The result rests on few sales and on the minimum-data rule.
22. **M1's error is the same at 22 May and at report-date prices** by construction (the same benchmark moves both its
    price and its prediction).

## M2 discounted cash flow

23. **No FFA curve.** Earnings for years 1–3 use one broker's weekly time-charter estimates (13 May 2026) as a stand-in
    for forward freight agreement (FFA) prices, which need a paid subscription. Year 2 ($19,000) is derived from the 1-
    and 2-year estimates, assuming the 2-year rate is the average of both years; this is approximate, and owners often
    accept a lower rate for a longer charter, so year 2 may be understated. Year 3 ($17,500) is a judgement.
24. **Long-run earnings are a judgement and drive the value twice.** The long-run TCE ($16,000 a day, one listed
    owner's 2015–25 median) sets the earnings from year 4 and the earnings-based sale price. Each $1,000 a day moves the
    value by about $1.7m; the price is matched at $19,131.
25. **Sale price basis.** The default prices the sale from the earnings left; the alternative (M1 curve at the exit
    age) assumes today's high ship prices last and adds $5.37m. Both are reported.
26. **Discount rate.** The beta is a sector figure from eight US firms (Damodaran, Shipbuilding & Marine), not tanker
    owners; the debt share (18%) is far below a typical ship loan (50–65%). At 60% debt (beta 0.75 → 0.61 without debt → 1.53,
    no tax both ways) the value falls $0.34m. The 50–65% bank lending range has no dated source yet.
27. **Nominal and flat figures mixed.** Opex grows 3.3% a year while TCE, the sale price and scrap are flat, which
    leans the value low.
28. **Gross hire.** Address and brokerage commission (1.25–5%) is not deducted: 2.5% off the hire in every year to age 25 (the sale price included) would lower the value by $1.19m.
29. **Charter quotes describe a standard MR.** The case ship is 14 years old and non-eco and may earn less; EU carbon
    cost is assumed to be carried by the charterer.
30. **The implied TCE holds the sale value fixed** (it changes earnings in the holding years only), so it understates
    how much earnings matter. Every change in the M2 page's sensitivity table recalculates the sale price; the long-run
    TCE chart shows the full effect.

## Use

31. **Portfolio exercise.** The values are model estimates from public broker reports. They do not use inspection,
    condition, class or charter records and are not investment advice.
