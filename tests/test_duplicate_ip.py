"""Dedicated duplicate-IP rule tests (M4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from models.rules import RuleId, RuleStatus
from rules import duplicate_ip
from rules.engine import run_rules

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "rule_cases.json"


def _cases() -> list[dict]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))["duplicate_ip"]


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case["id"])
def test_duplicate_ip_fixture_cases(case: dict) -> None:
    finding = duplicate_ip.evaluate(case["symptom"], case["topology_notes"], case["show_output"])
    assert finding.rule_id == RuleId.DUPLICATE_IP
    assert finding.status == RuleStatus(case["expected_status"])
    blob = " ".join(finding.evidence).lower()
    for needle in case["evidence_contains"]:
        assert needle.lower() in blob
    assert finding.evidence


def test_duplicate_ip_same_device_listed_twice_is_not_duplicate() -> None:
    finding = duplicate_ip.evaluate(
        "",
        "PC1 = 192.168.1.10. PC1 is 192.168.1.10.",
        "PC2 = 192.168.1.11.",
    )
    assert finding.status == RuleStatus.NOT_DETECTED


def test_duplicate_ip_multiple_simultaneous_findings() -> None:
    payload = json.loads(FIXTURES.read_text(encoding="utf-8"))["multiple_findings"]
    result = run_rules(payload["symptom"], payload["topology_notes"], payload["show_output"])
    detected = {item.rule_id.value for item in result.findings if item.status == RuleStatus.DETECTED}
    assert "duplicate_ip" in detected
    assert set(payload["expected_detected"]).issubset(detected)
