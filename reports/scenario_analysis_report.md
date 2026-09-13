# Phase 12 — Scenario Analysis Report

Four scenarios computed from the same verified FY2025 baseline used in Phase 11's `excel/business_model.xlsx` (Current, Retention +5pp, Discount -2pp, Marketing +25%), per spec sections 21-22. All figures below are computed by `python/scenarios/run_scenarios.py`, not typed in by hand — re-running it reproduces every number here.

## Data Integrity Check (found during this phase)

- Real FY2025 order count, verified two independent ways (distinct `order_id` in `orders.csv` filtered to 2025, and the sum of `orders` across the 12 rows of `kpi_revenue_by_month.csv` for 2025): **36,459**.
- The Assumptions sheet's 'Total Orders (FY2025)' cell says **30,895** — this does not match and looks like a Phase 11 filter bug. It does not propagate into any Financial Model output (Total Orders isn't referenced by any formula there), and this phase's scenarios use the verified figure directly from source data, not the stale cell. Recommend correcting that cell in Phase 11's workbook for consistency, but it does not change any reported result to date.
- FY2025 revenue splits by first-vs-repeat order: new-order revenue = Rs 103,616,736.45, repeat-order revenue = Rs 264,308,263.33. These reconcile exactly to Gross Revenue (Rs 367,924,999.78).

## Methodology per Scenario

**Current (Baseline)**

No change. Baseline FY2025 run-rate, as verified in Phase 11.

**Retention Improvement (+5pp)**

Average Monthly Retention Rate +5 percentage points (12.4% -> 17.4%), the fixed lever from spec section 22. Retention governs REPEAT purchasing, not first-time acquisition, so the uplift is applied only to FY2025 revenue from orders that were NOT a customer's first-ever order (computed directly from orders_enriched.csv + full order history: repeat-order revenue = Rs 264,308,263 of the Rs 367,924,999.78 FY2025 total; new-order revenue = Rs 103,616,736, held fixed). The uplift factor is the direct ratio of new to old retention (17.4/12.4 = 1.4032x) applied to that repeat-revenue base. Variable costs (COGS, shipping, operational, returns) scale with the resulting revenue growth ratio, since higher repeat volume drives proportionally more units shipped and handled. Marketing spend is held fixed (this scenario is not a marketing lever).

**Discount Reduction (-2pp)**

Discount Rate -2 percentage points (13.44% -> 11.44%), the fixed lever from spec section 22. Gross Revenue in this dataset is already net of discount (i.e. what the customer actually paid), so the pre-discount list value is backed out as gross_revenue / (1 - discount_rate), then re-applied at the lower discount rate to get the new realized revenue at the SAME order volume. COGS, shipping, operational cost and returns are held at their baseline absolute values, because these are driven by units sold and cost-of-goods, not by the price/discount charged to the customer -- reducing a discount does not change what a unit costs to source or ship. Marketing spend unchanged. Caveat stated in the report: this does not model any secondary effect discount changes might have on order volume or on the discount<->return correlation Phase 08 found -- doing so would require a price-elasticity estimate this dataset cannot support without inventing one.

**Marketing Increase**

The spec (section 22) only says 'Increase marketing investment' with no fixed percentage, unlike the other two levers. This scenario assumes a +25% increase in Marketing Spend (Rs 6,536,583 -> Rs 8,170,729), applied with a documented DIMINISHING-RETURNS elasticity of 0.7 on customers acquired (new_acquired = old_acquired * (1.25)^0.7), rather than assuming naive 1:1 linear scaling -- real-world marketing spend does not convert to new customers at a constant rate, and assuming it does would silently inflate this scenario's ROI. Revenue per acquired customer is held at the FY2025 baseline (Rs 47,847,409 / 5,885 = Rs 8,131.94/customer). The resulting incremental acquired-customer revenue is added to the FY2025 baseline; incremental variable costs (COGS, shipping, operational, returns) scale with that incremental revenue at the baseline blended variable-cost ratio.

## Comparison Table

| Metric | Current | Retention +5pp | Discount -2pp | Marketing +25% |
|---|---|---|---|---|
| Gross Revenue | Rs 367,925,000 | Rs 474,500,912 | Rs 376,426,040 | Rs 376,014,110 |
| Gross Profit | Rs 108,423,744 | Rs 139,830,578 | Rs 116,924,783 | Rs 110,807,522 |
| Gross Margin % | 29.47% | 29.47% | 31.06% | 29.47% |
| Net Profit | Rs 40,691,374 | Rs 54,371,778 | Rs 49,192,414 | Rs 40,095,571 |
| Net Margin % | 11.06% | 11.46% | 13.07% | 10.66% |
| CAC | Rs 1,110.72 | Rs 1,110.72 | Rs 1,110.72 | Rs 1,187.62 |
| Marketing ROI % | 632.0% | 632.0% | 632.0% | 584.6% |
| **Incremental Value vs Current** | **Rs 0** | **Rs 13,680,404** | **Rs 8,501,040** | **Rs -595,803** |

## What the Numbers Show

- **Retention improvement is the strongest lever**: +5pp retention is worth an estimated **Rs 13,680,404** in incremental annual net profit — directly because retention drives repeat-order revenue, and repeat orders are already 72% of FY2025 revenue. This is consistent with Phase 07/08's finding that repeat-purchase decline is the core problem, not a demand-side one.

- **Discount reduction is the second-strongest lever**: cutting discount rate by 2pp is worth **Rs 8,501,040** in incremental profit at the SAME order volume, since it's pure margin recovery. This assumes volume holds — Phase 08 found discount tier materially affects margin, but did not establish that lower discounts reduce volume, so this is presented as an upper-bound estimate, not a volume-adjusted one.

- **Marketing increase is close to break-even** (a modeled **Rs -595,803** change) once diminishing acquisition returns are assumed rather than linear scaling. This matches Phase 08's statistical finding that marketing spend did not significantly predict performance at this sample size — spending more without fixing retention or regional execution is not shown to pay for itself here.

- Ranked by incremental value: Retention +5pp (Rs 13,680,404) > Discount -2pp (Rs 8,501,040) > Marketing +25% (Rs -595,803). This ranking is an input to Phase 14's prioritized recommendations, not the recommendations themselves — Phase 14 will also weigh implementation cost, risk, and confidence, which this phase does not quantify.

## Assumptions Requiring Explicit Caveat

- Retention and discount scenarios hold everything else constant (no cross-effects modeled between levers — e.g. a discount cut could itself affect retention, and vice versa).
- The marketing elasticity (0.7) and spend increase (+25%) are reasonable planning assumptions, not statistically fitted values — the dataset does not have enough campaign-level variation (per Phase 08) to fit a real elasticity curve.
- All scenarios are static, single-year projections, not multi-year compounding models.


Outputs: `data/processed/scenario_comparison.csv`, `excel/business_model.xlsx` (new 'Scenario Comparison' sheet), this report.

Next: **Phase 13 — Business Diagnosis** (combine all analytical outputs from Phases 07-12 into the 'why is performance changing' narrative).