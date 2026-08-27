"""M11 tests: dashboard metric calculations.

Pure data tests; no Streamlit rendering is invoked here.
"""
from __future__ import annotations

from datetime import datetime, timezone

from core.review_logger import ReviewLog
from ui.dashboard_view import compute_dashboard_metrics


def _diagnosis_payload(issue_type: str, severity: str) -> dict:
    return {
        "diagnosis": {
            "root_cause": "Example root cause.",
            "issue_type": issue_type,
            "osi_layer": "Layer 2",
            "confidence": 80,
            "severity": severity,
        },
        "evidence": [],
        "next_command": {"command": "show run", "purpose": "Confirm state."},
        "fix_steps": [],
        "uncertainties": [],
    }


def _review_log(
    review_id: str, decision: str, issue_type: str = "VLAN", severity: str = "medium"
) -> ReviewLog:
    diagnosis_payload = _diagnosis_payload(issue_type, severity)
    return ReviewLog.model_validate(
        {
            "review_id": review_id,
            "case_id": "CASE-001",
            "ai_diagnosis": diagnosis_payload,
            "python_findings": [],
            "comparison": {"status": "AGREEMENT", "reason": "Example."},
            "human_decision": {
                "review_id": review_id,
                "case_id": "CASE-001",
                "ai_diagnosis": diagnosis_payload,
                "human_decision": decision,
                "human_final_diagnosis": diagnosis_payload if decision != "rejected" else None,
                "review_comment": "",
            },
            "verification": {"status": "not_attempted", "evidence": ""},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


def test_empty_reviews_returns_zeroed_metrics() -> None:
    metrics = compute_dashboard_metrics([])
    assert metrics.total_reviews == 0
    assert metrics.issue_type_counts == {}
    assert metrics.severity_counts == {}
    assert metrics.decision_counts == {"accepted": 0, "edited": 0, "rejected": 0}
    assert metrics.agreement_rate is None


def test_decision_counts_match_plan_example() -> None:
    reviews = (
        [_review_log(f"A{i}", "accepted") for i in range(5)]
        + [_review_log(f"E{i}", "edited") for i in range(3)]
        + [_review_log(f"R{i}", "rejected") for i in range(2)]
    )
    metrics = compute_dashboard_metrics(reviews)
    assert metrics.total_reviews == 10
    assert metrics.decision_counts == {"accepted": 5, "edited": 3, "rejected": 2}


def test_issue_type_counts_reflect_actual_data() -> None:
    reviews = [
        _review_log("R1", "accepted", issue_type="VLAN"),
        _review_log("R2", "accepted", issue_type="VLAN"),
        _review_log("R3", "accepted", issue_type="DHCP"),
    ]
    metrics = compute_dashboard_metrics(reviews)
    assert metrics.issue_type_counts == {"VLAN": 2, "DHCP": 1}


def test_severity_counts_reflect_actual_data() -> None:
    reviews = [
        _review_log("R1", "accepted", severity="high"),
        _review_log("R2", "accepted", severity="high"),
        _review_log("R3", "accepted", severity="low"),
    ]
    metrics = compute_dashboard_metrics(reviews)
    assert metrics.severity_counts == {"high": 2, "low": 1}


def test_agreement_rate_is_computed_not_hardcoded() -> None:
    reviews = (
        [_review_log(f"A{i}", "accepted") for i in range(3)]
        + [_review_log(f"E{i}", "edited") for i in range(1)]
    )
    metrics = compute_dashboard_metrics(reviews)
    assert metrics.agreement_rate == 3 / 4


def test_single_rejected_review() -> None:
    reviews = [_review_log("R1", "rejected")]
    metrics = compute_dashboard_metrics(reviews)
    assert metrics.decision_counts == {"accepted": 0, "edited": 0, "rejected": 1}
    assert metrics.agreement_rate == 0.0