"""
Phase 17 - Data tests (spec section 33):
    - No invalid revenue
    - No impossible discounts
    - No broken foreign keys

These check the actual CSVs on disk directly (independent of Phase 06's own
data_quality.py logic), AND separately run Phase 06's real build_report() to
confirm it still reports zero critical issues end-to-end - so a regression
in either the data or the checker itself would be caught.
"""

from __future__ import annotations

import pandas as pd


# ---------------------------------------------------------------------------
# Direct checks against the raw CSVs (independent of data_quality.py's logic)
# ---------------------------------------------------------------------------

def test_no_negative_revenue(order_items_raw):
    assert (order_items_raw["revenue"] >= 0).all(), "Found negative revenue in order_items.csv"


def test_no_negative_quantity(order_items_raw):
    assert (order_items_raw["quantity"] > 0).all(), "Found non-positive quantity in order_items.csv"


def test_discount_never_exceeds_order_value(order_items_raw):
    """discount must not exceed quantity * unit_price for any line item."""
    pre_discount_value = order_items_raw["quantity"] * order_items_raw["unit_price"]
    assert (order_items_raw["discount"] <= pre_discount_value + 1e-6).all(), (
        "Found order_items rows where discount exceeds the pre-discount order value"
    )


def test_discount_never_negative(order_items_raw):
    assert (order_items_raw["discount"] >= 0).all()


def test_revenue_equals_qty_times_price_minus_discount(order_items_raw):
    expected = (
        order_items_raw["quantity"] * order_items_raw["unit_price"] - order_items_raw["discount"]
    )
    assert (order_items_raw["revenue"] - expected).abs().max() < 1e-6, (
        "revenue != quantity * unit_price - discount for at least one row"
    )


def test_no_invalid_order_dates(orders_raw):
    assert orders_raw["order_date"].notna().all()
    assert orders_raw["order_date"].min() >= pd.Timestamp("2000-01-01")
    assert orders_raw["order_date"].max() <= pd.Timestamp.today()


def test_no_duplicate_primary_keys(orders_raw, customers_raw, products_raw):
    assert orders_raw["order_id"].is_unique, "Duplicate order_id found"
    assert customers_raw["customer_id"].is_unique, "Duplicate customer_id found"
    assert products_raw["product_id"].is_unique, "Duplicate product_id found"


def test_campaign_conversions_never_exceed_targeted(campaigns_raw):
    assert (campaigns_raw["customers_converted"] <= campaigns_raw["customers_targeted"]).all()


def test_return_amount_never_negative(returns_raw):
    assert (returns_raw["return_amount"] >= 0).all()


# ---------------------------------------------------------------------------
# Foreign key integrity (no broken FKs)
# ---------------------------------------------------------------------------

def test_orders_customer_id_resolves(orders_raw, customers_raw):
    valid_ids = set(customers_raw["customer_id"])
    assert set(orders_raw["customer_id"]).issubset(valid_ids), (
        "orders.csv has customer_id values not present in customers.csv"
    )


def test_order_items_order_id_resolves(order_items_raw, orders_raw):
    valid_ids = set(orders_raw["order_id"])
    assert set(order_items_raw["order_id"]).issubset(valid_ids), (
        "order_items.csv has order_id values not present in orders.csv"
    )


def test_order_items_product_id_resolves(order_items_raw, products_raw):
    valid_ids = set(products_raw["product_id"])
    assert set(order_items_raw["product_id"]).issubset(valid_ids), (
        "order_items.csv has product_id values not present in products.csv"
    )


def test_returns_order_id_resolves(returns_raw, orders_raw):
    valid_ids = set(orders_raw["order_id"])
    assert set(returns_raw["order_id"]).issubset(valid_ids), (
        "returns.csv has order_id values not present in orders.csv"
    )


def test_stores_region_id_resolves(stores_raw, regions_raw):
    valid_ids = set(regions_raw["region_id"])
    assert set(stores_raw["region_id"]).issubset(valid_ids)


def test_in_store_orders_have_a_store_online_orders_do_not(orders_raw):
    in_store = orders_raw[orders_raw["channel"] == "in-store"]
    online = orders_raw[orders_raw["channel"] == "online"]
    assert in_store["store_id"].notna().all(), "Some in-store orders have no store_id"
    assert online["store_id"].isna().all(), "Some online orders unexpectedly have a store_id"


# ---------------------------------------------------------------------------
# Full Phase 06 pipeline: the actual checker, run end-to-end
# ---------------------------------------------------------------------------

def test_data_quality_module_reports_zero_critical_issues():
    """Runs the real Phase 06 build_report() and asserts it still finds no
    critical issues - a regression test for the checker + data together."""
    import data_quality as dq

    report = dq.build_report()
    assert report.critical_issues == [], (
        f"Phase 06 data_quality checker found critical issues: {report.critical_issues}"
    )
    assert report.total_rows_processed > 0


def test_data_quality_reconciliation_check_passes():
    import data_quality as dq

    report = dq.build_report()
    reconciliation_issues = [
        i for i in report.issues
        if i.check == "processed_reconciliation" and i.severity == "critical" and i.count > 0
    ]
    assert reconciliation_issues == []
