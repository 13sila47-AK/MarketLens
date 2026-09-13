"""MarketLens - Phase 16: Recommendations Dashboard (spec section 32)."""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_access import inr, load_recommendations  # noqa: E402

st.set_page_config(page_title="MarketLens | Recommendations", page_icon="\u2705", layout="wide")
st.title("\u2705 Recommendations")
st.caption("Prioritized recommendations, each traced back to the evidence that produced it.")

data = load_recommendations()
recs = data["recommendations"]

impact_df = pd.DataFrame(
    [
        {
            "Priority": r["priority"],
            "Recommendation": r["title"],
            "Incremental Profit": r["expected_impact"]["expected_incremental_profit"],
            "Implementation Cost": r["expected_impact"]["implementation_cost"],
            "ROI (%)": r["expected_impact"]["roi_pct"],
        }
        for r in recs
    ]
)

st.subheader("At a Glance")
fig = px.bar(
    impact_df.sort_values("Priority"),
    x="Recommendation",
    y="Incremental Profit",
    color="Recommendation",
    title="Expected Incremental Profit by Recommendation",
)
st.plotly_chart(fig, use_container_width=True)

disp = impact_df.copy()
disp["Incremental Profit"] = disp["Incremental Profit"].apply(inr)
disp["Implementation Cost"] = disp["Implementation Cost"].apply(inr)
st.dataframe(disp.sort_values("Priority"), use_container_width=True, hide_index=True)

total_profit = impact_df["Incremental Profit"].sum()
total_cost = impact_df["Implementation Cost"].sum()
st.caption(
    f"If all three are funded: {inr(total_profit)} combined incremental profit at "
    f"{inr(total_cost)} cost \u2014 a **simple sum / directional upper bound**, not a "
    "jointly re-modeled scenario, since the levers could interact."
)

st.divider()

for r in sorted(recs, key=lambda x: x["priority"]):
    with st.container(border=True):
        st.markdown(f"### Priority {r['priority']}: {r['title']}")
        st.markdown("**Problem**")
        st.write(r["problem"])
        st.markdown("**Evidence**")
        st.write(r["evidence"])
        st.markdown("**Recommendation**")
        st.write(r["recommendation"])
        st.markdown("**Expected Impact**")
        imp = r["expected_impact"]
        ic1, ic2, ic3, ic4 = st.columns(4)
        if "potential_customers_affected" in imp:
            ic1.metric("Customers Affected", f"{imp['potential_customers_affected']:,}")
        elif "potential_orders_affected" in imp:
            ic1.metric("Orders Affected", str(imp["potential_orders_affected"]))
        ic2.metric("Incremental Profit", inr(imp["expected_incremental_profit"]))
        ic3.metric("Implementation Cost", inr(imp["implementation_cost"]))
        ic4.metric("ROI", f"{imp['roi_pct']:.1f}%")
        st.caption(imp["implementation_cost_assumption"])
        st.markdown("**Risk**")
        st.write(r["risk"])
    st.write("")

if "south_recovery_calculation" in data:
    with st.expander("How the South recovery opportunity was calculated"):
        st.json(data["south_recovery_calculation"])
