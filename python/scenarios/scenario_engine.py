"""
Phase 12 — Scenario Analysis (Scenario Engine)
================================================

Computes the four FIXED scenarios required by the spec (section 22):

    1. Current            — baseline, no change
    2. Retention +5pp      — Average Monthly Retention Rate +5 percentage points
    3. Discount -2pp       — Discount Rate reduced by 2 percentage points
    4. Marketing increase  — Marketing Spend increased (with a documented,
                              non-linear acquisition-elasticity assumption,
                              since the spec does not fix an exact % for this one)

Every input value is pulled from the SAME verified sources Phase 07-11 already
used (excel/business_model.xlsx "Assumptions" sheet, cross-checked against
data/processed/*.csv). No number here is invented — where a scenario requires
a modeling assumption beyond "what changes when X moves", that assumption is
stated explicitly in SCENARIO_METHODOLOGY and printed in the report, not
buried in code.

Honesty note (data quality catch): the Assumptions sheet's "Total Orders
(FY2025)" cell (30,895) does not match the real FY2025 order count in
data/raw/orders.csv / orders_enriched.csv (36,459 — verified two independent
ways: distinct order_id count, and sum of data/processed/kpi_revenue_by_month.csv
for the 12 months of 2025). This looks like a Phase 11 filter bug. It does NOT
affect Gross Revenue (367,924,999.78, which matches exactly) or any Financial
Model formula, since no Phase 11 output formula references Total Orders. This
script uses the verified 36,459 figure directly from the raw data wherever an
order count / order-level split is needed, and flags the stale Assumptions
cell for correction rather than silently propagating it.
"""

import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

# ---------------------------------------------------------------------------
# 1. BASELINE — pulled directly from excel/business_model.xlsx "Assumptions"
#    (Phase 11, itself sourced from Phase 07's kpi_*.csv files). Hardcoded
#    here as verified constants (not re-read from the workbook) so this
#    script has no runtime dependency on openpyxl to execute the model;
#    run_scenarios.py separately re-opens the workbook and asserts these
#    match before writing anything, so drift would be caught, not hidden.
# ---------------------------------------------------------------------------

BASELINE = {
    "gross_revenue": 367_924_999.78,
    "cogs": 259_501_256.23,
    "shipping_cost": 5_326_939.64,
    "operational_cost": 29_675_843.83,
    "return_amount": 26_193_002.54,
    "marketing_spend": 6_536_583.30,
    "customers_targeted": 227_104,
    "customers_converted": 6_508,
    "customers_acquired": 5_885,
    "revenue_from_acquired": 47_847_409.34,
    "avg_monthly_retention": 0.124,
    "discount_rate": 0.1344,
    "return_rate": 0.0718,
}

