"""Dedicated interface-down rule tests (M4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from models.rules import RuleId, RuleStatus
from rules import interface
from rules.engine import run_rules

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "rule_cases.json"


def _cases() -> list[dict]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))["interface_down"]


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case["id"])
def test_interface_fixture_cases(case: dict) -> None:
    finding = interface.evaluate(case["symptom"], case["topology_notes"], case["show_output"])
    assert finding.rule_id == RuleId.INTERFACE_DOWN
    assert finding.status == RuleStatus(case["expected_status"])
    blob = " ".join(finding.evidence).lower()
    for needle in case["evidence_contains"]:
        assert needle.lower() in blob
    assert finding.evidence


def test_interface_does_not_infer_down_from_missing_output() -> None:
    finding = interface.evaluate(
        "The WAN might be down.",
        "Router1 Serial0/0/0 connects to the ISP.",
        "Router1# show version\nCisco IOS Software",
    )
    assert finding.status == RuleStatus.INSUFFICIENT_EVIDENCE


def test_interface_multiple_simultaneous_findings() -> None:
    payload = json.loads(FIXTURES.read_text(encoding="utf-8"))["multiple_findings"]
    result = run_rules(payload["symptom"], payload["topology_notes"], payload["show_output"])
    detected = {item.rule_id.value for item in result.findings if item.status == RuleStatus.DETECTED}
    assert "interface_down" in detected
    assert set(payload["expected_detected"]).issubset(detected)
