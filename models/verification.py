"""Post-fix verification model."""

from enum import Enum

from pydantic import BaseModel


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    NOT_VERIFIED = "not_verified"
    NOT_ATTEMPTED = "not_attempted"


class Verification(BaseModel):
    status: VerificationStatus
    evidence: str
