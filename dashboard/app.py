"""
MarketLens - Phase 16: Streamlit Dashboard
============================================
Main entry point / Executive Overview page (spec section 26-27).

Run with:
    streamlit run dashboard/app.py

Every number on this page is read from an already-verified Phase 07/11/13
output file via dashboard/data_access.py -- nothing here is recomputed.
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_access import executive_summary, inr, load_kpi  # noqa: E402

st.set_page_config(page_title="MarketLens | Executive Overview", page_icon="\U0001F4CA", layout="wide")

st.title("\U0001F4CA MarketLens")
st.caption("AI-Powered Business Growth & Decision Intelligence Platform \u2014 UrbanCart FY2023\u2013FY2025")

summary = executive_summary()

st.header("Executive Overview")

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Revenue (FY2025)", inr(summary["revenue_2025"]))
col2.metric("Net Profit (FY2025)", inr(summary["net_profit_2025"]))
col3.metric("Net Margin", f"{summary['net_margin_pct_2025']:.1f}%")
col4.metric("Total Customers", f"{summary['total_customers']:,}")
col5.metric("Revenue Growth (YoY)", f"{summary['revenue_growth_pct']:.1f}%", delta=f"{summary['revenue_growth_pct']:.1f}%")
col6.metric("Gross Profit Growth (YoY)", f"{summary['profit_growth_pct']:.1f}%", delta=f"{summary['profit_growth_pct']:.1f}%")

st.caption(
    "Revenue growth decelerated sharply from +97.8% (2023\u21922024) to "
    f"+{summary['revenue_growth_pct']:.1f}% (2024\u21922025) \u2014 the central "
    "finding driving this whole diagnosis. See **Revenue Diagnostics**."
)

st.divider()

st.subheader("Top Issues Management Should Know About")

issue_col1, issue_col2, issue_col3 = st.columns(3)

with issue_col1:
    st.markdown("##### \U0001F53B Top Business Issue")
    issue = summary["top_business_issue"]
    st.markdown(f"**{issue['finding']}**")
    st.caption(issue["evidence"])

with issue_col2:
    st.markdown("##### \U0001F5FA\uFE0F Top Region Issue")
    issue = summary["top_region_issue"]
    st.markdown(f"**{issue['finding']}**")
    st.caption(issue["evidence"])

with issue_col3:
    st.markdown("##### \U0001F465 Top Customer Issue")
    ci = summary["top_customer_issue"]
    st.markdown(
        f"**{ci['priority_segment_customers']:,} High-Value + High-Risk customers** "
        f"hold {inr(ci['priority_segment_clv'])} ({ci['priority_segment_clv_pct']}% of total CLV) at risk."
    )
    st.caption(f"Company-wide churn model AUC: {ci['model_auc']:.3f} \u2014 modest but directionally useful.")

st.divider()

st.subheader("Top Recommendation")
rec = summary["top_recommendation"]
with st.container(border=True):
    st.markdown(f"**Priority {rec['priority']}: {rec['title']}**")
    st.write(rec["problem"])
    imp = rec["expected_impact"]
    rcol1, rcol2, rcol3 = st.columns(3)
    rcol1.metric("Expected Incremental Profit", inr(imp["expected_incremental_profit"]))
    rcol2.metric("Implementation Cost", inr(imp["implementation_cost"]))
    rcol3.metric("ROI", f"{imp['roi_pct']:.1f}%")
    st.caption("See the **Recommendations** page for all 3 prioritized recommendations.")

st.divider()

st.subheader("Revenue Trend (FY2023\u2013FY2025)")
monthly = load_kpi("revenue_by_month")
st.line_chart(monthly.set_index("month")["gross_revenue"])

st.caption(
    "Use the sidebar to navigate: Revenue Diagnostics \u00b7 Customer Intelligence \u00b7 "
    "Marketing \u00b7 Scenario Simulator \u00b7 Recommendations \u00b7 Ask MarketLens."
)
