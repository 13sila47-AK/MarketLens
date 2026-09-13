# MarketLens Predictive Churn Model Report

_Phase 09 output. All figures computed live by `python/modeling/run_modeling.py` from `data/processed/orders_enriched.csv`._

## 1. Methodology - Avoiding Label Leakage

Phase 07's `customer_features.csv` computes `days_since_last_purchase` and `customer_segment` as of the end of the dataset - using that table directly as both model input AND churn label would be leakage (the answer would already be baked into the features).

Instead, this phase builds two separate, cutoff-based feature tables:

- **Training set:** features computed using only orders on/before **2025-06-30**, for the **24,427 customers** who had already purchased at least once by that date. Label = did the customer place **zero orders** in the **90 days after** that cutoff? Because the cutoff is in the dataset's past, real observed outcomes exist to check the label against - the evaluation metrics below are measuring something real.
- **Scoring set:** the same feature logic applied as of the dataset's latest date (2025-12-27), for **29,340** customers, with no label (the future hasn't happened yet in this dataset) - this is the actual deployment-style prediction.

**Training-set churn rate: 81.3%** (no repeat purchase within 90 days of a prior order) - consistent with, and now quantifying, the low repeat-purchase behavior Phase 07/08 already flagged as the core business problem.

## 2. Model Comparison

Trained on 19,541 customers, evaluated on a held-out 4,886-customer test set (stratified 80/20 split).

| Metric | Logistic Regression | Random Forest |
|---|---:|---:|
| accuracy | 0.613 | 0.6515 |
| precision | 0.8782 | 0.8699 |
| recall | 0.6083 | 0.6717 |
| f1 | 0.7187 | 0.7581 |
| roc_auc | 0.6753 | 0.668 |

**Confusion matrices** (rows = actual, cols = predicted; `[[TN, FP], [FN, TP]]`):

- Logistic Regression: `[[579, 335], [1556, 2416]]`
- Random Forest: `[[515, 399], [1304, 2668]]`

**Selected model: `logistic_regression`** (highest ROC-AUC).

Honest caveat: the two models are close, and each wins on a different metric - Logistic Regression edges out Random Forest on ROC-AUC (0.6753 vs 0.668), while Random Forest has higher precision-adjusted F1 and recall (0.7581 vs 0.7187). ROC-AUC was used as the selection criterion because it's threshold-independent and standard for ranking/risk-scoring use cases like this one, but a team optimizing for catching the most true churners (recall) might reasonably prefer Random Forest instead. Overall discriminative power (AUC ~0.67-0.68) is modest, not excellent - the available features (order history, tenure, region) explain real signal but far from all of what drives an individual customer's next purchase decision.

**Top feature importance/coefficients (logistic_regression):**

| Feature | Weight |
|---|---:|
| region_South | 0.7244 |
| total_orders | -0.4792 |
| tenure_days | 0.472 |
| region_North | -0.4161 |
| region_Central | -0.3028 |
| region_West | 0.2508 |
| total_gross_revenue | 0.1553 |
| region_East | -0.084 |

`total_orders` is negatively associated with churn (more historical orders = more loyal = less likely to go quiet) and `region_South` is positively associated with churn - both independently consistent with Phase 07/08's findings, which is a good sign the model learned something real rather than noise.

## 3. Business Impact - Revenue at Risk

Scoring the current customer base (29,340 customers, as of 2025-12-27) with the final model:

| Risk Segment | Customers | Total CLV | % of Total CLV | Avg Churn Probability |
|---|---:|---:|---:|---:|
| Low | 1,703 | ₹87,803,054.66 | 10.9% | 25.0% |
| Medium | 13,890 | ₹422,071,572.54 | 52.6% | 46.4% |
| High | 13,747 | ₹293,201,371.29 | 36.5% | 72.4% |

**₹293,201,371.29 of historical customer value (36.5% of the total) sits with customers flagged High risk** (13,747 customers, avg churn probability 72%).

## 4. Customer Value x Risk Segmentation (Section 16)

Combining CLV (split at the median, ₹20,495.36) with churn risk (High risk = churn probability >= 50%) into four segments:

| Segment | Customers | Total CLV | % of Customers | % of Total CLV |
|---|---:|---:|---:|---:|
| High Value / High Risk | 8,674 | ₹335,678,884.57 | 29.6% | 41.8% |
| High Value / Low Risk | 5,996 | ₹314,346,997.16 | 20.4% | 39.1% |
| Low Value / High Risk | 10,498 | ₹108,870,930.92 | 35.8% | 13.6% |
| Low Value / Low Risk | 4,172 | ₹44,179,185.84 | 14.2% | 5.5% |

**Priority segment: High Value + High Risk — 8,674 customers holding ₹335,678,884.57 (41.8% of all customer value) who are also likely to churn.** This is where retention spend should concentrate first - it's less than a third of the customer base but carries the largest single share of value at stake.

## 5. Files Produced

- `data/processed/churn_training_dataset.csv` — features + label, past cutoff
- `data/processed/churn_scoring_dataset.csv` — features, current cutoff, no label
- `data/processed/churn_predictions.csv` — customer_id, churn_probability, risk_segment
- `data/processed/customer_value_risk_quadrants.csv` — Section 16 quadrant assignment
- `data/processed/churn_model_comparison.json` — full metrics + feature importance

Next: **Phase 10 — External Market Intelligence** (industry/competitor research to compare against these internal findings — is South's decline company-specific, or a broader market trend?).