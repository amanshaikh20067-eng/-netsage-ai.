"""R003 — Gateway mismatch."""

from __future__ import annotations

from models.rules import PythonFinding, RuleId, RuleStatus
from rules.extract import documented_gateway, parse_host_records, same_subnet


def evaluate(symptom: str, topology_notes: str, show_output: str) -> PythonFinding:
    hosts = parse_host_records(symptom, topology_notes, show_output)
    hosts_with_gateway = [item for item in hosts if item.gateway is not None]
    documented = documented_gateway(topology_notes)

    if not hosts_with_gateway and documented is None:
        return PythonFinding(
            rule_id=RuleId.GATEWAY_MISMATCH,
            status=RuleStatus.INSUFFICIENT_EVIDENCE,
            evidence=["No host default gateway was present in the supplied evidence."],
        )

    problems: list[str] = []
    for host in hosts_with_gateway:
        if host.gateway in {"0.0.0.0", "255.255.255.255"}:
            problems.append(f"{host.name} has no usable default gateway ({host.gateway}).")
            continue
        if host.mask and not same_subnet(host.ip, host.mask, host.gateway):
            problems.append(
                f"{host.name} gateway {host.gateway} is outside subnet {host.ip}/{host.mask}."
            )
        if documented and host.gateway != documented:
            problems.append(
                f"{host.name} gateway {host.gateway} conflicts with documented gateway {documented}."
            )

    if documented and not hosts_with_gateway:
        return PythonFinding(
            rule_id=RuleId.GATEWAY_MISMATCH,
            status=RuleStatus.INSUFFICIENT_EVIDENCE,
            evidence=["Topology documents a gateway, but no host gateway configuration was supplied."],
        )

    if not hosts_with_gateway:
        return PythonFinding(
            rule_id=RuleId.GATEWAY_MISMATCH,
            status=RuleStatus.INSUFFICIENT_EVIDENCE,
            evidence=["No host default gateway was present in the supplied evidence."],
        )

    if problems:
        return PythonFinding(
            rule_id=RuleId.GATEWAY_MISMATCH,
            status=RuleStatus.DETECTED,
            evidence=list(dict.fromkeys(problems)),
        )

    return PythonFinding(
        rule_id=RuleId.GATEWAY_MISMATCH,
        status=RuleStatus.NOT_DETECTED,
        evidence=["Host default gateway is in the local subnet and does not conflict with documented topology."],
    )
