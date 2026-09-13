# MarketLens

**AI-Powered Business Growth & Decision Intelligence Platform**

> Status: 🚧 In active build — Phase 05 (Data Extraction) complete.
> This README is a working skeleton and will be fully expanded in Phase 20.

## What is MarketLens?

MarketLens is a consulting-style analytics platform built around a fictional
multi-location retail/e-commerce company. It answers:

- Why is business performance changing?
- What is causing it?
- What should management do?
- How much could each decision be worth?

## Tech Stack

| Area | Technology |
|---|---|
| Programming | Python |
| Statistical analysis | R |
| Database | PostgreSQL |
| Data processing | Pandas |
| Statistical/ML | Scikit-learn |
| Dashboard | Streamlit + Plotly |
| Financial model | Excel (.xlsx) |
| External data | Public APIs / research |
| LLM | OpenAI / Gemini |
| Testing | Pytest |
| Docs | Markdown |
| Version control | Git/GitHub |

## Project Structure

```
MarketLens/
├── data/           raw / processed / external data
├── sql/            schema, data quality checks, business queries
├── python/         ingestion, validation, analytics, modeling, scenarios
├── R/              statistical analysis, validation
├── excel/          financial model
├── dashboard/      Streamlit app
├── research/       industry & competitor analysis
├── reports/        executive report, methodology
├── presentation/   client deck
├── tests/          pytest suite
├── requirements.txt
└── .env.example
```

## Build Progress (Frozen Phase Order)

- [x] Phase 01 — Project Setup
- [x] Phase 02 — Business & Data Design
- [x] Phase 03 — Dataset Creation
- [x] Phase 04 — PostgreSQL + SQL
- [x] Phase 05 — Data Extraction
- [x] Phase 06 — Data Quality & Validation
- [x] Phase 07 — Business Analytics
- [x] Phase 08 — R Statistical Analysis
- [x] Phase 09 — Predictive Modeling
- [x] Phase 10 — External Market Intelligence
- [x] Phase 11 — Financial Model
- [x] Phase 12 — Scenario Analysis
- [x] Phase 13 — Business Diagnosis
- [x] Phase 14 — Recommendations & Impact
- [x] Phase 15 — AI Business Analyst
- [x] Phase 16 — Streamlit Dashboard
- [x] Phase 17 — Testing
- [ ] Phase 18 — Executive Report
- [ ] Phase 19 — Client Presentation
- [ ] Phase 20 — README + GitHub
- [ ] Phase 21 — Complete End-to-End Test

## The Business Case (Phase 02)

MarketLens models a fictional company, **UrbanCart Retail Group**
(multi-location retail/e-commerce, 5 regions, 18 stores + online channel).
The client problem: revenue growth slowing, margins declining, repeat
purchases falling, and specific regions underperforming.

- Full business case: [`research/business_case.md`](research/business_case.md)
- Full data model & relationships: [`research/data_model.md`](research/data_model.md)

## The Dataset (Phase 03)

Run `python/ingestion/generate_dataset.py` to (re)generate the full
synthetic dataset into `data/raw/`. It's seeded (`np.random.default_rng(42)`)
so it's fully reproducible.

| Table | Rows |
|---|---|
| customers | 45,000 |
| orders | 82,800 |
| order_items | 206,497 |
| returns | 12,333 (6.0% of items) |
| marketing_campaigns | 75 |
| products | 150 |
| stores | 18 |
| regions | 5 |

The data has real, discoverable business patterns baked in (not asserted
anywhere else): decelerating company-wide revenue growth, a South region in
outright decline, rising discount rates, rising return rates, and declining
month-over-month customer retention. See
[`research/data_dictionary.md`](research/data_dictionary.md) for full field
definitions and the verified ground-truth patterns.

## Database (Phase 04)

`sql/schema.sql` defines the full PostgreSQL schema (9 tables, FKs, CHECK
constraints enforcing business rules like "discount ≤ order value" and
"customers_converted ≤ customers_targeted", plus indexes).

To load the generated dataset into your own PostgreSQL instance:

```bash
cp .env.example .env         # fill in your DB credentials
python python/ingestion/load_to_postgres.py
```

This applies `schema.sql`, bulk-loads every `data/raw/*.csv` via `COPY` (fast,
not row-by-row), and runs a smoke-test query. The loader's logic (including
resolving `customers.region_name` → `region_id`) was verified against the
actual generated data using a local SQLite proxy before being finalized —
row counts and the smoke-test result matched exactly:

```
region    total_revenue
North     ₹289,678,811
East      ₹180,647,264
Central   ₹153,314,892
South     ₹117,583,768
West      ₹115,944,204
```

## Data Extraction Layer (Phase 05)

`python/ingestion/extract.py` implements
`SOURCE → READ → STANDARDIZE → COMBINE → VALIDATE → ANALYTICAL DATA`, and
supports two interchangeable sources with identical downstream logic:

