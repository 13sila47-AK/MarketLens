# MarketLens — Data Model

This defines the entities, key fields, and relationships for UrbanCart's
data before any dataset or SQL is written. Full field-level definitions
(types, validation rules, allowed values) will be finalized in the data
dictionary once the dataset is generated (Phase 03).

## Entity List

| Table | Purpose |
|---|---|
| `regions` | The 5 geographic regions UrbanCart operates in |
| `stores` | Physical store locations, each belongs to a region |
| `customers` | Customer master data, each linked to a region |
| `products` | Product catalog with cost and price |
| `orders` | Order header — one row per order |
| `order_items` | Order line items — one row per product per order |
| `marketing_campaigns` | Campaigns run to acquire/re-engage customers |
| `returns` | Returned items linked back to orders |
| `costs` | Shipping and operational cost linked to orders |
| `competitors` | External competitor reference data (used in research, not internal DB-joined) |

## Relationships (Entity Hierarchy)

```
regions
   └── stores
          └── customers
                 └── orders
                        └── order_items ── products

marketing_campaigns ──> customers   (a campaign targets/converts customers)
orders ──> returns                  (an order may have 0..n returns)
orders ──> costs                    (an order has one costs record)
```

## Key Fields Per Table (overview — full spec in data dictionary)

**regions**
- `region_id` (PK), `region_name`

**stores**
- `store_id` (PK), `store_name`, `region_id` (FK → regions)

**customers**
- `customer_id` (PK), `signup_date`, `region_id` (FK → regions),
  `customer_segment` (derived, recalculated from behavior — not a fixed
  attribute set at signup)

**products**
- `product_id` (PK), `product_name`, `category`, `cost`, `selling_price`

**orders**
- `order_id` (PK), `customer_id` (FK), `store_id` (FK, nullable for
  online orders), `order_date`, `channel` (in-store / online)

**order_items**
- `order_item_id` (PK), `order_id` (FK), `product_id` (FK), `quantity`,
  `unit_price`, `discount`, `revenue` (derived: quantity × unit_price −
  discount)

**marketing_campaigns**
- `campaign_id` (PK), `campaign_date`, `campaign_type`, `spend`,
  `customers_targeted`, `customers_converted`

**returns**
- `return_id` (PK), `order_id` (FK), `return_date`, `return_reason`,
  `return_amount`

**costs**
- `order_id` (FK, effectively PK — one cost record per order),
  `shipping_cost`, `operational_cost`

**competitors** *(external/reference — populated from research, not
transactional)*
- `competitor_name`, `product_focus`, `price_positioning`, `notable_trend`

## Design Decisions

1. **`customer_segment` is derived, not stored as a fixed label.** It will
   be computed from purchase recency/frequency in the analytics layer
   (Phase 07) rather than baked into the raw dataset, so the segmentation
   logic is transparent and auditable rather than a hidden hardcoded value.
2. **Revenue lives at the `order_items` grain**, not the `orders` grain.
   Order-level revenue is always a SUM aggregation over its items. This
   keeps product-level analysis (top products, category performance)
   possible without a second source of truth for revenue.
3. **`channel` (in-store vs. online) sits on `orders`**, since a single
   order is fulfilled through exactly one channel, letting `store_id` be
   nullable for online orders while still resolving to a region via the
   customer's registered region.
4. **Costs are separated from `order_items`** because shipping and
   operational cost are order-level (not product-level) in this dataset —
   consistent with how the source data will be generated in Phase 03.
5. **Competitors are not foreign-keyed into the transactional schema.**
   They inform the external market comparison (Phase 10) and are treated
   as reference/research data, not part of the operational database.

## What Comes Next (Phase 03)

Phase 03 will generate a realistic synthetic dataset that populates every
table above with internally consistent values (e.g., an order's revenue
correctly sums its line items; a returned item references a real order;
a campaign's `customers_converted` never exceeds `customers_targeted`),
followed by the full data dictionary documenting every field's type,
source, allowed values, and validation rule.
