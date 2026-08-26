"""M2 dataset loader tests. No AI, rules, or evaluation engine."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.dataset_loader import (
    DEFAULT_DATASET_PATH,
    REQUIRED_ISSUE_TYPES,
    DatasetLoadError,
    load_cases,
    runtime_input,
)
from models.case import Case, IssueType

MIN_CASE_COUNT = 30


def test_dataset_loads() -> None:
    cases = load_cases()
    assert isinstance(cases, list)
    assert all(isinstance(case, Case) for case in cases)


def test_all_cases_validate() -> None:
    cases = load_cases(DEFAULT_DATASET_PATH)
    assert len(cases) >= MIN_CASE_COUNT


def test_minimum_case_count_is_satisfied() -> None:
    cases = load_cases()
    assert len(cases) >= MIN_CASE_COUNT


def test_required_issue_categories_exist() -> None:
    present = {case.issue_type for case in load_cases()}
    missing = REQUIRED_ISSUE_TYPES - present
    assert missing == set()
    for issue_type in (
        IssueType.VLAN,
        IssueType.GATEWAY,
        IssueType.DHCP,
        IssueType.DNS,
        IssueType.ROUTING,
        IssueType.ACL,
        IssueType.NAT,
        IssueType.WIRELESS,
    ):
        assert issue_type in present


def test_duplicate_case_ids_are_rejected(tmp_path: Path) -> None:
    cases = load_cases()
    payload = [cases[0].model_dump(mode="json"), cases[0].model_dump(mode="json")]
    path = tmp_path / "dup.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(DatasetLoadError, match="Duplicate case_id"):
        load_cases(path)


def test_malformed_case_is_rejected(tmp_path: Path) -> None:
    valid = load_cases()[0].model_dump(mode="json")
    valid["issue_type"] = "NOT-A-TYPE"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([valid]), encoding="utf-8")

    with pytest.raises(DatasetLoadError, match="failed validation"):
        load_cases(path)


def test_missing_required_field_is_rejected(tmp_path: Path) -> None:
    valid = load_cases()[0].model_dump(mode="json")
    case_id = valid["case_id"]
    del valid["symptom"]
    path = tmp_path / "missing.json"
    path.write_text(json.dumps([valid]), encoding="utf-8")

    with pytest.raises(DatasetLoadError, match=case_id):
        load_cases(path)


def test_invalid_json_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(DatasetLoadError, match="not valid JSON"):
        load_cases(path)


def test_runtime_input_omits_expected_answers() -> None:
    case = load_cases()[0]
    payload = runtime_input(case)
    assert set(payload.keys()) == {"symptom", "topology_notes", "show_output"}
    assert "expected_root_cause" not in payload
    assert "expected_fix" not in payload
    assert "issue_type" not in payload
    assert payload["symptom"] == case.symptom
