"""Dedicated missing-VLAN rule tests (M4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from models.rules import RuleId, RuleStatus
from rules import vlan
from rules.engine import run_rules

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "rule_cases.json"


def _cases() -> list[dict]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))["missing_vlan"]


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case["id"])
def test_vlan_fixture_cases(case: dict) -> None:
    finding = vlan.evaluate(case["symptom"], case["topology_notes"], case["show_output"])
    assert finding.rule_id == RuleId.MISSING_VLAN
    assert finding.status == RuleStatus(case["expected_status"])
    blob = " ".join(finding.evidence).lower()
    for needle in case["evidence_contains"]:
        assert needle.lower() in blob
    assert finding.evidence


def test_vlan_does_not_treat_missing_table_as_vlan_absent() -> None:
    finding = vlan.evaluate(
        "PC2 cannot reach PC1.",
        "PC2 belongs to VLAN 20.",
        "Switch1# show running-config\nhostname Switch1",
    )
    assert finding.status == RuleStatus.INSUFFICIENT_EVIDENCE


def test_vlan_multiple_simultaneous_findings() -> None:
    payload = json.loads(FIXTURES.read_text(encoding="utf-8"))["multiple_findings"]
    result = run_rules(payload["symptom"], payload["topology_notes"], payload["show_output"])
    detected = {item.rule_id.value for item in result.findings if item.status == RuleStatus.DETECTED}
    assert "missing_vlan" in detected
    assert set(payload["expected_detected"]).issubset(detected)
