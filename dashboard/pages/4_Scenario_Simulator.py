"""MarketLens - Phase 16: Scenario Simulator (spec sections 21-22, 31)."""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_access import inr, load_scenario_comparison  # noqa: E402
from scenario_model import BASELINE, simulate  # noqa: E402

st.set_page_config(page_title="MarketLens | Scenario Simulator", page_icon="\U0001F52E", layout="wide")
st.title("\U0001F52E Scenario Simulator")
st.caption(
    "Move any lever below to see projected Revenue, Profit, Margin, ROI, and Incremental "
    "Value \u2014 built on the exact same verified baseline and methodology as Phase 12's fixed scenarios."
)

st.sidebar.header("Presets (Phase 12 fixed scenarios)")
preset = st.sidebar.radio(
    "Load a preset",
    ["Custom", "Current (baseline)", "Retention +5pp", "Discount -2pp", "Marketing +25%"],
    index=0,
)

preset_defaults = {
    "Current (baseline)": dict(retention=0.0, discount=0.0, marketing=0.0, price=0.0, conversion=0.0, acquisition=0.0, return_rate=0.0),
    "Retention +5pp": dict(retention=5.0, discount=0.0, marketing=0.0, price=0.0, conversion=0.0, acquisition=0.0, return_rate=0.0),
    "Discount -2pp": dict(retention=0.0, discount=2.0, marketing=0.0, price=0.0, conversion=0.0, acquisition=0.0, return_rate=0.0),
    "Marketing +25%": dict(retention=0.0, discount=0.0, marketing=25.0, price=0.0, conversion=0.0, acquisition=0.0, return_rate=0.0),
    "Custom": dict(retention=0.0, discount=0.0, marketing=0.0, price=0.0, conversion=0.0, acquisition=0.0, return_rate=0.0),
}
d = preset_defaults[preset]

st.subheader("Levers")
c1, c2, c3, c4 = st.columns(4)
retention_pp = c1.slider("Retention (+pp)", -5.0, 15.0, d["retention"], 0.5, help="Avg. monthly retention rate, currently 12.4%. Applied to repeat-purchase revenue only.")
discount_pp = c2.slider("Discount reduction (-pp)", -5.0, 10.0, d["discount"], 0.5, help="Reduces the discount rate, currently 13.44%.")
marketing_pct = c3.slider("Marketing spend change (%)", -50.0, 100.0, d["marketing"], 5.0, help="Applied with 0.7 diminishing-returns elasticity on new customers acquired.")
price_pct = c4.slider("Price change (%)", -20.0, 20.0, d["price"], 1.0, help="Direct revenue pass-through at the same unit volume (no demand-elasticity modeled).")

c5, c6, c7 = st.columns(3)
conversion_pp = c5.slider("Conversion rate (+pp)", -5.0, 10.0, d["conversion"], 0.5, help="Reference metric only \u2014 does not itself move revenue/cost in this model (see page notes).")
acquisition_pct = c6.slider("Customer acquisition efficiency (%)", -30.0, 60.0, d["acquisition"], 5.0, help="Extra customers acquired at the SAME marketing spend (e.g. a funnel-efficiency improvement).")
return_rate_pp = c7.slider("Return rate reduction (-pp)", -3.0, 5.0, d["return_rate"], 0.25, help="Reduces the return rate, currently 7.18%, scaling the return-cost opex line.")

result = simulate(
    retention_delta_pp=retention_pp / 100.0,
    discount_delta_pp=discount_pp / 100.0,
    marketing_pct_change=marketing_pct,
    price_pct_change=price_pct,
    conversion_delta_pp=conversion_pp,
    acquisition_pct_change=acquisition_pct,
    return_rate_delta_pp=return_rate_pp / 100.0,
)
current = simulate()

st.divider()
st.subheader("Projected Results")

r1, r2, r3, r4, r5 = st.columns(5)
r1.metric("Projected Revenue", inr(result["gross_revenue"]), delta=inr(result["gross_revenue"] - current["gross_revenue"]))
r2.metric("Projected Net Profit", inr(result["net_profit"]), delta=inr(result["net_profit"] - current["net_profit"]))
r3.metric("Projected Net Margin", f"{result['net_margin_pct']:.2f}%", delta=f"{result['net_margin_pct'] - current['net_margin_pct']:.2f} pp")
r4.metric("Marketing ROI", f"{result['marketing_roi_pct']:.1f}%")
r5.metric("Incremental Value vs Current", inr(result["incremental_value_vs_current"]))

st.divider()

st.subheader("Scenario vs Current Baseline")
compare_df = pd.DataFrame(
    [
        {"Metric": "Gross Revenue", "Current": current["gross_revenue"], "Scenario": result["gross_revenue"]},
        {"Metric": "Gross Profit", "Current": current["gross_profit"], "Scenario": result["gross_profit"]},
        {"Metric": "Net Profit", "Current": current["net_profit"], "Scenario": result["net_profit"]},
        {"Metric": "Total OpEx", "Current": current["total_opex"], "Scenario": result["total_opex"]},
    ]
)
fig = px.bar(compare_df.melt(id_vars="Metric", var_name="Case", value_name="Amount"), x="Metric", y="Amount", color="Case", barmode="group", title="Current vs Scenario")
st.plotly_chart(fig, use_container_width=True)

with st.expander("See full computed breakdown"):
    st.json(result)

st.divider()

st.subheader("Reference: Phase 12's Fixed Scenarios")
st.caption("The four scenarios the frozen spec requires (section 22), pre-computed and verified in Phase 12 \u2014 shown here for comparison against whatever you've set above.")
fixed = load_scenario_comparison()
fixed_disp = fixed.copy()
for col in ["gross_revenue", "cogs", "gross_profit", "net_profit", "incremental_value_vs_current"]:
    fixed_disp[col] = fixed_disp[col].apply(inr)
fixed_disp["gross_margin_pct"] = fixed["gross_margin_pct"].round(2)
fixed_disp["net_margin_pct"] = fixed["net_margin_pct"].round(2)
st.dataframe(
    fixed_disp[["scenario", "gross_revenue", "net_profit", "net_margin_pct", "incremental_value_vs_current"]],
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Assumptions: price and discount changes don't affect unit volume/cost (no demand-elasticity "
    "modeled); when multiple levers are moved together their effects combine additively, not "
    "as a jointly re-fitted model \u2014 same caveat Phase 14 used for its combined recommendation total."
)
