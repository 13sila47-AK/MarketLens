"""
run_ai_analyst.py — Phase 15 orchestrator

Two modes:

1. Demo mode (default, no args):
   Runs a fixed set of realistic management questions through the AI
   Business Analyst and writes reports/ai_analyst_qna.md — this is the
   artifact that proves the LLM layer works end-to-end on the real
   Phase 13/14 evidence.

2. CLI mode (--question "..."):
   Answers a single ad-hoc question, printed to stdout. This is what
   Phase 16's Streamlit dashboard will call into for the interactive
   "Ask MarketLens" panel.

Sandbox honesty note: this container has no internet access, so every
question below will run through llm_provider's offline fallback and the
output file will say so plainly at the top. On a machine with a real
OPENAI_API_KEY or GEMINI_API_KEY and internet access, re-running this
script will populate the exact same file with genuine LLM-authored
explanations of the same evidence — no code changes needed.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from ai_business_analyst import AIBusinessAnalyst

BASE_DIR = Path(__file__).resolve().parents[2]  # MarketLens/
REPORT_PATH = BASE_DIR / "reports" / "ai_analyst_qna.md"

DEMO_QUESTIONS = [
    "Why did revenue growth slow down in 2025?",
    "Why is the South region declining, and is it a pricing problem?",
    "Which customers should we prioritize for retention, and how much value is at risk?",
    "Is discounting hurting our margins?",
    "Should we increase marketing spend to fix the slowdown?",
    "What is the single highest-priority recommendation and why?",
]


def run_demo() -> None:
    analyst = AIBusinessAnalyst()
    results = [analyst.answer(q) for q in DEMO_QUESTIONS]

    offline = results[0]["offline"] if results else True
    provider = results[0]["provider"] if results else "offline"

    lines = ["# MarketLens — AI Business Analyst: Sample Q&A", ""]
    lines.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_")
    lines.append(f"_Provider: {provider}_")
    lines.append("")

    if offline:
        lines.append(
            "> **Note:** This report was generated in a sandbox with no internet "
            "access, so no real OpenAI/Gemini call could be made (the same "
            "constraint that affected PostgreSQL, R, and Faker in earlier phases). "
            "Every answer below shows the exact evidence-bundle context the LLM "
            "prompt would have received, so the retrieval-and-grounding pipeline "
            "can be verified end-to-end. Set `OPENAI_API_KEY` or `GEMINI_API_KEY` "
            "in `.env` (provider selected via `LLM_PROVIDER`) and re-run "
            "`python python/analytics/run_ai_analyst.py` on a machine with "
            "internet access to regenerate this file with genuine LLM-authored "
            "explanations of the same underlying facts — no code changes needed."
        )
        lines.append("")

    for i, r in enumerate(results, 1):
        lines.append(f"## Q{i}: {r['question']}")
        lines.append("")
        lines.append(r["answer"])
        lines.append("")
        if r["ungrounded_numbers_flagged"]:
            lines.append(f"> **Grounding check flagged these numbers as not found verbatim in the evidence bundle** "
                          f"(may be formatting differences, e.g. rounding or commas — reviewed manually, not auto-removed): "
                          f"{', '.join(r['ungrounded_numbers_flagged'])}")
            lines.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines))
    print(f"Wrote {REPORT_PATH} ({len(results)} questions, provider={provider}, offline={offline})")


def run_cli(question: str) -> None:
    analyst = AIBusinessAnalyst()
    result = analyst.answer(question)
    print(f"[provider={result['provider']} offline={result['offline']}]\n")
    print(result["answer"])
    if result["ungrounded_numbers_flagged"]:
        print("\n[WARNING] Numbers in answer not found in evidence bundle:", result["ungrounded_numbers_flagged"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MarketLens AI Business Analyst")
    parser.add_argument("--question", "-q", type=str, default=None, help="Ask a single ad-hoc question")
    args = parser.parse_args()

    if args.question:
        run_cli(args.question)
    else:
        run_demo()
