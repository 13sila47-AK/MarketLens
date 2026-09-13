"""MarketLens - Phase 16: Ask MarketLens (AI Business Analyst panel).

Wires the dashboard directly to Phase 15's `AIBusinessAnalyst`. This page
does not add any new logic of its own -- it is a thin UI over
`python/analytics/ai_business_analyst.py`, which itself never invents a
number (see that module's docstring / spec Section 25).
"""

import sys
from pathlib import Path

import streamlit as st

DASHBOARD_DIR = Path(__file__).resolve().parents[1]
ANALYTICS_DIR = DASHBOARD_DIR.parent / "python" / "analytics"
sys.path.insert(0, str(DASHBOARD_DIR))
sys.path.insert(0, str(ANALYTICS_DIR))

from data_access import load_diagnosis_evidence, load_recommendations  # noqa: E402

st.set_page_config(page_title="MarketLens | Ask MarketLens", page_icon="\U0001F916", layout="wide")
st.title("\U0001F916 Ask MarketLens")
st.caption(
    "Ask a management question in plain English. The AI Business Analyst only explains "
    "facts already computed by SQL/Python/R (Phases 07\u201314) \u2014 it never invents a number."
)


@st.cache_resource
def get_analyst():
    from ai_business_analyst import AIBusinessAnalyst

    return AIBusinessAnalyst()


try:
    analyst = get_analyst()
    load_error = None
except Exception as e:  # pragma: no cover - defensive, e.g. missing .env
    analyst = None
    load_error = str(e)

if load_error:
    st.error(f"Could not initialize the AI Business Analyst: {load_error}")
    st.stop()

SAMPLE_QUESTIONS = [
    "Why did revenue growth slow down in 2025?",
    "Why is South declining?",
    "What should management prioritize first?",
    "Is the discount rate hurting margin?",
    "How much revenue is at risk from customer churn?",
    "Is marketing spend worth increasing?",
]

st.subheader("Ask a question")
col_input, col_samples = st.columns([3, 2])
with col_input:
    question = st.text_input("Your question", value="", placeholder="e.g. Why is South declining?")
    ask_clicked = st.button("Ask", type="primary")
with col_samples:
    st.caption("Or try a sample question:")
    picked = None
    for q in SAMPLE_QUESTIONS:
        if st.button(q, key=f"sample_{q}"):
            picked = q

final_question = picked or (question if ask_clicked and question.strip() else None)

if final_question:
    with st.spinner("Consulting the evidence bundle..."):
        result = analyst.answer(final_question)

    if result["offline"]:
        st.warning(
            "\u26A0\uFE0F **[OFFLINE MODE]** \u2014 no reachable OpenAI/Gemini API key/internet in this "
            "environment, so this is a deterministic, evidence-only answer (not a real LLM call). "
            "Set `LLM_PROVIDER` + the matching API key in `.env` to enable real LLM responses."
        )
    else:
        st.success(f"Answered by **{result['provider']}** ({result.get('model', 'n/a')})")
        if result["ungrounded_numbers_flagged"]:
            st.warning(f"Numeric grounding check flagged possibly ungrounded numbers: {result['ungrounded_numbers_flagged']}")

    st.markdown("### Answer")
    st.markdown(result["answer"])

st.divider()

with st.expander("What evidence is this analyst allowed to use?"):
    st.caption("The full evidence bundle it's grounded in \u2014 nothing outside this is ever used.")
    tab1, tab2 = st.tabs(["Business Diagnosis (Phase 13)", "Recommendations (Phase 14)"])
    with tab1:
        st.json(load_diagnosis_evidence())
    with tab2:
        st.json(load_recommendations())
