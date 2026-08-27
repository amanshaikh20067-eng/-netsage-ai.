"""Human review controls: Accept / Edit / Reject.

All business rules are delegated to core.review.submit_review. This
file only collects input and displays the result.
"""
from __future__ import annotations

import streamlit as st

from core.review import (
    InvalidReviewDecisionError,
    MissingFinalDiagnosisError,
    ReviewValidationError,
    submit_review,
)
from models.diagnosis import AIDiagnosis
from models.review import HumanReview, ReviewDecision


def render_review_form(
    ai_diagnosis: AIDiagnosis,
    case_id: str,
    review_id: str,
) -> HumanReview | None:
    st.subheader("5. Human Review")
    st.warning("A human must review this diagnosis before it can be treated as final.")

    decision_label = st.radio(
        "Decision", options=["Accept", "Edit", "Reject"],
        horizontal=True, key="review_decision_radio",
    )

    edited_root_cause = None
    edited_confidence = None
    if decision_label == "Edit":
        st.markdown("**Edit the diagnosis:**")
        edited_root_cause = st.text_area(
            "Corrected root cause",
            value=ai_diagnosis.diagnosis.root_cause,
            key="edit_root_cause",
        )
        edited_confidence = st.slider(
            "Corrected confidence", min_value=0, max_value=100,
            value=ai_diagnosis.diagnosis.confidence, key="edit_confidence",
        )

    review_comment = st.text_area("Review comment", key="review_comment")

    if not st.button("Submit review", key="submit_review_button"):
        return None

    decision_map = {
        "Accept": ReviewDecision.ACCEPTED,
        "Edit": ReviewDecision.EDITED,
        "Reject": ReviewDecision.REJECTED,
    }
    decision = decision_map[decision_label]

    human_final_diagnosis = None
    if decision == ReviewDecision.EDITED:
        human_final_diagnosis = ai_diagnosis.model_copy(
            update={
                "diagnosis": ai_diagnosis.diagnosis.model_copy(
                    update={
                        "root_cause": edited_root_cause,
                        "confidence": edited_confidence,
                    }
                )
            }
        )

    try:
        review = submit_review(
            review_id=review_id,
            case_id=case_id,
            ai_diagnosis=ai_diagnosis,
            decision=decision,
            human_final_diagnosis=human_final_diagnosis,
            review_comment=review_comment,
        )
    except (InvalidReviewDecisionError, MissingFinalDiagnosisError, ReviewValidationError) as exc:
        st.error(str(exc))
        return None

    st.success(f"Review recorded: {decision.value}")
    return review