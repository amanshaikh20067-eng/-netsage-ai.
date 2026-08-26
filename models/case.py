"""Troubleshooting case model."""

from enum import Enum

from pydantic import BaseModel, Field


class IssueType(str, Enum):
    VLAN = "VLAN"
    GATEWAY = "GATEWAY"
    DHCP = "DHCP"
    DNS = "DNS"
    ROUTING = "ROUTING"
    ACL = "ACL"
    NAT = "NAT"
    WIRELESS = "WIRELESS"
    OTHER = "OTHER"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Case(BaseModel):
    """A Packet Tracer troubleshooting case used for dataset and evaluation."""

    case_id: str = Field(min_length=1)
    issue_type: IssueType
    severity: Severity
    symptom: str
    topology_notes: str
    show_output: str
    expected_root_cause: str
    expected_osi_layer: str
    expected_next_command: str
    expected_fix: str
    verification: str
