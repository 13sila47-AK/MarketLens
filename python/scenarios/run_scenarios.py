"""
Phase 12 — Scenario Analysis (Orchestrator)
=============================================
1. Opens excel/business_model.xlsx and asserts the "Assumptions" sheet still
   matches the BASELINE constants in scenario_engine.py (catches silent drift
   if Phase 11's workbook is ever edited without updating this script).
2. Runs the four fixed scenarios (Current, Retention +5pp, Discount -2pp,
   Marketing +25%).
3. Writes data/processed/scenario_comparison.csv.
4. Adds a "Scenario Comparison" sheet to excel/business_model.xlsx (color-coded
   consistent with the Phase 11 legend: blue=input/lever, black=computed).
5. Writes reports/scenario_analysis_report.md with full methodology,
   the comparison table, and a ranked recommendation preview (full
   prioritization is Phase 14's job -- this just states what the numbers show).
"""

import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scenario_engine import (  # noqa: E402
    BASELINE,
    SCENARIO_METHODOLOGY,
    MARKETING_SPEND_INCREASE_PCT,
    MARKETING_ACQUISITION_ELASTICITY,
    RETENTION_DELTA_PP,
    DISCOUNT_DELTA_PP,
    run_all_scenarios,
)

EXCEL_PATH = BASE_DIR / "excel" / "business_model.xlsx"
CSV_OUT = BASE_DIR / "data" / "processed" / "scenario_comparison.csv"
REPORT_OUT = BASE_DIR / "reports" / "scenario_analysis_report.md"

INPUT_FILL = PatternFill("solid", fgColor="DCE6F1")   # blue-ish, matches Phase 11 legend
KEY_LEVER_FILL = PatternFill("solid", fgColor="FFF2CC")  # yellow, matches Phase 11 "key lever"
HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(color="FFFFFF", bold=True)
TITLE_FONT = Font(bold=True, size=13)
SECTION_FONT = Font(bold=True, size=11)


def verify_workbook_matches_baseline():
    """Confirm the live workbook's Assumptions sheet still equals BASELINE."""
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=False)
    ws = wb["Assumptions"]

    checks = {
        "gross_revenue": ws["C5"].value,
        "marketing_spend": ws["C16"].value,
        "avg_monthly_retention": ws["C10"].value,
        "discount_rate": ws["C13"].value,
        "customers_acquired": ws["C19"].value,
        "revenue_from_acquired": ws["C20"].value,
        "return_rate": ws["C29"].value,
        "cogs": ws["C33"].value,
        "shipping_cost": ws["C34"].value,
        "operational_cost": ws["C35"].value,
    }

    mismatches = []
    for key, cell_value in checks.items():
        expected = BASELINE[key]
        if cell_value is None or abs(float(cell_value) - expected) > 0.01:
            mismatches.append((key, cell_value, expected))

    if mismatches:
        raise AssertionError(
            "Assumptions sheet no longer matches scenario_engine.BASELINE — "
            f"drift detected: {mismatches}. Update BASELINE before continuing."
        )
    return wb


