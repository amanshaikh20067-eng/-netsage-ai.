"""Models used by the M12 end-to-end workflow."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from models.comparison import ComparisonResult
from models.diagnosis import AIDiagnosis
from models.rules import PythonFinding
from models.verification import Verification


class TroubleshootingInput(BaseModel):
    """User-provided troubleshooting information."""

    model_config = ConfigDict(extra="forbid")

    symptom: str
    topology_notes: str
    show_output: str


class AnalysisResult(BaseModel):
    """Result of AI + deterministic analysis."""

    model_config = ConfigDict(extra="forbid")

    ai_diagnosis: AIDiagnosis
    python_findings: list[PythonFinding]
    comparison: ComparisonResult


class CompletedWorkflow(BaseModel):
    """Final M12 workflow state."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    analysis: AnalysisResult
    verification: Verification
    review_id: str