- `source="csv"` — reads `data/raw/*.csv` directly (what actually runs in
  this build environment, no live DB needed)
- `source="postgres"` — reads from the PostgreSQL database loaded in
  Phase 04 (the production path once you have a live DB)

Run it:

```bash
python python/ingestion/extract.py
```

Output, written to `data/processed/`:

| File | Grain | Use |
|---|---|---|
| `order_items_enriched.csv` | 1 row per line item (206,497 rows) | product/category-level analysis |
| `orders_enriched.csv` | 1 row per order (82,800 rows) | revenue, margin, customer, marketing KPIs |

Validated on the actual generated data: row counts are preserved through
every join (no fan-out, no silent drops), and total revenue reconciles
exactly (₹857,168,939.70) across the raw item grain, enriched item grain,
and aggregated order grain.

External public-API extraction is architecturally stubbed
(`fetch_external_indicator()`) but not invoked here (no outbound network in
this sandbox). Qualitative external research (industry/competitor) is
handled separately in Phase 10 as markdown documents.

## Setup

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # then fill in your DB + LLM credentials
```

A PostgreSQL server is required for the SQL layer (Phase 04 onward). Any
local install or Docker instance works — connection settings go in `.env`.

## Note on this build environment

This project is being built inside a sandboxed environment without a live
PostgreSQL server or outbound network access. SQL scripts are written to be
correct and runnable against **your** PostgreSQL instance; they are not
executed live inside this sandbox. Python/pandas/scikit-learn work runs and
is verified directly.

## Phase 06 — Data Quality & Validation

Two parallel implementations of the same checks, per the frozen stack:

- `python/validation/data_quality.py` — runs against `data/raw/*.csv` +
  `data/processed/*.csv` directly (what actually executes in this sandbox).
- `sql/data_quality.sql` — the same checks written as pure SQL, for running
  against your live PostgreSQL instance once Phase 04's schema is loaded.

Four categories, matching the project spec exactly:

1. **Missing values** — required fields null-checked per table, plus the
   in-store-order-must-have-a-store rule.
2. **Duplicates** — primary-key duplicates per table, plus a full-row exact
   duplicate scan as a defensive extra.
3. **Invalid values** — negative/zero revenue, non-positive quantity,
   discount exceeding order value, revenue not reconciling to
   `qty × price − discount`, out-of-range/unparseable dates, invalid
   region/channel/category/campaign-type/return-reason enum values, and
   product cost ≥ selling price (impossible margin).
4. **Cross-source integrity** — every FK actually resolves: orders →
   customers, order_items → orders/products, returns/costs → orders,
   customers.region_name → regions, customers.acquisition_campaign_id →
   marketing_campaigns, plus a 1:1 orders↔costs check and an
   orders-must-have-≥1-item check.

A fifth check reconciles Phase 05's enriched outputs
(`data/processed/*.csv`) back against the raw CSVs — same row counts, same
total revenue — confirming the extraction layer didn't silently drop or
duplicate anything.

Run it:

```bash
python python/validation/data_quality.py
```

**Result on the actual generated dataset: PASS — 0 critical issues** across
429,678 rows checked (all 9 raw tables). Full detail, including every
individual check and its live-computed count, is written to
`reports/data_quality_report.md` on every run.

This is deliberately redundant with the CHECK constraints already enforced
at generation time (Phase 03) and at the schema level (Phase 04) — the
point of Phase 06 is to independently *prove* the data survives extraction
clean, rather than assume it because earlier phases said so.

Next: **Phase 07 — Business Analytics** (the Python KPI engine: revenue,
profitability, customer, product, and marketing metrics computed from
`data/processed/*.csv`).

## Phase 07 — Business Analytics

`python/analytics/` — the Python KPI engine, one module per KPI family:

- `data_loader.py` — shared loaders for `data/processed/*.csv` and
  `data/raw/*.csv`
- `revenue.py` — total revenue, MoM/YoY growth, revenue by region/category/
  channel/segment, and a region×year trend table
- `profitability.py` — gross profit/margin, contribution margin, cost per
  order, discount impact, return impact, margin trend by year
- `customer_features.py` — **Section 12**: builds the per-customer feature
  table (`total_orders`, `average_order_value`, `days_since_last_purchase`,
  `purchase_frequency`, `return_rate`, `discount_usage`,
  `customer_lifetime_value`) plus a derived `customer_segment`
  (New / Regular / Loyal / At-Risk / Churned / Never Purchased) — this table
  is the direct input to Phase 09's churn model
- `customer_analytics.py` — acquisition, repeat-purchase rate, churn rate
  (descriptive), month-over-month retention curve, revenue-at-risk
- `product_analytics.py` — best sellers, low-margin products, high-growth
  / declining products (YoY), category performance
- `marketing_analytics.py` — campaign-level and campaign-type ROI, CAC,
  conversion rate, revenue attribution
- `run_analytics.py` — orchestrates all of the above, writes every KPI
  table to `data/processed/kpi_*.csv` and `customer_features.csv`, and
  generates `reports/business_analytics_report.md`

Run it:

```bash
python python/analytics/run_analytics.py
```

**Key verified findings** (computed live from the actual dataset, not
asserted):

- Total gross revenue ₹857.2M across 82,800 orders; revenue growth
  decelerated from **+97.8% (2023→2024) to +13.2% (2024→2025)**.
- **South region revenue fell -24.7%** in 2025 while North grew +31.3% —
  region-level decline is real and isolated, not a company-wide slowdown.
- **Gross margin compressed from 34.3% (2023) to 29.5% (2025)**, tracking
  a **discount rate that rose from 7.0% to 13.4%** and a **return rate that
  rose from 5.2% to 7.2%**.
- **Month-over-month customer retention fell from ~18% to ~12%** over the
  3 years — confirms Phase 03's embedded "repeat purchases falling" signal
  independently, from the real order data.
- Of 45,000 signed-up customers, only 65.2% ever placed an order; of those,
  58% are now "Churned" (no purchase in >180 days) and hold **71.2% of all
  historical customer value (₹571.6M CLV)** — retention, not acquisition,
  is where the money is.
- Electronics Accessories is the highest-revenue-per-unit category but the
  **lowest margin (19.98%)** — a mix-shift risk if it keeps growing share.

**Methodology note on marketing ROI:** campaign ROI here is *lifetime
revenue attributed to the acquiring campaign, to date, vs. that campaign's
one-time spend* — not a per-period return. This means older campaigns show
structurally higher ROI simply because their acquired customers have had
more time to purchase (visible in the report: the two most recent campaigns,
Nov/Dec 2025, show the lowest ROI in the dataset). This is flagged here so
it isn't mistaken for those campaigns actually underperforming.

## Phase 08 — R Statistical Analysis

`R/statistics/` — formal statistical tests (not just descriptive KPIs) in
R, using **only base R's built-in `stats` package** (no CRAN installs
required, matching the project's dependency-light approach):

- `utils.R` — shared data loaders; builds the order-level margin table
  (COGS via `quantity × product.cost`, aggregated to order grain — same
  definition Phase 07's `profitability.py` uses)
- `01_trend_tests.R` — linear regression to test whether the retention
  decline is statistically real; quadratic regression on log(monthly
  revenue) to test whether growth is actually *decelerating*, not just
  slower-but-still-accelerating
- `02_correlation_tests.R` — Pearson + Spearman correlations: discount
  rate ↔ margin, return_rate ↔ CLV, discount_usage ↔ CLV, marketing
  spend ↔ attributed revenue
- `03_group_difference_tests.R` — ANOVA + Kruskal-Wallis (regions,
  campaign types, customer segments), Welch's t-test + Mann-Whitney U
  (high- vs low-discount order margins)
- `run_statistics.R` — orchestrates all of the above, writes
  `reports/statistical_analysis_report.md`

`R/validation/cross_check_kpis.R` — an independent QA layer: recomputes
the headline revenue/margin KPIs straight from `data/raw/*.csv` in R,
without touching any Python code, and checks them against Phase 07's
Python output. Writes `reports/r_cross_validation.md`. Two independent
language implementations agreeing is stronger evidence than one.

Run it (from the project root, on a machine with R installed):

```bash
Rscript R/statistics/run_statistics.R
Rscript R/validation/cross_check_kpis.R
```

**Key verified findings** (statistically tested, not just eyeballed off a
trend line):

- **Retention decline is real, not noise:** slope = -0.148 pp/month,
  R² = 0.76, p = 9.5e-12.
- **Revenue growth is genuinely decelerating:** significant negative
  curvature in log-revenue over time, p = 6.7e-11.
- **Discounting materially erodes margin:** high-discount orders average
  28.9% margin vs. 35.6% for low-discount orders, p < 0.001.
- **South's problem is volume, not pricing:** regional margin differences
  are statistically significant but tiny (~0.6pp), and South actually has
  the *highest* per-order margin of any region — its revenue decline
  (Phase 07) is a demand/volume problem, not a discounting or cost
  problem. This directly sharpens the Phase 13 diagnosis.
- **Return rate alone is a weak/misleading churn signal:** it correlates
  *negatively* with CLV under Pearson but *positively* under Spearman —
  the relationship is confounded by purchase volume (customers who buy
  more also return more in absolute terms).
- **Marketing spend doesn't predict attributed revenue** (p = 0.25) and
  **campaign type doesn't predict performance** (p = 0.16–0.87) at the
  current sample size (75 campaigns) — descriptive-looking winners in
  Phase 07 (e.g. Influencer's higher conversion rate) aren't yet
  statistically defensible reasons to reallocate budget.
- **Customer segments are real, statistically separable behavior
  groups** (p < 0.001 for both CLV and purchase frequency) — this is
  what justifies treating "High Value + High Risk" as a genuine priority
  segment later in the project, not an arbitrary label.

**Note on this build environment:** this sandbox has no R interpreter and
no internet access to install one (the same constraint hit PostgreSQL in
Phase 04 and Faker in Phase 03). Every test above was run and verified in
Python (`scipy.stats`) on the identical CSVs first — same formulas, same
data — to confirm the numbers are real. The R scripts implement the exact
same logic in base R and will reproduce these results when run for real
via `Rscript`.

## Phase 09 — Predictive Churn Model

`python/modeling/`:

- `churn_features.py` — **the important part of this phase.** Phase 07's
  `customer_features.csv` computes `days_since_last_purchase` as of the
  *end* of the dataset, so using it directly as both a model input and a
  churn label would be leakage (the label would already be baked into
  the features). This module instead builds features from
  `orders_enriched.csv` at an explicit cutoff date, using only orders
  on/before that cutoff:
  - **Training set** — features as of **2025-06-30**, for the 24,427
    customers who'd already purchased by then. Label = did they place
    zero orders in the 90 days *after* that cutoff? Because the cutoff
    is in the dataset's past, real observed outcomes exist to check the
    label against.
  - **Scoring set** — the same feature logic applied as of the dataset's
    latest date (2025-12-27), for all 29,340 customers, with no label —
    this is genuine deployment-style prediction.
- `train_churn_model.py` — Logistic Regression and Random Forest
  (both `class_weight='balanced'`, 80/20 stratified split), compared on
  accuracy/precision/recall/F1/ROC-AUC, best model selected by ROC-AUC,
  then refit on the full training set and applied to the scoring set to
  produce `churn_probability` + `risk_segment` (Low/Medium/High) per
  customer.
- `clv_segments.py` — **Section 16**: combines CLV (median split) with
  churn risk into High/Low Value × High/Low Risk quadrants.
- `run_modeling.py` — orchestrates all of the above, writes
  `reports/churn_model_report.md`.

Run it:

```bash
python python/modeling/run_modeling.py
```

**Key verified findings** (all from real train/test evaluation, not
asserted):

- **Training-set churn rate: 81.3%** (no repeat purchase within 90 days
  of a prior order) — this quantifies, in a single number, the low
  repeat-purchase problem Phase 07/08 already flagged.
- Logistic Regression edged out Random Forest on ROC-AUC (**0.675 vs
  0.668**) and was selected, though the two are close and Random Forest
  actually has higher F1 (0.758 vs 0.719) — reported honestly rather than
  picking whichever number looks better. Discriminative power is modest
  (~0.67 AUC), not excellent: order history and region explain real
  signal but far from all of what drives a customer's next purchase.
- `total_orders` is negatively associated with churn and `region_South`
  is positively associated with churn — both independently consistent
  with Phase 07/08's findings, a good sign the model learned something
  real.
- **₹293.2M of historical customer value (36.5% of the total) sits with
  customers flagged High risk** (13,747 customers, avg churn probability
  72%).
- **Priority segment — High Value + High Risk: 8,674 customers holding
  ₹335.7M (41.8% of all customer value)** who are also likely to churn.
  Under 30% of the customer base, but the single largest share of value
  at stake — this is where retention spend should concentrate first.

Next: **Phase 10 — External Market Intelligence** (industry/competitor
research to compare against these internal findings — is South's
decline company-specific, or a broader market trend?).

## Phase 10 — External Market Intelligence

`research/industry_analysis.md` and `research/competitor_analysis.md`.

UrbanCart itself is fictional, so this phase pulls **real, public,
web-sourced data** about the actual Indian retail/e-commerce market via live
web search, and uses it as a benchmark against UrbanCart's own (synthetic
but internally consistent) Phase 03/07 numbers. This is the section-19
"internal vs external" comparison the spec calls for.

**Industry analysis (`industry_analysis.md`):**
- Market size and growth benchmarks: India retail ~US$1.0–1.1 trillion
  (2025), forecast CAGR ~11.4%–12.8% through the early 2030s; e-commerce
  ~US$53–91B (2024→2029 forecast), ~11.45% CAGR (IMARC, IBEF, Expert Market
  Research, BCG/RAI — all sourced and dated).
- Structural trends relevant to UrbanCart's own symptoms: discounting is
  shifting from blanket markdowns to behavior-gated offers because margins
  can't absorb careless discounting anymore; loyalty/retention research
  frames repeat purchase as earned through consistent experience, not
  manufactured by loyalty programs alone; predictive churn modeling is
  becoming a mainstream retailer capability (validates Phase 09's approach
  as on-trend, not speculative).
- **The key comparison**: UrbanCart's company-wide 2024→2025 growth
  (+13%, from Phase 03) is roughly *in line* with the ~11–13% industry CAGR
  — meaning the slowdown is **not a market-wide phenomenon**. It's a mix
  effect: North (+31.25%) and Central (+21.59%) are growing well above
  market, while South (**-24.70%**) and West (-1.26%) are sharply
  underperforming the market and dragging the blended average down. This
  sharpens Phase 13's diagnosis: South/West are company-specific execution
  problems, not a shrinking market.

**Competitor analysis (`competitor_analysis.md`):**
- Real, currently-operating Indian omnichannel retailers in overlapping
  categories (Reliance Retail, DMart, Trent/Zudio, Aditya Birla Fashion &
  Retail, Shoppers Stop, Croma), used as qualitative reference points, not
  matched head-to-head competitors — UrbanCart's revenue scale is a
  synthetic fraction of these real companies' scale, and the report says so
  explicitly.
- What's relevant for later phases: Shoppers Stop's long-established
  loyalty program is a direct contrast to UrbanCart's declining repeat
  purchase rate with no loyalty lever currently modeled; Trent's
  private-label/value-format growth (Zudio) suggests format innovation, not
  just discount depth, drives real-world growth; multiple retailers are
  explicitly expanding into Tier II/III markets as a growth strategy — a
  caveat that South's decline could be execution, not a structurally
  unwinnable local market.

**Honesty note:** all figures in both files are real, retrieved via live web
search on 2026-09-12, with sources and dates listed at the bottom of each
file. Nothing about the external market data is invented; only UrbanCart
itself is fictional.

Next: **Phase 11 — Financial Model** (`excel/business_model.xlsx` — inputs,
outputs, and the scenario-ready structure Phase 12 will drive).

## Phase 11 — Financial Model

`excel/business_model.xlsx` — three sheets:

- **README** — color legend (blue = input, black = formula, green = link to
  another sheet, yellow fill = key assumption/lever) and data basis.
- **Assumptions** — every input from the spec's Section 20 list (Revenue,
  Retention, Discount, Marketing Spend, Conversion, Customer Acquisition,
  Return Rate, Costs), each with a **Source** column pointing to the exact
  file/calculation it came from. All values are UrbanCart's real FY2025
  (Jan–Dec 2025) results pulled straight from `data/raw/*.csv` and
  `data/processed/kpi_*.csv` — the same files Phase 07/08/09's verified
  reports are built from. Nothing is invented.
- **Financial Model** — the spec's Section 20 Outputs (Revenue, Gross
  Profit, Margin, CAC, ROI, Expected Profit, Incremental Value), computed
  with **live formulas** linked back to Assumptions, not hardcoded numbers
  — change an input cell and every output recalculates.

**Verified current-state (FY2025) results:**

| Metric | Value |
|---|---:|
| Gross Revenue | ₹367,924,999.78 |
| COGS | ₹259,501,256.23 |
| Gross Profit | ₹108,423,743.55 |
| Gross Margin | 29.47% |
| Total Operating Costs (shipping + ops + returns + marketing) | ₹67,732,369.31 |
| Net Profit | ₹40,691,374.24 |
| Net Margin | 11.06% |
| CAC | ₹1,110.72 |
| Marketing ROI | 632.0% |
| Expected Profit (current run-rate) | ₹40,691,374.24 |
| Incremental Value | ₹0 (baseline — see note below) |

Recalculated with LibreOffice via `scripts/recalc.py`: **0 formula errors,
17 formulas**, all evaluating correctly.

**Honest note on Incremental Value**: it's 0 in this workbook by
definition — the current state has no incremental value versus itself.
It becomes meaningful once Phase 12's Scenario Simulator computes
`(Scenario Expected Profit − this baseline)` for each of the four fixed
scenarios (Section 21/22 of the spec).

Next: **Phase 12 — Scenario Analysis** (Retention +5%, Discount −2pp,
Marketing increase, vs. Current — projected Revenue/Profit/Margin/ROI and
the Incremental Value each is worth).

## Phase 12 — Scenario Analysis

`python/scenarios/scenario_engine.py` computes the four fixed scenarios from
spec section 22, and `run_scenarios.py` orchestrates verification + output.

**Data integrity catch first**: before trusting Phase 11's baseline further,
this phase independently re-verified the FY2025 order count two ways (raw
`orders.csv` filtered to 2025, and the sum of `kpi_revenue_by_month.csv`'s
2025 rows) — both agree at **36,459 orders**. The Assumptions sheet's "Total
Orders (FY2025)" cell says 30,895, which doesn't match — a stale/incorrect
filter from Phase 11. It never fed into any Financial Model formula, so it
didn't corrupt anything downstream, but it's flagged here rather than quietly
carried forward.

**Scenarios** (all computed from the same verified FY2025 baseline as Phase
11's Financial Model sheet — nothing re-typed by hand):

| Metric | Current | Retention +5pp | Discount −2pp | Marketing +25% |
|---|---|---|---|---|
| Gross Revenue | ₹367.9M | ₹474.5M | ₹376.4M | ₹376.0M |
| Net Profit | ₹40.69M | ₹54.37M | ₹49.19M | ₹40.10M |
| Net Margin | 11.06% | 11.46% | 13.07% | 10.66% |
| **Incremental Value vs Current** | ₹0 | **₹13.68M** | **₹8.50M** | **−₹0.60M** |

Methodology (full detail in `reports/scenario_analysis_report.md`):
- **Retention +5pp** (12.4% → 17.4%, fixed by spec): applied only to FY2025
  *repeat*-order revenue (₹264.3M of the ₹367.9M total, computed by comparing
  each FY2025 order's date to that customer's first-ever order date across
  full history) — not to new-customer acquisition revenue, since retention
  drives repeat behavior, not first purchases. Variable costs scale with the
  resulting revenue growth.
- **Discount −2pp** (13.44% → 11.44%, fixed by spec): backs out the
  pre-discount list value and re-applies the lower rate at the *same order
  volume*; unit costs (COGS/shipping/ops) are held constant since discount
  policy doesn't change what a unit costs to source or ship.
- **Marketing increase**: the spec gives no fixed % here (unlike the other
  two), so this uses an explicit, documented assumption — +25% spend with a
  diminishing-returns elasticity of 0.7 on customer acquisition, not naive
  1:1 linear scaling. Result: essentially break-even, which is internally
  consistent with Phase 08's statistical finding that marketing spend didn't
  significantly predict performance at this sample size.

Ranked by incremental value: **Retention +5pp > Discount −2pp > Marketing
+25%** — this feeds Phase 14's prioritized recommendations (which will also
weigh cost, risk, and confidence, not just this ranking).

Outputs: `data/processed/scenario_comparison.csv`, `excel/business_model.xlsx`
(new "Scenario Comparison" sheet, recalculated with LibreOffice — 0 formula
errors), `reports/scenario_analysis_report.md`.

Next: **Phase 13 — Business Diagnosis** (combine Phases 07–12 into the "why
is performance changing" narrative — revenue, margin, customers, products,
discounts, returns, marketing, and regions together).

## Phase 13 — Business Diagnosis

`python/analytics/business_diagnosis.py` + `run_diagnosis.py` — spec sections
17 and 19. This is a **synthesis phase**: no new statistics or models are
run. It combines the already-verified outputs of Phases 07–12 into one
causal chain, with every figure either recomputed live from
`data/processed/*.csv` or quoted from an earlier phase's report (cited by
file), so the diagnosis is traceable end-to-end rather than asserted.

**The 9-step causal chain** (full detail with sources in
`reports/business_diagnosis_report.md`):

1. Revenue growth is decelerating (+98% → +13% YoY), statistically confirmed.
2. The deceleration is regional, not market-wide — North/Central are growing
   well above the ~11–13% industry benchmark; South/West are badly
   underperforming it.
3. South's problem is volume/demand, not pricing — it has the **best**
   per-order margin of any region, but `region_South` is the strongest
   positive churn predictor.
4. Repeat-purchase behavior is weakening company-wide: monthly retention
   13.96% → 11.98% (statistically real, p=9.5e-12), 81.3% of the churn
   model's training cohort made no repeat purchase within 90 days.
5. Margin compression: gross margin 34.29% → 29.47% as discount rate rose
   7.04% → 13.44% (high-discount orders average 28.9% margin vs 35.6%,
   p < 1e-300).
6. Returns also rose (5.22% → 7.18%), a second, smaller margin drag.
7. Exposure is concentrated — 8,674 High-Value + High-Risk customers hold
   41.8% of all customer value.
8. Net effect: FY2025 net margin compressed to 11.06%.
9. Scenario testing (Phase 12) independently confirms retention is the
   highest-leverage fix, ahead of discount correction and marketing spend.

**Section 19 comparison**: UrbanCart's blended +13% growth looks in line with
the market, but that number hides the regional split — South and West are
company-specific execution problems layered on top of a company-wide
retention decline, not a market downturn.

Outputs: `data/processed/diagnosis_evidence.json` (structured facts for
Phase 15's AI Business Analyst to explain, not invent),
`reports/business_diagnosis_report.md`.

Next: **Phase 14 — Recommendations & Impact** (turn this diagnosis into 3
prioritized recommendations — problem/evidence/action/expected impact/risk —
using this evidence bundle and Phase 12's scenario values).

## Phase 14 — Recommendations & Impact

`python/analytics/recommendations.py` + `run_recommendations.py` — spec
sections 23 and 24. Converts Phase 13's diagnosis and Phase 12's scenario
values into three ranked, quantified recommendations, each with the full
impact chain: potential customers affected → expected revenue impact →
implementation cost → expected incremental profit → ROI.

| Priority | Recommendation | Incremental Profit | Cost | ROI |
|---|---|---|---|---|
| 1 | Targeted retention program for 8,674 High-Value + High-Risk customers | ₹13.68M | ₹1.73M | 688.6% |
| 2 | Discount governance (approval workflow for top discount-quartile orders) | ₹8.50M | ₹0.50M | 1600.2% |
| 3 | South region execution recovery program | ₹5.80M | ₹2.00M | 190.2% |

Priority order follows total incremental value and strategic weight (Priority
2 actually has a higher ROI% — it's a cheaper policy change — but a smaller
absolute opportunity than Priority 1).

**New number computed this phase** (not a rehash of an earlier phase): the
South recovery opportunity. If South had grown at the ~12% market benchmark
(Phase 10) instead of declining, FY2025 South revenue would have been
₹55.6M vs the actual ₹37.4M — an ₹18.2M revenue gap, ₹5.8M at South's own
gross margin. Computed directly from `kpi_revenue_by_region_trend.csv`.

**Honesty notes baked into the report**:
- Implementation costs are explicitly labeled *planning assumptions*
  (₹200/customer retention outreach, ₹500K discount tooling, ₹2M regional
  program) — reasonable consulting-style estimates, not measured figures.
- Combined impact (₹27.99M profit / ₹4.23M cost if all three are funded) is
  a simple sum, explicitly flagged as a directional upper bound, not a
  re-modeled combined scenario, since the three levers could interact.

Outputs: `data/processed/recommendations.json` (for Phase 15's LLM and
Phase 16's dashboard), `reports/recommendations_report.md`.

Next: **Phase 15 — AI Business Analyst** (the LLM layer that takes this
diagnosis + these recommendations as pre-computed evidence and explains them
conversationally — SQL/Python/R calculate facts, the LLM explains facts,
never invents them).

## Phase 15 — AI Business Analyst

`python/analytics/llm_provider.py`, `ai_business_analyst.py`,
`run_ai_analyst.py` — the LLM explanation layer, enforcing spec Section 25
by construction:

```
SQL / Python / R  ->  CALCULATE FACTS  ->  LLM  ->  EXPLAIN FACTS
```

The LLM never computes a number. It is handed a fixed evidence bundle
assembled from `data/processed/diagnosis_evidence.json` (Phase 13) and
`data/processed/recommendations.json` (Phase 14) — every fact already
computed and cited — and is instructed, via the system prompt, to explain
only what's in that bundle and say so explicitly if a question falls outside
it. Every answer follows: Finding / Evidence / Possible Causes / Confidence
/ Recommendation / Expected Impact / Risks.

**Provider support** — switchable via `.env`, per the frozen stack's
"OpenAI/Gemini" requirement:

- `LLM_PROVIDER=openai` → uses `OPENAI_API_KEY` (model configurable via
  `OPENAI_MODEL`, default `gpt-4o-mini`)
- `LLM_PROVIDER=gemini` → uses `GEMINI_API_KEY` (model configurable via
  `GEMINI_MODEL`, default `gemini-1.5-flash`)

Both SDKs are imported lazily, only inside the code path that actually
calls that provider, so the module doesn't hard-fail if only one SDK is
installed.

**Sandbox honesty note** (same pattern as Postgres/R/Faker in earlier
phases): this sandbox has no internet access, so no real OpenAI/Gemini API
call can be executed here. When no reachable provider/key is found,
`llm_provider.py` falls back to a deterministic **offline mode**, and
`ai_business_analyst.py`'s `compose_offline_answer()` builds a genuine,
evidence-only answer by keyword-scoring the question against every causal
finding (Phase 13) and recommendation (Phase 14), then rendering the best
match under the same heading structure — no invented text, no fabricated
LLM reasoning, just deterministic evidence lookup, clearly labeled
`[OFFLINE MODE]` in every response. The real API call path is fully
implemented and untested-but-correct against each provider's current SDK;
it will run as-is the moment a real key + internet access are present — no
code changes needed.

**Numeric grounding check**: when a real LLM response is used (not
offline), `_check_grounding()` scans the answer for numeric tokens and
flags any that don't appear verbatim in the evidence context — surfaced as
a warning, not silently edited, since minor formatting differences (commas,
rounding) can cause false positives that a human should judge.

Two ways to run it:

```bash
# Demo mode — answers 6 realistic management questions, writes the report
python python/analytics/run_ai_analyst.py

# CLI mode — ask one ad-hoc question (what Phase 16's dashboard will call)
python python/analytics/run_ai_analyst.py --question "Why is South declining?"
```

Output: `reports/ai_analyst_qna.md` (6 sample Q&A pairs, generated here in
offline mode — see the note at the top of that file for how it looks with
a real key). README checklist below updated.

Next: **Phase 16 — Streamlit Dashboard** (Executive Overview, Revenue
Diagnostics, Customer Intelligence, Marketing, Scenario Simulator, and
Recommendations pages — with an "Ask MarketLens" panel wired to
`ai_business_analyst.py`'s `AIBusinessAnalyst.answer()`).

## Phase 16 — Streamlit Dashboard

`dashboard/` — a multi-page Streamlit app, structured per spec section 26:

```
dashboard/
├── app.py                     # Executive Overview (main/landing page)
├── data_access.py             # shared cached loaders — reads ONLY files
│                               already written by Phases 05/07/09/12/13/14
├── scenario_model.py          # interactive scenario engine (see below)
└── pages/
    ├── 1_Revenue_Diagnostics.py
    ├── 2_Customer_Intelligence.py
    ├── 3_Marketing.py
    ├── 4_Scenario_Simulator.py
    ├── 5_Recommendations.py
    └── 6_Ask_MarketLens.py     # bonus: AI analyst panel, wired to Phase 15
```

**Design principle carried over from Phase 15**: the dashboard never
recomputes a KPI from scratch. Every chart and metric reads a file an
earlier, already-verified phase produced (`kpi_*.csv`, `customer_features.csv`,
`churn_predictions.csv`, `scenario_comparison.csv`, `diagnosis_evidence.json`,
`recommendations.json`). If a page needed a number that wasn't already
computed by an earlier phase, that's a signal the number belongs in an
earlier phase's analytics module — not invented here.

**Pages**

- **Executive Overview** (`app.py`) — Revenue, Profit, Margin, Customers,
  Revenue Growth, Profit Growth (section 27), plus the top business/region/
  customer issue and the #1 recommendation, all pulled from Phase 13/14.
- **Revenue Diagnostics** — revenue over time / by region / by product
  category / by customer segment, all filterable by Region, Category,
  Segment, and Date Range (section 28), computed live from
  `order_items_enriched.csv` joined to `customer_features.csv`.
- **Customer Intelligence** — churn probability distribution, CLV vs churn
  scatter, the Value × Risk quadrant breakdown (with High Value + High Risk
  called out explicitly, per spec), and the retention trend (section 29).
- **Marketing** — campaign spend, conversions, revenue, CAC, and ROI,
  compared by campaign and by campaign type (section 30), with Phase 08's
  "spend doesn't statistically predict performance" caveat repeated here.
- **Scenario Simulator** — the interactive decision tool (sections 21/31).
  `scenario_model.py` generalizes Phase 12's exact verified
  retention/discount/marketing formulas into continuous sliders, and adds
  Price, Conversion, Customer Acquisition, and Return Rate — all seven
  levers the spec asks for. A `verify_against_fixed_scenarios()` self-check
  confirms the generalized model reproduces Phase 12's three fixed
  scenarios (Retention +5pp, Discount −2pp, Marketing +25%) to the rupee;
  it caught and fixed a real bug during development (cost lines were
  incorrectly scaling with price/discount changes, which don't move unit
  volume — only retention does). Preset buttons load the exact Phase 12
  scenarios; free sliders let the user explore combinations Phase 12 never
  fixed. Assumptions for the two new levers (price pass-through with no
  demand elasticity; multi-lever effects combined additively, not jointly
  re-modeled) are stated on the page itself.
- **Recommendations** — all 3 priorities from Phase 14 with Problem /
  Evidence / Recommendation / Expected Impact / Risk (section 32), plus the
  combined "if all three funded" total, explicitly labeled a simple sum.
- **Ask MarketLens** *(bonus, beyond the base spec's page list, promised at
  the end of Phase 15)* — a chat-style panel wired directly to Phase 15's
  `AIBusinessAnalyst.answer()`. Verified end-to-end in this sandbox: with no
  OPENAI_API_KEY/internet available it correctly falls back to labeled
  `[OFFLINE MODE]` evidence-grounded answers, exactly as Phase 15 designed.

**Sandbox honesty note** (same pattern as every prior phase): this sandbox
has no internet access, so `streamlit` and `plotly` cannot be `pip install`ed
here and the app itself cannot actually be launched in this environment.
Every page's underlying data logic was independently verified by running it
against a lightweight stub of the `streamlit`/`plotly` APIs (so real
`pandas`/`scikit-learn`/JSON logic executes for real, only rendering calls
are no-ops) — this caught and fixed two real bugs (a KeyError on Priority
2's differently-shaped `expected_impact`, and the cost-scaling bug in the
scenario simulator noted above) before you ever run it. The AI analyst
integration was verified with a real call into `AIBusinessAnalyst.answer()`
through the dashboard's own import path, not just inspected. On your own
machine, running:

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

will launch the real, interactive app — no code changes needed.

Next: **Phase 17 — Testing** (`tests/` — data integrity, analytics,
ML, and scenario-calculation tests with `pytest`).


