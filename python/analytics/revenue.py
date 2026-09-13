"""
MarketLens - Phase 07: Revenue KPIs
====================================
Total revenue, growth (MoM/YoY), and revenue breakdowns by region, product
category, and customer segment.

All figures use `gross_revenue` at the order grain (= sum of item-level
`revenue`, which is already net of discount — see order_items.revenue =
quantity * unit_price - discount) unless explicitly noted as "net of
returns" (net_revenue = gross_revenue - total_returned_amount).
"""

from __future__ import annotations

import pandas as pd


def total_revenue(orders: pd.DataFrame) -> dict:
    return {
        "gross_revenue": round(float(orders["gross_revenue"].sum()), 2),
        "net_revenue": round(float(orders["net_revenue"].sum()), 2),
        "total_discount_given": round(float(orders["total_discount"].sum()), 2),
        "total_returned_amount": round(float(orders["total_returned_amount"].sum()), 2),
        "total_orders": int(len(orders)),
    }


def revenue_by_month(orders: pd.DataFrame) -> pd.DataFrame:
    df = orders.copy()
    df["month"] = df["order_date"].dt.to_period("M").astype(str)
    out = (
        df.groupby("month")
        .agg(gross_revenue=("gross_revenue", "sum"), orders=("order_id", "count"))
        .reset_index()
        .sort_values("month")
    )
    out["mom_growth_pct"] = out["gross_revenue"].pct_change().mul(100).round(2)
    return out


def revenue_growth_yoy(orders: pd.DataFrame) -> pd.DataFrame:
    df = orders.copy()
    df["year"] = df["order_date"].dt.year
    out = (
        df.groupby("year")
        .agg(gross_revenue=("gross_revenue", "sum"), orders=("order_id", "count"))
        .reset_index()
        .sort_values("year")
    )
    out["yoy_growth_pct"] = out["gross_revenue"].pct_change().mul(100).round(2)
    return out


def revenue_by_region(orders: pd.DataFrame) -> pd.DataFrame:
    out = (
        orders.groupby("region")
        .agg(gross_revenue=("gross_revenue", "sum"), orders=("order_id", "count"),
             customers=("customer_id", "nunique"))
        .reset_index()
        .sort_values("gross_revenue", ascending=False)
    )
    out["pct_of_total"] = (out["gross_revenue"] / out["gross_revenue"].sum() * 100).round(2)
    return out


def revenue_by_region_trend_yoy(orders: pd.DataFrame) -> pd.DataFrame:
    """Region x year revenue with YoY growth per region — this is where the
    South-region decline (a core business-case signal) becomes visible."""
    df = orders.copy()
    df["year"] = df["order_date"].dt.year
    pivot = df.pivot_table(index="region", columns="year", values="gross_revenue", aggfunc="sum")
    growth = pivot.pct_change(axis=1).mul(100).round(2)
    growth.columns = [f"{c}_yoy_growth_pct" for c in growth.columns]
    combined = pivot.join(growth).reset_index()
    return combined


def revenue_by_category(order_items: pd.DataFrame) -> pd.DataFrame:
    out = (
        order_items.groupby("category")
        .agg(revenue=("revenue", "sum"), units=("quantity", "sum"),
             order_items=("order_item_id", "count"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    out["pct_of_total"] = (out["revenue"] / out["revenue"].sum() * 100).round(2)
    return out


def revenue_by_channel(orders: pd.DataFrame) -> pd.DataFrame:
    out = (
        orders.groupby("channel")
        .agg(gross_revenue=("gross_revenue", "sum"), orders=("order_id", "count"))
        .reset_index()
        .sort_values("gross_revenue", ascending=False)
    )
    out["pct_of_total"] = (out["gross_revenue"] / out["gross_revenue"].sum() * 100).round(2)
    return out


def revenue_by_segment(orders_with_segment: pd.DataFrame) -> pd.DataFrame:
    """Requires an orders dataframe merged with customer_segment (see
    customer_features.py — this KPI depends on segmentation)."""
    out = (
        orders_with_segment.groupby("customer_segment")
        .agg(gross_revenue=("gross_revenue", "sum"), orders=("order_id", "count"),
             customers=("customer_id", "nunique"))
        .reset_index()
        .sort_values("gross_revenue", ascending=False)
    )
    out["pct_of_total"] = (out["gross_revenue"] / out["gross_revenue"].sum() * 100).round(2)
    return out
