"""M3 deterministic rule engine tests. No OpenAI."""

from models.rules import RuleId, RuleStatus
from rules.engine import run_rules
from rules import duplicate_ip, gateway, interface, route, subnet_mask, vlan


def _finding(result, rule_id: RuleId):
    return next(item for item in result.findings if item.rule_id == rule_id)


def test_engine_runs_all_six_rules_independently() -> None:
    result = run_rules("PC cannot ping.", "No extra notes.", "No show output.")
    assert {item.rule_id for item in result.findings} == set(RuleId)
    assert all(item.status == RuleStatus.INSUFFICIENT_EVIDENCE for item in result.findings)


def test_duplicate_ip_detected() -> None:
    finding = duplicate_ip.evaluate(
        "PC1 cannot ping PC2.",
        "PC1 = 192.168.1.10. PC2 = 192.168.1.10.",
        "",
    )
    assert finding.status == RuleStatus.DETECTED
    assert finding.rule_id == RuleId.DUPLICATE_IP
    assert any("192.168.1.10" in item for item in finding.evidence)


def test_duplicate_ip_not_detected() -> None:
    finding = duplicate_ip.evaluate(
        "PC1 cannot ping PC2.",
        "PC1 = 192.168.1.10. PC2 = 192.168.1.11.",
        "",
    )
    assert finding.status == RuleStatus.NOT_DETECTED


def test_duplicate_ip_insufficient_evidence() -> None:
    finding = duplicate_ip.evaluate("PC1 cannot ping PC2.", "Both devices appear connected.", "")
    assert finding.status == RuleStatus.INSUFFICIENT_EVIDENCE


def test_subnet_detected() -> None:
    finding = subnet_mask.evaluate(
        "PC1 cannot reach the server.",
        "PC1 is 192.168.10.10/24 on the student LAN.",
        "PC1> ipconfig\nIP Address......................: 192.168.10.10\nSubnet Mask.....................: 255.255.0.0\nDefault Gateway.................: 192.168.10.1",
    )
    assert finding.status == RuleStatus.DETECTED
    assert any("255.255.0.0" in item for item in finding.evidence)


def test_subnet_valid() -> None:
    finding = subnet_mask.evaluate(
        "PC1 cannot reach the server.",
        "PC1 is 192.168.10.10/24 on the student LAN.",
        "PC1> ipconfig\nIP Address......................: 192.168.10.10\nSubnet Mask.....................: 255.255.255.0\nDefault Gateway.................: 192.168.10.1",
    )
    assert finding.status == RuleStatus.NOT_DETECTED


def test_subnet_insufficient_evidence() -> None:
    finding = subnet_mask.evaluate("PC1 cannot ping PC2.", "Both PCs are connected to Switch1.", "")
    assert finding.status == RuleStatus.INSUFFICIENT_EVIDENCE


def test_gateway_detected() -> None:
    finding = gateway.evaluate(
        "PC1 cannot ping the web server.",
        "PC1 IP is 192.168.10.10/24. The LAN gateway should be 192.168.10.1.",
        "PC1> ipconfig\nIP Address......................: 192.168.10.10\nSubnet Mask.....................: 255.255.255.0\nDefault Gateway.................: 192.168.20.1",
    )
    assert finding.status == RuleStatus.DETECTED
    assert any("192.168.20.1" in item for item in finding.evidence)


def test_gateway_valid() -> None:
    finding = gateway.evaluate(
        "PC1 cannot ping the web server.",
        "PC1 IP is 192.168.10.10/24. The LAN gateway should be 192.168.10.1.",
        "PC1> ipconfig\nIP Address......................: 192.168.10.10\nSubnet Mask.....................: 255.255.255.0\nDefault Gateway.................: 192.168.10.1",
    )
    assert finding.status == RuleStatus.NOT_DETECTED


def test_gateway_insufficient_evidence() -> None:
    finding = gateway.evaluate("PC cannot ping.", "A router is present.", "Switch1# show vlan brief")
    assert finding.status == RuleStatus.INSUFFICIENT_EVIDENCE


def test_interface_down() -> None:
    finding = interface.evaluate(
        "PC1 cannot ping PC2.",
        "PC1 is connected to Router1 GigabitEthernet0/1.",
        "Router1# show interfaces\nGigabitEthernet0/1 is administratively down, line protocol is down",
    )
    assert finding.status == RuleStatus.DETECTED
    assert any("administratively down" in item.lower() for item in finding.evidence)


