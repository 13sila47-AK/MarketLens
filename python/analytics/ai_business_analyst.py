"""
ai_business_analyst.py — Phase 15: AI Business Analyst

Spec Section 25 pipeline, enforced by construction:

    SQL / Python / R
          |
    CALCULATE FACTS   <-- Phases 07-14 already did this. This module
          |                does NOT recompute or re-derive any number.
        LLM
          |
    EXPLAIN FACTS     <-- this module's only job.

The LLM is handed a fixed, structured evidence bundle assembled from:
    - data/processed/diagnosis_evidence.json   (Phase 13)
    - data/processed/recommendations.json      (Phase 14)
It is explicitly instructed to only use numbers found in that bundle and
to say "not available in the evidence provided" rather than estimate,
if a question asks for something outside it. This is stated in the
system prompt AND checked afterwards by a lightweight numeric-grounding
check (see `_check_grounding`) that flags (does not silently strip)
any number in the answer that doesn't trace back to the context.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from llm_provider import call_llm, LLMResponse

BASE_DIR = Path(__file__).resolve().parents[2]  # MarketLens/
DIAGNOSIS_PATH = BASE_DIR / "data" / "processed" / "diagnosis_evidence.json"
RECOMMENDATIONS_PATH = BASE_DIR / "data" / "processed" / "recommendations.json"

SYSTEM_PROMPT = """You are the MarketLens AI Business Analyst, embedded in a \
consulting-style analytics platform for UrbanCart, a fictional multi-location \
retail/e-commerce company.

You will be given a structured EVIDENCE BUNDLE containing facts that have \
already been calculated by SQL, Python (pandas/scikit-learn), and R \
(statistical tests). Every number in the bundle is real, computed from the \
company's actual dataset, and cited to the report/file it came from.

Your ONLY job is to EXPLAIN these facts in clear, executive-friendly language. \
You must NEVER invent, estimate, round-guess, or extrapolate a number that is \
not present in the evidence bundle. If the user asks something the evidence \
bundle does not cover, say so explicitly rather than guessing.

For every substantive answer, structure your response with these headings, \
in this order:

