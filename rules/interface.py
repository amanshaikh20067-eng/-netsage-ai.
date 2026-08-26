"""R004 — Interface down."""

from __future__ import annotations

import re

from models.rules import PythonFinding, RuleId, RuleStatus

NARRATIVE_DOWN = re.compile(
    r"(?P<intf>\S+)\s+is\s+(?P<state>administratively down|down, line protocol is down)",
    re.IGNORECASE,
)
NARRATIVE_UP = re.compile(
    r"(?P<intf>\S+)\s+is\s+up, line protocol is up",
    re.IGNORECASE,
)
BRIEF_ROW = re.compile(
    r"^(?P<intf>\S+)\s+\S+\s+(?:YES|NO)\s+\S+\s+"
    r"(?P<status>administratively down|down|up)\s+(?P<proto>up|down)\s*$",
    re.IGNORECASE,
)


def evaluate(symptom: str, topology_notes: str, show_output: str) -> PythonFinding:
    show_output = show_output if isinstance(show_output, str) else ""
    down: list[str] = []
    seen_state = False

    for match in NARRATIVE_DOWN.finditer(show_output):
        seen_state = True
        down.append(f"{match.group('intf')} is {match.group('state')}.")
    for _match in NARRATIVE_UP.finditer(show_output):
        seen_state = True

    for line in show_output.splitlines():
        brief = BRIEF_ROW.match(line.strip())
        if not brief:
            continue
        seen_state = True
        status = brief.group("status").lower()
        proto = brief.group("proto").lower()
        name = brief.group("intf")
        if status == "administratively down":
            down.append(f"{name} is administratively down.")
        elif status == "down" or proto == "down":
            down.append(f"{name} is down/down (status={status}, protocol={proto}).")

    if not seen_state:
        return PythonFinding(
            rule_id=RuleId.INTERFACE_DOWN,
            status=RuleStatus.INSUFFICIENT_EVIDENCE,
            evidence=["No explicit interface up/down state was present in the supplied output."],
        )

    if down:
        return PythonFinding(
            rule_id=RuleId.INTERFACE_DOWN,
            status=RuleStatus.DETECTED,
            evidence=list(dict.fromkeys(down)),
        )

    return PythonFinding(
        rule_id=RuleId.INTERFACE_DOWN,
        status=RuleStatus.NOT_DETECTED,
        evidence=["All interfaces with explicit state information are up."],
    )
