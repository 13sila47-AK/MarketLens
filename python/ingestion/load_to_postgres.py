"""
MarketLens - Phase 04: Load into PostgreSQL
=============================================
Applies sql/schema.sql, then loads every table in data/raw/*.csv into
PostgreSQL, in FK-safe order, using fast COPY (not row-by-row inserts).

Requires a running PostgreSQL instance reachable via the DB_* variables in
.env (copy .env.example -> .env and fill in your credentials first).

Usage:
    python python/ingestion/load_to_postgres.py

This script is NOT executed as part of the build sandbox (no live Postgres
server / no network access there) - it is written to be correct and is
meant to be run against your own PostgreSQL instance. The loading logic
(especially the region_name -> region_id resolution for customers) has been
verified against the actual generated CSVs using pandas beforehand.
"""

import io
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

try:
    import psycopg2
except ImportError:
    print("psycopg2 is required: pip install psycopg2-binary --break-system-packages")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
SCHEMA_SQL = ROOT / "sql" / "schema.sql"

load_dotenv(ROOT / ".env")

DB_CONFIG = dict(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    dbname=os.getenv("DB_NAME", "marketlens"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", ""),
)


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def apply_schema(conn):
    print("[1/4] Applying sql/schema.sql ...")
    with open(SCHEMA_SQL, "r") as f:
        ddl = f.read()
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()
    print("      Schema applied.")


def copy_dataframe(conn, df: pd.DataFrame, table: str, columns: list[str]):
    """Fast bulk load via COPY FROM STDIN (CSV in-memory buffer)."""
    buf = io.StringIO()
    df[columns].to_csv(buf, index=False, header=False, na_rep="")
    buf.seek(0)
    with conn.cursor() as cur:
        cur.copy_expert(
            f"COPY {table} ({', '.join(columns)}) FROM STDIN WITH (FORMAT csv, NULL '')",
            buf,
        )
    conn.commit()


def load_all(conn):
    print("[2/4] Loading base/reference tables ...")
    regions = pd.read_csv(RAW_DIR / "regions.csv")
    stores = pd.read_csv(RAW_DIR / "stores.csv")
    products = pd.read_csv(RAW_DIR / "products.csv")
    campaigns = pd.read_csv(RAW_DIR / "marketing_campaigns.csv")

    copy_dataframe(conn, regions, "regions", ["region_id", "region_name"])
    copy_dataframe(conn, stores, "stores", ["store_id", "store_name", "region_id"])
    copy_dataframe(conn, products, "products",
                    ["product_id", "product_name", "category", "cost", "selling_price"])
    copy_dataframe(conn, campaigns, "marketing_campaigns",
                    ["campaign_id", "campaign_date", "campaign_type", "spend",
                     "customers_targeted", "customers_converted"])
    print(f"      regions={len(regions)}, stores={len(stores)}, "
          f"products={len(products)}, campaigns={len(campaigns)}")

    print("[3/4] Loading customers, orders, order_items, returns, costs ...")
    # Resolve region_name -> region_id (raw CSV stores the name; schema uses the FK id)
    customers = pd.read_csv(RAW_DIR / "customers.csv")
    customers = customers.merge(regions, left_on="region_name", right_on="region_name")
    customers["acquisition_campaign_id"] = customers["acquisition_campaign_id"].astype("Int64")
    copy_dataframe(conn, customers, "customers",
                    ["customer_id", "customer_name", "signup_date", "region_id",
                     "acquisition_campaign_id"])

    orders = pd.read_csv(RAW_DIR / "orders.csv")
    orders["store_id"] = orders["store_id"].astype("Int64")
    copy_dataframe(conn, orders, "orders",
                    ["order_id", "customer_id", "order_date", "channel", "store_id"])

    order_items = pd.read_csv(RAW_DIR / "order_items.csv")
    copy_dataframe(conn, order_items, "order_items",
                    ["order_item_id", "order_id", "product_id", "quantity",
                     "unit_price", "discount", "revenue"])

    returns = pd.read_csv(RAW_DIR / "returns.csv")
    copy_dataframe(conn, returns, "returns",
                    ["return_id", "order_id", "return_date", "return_reason", "return_amount"])

    costs = pd.read_csv(RAW_DIR / "costs.csv")
    copy_dataframe(conn, costs, "costs", ["order_id", "shipping_cost", "operational_cost"])

    print(f"      customers={len(customers)}, orders={len(orders)}, "
          f"order_items={len(order_items)}, returns={len(returns)}, costs={len(costs)}")


def smoke_test(conn):
    print("[4/4] Running smoke-test query (revenue by region) ...")
    query = """
        SELECT r.region_name AS region, SUM(oi.revenue) AS total_revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN regions r ON c.region_id = r.region_id
        GROUP BY r.region_name
        ORDER BY total_revenue DESC;
    """
    df = pd.read_sql(query, conn)
    print(df.to_string(index=False))
    return df


if __name__ == "__main__":
    conn = get_connection()
    try:
        apply_schema(conn)
        load_all(conn)
        smoke_test(conn)
        print("\n✅ Load complete.")
    finally:
        conn.close()
