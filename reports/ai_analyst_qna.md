# MarketLens — AI Business Analyst: Sample Q&A

_Generated: 2026-09-12 17:53_
_Provider: offline_

> **Note:** This report was generated in a sandbox with no internet access, so no real OpenAI/Gemini call could be made (the same constraint that affected PostgreSQL, R, and Faker in earlier phases). Every answer below shows the exact evidence-bundle context the LLM prompt would have received, so the retrieval-and-grounding pipeline can be verified end-to-end. Set `OPENAI_API_KEY` or `GEMINI_API_KEY` in `.env` (provider selected via `LLM_PROVIDER`) and re-run `python python/analytics/run_ai_analyst.py` on a machine with internet access to regenerate this file with genuine LLM-authored explanations of the same underlying facts — no code changes needed.

## Q1: Why did revenue growth slow down in 2025?

[OFFLINE MODE — deterministic evidence lookup, not a real LLM response. See run_ai_analyst.py / llm_provider.py for how to enable a genuine OpenAI/Gemini call once run with internet access.]

Finding: Company revenue growth is decelerating, not reversing.

Evidence:
  - +98% YoY (2023->2024) slowing to +13% YoY (2024->2025); statistically confirmed deceleration, not just early-stage base effects (quadratic trend p=6.7e-11). (Source: data/processed/kpi_margin_trend_yoy.csv (Phase 07), reports/statistical_analysis_report.md (Phase 08, Section 1))
  - 8,674 customers are classified High Value + High Risk, holding Rs 335,678,885 (41.8% of all customer value) at churn risk (reports/churn_model_report.md, Phase 09). Scenario testing shows a +5pp retention improvement is worth Rs 13,680,404 in incremental annual net profit -- the single highest-value lever tested (reports/scenario_analysis_report.md, Phase 12). (Source: Phase 14 recommendation, priority 1)

Possible Causes: This finding's evidence text above already states the mechanism identified by the analysis; the evidence bundle does not separately decompose further root causes beyond what is shown.

Confidence: High (statistically tested, see p-values above)

Recommendation: Launch a targeted retention program (personalized win-back offers, proactive outreach, loyalty incentives) aimed first at the 8,674 High-Value + High-Risk customers, since they carry the largest share of value at stake per customer reached. Use the churn model's probability scores (churn_predictions.csv) to prioritize outreach timing and channel.

Expected Impact: {"potential_customers_affected": 8674, "expected_revenue_impact_note": "The modeled financial outcome is the company-wide +5pp retention scenario (Rs 13,680,404 incremental net profit, Phase 12); this program is the operational mechanism proposed to help achieve that lift by concentrating effort on the highest-value at-risk segment, not a separately fitted number.", "expected_incremental_profit": 13680404.1, "implementation_cost_assumption": "Planning assumption: Rs 200 per targeted customer for personalized retention outreach/incentives (8,674 x Rs 200 = Rs 1,734,800). Not a measured figure -- a reasonable consulting-style planning estimate.", "implementation_cost": 1734800.0, "roi_pct": 688.6}

Risks: Retention lift is modeled at the aggregate +5pp level, not validated as achievable specifically by targeting this segment -- actual response to outreach could be lower than the blended model assumes. Churn model AUC is modest (~0.67-0.68), so targeting will include some false positives/negatives.

## Q2: Why is the South region declining, and is it a pricing problem?

[OFFLINE MODE — deterministic evidence lookup, not a real LLM response. See run_ai_analyst.py / llm_provider.py for how to enable a genuine OpenAI/Gemini call once run with internet access.]

Finding: South revenue declined ~24.7% in FY2025 while the broader Indian e-commerce/retail market grew ~11-13% -- a company-specific execution problem, not a market contraction (Phase 13, Step 2 and Section 19).

Evidence:
  - South has the HIGHEST per-order margin of any region (31.84% aggregate / 32.68% per-order), ruling out pricing as the cause. region_South is the strongest positive churn predictor in the logistic regression model (coefficient 0.7244, reports/churn_model_report.md, Phase 09) -- pointing to a retention/execution gap specific to the region (service quality, delivery, local competition, or store/ops issues), not demand. (Source: Phase 14 recommendation, priority 3)
  - South's per-order margin (32.68%) is the HIGHEST of any region (North lowest at 32.03%), though the regional spread is small (~0.6-0.7pp). Combined with churn modeling where region_South is the single strongest positive churn predictor, South looks like a traffic/retention execution gap, not a pricing problem that discounting more could fix. (Source: reports/statistical_analysis_report.md (Phase 08, Section 3), reports/churn_model_report.md (Phase 09))

