"""
Phase 14 — Recommendations & Impact
=====================================
Spec sections 23 ("prioritized recommendations, not generic suggestions")
and 24 (expected business impact chain: potential customers affected ->
expected revenue impact -> implementation cost -> expected incremental
profit -> ROI).

This phase does NOT re-run analytics. It converts Phase 13's diagnosis
and Phase 12's scenario values into three ranked, quantified
recommendations. Where a number is a direct carry-over from an earlier
phase, it is used as-is (cited). Where a recommendation needs a number
Phase 07-13 didn't already produce (e.g. "what if South had grown at the
market rate"), that number is computed here, transparently, from the same
source CSVs -- not invented.

Implementation costs are stated as explicit PLANNING ASSUMPTIONS (labeled as
such), since no phase before this one produced a costed operational plan --
inventing false precision here would be worse than being honest that these
are reasonable consulting-style estimates, not measured figures.
"""

import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PROCESSED = BASE_DIR / "data" / "processed"

MARKET_BENCHMARK_GROWTH = 0.12  # midpoint of Phase 10's ~11-13% India e-commerce/retail CAGR


def compute_south_recovery_potential():
    trend = pd.read_csv(DATA_PROCESSED / "kpi_revenue_by_region_trend.csv").set_index("region")
    rev = pd.read_csv(DATA_PROCESSED / "kpi_revenue_by_region.csv").set_index("region")
    profit = pd.read_csv(DATA_PROCESSED / "kpi_profitability_by_region.csv").set_index("region")

    south_2024 = float(trend.loc["South", "2024"])
    south_2025_actual = float(trend.loc["South", "2025"])
    south_2025_if_market = south_2024 * (1 + MARKET_BENCHMARK_GROWTH)
    revenue_gap = south_2025_if_market - south_2025_actual
    south_margin_pct = float(profit.loc["South", "gross_margin_pct"])
    profit_gap = revenue_gap * (south_margin_pct / 100)

    return {
        "south_2024_revenue": south_2024,
        "south_2025_actual_revenue": south_2025_actual,
        "south_2025_at_market_growth_revenue": south_2025_if_market,
        "market_growth_assumption_pct": MARKET_BENCHMARK_GROWTH * 100,
        "recoverable_revenue_gap": revenue_gap,
        "south_gross_margin_pct": south_margin_pct,
        "recoverable_gross_profit_gap": profit_gap,
        "south_customers": int(rev.loc["South", "customers"]),
        "south_orders": int(rev.loc["South", "orders"]),
        "source": (
            "data/processed/kpi_revenue_by_region_trend.csv, "
            "kpi_revenue_by_region.csv, kpi_profitability_by_region.csv (Phase 07); "
            "market growth benchmark from research/industry_analysis.md (Phase 10)"
        ),
    }


