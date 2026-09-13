"""
Phase 13 — Business Diagnosis
==============================
Spec sections 17 ("why is performance changing?") and 19 (internal vs
external comparison). This phase does NOT run new statistics or models --
it combines the already-verified outputs of Phases 07-12 into one causal
narrative, and packages the evidence as structured JSON so Phase 15's LLM
layer has real "CALCULATE FACTS" to explain rather than invent.

Every number pulled in here is either:
  (a) recomputed directly from data/processed/*.csv in this script, or
  (b) a verified figure quoted from an earlier phase's report, cited by
      file so it can be checked.
Nothing here is a new claim invented at synthesis time.
"""

import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PROCESSED = BASE_DIR / "data" / "processed"
REPORTS = BASE_DIR / "reports"


def compute_revenue_deceleration():
    df = pd.read_csv(DATA_PROCESSED / "kpi_margin_trend_yoy.csv")
    df = df.set_index("year")
    growth_23_24 = (df.loc[2024, "gross_revenue"] / df.loc[2023, "gross_revenue"] - 1) * 100
    growth_24_25 = (df.loc[2025, "gross_revenue"] / df.loc[2024, "gross_revenue"] - 1) * 100
    return {
        "revenue_2023": float(df.loc[2023, "gross_revenue"]),
        "revenue_2024": float(df.loc[2024, "gross_revenue"]),
        "revenue_2025": float(df.loc[2025, "gross_revenue"]),
        "yoy_growth_2023_to_2024_pct": round(float(growth_23_24), 2),
        "yoy_growth_2024_to_2025_pct": round(float(growth_24_25), 2),
        "gross_margin_pct_2023": float(df.loc[2023, "gross_margin_pct"]),
        "gross_margin_pct_2025": float(df.loc[2025, "gross_margin_pct"]),
        "discount_rate_pct_2023": float(df.loc[2023, "discount_rate_pct"]),
        "discount_rate_pct_2025": float(df.loc[2025, "discount_rate_pct"]),
        "return_rate_pct_2023": float(df.loc[2023, "return_rate_pct"]),
        "return_rate_pct_2025": float(df.loc[2025, "return_rate_pct"]),
        "source": "data/processed/kpi_margin_trend_yoy.csv (Phase 07)",
    }


def compute_regional_divergence():
    df = pd.read_csv(DATA_PROCESSED / "kpi_revenue_by_region_trend.csv")
    rows = df.set_index("region")[["2025_yoy_growth_pct"]].to_dict()["2025_yoy_growth_pct"]
    profitability = pd.read_csv(DATA_PROCESSED / "kpi_profitability_by_region.csv").set_index("region")
    revenue = pd.read_csv(DATA_PROCESSED / "kpi_revenue_by_region.csv").set_index("region")
    regions = {}
    for region in rows:
        regions[region] = {
            "yoy_growth_2025_pct": float(rows[region]),
            "gross_margin_pct": float(profitability.loc[region, "gross_margin_pct"]),
            "gross_revenue": float(revenue.loc[region, "gross_revenue"]),
            "pct_of_total_revenue": float(revenue.loc[region, "pct_of_total"]),
        }
    return {
        "regions": regions,
        "source": (
            "data/processed/kpi_revenue_by_region_trend.csv, "
            "kpi_profitability_by_region.csv, kpi_revenue_by_region.csv (Phase 07)"
        ),
    }


# --- Verified figures quoted from earlier phase reports (cited, not invented) ---

RETENTION_TREND = {
    "monthly_retention_start_pct": 13.96,  # kpi_monthly_retention.csv, 2024-04
    "monthly_retention_recent_pct": 11.98,  # kpi_monthly_retention.csv, 2025-11
    "trend_slope_pp_per_month": -0.1482,
    "trend_p_value": 9.49e-12,
    "trend_r_squared": 0.760,
    "source": "reports/statistical_analysis_report.md (Phase 08, Section 1)",
}

REVENUE_DECELERATION_STAT = {
    "quadratic_t2_coefficient": -0.00299,
    "p_value": 6.69e-11,
    "r_squared": 0.900,
    "source": "reports/statistical_analysis_report.md (Phase 08, Section 1)",
}

DISCOUNT_MARGIN_EFFECT = {
    "high_discount_tier_margin_pct": 28.90,
    "low_discount_tier_margin_pct": 35.61,
    "high_discount_tier_threshold_pct": 13.48,
    "low_discount_tier_threshold_pct": 8.57,
    "welch_t_p_value": "< 1e-300",
    "source": "reports/statistical_analysis_report.md (Phase 08, Section 3)",
}

SOUTH_MARGIN_FINDING = {
    "regional_margin_anova_p": 1.97e-10,
    "regional_margin_effect_size": "small (~0.6-0.7pp spread)",
    "south_per_order_margin_pct": 32.68,
    "lowest_region_margin_pct": 32.03,  # North
    "conclusion": "South has the HIGHEST per-order margin of any region -- its revenue decline is a volume/demand problem, not a pricing/margin problem.",
    "source": "reports/statistical_analysis_report.md (Phase 08, Section 3)",
}

