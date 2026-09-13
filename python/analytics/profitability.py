"""
MarketLens - Phase 07: Profitability KPIs
===========================================
Gross profit, margin, contribution margin, cost per order, and the revenue
impact of discounts and returns.

COGS (cost of goods sold) is computed at the item grain as
`quantity * cost` (product.cost, the wholesale/production cost — distinct
from `unit_price`, the price charged). This isn't available pre-aggregated
in orders_enriched.csv, so profitability functions take order_items as
input, or a pre-aggregated per-order COGS table (see `cogs_by_order`).
"""

from __future__ import annotations

import pandas as pd


def cogs_by_order(order_items: pd.DataFrame) -> pd.DataFrame:
    """Cost of goods sold, aggregated to the order grain."""
    items = order_items.copy()
    items["item_cogs"] = items["quantity"] * items["cost"]
    return (
        items.groupby("order_id")
        .agg(cogs=("item_cogs", "sum"))
        .reset_index()
    )


def profitability_summary(orders: pd.DataFrame, order_items: pd.DataFrame) -> dict:
    cogs = cogs_by_order(order_items)
    merged = orders.merge(cogs, on="order_id", how="left")
    merged["cogs"] = merged["cogs"].fillna(0)

    gross_revenue = float(merged["gross_revenue"].sum())
    net_revenue = float(merged["net_revenue"].sum())
    total_cogs = float(merged["cogs"].sum())
    total_variable_cost = float(merged["total_cost"].sum())  # shipping + operational
    total_discount = float(merged["total_discount"].sum())
    total_returned = float(merged["total_returned_amount"].sum())

    gross_profit = gross_revenue - total_cogs
    gross_margin_pct = (gross_profit / gross_revenue * 100) if gross_revenue else 0.0

    contribution_margin = net_revenue - total_cogs - total_variable_cost
    contribution_margin_pct = (contribution_margin / net_revenue * 100) if net_revenue else 0.0

    n_orders = len(merged)
    cost_per_order = total_variable_cost / n_orders if n_orders else 0.0

    # discount_impact: discount as a % of what revenue would have been
    # without it (gross_revenue is already net of discount, so pre-discount
    # value = gross_revenue + total_discount)
    pre_discount_revenue = gross_revenue + total_discount
    discount_impact_pct = (total_discount / pre_discount_revenue * 100) if pre_discount_revenue else 0.0

    # return_impact: returned amount as a % of gross revenue
    return_impact_pct = (total_returned / gross_revenue * 100) if gross_revenue else 0.0

    return {
        "gross_revenue": round(gross_revenue, 2),
        "net_revenue": round(net_revenue, 2),
        "cogs": round(total_cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin_pct": round(gross_margin_pct, 2),
        "total_variable_cost": round(total_variable_cost, 2),
        "contribution_margin": round(contribution_margin, 2),
        "contribution_margin_pct": round(contribution_margin_pct, 2),
        "cost_per_order": round(cost_per_order, 2),
        "total_discount_given": round(total_discount, 2),
        "discount_impact_pct": round(discount_impact_pct, 2),
        "total_returned_amount": round(total_returned, 2),
        "return_impact_pct": round(return_impact_pct, 2),
    }


def gross_margin_trend_yoy(orders: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
    """Gross margin % by year — this is where margin compression (rising
    discount rate + rising return rate) becomes visible over time."""
    cogs = cogs_by_order(order_items)
    merged = orders.merge(cogs, on="order_id", how="left")
    merged["cogs"] = merged["cogs"].fillna(0)
    merged["year"] = merged["order_date"].dt.year

    out = (
        merged.groupby("year")
        .agg(gross_revenue=("gross_revenue", "sum"),
             cogs=("cogs", "sum"),
             total_discount=("total_discount", "sum"),
             total_returned=("total_returned_amount", "sum"))
        .reset_index()
    )
    out["gross_profit"] = out["gross_revenue"] - out["cogs"]
    out["gross_margin_pct"] = (out["gross_profit"] / out["gross_revenue"] * 100).round(2)
    pre_discount = out["gross_revenue"] + out["total_discount"]
    out["discount_rate_pct"] = (out["total_discount"] / pre_discount * 100).round(2)
    out["return_rate_pct"] = (out["total_returned"] / out["gross_revenue"] * 100).round(2)
    return out[["year", "gross_revenue", "cogs", "gross_profit", "gross_margin_pct",
                "discount_rate_pct", "return_rate_pct"]]


def profitability_by_region(orders: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
    cogs = cogs_by_order(order_items)
    merged = orders.merge(cogs, on="order_id", how="left")
    merged["cogs"] = merged["cogs"].fillna(0)

    out = (
        merged.groupby("region")
        .agg(gross_revenue=("gross_revenue", "sum"), cogs=("cogs", "sum"),
             total_variable_cost=("total_cost", "sum"))
        .reset_index()
    )
    out["gross_profit"] = out["gross_revenue"] - out["cogs"]
    out["gross_margin_pct"] = (out["gross_profit"] / out["gross_revenue"] * 100).round(2)
    return out.sort_values("gross_margin_pct")