def write_csv(scenarios):
    import csv

    fields = [
        "scenario", "gross_revenue", "cogs", "gross_profit", "gross_margin_pct",
        "shipping_cost", "operational_cost", "return_amount", "marketing_spend",
        "total_opex", "net_profit", "net_margin_pct", "cac", "marketing_roi_pct",
        "incremental_value_vs_current",
    ]
    with open(CSV_OUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for s in scenarios:
            writer.writerow(s)


def add_scenario_sheet(wb, scenarios, notes):
    if "Scenario Comparison" in wb.sheetnames:
        del wb["Scenario Comparison"]
    ws = wb.create_sheet("Scenario Comparison")

    ws["A1"] = "UrbanCart — Scenario Comparison (Phase 12)"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = "All four scenarios computed from the same verified FY2025 baseline as the Financial Model sheet."
    ws["A2"].font = Font(italic=True, size=9)

    ws["A4"] = "Scenario Levers"
    ws["A4"].font = SECTION_FONT
    lever_rows = [
        ("Retention improvement", f"+{RETENTION_DELTA_PP*100:.0f} percentage points", "Fixed by spec"),
        ("Discount reduction", f"-{DISCOUNT_DELTA_PP*100:.0f} percentage points", "Fixed by spec"),
        ("Marketing increase", f"+{MARKETING_SPEND_INCREASE_PCT*100:.0f}% spend, elasticity {MARKETING_ACQUISITION_ELASTICITY}", "Assumed — spec gives no fixed %"),
    ]
    r = 5
    ws.cell(row=r, column=1, value="Lever").font = Font(bold=True)
    ws.cell(row=r, column=2, value="Value").font = Font(bold=True)
    ws.cell(row=r, column=3, value="Note").font = Font(bold=True)
    for name, val, note in lever_rows:
        r += 1
        ws.cell(row=r, column=1, value=name)
        c = ws.cell(row=r, column=2, value=val)
        c.fill = KEY_LEVER_FILL
        ws.cell(row=r, column=3, value=note)

    r += 2
    ws.cell(row=r, column=1, value="Comparison Table").font = SECTION_FONT
    r += 1

    headers = [
        "Metric", "Current", "Retention +5pp", "Discount -2pp", "Marketing +25%",
    ]
    metric_rows = [
        ("Gross Revenue (INR)", "gross_revenue", "{:,.2f}"),
        ("Gross Profit (INR)", "gross_profit", "{:,.2f}"),
        ("Gross Margin %", "gross_margin_pct", "{:.2f}%"),
        ("Total Operating Costs (INR)", "total_opex", "{:,.2f}"),
        ("Net Profit (INR)", "net_profit", "{:,.2f}"),
        ("Net Margin %", "net_margin_pct", "{:.2f}%"),
        ("CAC (INR/customer)", "cac", "{:,.2f}"),
        ("Marketing ROI %", "marketing_roi_pct", "{:.1f}%"),
        ("Incremental Value vs Current (INR)", "incremental_value_vs_current", "{:,.2f}"),
    ]

    header_row = r
    for col, h in enumerate(headers, start=1):
        c = ws.cell(row=header_row, column=col, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = Alignment(horizontal="center")

    by_name = {s["scenario"]: s for s in scenarios}
    order = ["Current", "Retention +5pp", "Discount -2pp", "Marketing +25%"]

    for i, (label, key, fmt) in enumerate(metric_rows):
        row = header_row + 1 + i
        ws.cell(row=row, column=1, value=label).font = Font(bold=True)
        for col, scen_name in enumerate(order, start=2):
            val = by_name[scen_name][key]
            ws.cell(row=row, column=col, value=fmt.format(val))

    r = header_row + len(metric_rows) + 3
    ws.cell(row=r, column=1, value="Data Integrity Note").font = SECTION_FONT
    r += 1
    ws.cell(
        row=r, column=1,
        value=(
            "FY2025 order count verified independently at 36,459 (raw orders.csv "
            "and kpi_revenue_by_month.csv agree). The Assumptions sheet's "
            "'Total Orders (FY2025)' cell (30,895) does not match this and looks "
            "like a stale/incorrect filter from Phase 11 -- flagged for correction. "
            "It did not affect any Financial Model formula (Total Orders is not "
            "referenced downstream) and does not affect these scenario results, "
            "which recompute order-level splits directly from source data."
        ),
    )
    ws["A" + str(r)].alignment = Alignment(wrap_text=True)
    ws.merge_cells(f"A{r}:E{r}")
    ws.row_dimensions[r].height = 60

    widths = [32, 20, 20, 20, 20]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def write_report(scenarios, notes):
    by_name = {s["scenario"]: s for s in scenarios}
    current = by_name["Current"]
    retention = by_name["Retention +5pp"]
    discount = by_name["Discount -2pp"]
    marketing = by_name["Marketing +25%"]

    ranked = sorted(
        [retention, discount, marketing],
        key=lambda s: s["incremental_value_vs_current"],
        reverse=True,
    )

    lines = []
    lines.append("# Phase 12 — Scenario Analysis Report\n")
    lines.append(
        "Four scenarios computed from the same verified FY2025 baseline used in "
        "Phase 11's `excel/business_model.xlsx` (Current, Retention +5pp, "
        "Discount -2pp, Marketing +25%), per spec sections 21-22. All figures "
        "below are computed by `python/scenarios/run_scenarios.py`, not typed "
        "in by hand — re-running it reproduces every number here.\n"
    )

    lines.append("## Data Integrity Check (found during this phase)\n")
    lines.append(
        f"- Real FY2025 order count, verified two independent ways "
        f"(distinct `order_id` in `orders.csv` filtered to 2025, and the sum "
        f"of `orders` across the 12 rows of `kpi_revenue_by_month.csv` for "
        f"2025): **{notes['fy2025_order_count_verified']:,}**.\n"
        f"- The Assumptions sheet's 'Total Orders (FY2025)' cell says "
        f"**{notes['assumptions_sheet_total_orders_cell']:,}** — this does not "
        f"match and looks like a Phase 11 filter bug. It does not propagate "
        f"into any Financial Model output (Total Orders isn't referenced by "
        f"any formula there), and this phase's scenarios use the verified "
        f"figure directly from source data, not the stale cell. Recommend "
        f"correcting that cell in Phase 11's workbook for consistency, but it "
        f"does not change any reported result to date.\n"
        f"- FY2025 revenue splits by first-vs-repeat order: new-order revenue "
        f"= Rs {notes['fy2025_new_order_revenue']:,.2f}, repeat-order revenue = "
        f"Rs {notes['fy2025_repeat_order_revenue']:,.2f}. These reconcile "
        f"exactly to Gross Revenue (Rs {BASELINE['gross_revenue']:,.2f}).\n"
    )

    lines.append("## Methodology per Scenario\n")
    for key, label in [
        ("current", "Current (Baseline)"),
        ("retention_improvement", "Retention Improvement (+5pp)"),
        ("discount_reduction", "Discount Reduction (-2pp)"),
        ("marketing_increase", "Marketing Increase"),
    ]:
        lines.append(f"**{label}**\n\n{SCENARIO_METHODOLOGY[key]}\n")

    lines.append("## Comparison Table\n")
    lines.append("| Metric | Current | Retention +5pp | Discount -2pp | Marketing +25% |")
    lines.append("|---|---|---|---|---|")
    rows = [
        ("Gross Revenue", "gross_revenue", "Rs {:,.0f}"),
        ("Gross Profit", "gross_profit", "Rs {:,.0f}"),
        ("Gross Margin %", "gross_margin_pct", "{:.2f}%"),
        ("Net Profit", "net_profit", "Rs {:,.0f}"),
        ("Net Margin %", "net_margin_pct", "{:.2f}%"),
        ("CAC", "cac", "Rs {:,.2f}"),
        ("Marketing ROI %", "marketing_roi_pct", "{:.1f}%"),
        ("**Incremental Value vs Current**", "incremental_value_vs_current", "**Rs {:,.0f}**"),
    ]
    for label, key, fmt in rows:
        vals = [fmt.format(by_name[s][key]) for s in ["Current", "Retention +5pp", "Discount -2pp", "Marketing +25%"]]
        lines.append(f"| {label} | " + " | ".join(vals) + " |")
    lines.append("")

    lines.append("## What the Numbers Show\n")
    lines.append(
        f"- **Retention improvement is the strongest lever**: +5pp retention is "
        f"worth an estimated **Rs {retention['incremental_value_vs_current']:,.0f}** "
        f"in incremental annual net profit — directly because retention drives "
        f"repeat-order revenue, and repeat orders are already {notes['fy2025_repeat_order_revenue']/BASELINE['gross_revenue']*100:.0f}% "
        f"of FY2025 revenue. This is consistent with Phase 07/08's finding that "
        f"repeat-purchase decline is the core problem, not a demand-side one.\n"
    )
    lines.append(
        f"- **Discount reduction is the second-strongest lever**: cutting "
        f"discount rate by 2pp is worth **Rs {discount['incremental_value_vs_current']:,.0f}** "
        f"in incremental profit at the SAME order volume, since it's pure "
        f"margin recovery. This assumes volume holds — Phase 08 found discount "
        f"tier materially affects margin, but did not establish that lower "
        f"discounts reduce volume, so this is presented as an upper-bound "
        f"estimate, not a volume-adjusted one.\n"
    )
    lines.append(
        f"- **Marketing increase is close to break-even** (a modeled "
        f"**Rs {marketing['incremental_value_vs_current']:,.0f}** change) once diminishing "
        f"acquisition returns are assumed rather than linear scaling. This "
        f"matches Phase 08's statistical finding that marketing spend did not "
        f"significantly predict performance at this sample size — spending more "
        f"without fixing retention or regional execution is not shown to pay for "
        f"itself here.\n"
    )
    lines.append(
        "- Ranked by incremental value: "
        + " > ".join(f"{s['scenario']} (Rs {s['incremental_value_vs_current']:,.0f})" for s in ranked)
        + ". This ranking is an input to Phase 14's prioritized recommendations, "
        "not the recommendations themselves — Phase 14 will also weigh "
        "implementation cost, risk, and confidence, which this phase does not "
        "quantify.\n"
    )

    lines.append("## Assumptions Requiring Explicit Caveat\n")
    lines.append(
        "- Retention and discount scenarios hold everything else constant "
        "(no cross-effects modeled between levers — e.g. a discount cut could "
        "itself affect retention, and vice versa).\n"
        "- The marketing elasticity (0.7) and spend increase (+25%) are "
        "reasonable planning assumptions, not statistically fitted values — "
        "the dataset does not have enough campaign-level variation (per Phase "
        "08) to fit a real elasticity curve.\n"
        "- All scenarios are static, single-year projections, not "
        "multi-year compounding models.\n"
    )

    lines.append(
        "\nOutputs: `data/processed/scenario_comparison.csv`, "
        "`excel/business_model.xlsx` (new 'Scenario Comparison' sheet), this report.\n"
    )
    lines.append(
        "Next: **Phase 13 — Business Diagnosis** (combine all analytical outputs "
        "from Phases 07-12 into the 'why is performance changing' narrative)."
    )

    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")


def main():
    wb = verify_workbook_matches_baseline()
    scenarios, notes = run_all_scenarios()
    write_csv(scenarios)
    add_scenario_sheet(wb, scenarios, notes)
    wb.save(EXCEL_PATH)
    write_report(scenarios, notes)

    print("Phase 12 complete.")
    print(f"- {CSV_OUT}")
    print(f"- {EXCEL_PATH} (Scenario Comparison sheet added)")
    print(f"- {REPORT_OUT}")
    for s in scenarios:
        print(f"  {s['scenario']:20s} net_profit={s['net_profit']:,.0f}  incremental={s['incremental_value_vs_current']:,.0f}")


if __name__ == "__main__":
    main()
