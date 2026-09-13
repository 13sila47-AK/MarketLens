"""
MarketLens - Phase 07: Product KPIs
=====================================
Best sellers, low-margin products, high-growth products, declining
products — all computed from order_items_enriched.csv (item grain, has
product cost/price/category attached).
"""

from __future__ import annotations

import pandas as pd


def product_performance(order_items: pd.DataFrame) -> pd.DataFrame:
    items = order_items.copy()
    items["item_cogs"] = items["quantity"] * items["cost"]
    items["item_profit"] = items["revenue"] - items["item_cogs"]

    out = (
        items.groupby(["product_id", "product_name", "category"])
        .agg(
            revenue=("revenue", "sum"),
            units_sold=("quantity", "sum"),
            orders=("order_id", "nunique"),
            cogs=("item_cogs", "sum"),
            profit=("item_profit", "sum"),
        )
        .reset_index()
    )
    out["margin_pct"] = (out["profit"] / out["revenue"] * 100).round(2)
    return out


def top_products(order_items: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    perf = product_performance(order_items)
    return perf.sort_values("revenue", ascending=False).head(n)


def low_margin_products(order_items: pd.DataFrame, n: int = 10, min_revenue: float = 10000) -> pd.DataFrame:
    """Lowest-margin products among those with meaningful revenue (so a
    barely-sold product with one discounted unit doesn't dominate)."""
    perf = product_performance(order_items)
    meaningful = perf[perf["revenue"] >= min_revenue]
    return meaningful.sort_values("margin_pct", ascending=True).head(n)


def product_growth_yoy(order_items: pd.DataFrame) -> pd.DataFrame:
    """Revenue by product by year with YoY growth — the basis for
    high-growth / declining product classification below."""
    items = order_items.copy()
    items["year"] = items["order_date"].dt.year
    pivot = items.pivot_table(
        index=["product_id", "product_name", "category"],
        columns="year", values="revenue", aggfunc="sum",
    ).fillna(0)
    years = sorted(pivot.columns)
    if len(years) >= 2:
        latest, prior = years[-1], years[-2]
        pivot["latest_yoy_growth_pct"] = (
            (pivot[latest] - pivot[prior]) / pivot[prior].replace(0, pd.NA) * 100
        ).round(2)
    return pivot.reset_index()


def high_growth_products(order_items: pd.DataFrame, n: int = 10, min_revenue: float = 10000) -> pd.DataFrame:
    growth = product_growth_yoy(order_items)
    perf = product_performance(order_items)[["product_id", "revenue"]]
    merged = growth.merge(perf, on="product_id", how="left")
    meaningful = merged[merged["revenue"] >= min_revenue].dropna(subset=["latest_yoy_growth_pct"])
    return meaningful.sort_values("latest_yoy_growth_pct", ascending=False).head(n)


def declining_products(order_items: pd.DataFrame, n: int = 10, min_revenue: float = 10000) -> pd.DataFrame:
    growth = product_growth_yoy(order_items)
    perf = product_performance(order_items)[["product_id", "revenue"]]
    merged = growth.merge(perf, on="product_id", how="left")
    meaningful = merged[merged["revenue"] >= min_revenue].dropna(subset=["latest_yoy_growth_pct"])
    return meaningful.sort_values("latest_yoy_growth_pct", ascending=True).head(n)


def category_performance(order_items: pd.DataFrame) -> pd.DataFrame:
    items = order_items.copy()
    items["item_cogs"] = items["quantity"] * items["cost"]
    items["item_profit"] = items["revenue"] - items["item_cogs"]
    out = (
        items.groupby("category")
        .agg(revenue=("revenue", "sum"), units_sold=("quantity", "sum"),
             profit=("item_profit", "sum"))
        .reset_index()
    )
    out["margin_pct"] = (out["profit"] / out["revenue"] * 100).round(2)
    return out.sort_values("revenue", ascending=False)
