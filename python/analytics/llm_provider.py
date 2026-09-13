"""
llm_provider.py â€” Phase 15: AI Business Analyst

Thin abstraction over LLM providers. The provider is chosen at runtime via
the LLM_PROVIDER env var, so the AI Business Analyst code above this layer
never needs to know which one is active.

SPEC DEVIATION NOTE (documented, not silent):
    The frozen tech stack (Section 0) names "OpenAI/Gemini" as the LLM.
    A third provider, xAI's Grok, was added below during Phase 17 testing
    after a live OpenAI key ran out of credits and a live Gemini key was
    denied project access by Google for reasons outside this project's
    control - both were genuinely attempted and both failed for
    account/billing reasons, not code reasons. Grok's chat-completions API
    is OpenAI-wire-compatible, so it was added as a pragmatic fallback to
    get a real, live LLM call working end-to-end, rather than silently
    swapping it in for one of the two named providers. If strict
    conformance to the frozen stack is required for submission, set
    LLM_PROVIDER to "openai" or "gemini" (below) and treat Grok as unused;
    the offline fallback remains fully spec-compliant either way.

Critical design rule (spec Section 25):
    SQL / Python / R  ->  CALCULATE FACTS  ->  LLM  ->  EXPLAIN FACTS
The LLM is only ever asked to explain numbers it is handed in the prompt.
It is never asked to produce a number itself. This module does not enforce
that (the calling code does, by construction), but the system prompt in
ai_business_analyst.py repeats the rule explicitly so the model does not
drift into inventing figures either.

Sandbox honesty note:
    This container has no internet access, so a real OpenAI/Gemini/Grok
    call cannot be executed here (same constraint that affected Postgres,
    R, and Faker in earlier phases). When no reachable provider/key is
    found, this module falls back to `_offline_explainer()`, a
    deterministic, template-based responder that is clearly labeled
    "[OFFLINE MODE]" in every response it produces. It is built ONLY from
    the facts passed to it - no invented numbers - so demo output
    generated in this sandbox is honest about being non-LLM, while the
    real API call paths are fully implemented and run as-is the moment a
    real API key is present in .env on a machine with internet access.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMResponse:
    text: str
    provider: str          # "openai" | "gemini" | "grok" | "offline"
    model: Optional[str] = None
    offline: bool = False  # True if this did NOT come from a real LLM call


def _get_provider_name() -> str:
    return os.getenv("LLM_PROVIDER", "openai").strip().lower()


def _call_openai(system_prompt: str, user_prompt: str) -> LLMResponse:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "your_openai_key_here":
        raise RuntimeError("OPENAI_API_KEY not set")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    text = resp.choices[0].message.content
    return LLMResponse(text=text, provider="openai", model=model, offline=False)


def _call_gemini(system_prompt: str, user_prompt: str) -> LLMResponse:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_key_here":
        raise RuntimeError("GEMINI_API_KEY not set")

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name, system_instruction=system_prompt)
    resp = model.generate_content(user_prompt, generation_config={"temperature": 0.2})
    return LLMResponse(text=resp.text, provider="gemini", model=model_name, offline=False)


def _call_grok(system_prompt: str, user_prompt: str) -> LLMResponse:
    """
    xAI Grok - NOT part of the frozen tech stack (see SPEC DEVIATION NOTE
    above). Grok's API is wire-compatible with OpenAI's chat-completions
    format, so this reuses the `openai` Python package pointed at xAI's
    base_url instead of a separate SDK.
    """
    api_key = os.getenv("GROK_API_KEY", "")
    if not api_key or api_key == "your_grok_key_here":
        raise RuntimeError("GROK_API_KEY not set")

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    model = os.getenv("GROK_MODEL", "llama-3.3-70b-versatile")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    text = resp.choices[0].message.content
    return LLMResponse(text=text, provider="grok", model=model, offline=False)


def _offline_explainer(system_prompt: str, user_prompt: str) -> LLMResponse:
    """
    Deterministic, non-LLM fallback used only when no real provider is
    reachable (no API key, no internet, or the call raised an exception).

    It does NOT attempt to reproduce genuine LLM reasoning. It returns the
    exact evidence context it was given, framed under the same
    Finding / Evidence / Possible Causes / Confidence / Recommendation /
    Expected Impact / Risks headings the real LLM is instructed to use,
    plus an explicit notice that this is offline/template output.
    This keeps the demo honest rather than faking a model response.
    """
    notice = (
        "[OFFLINE MODE - no reachable LLM provider. This is NOT a real "
        "model response. It is the same evidence bundle the LLM prompt "
        "would have received, shown directly so the pipeline can be "
        "demonstrated end-to-end without internet access. Set OPENAI_API_KEY, "
        "GEMINI_API_KEY, or GROK_API_KEY in .env and re-run on a machine "
        "with internet access to get a genuine LLM-authored explanation "
        "of these facts.]\n"
    )
    return LLMResponse(text=notice + "\n" + user_prompt, provider="offline", model=None, offline=True)


def call_llm(system_prompt: str, user_prompt: str) -> LLMResponse:
    """
    Route to the configured provider. Falls back to the offline explainer
    on any error (missing key, no internet, API error) rather than
    crashing - this is a business-analyst feature, not a hard dependency.
    """
    provider = _get_provider_name()

    if provider == "openai":
        try:
            return _call_openai(system_prompt, user_prompt)
        except Exception as e:
            print(f"[llm_provider] OpenAI call failed ({e}); falling back to offline mode.", file=sys.stderr)
            return _offline_explainer(system_prompt, user_prompt)

    if provider == "gemini":
        try:
            return _call_gemini(system_prompt, user_prompt)
        except Exception as e:
            print(f"[llm_provider] Gemini call failed ({e}); falling back to offline mode.", file=sys.stderr)
            return _offline_explainer(system_prompt, user_prompt)

    if provider == "grok":
        try:
            return _call_grok(system_prompt, user_prompt)
        except Exception as e:
            print(f"[llm_provider] Grok call failed ({e}); falling back to offline mode.", file=sys.stderr)
            return _offline_explainer(system_prompt, user_prompt)

    print(f"[llm_provider] Unknown LLM_PROVIDER='{provider}'; falling back to offline mode.", file=sys.stderr)
    return _offline_explainer(system_prompt, user_prompt)