Finding: (what happened, one or two sentences)
Evidence: (the specific numbers/statistics from the bundle that support it, \
with their source)
Possible Causes: (grounded in the evidence, not speculation beyond it)
Confidence: (High / Medium / Low, and why — e.g. statistical significance, \
sample size, or explicit caveats present in the evidence)
Recommendation: (only if the evidence bundle contains a related recommendation \
— cite it; otherwise say recommendations for this specific angle are outside \
what Phase 14 modeled)
Expected Impact: (only figures present in the evidence bundle)
Risks: (from the evidence bundle's own risk/caveat notes where available)

Keep the tone like a careful, honest management consultant — confident about \
what the data shows, explicit about what it doesn't."""


@dataclass
class EvidenceBundle:
    diagnosis: dict = field(default_factory=dict)
    recommendations: dict = field(default_factory=dict)

    @classmethod
    def load(cls) -> "EvidenceBundle":
        diagnosis = json.loads(DIAGNOSIS_PATH.read_text()) if DIAGNOSIS_PATH.exists() else {}
        recommendations = json.loads(RECOMMENDATIONS_PATH.read_text()) if RECOMMENDATIONS_PATH.exists() else {}
        return cls(diagnosis=diagnosis, recommendations=recommendations)

    def as_context_text(self) -> str:
        """Render the full evidence bundle as readable, source-tagged text for the prompt."""
        lines = ["=== EVIDENCE BUNDLE (Phase 13 diagnosis + Phase 14 recommendations) ===\n"]

        lines.append("--- CAUSAL CHAIN (Phase 13) ---")
        for step in self.diagnosis.get("causal_chain", []):
            lines.append(f"Step {step['step']}: {step['finding']}")
            lines.append(f"  Evidence: {step['evidence']}")
            lines.append(f"  Source: {', '.join(step['sources'])}")
        lines.append("")

        lines.append("--- KEY METRICS (Phase 13 raw facts) ---")
        for section, content in self.diagnosis.items():
            if section == "causal_chain":
                continue
            lines.append(f"[{section}]")
            lines.append(json.dumps(content, indent=2, default=str))
        lines.append("")

        lines.append("--- RECOMMENDATIONS (Phase 14) ---")
        for rec in self.recommendations.get("recommendations", []):
            lines.append(f"Priority {rec['priority']}: {rec['title']}")
            lines.append(f"  Problem: {rec['problem']}")
            lines.append(f"  Evidence: {rec['evidence']}")
            lines.append(f"  Recommendation: {rec['recommendation']}")
            lines.append(f"  Expected Impact: {json.dumps(rec['expected_impact'], default=str)}")
            lines.append(f"  Risk: {rec['risk']}")
        south_calc = self.recommendations.get("south_recovery_calculation")
        if south_calc:
            lines.append("[south_recovery_calculation]")
            lines.append(json.dumps(south_calc, indent=2, default=str))

        return "\n".join(lines)


_NUMBER_RE = re.compile(r"\d[\d,]*\.?\d*")


def _check_grounding(answer_text: str, context_text: str) -> list[str]:
    """
    Lightweight sanity check, not a hard filter: extract numeric tokens
    (2+ digits, to skip list markers like "1." and headings) from the
    answer and flag any that don't appear anywhere in the context text.
    Percent/currency-adjacent formatting differences can cause false
    positives, so this is reported as a caution to the operator, not
    used to silently edit the LLM's answer.
    """
    context_numbers = set(_NUMBER_RE.findall(context_text))
    answer_numbers = [n for n in _NUMBER_RE.findall(answer_text) if len(n.replace(",", "").replace(".", "")) >= 2]
    unmatched = [n for n in answer_numbers if n not in context_numbers]
    return sorted(set(unmatched))


_STOPWORDS = {
    "the", "and", "for", "are", "was", "were", "why", "what", "should", "does",
    "this", "that", "with", "have", "has", "did", "our", "we", "is", "in",
    "to", "of", "a", "an", "on", "it", "us", "how", "much", "which", "who",
}


def _stem(word: str) -> str:
    """Minimal suffix-stripping so 'discounting'/'discount', 'margins'/'margin' etc. match."""
    for suffix in ("ing", "es", "ed", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def _tokenize(text: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-zA-Z]{4,}", text.lower()) if w not in _STOPWORDS}


def _build_fact_cards(evidence: EvidenceBundle) -> list[dict]:
    """Flatten causal_chain steps + recommendations into a common searchable shape."""
    cards = []
    for step in evidence.diagnosis.get("causal_chain", []):
        cards.append({
            "type": "causal_step",
            "title": step["finding"],
            "finding": step["finding"],
            "evidence": step["evidence"],
            "source": ", ".join(step["sources"]),
            "recommendation": None,
            "impact": None,
            "risk": None,
        })
    for rec in evidence.recommendations.get("recommendations", []):
        cards.append({
            "type": "recommendation",
            "title": rec["title"],
            "finding": rec["problem"],
            "evidence": rec["evidence"],
            "source": f"Phase 14 recommendation, priority {rec['priority']}",
            "recommendation": rec["recommendation"],
            "impact": rec["expected_impact"],
            "risk": rec["risk"],
        })
    return cards


def compose_offline_answer(question: str, evidence: EvidenceBundle) -> str:
    """
    Deterministic, evidence-only answer used when no real LLM provider is
    reachable. Scores every causal-chain step and recommendation against
    the question by keyword overlap, picks the best matches, and renders
    them under the same heading structure the real LLM is instructed to
    use — built entirely from fields already present in the evidence
    bundle, nothing synthesized.
    """
    cards = _build_fact_cards(evidence)
    q_tokens = _tokenize(question)
    q_lower = question.lower()
    wants_recommendation = any(w in q_lower for w in ["recommend", "priority", "should we", "what should"])

    scored = []
    for c in cards:
        c_tokens = _tokenize(c["title"] + " " + c["finding"] + " " + c["evidence"])
        score = float(len(q_tokens & c_tokens))
        if c["type"] == "recommendation":
            if wants_recommendation:
                score += 2.0
            # tie-break: prefer higher-priority (lower number) recommendations slightly
            priority = int(c["source"].rsplit(" ", 1)[-1]) if c["source"].rsplit(" ", 1)[-1].isdigit() else 9
            score += (9 - priority) * 0.01
        scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)

    top = [c for s, c in scored if s > 0][:2]
    if not top:
        top = [c for _, c in scored[:2]]  # fall back to first two cards if nothing matched

    lines = ["[OFFLINE MODE — deterministic evidence lookup, not a real LLM response. "
             "See run_ai_analyst.py / llm_provider.py for how to enable a genuine "
             "OpenAI/Gemini call once run with internet access.]\n"]

    lines.append(f"Finding: {top[0]['finding']}")
    lines.append("")
    lines.append("Evidence:")
    for c in top:
        lines.append(f"  - {c['evidence']} (Source: {c['source']})")
    lines.append("")

    lines.append("Possible Causes: " +
                  ("This finding's evidence text above already states the mechanism identified "
                   "by the analysis; the evidence bundle does not separately decompose further "
                   "root causes beyond what is shown."))
    lines.append("")

    has_stat = any(kw in (c["evidence"] + c["finding"]).lower() for kw in ["p=", "p <", "p-value", "significant", "p<"] for c in top)
    lines.append(f"Confidence: {'High (statistically tested, see p-values above)' if has_stat else 'Medium (descriptive evidence; see source report for any statistical testing)'}")
    lines.append("")

    rec_card = next((c for c in top if c["recommendation"]), None)
    if rec_card:
        lines.append(f"Recommendation: {rec_card['recommendation']}")
        lines.append("")
        lines.append(f"Expected Impact: {json.dumps(rec_card['impact'], default=str)}")
        lines.append("")
        lines.append(f"Risks: {rec_card['risk']}")
    else:
        lines.append("Recommendation: This specific angle does not map directly to one of Phase 14's "
                      "three prioritized recommendations — see reports/recommendations_report.md for "
                      "the full set.")
        lines.append("")
        lines.append("Expected Impact: Not modeled for this specific angle; see Phase 12 "
                      "(scenario_evidence) or Phase 14 (recommendations.json) for the figures that are.")
        lines.append("")
        lines.append("Risks: See the source report(s) cited above for caveats specific to this finding.")

    return "\n".join(lines)


class AIBusinessAnalyst:
    def __init__(self):
        self.evidence = EvidenceBundle.load()
        self.context_text = self.evidence.as_context_text()

    def answer(self, question: str) -> dict:
        user_prompt = (
            f"{self.context_text}\n\n"
            f"=== MANAGEMENT QUESTION ===\n{question}\n\n"
            "Answer using ONLY the evidence bundle above, following the required "
            "heading structure (Finding / Evidence / Possible Causes / Confidence / "
            "Recommendation / Expected Impact / Risks)."
        )
        response: LLMResponse = call_llm(SYSTEM_PROMPT, user_prompt)

        if response.offline:
            # Replace the generic raw-context dump with a question-aware,
            # evidence-only composed answer (see compose_offline_answer).
            answer_text = compose_offline_answer(question, self.evidence)
            grounding_flags: list[str] = []
        else:
            answer_text = response.text
            grounding_flags = _check_grounding(answer_text, self.context_text)

        return {
            "question": question,
            "answer": answer_text,
            "provider": response.provider,
            "model": response.model,
            "offline": response.offline,
            "ungrounded_numbers_flagged": grounding_flags,
        }


if __name__ == "__main__":
    analyst = AIBusinessAnalyst()
    result = analyst.answer("Why did revenue growth slow down in 2025?")
    print(f"[provider={result['provider']} offline={result['offline']}]\n")
    print(result["answer"])
    if result["ungrounded_numbers_flagged"]:
        print("\n[WARNING] Numbers in answer not found in evidence bundle:", result["ungrounded_numbers_flagged"])
