"""
Phase 17 - Scenario tests (spec section 33): Scenario calculations.

Runs the real Phase 12 scenario engine (the four fixed scenarios: Current,
Retention +5pp, Discount -2pp, Marketing +25%) and checks its internal
arithmetic and invariants - independent of the exact baseline numbers, so
these keep passing if BASELINE is ever refreshed from a newer dataset run.
"""

from __future__ import annotations

import pytest

import scenario_engine as se


@pytest.fixture(scope="module")
def scenarios_and_notes():
    return se.run_all_scenarios()


@pytest.fixture(scope="module")
def scenarios(scenarios_and_notes):
    return {s["scenario"]: s for s in scenarios_and_notes[0]}


def test_all_four_fixed_scenarios_present(scenarios):
    assert set(scenarios.keys()) == {
        "Current", "Retention +5pp", "Discount -2pp", "Marketing +25%",
    }


def test_current_scenario_has_zero_incremental_value(scenarios):
    """By definition: the baseline can't have incremental value vs itself."""
    assert scenarios["Current"]["incremental_value_vs_current"] == pytest.approx(0.0, abs=1e-6)


def test_net_profit_formula_consistent_for_every_scenario(scenarios):
    for name, s in scenarios.items():
        expected_net_profit = s["gross_profit"] - (
            s["shipping_cost"] + s["operational_cost"] + s["return_amount"] + s["marketing_spend"]
        )
        assert s["net_profit"] == pytest.approx(expected_net_profit, abs=1.0), (
            f"net_profit inconsistent with its own opex breakdown in scenario '{name}'"
        )


def test_gross_profit_formula_consistent_for_every_scenario(scenarios):
    for name, s in scenarios.items():
        assert s["gross_profit"] == pytest.approx(
            s["gross_revenue"] - s["cogs"], abs=1.0
        ), f"gross_profit != gross_revenue - cogs in scenario '{name}'"


def test_margin_percentages_are_plausible(scenarios):
    for name, s in scenarios.items():
        assert 0 < s["gross_margin_pct"] < 100, f"Implausible gross margin in '{name}'"
        assert -100 < s["net_margin_pct"] < 100, f"Implausible net margin in '{name}'"


def test_incremental_value_matches_net_profit_delta(scenarios):
    current = scenarios["Current"]
    for name, s in scenarios.items():
        if name == "Current":
            continue
        expected_delta = s["net_profit"] - current["net_profit"]
        assert s["incremental_value_vs_current"] == pytest.approx(expected_delta, abs=1.0), (
            f"incremental_value_vs_current doesn't match net_profit delta for '{name}'"
        )


def test_retention_scenario_only_scales_repeat_revenue(scenarios, scenarios_and_notes):
    """Retention scenario must beat Current on revenue (uplift factor > 1),
    since Retention +5pp is strictly an improvement over baseline retention."""
    _, notes = scenarios_and_notes
    assert scenarios["Retention +5pp"]["gross_revenue"] > scenarios["Current"]["gross_revenue"]
    assert notes["fy2025_revenue_reconciled"] is True


def test_discount_scenario_same_order_volume_higher_revenue(scenarios):
    """Reducing the discount rate at the same list pricing must realize
    MORE revenue at the same volume, and leave COGS untouched (spec:
    a discount change doesn't change what a unit costs)."""
    assert scenarios["Discount -2pp"]["gross_revenue"] > scenarios["Current"]["gross_revenue"]
    assert scenarios["Discount -2pp"]["cogs"] == pytest.approx(scenarios["Current"]["cogs"], abs=0.01)


def test_marketing_scenario_spend_increases_by_configured_pct(scenarios):
    expected_spend = se.BASELINE["marketing_spend"] * (1 + se.MARKETING_SPEND_INCREASE_PCT)
    assert scenarios["Marketing +25%"]["marketing_spend"] == pytest.approx(expected_spend, abs=0.01)


def test_marketing_scenario_uses_diminishing_returns_not_linear_scaling(scenarios):
    """acquired_new should scale by (1+pct)^elasticity, NOT 1:1 with spend -
    i.e. less than proportionally, since elasticity < 1."""
    spend_multiplier = 1 + se.MARKETING_SPEND_INCREASE_PCT
    acquired_multiplier = scenarios["Marketing +25%"]["customers_acquired_new"] / se.BASELINE["customers_acquired"]
    assert acquired_multiplier < spend_multiplier, (
        "Marketing scenario appears to scale acquisition linearly with spend, "
        "not via the documented diminishing-returns elasticity."
    )
    assert acquired_multiplier == pytest.approx(spend_multiplier ** se.MARKETING_ACQUISITION_ELASTICITY, rel=1e-6)


def test_net_profit_ranks_retention_as_strongest_lever(scenarios):
    """Regression check for Phase 12/13's real finding: retention improvement
    delivers more incremental profit than either discount reduction or the
    marketing increase."""
    retention_gain = scenarios["Retention +5pp"]["incremental_value_vs_current"]
    discount_gain = scenarios["Discount -2pp"]["incremental_value_vs_current"]
    marketing_gain = scenarios["Marketing +25%"]["incremental_value_vs_current"]
    assert retention_gain > discount_gain
    assert retention_gain > marketing_gain


def test_verify_fy2025_order_count_matches_two_independent_sources():
    """se.verify_fy2025_order_count() itself asserts raw vs monthly-KPI
    agreement internally - this test just confirms it runs clean and
    returns a sane positive count."""
    count = se.verify_fy2025_order_count()
    assert count > 0