CHURN_MODEL_FINDINGS = {
    "training_churn_rate_pct": 81.3,
    "model_auc": 0.6753,
    "top_features": ["region_South (+)", "total_orders (-)", "tenure_days (+)"],
    "high_risk_customers": 13747,
    "high_risk_clv_total": 293201371.29,
    "high_risk_clv_pct_of_total": 36.5,
    "priority_segment_customers": 8674,
    "priority_segment_clv": 335678884.57,
    "priority_segment_clv_pct": 41.8,
    "source": "reports/churn_model_report.md (Phase 09)",
}

EXTERNAL_BENCHMARK = {
    "india_ecommerce_cagr_pct": "~11.45",
    "urbancart_overall_growth_2025_pct": 13.0,
    "north_growth_vs_market": "well above market (+31.25% vs ~11-13%)",
    "central_growth_vs_market": "well above market (+21.59% vs ~11-13%)",
    "south_growth_vs_market": "far below market (-24.7% vs ~11-13%) -- company-specific, not market contraction",
    "west_growth_vs_market": "below market (-1.26% vs ~11-13%) -- flattened, not growing with the category",
    "source": "research/industry_analysis.md, research/competitor_analysis.md (Phase 10)",
}

FINANCIAL_BASELINE = {
    "fy2025_net_profit": 40691374.24,
    "fy2025_net_margin_pct": 11.06,
    "fy2025_gross_margin_pct": 29.47,
    "source": "excel/business_model.xlsx (Phase 11)",
}

SCENARIO_EVIDENCE = {
    "retention_5pp_incremental_value": 13680404.10,
    "discount_2pp_incremental_value": 8501039.74,
    "marketing_25pct_incremental_value": -595803.41,
    "ranking": "Retention +5pp > Discount -2pp > Marketing +25%",
    "interpretation": (
        "Fixing retention is worth more than fixing discounting, and both are "
        "worth more than spending more on marketing -- reinforcing that this is "
        "a retention/execution problem, not a demand-generation problem."
    ),
    "source": "reports/scenario_analysis_report.md (Phase 12)",
}


