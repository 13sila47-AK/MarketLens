"""
MarketLens - Phase 05: Data Extraction Layer
==============================================
Pipeline:  SOURCE -> READ -> STANDARDIZE -> COMBINE -> VALIDATE -> ANALYTICAL DATA

Two internal sources are supported for READ:
  - "postgres": reads from the PostgreSQL database loaded in Phase 04
    (requires a live DB — see .env). This is the production path.
  - "csv":      reads directly from data/raw/*.csv. This is what actually
    runs in this build environment (no live Postgres / no network here).

Both paths converge on the exact same STANDARDIZE/COMBINE/VALIDATE logic
below, so switching sources later requires no changes to the analytics
that consume the output.

Output (data/processed/):
  - order_items_enriched.csv  : line-item grain, joined with product,
                                 order, customer, and region attributes.
                                 Use for product/category-level analysis.
  - orders_enriched.csv       : order grain, revenue aggregated from items,
                                 with costs, returns, and campaign
                                 attribution attached. Use for revenue,
                                 margin, customer, and marketing KPIs.

External sources (public APIs / research) are handled separately:
  - fetch_external_indicator() below shows the intended architecture for
    pulling a live public economic indicator, but is not invoked in this
    sandbox (no outbound network access here).
  - Qualitative external research (industry/competitor) is gathered
    directly and documented as markdown in Phase 10
    (research/industry_analysis.md, research/competitor_analysis.md),
    since that content doesn't fit a single structured API call.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# READ
# ============================================================================
def read_from_csv() -> dict[str, pd.DataFrame]:
    """Read every raw table directly from data/raw/*.csv."""
    tables = {}
    for name in ["regions", "stores", "products", "marketing_campaigns",
                 "customers", "orders", "order_items", "returns", "costs"]:
        tables[name] = pd.read_csv(RAW_DIR / f"{name}.csv")
    return tables


def read_from_postgres() -> dict[str, pd.DataFrame]:
    """Read every table from PostgreSQL (production path, Phase 04 schema)."""
    import os
    from sqlalchemy import create_engine
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    engine = create_engine(url)
    tables = {}
    for name in ["regions", "stores", "products", "marketing_campaigns",
                 "customers", "orders", "order_items", "returns", "costs"]:
        tables[name] = pd.read_sql(f"SELECT * FROM {name}", engine)
    return tables


def read_source(source: str = "csv") -> dict[str, pd.DataFrame]:
    if source == "csv":
        return read_from_csv()
    elif source == "postgres":
        return read_from_postgres()
    raise ValueError(f"Unknown source: {source!r} (expected 'csv' or 'postgres')")


# ============================================================================
# STANDARDIZE
# ============================================================================
def standardize(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Normalize dtypes so the CSV path and the Postgres path produce
    identical schemas downstream (Postgres returns real DATE/NUMERIC types;
    CSV returns strings that need explicit parsing)."""
    t = {k: v.copy() for k, v in tables.items()}

    t["customers"]["signup_date"] = pd.to_datetime(t["customers"]["signup_date"])
    t["orders"]["order_date"] = pd.to_datetime(t["orders"]["order_date"])
    t["marketing_campaigns"]["campaign_date"] = pd.to_datetime(t["marketing_campaigns"]["campaign_date"])
    t["returns"]["return_date"] = pd.to_datetime(t["returns"]["return_date"])

    # The CSV source stores region as a name on customers; the Postgres
    # source stores region_id (per schema.sql). Normalize both to carry a
    # `region_name` column so COMBINE doesn't need to branch on source.
    if "region_name" not in t["customers"].columns and "region_id" in t["customers"].columns:
        t["customers"] = t["customers"].merge(
            t["regions"][["region_id", "region_name"]], on="region_id", how="left"
        )

    t["orders"]["store_id"] = t["orders"]["store_id"].astype("Int64")
    t["customers"]["acquisition_campaign_id"] = (
        t["customers"]["acquisition_campaign_id"].astype("Int64")
    )
    return t


# ============================================================================
# COMBINE
# ============================================================================
def build_order_items_enriched(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = (
        t["order_items"]
        .merge(t["products"], on="product_id", how="left")
        .merge(t["orders"][["order_id", "customer_id", "order_date", "channel", "store_id"]],
               on="order_id", how="left")
        .merge(t["customers"][["customer_id", "customer_name", "signup_date",
                                 "region_name", "acquisition_campaign_id"]],
               on="customer_id", how="left")
        .merge(t["stores"][["store_id", "store_name"]], on="store_id", how="left")
    )
    df = df.rename(columns={"region_name": "region"})
    return df


def build_orders_enriched(t: dict[str, pd.DataFrame], items_enriched: pd.DataFrame) -> pd.DataFrame:
    order_revenue = (
        items_enriched.groupby("order_id")
        .agg(gross_revenue=("revenue", "sum"),
             total_discount=("discount", "sum"),
             item_count=("order_item_id", "count"),
             units=("quantity", "sum"))
        .reset_index()
    )

    order_returns = (
        t["returns"].groupby("order_id")
        .agg(total_returned_amount=("return_amount", "sum"),
             return_count=("return_id", "count"))
        .reset_index()
    )

    df = (
        t["orders"]
        .merge(order_revenue, on="order_id", how="left")
        .merge(t["costs"], on="order_id", how="left")
        .merge(order_returns, on="order_id", how="left")
        .merge(t["customers"][["customer_id", "region_name", "acquisition_campaign_id",
                                 "signup_date"]],
               on="customer_id", how="left")
    )
    df["total_returned_amount"] = df["total_returned_amount"].fillna(0.0)
    df["return_count"] = df["return_count"].fillna(0).astype(int)
    df = df.rename(columns={"region_name": "region"})
    df["net_revenue"] = df["gross_revenue"] - df["total_returned_amount"]
    df["total_cost"] = df["shipping_cost"] + df["operational_cost"]
    return df


# ============================================================================
# VALIDATE
# ============================================================================
def validate(t: dict[str, pd.DataFrame], items_enriched: pd.DataFrame, orders_enriched: pd.DataFrame):
    errors = []

    if len(items_enriched) != len(t["order_items"]):
        errors.append(
            f"Row count changed during item enrichment: "
            f"{len(t['order_items'])} raw -> {len(items_enriched)} enriched "
            f"(a join likely fanned out or dropped rows)"
        )

    if len(orders_enriched) != len(t["orders"]):
        errors.append(
            f"Row count changed during order enrichment: "
            f"{len(t['orders'])} raw -> {len(orders_enriched)} enriched"
        )

    raw_total_revenue = t["order_items"]["revenue"].sum()
    enriched_total_revenue = items_enriched["revenue"].sum()
    if abs(raw_total_revenue - enriched_total_revenue) > 1.0:
        errors.append(
            f"Total revenue mismatch after enrichment: "
            f"raw={raw_total_revenue:,.2f} vs enriched={enriched_total_revenue:,.2f}"
        )

    order_grain_revenue = orders_enriched["gross_revenue"].sum()
    if abs(order_grain_revenue - raw_total_revenue) > 1.0:
        errors.append(
            f"Order-grain revenue does not reconcile to item-grain revenue: "
            f"{order_grain_revenue:,.2f} vs {raw_total_revenue:,.2f}"
        )

    null_region_items = items_enriched["region"].isna().sum()
    if null_region_items > 0:
        errors.append(f"{null_region_items} enriched order_items have a null region")

    if errors:
        raise AssertionError("Data extraction validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    print("✅ Validation passed:")
    print(f"   order_items: {len(t['order_items']):,} raw -> {len(items_enriched):,} enriched (row count preserved)")
    print(f"   orders:      {len(t['orders']):,} raw -> {len(orders_enriched):,} enriched (row count preserved)")
    print(f"   revenue reconciles across item-grain, enriched-item-grain, and order-grain: ₹{raw_total_revenue:,.2f}")


# ============================================================================
# EXTERNAL SOURCES (architecture stub — not invoked in this sandbox)
# ============================================================================
def fetch_external_indicator(indicator_code: str = "NY.GDP.MKTP.KD.ZG", country: str = "IN") -> pd.DataFrame:
    """
    Illustrates the intended architecture for pulling a public economic
    indicator (e.g. World Bank API) to support the external market
    comparison in Phase 10. Requires outbound network access, which this
    build sandbox does not have — retained here as the production
    implementation, not executed during this build.
    """
    import requests

    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator_code}?format=json"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    _, records = resp.json()
    return pd.DataFrame(records)[["date", "value"]].rename(columns={"date": "year"})


# ============================================================================
# MAIN
# ============================================================================
def run(source: str = "csv"):
    print(f"[READ] source = '{source}'")
    tables = read_source(source)
    for name, df in tables.items():
        print(f"       {name}: {len(df):,} rows")

    print("[STANDARDIZE] normalizing dtypes and region representation")
    tables = standardize(tables)

    print("[COMBINE] building order_items_enriched ...")
    items_enriched = build_order_items_enriched(tables)
    print(f"          -> {len(items_enriched):,} rows, {items_enriched.shape[1]} columns")

    print("[COMBINE] building orders_enriched ...")
    orders_enriched = build_orders_enriched(tables, items_enriched)
    print(f"          -> {len(orders_enriched):,} rows, {orders_enriched.shape[1]} columns")

    print("[VALIDATE]")
    validate(tables, items_enriched, orders_enriched)

    items_enriched.to_csv(PROCESSED_DIR / "order_items_enriched.csv", index=False)
    orders_enriched.to_csv(PROCESSED_DIR / "orders_enriched.csv", index=False)
    print(f"\n[ANALYTICAL DATA] written to {PROCESSED_DIR}/")
    print("   - order_items_enriched.csv  (line-item grain)")
    print("   - orders_enriched.csv       (order grain)")

    return items_enriched, orders_enriched


if __name__ == "__main__":
    run(source="csv")
