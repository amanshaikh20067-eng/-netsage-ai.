"""Human review decision model."""

from enum import Enum

from pydantic import BaseModel, Field

from models.diagnosis import AIDiagnosis


class ReviewDecision(str, Enum):
    ACCEPTED = "accepted"
    EDITED = "edited"
    REJECTED = "rejected"


class HumanReview(BaseModel):
    review_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    human_decision: ReviewDecision
    human_final_diagnosis: AIDiagnosis | None = None
    review_comment: str = ""
