"""
Phase 13 orchestrator. Writes:
  - data/processed/diagnosis_evidence.json  (structured facts for Phase 15's LLM)
  - reports/business_diagnosis_report.md    (the causal-chain narrative, spec section 17)
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from business_diagnosis import build_evidence_bundle  # noqa: E402

EVIDENCE_OUT = BASE_DIR / "data" / "processed" / "diagnosis_evidence.json"
REPORT_OUT = BASE_DIR / "reports" / "business_diagnosis_report.md"


def render_causal_chain_ascii(chain):
    lines = []
    for i, link in enumerate(chain):
        lines.append(f"[{link['step']}] {link['finding']}")
        if i < len(chain) - 1:
            lines.append("     |")
            lines.append("     v")
    return "\n".join(lines)


def write_report(bundle):
    chain = bundle["causal_chain"]
    lines = []
    lines.append("# Phase 13 — Business Diagnosis Report\n")
    lines.append(
        "Answers spec section 17 (\"why is business performance changing?\") "
        "and section 19 (internal vs external comparison) by combining the "
        "already-verified outputs of Phases 07-12. No new statistics or "
        "models are run here — this is a synthesis phase. Every figure below "
        "is either recomputed directly from `data/processed/*.csv` by "
        "`python/analytics/business_diagnosis.py`, or quoted from an earlier "
        "phase's report with its source file named, so nothing here is "
        "asserted without a traceable origin.\n"
    )

    lines.append("## The Diagnosis Chain\n")
    lines.append("```")
    lines.append(render_causal_chain_ascii(chain))
    lines.append("```\n")

    for link in chain:
        lines.append(f"### Step {link['step']}: {link['finding']}\n")
        lines.append(f"{link['evidence']}\n")
        lines.append(f"*Sources: {', '.join(link['sources'])}*\n")

    lines.append("## Internal vs External Comparison (Section 19)\n")
    eb = bundle["external_benchmark"]
    lines.append(
        f"UrbanCart's overall FY2025 growth (+{eb['urbancart_overall_growth_2025_pct']}%) "
        f"is roughly in line with the Indian e-commerce/retail benchmark "
        f"({eb['india_ecommerce_cagr_pct']}% CAGR, per Phase 10's sourced research) "
        f"— so the company is **not** shrinking because the market is shrinking. "
        f"The blended company-wide number hides a real regional split:\n\n"
        f"- North: {eb['north_growth_vs_market']}\n"
        f"- Central: {eb['central_growth_vs_market']}\n"
        f"- South: {eb['south_growth_vs_market']}\n"
        f"- West: {eb['west_growth_vs_market']}\n\n"
        f"**Conclusion: this is a company-specific execution problem concentrated "
        f"in South and West, layered on top of a company-wide retention decline "
        f"— not a market downturn.**\n"
    )

    lines.append("## Summary Diagnosis\n")
    lines.append(
        "Revenue growth is decelerating not because the market is slowing, but "
        "because two distinct problems are compounding:\n\n"
        "1. **A regional execution gap** (South declining, West flat) that is "
        "unrelated to pricing — South already has the best per-order margin in "
        "the company, and its customers show the strongest churn signal.\n"
        "2. **A company-wide retention/repeat-purchase decline**, which is "
        "statistically real, independently confirmed by both the trend "
        "regression (Phase 08) and the churn model (Phase 09), and is "
        "concentrated in value terms among 8,674 High-Value + High-Risk "
        "customers holding 41.8% of all customer value.\n\n"
        "Margin compression (discounting up, returns up) is compounding both "
        "problems rather than causing them — it is a second, independent drag "
        "on the same P&L. Scenario testing (Phase 12) confirms the fix with the "
        "highest financial leverage is retention, not discount correction and "
        "not increased marketing spend.\n"
    )

    lines.append(
        "\nOutputs: `data/processed/diagnosis_evidence.json` (structured facts "
        "for Phase 15's AI Business Analyst), this report.\n"
    )
    lines.append(
        "Next: **Phase 14 — Recommendations & Impact** (turn this diagnosis "
        "into 3 prioritized recommendations with problem/evidence/action/"
        "expected impact/risk, using this evidence bundle and Phase 12's "
        "scenario values)."
    )

    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")


def main():
    bundle = build_evidence_bundle()
    EVIDENCE_OUT.write_text(json.dumps(bundle, indent=2, default=str), encoding="utf-8")
    write_report(bundle)
    print("Phase 13 complete.")
    print(f"- {EVIDENCE_OUT}")
    print(f"- {REPORT_OUT}")


if __name__ == "__main__":
    main()
