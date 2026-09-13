# Phase 13 — Business Diagnosis Report

Answers spec section 17 ("why is business performance changing?") and section 19 (internal vs external comparison) by combining the already-verified outputs of Phases 07-12. No new statistics or models are run here — this is a synthesis phase. Every figure below is either recomputed directly from `data/processed/*.csv` by `python/analytics/business_diagnosis.py`, or quoted from an earlier phase's report with its source file named, so nothing here is asserted without a traceable origin.

## The Diagnosis Chain

```
[1] Company revenue growth is decelerating, not reversing.
     |
     v
[2] The deceleration is a regional mix problem, not a market-wide one.
     |
     v
[3] South's problem is volume/demand, not pricing -- it has the best per-order margin in the company.
     |
     v
[4] Underneath the regional story, repeat-purchase behavior is weakening company-wide.
     |
     v
[5] Margin compression compounds the revenue slowdown: heavier discounting has materially eroded profitability.
     |
     v
[6] Returns are rising too, adding a second (smaller) drag on margin.
     |
     v
[7] The financial exposure is concentrated: a specific customer segment holds most of the value at risk.
     |
     v
[8] Net result: profitability has compressed to single-digit-adjacent net margin.
     |
     v
[9] Scenario testing independently confirms retention, not marketing spend, is the highest-leverage fix.
```

### Step 1: Company revenue growth is decelerating, not reversing.

+98% YoY (2023->2024) slowing to +13% YoY (2024->2025); statistically confirmed deceleration, not just early-stage base effects (quadratic trend p=6.7e-11).

*Sources: data/processed/kpi_margin_trend_yoy.csv (Phase 07), reports/statistical_analysis_report.md (Phase 08, Section 1)*

### Step 2: The deceleration is a regional mix problem, not a market-wide one.

North (+31.3%) and Central (+21.6%) are growing well above the ~11-13% Indian e-commerce/retail benchmark; South (-24.7%) and West (-1.3%) are badly underperforming that same benchmark. Since the market itself grew at a normal rate, South/West's declines are company-specific execution issues, not a shrinking category.

*Sources: data/processed/kpi_revenue_by_region_trend.csv, kpi_profitability_by_region.csv, kpi_revenue_by_region.csv (Phase 07), research/industry_analysis.md, research/competitor_analysis.md (Phase 10)*

### Step 3: South's problem is volume/demand, not pricing -- it has the best per-order margin in the company.

South's per-order margin (32.68%) is the HIGHEST of any region (North lowest at 32.03%), though the regional spread is small (~0.6-0.7pp). Combined with churn modeling where region_South is the single strongest positive churn predictor, South looks like a traffic/retention execution gap, not a pricing problem that discounting more could fix.

*Sources: reports/statistical_analysis_report.md (Phase 08, Section 3), reports/churn_model_report.md (Phase 09)*

### Step 4: Underneath the regional story, repeat-purchase behavior is weakening company-wide.

Monthly customer retention fell from 13.96% to 11.98% over the tracked period, a statistically real decline (p=9.5e-12, R²=0.76), not noise. The churn model independently found 81.3% of the training cohort made no repeat purchase within 90 days.

*Sources: reports/statistical_analysis_report.md (Phase 08, Section 1), reports/churn_model_report.md (Phase 09)*

### Step 5: Margin compression compounds the revenue slowdown: heavier discounting has materially eroded profitability.

Gross margin fell from 34.29% (2023) to 29.47% (2025) as discount rate rose from 7.04% to 13.44% of order value. This is a real, material effect, not a coincidence: high-discount orders average 28.9% margin vs 35.61% for low-discount orders (p < 1e-300).

*Sources: data/processed/kpi_margin_trend_yoy.csv (Phase 07), reports/statistical_analysis_report.md (Phase 08, Section 3)*

### Step 6: Returns are rising too, adding a second (smaller) drag on margin.

Return rate rose from 5.22% to 7.18% of order value over the same period. Note: return_rate alone is a weak/confounded signal of customer value (Phase 08 correlation test sign-flipped between Pearson and Spearman), so this is best read as a margin drag, not an independent churn predictor.

*Sources: data/processed/kpi_margin_trend_yoy.csv (Phase 07), reports/statistical_analysis_report.md (Phase 08, Section 2)*

### Step 7: The financial exposure is concentrated: a specific customer segment holds most of the value at risk.

8,674 customers classified High Value + High Risk hold Rs 335,678,885 (41.8% of all customer value) -- under a third of the customer base carries the largest single share of value that retention efforts could protect.

*Sources: reports/churn_model_report.md (Phase 09)*

### Step 8: Net result: profitability has compressed to single-digit-adjacent net margin.

FY2025 net margin stands at 11.06% (net profit Rs 40,691,374 on gross margin 29.47%) -- the combined effect of steps 1-7.

*Sources: excel/business_model.xlsx (Phase 11)*

### Step 9: Scenario testing independently confirms retention, not marketing spend, is the highest-leverage fix.

Modeled incremental annual profit: Retention +5pp = Rs 13,680,404; Discount -2pp = Rs 8,501,040; Marketing +25% = Rs -595,803 (essentially break-even, consistent with Phase 08's finding that marketing spend does not statistically predict performance at this sample size).

*Sources: reports/scenario_analysis_report.md (Phase 12)*

## Internal vs External Comparison (Section 19)

UrbanCart's overall FY2025 growth (+13.0%) is roughly in line with the Indian e-commerce/retail benchmark (~11.45% CAGR, per Phase 10's sourced research) — so the company is **not** shrinking because the market is shrinking. The blended company-wide number hides a real regional split:

- North: well above market (+31.25% vs ~11-13%)
- Central: well above market (+21.59% vs ~11-13%)
- South: far below market (-24.7% vs ~11-13%) -- company-specific, not market contraction
- West: below market (-1.26% vs ~11-13%) -- flattened, not growing with the category

**Conclusion: this is a company-specific execution problem concentrated in South and West, layered on top of a company-wide retention decline — not a market downturn.**

## Summary Diagnosis

Revenue growth is decelerating not because the market is slowing, but because two distinct problems are compounding:

1. **A regional execution gap** (South declining, West flat) that is unrelated to pricing — South already has the best per-order margin in the company, and its customers show the strongest churn signal.
2. **A company-wide retention/repeat-purchase decline**, which is statistically real, independently confirmed by both the trend regression (Phase 08) and the churn model (Phase 09), and is concentrated in value terms among 8,674 High-Value + High-Risk customers holding 41.8% of all customer value.

Margin compression (discounting up, returns up) is compounding both problems rather than causing them — it is a second, independent drag on the same P&L. Scenario testing (Phase 12) confirms the fix with the highest financial leverage is retention, not discount correction and not increased marketing spend.


Outputs: `data/processed/diagnosis_evidence.json` (structured facts for Phase 15's AI Business Analyst), this report.

Next: **Phase 14 — Recommendations & Impact** (turn this diagnosis into 3 prioritized recommendations with problem/evidence/action/expected impact/risk, using this evidence bundle and Phase 12's scenario values).