"""R001 — Duplicate IP."""

from __future__ import annotations

from collections import defaultdict

from models.rules import PythonFinding, RuleId, RuleStatus
from rules.extract import parse_host_records


def evaluate(symptom: str, topology_notes: str, show_output: str) -> PythonFinding:
    records = parse_host_records(symptom, topology_notes, show_output)
    unique_assignments: dict[tuple[str, str], str] = {}
    for record in records:
        unique_assignments[(record.name.lower(), record.ip)] = record.name

    if len(unique_assignments) < 2:
        return PythonFinding(
            rule_id=RuleId.DUPLICATE_IP,
            status=RuleStatus.INSUFFICIENT_EVIDENCE,
            evidence=["Fewer than two explicit IP assignments were present in the supplied evidence."],
        )

    by_ip: dict[str, set[str]] = defaultdict(set)
    for (name, ip), display in unique_assignments.items():
        by_ip[ip].add(display)

    duplicates = {ip: names for ip, names in by_ip.items() if len(names) > 1}
    if not duplicates:
        return PythonFinding(
            rule_id=RuleId.DUPLICATE_IP,
            status=RuleStatus.NOT_DETECTED,
            evidence=["Multiple IP assignments were present and no address was shared by more than one device or interface."],
        )

    evidence = []
    for ip, names in sorted(duplicates.items()):
        listed = ", ".join(sorted(names))
        evidence.append(f"{listed} use {ip}")
    return PythonFinding(
        rule_id=RuleId.DUPLICATE_IP,
        status=RuleStatus.DETECTED,
        evidence=evidence,
    )
