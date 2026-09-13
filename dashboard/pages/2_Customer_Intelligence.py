"""MarketLens - Phase 16: Customer Intelligence (spec section 29)."""

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_access import (  # noqa: E402
    inr,
    load_churn_model_comparison,
    load_customer_quadrants,
    load_kpi,
)

st.set_page_config(page_title="MarketLens | Customer Intelligence", page_icon="\U0001F465", layout="wide")
st.title("\U0001F465 Customer Intelligence")
st.caption("Churn risk, customer lifetime value, and retention \u2014 who is most valuable and most at risk.")

quad = load_customer_quadrants()
model_info = load_churn_model_comparison()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Scored Customers", f"{len(quad):,}")
k2.metric("High-Risk Customers", f"{(quad['risk_segment'] == 'High').sum():,}")
hv_hr = quad[quad["quadrant"] == "High Value / High Risk"]
k3.metric("High Value + High Risk", f"{len(hv_hr):,}")
k4.metric("CLV at Risk (this segment)", inr(hv_hr["customer_lifetime_value_to_date"].sum()))

st.caption(
    f"Best churn model: **{model_info['best_model'].replace('_', ' ').title()}** "
    f"(ROC-AUC {model_info['results'][model_info['best_model']]['roc_auc']:.3f}, "
    f"F1 {model_info['results'][model_info['best_model']]['f1']:.3f}). "
    f"Training-set churn rate: {model_info['class_balance_train_churn_rate'] * 100:.1f}%."
)

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Churn Probability Distribution")
    fig_hist = px.histogram(quad, x="churn_probability", nbins=30, color="risk_segment", title="Churn Probability by Risk Segment")
    st.plotly_chart(fig_hist, use_container_width=True)

with col_b:
    st.subheader("CLV vs Churn Risk")
    sample = quad.sample(min(5000, len(quad)), random_state=42)
    fig_scatter = px.scatter(
        sample,
        x="churn_probability",
        y="customer_lifetime_value_to_date",
        color="quadrant",
        opacity=0.5,
        title="Customer Lifetime Value vs Churn Probability (5,000-customer sample)",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

st.subheader("Value \u00d7 Risk Quadrants")
quad_summary = (
    quad.groupby("quadrant")
    .agg(customers=("customer_id", "count"), total_clv=("customer_lifetime_value_to_date", "sum"))
    .reset_index()
)
quad_summary["pct_of_clv"] = (quad_summary["total_clv"] / quad_summary["total_clv"].sum() * 100).round(1)
quad_summary["total_clv_display"] = quad_summary["total_clv"].apply(inr)

fig_quad = px.bar(quad_summary, x="quadrant", y="customers", color="quadrant", title="Customers per Quadrant")
st.plotly_chart(fig_quad, use_container_width=True)
st.dataframe(
    quad_summary[["quadrant", "customers", "total_clv_display", "pct_of_clv"]].rename(
        columns={"total_clv_display": "total_clv", "pct_of_clv": "pct_of_clv (%)"}
    ),
    use_container_width=True,
    hide_index=True,
)

st.info(
    f"\U0001F3AF **Priority segment \u2014 High Value / High Risk**: {len(hv_hr):,} customers hold "
    f"{inr(hv_hr['customer_lifetime_value_to_date'].sum())} "
    f"({quad_summary.loc[quad_summary['quadrant'] == 'High Value / High Risk', 'pct_of_clv'].values[0]}% of total CLV) "
    "at risk \u2014 the group Phase 14's #1 recommendation targets first."
)

st.divider()

st.subheader("Monthly Retention Trend")
retention = load_kpi("monthly_retention")
fig_ret = px.line(retention, x="month", y="retention_rate_pct", markers=True, title="Month-over-Month Customer Retention Rate")
fig_ret.update_layout(yaxis_title="Retention Rate (%)")
st.plotly_chart(fig_ret, use_container_width=True)
st.caption("Retention declined from ~16% to ~12% over 3 years (statistically confirmed, p=9.5e-12). See Business Diagnosis.")
