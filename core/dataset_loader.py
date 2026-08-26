"""Load and validate the troubleshooting case dataset.

Expected evaluation fields stay on the Case model for tests. Runtime helpers
must not pass those fields to the AI.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from models.case import Case, IssueType

DEFAULT_DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "cases.json"

REQUIRED_ISSUE_TYPES = frozenset(
    {
        IssueType.VLAN,
        IssueType.GATEWAY,
        IssueType.DHCP,
        IssueType.DNS,
        IssueType.ROUTING,
        IssueType.ACL,
        IssueType.NAT,
        IssueType.WIRELESS,
    }
)


class DatasetLoadError(Exception):
    """Raised when the case dataset cannot be read or validated."""


def runtime_input(case: Case) -> dict[str, str]:
    """Return only the fields that may be sent to the AI at runtime."""
    return {
        "symptom": case.symptom,
        "topology_notes": case.topology_notes,
        "show_output": case.show_output,
    }


def load_cases(path: Path | str | None = None) -> list[Case]:
    """Load every case from JSON. Invalid or duplicate cases abort the load."""
    dataset_path = Path(path) if path is not None else DEFAULT_DATASET_PATH

    try:
        raw_text = dataset_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DatasetLoadError(f"Unable to read dataset at {dataset_path}: {exc}") from exc

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise DatasetLoadError(f"Dataset is not valid JSON: {exc}") from exc

    if not isinstance(payload, list):
        raise DatasetLoadError("Dataset must be a JSON array of cases.")

    cases: list[Case] = []
    seen_ids: dict[str, int] = {}

    for index, item in enumerate(payload):
        case_id = item.get("case_id") if isinstance(item, dict) else None
        location = f"index {index}"
        if case_id:
            location = f"index {index} (case_id={case_id})"

        try:
            case = Case.model_validate(item)
        except ValidationError as exc:
            raise DatasetLoadError(f"Case failed validation at {location}: {exc}") from exc

        previous_index = seen_ids.get(case.case_id)
        if previous_index is not None:
            raise DatasetLoadError(
                f"Duplicate case_id {case.case_id!r} at index {index} "
                f"(first seen at index {previous_index})."
            )

        seen_ids[case.case_id] = index
        cases.append(case)

    return cases