SCENARIO_METHODOLOGY = {
    "current": (
        "No change. Baseline FY2025 run-rate, as verified in Phase 11."
    ),
    "retention_improvement": (
        "Average Monthly Retention Rate +5 percentage points (12.4% -> 17.4%), "
        "the fixed lever from spec section 22. Retention governs REPEAT "
        "purchasing, not first-time acquisition, so the uplift is applied only "
        "to FY2025 revenue from orders that were NOT a customer's first-ever "
        "order (computed directly from orders_enriched.csv + full order "
        "history: repeat-order revenue = Rs 264,308,263 of the Rs 367,924,999.78 "
        "FY2025 total; new-order revenue = Rs 103,616,736, held fixed). The "
        "uplift factor is the direct ratio of new to old retention "
        "(17.4/12.4 = 1.4032x) applied to that repeat-revenue base. Variable "
        "costs (COGS, shipping, operational, returns) scale with the resulting "
        "revenue growth ratio, since higher repeat volume drives proportionally "
        "more units shipped and handled. Marketing spend is held fixed (this "
        "scenario is not a marketing lever)."
    ),
    "discount_reduction": (
        "Discount Rate -2 percentage points (13.44% -> 11.44%), the fixed lever "
        "from spec section 22. Gross Revenue in this dataset is already net of "
        "discount (i.e. what the customer actually paid), so the pre-discount "
        "list value is backed out as gross_revenue / (1 - discount_rate), then "
        "re-applied at the lower discount rate to get the new realized revenue "
        "at the SAME order volume. COGS, shipping, operational cost and returns "
        "are held at their baseline absolute values, because these are driven "
        "by units sold and cost-of-goods, not by the price/discount charged to "
        "the customer -- reducing a discount does not change what a unit costs "
        "to source or ship. Marketing spend unchanged. Caveat stated in the "
        "report: this does not model any secondary effect discount changes "
        "might have on order volume or on the discount<->return correlation "
        "Phase 08 found -- doing so would require a price-elasticity estimate "
        "this dataset cannot support without inventing one."
    ),
    "marketing_increase": (
        "The spec (section 22) only says 'Increase marketing investment' with "
        "no fixed percentage, unlike the other two levers. This scenario "
        "assumes a +25% increase in Marketing Spend (Rs 6,536,583 -> "
        "Rs 8,170,729), applied with a documented DIMINISHING-RETURNS "
        "elasticity of 0.7 on customers acquired (new_acquired = "
        "old_acquired * (1.25)^0.7), rather than assuming naive 1:1 linear "
        "scaling -- real-world marketing spend does not convert to new "
        "customers at a constant rate, and assuming it does would silently "
        "inflate this scenario's ROI. Revenue per acquired customer is held "
        "at the FY2025 baseline (Rs 47,847,409 / 5,885 = Rs 8,131.94/customer). "
        "The resulting incremental acquired-customer revenue is added to the "
        "FY2025 baseline; incremental variable costs (COGS, shipping, "
        "operational, returns) scale with that incremental revenue at the "
        "baseline blended variable-cost ratio."
    ),
}

MARKETING_SPEND_INCREASE_PCT = 0.25
MARKETING_ACQUISITION_ELASTICITY = 0.7
RETENTION_DELTA_PP = 0.05
DISCOUNT_DELTA_PP = 0.02


def load_fy2025_new_vs_repeat_revenue():
    """
    Independently recompute (not re-use a prior cached number) the FY2025
    split between 'new customer first order' revenue and 'repeat order'
    revenue, straight from orders_enriched.csv + full order history.
    Returns (new_order_revenue, repeat_order_revenue, verified_total).
    """
    orders = pd.read_csv(DATA_PROCESSED / "orders_enriched.csv", parse_dates=["order_date"])
    orders_2025 = orders[orders["order_date"].dt.year == 2025].copy()

    first_order = orders.groupby("customer_id")["order_date"].min().rename("first_order_date")
    orders_2025 = orders_2025.merge(first_order, on="customer_id", how="left")
    orders_2025["is_new_order"] = orders_2025["order_date"] == orders_2025["first_order_date"]

    new_rev = float(orders_2025.loc[orders_2025["is_new_order"], "gross_revenue"].sum())
    repeat_rev = float(orders_2025.loc[~orders_2025["is_new_order"], "gross_revenue"].sum())
    total = new_rev + repeat_rev

    assert abs(total - BASELINE["gross_revenue"]) < 1.0, (
        f"New+repeat revenue ({total}) does not reconcile with baseline gross "
        f"revenue ({BASELINE['gross_revenue']}) -- would silently corrupt the "
        f"retention scenario."
    )
    return new_rev, repeat_rev, total


def verify_fy2025_order_count():
    """Cross-check the real FY2025 order count two independent ways."""
    raw = pd.read_csv(DATA_RAW / "orders.csv", parse_dates=["order_date"])
    count_raw = int((raw["order_date"].dt.year == 2025).sum())

    monthly = pd.read_csv(DATA_PROCESSED / "kpi_revenue_by_month.csv")
    count_monthly = int(monthly[monthly["month"].str.startswith("2025")]["orders"].sum())

    assert count_raw == count_monthly, "FY2025 order count disagrees between raw file and monthly KPI file."
    return count_raw


