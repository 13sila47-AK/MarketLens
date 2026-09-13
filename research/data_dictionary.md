# MarketLens — Data Dictionary

Documents every field in `data/raw/*.csv` as actually generated in Phase 03
(`python/ingestion/generate_dataset.py`). Types and null counts below were
verified against the generated files, not assumed.

## regions.csv (5 rows)

| Field | Type | Description | Allowed Values | Validation |
|---|---|---|---|---|
| `region_id` | INTEGER | Region identifier (PK) | 1–5 | Not null, unique |
| `region_name` | VARCHAR | Region display name | North, South, East, West, Central | Not null, unique |

## stores.csv (18 rows)

| Field | Type | Description | Allowed Values | Validation |
|---|---|---|---|---|
| `store_id` | INTEGER | Store identifier (PK) | 1–18 | Not null, unique |
| `store_name` | VARCHAR | Store display name | — | Not null |
| `region_id` | INTEGER | Region the store belongs to (FK → regions) | 1–5 | Not null, must exist in regions |

## products.csv (150 rows)

| Field | Type | Description | Allowed Values | Validation |
|---|---|---|---|---|
| `product_id` | INTEGER | Product identifier (PK) | 1–150 | Not null, unique |
| `product_name` | VARCHAR | Product display name | — | Not null |
| `category` | VARCHAR | Product category | Apparel, Home Goods, Electronics Accessories, Personal Care, Footwear | Not null |
| `cost` | DECIMAL | Unit cost to the business | > 0 | Not null, ≤ `selling_price` |
| `selling_price` | DECIMAL | Catalog selling price | > 0 | Not null, > `cost` |

## customers.csv (45,000 rows)

| Field | Type | Description | Allowed Values | Validation |
|---|---|---|---|---|
| `customer_id` | INTEGER | Customer identifier (PK) | 1–45000 | Not null, unique |
| `customer_name` | VARCHAR | Customer display name (synthetic) | — | Not null |
| `signup_date` | DATE | Date the customer registered | 2023-01-01 to 2025-12-27 | Not null, valid date |
| `region_name` | VARCHAR | Customer's registered region (FK → regions.region_name) | North, South, East, West, Central | Not null, must exist in regions |
| `acquisition_campaign_id` | FLOAT (nullable int) | Marketing campaign credited with acquiring this customer (FK → marketing_campaigns.campaign_id) | valid campaign_id or null | Null = organic signup (54% of rows are null in the generated data) |

Note: `customer_segment` (New / Regular / Loyal / At-Risk / Churned) is
**intentionally not stored here**. Per the Phase 02 data-model design
decision, segment is a derived, time-dependent label computed from purchase
recency/frequency in the analytics layer (Phase 07), not a fixed raw
attribute — a customer's segment changes over time without their master
record changing.

## marketing_campaigns.csv (75 rows)

| Field | Type | Description | Allowed Values | Validation |
|---|---|---|---|---|
| `campaign_id` | INTEGER | Campaign identifier (PK) | 1–75 | Not null, unique |
| `campaign_date` | DATE | Campaign launch date | 2023-01-01 to 2025-12-27 | Not null |
| `campaign_type` | VARCHAR | Channel/type of campaign | Email, Social Media, Search Ads, Influencer, In-Store Promo | Not null |
| `spend` | DECIMAL | Campaign spend (₹) | 50,000–400,000 | Not null, ≥ 0 |
| `customers_targeted` | INTEGER | Number of customers targeted | 2,000–15,000 | Not null, ≥ 0 |
| `customers_converted` | INTEGER | Number of customers converted | ≥ 0 | Not null, **≤ `customers_targeted`** (enforced) |

## orders.csv (82,800 rows)

| Field | Type | Description | Allowed Values | Validation |
|---|---|---|---|---|
| `order_id` | INTEGER | Order identifier (PK) | 1–82800 | Not null, unique |
| `customer_id` | INTEGER | Customer who placed the order (FK → customers) | valid customer_id | Not null, must exist in customers |
| `order_date` | DATE | Date of purchase | 2023-01-01 to 2025-12-27 | Not null, valid date |
| `channel` | VARCHAR | Fulfillment channel | `online`, `in-store` | Not null |
| `store_id` | FLOAT (nullable int) | Store where the order was placed (FK → stores) | valid store_id or null | **Null only when `channel = 'online'`** (47,707 of 82,800 rows are online and thus null) |

