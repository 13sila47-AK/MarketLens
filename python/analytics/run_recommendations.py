"""
Phase 14 orchestrator. Writes:
  - data/processed/recommendations.json   (structured, for Phase 15 LLM + Phase 16 dashboard)
  - reports/recommendations_report.md     (spec section 23/24 formatted report)
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from recommendations import build_bundle  # noqa: E402

JSON_OUT = BASE_DIR / "data" / "processed" / "recommendations.json"
REPORT_OUT = BASE_DIR / "reports" / "recommendations_report.md"


def fmt_money(x):
    return f"Rs {x:,.0f}"


def write_report(bundle):
    recs = bundle["recommendations"]
    lines = []
    lines.append("# Phase 14 — Recommendations & Impact Report\n")
    lines.append(
        "Three prioritized recommendations (spec section 23), each with the "
        "full expected-impact chain from spec section 24: potential customers "
        "affected -> expected revenue impact -> implementation cost -> "
        "expected incremental profit -> ROI. Built directly from Phase 13's "
        "diagnosis and Phase 12's scenario values — nothing here re-derives "
        "analysis, it packages and quantifies what was already found.\n"
    )
    lines.append(
        "**Priority order reflects total incremental value and strategic "
        "weight** (retention is the root cause named across every phase from "
        "07 onward), not raw ROI% — Priority 2 actually has a higher ROI% "
        "than Priority 1 because it is a lower-cost policy change, but a "
        "smaller absolute opportunity. Both are worth pursuing; the ranking "
        "below is what to fund first if resources are constrained.\n"
    )

    for rec in recs:
        impact = rec["expected_impact"]
        lines.append(f"## Priority {rec['priority']}: {rec['title']}\n")
        lines.append(f"**Problem**\n\n{rec['problem']}\n")
        lines.append(f"**Evidence**\n\n{rec['evidence']}\n")
        lines.append(f"**Recommendation**\n\n{rec['recommendation']}\n")
        lines.append("**Expected Impact**\n")
        lines.append("| Step | Value |")
        lines.append("|---|---|")
        if "potential_customers_affected" in impact:
            lines.append(f"| Potential customers affected | {impact['potential_customers_affected']:,} |")
        if "potential_orders_affected" in impact:
            lines.append(f"| Potential orders affected | {impact['potential_orders_affected']} |")
        if "expected_revenue_impact" in impact:
            lines.append(f"| Expected revenue impact | {fmt_money(impact['expected_revenue_impact'])} |")
        lines.append(f"| Implementation cost | {fmt_money(impact['implementation_cost'])} |")
        lines.append(f"| Expected incremental profit | {fmt_money(impact['expected_incremental_profit'])} |")
        lines.append(f"| Estimated ROI | {impact['roi_pct']:.1f}% |")
        lines.append("")
        lines.append(f"*{impact['expected_revenue_impact_note']}*\n")
        lines.append(
            f"*Implementation cost basis: {impact['implementation_cost_assumption']}*\n"
        )
        lines.append(f"**Risk**\n\n{rec['risk']}\n")

    total_profit = sum(r["expected_impact"]["expected_incremental_profit"] for r in recs)
    total_cost = sum(r["expected_impact"]["implementation_cost"] for r in recs)
    lines.append("## Combined Impact (if all three are implemented)\n")
    lines.append(
        f"- Total expected incremental annual profit: {fmt_money(total_profit)}\n"
        f"- Total implementation cost: {fmt_money(total_cost)}\n"
        f"- Combined ROI: {(total_profit - total_cost) / total_cost * 100:.1f}%\n\n"
        "This is a simple sum, not a re-modeled combined scenario — the three "
        "levers are not guaranteed to be additive (e.g. retention gains and "
        "discount changes could interact), so treat this as a directional "
        "upper bound, not a forecast."
    )

    lines.append(
        "\nOutputs: `data/processed/recommendations.json` (for Phase 15's AI "
        "Business Analyst and Phase 16's dashboard), this report.\n"
    )
    lines.append(
        "Next: **Phase 15 — AI Business Analyst** (the LLM layer that takes "
        "this diagnosis + these recommendations as pre-computed evidence and "
        "explains them conversationally — SQL/Python/R calculate facts, the "
        "LLM explains facts, never invents them)."
    )

    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")


def main():
    bundle = build_bundle()
    JSON_OUT.write_text(json.dumps(bundle, indent=2, default=str), encoding="utf-8")
    write_report(bundle)
    print("Phase 14 complete.")
    print(f"- {JSON_OUT}")
    print(f"- {REPORT_OUT}")


if __name__ == "__main__":
    main()
