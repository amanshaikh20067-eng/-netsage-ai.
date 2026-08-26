"""Deterministic Python rule finding models."""

from enum import Enum

from pydantic import BaseModel, Field


class RuleId(str, Enum):
    DUPLICATE_IP = "duplicate_ip"
    WRONG_SUBNET_MASK = "wrong_subnet_mask"
    GATEWAY_MISMATCH = "gateway_mismatch"
    INTERFACE_DOWN = "interface_down"
    MISSING_VLAN = "missing_vlan"
    MISSING_ROUTE = "missing_route"


class RuleStatus(str, Enum):
    DETECTED = "detected"
    NOT_DETECTED = "not_detected"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class PythonFinding(BaseModel):
    rule_id: RuleId
    status: RuleStatus
    evidence: list[str] = Field(default_factory=list)


class RuleEngineResult(BaseModel):
    findings: list[PythonFinding]
