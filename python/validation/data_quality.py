"""
MarketLens - Phase 06: Data Quality & Validation
=================================================
Runs the formal data-quality gate described in the project spec:
  - Missing values      (customer_id, product_id, region, revenue, order_date, ...)
  - Duplicates           (duplicate customers, orders, products, order_items)
  - Invalid values       (negative revenue, negative quantity, invalid dates,
                           invalid regions, discount > revenue)
  - Cross-source validation (every FK actually resolves: orders.customer_id
                           exists in customers, order_items.product_id exists
                           in products, etc.)

This is deliberately independent of the CHECK constraints already enforced
at generation time (Phase 03) and at the PostgreSQL schema level (Phase 04):
those prevent bad data from ever being written, this formally *proves* the
data that made it through Phase 05's extraction is still clean, end to end.
A clean report here is a real, checked finding — not an assumption.

Usage:
    python python/validation/data_quality.py

Output:
    Prints a full report to stdout and writes it to
    reports/data_quality_report.md (numbers computed live from the actual
    CSVs in data/raw/ and data/processed/ — never hardcoded).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_PATH = ROOT / "reports" / "data_quality_report.md"

VALID_REGIONS = {"North", "South", "East", "West", "Central"}
VALID_CHANNELS = {"online", "in-store"}
VALID_CATEGORIES = {
    "Apparel", "Home Goods", "Electronics Accessories",
    "Personal Care", "Footwear",
}
VALID_CAMPAIGN_TYPES = {
    "Email", "Social Media", "Search Ads", "Influencer", "In-Store Promo",
}
VALID_RETURN_REASONS = {
    "Wrong size", "Defective item", "Not as described",
    "Changed mind", "Better price found elsewhere", "Late delivery",
}


@dataclass
class Issue:
    """One logged data-quality finding."""
    check: str
    table: str
    severity: str          # "info" | "warning" | "critical"
    count: int
    detail: str


@dataclass
class QualityReport:
    rows_processed: dict[str, int] = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)

    def log(self, check: str, table: str, severity: str, count: int, detail: str) -> None:
        self.issues.append(Issue(check, table, severity, count, detail))

    @property
    def total_rows_processed(self) -> int:
        return sum(self.rows_processed.values())

    @property
    def critical_issues(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "critical" and i.count > 0]

    @property
    def warning_issues(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warning" and i.count > 0]

    @property
    def rejected_records(self) -> int:
        """Count of records that fail a hard-integrity rule (would be dropped
        before analytics): missing PK/FK, invalid date, negative amount."""
        return sum(i.count for i in self.critical_issues)


def load_tables() -> dict[str, pd.DataFrame]:
    names = [
        "regions", "stores", "products", "marketing_campaigns",
        "customers", "orders", "order_items", "returns", "costs",
    ]
    tables = {}
    for name in names:
        df = pd.read_csv(RAW_DIR / f"{name}.csv")
        tables[name] = df
    return tables


def check_missing_values(tables: dict[str, pd.DataFrame], report: QualityReport) -> None:
    required_cols = {
        "customers": ["customer_id", "customer_name", "signup_date", "region_name"],
        "orders": ["order_id", "customer_id", "order_date", "channel"],
        "order_items": ["order_item_id", "order_id", "product_id", "quantity",
                         "unit_price", "revenue"],
        "products": ["product_id", "product_name", "category", "cost", "selling_price"],
        "returns": ["return_id", "order_id", "return_date", "return_amount"],
        "costs": ["order_id", "shipping_cost", "operational_cost"],
        "marketing_campaigns": ["campaign_id", "campaign_date", "spend"],
    }
    for table, cols in required_cols.items():
        df = tables[table]
        for col in cols:
            n_missing = int(df[col].isna().sum())
            pct = (n_missing / len(df) * 100) if len(df) else 0.0
            report.log(
                check="missing_values", table=table,
                severity="critical" if n_missing else "info",
                count=n_missing,
                detail=f"{table}.{col}: {n_missing} missing ({pct:.2f}%)",
            )
    # store_id is allowed to be missing ONLY for online orders
    orders = tables["orders"]
    bad_store = orders[(orders["channel"] == "in-store") & (orders["store_id"].isna())]
    report.log(
        check="missing_values", table="orders",
        severity="critical", count=len(bad_store),
        detail=f"orders.store_id missing on in-store orders: {len(bad_store)}",
    )


def check_duplicates(tables: dict[str, pd.DataFrame], report: QualityReport) -> None:
    pk_cols = {
        "customers": "customer_id",
        "orders": "order_id",
        "order_items": "order_item_id",
        "products": "product_id",
        "stores": "store_id",
        "regions": "region_id",
        "marketing_campaigns": "campaign_id",
        "returns": "return_id",
    }
    for table, pk in pk_cols.items():
        df = tables[table]
        n_dupe = int(df[pk].duplicated().sum())
        report.log(
            check="duplicates", table=table,
            severity="critical" if n_dupe else "info",
            count=n_dupe,
            detail=f"{table}: {n_dupe} duplicate {pk} values",
        )
    # costs.order_id is a PK too (one row per order)
    n_dupe_costs = int(tables["costs"]["order_id"].duplicated().sum())
    report.log(
        check="duplicates", table="costs",
        severity="critical" if n_dupe_costs else "info",
        count=n_dupe_costs,
        detail=f"costs: {n_dupe_costs} duplicate order_id values",
    )
    # Exact full-row duplicates (defensive check, separate from PK dupes)
    for table, df in tables.items():
        n_exact = int(df.duplicated().sum())
        report.log(
            check="exact_row_duplicates", table=table,
            severity="warning" if n_exact else "info",
            count=n_exact,
            detail=f"{table}: {n_exact} fully duplicated rows",
        )


def check_invalid_values(tables: dict[str, pd.DataFrame], report: QualityReport) -> None:
    order_items = tables["order_items"]
    orders = tables["orders"]
    customers = tables["customers"]
    returns = tables["returns"]
    campaigns = tables["marketing_campaigns"]
    products = tables["products"]

    # Negative / non-positive revenue
    n_neg_rev = int((order_items["revenue"] < 0).sum())
    report.log("invalid_values", "order_items", "critical" if n_neg_rev else "info",
               n_neg_rev, f"Negative revenue rows: {n_neg_rev}")

    # Negative or zero quantity
    n_bad_qty = int((order_items["quantity"] <= 0).sum())
    report.log("invalid_values", "order_items", "critical" if n_bad_qty else "info",
               n_bad_qty, f"Non-positive quantity rows: {n_bad_qty}")

    # discount > order value (quantity * unit_price)
    order_value = order_items["quantity"] * order_items["unit_price"]
    n_bad_discount = int((order_items["discount"] > order_value + 0.01).sum())
    report.log("invalid_values", "order_items", "critical" if n_bad_discount else "info",
               n_bad_discount, f"discount > order value rows: {n_bad_discount}")

    # revenue reconciliation: revenue should equal qty*price - discount
    expected_revenue = order_value - order_items["discount"]
    n_mismatch = int((expected_revenue - order_items["revenue"]).abs().gt(0.01).sum())
    report.log("invalid_values", "order_items", "critical" if n_mismatch else "info",
               n_mismatch, f"revenue != qty*price-discount rows: {n_mismatch}")

    # Invalid dates (unparseable, or outside sane project date range)
    for table, col in [("orders", "order_date"), ("customers", "signup_date"),
                        ("returns", "return_date"), ("marketing_campaigns", "campaign_date")]:
        parsed = pd.to_datetime(tables[table][col], errors="coerce")
        n_invalid = int(parsed.isna().sum())
        out_of_range = int(((parsed.dt.year < 2020) | (parsed.dt.year > 2026)).sum())
        report.log("invalid_values", table, "critical" if n_invalid else "info",
                   n_invalid, f"{table}.{col}: {n_invalid} unparseable dates")
        report.log("invalid_values", table, "warning" if out_of_range else "info",
                   out_of_range, f"{table}.{col}: {out_of_range} dates outside 2020-2026")

    # Invalid regions
    n_bad_region = int((~customers["region_name"].isin(VALID_REGIONS)).sum())
    report.log("invalid_values", "customers", "critical" if n_bad_region else "info",
               n_bad_region, f"customers.region_name not in {sorted(VALID_REGIONS)}: {n_bad_region}")

    # Invalid channel
    n_bad_channel = int((~orders["channel"].isin(VALID_CHANNELS)).sum())
    report.log("invalid_values", "orders", "critical" if n_bad_channel else "info",
               n_bad_channel, f"orders.channel invalid: {n_bad_channel}")

    # Invalid category
    n_bad_cat = int((~products["category"].isin(VALID_CATEGORIES)).sum())
    report.log("invalid_values", "products", "critical" if n_bad_cat else "info",
               n_bad_cat, f"products.category invalid: {n_bad_cat}")

    # cost >= selling_price (should never happen — margin would be impossible)
    n_bad_cost = int((products["cost"] >= products["selling_price"]).sum())
    report.log("invalid_values", "products", "critical" if n_bad_cost else "info",
               n_bad_cost, f"products.cost >= selling_price: {n_bad_cost}")

    # returns.return_amount negative
    n_neg_return = int((returns["return_amount"] < 0).sum())
    report.log("invalid_values", "returns", "critical" if n_neg_return else "info",
               n_neg_return, f"Negative return_amount rows: {n_neg_return}")

    # invalid return_reason
    n_bad_reason = int((~returns["return_reason"].isin(VALID_RETURN_REASONS)).sum())
    report.log("invalid_values", "returns", "critical" if n_bad_reason else "info",
               n_bad_reason, f"returns.return_reason invalid: {n_bad_reason}")

    # campaigns: converted > targeted
    n_bad_conv = int((campaigns["customers_converted"] > campaigns["customers_targeted"]).sum())
    report.log("invalid_values", "marketing_campaigns", "critical" if n_bad_conv else "info",
               n_bad_conv, f"customers_converted > customers_targeted: {n_bad_conv}")
    # invalid campaign_type
    n_bad_ctype = int((~campaigns["campaign_type"].isin(VALID_CAMPAIGN_TYPES)).sum())
    report.log("invalid_values", "marketing_campaigns", "critical" if n_bad_ctype else "info",
               n_bad_ctype, f"campaign_type invalid: {n_bad_ctype}")


def check_cross_source_integrity(tables: dict[str, pd.DataFrame], report: QualityReport) -> None:
    """Referential integrity across tables — every FK must resolve."""
    orders, order_items = tables["orders"], tables["order_items"]
    customers, products = tables["customers"], tables["products"]
    stores, returns, costs = tables["stores"], tables["returns"], tables["costs"]
    campaigns = tables["marketing_campaigns"]

    checks = [
        ("orders.customer_id -> customers.customer_id",
         ~orders["customer_id"].isin(customers["customer_id"])),
        ("order_items.order_id -> orders.order_id",
         ~order_items["order_id"].isin(orders["order_id"])),
        ("order_items.product_id -> products.product_id",
         ~order_items["product_id"].isin(products["product_id"])),
        ("orders.store_id -> stores.store_id (non-null only)",
         orders["store_id"].notna() & ~orders["store_id"].isin(stores["store_id"])),
        ("returns.order_id -> orders.order_id",
         ~returns["order_id"].isin(orders["order_id"])),
        ("costs.order_id -> orders.order_id",
         ~costs["order_id"].isin(orders["order_id"])),
        ("customers.region_name -> regions.region_name",
         ~customers["region_name"].isin(tables["regions"]["region_name"])),
        ("customers.acquisition_campaign_id -> marketing_campaigns.campaign_id (non-null only)",
         customers["acquisition_campaign_id"].notna()
         & ~customers["acquisition_campaign_id"].isin(campaigns["campaign_id"])),
    ]
    for label, mask in checks:
        n_orphan = int(mask.sum())
        report.log("cross_source_integrity", label.split(" -> ")[0].split(".")[0],
                   "critical" if n_orphan else "info", n_orphan,
                   f"{label}: {n_orphan} orphan rows")

    # Every order should have exactly one costs row (1:1 relationship)
    orders_without_costs = int((~orders["order_id"].isin(costs["order_id"])).sum())
    report.log("cross_source_integrity", "costs", "critical" if orders_without_costs else "info",
               orders_without_costs, f"orders missing a costs row: {orders_without_costs}")

    # Every order should have at least one order_item
    orders_without_items = int((~orders["order_id"].isin(order_items["order_id"])).sum())
    report.log("cross_source_integrity", "order_items",
               "critical" if orders_without_items else "info",
               orders_without_items, f"orders with zero order_items: {orders_without_items}")


def check_processed_reconciliation(report: QualityReport) -> None:
    """Sanity check that Phase 05's enriched outputs still reconcile to raw."""
    raw_items = pd.read_csv(RAW_DIR / "order_items.csv")
    enriched_items = pd.read_csv(PROCESSED_DIR / "order_items_enriched.csv")
    enriched_orders = pd.read_csv(PROCESSED_DIR / "orders_enriched.csv")

    raw_total = round(float(raw_items["revenue"].sum()), 2)
    enriched_item_total = round(float(enriched_items["revenue"].sum()), 2)
    enriched_order_total = round(float(enriched_orders["gross_revenue"].sum()), 2)

    diff_items = round(abs(raw_total - enriched_item_total), 2)
    diff_orders = round(abs(raw_total - enriched_order_total), 2)

    report.log("processed_reconciliation", "order_items_enriched",
               "critical" if diff_items > 1.0 else "info", int(diff_items > 1.0),
               f"Revenue reconciliation raw vs item-grain enriched: "
               f"raw=₹{raw_total:,.2f} enriched=₹{enriched_item_total:,.2f} diff=₹{diff_items:,.2f}")
    report.log("processed_reconciliation", "orders_enriched",
               "critical" if diff_orders > 1.0 else "info", int(diff_orders > 1.0),
               f"Revenue reconciliation raw vs order-grain enriched: "
               f"raw=₹{raw_total:,.2f} enriched=₹{enriched_order_total:,.2f} diff=₹{diff_orders:,.2f}")

    n_row_diff = abs(len(raw_items) - len(enriched_items))
    report.log("processed_reconciliation", "order_items_enriched",
               "critical" if n_row_diff else "info", n_row_diff,
               f"Row count raw ({len(raw_items)}) vs enriched item-grain ({len(enriched_items)})")


