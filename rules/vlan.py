"""R005 — Missing VLAN."""

from __future__ import annotations

from models.rules import PythonFinding, RuleId, RuleStatus
from rules.extract import parse_vlan_brief_ids, referenced_vlan_ids


def evaluate(symptom: str, topology_notes: str, show_output: str) -> PythonFinding:
    required = referenced_vlan_ids(topology_notes, show_output)
    present = parse_vlan_brief_ids(show_output)

    if present is None:
        return PythonFinding(
            rule_id=RuleId.MISSING_VLAN,
            status=RuleStatus.INSUFFICIENT_EVIDENCE,
            evidence=["No VLAN table evidence (such as show vlan brief) was supplied."],
        )

    if not required:
        return PythonFinding(
            rule_id=RuleId.MISSING_VLAN,
            status=RuleStatus.INSUFFICIENT_EVIDENCE,
            evidence=["No required VLAN identifiers were present in topology notes or interface configuration."],
        )

    missing = sorted(required - present)
    if missing:
        evidence = [
            f"VLAN {vlan_id} is referenced in topology or configuration but is absent from VLAN evidence."
            for vlan_id in missing
        ]
        evidence.append(f"VLANs present in evidence: {', '.join(str(item) for item in sorted(present))}.")
        return PythonFinding(
            rule_id=RuleId.MISSING_VLAN,
            status=RuleStatus.DETECTED,
            evidence=evidence,
        )

    return PythonFinding(
        rule_id=RuleId.MISSING_VLAN,
        status=RuleStatus.NOT_DETECTED,
        evidence=[f"Referenced VLANs are present: {', '.join(str(item) for item in sorted(required))}."],
    )
