"""
MarketLens - Phase 09: Predictive Churn Model
python/modeling/train_churn_model.py
==============================================================================
Pipeline:
  customer data (churn_features.py)
        -> feature engineering (numeric + one-hot region)
        -> train/test split (stratified, 80/20)
        -> Logistic Regression  (scaled features, class_weight='balanced')
        -> Random Forest        (class_weight='balanced')
        -> model comparison (accuracy, precision, recall, F1, ROC-AUC)
        -> best model selected on ROC-AUC
        -> best model class refit on the FULL training dataset
        -> applied to the scoring dataset (features as of "now")
        -> churn_probability + risk_segment per customer
"""

from __future__ import annotations

import json
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC_FEATURES = [
    "total_orders", "total_gross_revenue", "avg_order_value",
    "days_since_last_purchase", "tenure_days", "purchase_frequency",
    "return_rate", "discount_usage", "online_share",
]
CATEGORICAL_FEATURES = ["region"]
TARGET = "churned"
RANDOM_STATE = 42


def _preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])


def _metrics(y_true, y_pred, y_proba) -> dict:
    cm = confusion_matrix(y_true, y_pred).tolist()
    return {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred), 4),
        "recall": round(recall_score(y_true, y_pred), 4),
        "f1": round(f1_score(y_true, y_pred), 4),
        "roc_auc": round(roc_auc_score(y_true, y_proba), 4),
        "confusion_matrix": cm,  # [[TN, FP], [FN, TP]]
    }


def train_and_compare(train_df: pd.DataFrame) -> dict:
    X = train_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = train_df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    models = {
        "logistic_regression": Pipeline([
            ("prep", _preprocessor()),
            ("clf", LogisticRegression(
                class_weight="balanced", max_iter=1000, random_state=RANDOM_STATE
            )),
        ]),
        "random_forest": Pipeline([
            ("prep", _preprocessor()),
            ("clf", RandomForestClassifier(
                n_estimators=300, max_depth=8, min_samples_leaf=20,
                class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1,
            )),
        ]),
    }

    results = {}
    fitted = {}
    for name, pipe in models.items():
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        y_proba = pipe.predict_proba(X_test)[:, 1]
        results[name] = _metrics(y_test, y_pred, y_proba)
        fitted[name] = pipe

    best_name = max(results, key=lambda n: results[n]["roc_auc"])

    # Feature importance (random forest) / coefficients (logistic) for the
    # winning model family, for interpretability in the report.
    best_pipe_test = fitted[best_name]
    feature_names = (
        NUMERIC_FEATURES
        + list(best_pipe_test.named_steps["prep"]
               .named_transformers_["cat"].get_feature_names_out(CATEGORICAL_FEATURES))
    )
    clf = best_pipe_test.named_steps["clf"]
    if hasattr(clf, "feature_importances_"):
        importance = dict(zip(feature_names, clf.feature_importances_.round(4).tolist()))
    else:
        importance = dict(zip(feature_names, clf.coef_[0].round(4).tolist()))
    importance = dict(sorted(importance.items(), key=lambda kv: -abs(kv[1])))

    # Refit the winning model TYPE on the full training dataset for deployment scoring.
    final_pipe = models[best_name]
    final_pipe.fit(X, y)

    return {
        "results": results,
        "best_model": best_name,
        "feature_importance": importance,
        "final_pipeline": final_pipe,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "class_balance_train": y.mean(),
    }


def score_customers(pipeline: Pipeline, score_df: pd.DataFrame) -> pd.DataFrame:
    X_score = score_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    proba = pipeline.predict_proba(X_score)[:, 1]

    out = score_df[["customer_id", "customer_lifetime_value_to_date",
                     "days_since_last_purchase", "total_orders"]].copy()
    out["churn_probability"] = proba.round(4)
    out["risk_segment"] = pd.cut(
        out["churn_probability"],
        bins=[-0.01, 0.30, 0.60, 1.01],
        labels=["Low", "Medium", "High"],
    )
    return out


if __name__ == "__main__":
    train_df = pd.read_csv("data/processed/churn_training_dataset.csv")
    score_df = pd.read_csv("data/processed/churn_scoring_dataset.csv")

    comparison = train_and_compare(train_df)

    print("=" * 70)
    print("Model comparison (test set, n=%d)" % comparison["n_test"])
    print("=" * 70)
    for name, m in comparison["results"].items():
        print(f"\n{name}:")
        for k, v in m.items():
            print(f"  {k}: {v}")
    print(f"\nBest model (by ROC-AUC): {comparison['best_model']}")
    print(f"\nTop feature importance/coefficients ({comparison['best_model']}):")
    for k, v in list(comparison["feature_importance"].items())[:8]:
        print(f"  {k}: {v}")

    predictions = score_customers(comparison["final_pipeline"], score_df)
    predictions.to_csv("data/processed/churn_predictions.csv", index=False)
    print(f"\nWrote data/processed/churn_predictions.csv ({len(predictions):,} customers)")
    print(predictions["risk_segment"].value_counts())

    with open("data/processed/churn_model_comparison.json", "w") as f:
        json.dump({
            "results": comparison["results"],
            "best_model": comparison["best_model"],
            "feature_importance": comparison["feature_importance"],
            "n_train": comparison["n_train"],
            "n_test": comparison["n_test"],
            "class_balance_train_churn_rate": round(float(comparison["class_balance_train"]), 4),
        }, f, indent=2)
    print("Wrote data/processed/churn_model_comparison.json")
