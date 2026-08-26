"""Persistence service for NetSage AI human-review records."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from models.comparison import ComparisonResult
from models.diagnosis import AIDiagnosis
from models.review import HumanReview
from models.rules import PythonFinding
from models.verification import Verification
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ReviewLog(BaseModel):
    """Persisted representation of a completed human review."""

    model_config = ConfigDict(extra="forbid")

    review_id: str
    case_id: str
    ai_diagnosis: AIDiagnosis
    python_findings: list[PythonFinding] = Field(default_factory=list)
    comparison: ComparisonResult
    human_decision: HumanReview
    verification: Verification
    timestamp: datetime


class ReviewLogError(Exception):
    """Base exception for review-log failures."""


class ReviewLogCorruptedError(ReviewLogError):
    """Raised when the review JSON file cannot be parsed or validated."""


class ReviewLogger:
    """Store and retrieve human-review records in a JSON file."""

    _REVIEW_ID_PATTERN = re.compile(r"^REV-(\d+)$")

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)

    def save_review(
        self,
        *,
        case_id: str,
        ai_diagnosis: AIDiagnosis,
        python_findings: list[PythonFinding],
        comparison: ComparisonResult,
        review: HumanReview,
        verification: Verification,
    ) -> ReviewLog:
        """Create and persist a new review log."""

        if not case_id.strip():
            raise ValueError("case_id must not be empty")

        records = self._load_records()

        review_id = self._generate_next_review_id(records)

        review_log = ReviewLog(
            review_id=review_id,
            case_id=case_id,
            ai_diagnosis=ai_diagnosis,
            python_findings=python_findings,
            comparison=comparison,
            human_decision=review,
            verification=verification,
            timestamp=datetime.now(timezone.utc),
        )

        records.append(review_log)
        self._write_records(records)

        return review_log

    def get_review(self, review_id: str) -> ReviewLog | None:
        """Return a review by ID, or None if it does not exist."""

        if not review_id.strip():
            raise ValueError("review_id must not be empty")

        records = self._load_records()

        for record in records:
            if record.review_id == review_id:
                return record

        return None

    def get_all_reviews(self) -> list[ReviewLog]:
        """Return all persisted review records."""

        return self._load_records()

    def _load_records(self) -> list[ReviewLog]:
        """Load and validate persisted records."""

        if not self.file_path.exists():
            return []

        try:
            raw_text = self.file_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ReviewLogError(
                f"Unable to read review log: {self.file_path}"
            ) from exc

        if not raw_text.strip():
            raise ReviewLogCorruptedError(
                f"Review log is empty or invalid: {self.file_path}"
            )

        try:
            payload: Any = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ReviewLogCorruptedError(
                f"Review log contains invalid JSON: {self.file_path}"
            ) from exc

        if not isinstance(payload, list):
            raise ReviewLogCorruptedError(
                "Review log JSON root must be an array."
            )

        records: list[ReviewLog] = []

        try:
            for index, item in enumerate(payload):
                records.append(ReviewLog.model_validate(item))
        except ValidationError as exc:
            raise ReviewLogCorruptedError(
                f"Review log contains an invalid record at index {index}."
            ) from exc

        return records

    def _write_records(self, records: list[ReviewLog]) -> None:
        """Write records using a temporary file replacement."""

        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        payload = [
            record.model_dump(mode="json")
            for record in records
        ]

        temp_path = self.file_path.with_suffix(
            self.file_path.suffix + ".tmp"
        )

        try:
            temp_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            temp_path.replace(self.file_path)
        except OSError as exc:
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except OSError:
                pass

            raise ReviewLogError(
                f"Unable to write review log: {self.file_path}"
            ) from exc

    def _generate_next_review_id(
        self,
        records: list[ReviewLog],
    ) -> str:
        """Generate the next sequential unique review ID."""

        max_number = 0

        for record in records:
            match = self._REVIEW_ID_PATTERN.fullmatch(record.review_id)
            if match:
                max_number = max(max_number, int(match.group(1)))

        return f"REV-{max_number + 1:06d}"