Possible Causes: This finding's evidence text above already states the mechanism identified by the analysis; the evidence bundle does not separately decompose further root causes beyond what is shown.

Confidence: Medium (descriptive evidence; see source report for any statistical testing)

Recommendation: Commission a focused operational review of South (store operations, delivery/service quality, local competitive positioning) and pilot a regional recovery program -- localized retention outreach plus operational fixes -- before allocating further blanket marketing spend, since Phase 12 showed marketing spend increases are not shown to pay for themselves at the company level.

Expected Impact: {"potential_customers_affected": 4800, "expected_revenue_impact": 18230184.519600004, "expected_revenue_impact_note": "If South had grown at the 12% market benchmark instead of declining, FY2025 South revenue would have been Rs 55,636,939 vs the actual Rs 37,406,754 -- a Rs 18,230,185 gap, computed directly from Phase 07's regional trend data.", "expected_incremental_profit": 5804490.751040641, "implementation_cost_assumption": "Planning assumption: Rs 2,000,000 for a regional operational review and pilot recovery program (audit, service improvements, localized retention outreach for South's 4,800 customers).", "implementation_cost": 2000000.0, "roi_pct": 190.2}

Risks: The recoverable-value estimate assumes South could have matched the market benchmark growth rate purely by fixing execution -- this is a gap estimate, not a validated forecast of what a recovery program would actually achieve, and the true cause (service, delivery, competition, or something else) has not yet been diagnosed at the root-cause level. Smallest expected financial impact of the three recommendations, but addresses the only regionally-concentrated decline directly.

## Q3: Which customers should we prioritize for retention, and how much value is at risk?

[OFFLINE MODE — deterministic evidence lookup, not a real LLM response. See run_ai_analyst.py / llm_provider.py for how to enable a genuine OpenAI/Gemini call once run with internet access.]

Finding: Monthly customer retention has declined from 13.96% to 11.98% (statistically confirmed, p=9.5e-12), and 81.3% of customers in the churn model's training cohort made no repeat purchase within 90 days. This is the single largest driver of the revenue growth deceleration (Phase 13, Steps 1 and 4).

Evidence:
  - 8,674 customers are classified High Value + High Risk, holding Rs 335,678,885 (41.8% of all customer value) at churn risk (reports/churn_model_report.md, Phase 09). Scenario testing shows a +5pp retention improvement is worth Rs 13,680,404 in incremental annual net profit -- the single highest-value lever tested (reports/scenario_analysis_report.md, Phase 12). (Source: Phase 14 recommendation, priority 1)
  - 8,674 customers classified High Value + High Risk hold Rs 335,678,885 (41.8% of all customer value) -- under a third of the customer base carries the largest single share of value that retention efforts could protect. (Source: reports/churn_model_report.md (Phase 09))

Possible Causes: This finding's evidence text above already states the mechanism identified by the analysis; the evidence bundle does not separately decompose further root causes beyond what is shown.

Confidence: High (statistically tested, see p-values above)

Recommendation: Launch a targeted retention program (personalized win-back offers, proactive outreach, loyalty incentives) aimed first at the 8,674 High-Value + High-Risk customers, since they carry the largest share of value at stake per customer reached. Use the churn model's probability scores (churn_predictions.csv) to prioritize outreach timing and channel.

Expected Impact: {"potential_customers_affected": 8674, "expected_revenue_impact_note": "The modeled financial outcome is the company-wide +5pp retention scenario (Rs 13,680,404 incremental net profit, Phase 12); this program is the operational mechanism proposed to help achieve that lift by concentrating effort on the highest-value at-risk segment, not a separately fitted number.", "expected_incremental_profit": 13680404.1, "implementation_cost_assumption": "Planning assumption: Rs 200 per targeted customer for personalized retention outreach/incentives (8,674 x Rs 200 = Rs 1,734,800). Not a measured figure -- a reasonable consulting-style planning estimate.", "implementation_cost": 1734800.0, "roi_pct": 688.6}

