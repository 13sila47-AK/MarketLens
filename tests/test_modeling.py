"""
Phase 17 - ML tests (spec section 33):
    - Features exist
    - Prediction probabilities valid
    - Output has expected columns

Runs the real Phase 09 pipeline (churn_features -> train_churn_model ->
clv_segments) end-to-end on the actual dataset. This is intentionally the
slowest file in the suite (it trains two real models), so keep it scoped to
one shared fixture rather than retraining per test.
"""

from __future__ import annotations

import pandas as pd
import pytest

import churn_features as cfeat
import train_churn_model as tcm
import clv_segments as clv

EXPECTED_FEATURE_COLUMNS = {
    "customer_id", "region",
    "total_orders", "total_gross_revenue", "avg_order_value",
    "days_since_last_purchase", "tenure_days", "purchase_frequency",
    "return_rate", "discount_usage", "online_share",
    "customer_lifetime_value_to_date",
}


@pytest.fixture(scope="module")
def training_dataset():
    return cfeat.build_training_dataset()


@pytest.fixture(scope="module")
def scoring_dataset():
    return cfeat.build_scoring_dataset()


@pytest.fixture(scope="module")
def model_results(training_dataset):
    return tcm.train_and_compare(training_dataset)


@pytest.fixture(scope="module")
def scored_customers(model_results, scoring_dataset):
    return tcm.score_customers(model_results["final_pipeline"], scoring_dataset)


# ---------------------------------------------------------------------------
# Features exist
# ---------------------------------------------------------------------------

def test_training_dataset_has_expected_feature_columns(training_dataset):
    assert EXPECTED_FEATURE_COLUMNS.issubset(training_dataset.columns)
    assert "churned" in training_dataset.columns


def test_scoring_dataset_has_expected_feature_columns(scoring_dataset):
    assert EXPECTED_FEATURE_COLUMNS.issubset(scoring_dataset.columns)
    assert "churned" not in scoring_dataset.columns, (
        "Scoring dataset must NOT have a label - the future hasn't happened "
        "in this dataset at the scoring cutoff (leakage check)."
    )


def test_training_dataset_no_missing_values_in_model_features(training_dataset):
    feature_cols = tcm.NUMERIC_FEATURES + tcm.CATEGORICAL_FEATURES
    assert training_dataset[feature_cols].isna().sum().sum() == 0


def test_churn_label_is_binary(training_dataset):
    assert set(training_dataset["churned"].unique()).issubset({0, 1})


def test_training_dataset_has_both_classes(training_dataset):
    """A model can't be trained/evaluated meaningfully on a single class."""
    assert training_dataset["churned"].nunique() == 2


# ---------------------------------------------------------------------------
# Prediction probabilities valid
# ---------------------------------------------------------------------------

def test_model_comparison_has_both_models(model_results):
    assert set(model_results["results"].keys()) == {"logistic_regression", "random_forest"}


def test_model_metrics_within_valid_ranges(model_results):
    for name, metrics in model_results["results"].items():
        for key in ["accuracy", "precision", "recall", "f1", "roc_auc"]:
            assert 0.0 <= metrics[key] <= 1.0, f"{name}.{key} = {metrics[key]} out of [0, 1]"


def test_best_model_is_one_of_the_two_trained(model_results):
    assert model_results["best_model"] in model_results["results"]


def test_churn_probabilities_are_valid_probabilities(scored_customers):
    proba = scored_customers["churn_probability"]
    assert proba.notna().all()
    assert ((proba >= 0.0) & (proba <= 1.0)).all(), "churn_probability outside [0, 1]"


def test_risk_segment_labels_are_valid(scored_customers):
    assert set(scored_customers["risk_segment"].dropna().unique()).issubset(
        {"Low", "Medium", "High"}
    )


def test_risk_segment_matches_probability_bins(scored_customers):
    """Low < 0.30 <= Medium < 0.60 <= High, per the score_customers cut."""
    bad_low = scored_customers[
        (scored_customers["risk_segment"] == "Low") & (scored_customers["churn_probability"] > 0.30)
    ]
    bad_high = scored_customers[
        (scored_customers["risk_segment"] == "High") & (scored_customers["churn_probability"] <= 0.60)
    ]
    assert bad_low.empty and bad_high.empty


# ---------------------------------------------------------------------------
# Output has expected columns
# ---------------------------------------------------------------------------

def test_score_customers_output_columns(scored_customers):
    expected = {
        "customer_id", "customer_lifetime_value_to_date",
        "days_since_last_purchase", "total_orders",
        "churn_probability", "risk_segment",
    }
    assert expected.issubset(scored_customers.columns)


def test_score_customers_covers_every_scoring_row(scored_customers, scoring_dataset):
    assert len(scored_customers) == len(scoring_dataset)


def test_value_risk_quadrants_output_columns(scored_customers):
    quadrants = clv.build_value_risk_quadrants(scored_customers)
    assert {"value_tier", "risk_tier", "quadrant"}.issubset(quadrants.columns)
    assert set(quadrants["value_tier"].unique()).issubset({"High Value", "Low Value"})
    assert set(quadrants["risk_tier"].unique()).issubset({"High Risk", "Low Risk"})


def test_quadrant_summary_percentages_sum_to_100(scored_customers):
    quadrants = clv.build_value_risk_quadrants(scored_customers)
    summary = clv.quadrant_summary(quadrants)
    assert summary["pct_of_customers"].sum() == pytest.approx(100.0, abs=0.01)
    assert summary["pct_of_total_clv"].sum() == pytest.approx(100.0, abs=0.01)


def test_high_value_high_risk_is_a_real_priority_segment(scored_customers):
    """Regression check for the priority segment the diagnosis/recommendations
    phases depend on (spec section 16) - it must actually exist with >0
    customers, not just be a theoretical label."""
    quadrants = clv.build_value_risk_quadrants(scored_customers)
    summary = clv.quadrant_summary(quadrants)
    hv_hr = summary[summary["quadrant"] == "High Value / High Risk"]
    assert not hv_hr.empty
    assert int(hv_hr["customers"].iloc[0]) > 0
