"""
MarketLens - Phase 07: Business Analytics Engine
==================================================
Shared loading helpers. Every analytics module (revenue, profitability,
customer, product, marketing) reads from the SAME two Phase 05 outputs, so
every KPI in this engine is traceable back to `data/processed/*.csv` and,
from there, to the raw CSVs validated clean in Phase 06.

    order_items_enriched.csv  -> item/product-grain analysis
    orders_enriched.csv       -> order/customer/marketing-grain analysis
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
RAW_DIR = ROOT / "data" / "raw"


def load_orders() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "orders_enriched.csv", parse_dates=["order_date", "signup_date"])
    return df


def load_order_items() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "order_items_enriched.csv", parse_dates=["order_date", "signup_date"])
    return df


def load_customers() -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / "customers.csv", parse_dates=["signup_date"])


def load_campaigns() -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / "marketing_campaigns.csv", parse_dates=["campaign_date"])


def load_returns() -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / "returns.csv", parse_dates=["return_date"])


def as_of_date(orders: pd.DataFrame | None = None) -> pd.Timestamp:
    """The 'today' the whole analytics engine reasons from: the most recent
    order date in the dataset (this is historical data, not live data, so
    'now' is defined by the data itself, not the wall clock)."""
    if orders is None:
        orders = load_orders()
    return orders["order_date"].max()
