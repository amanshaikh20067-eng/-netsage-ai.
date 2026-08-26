"""M1 data-model tests. No networking or diagnosis business logic."""

import json

import pytest
from pydantic import ValidationError

from models.case import Case, IssueType, Severity
from models.comparison import ComparisonResult, ComparisonStatus
from models.diagnosis import (
    AIDiagnosis,
    DiagnosisDetails,
    EvidenceItem,
    EvidenceSource,
    NextCommand,
)
from models.review import HumanReview, ReviewDecision
from models.rules import PythonFinding, RuleId, RuleStatus
from models.verification import Verification, VerificationStatus


def _valid_case_payload() -> dict:
    return {
        "case_id": "CASE-001",
        "issue_type": "VLAN",
        "severity": "medium",
        "symptom": "PC1 cannot ping PC2.",
        "topology_notes": "PC1 is in VLAN 10. PC2 is in VLAN 20.",
        "show_output": "VLAN 10 exists. VLAN 20 is absent.",
        "expected_root_cause": "Missing VLAN 20",
        "expected_osi_layer": "Layer 2",
        "expected_next_command": "show vlan brief",
        "expected_fix": "Create VLAN 20 and assign the PC2 port.",
        "verification": "show vlan brief lists VLAN 20",
    }


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
        "fix_steps": ["Create VLAN 20."],
        "uncertainties": [],
    }


def test_valid_case_creation() -> None:
    case = Case.model_validate(_valid_case_payload())
    assert case.case_id == "CASE-001"
    assert case.issue_type == IssueType.VLAN
    assert case.severity == Severity.MEDIUM


def test_invalid_issue_type() -> None:
    payload = _valid_case_payload()
    payload["issue_type"] = "SWITCH"
    with pytest.raises(ValidationError):
        Case.model_validate(payload)


def test_invalid_severity() -> None:
    payload = _valid_case_payload()
    payload["severity"] = "critical"
    with pytest.raises(ValidationError):
        Case.model_validate(payload)


def test_invalid_review_decision() -> None:
    with pytest.raises(ValidationError):
        HumanReview.model_validate(
            {
                "review_id": "REV-001",
                "case_id": "CASE-001",
                "human_decision": "ignore",
                "human_final_diagnosis": None,
                "review_comment": "",
            }
        )


def test_confidence_below_zero() -> None:
    payload = _valid_diagnosis_payload()
    payload["diagnosis"]["confidence"] = -1
    with pytest.raises(ValidationError):
        AIDiagnosis.model_validate(payload)


def test_confidence_above_100() -> None:
    payload = _valid_diagnosis_payload()
    payload["diagnosis"]["confidence"] = 101
    with pytest.raises(ValidationError):
        AIDiagnosis.model_validate(payload)


def test_valid_ai_diagnosis() -> None:
    diagnosis = AIDiagnosis.model_validate(_valid_diagnosis_payload())
    assert diagnosis.diagnosis.confidence == 85
    assert diagnosis.diagnosis.issue_type == IssueType.VLAN
    assert diagnosis.next_command.command == "show vlan brief"


def test_invalid_ai_diagnosis() -> None:
    payload = _valid_diagnosis_payload()
    del payload["diagnosis"]["root_cause"]
    with pytest.raises(ValidationError):
        AIDiagnosis.model_validate(payload)


def test_valid_comparison() -> None:
    result = ComparisonResult.model_validate(
        {
            "status": "AGREEMENT",
            "reason": "Both identify missing VLAN 20.",
        }
    )
    assert result.status == ComparisonStatus.AGREEMENT


def test_valid_review() -> None:
    review = HumanReview.model_validate(
        {
            "review_id": "REV-001",
            "case_id": "CASE-001",
            "human_decision": "accepted",
            "human_final_diagnosis": _valid_diagnosis_payload(),
            "review_comment": "Agrees with the AI diagnosis.",
        }
    )
    assert review.human_decision == ReviewDecision.ACCEPTED
    assert review.human_final_diagnosis is not None


def test_valid_verification() -> None:
    verification = Verification.model_validate(
        {
            "status": "verified",
            "evidence": "ping 192.168.10.20 succeeded",
        }
    )
    assert verification.status == VerificationStatus.VERIFIED


def test_case_json_round_trip() -> None:
    case = Case.model_validate(_valid_case_payload())
    restored = Case.model_validate_json(case.model_dump_json())
    assert restored == case


def test_ai_diagnosis_json_round_trip() -> None:
    diagnosis = AIDiagnosis.model_validate(_valid_diagnosis_payload())
    as_json = json.loads(diagnosis.model_dump_json())
    restored = AIDiagnosis.model_validate(as_json)
    assert restored == diagnosis


def test_python_finding_model() -> None:
    finding = PythonFinding.model_validate(
        {
            "rule_id": "missing_vlan",
            "status": "detected",
            "evidence": ["VLAN 20 referenced in topology notes"],
        }
    )
    assert finding.rule_id == RuleId.MISSING_VLAN
    assert finding.status == RuleStatus.DETECTED


def test_invalid_comparison_status() -> None:
    with pytest.raises(ValidationError):
        ComparisonResult.model_validate({"status": "MAYBE", "reason": "n/a"})


def test_confidence_boundary_values() -> None:
    for value in (0, 100):
        details = DiagnosisDetails.model_validate(
            {
                "root_cause": "Interface is administratively down.",
                "issue_type": "OTHER",
                "osi_layer": "Layer 1",
                "confidence": value,
                "severity": "high",
            }
        )
        assert details.confidence == value


def test_evidence_item_and_next_command_types() -> None:
    item = EvidenceItem.model_validate(
        {"source": "show_output", "observation": "Gi0/1 is administratively down"}
    )
    assert item.source == EvidenceSource.SHOW_OUTPUT
    command = NextCommand.model_validate(
        {"command": "show ip interface brief", "purpose": "Check interface state"}
    )
    assert command.command.startswith("show")
