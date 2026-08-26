"""AI vs Python comparison result model."""

from enum import Enum

from pydantic import BaseModel


class ComparisonStatus(str, Enum):
    AGREEMENT = "AGREEMENT"
    PARTIAL_AGREEMENT = "PARTIAL_AGREEMENT"
    AI_ONLY = "AI_ONLY"
    PYTHON_ONLY = "PYTHON_ONLY"
    CONFLICT = "CONFLICT"
    NO_DETERMINISTIC_RESULT = "NO_DETERMINISTIC_RESULT"


class ComparisonResult(BaseModel):
    status: ComparisonStatus
    reason: str
