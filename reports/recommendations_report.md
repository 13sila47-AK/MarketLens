# Phase 14 — Recommendations & Impact Report

Three prioritized recommendations (spec section 23), each with the full expected-impact chain from spec section 24: potential customers affected -> expected revenue impact -> implementation cost -> expected incremental profit -> ROI. Built directly from Phase 13's diagnosis and Phase 12's scenario values — nothing here re-derives analysis, it packages and quantifies what was already found.

**Priority order reflects total incremental value and strategic weight** (retention is the root cause named across every phase from 07 onward), not raw ROI% — Priority 2 actually has a higher ROI% than Priority 1 because it is a lower-cost policy change, but a smaller absolute opportunity. Both are worth pursuing; the ranking below is what to fund first if resources are constrained.

## Priority 1: Targeted retention program for High-Value + High-Risk customers

**Problem**

Monthly customer retention has declined from 13.96% to 11.98% (statistically confirmed, p=9.5e-12), and 81.3% of customers in the churn model's training cohort made no repeat purchase within 90 days. This is the single largest driver of the revenue growth deceleration (Phase 13, Steps 1 and 4).

**Evidence**

8,674 customers are classified High Value + High Risk, holding Rs 335,678,885 (41.8% of all customer value) at churn risk (reports/churn_model_report.md, Phase 09). Scenario testing shows a +5pp retention improvement is worth Rs 13,680,404 in incremental annual net profit -- the single highest-value lever tested (reports/scenario_analysis_report.md, Phase 12).

**Recommendation**

Launch a targeted retention program (personalized win-back offers, proactive outreach, loyalty incentives) aimed first at the 8,674 High-Value + High-Risk customers, since they carry the largest share of value at stake per customer reached. Use the churn model's probability scores (churn_predictions.csv) to prioritize outreach timing and channel.

**Expected Impact**

| Step | Value |
|---|---|
| Potential customers affected | 8,674 |
| Implementation cost | Rs 1,734,800 |
| Expected incremental profit | Rs 13,680,404 |
| Estimated ROI | 688.6% |

*The modeled financial outcome is the company-wide +5pp retention scenario (Rs 13,680,404 incremental net profit, Phase 12); this program is the operational mechanism proposed to help achieve that lift by concentrating effort on the highest-value at-risk segment, not a separately fitted number.*

*Implementation cost basis: Planning assumption: Rs 200 per targeted customer for personalized retention outreach/incentives (8,674 x Rs 200 = Rs 1,734,800). Not a measured figure -- a reasonable consulting-style planning estimate.*

**Risk**

Retention lift is modeled at the aggregate +5pp level, not validated as achievable specifically by targeting this segment -- actual response to outreach could be lower than the blended model assumes. Churn model AUC is modest (~0.67-0.68), so targeting will include some false positives/negatives.

## Priority 2: Discount governance to recover margin without cutting volume

**Problem**

Gross margin fell from 34.29% (2023) to 29.47% (2025) as discount rate nearly doubled, 7.04% to 13.44% of order value (Phase 13, Step 5).

**Evidence**

High-discount orders (top quartile, >=13.48% discount rate) average 28.90% margin vs 35.61% for low-discount orders (Welch t-test p < 1e-300; reports/statistical_analysis_report.md, Phase 08). Scenario testing shows a -2pp discount rate reduction at the same order volume is worth Rs 8,501,040 in incremental annual net profit (reports/scenario_analysis_report.md, Phase 12).

**Recommendation**

Introduce a discount approval workflow/threshold for orders in the top discount quartile, and review whether current blanket discount levels are necessary to hold volume, given South -- the region with a genuine volume problem -- already has the highest per-order margin without needing the deepest discounts.

**Expected Impact**

| Step | Value |
|---|---|
| Potential orders affected | Top discount quartile of FY2025 orders (~9,115 of 36,459) |
| Implementation cost | Rs 500,000 |
| Expected incremental profit | Rs 8,501,040 |
| Estimated ROI | 1600.2% |

*This is a margin-recovery lever, not new revenue: it recovers profit from the SAME order volume by charging closer to full price, rather than generating additional orders.*

*Implementation cost basis: Planning assumption: Rs 500,000 one-time for discount governance tooling/workflow and staff training -- this is a policy/process change, not new spend on customers, so cost is low relative to the other two recommendations.*

**Risk**

Model assumes order volume holds at the lower discount rate -- not validated, since this dataset cannot support a price-elasticity estimate (Phase 12 caveat). If reduced discounting meaningfully depresses volume, realized incremental profit would be lower than modeled.

## Priority 3: South region execution recovery program

**Problem**

South revenue declined ~24.7% in FY2025 while the broader Indian e-commerce/retail market grew ~11-13% -- a company-specific execution problem, not a market contraction (Phase 13, Step 2 and Section 19).

**Evidence**

South has the HIGHEST per-order margin of any region (31.84% aggregate / 32.68% per-order), ruling out pricing as the cause. region_South is the strongest positive churn predictor in the logistic regression model (coefficient 0.7244, reports/churn_model_report.md, Phase 09) -- pointing to a retention/execution gap specific to the region (service quality, delivery, local competition, or store/ops issues), not demand.

**Recommendation**

Commission a focused operational review of South (store operations, delivery/service quality, local competitive positioning) and pilot a regional recovery program -- localized retention outreach plus operational fixes -- before allocating further blanket marketing spend, since Phase 12 showed marketing spend increases are not shown to pay for themselves at the company level.

**Expected Impact**

| Step | Value |
|---|---|
| Potential customers affected | 4,800 |
| Expected revenue impact | Rs 18,230,185 |
| Implementation cost | Rs 2,000,000 |
| Expected incremental profit | Rs 5,804,491 |
| Estimated ROI | 190.2% |

*If South had grown at the 12% market benchmark instead of declining, FY2025 South revenue would have been Rs 55,636,939 vs the actual Rs 37,406,754 -- a Rs 18,230,185 gap, computed directly from Phase 07's regional trend data.*

*Implementation cost basis: Planning assumption: Rs 2,000,000 for a regional operational review and pilot recovery program (audit, service improvements, localized retention outreach for South's 4,800 customers).*

**Risk**

The recoverable-value estimate assumes South could have matched the market benchmark growth rate purely by fixing execution -- this is a gap estimate, not a validated forecast of what a recovery program would actually achieve, and the true cause (service, delivery, competition, or something else) has not yet been diagnosed at the root-cause level. Smallest expected financial impact of the three recommendations, but addresses the only regionally-concentrated decline directly.

## Combined Impact (if all three are implemented)

- Total expected incremental annual profit: Rs 27,985,935
- Total implementation cost: Rs 4,234,800
- Combined ROI: 560.9%

This is a simple sum, not a re-modeled combined scenario — the three levers are not guaranteed to be additive (e.g. retention gains and discount changes could interact), so treat this as a directional upper bound, not a forecast.

Outputs: `data/processed/recommendations.json` (for Phase 15's AI Business Analyst and Phase 16's dashboard), this report.

Next: **Phase 15 — AI Business Analyst** (the LLM layer that takes this diagnosis + these recommendations as pre-computed evidence and explains them conversationally — SQL/Python/R calculate facts, the LLM explains facts, never invents them).