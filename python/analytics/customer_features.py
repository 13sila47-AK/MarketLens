"""
MarketLens - Phase 07 / Spec Section 12: Customer Feature Engineering
=======================================================================
Builds the per-customer analytical table used both for descriptive customer
KPIs (this phase) and as the model input for churn prediction later
(Phase 09). Every row is one customer — including the ~35% who signed up
but never placed an order, since "never converted" is itself a real,
important business signal, not something to silently drop.

Features per customer (per spec section 12):
    total_orders, total_revenue, average_order_value,
    days_since_last_purchase, purchase_frequency, return_rate,
    discount_usage, customer_lifetime_value

Plus a derived `customer_segment` (New / Regular / Loyal / At-Risk /
Churned / Never Purchased) — deliberately NOT stored in the database
(see sql/schema.sql notes), recomputed here from behavior as of the
dataset's "as of" date (the most recent order date in the data).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_customer_features(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    as_of: pd.Timestamp,
) -> pd.DataFrame:
    # Aggregate order-level behavior per customer
    agg = (
        orders.groupby("customer_id")
        .agg(
            total_orders=("order_id", "count"),
            total_revenue=("gross_revenue", "sum"),
            total_net_revenue=("net_revenue", "sum"),
            total_discount=("total_discount", "sum"),
            total_returned_amount=("total_returned_amount", "sum"),
            return_count=("return_count", "sum"),
            first_purchase_date=("order_date", "min"),
            last_purchase_date=("order_date", "max"),
        )
        .reset_index()
    )

    df = customers[["customer_id", "customer_name", "signup_date", "region_name"]].merge(
        agg, on="customer_id", how="left"
    )

    has_orders = df["total_orders"].notna()
    df["total_orders"] = df["total_orders"].fillna(0).astype(int)
    df["total_revenue"] = df["total_revenue"].fillna(0.0)
    df["total_net_revenue"] = df["total_net_revenue"].fillna(0.0)
    df["total_discount"] = df["total_discount"].fillna(0.0)
    df["total_returned_amount"] = df["total_returned_amount"].fillna(0.0)
    df["return_count"] = df["return_count"].fillna(0).astype(int)

    # average_order_value
    df["average_order_value"] = np.where(
        df["total_orders"] > 0, df["total_revenue"] / df["total_orders"], 0.0
    ).round(2)

    # days_since_last_purchase (NaN for customers who never purchased)
    df["days_since_last_purchase"] = (as_of - df["last_purchase_date"]).dt.days

    # customer_tenure_days: days since signup (as-of date), used for
    # purchase_frequency's denominator so it's a rate, not a raw count
    df["customer_tenure_days"] = (as_of - df["signup_date"]).dt.days.clip(lower=1)

    # purchase_frequency: orders per 30 active days since signup
    df["purchase_frequency"] = (
        df["total_orders"] / df["customer_tenure_days"] * 30
    ).round(4)

    # return_rate: returned order count / total orders placed
    df["return_rate"] = np.where(
        df["total_orders"] > 0, df["return_count"] / df["total_orders"], 0.0
    ).round(4)

    # discount_usage: total discount / (revenue + discount) = effective
    # discount rate this customer received
    pre_discount = df["total_revenue"] + df["total_discount"]
    df["discount_usage"] = np.where(
        pre_discount > 0, df["total_discount"] / pre_discount, 0.0
    ).round(4)

    # customer_lifetime_value (historical, as-of-date CLV — a straightforward
    # "value realized so far" measure). Phase 09/16 builds a more formal
    # forward-looking CLV on top of these same features.
    df["customer_lifetime_value"] = df["total_net_revenue"].round(2)

    df["has_purchased"] = has_orders

    df["customer_segment"] = df.apply(_assign_segment, axis=1)

    cols = [
        "customer_id", "customer_name", "signup_date", "region_name",
        "total_orders", "total_revenue", "total_net_revenue",
        "average_order_value", "days_since_last_purchase",
        "purchase_frequency", "return_rate", "discount_usage",
        "customer_lifetime_value", "customer_segment",
    ]
    return df[cols].rename(columns={"region_name": "region"})


def _assign_segment(row) -> str:
    """Recency/frequency based segmentation.

    Never Purchased : signed up, zero orders
    Churned         : last purchase > 180 days ago
    At-Risk         : last purchase 90-180 days ago
    Loyal           : >= 5 orders and purchased within last 90 days
    New             : exactly 1 order, within last 90 days
    Regular         : everything else active (2-4 orders, within 90 days)
    """
    if row["total_orders"] == 0:
        return "Never Purchased"
    days = row["days_since_last_purchase"]
    if days > 180:
        return "Churned"
    if days > 90:
        return "At-Risk"
    if row["total_orders"] >= 5:
        return "Loyal"
    if row["total_orders"] == 1:
        return "New"
    return "Regular"


def segment_summary(features: pd.DataFrame) -> pd.DataFrame:
    out = (
        features.groupby("customer_segment")
        .agg(
            customers=("customer_id", "count"),
            total_revenue=("total_revenue", "sum"),
            avg_clv=("customer_lifetime_value", "mean"),
            avg_orders=("total_orders", "mean"),
            avg_return_rate=("return_rate", "mean"),
        )
        .reset_index()
    )
    out["pct_of_customers"] = (out["customers"] / out["customers"].sum() * 100).round(2)
    out["avg_clv"] = out["avg_clv"].round(2)
    out["avg_orders"] = out["avg_orders"].round(2)
    out["avg_return_rate"] = out["avg_return_rate"].round(4)
    return out.sort_values("total_revenue", ascending=False)
