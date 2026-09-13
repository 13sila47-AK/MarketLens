"""MarketLens - Phase 16: Revenue Diagnostics (spec section 28)."""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_access import load_customer_features, load_kpi, load_order_items_enriched  # noqa: E402

st.set_page_config(page_title="MarketLens | Revenue Diagnostics", page_icon="\U0001F4C8", layout="wide")
st.title("\U0001F4C8 Revenue Diagnostics")
st.caption("Revenue over time, by region, by product, and by customer segment \u2014 filterable.")

items = load_order_items_enriched()
cust = load_customer_features()[["customer_id", "customer_segment"]]
items = items.merge(cust, on="customer_id", how="left")

# ---------------------------------------------------------------------------
# Filters (spec: "Allow the user to inspect: Region, Product, Customer
# Segment, Time")
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")
regions = st.sidebar.multiselect("Region", sorted(items["region"].dropna().unique()), default=None)
categories = st.sidebar.multiselect("Product Category", sorted(items["category"].dropna().unique()), default=None)
segments = st.sidebar.multiselect("Customer Segment", sorted(items["customer_segment"].dropna().unique()), default=None)
min_date, max_date = items["order_date"].min(), items["order_date"].max()
date_range = st.sidebar.date_input("Date Range", value=(min_date.date(), max_date.date()), min_value=min_date.date(), max_value=max_date.date())

filtered = items.copy()
if regions:
    filtered = filtered[filtered["region"].isin(regions)]
if categories:
    filtered = filtered[filtered["category"].isin(categories)]
if segments:
    filtered = filtered[filtered["customer_segment"].isin(segments)]
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    filtered = filtered[(filtered["order_date"] >= start) & (filtered["order_date"] <= end)]

st.caption(f"Showing {len(filtered):,} of {len(items):,} order line items after filters.")

if filtered.empty:
    st.warning("No data matches the current filters.")
    st.stop()

k1, k2, k3 = st.columns(3)
k1.metric("Filtered Revenue", f"\u20b9{filtered['revenue'].sum() / 1e7:.2f} Cr")
k2.metric("Filtered Units", f"{int(filtered['quantity'].sum()):,}")
k3.metric("Filtered Orders", f"{filtered['order_id'].nunique():,}")

st.divider()

# ---------------------------------------------------------------------------
# Revenue over time
# ---------------------------------------------------------------------------
st.subheader("Revenue Over Time")
monthly = filtered.copy()
monthly["month"] = monthly["order_date"].dt.to_period("M").astype(str)
monthly_rev = monthly.groupby("month", as_index=False)["revenue"].sum()
fig_time = px.line(monthly_rev, x="month", y="revenue", markers=True, title="Monthly Revenue (Filtered)")
fig_time.update_layout(yaxis_title="Revenue (\u20b9)", xaxis_title="Month")
st.plotly_chart(fig_time, use_container_width=True)

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Revenue by Region")
    region_rev = filtered.groupby("region", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)
    fig_region = px.bar(region_rev, x="region", y="revenue", color="region", title="Revenue by Region (Filtered)")
    st.plotly_chart(fig_region, use_container_width=True)

with col_b:
    st.subheader("Revenue by Product Category")
    cat_rev = filtered.groupby("category", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)
    fig_cat = px.bar(cat_rev, x="category", y="revenue", color="category", title="Revenue by Category (Filtered)")
    st.plotly_chart(fig_cat, use_container_width=True)

st.subheader("Revenue by Customer Segment")
seg_rev = filtered.groupby("customer_segment", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)
fig_seg = px.bar(seg_rev, x="customer_segment", y="revenue", color="customer_segment", title="Revenue by Customer Segment (Filtered)")
st.plotly_chart(fig_seg, use_container_width=True)

st.divider()

st.subheader("Unfiltered Reference: Regional YoY Trend (Phase 07)")
st.caption("Full-dataset regional trend (not affected by filters above) \u2014 South's 2025 decline vs North/Central growth.")
trend = load_kpi("revenue_by_region_trend")
st.dataframe(trend, use_container_width=True, hide_index=True)
