"""
MarketLens - Phase 09: Predictive Churn Model
python/modeling/churn_features.py
==============================================================================
Builds churn modeling datasets from orders_enriched.csv at a given cutoff
date, using ONLY information available as of that cutoff. This is the part
that's easy to get wrong: Phase 07's customer_features.csv computes
`days_since_last_purchase` and `customer_segment` as of the END of the
dataset - using that table directly as both features AND a churn label would
be leakage (the label would already be baked into the features).

Two datasets come out of this module:

1. TRAINING data - features as of a past cutoff (CUTOFF_TRAIN), label = did
   the customer place zero orders in the FUTURE_WINDOW_DAYS after that
   cutoff? Because the cutoff is in the past, we have real observed
   outcomes to check the label against - this is what makes the model
   honestly evaluable (Phase 09/15's accuracy/precision/recall/ROC-AUC are
   measuring something real, not something invented).

2. SCORING data - features as of the dataset's latest date (CUTOFF_NOW), no
   label (the future hasn't happened yet in this dataset). This is what a
   trained model gets applied to in Phase 09's actual deliverable: current
   churn_probability per customer.
"""

from __future__ import annotations

import pandas as pd
import numpy as np

FUTURE_WINDOW_DAYS = 90
CUTOFF_TRAIN = "2025-06-30"  # leaves ~180 days of real future data to check against


def _load_orders() -> pd.DataFrame:
    o = pd.read_csv("data/processed/orders_enriched.csv")
    o["order_date"] = pd.to_datetime(o["order_date"])
    o["signup_date"] = pd.to_datetime(o["signup_date"])
    return o


def _build_features(orders: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    """Features computed using ONLY orders with order_date <= cutoff."""
    hist = orders[orders["order_date"] <= cutoff].copy()

    hist["pre_discount_revenue"] = hist["gross_revenue"] + hist["total_discount"]

    agg = hist.groupby("customer_id").agg(
        region=("region", "first"),
        signup_date=("signup_date", "first"),
        total_orders=("order_id", "count"),
        total_gross_revenue=("gross_revenue", "sum"),
        total_net_revenue=("net_revenue", "sum"),
        total_pre_discount_revenue=("pre_discount_revenue", "sum"),
        total_discount=("total_discount", "sum"),
        total_returned_amount=("total_returned_amount", "sum"),
        total_return_count=("return_count", "sum"),
        n_online_orders=("channel", lambda s: (s == "online").sum()),
        first_order_date=("order_date", "min"),
        last_order_date=("order_date", "max"),
    ).reset_index()

    agg["avg_order_value"] = agg["total_gross_revenue"] / agg["total_orders"]
    agg["days_since_last_purchase"] = (cutoff - agg["last_order_date"]).dt.days
    agg["tenure_days"] = (cutoff - agg["signup_date"]).dt.days
    agg["customer_age_days"] = (cutoff - agg["first_order_date"]).dt.days.clip(lower=1)
    agg["purchase_frequency"] = agg["total_orders"] / (agg["customer_age_days"] / 30.0)
    agg["return_rate"] = agg["total_return_count"] / agg["total_orders"]
    agg["discount_usage"] = np.where(
        agg["total_pre_discount_revenue"] > 0,
        agg["total_discount"] / agg["total_pre_discount_revenue"],
        0.0,
    )
    agg["online_share"] = agg["n_online_orders"] / agg["total_orders"]
    agg["customer_lifetime_value_to_date"] = agg["total_net_revenue"]

    keep = [
        "customer_id", "region",
        "total_orders", "total_gross_revenue", "avg_order_value",
        "days_since_last_purchase", "tenure_days", "purchase_frequency",
        "return_rate", "discount_usage", "online_share",
        "customer_lifetime_value_to_date",
    ]
    return agg[keep]


def build_training_dataset(orders: pd.DataFrame | None = None) -> pd.DataFrame:
    """Features as of CUTOFF_TRAIN + label from the FUTURE_WINDOW_DAYS after it.

    Only customers with >=1 order on/before CUTOFF_TRAIN are included -
    this is a model of "will an existing/historical customer keep
    purchasing?", consistent with Phase 07's finding that retention, not
    acquisition, is where the business problem lives.
    """
    if orders is None:
        orders = _load_orders()

    cutoff = pd.Timestamp(CUTOFF_TRAIN)
    horizon_end = cutoff + pd.Timedelta(days=FUTURE_WINDOW_DAYS)

    features = _build_features(orders, cutoff)

    future_orders = orders[
        (orders["order_date"] > cutoff) & (orders["order_date"] <= horizon_end)
    ]
    purchased_in_future = set(future_orders["customer_id"].unique())

    features["churned"] = (~features["customer_id"].isin(purchased_in_future)).astype(int)

    max_date = orders["order_date"].max()
    assert max_date >= horizon_end, (
        f"Not enough future data to validate a {FUTURE_WINDOW_DAYS}-day window "
        f"after {CUTOFF_TRAIN} (data ends {max_date.date()})."
    )
    return features


def build_scoring_dataset(orders: pd.DataFrame | None = None) -> pd.DataFrame:
    """Features as of the LATEST date in the dataset. No label - this is
    real deployment-time scoring, predicting churn that hasn't happened
    (or not) yet."""
    if orders is None:
        orders = _load_orders()
    cutoff = orders["order_date"].max()
    features = _build_features(orders, cutoff)
    features.attrs["cutoff_date"] = str(cutoff.date())
    return features


if __name__ == "__main__":
    orders = _load_orders()

    train_df = build_training_dataset(orders)
    print(f"Training dataset: {len(train_df):,} customers as of {CUTOFF_TRAIN}")
    print(f"Churn rate (no purchase in next {FUTURE_WINDOW_DAYS} days): "
          f"{train_df['churned'].mean() * 100:.1f}%")

    score_df = build_scoring_dataset(orders)
    print(f"\nScoring dataset: {len(score_df):,} customers as of "
          f"{score_df.attrs['cutoff_date']}")

    train_df.to_csv("data/processed/churn_training_dataset.csv", index=False)
    score_df.to_csv("data/processed/churn_scoring_dataset.csv", index=False)
    print("\nWrote data/processed/churn_training_dataset.csv")
    print("Wrote data/processed/churn_scoring_dataset.csv")
