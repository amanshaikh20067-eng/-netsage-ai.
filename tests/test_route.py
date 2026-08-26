"""Dedicated missing-route rule tests (M4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from models.rules import RuleId, RuleStatus
from rules import route
from rules.engine import run_rules

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "rule_cases.json"


def _cases() -> list[dict]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))["missing_route"]


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case["id"])
def test_route_fixture_cases(case: dict) -> None:
    finding = route.evaluate(case["symptom"], case["topology_notes"], case["show_output"])
    assert finding.rule_id == RuleId.MISSING_ROUTE
    assert finding.status == RuleStatus(case["expected_status"])
    blob = " ".join(finding.evidence).lower()
    for needle in case["evidence_contains"]:
        assert needle.lower() in blob
    assert finding.evidence


def test_route_does_not_invent_required_destination() -> None:
    finding = route.evaluate(
        "PC1 cannot ping 8.8.8.8.",
        "RouterA connects to RouterB.",
        "RouterA# show ip route\nC    192.168.1.0/24 is directly connected, GigabitEthernet0/0",
    )
    assert finding.status == RuleStatus.INSUFFICIENT_EVIDENCE
    assert any("required destination" in item.lower() for item in finding.evidence)


def test_route_malformed_table_does_not_raise() -> None:
    finding = route.evaluate(
        "Routing failed",
        "Add a static route to 10.9.9.0/24.",
        "R1# show ip route\n**** broken ****",
    )
    assert finding.status == RuleStatus.DETECTED
    assert any("10.9.9.0" in item for item in finding.evidence)