def build_report() -> QualityReport:
    report = QualityReport()
    tables = load_tables()
    for name, df in tables.items():
        report.rows_processed[name] = len(df)

    check_missing_values(tables, report)
    check_duplicates(tables, report)
    check_invalid_values(tables, report)
    check_cross_source_integrity(tables, report)
    check_processed_reconciliation(report)
    return report


def render_markdown(report: QualityReport) -> str:
    lines = []
    lines.append("# MarketLens Data Quality Report")
    lines.append("")
    lines.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_")
    lines.append("")
    lines.append(
        "Phase 06 output. All numbers below are computed live from "
        "`data/raw/*.csv` and `data/processed/*.csv` by "
        "`python/validation/data_quality.py` — nothing here is hand-typed."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Tables checked | {len(report.rows_processed)} |")
    lines.append(f"| Total rows processed | {report.total_rows_processed:,} |")
    for table, n in report.rows_processed.items():
        lines.append(f"| &nbsp;&nbsp;— {table} | {n:,} |")
    lines.append(f"| Checks run | {len(report.issues)} |")
    lines.append(f"| Critical issues found | {len(report.critical_issues)} |")
    lines.append(f"| Warning issues found | {len(report.warning_issues)} |")
    lines.append(f"| Records failing a hard-integrity rule | {report.rejected_records:,} |")
    lines.append("")

    lines.append("## Result")
    lines.append("")
    if not report.critical_issues:
        lines.append(
            "**PASS** — zero critical data-quality violations found across "
            "missing values, duplicates, invalid values, and cross-source "
            "referential integrity. This confirms the pipeline "
            "(Phase 03 generation → Phase 04 schema constraints → Phase 05 "
            "extraction) preserves data integrity end to end, and that "
            "`data/processed/*.csv` is safe to build analytics on top of."
        )
    else:
        lines.append(
            f"**FAIL** — {len(report.critical_issues)} critical issue "
            f"categories found, affecting {report.rejected_records:,} records. "
            "See details below."
        )
    lines.append("")

    lines.append("## Checks by category")
    lines.append("")
    by_check: dict[str, list[Issue]] = {}
    for issue in report.issues:
        by_check.setdefault(issue.check, []).append(issue)

    for check_name, issues in by_check.items():
        lines.append(f"### {check_name.replace('_', ' ').title()}")
        lines.append("")
        lines.append("| Table | Severity | Count | Detail |")
        lines.append("|---|---|---|---|")
        for i in issues:
            flag = {"critical": "🔴", "warning": "🟡", "info": "🟢"}[i.severity]
            lines.append(f"| {i.table} | {flag} {i.severity} | {i.count} | {i.detail} |")
        lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "This check is intentionally redundant with the CHECK constraints in "
        "`sql/schema.sql` (Phase 04) and the generation-time consistency "
        "checks in `python/ingestion/generate_dataset.py` (Phase 03). "
        "Running it independently at Phase 06, against the actual files "
        "the analytics layer will consume, is what makes 'the data is clean' "
        "a verified fact rather than an assumption carried over from earlier "
        "phases."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = build_report()
    md = render_markdown(report)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(md, encoding="utf-8")

    print(md)
    print(f"\n[data_quality.py] Report written to {REPORT_PATH}")
    if report.critical_issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