def net_profit(gross_revenue, cogs, shipping, operational, returns, marketing):
    gross_profit = gross_revenue - cogs
    total_opex = shipping + operational + returns + marketing
    return gross_profit - total_opex


def build_current_scenario():
    b = BASELINE
    gross_profit = b["gross_revenue"] - b["cogs"]
    total_opex = b["shipping_cost"] + b["operational_cost"] + b["return_amount"] + b["marketing_spend"]
    np_ = gross_profit - total_opex
    cac = b["marketing_spend"] / b["customers_acquired"]
    roi = (b["revenue_from_acquired"] - b["marketing_spend"]) / b["marketing_spend"]
    return {
        "scenario": "Current",
        "gross_revenue": b["gross_revenue"],
        "cogs": b["cogs"],
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_profit / b["gross_revenue"] * 100,
        "shipping_cost": b["shipping_cost"],
        "operational_cost": b["operational_cost"],
        "return_amount": b["return_amount"],
        "marketing_spend": b["marketing_spend"],
        "total_opex": total_opex,
        "net_profit": np_,
        "net_margin_pct": np_ / b["gross_revenue"] * 100,
        "cac": cac,
        "marketing_roi_pct": roi * 100,
        "incremental_value_vs_current": 0.0,
    }


def build_retention_scenario(new_rev_2025, repeat_rev_2025, current):
    b = BASELINE
    new_retention = b["avg_monthly_retention"] + RETENTION_DELTA_PP
    uplift_factor = new_retention / b["avg_monthly_retention"]

    repeat_rev_new = repeat_rev_2025 * uplift_factor
    gross_revenue_new = repeat_rev_new + new_rev_2025
    growth_ratio = gross_revenue_new / b["gross_revenue"]

    cogs_new = b["cogs"] * growth_ratio
    shipping_new = b["shipping_cost"] * growth_ratio
    operational_new = b["operational_cost"] * growth_ratio
    returns_new = b["return_amount"] * growth_ratio
    marketing_new = b["marketing_spend"]  # unchanged lever

    gross_profit = gross_revenue_new - cogs_new
    total_opex = shipping_new + operational_new + returns_new + marketing_new
    np_ = gross_profit - total_opex
    cac = marketing_new / b["customers_acquired"]  # acquisition unaffected
    roi = (b["revenue_from_acquired"] - marketing_new) / marketing_new

    return {
        "scenario": "Retention +5pp",
        "gross_revenue": gross_revenue_new,
        "cogs": cogs_new,
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_profit / gross_revenue_new * 100,
        "shipping_cost": shipping_new,
        "operational_cost": operational_new,
        "return_amount": returns_new,
        "marketing_spend": marketing_new,
        "total_opex": total_opex,
        "net_profit": np_,
        "net_margin_pct": np_ / gross_revenue_new * 100,
        "cac": cac,
        "marketing_roi_pct": roi * 100,
        "incremental_value_vs_current": np_ - current["net_profit"],
        "new_retention_rate": new_retention,
        "revenue_uplift_factor": uplift_factor,
    }


def build_discount_scenario(current):
    b = BASELINE
    new_discount_rate = b["discount_rate"] - DISCOUNT_DELTA_PP
    pre_discount_value = b["gross_revenue"] / (1 - b["discount_rate"])
    gross_revenue_new = pre_discount_value * (1 - new_discount_rate)

    cogs_new = b["cogs"]  # unit cost unaffected by discount policy
    shipping_new = b["shipping_cost"]
    operational_new = b["operational_cost"]
    returns_new = b["return_amount"]
    marketing_new = b["marketing_spend"]

    gross_profit = gross_revenue_new - cogs_new
    total_opex = shipping_new + operational_new + returns_new + marketing_new
    np_ = gross_profit - total_opex
    cac = marketing_new / b["customers_acquired"]
    roi = (b["revenue_from_acquired"] - marketing_new) / marketing_new

    return {
        "scenario": "Discount -2pp",
        "gross_revenue": gross_revenue_new,
        "cogs": cogs_new,
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_profit / gross_revenue_new * 100,
        "shipping_cost": shipping_new,
        "operational_cost": operational_new,
        "return_amount": returns_new,
        "marketing_spend": marketing_new,
        "total_opex": total_opex,
        "net_profit": np_,
        "net_margin_pct": np_ / gross_revenue_new * 100,
        "cac": cac,
        "marketing_roi_pct": roi * 100,
        "incremental_value_vs_current": np_ - current["net_profit"],
        "new_discount_rate": new_discount_rate,
        "pre_discount_value": pre_discount_value,
    }


