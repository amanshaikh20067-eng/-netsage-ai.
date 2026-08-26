"""Deterministic rule engine. Does not call OpenAI or use AI results."""

from __future__ import annotations

from models.rules import PythonFinding, RuleEngineResult
from rules import duplicate_ip, gateway, interface, route, subnet_mask, vlan

_RULES = (
    duplicate_ip.evaluate,
    subnet_mask.evaluate,
    gateway.evaluate,
    interface.evaluate,
    vlan.evaluate,
    route.evaluate,
)


def run_rules(symptom: str, topology_notes: str, show_output: str) -> RuleEngineResult:
    """Run each networking rule independently against supplied evidence."""
    findings: list[PythonFinding] = [
        rule(symptom, topology_notes, show_output) for rule in _RULES
    ]
    return RuleEngineResult(findings=findings)
