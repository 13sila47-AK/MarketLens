# MarketLens Data Quality Report

_Generated: 2026-09-12 15:15_

Phase 06 output. All numbers below are computed live from `data/raw/*.csv` and `data/processed/*.csv` by `python/validation/data_quality.py` — nothing here is hand-typed.

## Summary

| Metric | Value |
|---|---|
| Tables checked | 9 |
| Total rows processed | 429,678 |
| &nbsp;&nbsp;— regions | 5 |
| &nbsp;&nbsp;— stores | 18 |
| &nbsp;&nbsp;— products | 150 |
| &nbsp;&nbsp;— marketing_campaigns | 75 |
| &nbsp;&nbsp;— customers | 45,000 |
| &nbsp;&nbsp;— orders | 82,800 |
| &nbsp;&nbsp;— order_items | 206,497 |
| &nbsp;&nbsp;— returns | 12,333 |
| &nbsp;&nbsp;— costs | 82,800 |
| Checks run | 81 |
| Critical issues found | 0 |
| Warning issues found | 0 |
| Records failing a hard-integrity rule | 0 |

## Result

**PASS** — zero critical data-quality violations found across missing values, duplicates, invalid values, and cross-source referential integrity. This confirms the pipeline (Phase 03 generation → Phase 04 schema constraints → Phase 05 extraction) preserves data integrity end to end, and that `data/processed/*.csv` is safe to build analytics on top of.

## Checks by category

### Missing Values

| Table | Severity | Count | Detail |
|---|---|---|---|
| customers | 🟢 info | 0 | customers.customer_id: 0 missing (0.00%) |
| customers | 🟢 info | 0 | customers.customer_name: 0 missing (0.00%) |
| customers | 🟢 info | 0 | customers.signup_date: 0 missing (0.00%) |
| customers | 🟢 info | 0 | customers.region_name: 0 missing (0.00%) |
| orders | 🟢 info | 0 | orders.order_id: 0 missing (0.00%) |
| orders | 🟢 info | 0 | orders.customer_id: 0 missing (0.00%) |
| orders | 🟢 info | 0 | orders.order_date: 0 missing (0.00%) |
| orders | 🟢 info | 0 | orders.channel: 0 missing (0.00%) |
| order_items | 🟢 info | 0 | order_items.order_item_id: 0 missing (0.00%) |
| order_items | 🟢 info | 0 | order_items.order_id: 0 missing (0.00%) |
| order_items | 🟢 info | 0 | order_items.product_id: 0 missing (0.00%) |
| order_items | 🟢 info | 0 | order_items.quantity: 0 missing (0.00%) |
| order_items | 🟢 info | 0 | order_items.unit_price: 0 missing (0.00%) |
| order_items | 🟢 info | 0 | order_items.revenue: 0 missing (0.00%) |
| products | 🟢 info | 0 | products.product_id: 0 missing (0.00%) |
| products | 🟢 info | 0 | products.product_name: 0 missing (0.00%) |
| products | 🟢 info | 0 | products.category: 0 missing (0.00%) |
| products | 🟢 info | 0 | products.cost: 0 missing (0.00%) |
| products | 🟢 info | 0 | products.selling_price: 0 missing (0.00%) |
| returns | 🟢 info | 0 | returns.return_id: 0 missing (0.00%) |
| returns | 🟢 info | 0 | returns.order_id: 0 missing (0.00%) |
| returns | 🟢 info | 0 | returns.return_date: 0 missing (0.00%) |
| returns | 🟢 info | 0 | returns.return_amount: 0 missing (0.00%) |
| costs | 🟢 info | 0 | costs.order_id: 0 missing (0.00%) |
| costs | 🟢 info | 0 | costs.shipping_cost: 0 missing (0.00%) |
| costs | 🟢 info | 0 | costs.operational_cost: 0 missing (0.00%) |
| marketing_campaigns | 🟢 info | 0 | marketing_campaigns.campaign_id: 0 missing (0.00%) |
| marketing_campaigns | 🟢 info | 0 | marketing_campaigns.campaign_date: 0 missing (0.00%) |
| marketing_campaigns | 🟢 info | 0 | marketing_campaigns.spend: 0 missing (0.00%) |
| orders | 🔴 critical | 0 | orders.store_id missing on in-store orders: 0 |

### Duplicates

| Table | Severity | Count | Detail |
|---|---|---|---|
| customers | 🟢 info | 0 | customers: 0 duplicate customer_id values |
| orders | 🟢 info | 0 | orders: 0 duplicate order_id values |
| order_items | 🟢 info | 0 | order_items: 0 duplicate order_item_id values |
| products | 🟢 info | 0 | products: 0 duplicate product_id values |
| stores | 🟢 info | 0 | stores: 0 duplicate store_id values |
| regions | 🟢 info | 0 | regions: 0 duplicate region_id values |
| marketing_campaigns | 🟢 info | 0 | marketing_campaigns: 0 duplicate campaign_id values |
| returns | 🟢 info | 0 | returns: 0 duplicate return_id values |
| costs | 🟢 info | 0 | costs: 0 duplicate order_id values |