def build_marketing_scenario(current):
    b = BASELINE
    marketing_new = b["marketing_spend"] * (1 + MARKETING_SPEND_INCREASE_PCT)
    acquired_new = b["customers_acquired"] * ((1 + MARKETING_SPEND_INCREASE_PCT) ** MARKETING_ACQUISITION_ELASTICITY)
    revenue_per_acquired = b["revenue_from_acquired"] / b["customers_acquired"]
    revenue_from_acquired_new = acquired_new * revenue_per_acquired
    incremental_revenue = revenue_from_acquired_new - b["revenue_from_acquired"]

    gross_revenue_new = b["gross_revenue"] + incremental_revenue

    variable_cost_ratio = (
        b["cogs"] + b["shipping_cost"] + b["operational_cost"] + b["return_amount"]
    ) / b["gross_revenue"]
    incremental_variable_cost = incremental_revenue * variable_cost_ratio

    # distribute incremental variable cost proportionally across the same
    # baseline cost mix so each line item scales consistently
    base_variable_total = b["cogs"] + b["shipping_cost"] + b["operational_cost"] + b["return_amount"]
    cogs_new = b["cogs"] + incremental_variable_cost * (b["cogs"] / base_variable_total)
    shipping_new = b["shipping_cost"] + incremental_variable_cost * (b["shipping_cost"] / base_variable_total)
    operational_new = b["operational_cost"] + incremental_variable_cost * (b["operational_cost"] / base_variable_total)
    returns_new = b["return_amount"] + incremental_variable_cost * (b["return_amount"] / base_variable_total)

    gross_profit = gross_revenue_new - cogs_new
    total_opex = shipping_new + operational_new + returns_new + marketing_new
    np_ = gross_profit - total_opex
    cac = marketing_new / acquired_new
    roi = (revenue_from_acquired_new - marketing_new) / marketing_new

    return {
        "scenario": "Marketing +25%",
        "gross_revenue": gross_revenue_new,
        "cogs": cogs_new,
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_profit / gross_revenue_new * 100,
        "shipping_cost": shipping_new,
        "operational_cost": operational_new,
        "return_amount": returns_new,
        "marketing_spend": marketing_new,
        "total_opex": total_opex,
        "net_profit": np_,
        "net_margin_pct": np_ / gross_revenue_new * 100,
        "cac": cac,
        "marketing_roi_pct": roi * 100,
        "incremental_value_vs_current": np_ - current["net_profit"],
        "customers_acquired_new": acquired_new,
        "incremental_acquired_revenue": incremental_revenue,
    }


def run_all_scenarios():
    order_count_2025 = verify_fy2025_order_count()
    new_rev, repeat_rev, total = load_fy2025_new_vs_repeat_revenue()

    current = build_current_scenario()
    retention = build_retention_scenario(new_rev, repeat_rev, current)
    discount = build_discount_scenario(current)
    marketing = build_marketing_scenario(current)

    scenarios = [current, retention, discount, marketing]

    data_notes = {
        "fy2025_order_count_verified": order_count_2025,
        "assumptions_sheet_total_orders_cell": 30_895,
        "discrepancy_flagged": order_count_2025 != 30_895,
        "fy2025_new_order_revenue": new_rev,
        "fy2025_repeat_order_revenue": repeat_rev,
        "fy2025_revenue_reconciled": abs(total - BASELINE["gross_revenue"]) < 1.0,
    }
    return scenarios, data_notes


if __name__ == "__main__":
    scenarios, notes = run_all_scenarios()
    print(json.dumps({"scenarios": scenarios, "data_notes": notes}, indent=2, default=str))
