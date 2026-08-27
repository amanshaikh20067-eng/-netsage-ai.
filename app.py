"""NetSage AI Streamlit entry point.

Orchestrates the tested backend pipeline:
input -> validation -> Python rules -> AI -> AI validation -> comparison
-> human review -> verification -> logging.

No business or networking logic lives here or in ui/*.py -- both only
call already-tested modules from core/, ai/, rules/, and models/.
"""
from __future__ import annotations

import os
import uuid

import streamlit as st

from ai.diagnosis import AIRequestError, DiagnosisService, DiagnosisServiceError, MissingAPIKeyError
from ai.validator import AIValidationError, validate_ai_response
from config.settings import is_openai_configured
from core.comparison import compare_ai_and_python
from core.review_logger import ReviewLogger
from rules.engine import run_rules
from ui.dashboard_view import render_dashboard
from ui.diagnosis_view import render_ai_diagnosis, render_comparison, render_python_findings
from ui.input_view import render_input_form
from ui.review_view import render_review_form
from ui.verification_view import render_verification_form

st.set_page_config(page_title="NetSage AI", layout="wide")
st.title("NetSage AI")

REVIEWS_PATH = os.environ.get("NETSAGE_REVIEWS_PATH", "data/reviews.json")

if "case" not in st.session_state:
    st.session_state.case = None
    st.session_state.case_id = None
    st.session_state.python_findings = None
    st.session_state.ai_diagnosis = None
    st.session_state.ai_error = None
    st.session_state.comparison = None
    st.session_state.review = None
    st.session_state.verification = None
    st.session_state.saved_review_id = None

tab1, tab2 = st.tabs(["Analyze Case", "Dashboard"])

with tab1:
    case_data = render_input_form()

    if case_data is not None:
        st.session_state.case = case_data
        st.session_state.case_id = f"CASE-{uuid.uuid4().hex[:8]}"
        st.session_state.ai_diagnosis = None
        st.session_state.ai_error = None
        st.session_state.review = None
        st.session_state.verification = None
        st.session_state.saved_review_id = None

        with st.spinner("Running deterministic Python rules..."):
            st.session_state.python_findings = run_rules(
                case_data["symptom"], case_data["topology_notes"], case_data["show_output"],
            )

        if not is_openai_configured():
            st.session_state.ai_error = (
                "OpenAI API key is not configured. Set OPENAI_API_KEY to run AI analysis."
            )
        else:
            try:
                with st.spinner("Requesting AI diagnosis..."):
                    service = DiagnosisService()
                    raw = service.request_diagnosis(
                        case_data["symptom"], case_data["topology_notes"],
                        case_data["show_output"], st.session_state.python_findings,
                    )
                st.session_state.ai_diagnosis = validate_ai_response(raw.content)
            except MissingAPIKeyError as exc:
                st.session_state.ai_error = str(exc)
            except AIRequestError as exc:
                st.session_state.ai_error = f"AI request failed: {exc}"
            except DiagnosisServiceError as exc:
                st.session_state.ai_error = f"AI diagnosis service error: {exc}"
            except AIValidationError as exc:
                st.session_state.ai_error = f"AI response failed validation: {exc}"

        if st.session_state.ai_diagnosis is not None:
            st.session_state.comparison = compare_ai_and_python(
                st.session_state.ai_diagnosis, st.session_state.python_findings,
            )

    if st.session_state.case is not None:
        render_ai_diagnosis(st.session_state.ai_diagnosis, st.session_state.ai_error)

        findings_list = (
            st.session_state.python_findings.findings
            if st.session_state.python_findings is not None else []
        )
        render_python_findings(findings_list)
        render_comparison(st.session_state.comparison)

        if st.session_state.ai_diagnosis is not None and st.session_state.review is None:
            review = render_review_form(
                st.session_state.ai_diagnosis,
                case_id=st.session_state.case_id, review_id="PENDING",
            )
            if review is not None:
                st.session_state.review = review
        elif st.session_state.review is not None:
            st.subheader("5. Human Review")
            st.success(f"Decision recorded: {st.session_state.review.human_decision.value}")

        if st.session_state.review is not None and st.session_state.verification is None:
            verification = render_verification_form()
            if verification is not None:
                st.session_state.verification = verification
        elif st.session_state.verification is not None:
            st.subheader("6. Verification")
            st.success(f"Status recorded: {st.session_state.verification.status.value}")

        if (
            st.session_state.review is not None
            and st.session_state.verification is not None
            and st.session_state.saved_review_id is None
        ):
            logger = ReviewLogger(REVIEWS_PATH)
            saved = logger.save_review(
                case_id=st.session_state.case_id,
                ai_diagnosis=st.session_state.ai_diagnosis,
                python_findings=findings_list,
                comparison=st.session_state.comparison,
                review=st.session_state.review,
                verification=st.session_state.verification,
            )
            st.session_state.saved_review_id = saved.review_id

        if st.session_state.saved_review_id is not None:
            st.info(f"This case has been logged as {st.session_state.saved_review_id}.")

with tab2:
    render_dashboard(ReviewLogger(REVIEWS_PATH))