### Exact Row Duplicates

| Table | Severity | Count | Detail |
|---|---|---|---|
| regions | 🟢 info | 0 | regions: 0 fully duplicated rows |
| stores | 🟢 info | 0 | stores: 0 fully duplicated rows |
| products | 🟢 info | 0 | products: 0 fully duplicated rows |
| marketing_campaigns | 🟢 info | 0 | marketing_campaigns: 0 fully duplicated rows |
| customers | 🟢 info | 0 | customers: 0 fully duplicated rows |
| orders | 🟢 info | 0 | orders: 0 fully duplicated rows |
| order_items | 🟢 info | 0 | order_items: 0 fully duplicated rows |
| returns | 🟢 info | 0 | returns: 0 fully duplicated rows |
| costs | 🟢 info | 0 | costs: 0 fully duplicated rows |

### Invalid Values

| Table | Severity | Count | Detail |
|---|---|---|---|
| order_items | 🟢 info | 0 | Negative revenue rows: 0 |
| order_items | 🟢 info | 0 | Non-positive quantity rows: 0 |
| order_items | 🟢 info | 0 | discount > order value rows: 0 |
| order_items | 🟢 info | 0 | revenue != qty*price-discount rows: 0 |
| orders | 🟢 info | 0 | orders.order_date: 0 unparseable dates |
| orders | 🟢 info | 0 | orders.order_date: 0 dates outside 2020-2026 |
| customers | 🟢 info | 0 | customers.signup_date: 0 unparseable dates |
| customers | 🟢 info | 0 | customers.signup_date: 0 dates outside 2020-2026 |
| returns | 🟢 info | 0 | returns.return_date: 0 unparseable dates |
| returns | 🟢 info | 0 | returns.return_date: 0 dates outside 2020-2026 |
| marketing_campaigns | 🟢 info | 0 | marketing_campaigns.campaign_date: 0 unparseable dates |
| marketing_campaigns | 🟢 info | 0 | marketing_campaigns.campaign_date: 0 dates outside 2020-2026 |
| customers | 🟢 info | 0 | customers.region_name not in ['Central', 'East', 'North', 'South', 'West']: 0 |
| orders | 🟢 info | 0 | orders.channel invalid: 0 |
| products | 🟢 info | 0 | products.category invalid: 0 |
| products | 🟢 info | 0 | products.cost >= selling_price: 0 |
| returns | 🟢 info | 0 | Negative return_amount rows: 0 |
| returns | 🟢 info | 0 | returns.return_reason invalid: 0 |
| marketing_campaigns | 🟢 info | 0 | customers_converted > customers_targeted: 0 |
| marketing_campaigns | 🟢 info | 0 | campaign_type invalid: 0 |

### Cross Source Integrity

| Table | Severity | Count | Detail |
|---|---|---|---|
| orders | 🟢 info | 0 | orders.customer_id -> customers.customer_id: 0 orphan rows |
| order_items | 🟢 info | 0 | order_items.order_id -> orders.order_id: 0 orphan rows |
| order_items | 🟢 info | 0 | order_items.product_id -> products.product_id: 0 orphan rows |
| orders | 🟢 info | 0 | orders.store_id -> stores.store_id (non-null only): 0 orphan rows |
| returns | 🟢 info | 0 | returns.order_id -> orders.order_id: 0 orphan rows |
| costs | 🟢 info | 0 | costs.order_id -> orders.order_id: 0 orphan rows |
| customers | 🟢 info | 0 | customers.region_name -> regions.region_name: 0 orphan rows |
| customers | 🟢 info | 0 | customers.acquisition_campaign_id -> marketing_campaigns.campaign_id (non-null only): 0 orphan rows |
| costs | 🟢 info | 0 | orders missing a costs row: 0 |
| order_items | 🟢 info | 0 | orders with zero order_items: 0 |

### Processed Reconciliation

| Table | Severity | Count | Detail |
|---|---|---|---|
| order_items_enriched | 🟢 info | 0 | Revenue reconciliation raw vs item-grain enriched: raw=₹857,168,939.70 enriched=₹857,168,939.70 diff=₹0.00 |
| orders_enriched | 🟢 info | 0 | Revenue reconciliation raw vs order-grain enriched: raw=₹857,168,939.70 enriched=₹857,168,939.70 diff=₹0.00 |
| order_items_enriched | 🟢 info | 0 | Row count raw (206497) vs enriched item-grain (206497) |

## Interpretation

This check is intentionally redundant with the CHECK constraints in `sql/schema.sql` (Phase 04) and the generation-time consistency checks in `python/ingestion/generate_dataset.py` (Phase 03). Running it independently at Phase 06, against the actual files the analytics layer will consume, is what makes 'the data is clean' a verified fact rather than an assumption carried over from earlier phases.
