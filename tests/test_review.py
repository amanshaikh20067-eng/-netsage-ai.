"""M8 tests: mandatory human review workflow.

No persistence, dashboard, or Streamlit UI logic covered here.
"""
from __future__ import annotations

import pytest

from core.review import (
    InvalidReviewDecisionError,
    MissingFinalDiagnosisError,
    ReviewValidationError,
    submit_review,
)
from models.case import IssueType, Severity
from models.diagnosis import AIDiagnosis, DiagnosisDetails, EvidenceItem, EvidenceSource, NextCommand
from models.review import ReviewDecision


def _diagnosis(root_cause: str = "VLAN 20 is missing.", confidence: int = 85) -> AIDiagnosis:
    return AIDiagnosis(
        diagnosis=DiagnosisDetails(
            root_cause=root_cause,
            issue_type=IssueType.VLAN,
            osi_layer="Layer 2",
            confidence=confidence,
            severity=Severity.MEDIUM,
        ),
        evidence=[EvidenceItem(source=EvidenceSource.SHOW_OUTPUT, observation="VLAN 20 absent.")],
        next_command=NextCommand(command="show vlan brief", purpose="Confirm VLAN 20 exists."),
        fix_steps=["Create VLAN 20."],
        uncertainties=[],
    )


def test_accept() -> None:
    ai = _diagnosis()
    review = submit_review("R1", "CASE-001", ai, ReviewDecision.ACCEPTED)
    assert review.human_decision == ReviewDecision.ACCEPTED
    assert review.human_final_diagnosis == ai


def test_edit() -> None:
    ai = _diagnosis()
    edited = _diagnosis(root_cause="VLAN 20 exists but Fa0/2 is in VLAN 1.")
    review = submit_review("R2", "CASE-001", ai, ReviewDecision.EDITED, human_final_diagnosis=edited)
    assert review.human_decision == ReviewDecision.EDITED
    assert review.human_final_diagnosis == edited
    assert review.human_final_diagnosis != ai


def test_reject() -> None:
    ai = _diagnosis()
    review = submit_review("R3", "CASE-001", ai, ReviewDecision.REJECTED)
    assert review.human_decision == ReviewDecision.REJECTED
    assert review.human_final_diagnosis is None


def test_edit_preserves_original_ai_diagnosis() -> None:
    ai = _diagnosis()
    edited = _diagnosis(root_cause="A different root cause entirely.")
    review = submit_review("R4", "CASE-001", ai, ReviewDecision.EDITED, human_final_diagnosis=edited)
    assert review.ai_diagnosis == ai
    assert review.ai_diagnosis.diagnosis.root_cause == "VLAN 20 is missing."


def test_reject_preserves_original_ai_diagnosis() -> None:
    ai = _diagnosis()
    review = submit_review("R5", "CASE-001", ai, ReviewDecision.REJECTED)
    assert review.ai_diagnosis == ai


def test_accept_preserves_original_ai_diagnosis() -> None:
    ai = _diagnosis()
    review = submit_review("R6", "CASE-001", ai, ReviewDecision.ACCEPTED)
    assert review.ai_diagnosis == ai


def test_invalid_review_decision_string() -> None:
    ai = _diagnosis()
    with pytest.raises(InvalidReviewDecisionError):
        submit_review("R7", "CASE-001", ai, "maybe")


def test_missing_final_diagnosis_for_edit() -> None:
    ai = _diagnosis()
    with pytest.raises(MissingFinalDiagnosisError):
        submit_review("R8", "CASE-001", ai, ReviewDecision.EDITED)


def test_edit_with_identical_diagnosis_is_rejected() -> None:
    ai = _diagnosis()
    same = _diagnosis()  # same content, different object
    with pytest.raises(ReviewValidationError):
        submit_review("R9", "CASE-001", ai, ReviewDecision.EDITED, human_final_diagnosis=same)


def test_accept_with_mismatched_final_diagnosis_is_rejected() -> None:
    ai = _diagnosis()
    different = _diagnosis(root_cause="Something else.")
    with pytest.raises(ReviewValidationError):
        submit_review("R10", "CASE-001", ai, ReviewDecision.ACCEPTED, human_final_diagnosis=different)


def test_reject_with_final_diagnosis_is_rejected() -> None:
    ai = _diagnosis()
    replacement = _diagnosis(root_cause="Something else.")
    with pytest.raises(ReviewValidationError):
        submit_review("R11", "CASE-001", ai, ReviewDecision.REJECTED, human_final_diagnosis=replacement)


def test_review_comment_is_preserved() -> None:
    ai = _diagnosis()
    review = submit_review(
        "R12", "CASE-001", ai, ReviewDecision.ACCEPTED, review_comment="Looks correct."
    )
    assert review.review_comment == "Looks correct."


def test_review_id_and_case_id_are_preserved() -> None:
    ai = _diagnosis()
    review = submit_review("R13", "CASE-042", ai, ReviewDecision.REJECTED)
    assert review.review_id == "R13"
    assert review.case_id == "CASE-042"