Risks: Retention lift is modeled at the aggregate +5pp level, not validated as achievable specifically by targeting this segment -- actual response to outreach could be lower than the blended model assumes. Churn model AUC is modest (~0.67-0.68), so targeting will include some false positives/negatives.

## Q4: Is discounting hurting our margins?

[OFFLINE MODE — deterministic evidence lookup, not a real LLM response. See run_ai_analyst.py / llm_provider.py for how to enable a genuine OpenAI/Gemini call once run with internet access.]

Finding: Gross margin fell from 34.29% (2023) to 29.47% (2025) as discount rate nearly doubled, 7.04% to 13.44% of order value (Phase 13, Step 5).

Evidence:
  - High-discount orders (top quartile, >=13.48% discount rate) average 28.90% margin vs 35.61% for low-discount orders (Welch t-test p < 1e-300; reports/statistical_analysis_report.md, Phase 08). Scenario testing shows a -2pp discount rate reduction at the same order volume is worth Rs 8,501,040 in incremental annual net profit (reports/scenario_analysis_report.md, Phase 12). (Source: Phase 14 recommendation, priority 2)
  - South's per-order margin (32.68%) is the HIGHEST of any region (North lowest at 32.03%), though the regional spread is small (~0.6-0.7pp). Combined with churn modeling where region_South is the single strongest positive churn predictor, South looks like a traffic/retention execution gap, not a pricing problem that discounting more could fix. (Source: reports/statistical_analysis_report.md (Phase 08, Section 3), reports/churn_model_report.md (Phase 09))

Possible Causes: This finding's evidence text above already states the mechanism identified by the analysis; the evidence bundle does not separately decompose further root causes beyond what is shown.

Confidence: High (statistically tested, see p-values above)

Recommendation: Introduce a discount approval workflow/threshold for orders in the top discount quartile, and review whether current blanket discount levels are necessary to hold volume, given South -- the region with a genuine volume problem -- already has the highest per-order margin without needing the deepest discounts.

Expected Impact: {"potential_orders_affected": "Top discount quartile of FY2025 orders (~9,115 of 36,459)", "expected_revenue_impact_note": "This is a margin-recovery lever, not new revenue: it recovers profit from the SAME order volume by charging closer to full price, rather than generating additional orders.", "expected_incremental_profit": 8501039.74, "implementation_cost_assumption": "Planning assumption: Rs 500,000 one-time for discount governance tooling/workflow and staff training -- this is a policy/process change, not new spend on customers, so cost is low relative to the other two recommendations.", "implementation_cost": 500000.0, "roi_pct": 1600.2}

Risks: Model assumes order volume holds at the lower discount rate -- not validated, since this dataset cannot support a price-elasticity estimate (Phase 12 caveat). If reduced discounting meaningfully depresses volume, realized incremental profit would be lower than modeled.

## Q5: Should we increase marketing spend to fix the slowdown?

[OFFLINE MODE — deterministic evidence lookup, not a real LLM response. See run_ai_analyst.py / llm_provider.py for how to enable a genuine OpenAI/Gemini call once run with internet access.]

Finding: South revenue declined ~24.7% in FY2025 while the broader Indian e-commerce/retail market grew ~11-13% -- a company-specific execution problem, not a market contraction (Phase 13, Step 2 and Section 19).

Evidence:
  - South has the HIGHEST per-order margin of any region (31.84% aggregate / 32.68% per-order), ruling out pricing as the cause. region_South is the strongest positive churn predictor in the logistic regression model (coefficient 0.7244, reports/churn_model_report.md, Phase 09) -- pointing to a retention/execution gap specific to the region (service quality, delivery, local competition, or store/ops issues), not demand. (Source: Phase 14 recommendation, priority 3)
  - 8,674 customers are classified High Value + High Risk, holding Rs 335,678,885 (41.8% of all customer value) at churn risk (reports/churn_model_report.md, Phase 09). Scenario testing shows a +5pp retention improvement is worth Rs 13,680,404 in incremental annual net profit -- the single highest-value lever tested (reports/scenario_analysis_report.md, Phase 12). (Source: Phase 14 recommendation, priority 1)

Possible Causes: This finding's evidence text above already states the mechanism identified by the analysis; the evidence bundle does not separately decompose further root causes beyond what is shown.

