"""MarketLens - Phase 16: Marketing Dashboard (spec section 30)."""

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_access import inr, load_kpi  # noqa: E402

st.set_page_config(page_title="MarketLens | Marketing", page_icon="\U0001F4E3", layout="wide")
st.title("\U0001F4E3 Marketing")
st.caption("Campaign spend, conversions, revenue, CAC, and ROI \u2014 compared across campaigns and types.")

campaigns = load_kpi("campaign_performance")
type_summary = load_kpi("campaign_type_summary")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Campaigns", f"{len(campaigns):,}")
k2.metric("Total Spend", inr(campaigns["spend"].sum()))
k3.metric("Total Revenue from Acquired", inr(campaigns["revenue_from_acquired"].sum()))
blended_cac = campaigns["spend"].sum() / campaigns["customers_acquired"].sum()
k4.metric("Blended CAC", f"\u20b9{blended_cac:,.0f}")

st.divider()

st.subheader("Campaign Type Summary")
disp = type_summary.copy()
disp["total_spend"] = disp["total_spend"].apply(inr)
disp["total_revenue_from_acquired"] = disp["total_revenue_from_acquired"].apply(inr)
disp["blended_cac"] = disp["blended_cac"].apply(lambda v: f"\u20b9{v:,.0f}")
st.dataframe(disp, use_container_width=True, hide_index=True)

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("CAC by Campaign Type")
    fig_cac = px.bar(type_summary.sort_values("blended_cac"), x="campaign_type", y="blended_cac", color="campaign_type", title="Blended CAC by Campaign Type")
    st.plotly_chart(fig_cac, use_container_width=True)

with col_b:
    st.subheader("ROI by Campaign Type")
    fig_roi = px.bar(type_summary.sort_values("roi_pct", ascending=False), x="campaign_type", y="roi_pct", color="campaign_type", title="ROI % by Campaign Type")
    st.plotly_chart(fig_roi, use_container_width=True)

st.divider()

st.subheader("Spend vs Revenue by Campaign")
fig_scatter = px.scatter(
    campaigns,
    x="spend",
    y="revenue_from_acquired",
    color="campaign_type",
    size="customers_acquired",
    hover_data=["campaign_id", "cac", "roi_pct"],
    title="Campaign Spend vs Revenue from Acquired Customers (bubble size = customers acquired)",
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.subheader("All Campaigns")
camp_disp = campaigns.sort_values("roi_pct", ascending=False).copy()
camp_disp["spend"] = camp_disp["spend"].apply(inr)
camp_disp["revenue_from_acquired"] = camp_disp["revenue_from_acquired"].apply(inr)
st.dataframe(camp_disp, use_container_width=True, hide_index=True)

st.caption(
    "Note (Phase 08): marketing spend and campaign type were NOT found to statistically "
    "predict performance at this sample size \u2014 read campaign-level ROI differences with "
    "that caution in mind."
)