## order_items.csv (206,497 rows)

| Field | Type | Description | Allowed Values | Validation |
|---|---|---|---|---|
| `order_item_id` | INTEGER | Line item identifier (PK) | 1–206497 | Not null, unique |
| `order_id` | INTEGER | Parent order (FK → orders) | valid order_id | Not null, must exist in orders |
| `product_id` | INTEGER | Product purchased (FK → products) | valid product_id | Not null, must exist in products |
| `quantity` | INTEGER | Units purchased | 1–3 | Not null, > 0 |
| `unit_price` | DECIMAL | Catalog price at time of purchase | > 0 | Not null, matches product's `selling_price` |
| `discount` | DECIMAL | Discount amount applied (₹, not %) | ≥ 0 | Not null, **≤ `quantity × unit_price`** (enforced) |
| `revenue` | DECIMAL | Net line revenue | ≥ 0 | Not null, = `quantity × unit_price − discount` (enforced) |

This is where the "revenue" figure in the original spec's flat `orders`
table now lives — split correctly across `order_id` + `product_id` grain
per the Phase 02 design decision, so order-level revenue is always a
derived `SUM(order_items.revenue)`, never a second stored value.

## returns.csv (12,333 rows — 6.0% of all line items)

| Field | Type | Description | Allowed Values | Validation |
|---|---|---|---|---|
| `return_id` | INTEGER | Return identifier (PK) | 1–12333 | Not null, unique |
| `order_id` | INTEGER | Order the return relates to (FK → orders) | valid order_id | Not null, must exist in orders |
| `return_date` | DATE | Date of return | 2–20 days after order_date | Not null, > order_date |
| `return_reason` | VARCHAR | Reason given for return | Wrong size, Defective item, Not as described, Changed mind, Better price found elsewhere, Late delivery | Not null |
| `return_amount` | DECIMAL | Amount refunded (₹) | ≥ 0 | Not null, = revenue of the returned line item |

## costs.csv (82,800 rows — exactly one per order)

| Field | Type | Description | Allowed Values | Validation |
|---|---|---|---|---|
| `order_id` | INTEGER | Order the cost relates to (FK → orders, effectively PK) | valid order_id | Not null, unique, must exist in orders |
| `shipping_cost` | DECIMAL | Shipping/delivery cost (₹) | ≥ 5 | Not null; higher for online orders and farther regions |
| `operational_cost` | DECIMAL | Fulfillment/operational cost (₹) | > 0 | Not null; ~6–10% of order revenue + fixed handling fee |

## Known, Intentional Data Patterns (ground truth for later diagnosis)

These were built into the generator and independently verified by direct
querying of the generated CSVs before this dictionary was written — they
are not assumptions, they are measured facts about this specific dataset:

- **Company-wide revenue growth decelerates**: ₹164.3M (2023) → ₹324.9M
  (2024, +98%) → ₹367.9M (2025, +13%).
- **South region is now in real decline**: revenue fell from ₹49.7M (2024)
  to ₹37.4M (2025), a ~25% YoY drop. West has flattened. North and Central
  continue to grow strongly.
- **Discounting intensity is rising**: average discount rate grew from
  ~7.0% (2023) to ~13.4% (2025) of gross order value.
- **Return rates are rising**: from ~5.0% (2023) to ~6.7% (2025) of line
  items, concentrated in Electronics Accessories.
- **Month-over-month customer retention is declining**: from ~16.3%
  average (first 6 months) to ~12.1% average (last 6 months) — a real,
  measurable weakening of repeat purchase behavior.
- **Regional customer stickiness varies**: South customers have the lowest
  early-tenure activity rate of any region; North the highest — consistent
  with South being the region driving the company's problem.

No downstream phase should hardcode these numbers — they are restated here
only as a record of what the generator produced, so later analytics
(Phase 07+) can be checked against a known ground truth during development.
