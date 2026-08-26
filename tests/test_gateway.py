"""Dedicated gateway-mismatch rule tests (M4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from models.rules import RuleId, RuleStatus
from rules import gateway

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "rule_cases.json"


def _cases() -> list[dict]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))["gateway_mismatch"]


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case["id"])
def test_gateway_fixture_cases(case: dict) -> None:
    finding = gateway.evaluate(case["symptom"], case["topology_notes"], case["show_output"])
    assert finding.rule_id == RuleId.GATEWAY_MISMATCH
    assert finding.status == RuleStatus(case["expected_status"])
    blob = " ".join(finding.evidence).lower()
    for needle in case["evidence_contains"]:
        assert needle.lower() in blob
    assert finding.evidence


def test_gateway_topology_conflict_on_same_subnet() -> None:
    finding = gateway.evaluate(
        "Office PC cannot reach the router.",
        "The correct gateway is 10.10.10.1.",
        "PC> ipconfig\nIP Address......................: 10.10.10.25\nSubnet Mask.....................: 255.255.255.0\nDefault Gateway.................: 10.10.10.254",
    )
    assert finding.status == RuleStatus.DETECTED
    assert any("10.10.10.254" in item and "10.10.10.1" in item for item in finding.evidence)


def test_gateway_malformed_input_does_not_raise() -> None:
    finding = gateway.evaluate("???", "not a network diagram", "#####")
    assert finding.status == RuleStatus.INSUFFICIENT_EVIDENCE
