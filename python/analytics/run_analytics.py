"""
MarketLens - Phase 07: Business Analytics Engine — Orchestrator
==================================================================
Runs every KPI module (revenue, profitability, customer, product,
marketing), builds the customer feature table, and writes:

  - data/processed/customer_features.csv   (Phase 09 model input)
  - data/processed/kpi_*.csv               (dashboard-ready breakdowns)
  - reports/business_analytics_report.md   (human-readable summary)

Usage:
    python python/analytics/run_analytics.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_loader import load_orders, load_order_items, load_customers, load_campaigns, as_of_date
import revenue as rev
import profitability as prof
import customer_features as cf
import customer_analytics as ca
import product_analytics as pa
import marketing_analytics as ma

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_PATH = ROOT / "reports" / "business_analytics_report.md"


def money(x: float) -> str:
    return f"\u20b9{x:,.2f}"


def df_to_md(df: pd.DataFrame, max_rows: int = 15) -> str:
    return df.head(max_rows).to_markdown(index=False, floatfmt=",.2f")


def main() -> None:
    orders = load_orders()
    order_items = load_order_items()
    customers = load_customers()
    campaigns = load_campaigns()
    cutoff = as_of_date(orders)

    # ---- Customer features (Section 12) ----
    features = cf.build_customer_features(customers, orders, cutoff)
    features.to_csv(PROCESSED_DIR / "customer_features.csv", index=False)
    seg_summary = cf.segment_summary(features)
    seg_summary.to_csv(PROCESSED_DIR / "kpi_customer_segment_summary.csv", index=False)

    orders_with_segment = orders.merge(
        features[["customer_id", "customer_segment"]], on="customer_id", how="left"
    )

    # ---- Revenue KPIs ----
    rev_summary = rev.total_revenue(orders)
    rev_month = rev.revenue_by_month(orders)
    rev_yoy = rev.revenue_growth_yoy(orders)
    rev_region = rev.revenue_by_region(orders)
    rev_region_trend = rev.revenue_by_region_trend_yoy(orders)
    rev_category = rev.revenue_by_category(order_items)
    rev_channel = rev.revenue_by_channel(orders)
    rev_segment = rev.revenue_by_segment(orders_with_segment)

    rev_month.to_csv(PROCESSED_DIR / "kpi_revenue_by_month.csv", index=False)
    rev_region.to_csv(PROCESSED_DIR / "kpi_revenue_by_region.csv", index=False)
    rev_region_trend.to_csv(PROCESSED_DIR / "kpi_revenue_by_region_trend.csv", index=False)
    rev_category.to_csv(PROCESSED_DIR / "kpi_revenue_by_category.csv", index=False)
    rev_segment.to_csv(PROCESSED_DIR / "kpi_revenue_by_segment.csv", index=False)

    # ---- Profitability KPIs ----
    prof_summary = prof.profitability_summary(orders, order_items)
    margin_trend = prof.gross_margin_trend_yoy(orders, order_items)
    prof_region = prof.profitability_by_region(orders, order_items)
    margin_trend.to_csv(PROCESSED_DIR / "kpi_margin_trend_yoy.csv", index=False)
    prof_region.to_csv(PROCESSED_DIR / "kpi_profitability_by_region.csv", index=False)

    # ---- Customer KPIs ----
    cust_summary = ca.customer_kpi_summary(features, orders)
    retention_curve = ca.monthly_retention_curve(orders)
    risk_clv = ca.revenue_at_risk(features)
    retention_curve.to_csv(PROCESSED_DIR / "kpi_monthly_retention.csv", index=False)

    # ---- Product KPIs ----
    top_prod = pa.top_products(order_items, n=10)
    low_margin = pa.low_margin_products(order_items, n=10)
    high_growth = pa.high_growth_products(order_items, n=10)
    declining = pa.declining_products(order_items, n=10)
    category_perf = pa.category_performance(order_items)
    category_perf.to_csv(PROCESSED_DIR / "kpi_category_performance.csv", index=False)

    # ---- Marketing KPIs ----
    camp_perf = ma.campaign_performance(campaigns, customers, orders)
    camp_type = ma.campaign_type_summary(camp_perf)
    mkt_summary = ma.marketing_summary(campaigns, customers, orders)
    camp_perf.to_csv(PROCESSED_DIR / "kpi_campaign_performance.csv", index=False)
    camp_type.to_csv(PROCESSED_DIR / "kpi_campaign_type_summary.csv", index=False)

    # ---- Report ----
    lines = []
    lines.append("# MarketLens Business Analytics Report")
    lines.append("")
    lines.append(f"_Phase 07 output. Data window: {orders['order_date'].min().date()} "
                 f"to {orders['order_date'].max().date()}. All figures computed live "
                 f"from `data/processed/*.csv` by `python/analytics/run_analytics.py`._")
    lines.append("")

    lines.append("## 1. Revenue KPIs")
    lines.append("")
    lines.append(f"- **Total gross revenue:** {money(rev_summary['gross_revenue'])}")
    lines.append(f"- **Total net revenue (after returns):** {money(rev_summary['net_revenue'])}")
    lines.append(f"- **Total discount given:** {money(rev_summary['total_discount_given'])}")
    lines.append(f"- **Total returned amount:** {money(rev_summary['total_returned_amount'])}")
    lines.append(f"- **Total orders:** {rev_summary['total_orders']:,}")
    lines.append("")
    lines.append("**Revenue growth YoY:**")
    lines.append("")
    lines.append(df_to_md(rev_yoy))
    lines.append("")
    lines.append("**Revenue by region:**")
    lines.append("")
    lines.append(df_to_md(rev_region))
    lines.append("")
    lines.append("**Revenue by region, year over year (this is where the "
                 "South-region decline shows up numerically):**")
    lines.append("")
    lines.append(df_to_md(rev_region_trend))
    lines.append("")
    lines.append("**Revenue by product category:**")
    lines.append("")
    lines.append(df_to_md(rev_category))
    lines.append("")
    lines.append("**Revenue by customer segment:**")
    lines.append("")
    lines.append(df_to_md(rev_segment))
    lines.append("")

    lines.append("## 2. Profitability KPIs")
    lines.append("")
    for k, v in prof_summary.items():
        label = k.replace("_", " ").capitalize()
        val = money(v) if ("revenue" in k or "profit" in k or "cost" in k or "discount" in k
                            or "returned" in k or "cogs" in k or "margin" in k) and "pct" not in k else v
        if "pct" in k:
            val = f"{v}%"
        lines.append(f"- **{label}:** {val}")
    lines.append("")
    lines.append("**Gross margin trend by year (margin compression visible here):**")
    lines.append("")
    lines.append(df_to_md(margin_trend))
    lines.append("")
    lines.append("**Profitability by region (weakest margin first):**")
    lines.append("")
    lines.append(df_to_md(prof_region))
    lines.append("")

    lines.append("## 3. Customer KPIs")
    lines.append("")
    for k, v in cust_summary.items():
        label = k.replace("_", " ").capitalize()
        val = f"{v}%" if "pct" in k else (money(v) if "value" in k else f"{v:,}" if isinstance(v, int) else v)
        lines.append(f"- **{label}:** {val}")
    lines.append("")
    lines.append("**Customer segment summary:**")
    lines.append("")
    lines.append(df_to_md(seg_summary))
    lines.append("")
    lines.append(f"- **Revenue sitting with At-Risk + Churned customers:** "
                 f"{money(risk_clv['at_risk_or_churned_clv'])} "
                 f"({risk_clv['pct_of_total_active_clv']}% of total active-customer CLV, "
                 f"across {risk_clv['at_risk_or_churned_customers']:,} customers)")
    lines.append("")
    lines.append("**Month-over-month retention curve (first 6 and last 6 months):**")
    lines.append("")
    lines.append(df_to_md(pd.concat([retention_curve.head(6), retention_curve.tail(6)])))
    lines.append("")

    lines.append("## 4. Product KPIs")
    lines.append("")
    lines.append("**Top 10 products by revenue:**")
    lines.append("")
    lines.append(df_to_md(top_prod))
    lines.append("")
    lines.append("**10 lowest-margin products (min ₹10,000 revenue):**")
    lines.append("")
    lines.append(df_to_md(low_margin))
    lines.append("")
    lines.append("**Top 10 highest-growth products (latest YoY):**")
    lines.append("")
    lines.append(df_to_md(high_growth[["product_id", "product_name", "category",
                                        "latest_yoy_growth_pct", "revenue"]]))
    lines.append("")
    lines.append("**10 most-declining products (latest YoY):**")
    lines.append("")
    lines.append(df_to_md(declining[["product_id", "product_name", "category",
                                      "latest_yoy_growth_pct", "revenue"]]))
    lines.append("")
    lines.append("**Category performance:**")
    lines.append("")
    lines.append(df_to_md(category_perf))
    lines.append("")

    lines.append("## 5. Marketing KPIs")
    lines.append("")
    for k, v in mkt_summary.items():
        label = k.replace("_", " ").capitalize()
        val = f"{v}%" if "pct" in k else (money(v) if ("spend" in k or "cac" in k or "revenue" in k) else f"{v:,}")
        lines.append(f"- **{label}:** {val}")
    lines.append("")
    lines.append("**Campaign type performance (ROI ranked):**")
    lines.append("")
    lines.append(df_to_md(camp_type))
    lines.append("")
    lines.append("**Top 10 individual campaigns by ROI:**")
    lines.append("")
    lines.append(df_to_md(camp_perf.head(10)[[
        "campaign_id", "campaign_type", "campaign_date", "spend",
        "customers_acquired", "cac", "revenue_from_acquired", "roi_pct",
    ]]))
    lines.append("")
    lines.append("**Bottom 10 individual campaigns by ROI:**")
    lines.append("")
    lines.append(df_to_md(camp_perf.tail(10)[[
        "campaign_id", "campaign_type", "campaign_date", "spend",
        "customers_acquired", "cac", "revenue_from_acquired", "roi_pct",
    ]]))
    lines.append("")

    lines.append("## Outputs written")
    lines.append("")
    lines.append("All under `data/processed/`: `customer_features.csv`, "
                 "`kpi_customer_segment_summary.csv`, `kpi_revenue_by_month.csv`, "
                 "`kpi_revenue_by_region.csv`, `kpi_revenue_by_region_trend.csv`, "
                 "`kpi_revenue_by_category.csv`, `kpi_revenue_by_segment.csv`, "
                 "`kpi_margin_trend_yoy.csv`, `kpi_profitability_by_region.csv`, "
                 "`kpi_monthly_retention.csv`, `kpi_category_performance.csv`, "
                 "`kpi_campaign_performance.csv`, `kpi_campaign_type_summary.csv`.")
    lines.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[run_analytics.py] Wrote {REPORT_PATH}")
    print(f"[run_analytics.py] Wrote customer_features.csv ({len(features):,} customers)")
    print(f"[run_analytics.py] Total gross revenue: {money(rev_summary['gross_revenue'])}")


if __name__ == "__main__":
    main()
