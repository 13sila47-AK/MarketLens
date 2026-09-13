"""
MarketLens - Phase 16: Scenario Simulator engine
===================================================
The frozen spec (section 21) asks the dashboard's Scenario Simulator to let
management move SEVEN levers: Retention, Discount, Marketing, Price,
Conversion, Customer Acquisition, and Return Rate. Phase 12's
`scenario_engine.py` only ever needed to compute three FIXED, spec-mandated
scenarios (Retention +5pp, Discount -2pp, Marketing +25%) and is left
untouched here -- it remains the authoritative source for those exact
numbers (see data/processed/scenario_comparison.csv).

This module is an interactive EXTENSION for Phase 16: it reuses the exact
same verified BASELINE constants and the exact same modeling logic Phase 12
already established for retention/discount/marketing, and adds two more
levers (Price, Return Rate) plus a standalone Customer-Acquisition lever
using the same documented-assumption style. Every formula is a direct
generalization of Phase 12's fixed-delta version to a continuous slider
value -- moving a slider to the Phase 12 fixed value reproduces Phase 12's
number exactly (checked in verify_against_fixed_scenarios()).

Assumptions this module adds beyond Phase 12 (stated here, not hidden):
  - Price change: applied directly to gross revenue at the SAME unit
    volume (no price-elasticity-of-demand effect modeled -- doing so
    would require an elasticity estimate this dataset cannot support
    without inventing one, same caveat Phase 12 gave for discount).
  - Return rate change: scales the return_amount opex line
    proportionally to the ratio of new/baseline return rate.
  - Customer acquisition (standalone): scales customers_acquired and
    revenue_from_acquired directly, independent of marketing spend --
    e.g. representing an efficiency improvement, not a spend increase.
  - Conversion: scales customers_converted only, which (in this
    dataset's cost structure) does not itself change any revenue/cost
    line -- it is reported for reference, matching the spec's KPI list,
    but does not move net profit on its own since acquisition (not raw
    conversion count) is what is wired to revenue.
  - When multiple levers are moved together, their revenue/cost effects
    are combined ADDITIVELY on top of the baseline (no cross-lever
    interaction is modeled) -- the same "simple sum, not re-modeled
    scenario" caveat Phase 14 used for its combined recommendation
    total.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python" / "scenarios"))

import scenario_engine as se  # noqa: E402  (Phase 12, verified baseline + fixed scenarios)

BASELINE = se.BASELINE


def simulate(
    retention_delta_pp: float = 0.0,
    discount_delta_pp: float = 0.0,
    marketing_pct_change: float = 0.0,
    price_pct_change: float = 0.0,
    conversion_delta_pp: float = 0.0,
    acquisition_pct_change: float = 0.0,
    return_rate_delta_pp: float = 0.0,
) -> dict:
    """Compute projected Revenue / Profit / Margin / ROI / Incremental Value
    for an arbitrary combination of the seven management levers.

    All deltas are expressed the same way the fixed scenarios are:
    percentage-POINT deltas for rates (retention, discount, conversion,
    return rate) and percentage CHANGE for spend-like quantities
    (marketing, price, acquisition).
    """
    b = BASELINE
    new_rev_2025, repeat_rev_2025, _ = se.load_fy2025_new_vs_repeat_revenue()

    marketing = b["marketing_spend"]
    acquired = b["customers_acquired"]
    converted = b["customers_converted"]
    revenue_from_acquired = b["revenue_from_acquired"]

    variable_cost_ratio = (b["cogs"] + b["shipping_cost"] + b["operational_cost"] + b["return_amount"]) / b["gross_revenue"]

    # --- Step 1: Retention lever (repeat-revenue only, same logic as Phase 12) ---
    # Applied first, at the baseline discount rate, exactly as Phase 12 does.
    new_retention = b["avg_monthly_retention"] + retention_delta_pp
    uplift_factor = max(new_retention, 0.0) / b["avg_monthly_retention"]
    repeat_rev_after_retention = repeat_rev_2025 * uplift_factor
    revenue_after_retention = repeat_rev_after_retention + new_rev_2025  # still net of baseline discount

    # --- Step 2: Discount lever ---------------------------------------------
    # Back out the pre-discount (list) value at the baseline discount rate,
    # then re-apply at the new discount rate. If discount_delta_pp == 0 this
    # is an identity transform (returns revenue_after_retention unchanged).
    new_discount_rate = max(b["discount_rate"] - discount_delta_pp, 0.0)
    pre_discount_value = revenue_after_retention / (1 - b["discount_rate"])
    revenue_after_discount = pre_discount_value * (1 - new_discount_rate)

    # --- Step 3: Price lever (direct pass-through at same unit volume) -----
    revenue = revenue_after_discount * (1 + price_pct_change / 100.0)

    # Variable costs (COGS, shipping, operational, returns) scale ONLY with
    # the VOLUME growth retention produces -- exactly Phase 12's rule.
    # Discount and price changes move revenue without moving unit volume,
    # so (matching Phase 12's discount-scenario treatment exactly) they do
    # NOT scale these cost lines.
    volume_growth_ratio = revenue_after_retention / b["gross_revenue"]
    cogs = b["cogs"] * volume_growth_ratio
    shipping = b["shipping_cost"] * volume_growth_ratio
    operational = b["operational_cost"] * volume_growth_ratio
    returns_amt = b["return_amount"] * volume_growth_ratio

    # --- Marketing spend lever (same elasticity logic as Phase 12) ---------
    if marketing_pct_change:
        marketing = b["marketing_spend"] * (1 + marketing_pct_change / 100.0)
        acquired_new = b["customers_acquired"] * ((1 + marketing_pct_change / 100.0) ** se.MARKETING_ACQUISITION_ELASTICITY)
        revenue_per_acquired = b["revenue_from_acquired"] / b["customers_acquired"]
        revenue_from_acquired_new = acquired_new * revenue_per_acquired
        incremental_revenue = revenue_from_acquired_new - b["revenue_from_acquired"]
        revenue += incremental_revenue
        incremental_variable_cost = incremental_revenue * variable_cost_ratio
        base_variable_total = b["cogs"] + b["shipping_cost"] + b["operational_cost"] + b["return_amount"]
        cogs += incremental_variable_cost * (b["cogs"] / base_variable_total)
        shipping += incremental_variable_cost * (b["shipping_cost"] / base_variable_total)
        operational += incremental_variable_cost * (b["operational_cost"] / base_variable_total)
        returns_amt += incremental_variable_cost * (b["return_amount"] / base_variable_total)
        acquired = acquired_new
        revenue_from_acquired = revenue_from_acquired_new

    # --- Standalone customer-acquisition efficiency lever -------------------
    if acquisition_pct_change:
        extra_acquired = b["customers_acquired"] * (acquisition_pct_change / 100.0)
        revenue_per_acquired = b["revenue_from_acquired"] / b["customers_acquired"]
        incremental_revenue = extra_acquired * revenue_per_acquired
        revenue += incremental_revenue
        incremental_variable_cost = incremental_revenue * variable_cost_ratio
        base_variable_total = b["cogs"] + b["shipping_cost"] + b["operational_cost"] + b["return_amount"]
        cogs += incremental_variable_cost * (b["cogs"] / base_variable_total)
        shipping += incremental_variable_cost * (b["shipping_cost"] / base_variable_total)
        operational += incremental_variable_cost * (b["operational_cost"] / base_variable_total)
        returns_amt += incremental_variable_cost * (b["return_amount"] / base_variable_total)
        acquired = acquired + extra_acquired

    # --- Conversion lever (reference only -- see module docstring) ---------
    if conversion_delta_pp:
        base_rate = converted / b["customers_targeted"]
        new_rate = max(base_rate + conversion_delta_pp / 100.0, 0.0)
        converted = new_rate * b["customers_targeted"]

    # --- Return rate lever ---------------------------------------------------
    if return_rate_delta_pp:
        new_return_rate = max(b["return_rate"] - return_rate_delta_pp, 0.0)
        returns_amt = returns_amt * (new_return_rate / b["return_rate"]) if b["return_rate"] else returns_amt

    gross_profit = revenue - cogs
    total_opex = shipping + operational + returns_amt + marketing
    net_profit = gross_profit - total_opex
    cac = marketing / acquired if acquired else float("nan")
    roi = (revenue_from_acquired - marketing) / marketing * 100 if marketing else float("nan")

    current = se.build_current_scenario()

    return {
        "gross_revenue": revenue,
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_profit / revenue * 100 if revenue else 0.0,
        "cogs": cogs,
        "shipping_cost": shipping,
        "operational_cost": operational,
        "return_amount": returns_amt,
        "marketing_spend": marketing,
        "total_opex": total_opex,
        "net_profit": net_profit,
        "net_margin_pct": net_profit / revenue * 100 if revenue else 0.0,
        "cac": cac,
        "marketing_roi_pct": roi,
        "customers_acquired": acquired,
        "customers_converted": converted,
        "incremental_value_vs_current": net_profit - current["net_profit"],
    }


def verify_against_fixed_scenarios(tolerance: float = 1.0) -> list[str]:
    """Sanity check: setting sliders to Phase 12's exact fixed deltas must
    reproduce Phase 12's exact numbers. Returns a list of mismatches
    (empty list = fully consistent)."""
    fixed, _ = se.run_all_scenarios()
    fixed_by_name = {s["scenario"]: s for s in fixed}
    mismatches = []

    checks = [
        ("Retention +5pp", dict(retention_delta_pp=se.RETENTION_DELTA_PP)),
        ("Discount -2pp", dict(discount_delta_pp=se.DISCOUNT_DELTA_PP)),
        ("Marketing +25%", dict(marketing_pct_change=se.MARKETING_SPEND_INCREASE_PCT * 100)),
    ]
    for name, kwargs in checks:
        sim = simulate(**kwargs)
        ref = fixed_by_name[name]
        diff = abs(sim["net_profit"] - ref["net_profit"])
        if diff > tolerance:
            mismatches.append(f"{name}: simulate() net_profit {sim['net_profit']:.2f} vs scenario_engine {ref['net_profit']:.2f} (diff {diff:.2f})")
    return mismatches


if __name__ == "__main__":
    mismatches = verify_against_fixed_scenarios()
    if mismatches:
        print("MISMATCHES FOUND:")
        for m in mismatches:
            print(" -", m)
    else:
        print("OK: simulate() reproduces all Phase 12 fixed scenarios within tolerance.")

    print("\nCurrent baseline:", simulate())
    print("\nRetention +5pp via simulate():", simulate(retention_delta_pp=0.05))
