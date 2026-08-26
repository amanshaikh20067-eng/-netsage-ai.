"""M9 tests for NetSage AI review logging."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.review_logger import (
    ReviewLogCorruptedError,
    ReviewLogger,
)
from models.comparison import ComparisonResult
from models.diagnosis import AIDiagnosis
from models.review import HumanReview
from models.rules import PythonFinding
from models.verification import Verification


def _valid_diagnosis_payload() -> dict:
    return {
        "diagnosis": {
            "root_cause": "VLAN 20 is missing from the switch.",
            "issue_type": "VLAN",
            "osi_layer": "Layer 2",
            "confidence": 85,
            "severity": "medium",
        },
        "evidence": [
            {
                "source": "topology",
                "observation": "PC2 belongs to VLAN 20.",
            }
        ],
        "next_command": {
            "command": "show vlan brief",
            "purpose": "Confirm whether VLAN 20 exists.",
        },
        "fix_steps": [
            "Create VLAN 20."
        ],
        "uncertainties": [],
    }


def _valid_ai_diagnosis() -> AIDiagnosis:
    return AIDiagnosis.model_validate(
        _valid_diagnosis_payload()
    )


def _valid_python_findings() -> list[PythonFinding]:
    return [
        PythonFinding.model_validate(
            {
                "rule_id": "missing_vlan",
                "status": "detected",
                "evidence": [
                    "VLAN 20 referenced in topology notes"
                ],
            }
        )
    ]


def _valid_comparison() -> ComparisonResult:
    return ComparisonResult.model_validate(
        {
            "status": "AGREEMENT",
            "reason": "Both identify missing VLAN 20.",
        }
    )


def _valid_human_review(
    decision: str = "accepted",
    final_diagnosis: dict | None = None,
) -> HumanReview:
    return HumanReview.model_validate(
        {
            "review_id": "TEMP-REV",
            "case_id": "CASE-001",
            "human_decision": decision,
            "ai_diagnosis": _valid_diagnosis_payload(),
            "human_final_diagnosis": (
                final_diagnosis
                if final_diagnosis is not None
                else _valid_diagnosis_payload()
            ),
            "review_comment": "Review completed.",
        }
    )


def _valid_verification() -> Verification:
    return Verification.model_validate(
        {
            "status": "verified",
            "evidence": "show vlan brief lists VLAN 20",
        }
    )


def _save_sample_review(
    logger: ReviewLogger,
    *,
    case_id: str = "CASE-001",
    decision: str = "accepted",
) -> object:
    return logger.save_review(
        case_id=case_id,
        ai_diagnosis=_valid_ai_diagnosis(),
        python_findings=_valid_python_findings(),
        comparison=_valid_comparison(),
        review=_valid_human_review(decision),
        verification=_valid_verification(),
    )


def test_empty_log_returns_empty_list(tmp_path: Path) -> None:
    file_path = tmp_path / "reviews.json"

    logger = ReviewLogger(file_path)

    assert logger.get_all_reviews() == []
    assert not file_path.exists()


def test_save_review_creates_record(tmp_path: Path) -> None:
    file_path = tmp_path / "reviews.json"
    logger = ReviewLogger(file_path)

    review = _save_sample_review(logger)

    assert review.review_id == "REV-000001"
    assert review.case_id == "CASE-001"
    assert review.ai_diagnosis == _valid_ai_diagnosis()
    assert review.python_findings == _valid_python_findings()
    assert review.comparison == _valid_comparison()
    assert review.human_decision.human_decision == "accepted"
    assert review.verification.status == "verified"
    assert review.timestamp is not None
    assert file_path.exists()


def test_review_ids_are_unique(tmp_path: Path) -> None:
    file_path = tmp_path / "reviews.json"
    logger = ReviewLogger(file_path)

    first = _save_sample_review(
        logger,
        case_id="CASE-001",
    )
    second = _save_sample_review(
        logger,
        case_id="CASE-002",
    )

    assert first.review_id == "REV-000001"
    assert second.review_id == "REV-000002"
    assert first.review_id != second.review_id


def test_persistence_across_logger_instances(tmp_path: Path) -> None:
    file_path = tmp_path / "reviews.json"

    logger_one = ReviewLogger(file_path)
    saved = _save_sample_review(logger_one)

    logger_two = ReviewLogger(file_path)
    reviews = logger_two.get_all_reviews()

    assert len(reviews) == 1
    assert reviews[0].review_id == saved.review_id
    assert reviews[0].case_id == saved.case_id


def test_get_specific_review(tmp_path: Path) -> None:
    file_path = tmp_path / "reviews.json"
    logger = ReviewLogger(file_path)

    saved = _save_sample_review(logger)

    result = logger.get_review(saved.review_id)

    assert result is not None
    assert result.review_id == saved.review_id
    assert result.case_id == "CASE-001"


def test_missing_review_returns_none(tmp_path: Path) -> None:
    file_path = tmp_path / "reviews.json"
    logger = ReviewLogger(file_path)

    assert logger.get_review("REV-999999") is None


def test_human_edit_preserves_ai_and_human_diagnoses(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "reviews.json"
    logger = ReviewLogger(file_path)

    human_diagnosis = _valid_diagnosis_payload()
    human_diagnosis["diagnosis"]["root_cause"] = (
        "The access port is assigned to the wrong VLAN."
    )

    review = _valid_human_review(
        decision="edited",
        final_diagnosis=human_diagnosis,
    )

    saved = logger.save_review(
        case_id="CASE-001",
        ai_diagnosis=_valid_ai_diagnosis(),
        python_findings=_valid_python_findings(),
        comparison=_valid_comparison(),
        review=review,
        verification=_valid_verification(),
    )

    loaded = logger.get_review(saved.review_id)

    assert loaded is not None

    assert (
        loaded.ai_diagnosis.diagnosis.root_cause
        == "VLAN 20 is missing from the switch."
    )

    assert loaded.human_decision.human_decision == "edited"

    assert loaded.human_decision.human_final_diagnosis is not None

    assert (
        loaded.human_decision.human_final_diagnosis.diagnosis.root_cause
        == "The access port is assigned to the wrong VLAN."
    )


def test_rejected_review_is_preserved(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "reviews.json"
    logger = ReviewLogger(file_path)

    saved = _save_sample_review(
        logger,
        decision="rejected",
    )

    loaded = logger.get_review(saved.review_id)

    assert loaded is not None
    assert loaded.human_decision.human_decision == "rejected"
    assert loaded.ai_diagnosis == _valid_ai_diagnosis()


def test_corrupted_json_raises_error(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "reviews.json"

    file_path.write_text(
        '{"broken":',
        encoding="utf-8",
    )

    logger = ReviewLogger(file_path)

    with pytest.raises(ReviewLogCorruptedError):
        logger.get_all_reviews()

    # The logger must not silently replace the corrupted file.
    assert file_path.read_text(encoding="utf-8") == '{"broken":'


def test_multiple_reviews_are_loaded(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "reviews.json"
    logger = ReviewLogger(file_path)

    _save_sample_review(logger, case_id="CASE-001")
    _save_sample_review(logger, case_id="CASE-002")
    _save_sample_review(logger, case_id="CASE-003")

    reviews = logger.get_all_reviews()

    assert len(reviews) == 3

    ids = [review.review_id for review in reviews]

    assert ids == [
        "REV-000001",
        "REV-000002",
        "REV-000003",
    ]


def test_saved_json_is_valid_and_readable(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "reviews.json"
    logger = ReviewLogger(file_path)

    _save_sample_review(logger)

    raw = file_path.read_text(encoding="utf-8")
    payload = json.loads(raw)

    assert isinstance(payload, list)
    assert len(payload) == 1
    assert payload[0]["review_id"] == "REV-000001"


def test_missing_file_is_not_created_by_read(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "reviews.json"
    logger = ReviewLogger(file_path)

    assert logger.get_all_reviews() == []
    assert not file_path.exists()


def test_existing_review_ids_continue_sequence(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "reviews.json"
    logger = ReviewLogger(file_path)

    _save_sample_review(logger, case_id="CASE-001")
    _save_sample_review(logger, case_id="CASE-002")

    # Create a new logger instance to verify IDs are derived
    # from persisted data rather than in-memory state.
    new_logger = ReviewLogger(file_path)

    third = _save_sample_review(
        new_logger,
        case_id="CASE-003",
    )

    assert third.review_id == "REV-000003"