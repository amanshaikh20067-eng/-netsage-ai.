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
    ai_diagnosis: AIDiagnosis
    """The original, unmodified AI diagnosis. Always preserved regardless
    of the human decision, so the AI's original output can never be lost
    or silently overwritten."""
    human_decision: ReviewDecision
    human_final_diagnosis: AIDiagnosis | None = None
    """The diagnosis to actually act on: equals ai_diagnosis when accepted,
    the human's replacement when edited, and None when rejected."""
    review_comment: str = ""