"""R006 — Missing route."""

from __future__ import annotations

from models.rules import PythonFinding, RuleId, RuleStatus
from rules.extract import parse_route_prefixes, required_route_prefixes, route_present


def evaluate(symptom: str, topology_notes: str, show_output: str) -> PythonFinding:
    table = parse_route_prefixes(show_output)
    required = required_route_prefixes(topology_notes)

    if table is None:
        return PythonFinding(
            rule_id=RuleId.MISSING_ROUTE,
            status=RuleStatus.INSUFFICIENT_EVIDENCE,
            evidence=["No routing table evidence (show ip route) was supplied."],
        )

    if not required:
        return PythonFinding(
            rule_id=RuleId.MISSING_ROUTE,
            status=RuleStatus.INSUFFICIENT_EVIDENCE,
            evidence=["No required destination network was stated in the supplied topology notes."],
        )

    missing = [item for item in required if not route_present(item, table)]
    if missing:
        evidence = []
        for network, prefix in missing:
            evidence.append(f"Required destination {network}/{prefix} has no corresponding route in the supplied table.")
        return PythonFinding(
            rule_id=RuleId.MISSING_ROUTE,
            status=RuleStatus.DETECTED,
            evidence=evidence,
        )

    return PythonFinding(
        rule_id=RuleId.MISSING_ROUTE,
        status=RuleStatus.NOT_DETECTED,
        evidence=["Each required destination network appears in the supplied routing evidence."],
    )
