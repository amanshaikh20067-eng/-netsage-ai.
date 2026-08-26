"""R002 — Wrong subnet mask."""

from __future__ import annotations

from models.rules import PythonFinding, RuleId, RuleStatus
from rules.extract import documented_masks, parse_host_records, same_subnet


def evaluate(symptom: str, topology_notes: str, show_output: str) -> PythonFinding:
    hosts = [item for item in parse_host_records(symptom, topology_notes, show_output) if item.mask]
    expected = documented_masks(topology_notes)

    if not hosts and not expected:
        return PythonFinding(
            rule_id=RuleId.WRONG_SUBNET_MASK,
            status=RuleStatus.INSUFFICIENT_EVIDENCE,
            evidence=["No subnet mask was present in the supplied evidence."],
        )

    if not hosts or not expected:
        return PythonFinding(
            rule_id=RuleId.WRONG_SUBNET_MASK,
            status=RuleStatus.INSUFFICIENT_EVIDENCE,
            evidence=["A mask was present, but there was not enough documented expected mask information to judge it."],
        )

    mismatches: list[str] = []
    for host in hosts:
        if host.mask is None:
            continue
        for ip, mask in expected:
            if host.mask != mask and (host.ip == ip or same_subnet(host.ip, mask, ip)):
                mismatches.append(
                    f"{host.name} has mask {host.mask} but topology documents {ip} with mask {mask}."
                )

    by_name: dict[str, set[str]] = {}
    for host in hosts:
        if host.mask:
            by_name.setdefault(host.name.lower(), set()).add(host.mask)
    for name, masks in by_name.items():
        if len(masks) > 1:
            mismatches.append(f"{name} has conflicting masks: {', '.join(sorted(masks))}.")

    if mismatches:
        unique = list(dict.fromkeys(mismatches))
        return PythonFinding(
            rule_id=RuleId.WRONG_SUBNET_MASK,
            status=RuleStatus.DETECTED,
            evidence=unique,
        )

    return PythonFinding(
        rule_id=RuleId.WRONG_SUBNET_MASK,
        status=RuleStatus.NOT_DETECTED,
        evidence=["Configured masks match the masks documented in the supplied topology notes."],
    )
