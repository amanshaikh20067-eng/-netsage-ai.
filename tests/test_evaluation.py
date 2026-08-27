"""M13 tests: evaluation script mechanics.

Uses a fake AI function; no live OpenAI call is made.
"""
from __future__ import annotations

from core.dataset_loader import REQUIRED_ISSUE_TYPES, load_cases
from evaluation.evaluate_cases import evaluate_all, evaluate_case
from models.case import IssueType, Severity
from models.diagnosis import AIDiagnosis, DiagnosisDetails, EvidenceItem, EvidenceSource, NextCommand


def _fake_ai_fn(symptom, topology_notes, show_output, python_findings):
    # Always claims "OTHER" -- deliberately wrong for nearly every case,
    # to prove mismatches get recorded rather than hidden.
    return AIDiagnosis(
        diagnosis=DiagnosisDetails(
            root_cause="Stub diagnosis for testing.",
            issue_type=IssueType.OTHER, osi_layer="Layer 1",
            confidence=50, severity=Severity.LOW,
        ),
        evidence=[EvidenceItem(source=EvidenceSource.SYMPTOM, observation="stub")],
        next_command=NextCommand(command="show run", purpose="stub"),
        fix_steps=["stub"], uncertainties=[],
    )


def test_all_cases_are_evaluated() -> None:
    cases = load_cases()
    results = evaluate_all(ai_fn=_fake_ai_fn)
    assert len(results) == len(cases) >= 30


def test_no_case_id_is_dropped() -> None:
    cases = load_cases()
    results = evaluate_all(ai_fn=_fake_ai_fn)
    assert {r["case_id"] for r in results} == {c.case_id for c in cases}


def test_all_required_issue_types_are_represented() -> None:
    results = evaluate_all(ai_fn=_fake_ai_fn)
    present = {r["expected_issue_type"] for r in results}
    missing = {t.value for t in REQUIRED_ISSUE_TYPES} - present
    assert missing == set()


def test_every_result_has_required_fields() -> None:
    results = evaluate_all(ai_fn=_fake_ai_fn)
    required_keys = {
        "case_id", "expected_issue_type", "expected_root_cause",
        "python_findings", "python_correct", "ai_issue_type",
        "ai_root_cause", "ai_confidence", "ai_correct", "ai_available",
        "comparison_status", "comparison_reason", "human_correction",
    }
    for r in results:
        assert required_keys.issubset(r.keys())


def test_mismatches_are_recorded_not_hidden() -> None:
    results = evaluate_all(ai_fn=_fake_ai_fn)
    mismatches = [r for r in results if r["ai_correct"] is False]
    assert len(mismatches) > 0


def test_human_correction_is_not_fabricated_by_default() -> None:
    results = evaluate_all(ai_fn=_fake_ai_fn)
    for r in results:
        assert r["human_correction"]["reviewed"] is False
        assert r["human_correction"]["decision"] is None


def test_ai_unavailable_case_is_still_recorded() -> None:
    def _failing_ai_fn(symptom, topology_notes, show_output, python_findings):
        return None

    results = evaluate_all(ai_fn=_failing_ai_fn)
    assert len(results) >= 30
    assert all(r["ai_available"] is False for r in results)
    assert all(r["ai_correct"] is None for r in results)


def test_single_case_evaluation_structure() -> None:
    case = load_cases()[0]
    result = evaluate_case(case, _fake_ai_fn)
    assert result["case_id"] == case.case_id
    assert isinstance(result["python_findings"], list)
    assert len(result["python_findings"]) == 6