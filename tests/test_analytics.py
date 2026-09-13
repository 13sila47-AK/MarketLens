"""
Phase 17 - Analytics tests (spec section 33):
    - Revenue calculations
    - Margin calculations
    - ROI calculations
    - CAC calculations

Each test recomputes the expected value independently (straight from the
enriched/raw CSVs with plain pandas) and checks it against the real Phase 07
module's output - so these are regression tests against the actual data,
not against hardcoded numbers that would go stale if the dataset changes.
"""

from __future__ import annotations

import pandas as pd
import pytest

import revenue as rev
import profitability as prof
import marketing_analytics as ma
import product_analytics as pa
import customer_analytics as ca
import customer_features as cfeat


# ---------------------------------------------------------------------------
# Revenue calculations
# ---------------------------------------------------------------------------

def test_total_revenue_matches_raw_sum(orders_enriched, order_items_raw):
    result = rev.total_revenue(orders_enriched)
    expected_gross = round(float(order_items_raw["revenue"].sum()), 2)
    assert result["gross_revenue"] == pytest.approx(expected_gross, abs=1.0)
    assert result["total_orders"] == len(orders_enriched)


def test_total_revenue_net_is_gross_minus_returns(orders_enriched):
    result = rev.total_revenue(orders_enriched)
    expected_net = round(result["gross_revenue"] - result["total_returned_amount"], 2)
    assert result["net_revenue"] == pytest.approx(expected_net, abs=0.5)


def test_revenue_by_region_sums_to_total(orders_enriched):
    by_region = rev.revenue_by_region(orders_enriched)
    total = rev.total_revenue(orders_enriched)["gross_revenue"]
    assert by_region["gross_revenue"].sum() == pytest.approx(total, rel=1e-6)


def test_revenue_by_month_is_chronologically_sorted(orders_enriched):
    by_month = rev.revenue_by_month(orders_enriched)
    months = by_month["month"].tolist()
    assert months == sorted(months)


def test_revenue_growth_yoy_has_expected_columns(orders_enriched):
    growth = rev.revenue_growth_yoy(orders_enriched)
    assert {"year", "gross_revenue"}.issubset(growth.columns)
    assert len(growth) >= 2  # dataset spans multiple years (2023-2025)


# ---------------------------------------------------------------------------
# Margin / profitability calculations
# ---------------------------------------------------------------------------

def test_gross_profit_equals_revenue_minus_cogs(orders_enriched, order_items_enriched):
    summary = prof.profitability_summary(orders_enriched, order_items_enriched)
    assert summary["gross_profit"] == pytest.approx(
        summary["gross_revenue"] - summary["cogs"], abs=0.5
    )


def test_gross_margin_pct_matches_manual_formula(orders_enriched, order_items_enriched):
    summary = prof.profitability_summary(orders_enriched, order_items_enriched)
    expected_margin = summary["gross_profit"] / summary["gross_revenue"] * 100
    assert summary["gross_margin_pct"] == pytest.approx(expected_margin, abs=0.01)


def test_margin_is_a_plausible_percentage(orders_enriched, order_items_enriched):
    """Sanity bound: a real retail margin should land well inside 0-100%."""
    summary = prof.profitability_summary(orders_enriched, order_items_enriched)
    assert 0 < summary["gross_margin_pct"] < 100


def test_cogs_by_order_never_negative(order_items_enriched):
    cogs = prof.cogs_by_order(order_items_enriched)
    assert (cogs["cogs"] >= 0).all()


def test_discount_impact_uses_pre_discount_base(orders_enriched, order_items_enriched):
    """discount_impact_pct = discount / (gross_revenue + discount), not
    discount / gross_revenue - the two differ, so this catches a common
    off-by-definition bug."""
    summary = prof.profitability_summary(orders_enriched, order_items_enriched)
    wrong_denominator_pct = (
        summary["total_discount_given"] / summary["gross_revenue"] * 100
    )
    # The correct (pre-discount-base) figure must be smaller than the
    # naive gross-revenue-denominator figure.
    assert summary["discount_impact_pct"] < wrong_denominator_pct


def test_gross_margin_trend_yoy_shows_compression(orders_enriched, order_items_enriched):
    """Known, verified business story (Phase 08/13): margin compresses over
    the 3-year window as discounting rises. This is a regression check that
    the trend calculation still reproduces that direction."""
    trend = prof.gross_margin_trend_yoy(orders_enriched, order_items_enriched)
    trend = trend.sort_values(trend.columns[0])
    assert trend["gross_margin_pct"].iloc[-1] < trend["gross_margin_pct"].iloc[0]


# ---------------------------------------------------------------------------
# Marketing: ROI + CAC calculations
# ---------------------------------------------------------------------------

def test_cac_equals_spend_over_customers_acquired(campaigns_raw, customers_raw, orders_enriched):
    perf = ma.campaign_performance(campaigns_raw, customers_raw, orders_enriched)
    with_acquisitions = perf[perf["customers_acquired"] > 0]
    expected_cac = (with_acquisitions["spend"] / with_acquisitions["customers_acquired"]).round(2)
    assert (with_acquisitions["cac"] == expected_cac).all()


def test_roi_pct_formula(campaigns_raw, customers_raw, orders_enriched):
    perf = ma.campaign_performance(campaigns_raw, customers_raw, orders_enriched)
    expected_roi = (
        (perf["revenue_from_acquired"] - perf["spend"]) / perf["spend"] * 100
    ).round(2)
    assert (perf["roi_pct"] == expected_roi).all()


def test_conversion_rate_never_exceeds_100_pct(campaigns_raw, customers_raw, orders_enriched):
    perf = ma.campaign_performance(campaigns_raw, customers_raw, orders_enriched)
    assert (perf["conversion_rate_pct"] <= 100.0 + 1e-6).all()


def test_marketing_summary_blended_cac_positive(campaigns_raw, customers_raw, orders_enriched):
    summary = ma.marketing_summary(campaigns_raw, customers_raw, orders_enriched)
    assert summary["total_marketing_spend"] > 0
    assert summary["total_customers_acquired_via_campaigns"] >= 0
    assert summary["blended_cac"] > 0


def test_campaign_type_summary_blended_cac_matches_spend_over_acquired(
    campaigns_raw, customers_raw, orders_enriched
):
    perf = ma.campaign_performance(campaigns_raw, customers_raw, orders_enriched)
    type_summary = ma.campaign_type_summary(perf)
    expected = (
        type_summary["total_spend"] / type_summary["total_customers_acquired"]
    ).round(2)
    pd.testing.assert_series_equal(
        type_summary["blended_cac"].reset_index(drop=True),
        expected.reset_index(drop=True),
        check_names=False,
    )


# ---------------------------------------------------------------------------
# Product / customer analytics - column-shape + invariant checks
# ---------------------------------------------------------------------------

def test_top_products_returns_requested_row_count(order_items_enriched):
    top5 = pa.top_products(order_items_enriched, n=5)
    assert len(top5) == 5


def test_product_performance_revenue_non_negative(order_items_enriched):
    perf = pa.product_performance(order_items_enriched)
    assert (perf["revenue"] >= 0).all()


def test_customer_kpi_summary_has_expected_keys(customers_raw, orders_enriched):
    as_of = orders_enriched["order_date"].max()
    features = cfeat.build_customer_features(customers_raw, orders_enriched, as_of)
    summary = ca.customer_kpi_summary(features, orders_enriched)
    for key in ["total_customers", "repeat_purchase_rate_pct"]:
        assert key in summary, f"Missing expected key '{key}' in customer_kpi_summary output"
    assert summary["total_customers"] == len(customers_raw)
