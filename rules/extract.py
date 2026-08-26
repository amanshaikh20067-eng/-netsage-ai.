"""Conservative text extraction from supplied evidence only.

Helpers parse what is present. They do not infer missing Packet Tracer output.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

IPV4 = re.compile(
    r"\b((?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\."
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?))\b"
)
CIDR = re.compile(
    r"\b((?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\."
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?))/(3[0-2]|[12]?\d)\b"
)
MASK = re.compile(
    r"\b(255\.(?:0|128|192|224|240|248|252|254|255)\.(?:0|128|192|224|240|248|252|254|255)\."
    r"(?:0|128|192|224|240|248|252|254|255))\b"
)
PROMPT = re.compile(r"^([A-Za-z][\w.-]*)[>#]")
VLAN_ID = re.compile(r"\bvlan\s+(\d+)\b", re.IGNORECASE)
ACCESS_VLAN = re.compile(r"access\s+vlan\s+(\d+)\b", re.IGNORECASE)
ACCESS_MODE_VLAN = re.compile(r"Access Mode VLAN:\s*(\d+)", re.IGNORECASE)
VLAN_BRIEF_ROW = re.compile(r"^(\d+)\s+\S+")
PREFIX_ROW = re.compile(
    r"^\s*[A-Za-z*]{1,4}\s+(\d+\.\d+\.\d+\.\d+)(?:/(3[0-2]|[12]?\d))?",
    re.MULTILINE,
)

SKIP_NAMES = {
    "vlan",
    "ip",
    "dns",
    "default",
    "subnet",
    "network",
    "address",
    "interface",
    "status",
    "protocol",
    "name",
    "port",
    "codes",
    "layer",
    "reply",
    "pinging",
    "server",
    "success",
}


@dataclass(frozen=True)
class HostRecord:
    name: str
    ip: str
    mask: str | None = None
    gateway: str | None = None
    source: str = ""


def as_text(value: object) -> str:
    return value if isinstance(value, str) else ""


def ip_to_int(ip: str) -> int:
    parts = [int(item) for item in ip.split(".")]
    return (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]


def cidr_to_mask(prefix: int) -> str:
    if prefix < 0 or prefix > 32:
        raise ValueError(f"CIDR prefix must be 0-32, got {prefix}")
    bits = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    return ".".join(str((bits >> shift) & 0xFF) for shift in (24, 16, 8, 0))


def mask_to_cidr(mask: str) -> int:
    value = ip_to_int(mask)
    if value == 0:
        return 0
    return bin(value).count("1")


def same_subnet(ip: str, mask: str, other: str) -> bool:
    mask_int = ip_to_int(mask)
    return (ip_to_int(ip) & mask_int) == (ip_to_int(other) & mask_int)


def combined_text(symptom: str, topology_notes: str, show_output: str) -> str:
    return f"{symptom}\n{topology_notes}\n{show_output}"


def parse_host_records(symptom: str, topology_notes: str, show_output: str) -> list[HostRecord]:
    symptom = as_text(symptom)
    topology_notes = as_text(topology_notes)
    show_output = as_text(show_output)
    records: list[HostRecord] = []
    records.extend(_parse_ipconfig_blocks(show_output))
    records.extend(_parse_interface_brief_ips(show_output))
    records.extend(_parse_named_assignments(topology_notes))
    records.extend(_parse_named_assignments(show_output))
    records.extend(_parse_named_assignments(symptom))
    return records


def _parse_ipconfig_blocks(text: str) -> list[HostRecord]:
    records: list[HostRecord] = []
    lines = text.splitlines()
    current_name = "ipconfig-host"
    i = 0
    while i < len(lines):
        prompt = PROMPT.match(lines[i].strip())
        if prompt:
            current_name = prompt.group(1)
        lower = lines[i].lower()
        if "ip address" in lower and ":" in lines[i]:
            ip_match = IPV4.search(lines[i])
            if ip_match:
                mask = None
                gateway = None
                for look in range(1, 4):
                    if i + look >= len(lines):
                        break
                    nxt = lines[i + look]
                    nxt_lower = nxt.lower()
                    if "subnet mask" in nxt_lower:
                        mask_match = MASK.search(nxt) or IPV4.search(nxt)
                        if mask_match:
                            mask = mask_match.group(1)
                    if "default gateway" in nxt_lower:
                        gw_match = IPV4.search(nxt)
                        if gw_match:
                            gateway = gw_match.group(1)
                records.append(
                    HostRecord(
                        name=current_name,
                        ip=ip_match.group(1),
                        mask=mask,
                        gateway=gateway,
                        source="ipconfig",
                    )
                )
        i += 1
    return records


def _parse_interface_brief_ips(text: str) -> list[HostRecord]:
    records: list[HostRecord] = []
    if "ip interface brief" not in text.lower() and "show ip int brief" not in text.lower():
        in_brief = False
    else:
        in_brief = False
    lines = text.splitlines()
    for line in lines:
        lowered = line.lower()
        if "ip interface brief" in lowered or "show ip int brief" in lowered:
            in_brief = True
            continue
        if in_brief and (line.startswith("#") or (PROMPT.match(line.strip()) and "interface" not in lowered)):
            if PROMPT.match(line.strip()) and "show" not in lowered:
                in_brief = False
        if not in_brief and "ip interface brief" not in text.lower():
            continue
        match = re.match(
            r"^(?P<intf>\S+)\s+(?P<ip>\d+\.\d+\.\d+\.\d+)\s+\S+\s+\S+\s+\S+",
            line.strip(),
        )
        if match and match.group("ip") != "unassigned":
            records.append(
                HostRecord(
                    name=match.group("intf"),
                    ip=match.group("ip"),
                    source="show ip interface brief",
                )
            )
    if records:
        return records
    for line in lines:
        match = re.match(
            r"^(?P<intf>(?:GigabitEthernet|FastEthernet|Ethernet|Serial|Vlan)\S*)\s+"
            r"(?P<ip>\d+\.\d+\.\d+\.\d+)\s+",
            line.strip(),
            re.IGNORECASE,
        )
        if match:
            records.append(
                HostRecord(
                    name=match.group("intf"),
                    ip=match.group("ip"),
                    source="interface ip",
                )
            )
    return records


def _parse_named_assignments(text: str) -> list[HostRecord]:
    records: list[HostRecord] = []
    pattern = re.compile(
        r"\b([A-Za-z][\w.-]*)\s+(?:IP\s+)?(?:address\s+)?(?:is|=)\s+"
        r"(\d+\.\d+\.\d+\.\d+)(?:/(\d{1,2}))?",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        name = match.group(1)
        if name.lower() in SKIP_NAMES:
            continue
        prefix = match.group(3)
        mask = None
        if prefix is not None:
            prefix_int = int(prefix)
            if prefix_int > 32:
                continue
            mask = cidr_to_mask(prefix_int)
        records.append(
            HostRecord(
                name=name,
                ip=match.group(2),
                mask=mask,
                source="named assignment",
            )
        )
    return records


def documented_gateway(topology_notes: str) -> str | None:
    topology_notes = as_text(topology_notes)
    patterns = [
        r"gateway should be[^\n]*?(\d+\.\d+\.\d+\.\d+)",
        r"correct gateway is[^\n]*?(\d+\.\d+\.\d+\.\d+)",
        r"documented to use\s+(\d+\.\d+\.\d+\.\d+)",
        r"default gateway[^\n]*?(\d+\.\d+\.\d+\.\d+)",
        r"use gateway\s+(\d+\.\d+\.\d+\.\d+)",
        r"gateway is Router[^\n]*?(\d+\.\d+\.\d+\.\d+)",
        r"G0/0 at\s+(\d+\.\d+\.\d+\.\d+)",
        r"G0/0\s+(\d+\.\d+\.\d+\.\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, topology_notes, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def documented_masks(topology_notes: str) -> list[tuple[str, str]]:
    """Return (ip, mask) pairs that topology states explicitly."""
    topology_notes = as_text(topology_notes)
    pairs: list[tuple[str, str]] = []
    for match in CIDR.finditer(topology_notes):
        pairs.append((match.group(1), cidr_to_mask(int(match.group(2)))))
    mask_phrase = re.search(
        r"(?:mask|subnet mask)\s+(255\.\d+\.\d+\.\d+)",
        topology_notes,
        re.IGNORECASE,
    )
    ip_match = IPV4.search(topology_notes)
    if mask_phrase and ip_match:
        pairs.append((ip_match.group(1), mask_phrase.group(1)))
    return pairs


def parse_vlan_brief_ids(show_output: str) -> set[int] | None:
    show_output = as_text(show_output)
    lower = show_output.lower()
    if "show vlan brief" not in lower and "vlan name" not in lower:
        return None
    present: set[int] = set()
    in_table = False
    for line in show_output.splitlines():
        if "vlan name" in line.lower() or "show vlan brief" in line.lower():
            in_table = True
            continue
        if in_table and line.strip().startswith("----"):
            continue
        if in_table and PROMPT.match(line.strip()):
            break
        if in_table:
            row = VLAN_BRIEF_ROW.match(line.strip())
            if row:
                present.add(int(row.group(1)))
    if not present:
        return None
    return present


def referenced_vlan_ids(topology_notes: str, show_output: str) -> set[int]:
    topology_notes = as_text(topology_notes)
    show_output = as_text(show_output)
    found: set[int] = set()
    for match in VLAN_ID.finditer(topology_notes):
        found.add(int(match.group(1)))
    for match in ACCESS_VLAN.finditer(show_output):
        found.add(int(match.group(1)))
    for match in ACCESS_MODE_VLAN.finditer(show_output):
        vlan_id = int(match.group(1))
        if vlan_id != 1:
            found.add(vlan_id)
    found.discard(1)
    return found


def parse_route_prefixes(show_output: str) -> list[tuple[str, int]] | None:
    show_output = as_text(show_output)
    lower = show_output.lower()
    if "show ip route" not in lower:
        return None
    prefixes: list[tuple[str, int]] = []
    in_table = False
    for line in show_output.splitlines():
        if "show ip route" in line.lower():
            in_table = True
            continue
        if in_table and PROMPT.match(line.strip()) and "show ip route" not in line.lower():
            if not line.strip().startswith("Codes") and not re.match(r"^\s*[A-Za-z*]", line):
                in_table = False
        if not in_table:
            continue
        match = re.search(
            r"(\d+\.\d+\.\d+\.\d+)(?:/(3[0-2]|[12]?\d))?",
            line,
        )
        if match and re.match(r"^\s*[A-Za-z*]", line):
            network = match.group(1)
            prefix = int(match.group(2)) if match.group(2) else 32
            if "is subnetted" in line.lower():
                continue
            prefixes.append((network, prefix))
        if "0.0.0.0/0" in line or re.search(r"\b0\.0\.0\.0\b.*\b0\.0\.0\.0\b", line):
            prefixes.append(("0.0.0.0", 0))
    if not prefixes:
        return []
    return prefixes


def required_route_prefixes(topology_notes: str) -> list[tuple[str, int]]:
    topology_notes = as_text(topology_notes)
    required: list[tuple[str, int]] = []
    if re.search(r"\bdefault route\b", topology_notes, re.IGNORECASE):
        required.append(("0.0.0.0", 0))
    patterns = [
        r"route to\s+(\d+\.\d+\.\d+\.\d+(?:/\d+)?)",
        r"static route to\s+(\d+\.\d+\.\d+\.\d+(?:/\d+)?)",
        r"remote (?:network|lan|subnet)\s+(?:is\s+)?(\d+\.\d+\.\d+\.\d+(?:/\d+)?)",
        r"destination network\s+(\d+\.\d+\.\d+\.\d+(?:/\d+)?)",
        r"branch lan is\s+(\d+\.\d+\.\d+\.\d+(?:/\d+)?)",
        r"needs a static route to the remote lan[^\n]*?(\d+\.\d+\.\d+\.\d+(?:/\d+)?)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, topology_notes, re.IGNORECASE):
            required.append(_parse_prefix(match.group(1)))
    # Deduplicate
    unique: dict[tuple[str, int], None] = {}
    for item in required:
        unique[item] = None
    return list(unique.keys())


def _parse_prefix(value: str) -> tuple[str, int]:
    if "/" in value:
        ip, prefix = value.split("/", 1)
        return ip, int(prefix)
    return value, 32


def prefix_covers(network: str, prefix: int, other_network: str, other_prefix: int) -> bool:
    if prefix > other_prefix:
        return False
    mask = cidr_to_mask(prefix)
    return same_subnet(network, mask, other_network) and prefix <= other_prefix


def route_present(
    required: tuple[str, int],
    table: list[tuple[str, int]],
) -> bool:
    req_net, req_len = required
    for net, length in table:
        if net == req_net and length == req_len:
            return True
        if req_len == 0 and net == "0.0.0.0" and length == 0:
            return True
        mask = cidr_to_mask(length)
        if req_len >= length and same_subnet(req_net, mask, net):
            return True
    return False