Confidence: High (statistically tested, see p-values above)

Recommendation: Commission a focused operational review of South (store operations, delivery/service quality, local competitive positioning) and pilot a regional recovery program -- localized retention outreach plus operational fixes -- before allocating further blanket marketing spend, since Phase 12 showed marketing spend increases are not shown to pay for themselves at the company level.

Expected Impact: {"potential_customers_affected": 4800, "expected_revenue_impact": 18230184.519600004, "expected_revenue_impact_note": "If South had grown at the 12% market benchmark instead of declining, FY2025 South revenue would have been Rs 55,636,939 vs the actual Rs 37,406,754 -- a Rs 18,230,185 gap, computed directly from Phase 07's regional trend data.", "expected_incremental_profit": 5804490.751040641, "implementation_cost_assumption": "Planning assumption: Rs 2,000,000 for a regional operational review and pilot recovery program (audit, service improvements, localized retention outreach for South's 4,800 customers).", "implementation_cost": 2000000.0, "roi_pct": 190.2}

Risks: The recoverable-value estimate assumes South could have matched the market benchmark growth rate purely by fixing execution -- this is a gap estimate, not a validated forecast of what a recovery program would actually achieve, and the true cause (service, delivery, competition, or something else) has not yet been diagnosed at the root-cause level. Smallest expected financial impact of the three recommendations, but addresses the only regionally-concentrated decline directly.

## Q6: What is the single highest-priority recommendation and why?

[OFFLINE MODE — deterministic evidence lookup, not a real LLM response. See run_ai_analyst.py / llm_provider.py for how to enable a genuine OpenAI/Gemini call once run with internet access.]

Finding: Monthly customer retention has declined from 13.96% to 11.98% (statistically confirmed, p=9.5e-12), and 81.3% of customers in the churn model's training cohort made no repeat purchase within 90 days. This is the single largest driver of the revenue growth deceleration (Phase 13, Steps 1 and 4).

Evidence:
  - 8,674 customers are classified High Value + High Risk, holding Rs 335,678,885 (41.8% of all customer value) at churn risk (reports/churn_model_report.md, Phase 09). Scenario testing shows a +5pp retention improvement is worth Rs 13,680,404 in incremental annual net profit -- the single highest-value lever tested (reports/scenario_analysis_report.md, Phase 12). (Source: Phase 14 recommendation, priority 1)
  - South has the HIGHEST per-order margin of any region (31.84% aggregate / 32.68% per-order), ruling out pricing as the cause. region_South is the strongest positive churn predictor in the logistic regression model (coefficient 0.7244, reports/churn_model_report.md, Phase 09) -- pointing to a retention/execution gap specific to the region (service quality, delivery, local competition, or store/ops issues), not demand. (Source: Phase 14 recommendation, priority 3)

Possible Causes: This finding's evidence text above already states the mechanism identified by the analysis; the evidence bundle does not separately decompose further root causes beyond what is shown.

Confidence: High (statistically tested, see p-values above)

Recommendation: Launch a targeted retention program (personalized win-back offers, proactive outreach, loyalty incentives) aimed first at the 8,674 High-Value + High-Risk customers, since they carry the largest share of value at stake per customer reached. Use the churn model's probability scores (churn_predictions.csv) to prioritize outreach timing and channel.

Expected Impact: {"potential_customers_affected": 8674, "expected_revenue_impact_note": "The modeled financial outcome is the company-wide +5pp retention scenario (Rs 13,680,404 incremental net profit, Phase 12); this program is the operational mechanism proposed to help achieve that lift by concentrating effort on the highest-value at-risk segment, not a separately fitted number.", "expected_incremental_profit": 13680404.1, "implementation_cost_assumption": "Planning assumption: Rs 200 per targeted customer for personalized retention outreach/incentives (8,674 x Rs 200 = Rs 1,734,800). Not a measured figure -- a reasonable consulting-style planning estimate.", "implementation_cost": 1734800.0, "roi_pct": 688.6}

Risks: Retention lift is modeled at the aggregate +5pp level, not validated as achievable specifically by targeting this segment -- actual response to outreach could be lower than the blended model assumes. Churn model AUC is modest (~0.67-0.68), so targeting will include some false positives/negatives.
