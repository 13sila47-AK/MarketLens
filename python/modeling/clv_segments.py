"""
MarketLens - Phase 09: Predictive Churn Model
python/modeling/clv_segments.py
==============================================================================
Section 16 of the spec: combine Customer Lifetime Value with churn risk into
four segments (High/Low Value x High/Low Risk). The priority segment for
retention spend is High Value + High Risk - customers worth the most who are
also the most likely to leave.
"""

from __future__ import annotations

import pandas as pd


def build_value_risk_quadrants(predictions: pd.DataFrame) -> pd.DataFrame:
    """predictions must have customer_lifetime_value_to_date and
    churn_probability columns (i.e. the output of train_churn_model.score_customers)."""
    df = predictions.copy()
    median_clv = df["customer_lifetime_value_to_date"].median()

    df["value_tier"] = df["customer_lifetime_value_to_date"].apply(
        lambda x: "High Value" if x >= median_clv else "Low Value"
    )
    df["risk_tier"] = df["churn_probability"].apply(
        lambda p: "High Risk" if p >= 0.5 else "Low Risk"
    )
    df["quadrant"] = df["value_tier"] + " / " + df["risk_tier"]
    df.attrs["median_clv_split"] = median_clv
    return df


def quadrant_summary(df_with_quadrants: pd.DataFrame) -> pd.DataFrame:
    summary = df_with_quadrants.groupby("quadrant").agg(
        customers=("customer_id", "count"),
        total_clv=("customer_lifetime_value_to_date", "sum"),
        avg_clv=("customer_lifetime_value_to_date", "mean"),
        avg_churn_probability=("churn_probability", "mean"),
    ).reset_index()
    summary["pct_of_customers"] = summary["customers"] / summary["customers"].sum() * 100
    summary["pct_of_total_clv"] = summary["total_clv"] / summary["total_clv"].sum() * 100
    return summary.sort_values("total_clv", ascending=False)


if __name__ == "__main__":
    predictions = pd.read_csv("data/processed/churn_predictions.csv")
    quadrants = build_value_risk_quadrants(predictions)
    summary = quadrant_summary(quadrants)

    print(f"Median CLV split point: \u20b9{quadrants.attrs['median_clv_split']:,.2f}\n")
    print(summary.to_string(index=False))

    priority = quadrants[quadrants["quadrant"] == "High Value / High Risk"]
    print(f"\nPriority segment (High Value + High Risk): {len(priority):,} customers, "
          f"\u20b9{priority['customer_lifetime_value_to_date'].sum():,.2f} CLV at stake")

    quadrants.to_csv("data/processed/customer_value_risk_quadrants.csv", index=False)
    print("\nWrote data/processed/customer_value_risk_quadrants.csv")
