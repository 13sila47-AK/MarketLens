"""
MarketLens - Phase 07: Customer KPIs
======================================
Descriptive customer-level KPIs built on top of customer_features.py's
per-customer table. Note: "churn" here is a descriptive rate from the
segment table (customers whose last purchase > 180 days ago), not a
prediction — the predictive churn model is Phase 09.
"""

from __future__ import annotations

import pandas as pd


def customer_kpi_summary(features: pd.DataFrame, orders: pd.DataFrame) -> dict:
    total_customers = len(features)

    repeat_customers = int((features["total_orders"] >= 2).sum())
    churned = int((features["customer_segment"] == "Churned").sum())
    at_risk = int((features["customer_segment"] == "At-Risk").sum())
    never_purchased = int((features["customer_segment"] == "Never Purchased").sum())

    active_purchasers = total_customers - never_purchased

    return {
        "total_customers": total_customers,
        "customers_with_purchase": active_purchasers,
        "conversion_rate_pct": round(active_purchasers / total_customers * 100, 2) if total_customers else 0.0,
        "never_purchased": never_purchased,
        "repeat_customers": repeat_customers,
        "repeat_purchase_rate_pct": round(
            repeat_customers / active_purchasers * 100, 2
        ) if active_purchasers else 0.0,
        "churned_customers": churned,
        "churn_rate_pct": round(churned / active_purchasers * 100, 2) if active_purchasers else 0.0,
        "at_risk_customers": at_risk,
        "at_risk_rate_pct": round(at_risk / active_purchasers * 100, 2) if active_purchasers else 0.0,
        "avg_customer_lifetime_value": round(
            float(features.loc[features["total_orders"] > 0, "customer_lifetime_value"].mean()), 2
        ) if active_purchasers else 0.0,
        "avg_orders_per_active_customer": round(
            float(features.loc[features["total_orders"] > 0, "total_orders"].mean()), 2
        ) if active_purchasers else 0.0,
    }


def acquisition_by_cohort_month(features: pd.DataFrame) -> pd.DataFrame:
    df = features.copy()
    df["signup_month"] = pd.to_datetime(df["signup_date"]).dt.to_period("M").astype(str)
    out = (
        df.groupby("signup_month")
        .agg(
            customers_acquired=("customer_id", "count"),
            converted=("total_orders", lambda s: int((s > 0).sum())),
        )
        .reset_index()
        .sort_values("signup_month")
    )
    out["conversion_rate_pct"] = (out["converted"] / out["customers_acquired"] * 100).round(2)
    return out


def monthly_retention_curve(orders: pd.DataFrame) -> pd.DataFrame:
    """Month-over-month retention: of customers active in month M, what
    share are also active in month M+1. This is the metric Phase 03's
    dataset generation deliberately embedded a decline into (~16% -> ~12%),
    calculated here independently from the actual order data rather than
    assumed from the generation notes."""
    df = orders.copy()
    df["month"] = df["order_date"].dt.to_period("M")
    monthly_customers = df.groupby("month")["customer_id"].apply(set).sort_index()

    months = monthly_customers.index.tolist()
    rows = []
    for i in range(len(months) - 1):
        this_month, next_month = months[i], months[i + 1]
        active_this = monthly_customers[this_month]
        active_next = monthly_customers[next_month]
        retained = active_this & active_next
        rate = len(retained) / len(active_this) * 100 if active_this else 0.0
        rows.append({
            "month": str(this_month),
            "active_customers": len(active_this),
            "retained_next_month": len(retained),
            "retention_rate_pct": round(rate, 2),
        })
    return pd.DataFrame(rows)


def revenue_at_risk(features: pd.DataFrame) -> dict:
    """How much historical CLV sits with At-Risk + Churned customers —
    frames retention as a dollar problem, not just a headcount problem."""
    at_risk_or_churned = features[features["customer_segment"].isin(["At-Risk", "Churned"])]
    total_active_clv = features.loc[features["total_orders"] > 0, "customer_lifetime_value"].sum()
    at_risk_clv = at_risk_or_churned["customer_lifetime_value"].sum()
    return {
        "at_risk_or_churned_customers": int(len(at_risk_or_churned)),
        "at_risk_or_churned_clv": round(float(at_risk_clv), 2),
        "pct_of_total_active_clv": round(
            float(at_risk_clv) / float(total_active_clv) * 100, 2
        ) if total_active_clv else 0.0,
    }
