"""Evaluate NetSage AI against the full case dataset.

Records actual AI/Python behavior. Never modifies expected answers or
fabricates results to make the system look better -- mismatches are
recorded honestly, including AI failures.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from core.comparison import (
    RULE_PRIMARY_ISSUE_TYPE,
    RULE_RELATED_ISSUE_TYPES,
    compare_ai_and_python,
)
from core.dataset_loader import load_cases
from models.case import Case
from models.diagnosis import AIDiagnosis
from models.rules import RuleEngineResult
from rules.engine import run_rules

RESULTS_PATH = Path(__file__).resolve().parent / "results.json"

AIFn = Callable[[str, str, str, RuleEngineResult], "AIDiagnosis | None"]


def _default_ai_fn(
    symptom: str, topology_notes: str, show_output: str, python_findings: RuleEngineResult
) -> AIDiagnosis | None:
    """Call the real AI diagnosis service.

    Returns None if it fails for any reason (missing key, API error,
    validation failure) so a single bad case does not stop the run.
    """
    from ai.diagnosis import DiagnosisService, DiagnosisServiceError
    from ai.validator import AIValidationError, validate_ai_response

    try:
        service = DiagnosisService()
        raw = service.request_diagnosis(symptom, topology_notes, show_output, python_findings)
        return validate_ai_response(raw.content)
    except (DiagnosisServiceError, AIValidationError):
        return None


def evaluate_case(case: Case, ai_fn: AIFn) -> dict:
    """Run the full pipeline for one case and record the outcome honestly."""
    python_result = run_rules(case.symptom, case.topology_notes, case.show_output)
    ai_diagnosis = ai_fn(case.symptom, case.topology_notes, case.show_output, python_result)

    detected_rules = [f for f in python_result.findings if f.status.value == "detected"]
    python_correct: bool | None = None
    if detected_rules:
        # Automated proxy only, not a substitute for human judgment: did any
        # detected rule's plausible domain match the case's labeled issue type?
        python_correct = any(
            RULE_PRIMARY_ISSUE_TYPE.get(f.rule_id) == case.issue_type
            or case.issue_type in RULE_RELATED_ISSUE_TYPES.get(f.rule_id, frozenset())
            for f in detected_rules
        )

    ai_correct: bool | None = None
    comparison_status = None
    comparison_reason = None
    if ai_diagnosis is not None:
        ai_correct = ai_diagnosis.diagnosis.issue_type == case.issue_type
        comparison = compare_ai_and_python(ai_diagnosis, python_result)
        comparison_status = comparison.status.value
        comparison_reason = comparison.reason

    return {
        "case_id": case.case_id,
        "expected_issue_type": case.issue_type.value,
        "expected_root_cause": case.expected_root_cause,
        "python_findings": [
            {"rule_id": f.rule_id.value, "status": f.status.value, "evidence": f.evidence}
            for f in python_result.findings
        ],
        "python_correct": python_correct,
        "ai_issue_type": ai_diagnosis.diagnosis.issue_type.value if ai_diagnosis else None,
        "ai_root_cause": ai_diagnosis.diagnosis.root_cause if ai_diagnosis else None,
        "ai_confidence": ai_diagnosis.diagnosis.confidence if ai_diagnosis else None,
        "ai_correct": ai_correct,
        "ai_available": ai_diagnosis is not None,
        "comparison_status": comparison_status,
        "comparison_reason": comparison_reason,
        "human_correction": {
            "reviewed": False,
            "decision": None,
            "final_diagnosis": None,
            "reason": None,
        },
    }


def evaluate_all(ai_fn: AIFn = _default_ai_fn) -> list[dict]:
    """Evaluate every case in the dataset. No case is skipped or dropped."""
    cases = load_cases()
    return [evaluate_case(case, ai_fn) for case in cases]


def save_results(results: list[dict], path: Path = RESULTS_PATH) -> None:
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    results = evaluate_all()
    save_results(results)
    ai_available_count = sum(1 for r in results if r["ai_available"])
    print(f"Evaluated {len(results)} cases. AI responded successfully for {ai_available_count}.")
    print(f"Results written to {RESULTS_PATH}")
    print(
        "\nNEXT STEP (required): open results.json, review the cases where "
        "ai_correct is false or comparison_status is CONFLICT/PARTIAL_AGREEMENT, "
        "and manually fill in human_correction for at least 5 of them with your "
        "own genuine judgment. Do not fabricate these -- they must reflect real "
        "review, per the project's integrity requirements."
    )