"""Validates raw AI diagnosis text against the structured AIDiagnosis model.

No AI response reaches a diagnosis display, comparison, or review step
unless it passes through validate_ai_response() successfully.
"""
from __future__ import annotations

from pydantic import ValidationError as PydanticValidationError

from ai.schema import JSONExtractionError, extract_json_object
from models.diagnosis import AIDiagnosis


class AIValidationError(Exception):
    """Raised when raw AI output fails schema or field validation.

    Carries a human-readable summary of what was wrong so callers
    (human review, logging, dashboards) can surface useful detail
    rather than a bare exception.
    """

    def __init__(self, message: str, *, raw_text: str | None = None) -> None:
        super().__init__(message)
        self.raw_text = raw_text


def validate_ai_response(raw_text: str) -> AIDiagnosis:
    """Validate raw AI text and return a typed AIDiagnosis.

    Raises AIValidationError for any failure: invalid JSON, missing
    fields, invalid enum values, out-of-range confidence, malformed
    evidence/next_command/fix_steps, etc. Never returns a partially
    valid or best-guess diagnosis.
    """
    try:
        payload = extract_json_object(raw_text)
    except JSONExtractionError as exc:
        raise AIValidationError(str(exc), raw_text=raw_text) from exc

    try:
        return AIDiagnosis.model_validate(payload)
    except PydanticValidationError as exc:
        raise AIValidationError(
            f"AI response failed schema validation: {exc}",
            raw_text=raw_text,
        ) from exc