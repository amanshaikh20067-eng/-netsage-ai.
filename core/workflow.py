"""End-to-end NetSage AI troubleshooting workflow.

M12 integration layer.

This module orchestrates already-existing components:
    validation
    Python deterministic rules
    AI diagnosis
    AI output validation
    AI/Python comparison
    human review
    verification
    review logging

It intentionally contains orchestration only.
Networking rules, AI prompting, review logic, and persistence remain
inside their respective modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.comparison import ComparisonResult
from models.diagnosis import AIDiagnosis
from models.rules import PythonFinding
from models.verification import Verification

# Corrected imports matching your actual file structures!
from core.validator import InputValidator
from rules.engine import RuleEngine
from ai.diagnosis import DiagnosisService
from ai.validator import validate_ai_response
from core.comparison import compare_ai_and_python
from core.review import submit_review
from core.review_logger import ReviewLogger


@dataclass
class TroubleshootingInput:
    """Raw information supplied by the user."""

    symptom: str
    topology_notes: str
    show_output: str


@dataclass
class WorkflowResult:
    """Result returned by a completed analysis/review workflow."""

    ai_diagnosis: AIDiagnosis
    python_findings: list[PythonFinding]
    comparison: ComparisonResult
    human_review: Any
    verification: Verification | None
    review_log: Any | None


class WorkflowError(Exception):
    """Base exception for workflow failures."""


class InputValidationWorkflowError(WorkflowError):
    """Raised when user input is invalid."""


class AIDiagnosisWorkflowError(WorkflowError):
    """Raised when AI diagnosis cannot be completed."""


class AIValidationWorkflowError(WorkflowError):
    """Raised when AI output cannot be validated."""


class NetSageWorkflow:
    """Coordinate the complete M12 troubleshooting workflow."""

    def __init__(
        self,
        *,
        validator: InputValidator,
        rule_engine: RuleEngine,
        ai_service: DiagnosisService,
        ai_validator: Any,       
        comparison_engine: Any,  
        review_manager: Any = None, # Made optional/Any since submit_review is a function
        review_logger: Any = None,
    ) -> None:
        self.validator = validator
        self.rule_engine = rule_engine
        self.ai_service = ai_service
        self.ai_validator = ai_validator
        self.comparison_engine = comparison_engine
        self.review_manager = review_manager
        self.review_logger = review_logger

    def analyze(
        self,
        troubleshooting_input: TroubleshootingInput,
    ) -> tuple[
        AIDiagnosis,
        list[PythonFinding],
        ComparisonResult,
    ]:
        """Run validation → Python → AI → AI validation → comparison."""

        self._validate_input(troubleshooting_input)

        # Deterministic analysis must happen independently of AI.
        python_findings_result = self.rule_engine.run(
            symptom=troubleshooting_input.symptom,
            topology_notes=troubleshooting_input.topology_notes,
            show_output=troubleshooting_input.show_output
        )
        
        # Handle the RuleEngineResult wrapper
        python_findings = (
            python_findings_result.findings 
            if hasattr(python_findings_result, "findings") 
            else python_findings_result
        )

        ai_input = {
            "symptom": troubleshooting_input.symptom,
            "topology_notes": troubleshooting_input.topology_notes,
            "show_output": troubleshooting_input.show_output,
            "python_findings": [
                finding.model_dump(mode="json") if hasattr(finding, "model_dump") else finding
                for finding in python_findings
            ],
        }

        try:
            raw_ai_response = self.ai_service.diagnose(ai_input)
        except Exception as exc:
            raise AIDiagnosisWorkflowError(
                "AI diagnosis could not be completed."
            ) from exc

        try:
            ai_diagnosis = self.ai_validator(
                raw_ai_response
            )
        except Exception as exc:
            raise AIValidationWorkflowError(
                "AI response failed structured validation."
            ) from exc

        comparison = self.comparison_engine(
            ai_diagnosis=ai_diagnosis,
            python_findings=python_findings,
        )

        return (
            ai_diagnosis,
            python_findings,
            comparison,
        )

    def finalize_review(
        self,
        *,
        case_id: str,
        ai_diagnosis: AIDiagnosis,
        python_findings: list[PythonFinding],
        comparison: ComparisonResult,
        review: Any,
        verification: Verification,
    ) -> Any:
        """Persist a human-reviewed result.

        Human review must already have occurred before this method is called.
        """

        self._ensure_human_review_completed(review)

        # If a mock review manager was injected during testing, use it. 
        # Otherwise, assume 'review' is already a valid HumanReview object from submit_review.
        review_result = review
        if self.review_manager and hasattr(self.review_manager, "validate_review"):
            review_result = self.review_manager.validate_review(review)

        return self.review_logger.save_review(
            case_id=case_id,
            ai_diagnosis=ai_diagnosis,
            python_findings=python_findings,
            comparison=comparison,
            review=review_result,
            verification=verification,
        )

    def _validate_input(
        self,
        troubleshooting_input: TroubleshootingInput,
    ) -> None:
        """Validate required user input."""

        result = self.validator.validate(
            symptom=troubleshooting_input.symptom,
            topology_notes=troubleshooting_input.topology_notes,
            show_output=troubleshooting_input.show_output
        )

        if isinstance(result, dict):
            if not result.get("valid", False):
                errors = result.get("errors", [])
                raise InputValidationWorkflowError(
                    f"Invalid troubleshooting input: {errors}"
                )
            return

        if hasattr(result, "valid"):
            if not result.valid:
                errors = getattr(result, "errors", [])
                raise InputValidationWorkflowError(
                    f"Invalid troubleshooting input: {errors}"
                )
            return

        if result is False:
            raise InputValidationWorkflowError(
                "Invalid troubleshooting input."
            )

    @staticmethod
    def _ensure_human_review_completed(
        review: Any,
    ) -> None:
        """Prevent finalization without an explicit human decision."""

        decision = getattr(review, "human_decision", None)

        if decision is None:
            raise WorkflowError(
                "Human review is mandatory before finalization."
            )

        decision_value = getattr(
            decision,
            "value",
            decision,
        )

        allowed = {
            "accepted",
            "edited",
            "rejected",
        }

        if str(decision_value).lower() not in allowed:
            raise WorkflowError(
                "Invalid human review decision."
            )