def test_interface_up() -> None:
    finding = interface.evaluate(
        "PC1 cannot ping PC2.",
        "PC1 is connected to Router1 GigabitEthernet0/1.",
        "Router1# show interfaces\nGigabitEthernet0/1 is up, line protocol is up",
    )
    assert finding.status == RuleStatus.NOT_DETECTED


def test_interface_insufficient_evidence() -> None:
    finding = interface.evaluate("PC1 cannot ping PC2.", "PC1 is connected to Switch1 Fa0/1.", "")
    assert finding.status == RuleStatus.INSUFFICIENT_EVIDENCE


def test_vlan_missing() -> None:
    finding = vlan.evaluate(
        "PC2 cannot reach PC1.",
        "PC1 belongs to VLAN 10. PC2 belongs to VLAN 20.",
        "Switch1# show vlan brief\n\nVLAN Name                             Status    Ports\n---- -------------------------------- --------- -------------------------------\n1    default                          active    Fa0/3, Fa0/4\n10   STUDENTS                         active    Fa0/1",
    )
    assert finding.status == RuleStatus.DETECTED
    assert any("VLAN 20" in item for item in finding.evidence)


def test_vlan_present() -> None:
    finding = vlan.evaluate(
        "PC2 cannot reach PC1.",
        "PC1 belongs to VLAN 10. PC2 belongs to VLAN 20.",
        "Switch1# show vlan brief\n\nVLAN Name                             Status    Ports\n---- -------------------------------- --------- -------------------------------\n1    default                          active    Fa0/3, Fa0/4\n10   STUDENTS                         active    Fa0/1\n20   STAFF                            active    Fa0/2",
    )
    assert finding.status == RuleStatus.NOT_DETECTED


def test_vlan_insufficient_evidence() -> None:
    finding = vlan.evaluate(
        "PC2 cannot reach PC1.",
        "PC1 belongs to VLAN 10. PC2 belongs to VLAN 20.",
        "Switch1# show interfaces fa0/1 switchport\nAccess Mode VLAN: 10",
    )
    assert finding.status == RuleStatus.INSUFFICIENT_EVIDENCE


def test_route_missing() -> None:
    finding = route.evaluate(
        "PC1 cannot ping PC2.",
        "Each router needs a static route to the remote LAN. Add a static route to 192.168.2.0/24 on RouterA.",
        "RouterA# show ip route\nCodes: C - connected, S - static\nC    192.168.1.0/24 is directly connected, GigabitEthernet0/0\nC    10.0.0.0/30 is directly connected, GigabitEthernet0/1",
    )
    assert finding.status == RuleStatus.DETECTED
    assert any("192.168.2.0" in item for item in finding.evidence)


def test_route_present() -> None:
    finding = route.evaluate(
        "PC1 cannot ping PC2.",
        "Each router needs a static route to the remote LAN. RouterA should have a route to 192.168.2.0/24.",
        "RouterA# show ip route\nCodes: C - connected, S - static\nC    192.168.1.0/24 is directly connected, GigabitEthernet0/0\nS    192.168.2.0/24 [1/0] via 10.0.0.2",
    )
    assert finding.status == RuleStatus.NOT_DETECTED


def test_route_insufficient_evidence() -> None:
    finding = route.evaluate("PC1 cannot ping PC2.", "There is a WAN link between RouterA and RouterB.", "")
    assert finding.status == RuleStatus.INSUFFICIENT_EVIDENCE


def test_engine_preserves_evidence_and_never_calls_openai() -> None:
    import inspect

    from rules import engine as engine_module

    source = inspect.getsource(engine_module)
    assert "import openai" not in source
    assert "from openai" not in source
    result = run_rules(
        "PC2 cannot reach PC1.",
        "PC1 belongs to VLAN 10. PC2 belongs to VLAN 20.",
        "Switch1# show vlan brief\nVLAN Name Status Ports\n1    default active Fa0/3\n10   STUDENTS active Fa0/1",
    )
    vlan_finding = _finding(result, RuleId.MISSING_VLAN)
    assert vlan_finding.status == RuleStatus.DETECTED
    assert vlan_finding.evidence
