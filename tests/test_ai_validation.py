"""M6 tests: AI structured output validation.

No comparison, human review, or dashboard logic covered here.
"""
from __future__ import annotations

import json

import pytest

from ai.validator import AIValidationError, validate_ai_response
from models.diagnosis import AIDiagnosis

VALID_PAYLOAD = {
    "diagnosis": {
        "root_cause": "VLAN 20 is missing from Switch1.",
        "issue_type": "VLAN",
        "osi_layer": "Layer 2",
        "confidence": 85,
        "severity": "medium",
    },
    "evidence": [
        {"source": "show_output", "observation": "show vlan brief does not list VLAN 20."}
    ],
    "next_command": {"command": "show vlan brief", "purpose": "Confirm VLAN 20 exists."},
    "fix_steps": ["Create VLAN 20.", "Assign Fa0/2 as an access port in VLAN 20."],
    "uncertainties": ["Intended subnet for VLAN 20 was not confirmed."],
}


def _payload(**overrides):
    data = json.loads(json.dumps(VALID_PAYLOAD))  # deep copy
    data.update(overrides)
    return data


def test_valid_response_becomes_typed_model() -> None:
    result = validate_ai_response(json.dumps(VALID_PAYLOAD))
    assert isinstance(result, AIDiagnosis)
    assert result.diagnosis.root_cause == VALID_PAYLOAD["diagnosis"]["root_cause"]
    assert result.diagnosis.confidence == 85


def test_invalid_json_is_rejected() -> None:
    with pytest.raises(AIValidationError, match="not valid JSON"):
        validate_ai_response("{not json at all")


def test_empty_response_is_rejected() -> None:
    with pytest.raises(AIValidationError):
        validate_ai_response("")


def test_missing_field_is_rejected() -> None:
    payload = json.loads(json.dumps(VALID_PAYLOAD))
    del payload["next_command"]
    with pytest.raises(AIValidationError, match="failed schema validation"):
        validate_ai_response(json.dumps(payload))


def test_invalid_issue_type_is_rejected() -> None:
    payload = json.loads(json.dumps(VALID_PAYLOAD))
    payload["diagnosis"]["issue_type"] = "NOT_A_TYPE"
    with pytest.raises(AIValidationError, match="failed schema validation"):
        validate_ai_response(json.dumps(payload))


def test_invalid_severity_is_rejected() -> None:
    payload = json.loads(json.dumps(VALID_PAYLOAD))
    payload["diagnosis"]["severity"] = "catastrophic"
    with pytest.raises(AIValidationError, match="failed schema validation"):
        validate_ai_response(json.dumps(payload))


def test_confidence_above_100_is_rejected() -> None:
    payload = json.loads(json.dumps(VALID_PAYLOAD))
    payload["diagnosis"]["confidence"] = 101
    with pytest.raises(AIValidationError, match="failed schema validation"):
        validate_ai_response(json.dumps(payload))


def test_confidence_below_0_is_rejected() -> None:
    payload = json.loads(json.dumps(VALID_PAYLOAD))
    payload["diagnosis"]["confidence"] = -1
    with pytest.raises(AIValidationError, match="failed schema validation"):
        validate_ai_response(json.dumps(payload))


def test_empty_evidence_list_is_still_valid() -> None:
    # M1 allows empty collections; evidence is not required to be non-empty.
    payload = json.loads(json.dumps(VALID_PAYLOAD))
    payload["evidence"] = []
    result = validate_ai_response(json.dumps(payload))
    assert result.evidence == []


def test_invalid_evidence_structure_is_rejected() -> None:
    payload = json.loads(json.dumps(VALID_PAYLOAD))
    payload["evidence"] = [{"source": "not_a_valid_source", "observation": "x"}]
    with pytest.raises(AIValidationError, match="failed schema validation"):
        validate_ai_response(json.dumps(payload))


def test_missing_next_command_is_rejected() -> None:
    payload = json.loads(json.dumps(VALID_PAYLOAD))
    del payload["next_command"]
    with pytest.raises(AIValidationError, match="failed schema validation"):
        validate_ai_response(json.dumps(payload))


def test_invalid_next_command_structure_is_rejected() -> None:
    payload = json.loads(json.dumps(VALID_PAYLOAD))
    payload["next_command"] = "show vlan brief"  # must be an object, not a string
    with pytest.raises(AIValidationError, match="failed schema validation"):
        validate_ai_response(json.dumps(payload))


def test_invalid_fix_steps_type_is_rejected() -> None:
    payload = json.loads(json.dumps(VALID_PAYLOAD))
    payload["fix_steps"] = "just create the vlan"  # must be a list, not a string
    with pytest.raises(AIValidationError, match="failed schema validation"):
        validate_ai_response(json.dumps(payload))


def test_markdown_code_fence_is_stripped_and_still_validates() -> None:
    fenced = "```json\n" + json.dumps(VALID_PAYLOAD) + "\n```"
    result = validate_ai_response(fenced)
    assert isinstance(result, AIDiagnosis)


def test_non_object_json_is_rejected() -> None:
    with pytest.raises(AIValidationError, match="must be a JSON object"):
        validate_ai_response(json.dumps(["not", "an", "object"]))