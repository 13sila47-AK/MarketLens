# MarketLens R Cross-Validation Report

_Phase 08. Headline financial KPIs recomputed independently in R,
straight from `data/raw/*.csv`, without importing any Python code,
and compared against `reports/business_analytics_report.md`
(Phase 07, computed in Python/pandas). Two independent language
implementations agreeing is stronger evidence than one._

| KPI | R (independent) | Python (Phase 07) | Match |
|---|---:|---:|:---:|
| gross_revenue | 857168939.70 | 857168939.70 | Yes |
| net_revenue | 803075998.49 | 803075998.49 | Yes |
| total_discount | 106043181.82 | 106043181.82 | Yes |
| total_returned | 54092941.21 | 54092941.21 | Yes |
| gross_margin_pct | 31.40 | 31.40 | Yes |
| discount_impact_pct | 11.01 | 11.01 | Yes |
| return_impact_pct | 6.31 | 6.31 | Yes |
| n_orders | 82800 | 82800 | Yes |

**Result: all headline KPIs cross-validated.**