def build_causal_chain(revenue_facts, regional_facts):
    """
    Assembles the diagnosis as an ordered causal chain, spec section 17 style.
    Each link names the evidence file backing it -- this is the structure
    Phase 15's AI Business Analyst will receive as pre-computed fact, not
    something the LLM is asked to infer on its own.
    """
    return [
        {
            "step": 1,
            "finding": "Company revenue growth is decelerating, not reversing.",
            "evidence": (
                f"+{revenue_facts['yoy_growth_2023_to_2024_pct']:.0f}% YoY (2023->2024) "
                f"slowing to +{revenue_facts['yoy_growth_2024_to_2025_pct']:.0f}% YoY (2024->2025); "
                f"statistically confirmed deceleration, not just early-stage base effects "
                f"(quadratic trend p={REVENUE_DECELERATION_STAT['p_value']:.1e})."
            ),
            "sources": [revenue_facts["source"], REVENUE_DECELERATION_STAT["source"]],
        },
        {
            "step": 2,
            "finding": "The deceleration is a regional mix problem, not a market-wide one.",
            "evidence": (
                "North (+31.3%) and Central (+21.6%) are growing well above the "
                "~11-13% Indian e-commerce/retail benchmark; South (-24.7%) and "
                "West (-1.3%) are badly underperforming that same benchmark. "
                "Since the market itself grew at a normal rate, South/West's "
                "declines are company-specific execution issues, not a shrinking "
                "category."
            ),
            "sources": [regional_facts["source"], EXTERNAL_BENCHMARK["source"]],
        },
        {
            "step": 3,
            "finding": "South's problem is volume/demand, not pricing -- it has the best per-order margin in the company.",
            "evidence": (
                f"South's per-order margin ({SOUTH_MARGIN_FINDING['south_per_order_margin_pct']}%) "
                f"is the HIGHEST of any region (North lowest at "
                f"{SOUTH_MARGIN_FINDING['lowest_region_margin_pct']}%), though the "
                f"regional spread is small (~0.6-0.7pp). Combined with churn "
                f"modeling where region_South is the single strongest positive "
                f"churn predictor, South looks like a traffic/retention execution "
                f"gap, not a pricing problem that discounting more could fix."
            ),
            "sources": [SOUTH_MARGIN_FINDING["source"], CHURN_MODEL_FINDINGS["source"]],
        },
        {
            "step": 4,
            "finding": "Underneath the regional story, repeat-purchase behavior is weakening company-wide.",
            "evidence": (
                f"Monthly customer retention fell from "
                f"{RETENTION_TREND['monthly_retention_start_pct']}% to "
                f"{RETENTION_TREND['monthly_retention_recent_pct']}% over the "
                f"tracked period, a statistically real decline "
                f"(p={RETENTION_TREND['trend_p_value']:.1e}, "
                f"R²={RETENTION_TREND['trend_r_squared']}), not noise. The churn "
                f"model independently found {CHURN_MODEL_FINDINGS['training_churn_rate_pct']}% "
                f"of the training cohort made no repeat purchase within 90 days."
            ),
            "sources": [RETENTION_TREND["source"], CHURN_MODEL_FINDINGS["source"]],
        },
        {
            "step": 5,
            "finding": "Margin compression compounds the revenue slowdown: heavier discounting has materially eroded profitability.",
            "evidence": (
                f"Gross margin fell from {revenue_facts['gross_margin_pct_2023']}% "
                f"(2023) to {revenue_facts['gross_margin_pct_2025']}% (2025) as "
                f"discount rate rose from {revenue_facts['discount_rate_pct_2023']}% "
                f"to {revenue_facts['discount_rate_pct_2025']}% of order value. This "
                f"is a real, material effect, not a coincidence: high-discount "
                f"orders average {DISCOUNT_MARGIN_EFFECT['high_discount_tier_margin_pct']}% "
                f"margin vs {DISCOUNT_MARGIN_EFFECT['low_discount_tier_margin_pct']}% "
                f"for low-discount orders (p < 1e-300)."
            ),
            "sources": [revenue_facts["source"], DISCOUNT_MARGIN_EFFECT["source"]],
        },
        {
            "step": 6,
            "finding": "Returns are rising too, adding a second (smaller) drag on margin.",
            "evidence": (
                f"Return rate rose from {revenue_facts['return_rate_pct_2023']}% to "
                f"{revenue_facts['return_rate_pct_2025']}% of order value over the "
                f"same period. Note: return_rate alone is a weak/confounded signal "
                f"of customer value (Phase 08 correlation test sign-flipped between "
                f"Pearson and Spearman), so this is best read as a margin drag, not "
                f"an independent churn predictor."
            ),
            "sources": [revenue_facts["source"], "reports/statistical_analysis_report.md (Phase 08, Section 2)"],
        },
        {
            "step": 7,
            "finding": "The financial exposure is concentrated: a specific customer segment holds most of the value at risk.",
            "evidence": (
                f"{CHURN_MODEL_FINDINGS['priority_segment_customers']:,} customers "
                f"classified High Value + High Risk hold "
                f"Rs {CHURN_MODEL_FINDINGS['priority_segment_clv']:,.0f} "
                f"({CHURN_MODEL_FINDINGS['priority_segment_clv_pct']}% of all customer "
                f"value) -- under a third of the customer base carries the largest "
                f"single share of value that retention efforts could protect."
            ),
            "sources": [CHURN_MODEL_FINDINGS["source"]],
        },
        {
            "step": 8,
            "finding": "Net result: profitability has compressed to single-digit-adjacent net margin.",
            "evidence": (
                f"FY2025 net margin stands at {FINANCIAL_BASELINE['fy2025_net_margin_pct']}% "
                f"(net profit Rs {FINANCIAL_BASELINE['fy2025_net_profit']:,.0f} on "
                f"gross margin {FINANCIAL_BASELINE['fy2025_gross_margin_pct']}%) -- the "
                f"combined effect of steps 1-7."
            ),
            "sources": [FINANCIAL_BASELINE["source"]],
        },
        {
            "step": 9,
            "finding": "Scenario testing independently confirms retention, not marketing spend, is the highest-leverage fix.",
            "evidence": (
                f"Modeled incremental annual profit: Retention +5pp = "
                f"Rs {SCENARIO_EVIDENCE['retention_5pp_incremental_value']:,.0f}; "
                f"Discount -2pp = Rs {SCENARIO_EVIDENCE['discount_2pp_incremental_value']:,.0f}; "
                f"Marketing +25% = Rs {SCENARIO_EVIDENCE['marketing_25pct_incremental_value']:,.0f} "
                f"(essentially break-even, consistent with Phase 08's finding that "
                f"marketing spend does not statistically predict performance at "
                f"this sample size)."
            ),
            "sources": [SCENARIO_EVIDENCE["source"]],
        },
    ]


def build_evidence_bundle():
    revenue_facts = compute_revenue_deceleration()
    regional_facts = compute_regional_divergence()
    chain = build_causal_chain(revenue_facts, regional_facts)

    return {
        "revenue_deceleration": revenue_facts,
        "regional_divergence": regional_facts,
        "retention_trend": RETENTION_TREND,
        "revenue_deceleration_stat": REVENUE_DECELERATION_STAT,
        "discount_margin_effect": DISCOUNT_MARGIN_EFFECT,
        "south_margin_finding": SOUTH_MARGIN_FINDING,
        "churn_model_findings": CHURN_MODEL_FINDINGS,
        "external_benchmark": EXTERNAL_BENCHMARK,
        "financial_baseline": FINANCIAL_BASELINE,
        "scenario_evidence": SCENARIO_EVIDENCE,
        "causal_chain": chain,
    }


if __name__ == "__main__":
    bundle = build_evidence_bundle()
    print(json.dumps(bundle, indent=2, default=str))
