"""M7 tests: AI vs Python comparison engine.

No human review, persistence, or dashboard logic covered here.
"""
from __future__ import annotations

from core.comparison import compare_ai_and_python
from models.case import IssueType, Severity
from models.comparison import ComparisonStatus
from models.diagnosis import AIDiagnosis, DiagnosisDetails, EvidenceItem, EvidenceSource, NextCommand
from models.rules import PythonFinding, RuleEngineResult, RuleId, RuleStatus


def _diagnosis(issue_type: IssueType, evidence_count: int = 1) -> AIDiagnosis:
    return AIDiagnosis(
        diagnosis=DiagnosisDetails(
            root_cause="Example root cause.",
            issue_type=issue_type,
            osi_layer="Layer 2",
            confidence=80,
            severity=Severity.MEDIUM,
        ),
        evidence=[
            EvidenceItem(source=EvidenceSource.SHOW_OUTPUT, observation=f"Observation {i}")
            for i in range(evidence_count)
        ],
        next_command=NextCommand(command="show run", purpose="Confirm state."),
        fix_steps=["Do the fix."],
        uncertainties=[],
    )


def _finding(rule_id: RuleId, status: RuleStatus) -> PythonFinding:
    return PythonFinding(rule_id=rule_id, status=status, evidence=["Example evidence."])


def test_agreement() -> None:
    ai = _diagnosis(IssueType.VLAN)
    findings = [_finding(RuleId.MISSING_VLAN, RuleStatus.DETECTED)]
    result = compare_ai_and_python(ai, findings)
    assert result.status == ComparisonStatus.AGREEMENT
    assert "missing_vlan" in result.reason


def test_partial_agreement_related_match() -> None:
    ai = _diagnosis(IssueType.GATEWAY)
    findings = [_finding(RuleId.MISSING_ROUTE, RuleStatus.DETECTED)]
    result = compare_ai_and_python(ai, findings)
    assert result.status == ComparisonStatus.PARTIAL_AGREEMENT


def test_partial_agreement_primary_plus_extra_detected() -> None:
    ai = _diagnosis(IssueType.VLAN)
    findings = [
        _finding(RuleId.MISSING_VLAN, RuleStatus.DETECTED),
        _finding(RuleId.MISSING_ROUTE, RuleStatus.DETECTED),
    ]
    result = compare_ai_and_python(ai, findings)
    assert result.status == ComparisonStatus.PARTIAL_AGREEMENT
    assert "missing_route" in result.reason


def test_ai_only() -> None:
    ai = _diagnosis(IssueType.DNS)
    findings = [
        _finding(RuleId.MISSING_VLAN, RuleStatus.NOT_DETECTED),
        _finding(RuleId.MISSING_ROUTE, RuleStatus.NOT_DETECTED),
    ]
    result = compare_ai_and_python(ai, findings)
    assert result.status == ComparisonStatus.AI_ONLY


def test_python_only() -> None:
    ai = _diagnosis(IssueType.DNS)
    findings = [_finding(RuleId.MISSING_VLAN, RuleStatus.DETECTED)]
    result = compare_ai_and_python(ai, findings)
    assert result.status == ComparisonStatus.PYTHON_ONLY
    assert "missing_vlan" in result.reason


def test_conflict() -> None:
    ai = _diagnosis(IssueType.GATEWAY)
    findings = [_finding(RuleId.GATEWAY_MISMATCH, RuleStatus.NOT_DETECTED)]
    result = compare_ai_and_python(ai, findings)
    assert result.status == ComparisonStatus.CONFLICT


def test_no_deterministic_result_empty_findings() -> None:
    ai = _diagnosis(IssueType.VLAN)
    result = compare_ai_and_python(ai, [])
    assert result.status == ComparisonStatus.NO_DETERMINISTIC_RESULT


def test_no_deterministic_result_all_insufficient() -> None:
    ai = _diagnosis(IssueType.VLAN)
    findings = [
        _finding(RuleId.MISSING_VLAN, RuleStatus.INSUFFICIENT_EVIDENCE),
        _finding(RuleId.MISSING_ROUTE, RuleStatus.INSUFFICIENT_EVIDENCE),
    ]
    result = compare_ai_and_python(ai, findings)
    assert result.status == ComparisonStatus.NO_DETERMINISTIC_RESULT


def test_comparison_does_not_assume_no_finding_means_ai_wrong() -> None:
    # Absence of a Python finding must not be treated as CONFLICT or as
    # evidence against the AI diagnosis. It must be NO_DETERMINISTIC_RESULT.
    ai = _diagnosis(IssueType.NAT)
    findings = [_finding(RuleId.DUPLICATE_IP, RuleStatus.INSUFFICIENT_EVIDENCE)]
    result = compare_ai_and_python(ai, findings)
    assert result.status == ComparisonStatus.NO_DETERMINISTIC_RESULT


def test_multiple_python_findings_all_detected_but_unrelated_to_ai() -> None:
    ai = _diagnosis(IssueType.ACL)
    findings = [
        _finding(RuleId.MISSING_VLAN, RuleStatus.DETECTED),
        _finding(RuleId.MISSING_ROUTE, RuleStatus.DETECTED),
    ]
    result = compare_ai_and_python(ai, findings)
    assert result.status == ComparisonStatus.PYTHON_ONLY
    assert "missing_vlan" in result.reason
    assert "missing_route" in result.reason


def test_multiple_evidence_items_do_not_affect_comparison() -> None:
    ai = _diagnosis(IssueType.VLAN, evidence_count=5)
    findings = [_finding(RuleId.MISSING_VLAN, RuleStatus.DETECTED)]
    result = compare_ai_and_python(ai, findings)
    assert result.status == ComparisonStatus.AGREEMENT


def test_ai_diagnosis_unrelated_issue_type_with_no_findings_detected() -> None:
    ai = _diagnosis(IssueType.WIRELESS)
    findings = [_finding(RuleId.MISSING_ROUTE, RuleStatus.NOT_DETECTED)]
    result = compare_ai_and_python(ai, findings)
    assert result.status == ComparisonStatus.AI_ONLY


def test_accepts_rule_engine_result_directly() -> None:
    ai = _diagnosis(IssueType.VLAN)
    engine_result = RuleEngineResult(
        findings=[_finding(RuleId.MISSING_VLAN, RuleStatus.DETECTED)]
    )
    result = compare_ai_and_python(ai, engine_result)
    assert result.status == ComparisonStatus.AGREEMENT


def test_comparison_never_calls_openai(monkeypatch) -> None:
    import openai

    def _fail(*args, **kwargs):
        raise AssertionError("compare_ai_and_python must never call OpenAI.")

    monkeypatch.setattr(openai, "OpenAI", _fail)
    ai = _diagnosis(IssueType.VLAN)
    findings = [_finding(RuleId.MISSING_VLAN, RuleStatus.DETECTED)]
    result = compare_ai_and_python(ai, findings)
    assert result.status == ComparisonStatus.AGREEMENT