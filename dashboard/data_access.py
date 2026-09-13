"""
MarketLens - Phase 16: Streamlit Dashboard
============================================
Shared data-access layer for every dashboard page.

Design principle (same one Phase 15's AI analyst follows): the dashboard
NEVER recomputes a KPI from scratch. Every number rendered here is read
straight from a file that an earlier, already-verified phase wrote:

    data/raw/*.csv                        -> Phase 03 (source data)
    data/processed/orders_enriched.csv    -> Phase 05
    data/processed/order_items_enriched.csv -> Phase 05
    data/processed/kpi_*.csv              -> Phase 07 (business analytics)
    data/processed/customer_features.csv  -> Phase 07
    data/processed/churn_predictions.csv,
    data/processed/customer_value_risk_quadrants.csv,
    data/processed/churn_model_comparison.json -> Phase 09 (modeling)
    data/processed/scenario_comparison.csv -> Phase 12 (scenario engine)
    data/processed/diagnosis_evidence.json -> Phase 13 (diagnosis)
    data/processed/recommendations.json    -> Phase 14 (recommendations)

If a page needs a number that isn't in one of these files, that's a sign
the number should have been computed by an earlier phase, not invented
here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"


# ---------------------------------------------------------------------------
# Raw / processed CSV loaders
# ---------------------------------------------------------------------------

@st.cache_data
def load_orders_enriched() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "orders_enriched.csv", parse_dates=["order_date", "signup_date"])


@st.cache_data
def load_order_items_enriched() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "order_items_enriched.csv", parse_dates=["order_date", "signup_date"])


@st.cache_data
def load_customer_features() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "customer_features.csv", parse_dates=["signup_date"])


@st.cache_data
def load_customers_raw() -> pd.DataFrame:
    return pd.read_csv(RAW / "customers.csv", parse_dates=["signup_date"])


@st.cache_data
def load_kpi(name: str) -> pd.DataFrame:
    """Generic loader for any data/processed/kpi_*.csv file."""
    return pd.read_csv(PROCESSED / f"kpi_{name}.csv")


@st.cache_data
def load_churn_predictions() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "churn_predictions.csv")


@st.cache_data
def load_customer_quadrants() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "customer_value_risk_quadrants.csv")


@st.cache_data
def load_churn_model_comparison() -> dict:
    with open(PROCESSED / "churn_model_comparison.json") as f:
        return json.load(f)


@st.cache_data
def load_scenario_comparison() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "scenario_comparison.csv")


@st.cache_data
def load_diagnosis_evidence() -> dict:
    with open(PROCESSED / "diagnosis_evidence.json") as f:
        return json.load(f)


@st.cache_data
def load_recommendations() -> dict:
    with open(PROCESSED / "recommendations.json") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Small derived helpers used across multiple pages
# ---------------------------------------------------------------------------

@st.cache_data
def executive_summary() -> dict:
    """Headline numbers for the Executive Overview page (section 27),
    each sourced from an already-verified Phase 07/11/13 file."""
    margin_trend = load_kpi("margin_trend_yoy")
    row_2025 = margin_trend[margin_trend["year"] == 2025].iloc[0]
    row_2024 = margin_trend[margin_trend["year"] == 2024].iloc[0]

    customers = load_customers_raw()
    diagnosis = load_diagnosis_evidence()
    recs = load_recommendations()

    return {
        "revenue_2025": float(row_2025["gross_revenue"]),
        "gross_profit_2025": float(row_2025["gross_profit"]),
        "gross_margin_pct_2025": float(row_2025["gross_margin_pct"]),
        "revenue_growth_pct": diagnosis["revenue_deceleration"]["yoy_growth_2024_to_2025_pct"],
        "profit_growth_pct": round(
            (float(row_2025["gross_profit"]) / float(row_2024["gross_profit"]) - 1) * 100, 2
        ),
        "net_profit_2025": diagnosis["financial_baseline"]["fy2025_net_profit"],
        "net_margin_pct_2025": diagnosis["financial_baseline"]["fy2025_net_margin_pct"],
        "total_customers": int(len(customers)),
        "top_business_issue": diagnosis["causal_chain"][0],
        "top_region_issue": diagnosis["causal_chain"][1],
        "top_customer_issue": diagnosis["churn_model_findings"],
        "top_recommendation": recs["recommendations"][0],
    }


def inr(value: float, decimals: int = 1) -> str:
    """Format a rupee amount in Lakh/Crore-friendly short form for KPI cards."""
    value = float(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1e7:
        return f"{sign}\u20b9{value / 1e7:.{decimals}f} Cr"
    if value >= 1e5:
        return f"{sign}\u20b9{value / 1e5:.{decimals}f} L"
    return f"{sign}\u20b9{value:,.0f}"