def build_recommendations(south_recovery):
    return [
        {
            "priority": 1,
            "title": "Targeted retention program for High-Value + High-Risk customers",
            "problem": (
                "Monthly customer retention has declined from 13.96% to 11.98% "
                "(statistically confirmed, p=9.5e-12), and 81.3% of customers in "
                "the churn model's training cohort made no repeat purchase within "
                "90 days. This is the single largest driver of the revenue growth "
                "deceleration (Phase 13, Steps 1 and 4)."
            ),
            "evidence": (
                "8,674 customers are classified High Value + High Risk, holding "
                "Rs 335,678,885 (41.8% of all customer value) at churn risk "
                "(reports/churn_model_report.md, Phase 09). Scenario testing shows "
                "a +5pp retention improvement is worth Rs 13,680,404 in "
                "incremental annual net profit -- the single highest-value lever "
                "tested (reports/scenario_analysis_report.md, Phase 12)."
            ),
            "recommendation": (
                "Launch a targeted retention program (personalized win-back "
                "offers, proactive outreach, loyalty incentives) aimed first at "
                "the 8,674 High-Value + High-Risk customers, since they carry the "
                "largest share of value at stake per customer reached. Use the "
                "churn model's probability scores (churn_predictions.csv) to "
                "prioritize outreach timing and channel."
            ),
            "expected_impact": {
                "potential_customers_affected": 8674,
                "expected_revenue_impact_note": (
                    "The modeled financial outcome is the company-wide +5pp "
                    "retention scenario (Rs 13,680,404 incremental net profit, "
                    "Phase 12); this program is the operational mechanism proposed "
                    "to help achieve that lift by concentrating effort on the "
                    "highest-value at-risk segment, not a separately fitted number."
                ),
                "expected_incremental_profit": 13680404.10,
                "implementation_cost_assumption": (
                    "Planning assumption: Rs 200 per targeted customer for "
                    "personalized retention outreach/incentives "
                    "(8,674 x Rs 200 = Rs 1,734,800). Not a measured figure -- "
                    "a reasonable consulting-style planning estimate."
                ),
                "implementation_cost": 1734800.0,
                "roi_pct": None,  # computed below
            },
            "risk": (
                "Retention lift is modeled at the aggregate +5pp level, not "
                "validated as achievable specifically by targeting this segment -- "
                "actual response to outreach could be lower than the blended "
                "model assumes. Churn model AUC is modest (~0.67-0.68), so "
                "targeting will include some false positives/negatives."
            ),
        },
        {
            "priority": 2,
            "title": "Discount governance to recover margin without cutting volume",
            "problem": (
                "Gross margin fell from 34.29% (2023) to 29.47% (2025) as discount "
                "rate nearly doubled, 7.04% to 13.44% of order value (Phase 13, "
                "Step 5)."
            ),
            "evidence": (
                "High-discount orders (top quartile, >=13.48% discount rate) "
                "average 28.90% margin vs 35.61% for low-discount orders "
                "(Welch t-test p < 1e-300; reports/statistical_analysis_report.md, "
                "Phase 08). Scenario testing shows a -2pp discount rate reduction "
                "at the same order volume is worth Rs 8,501,040 in incremental "
                "annual net profit (reports/scenario_analysis_report.md, Phase 12)."
            ),
            "recommendation": (
                "Introduce a discount approval workflow/threshold for orders in "
                "the top discount quartile, and review whether current blanket "
                "discount levels are necessary to hold volume, given South -- the "
                "region with a genuine volume problem -- already has the highest "
                "per-order margin without needing the deepest discounts."
            ),
            "expected_impact": {
                "potential_orders_affected": "Top discount quartile of FY2025 orders (~9,115 of 36,459)",
                "expected_revenue_impact_note": (
                    "This is a margin-recovery lever, not new revenue: it recovers "
                    "profit from the SAME order volume by charging closer to full "
                    "price, rather than generating additional orders."
                ),
                "expected_incremental_profit": 8501039.74,
                "implementation_cost_assumption": (
                    "Planning assumption: Rs 500,000 one-time for discount "
                    "governance tooling/workflow and staff training -- this is a "
                    "policy/process change, not new spend on customers, so cost is "
                    "low relative to the other two recommendations."
                ),
                "implementation_cost": 500000.0,
                "roi_pct": None,
            },
            "risk": (
                "Model assumes order volume holds at the lower discount rate -- "
                "not validated, since this dataset cannot support a price-"
                "elasticity estimate (Phase 12 caveat). If reduced discounting "
                "meaningfully depresses volume, realized incremental profit would "
                "be lower than modeled."
            ),
        },
        {
            "priority": 3,
            "title": "South region execution recovery program",
            "problem": (
                "South revenue declined ~24.7% in FY2025 while the broader Indian "
                "e-commerce/retail market grew ~11-13% -- a company-specific "
                "execution problem, not a market contraction (Phase 13, Step 2 "
                "and Section 19)."
            ),
            "evidence": (
                "South has the HIGHEST per-order margin of any region (31.84% "
                "aggregate / 32.68% per-order), ruling out pricing as the cause. "
                "region_South is the strongest positive churn predictor in the "
                "logistic regression model (coefficient 0.7244, "
                "reports/churn_model_report.md, Phase 09) -- pointing to a "
                "retention/execution gap specific to the region (service quality, "
                "delivery, local competition, or store/ops issues), not demand."
            ),
            "recommendation": (
                "Commission a focused operational review of South (store "
                "operations, delivery/service quality, local competitive "
                "positioning) and pilot a regional recovery program -- localized "
                "retention outreach plus operational fixes -- before allocating "
                "further blanket marketing spend, since Phase 12 showed marketing "
                "spend increases are not shown to pay for themselves at the "
                "company level."
            ),
            "expected_impact": {
                "potential_customers_affected": south_recovery["south_customers"],
                "expected_revenue_impact": south_recovery["recoverable_revenue_gap"],
                "expected_revenue_impact_note": (
                    f"If South had grown at the {south_recovery['market_growth_assumption_pct']:.0f}% "
                    f"market benchmark instead of declining, FY2025 South revenue "
                    f"would have been Rs {south_recovery['south_2025_at_market_growth_revenue']:,.0f} "
                    f"vs the actual Rs {south_recovery['south_2025_actual_revenue']:,.0f} -- "
                    f"a Rs {south_recovery['recoverable_revenue_gap']:,.0f} gap, computed "
                    f"directly from Phase 07's regional trend data."
                ),
                "expected_incremental_profit": south_recovery["recoverable_gross_profit_gap"],
                "implementation_cost_assumption": (
                    "Planning assumption: Rs 2,000,000 for a regional operational "
                    "review and pilot recovery program (audit, service "
                    "improvements, localized retention outreach for South's "
                    f"{south_recovery['south_customers']:,} customers)."
                ),
                "implementation_cost": 2000000.0,
                "roi_pct": None,
            },
            "risk": (
                "The recoverable-value estimate assumes South could have matched "
                "the market benchmark growth rate purely by fixing execution -- "
                "this is a gap estimate, not a validated forecast of what a "
                "recovery program would actually achieve, and the true cause "
                "(service, delivery, competition, or something else) has not yet "
                "been diagnosed at the root-cause level. Smallest expected "
                "financial impact of the three recommendations, but addresses "
                "the only regionally-concentrated decline directly."
            ),
        },
    ]


def finalize_roi(recommendations):
    for rec in recommendations:
        impact = rec["expected_impact"]
        profit = impact["expected_incremental_profit"]
        cost = impact["implementation_cost"]
        impact["roi_pct"] = round((profit - cost) / cost * 100, 1)
    return recommendations


def build_bundle():
    south_recovery = compute_south_recovery_potential()
    recommendations = build_recommendations(south_recovery)
    recommendations = finalize_roi(recommendations)
    return {
        "south_recovery_calculation": south_recovery,
        "recommendations": recommendations,
    }


if __name__ == "__main__":
    print(json.dumps(build_bundle(), indent=2, default=str))
