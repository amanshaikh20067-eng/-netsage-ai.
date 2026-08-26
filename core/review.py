"""Mandatory human review workflow.

No AI diagnosis may be treated as final without going through
submit_review(). This module enforces the business rules the plan
requires for Accept/Edit/Reject; models/review.py only holds structure.

Does not implement persistence, dashboards, or the Streamlit UI —
those are later milestones.
"""
from __future__ import annotations

from models.diagnosis import AIDiagnosis
from models.review import HumanReview, ReviewDecision


class ReviewError(Exception):
    """Base error for the human review workflow."""


class InvalidReviewDecisionError(ReviewError):
    """Raised when the decision is not accepted, edited, or rejected."""


class MissingFinalDiagnosisError(ReviewError):
    """Raised when an edited review has no human_final_diagnosis."""


class ReviewValidationError(ReviewError):
    """Raised when a decision and its final diagnosis are inconsistent."""


def submit_review(
    review_id: str,
    case_id: str,
    ai_diagnosis: AIDiagnosis,
    decision: ReviewDecision | str,
    human_final_diagnosis: AIDiagnosis | None = None,
    review_comment: str = "",
) -> HumanReview:
    """Apply mandatory review rules and build a HumanReview record.

    This is the only supported way to produce a HumanReview. The original
    ai_diagnosis is always stored unchanged, regardless of decision.

    - accepted: human_final_diagnosis is set to the AI diagnosis itself.
      A caller must not supply a different diagnosis alongside "accepted".
    - edited: human_final_diagnosis is required and must differ from the
      AI diagnosis (otherwise the decision should be "accepted").
    - rejected: no final diagnosis exists; the AI diagnosis is not acted
      on. Supplying a replacement diagnosis alongside "rejected" is
      invalid -- use "edited" if a corrected diagnosis is intended.
    """
    try:
        decision = ReviewDecision(decision)
    except ValueError as exc:
        raise InvalidReviewDecisionError(
            f"{decision!r} is not a valid review decision. "
            f"Must be one of: {[d.value for d in ReviewDecision]}."
        ) from exc

    if decision == ReviewDecision.ACCEPTED:
        if human_final_diagnosis is not None and human_final_diagnosis != ai_diagnosis:
            raise ReviewValidationError(
                "An 'accepted' review cannot include a final diagnosis that "
                "differs from the AI diagnosis. Use 'edited' instead."
            )
        final_diagnosis = ai_diagnosis

    elif decision == ReviewDecision.EDITED:
        if human_final_diagnosis is None:
            raise MissingFinalDiagnosisError(
                "An 'edited' review requires a human_final_diagnosis."
            )
        if human_final_diagnosis == ai_diagnosis:
            raise ReviewValidationError(
                "An 'edited' review's final diagnosis must differ from the "
                "AI diagnosis. Use 'accepted' instead."
            )
        final_diagnosis = human_final_diagnosis

    else:  # REJECTED
        if human_final_diagnosis is not None:
            raise ReviewValidationError(
                "A 'rejected' review cannot include a final diagnosis. "
                "Use 'edited' if a corrected diagnosis should replace it."
            )
        final_diagnosis = None

    return HumanReview(
        review_id=review_id,
        case_id=case_id,
        ai_diagnosis=ai_diagnosis,
        human_decision=decision,
        human_final_diagnosis=final_diagnosis,
        review_comment=review_comment,
    )