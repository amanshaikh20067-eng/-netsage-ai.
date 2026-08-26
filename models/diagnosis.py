"""Structured AI diagnosis models."""

from enum import Enum

from pydantic import BaseModel, Field

from models.case import IssueType, Severity


class EvidenceSource(str, Enum):
    TOPOLOGY = "topology"
    SHOW_OUTPUT = "show_output"
    SYMPTOM = "symptom"
    PYTHON_RULE = "python_rule"


class EvidenceItem(BaseModel):
    source: EvidenceSource
    observation: str


class NextCommand(BaseModel):
    command: str
    purpose: str


class DiagnosisDetails(BaseModel):
    root_cause: str
    issue_type: IssueType
    osi_layer: str
    confidence: int = Field(ge=0, le=100)
    severity: Severity


class AIDiagnosis(BaseModel):
    """Validated AI diagnosis payload. Empty collections are allowed at M1."""

    diagnosis: DiagnosisDetails
    evidence: list[EvidenceItem] = Field(default_factory=list)
    next_command: NextCommand
    fix_steps: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
