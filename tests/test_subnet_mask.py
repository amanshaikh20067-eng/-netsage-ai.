"""Dedicated subnet-mask rule tests (M4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from models.rules import RuleId, RuleStatus
from rules import subnet_mask

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "rule_cases.json"


def _cases() -> list[dict]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))["wrong_subnet_mask"]


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case["id"])
def test_subnet_mask_fixture_cases(case: dict) -> None:
    finding = subnet_mask.evaluate(case["symptom"], case["topology_notes"], case["show_output"])
    assert finding.rule_id == RuleId.WRONG_SUBNET_MASK
    assert finding.status == RuleStatus(case["expected_status"])
    blob = " ".join(finding.evidence).lower()
    for needle in case["evidence_contains"]:
        assert needle.lower() in blob
    assert finding.evidence


def test_subnet_mask_does_not_guess_expected_mask() -> None:
    finding = subnet_mask.evaluate(
        "Host cannot ping.",
        "A PC is attached to Switch1.",
        "PC1> ipconfig\nIP Address......................: 10.1.1.8\nSubnet Mask.....................: 255.255.255.0\nDefault Gateway.................: 10.1.1.1",
    )
    assert finding.status == RuleStatus.INSUFFICIENT_EVIDENCE


def test_subnet_mask_malformed_input_does_not_raise() -> None:
    finding = subnet_mask.evaluate("x", "PC1 is 192.168.10.10/99.", "!!!")
    assert finding.status == RuleStatus.INSUFFICIENT_EVIDENCE
