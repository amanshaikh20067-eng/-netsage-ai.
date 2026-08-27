"""M12 end-to-end integration test.

Exercises the full pipeline: Case -> Python rules -> AI (mocked) ->
validation -> comparison -> human review -> verification -> logging.
No live OpenAI call is made.
"""
from __future__ import annotations

import json

from ai.validator import validate_ai_response
from core.comparison import compare_ai_and_python
from core.review import submit_review
from core.review_logger import ReviewLogger
from models.case import Case
from models.review import ReviewDecision
from models.verification import Verification, VerificationStatus
from rules.engine import run_rules


def test_full_troubleshooting_pipeline(tmp_path) -> None:
    # 1. Case input
    case = Case(
        case_id="CASE-DEMO-001",
        issue_type="VLAN",
        severity="medium",
        symptom="PC1 cannot reach PC2 on Switch1.",
        topology_notes=(
            "PC1 is on Fa0/1 assigned to VLAN 10. PC2 is on Fa0/2 assigned "
            "to VLAN 20. VLAN 20 is missing."
        ),
        show_output=(
            "show vlan brief\n"
            "1 default active Fa0/3, Fa0/4\n"
            "10 SALES active Fa0/1"
        ),
        expected_root_cause="VLAN 20 is not created on Switch1.",
        expected_osi_layer="Layer 2",
        expected_next_command="show vlan brief",
        expected_fix="Create VLAN 20 and assign Fa0/2.",
        verification="Ping successful between PC1 and PC2.",
    )

    # 2. Python deterministic rule engine
    rule_result = run_rules(case.symptom, case.topology_notes, case.show_output)
    assert any(
        f.rule_id.value == "missing_vlan" and f.status.value == "detected"
        for f in rule_result.findings
    )

    # 3. AI diagnosis (mocked -- no live OpenAI call)
    mock_ai_json = json.dumps({
        "diagnosis": {
            "root_cause": (
                "VLAN 20 is referenced in topology but missing from switch "
                "configuration."
            ),
            "issue_type": "VLAN", "osi_layer": "Layer 2",
            "confidence": 95, "severity": "medium",
        },
        "evidence": [
            {"source": "show_output", "observation": "show vlan brief does not list VLAN 20."},
            {"source": "topology", "observation": "PC2 requires VLAN 20."},
        ],
        "next_command": {"command": "show vlan brief", "purpose": "Verify VLAN database."},
        "fix_steps": [
            "vlan 20", "name MARKETING", "interface Fa0/2", "switchport access vlan 20",
        ],
        "uncertainties": [],
    })
    ai_diagnosis = validate_ai_response(mock_ai_json)
    assert ai_diagnosis.diagnosis.issue_type.value == "VLAN"

    # 4. Comparison engine
    comparison = compare_ai_and_python(ai_diagnosis, rule_result)
    assert comparison.status.value == "AGREEMENT"

    # 5. Mandatory human review (acceptance)
    review = submit_review(
        review_id="PENDING", case_id=case.case_id, ai_diagnosis=ai_diagnosis,
        decision=ReviewDecision.ACCEPTED,
        review_comment="Confirmed missing VLAN 20 from show output.",
    )
    assert review.human_decision.value == "accepted"

    # 6. Verification recording
    verification = Verification(
        status=VerificationStatus.VERIFIED,
        evidence="PC1 ping to PC2 (192.168.20.10) succeeded with 0% packet loss.",
    )
    assert verification.status.value == "verified"

    # 7. Review logging & persistence
    log_file = tmp_path / "reviews.json"
    logger = ReviewLogger(log_file)
    record = logger.save_review(
        case_id=case.case_id, ai_diagnosis=ai_diagnosis,
        python_findings=rule_result.findings, comparison=comparison,
        review=review, verification=verification,
    )

    loaded_reviews = logger.get_all_reviews()
    assert len(loaded_reviews) == 1
    assert loaded_reviews[0].review_id == record.review_id
    assert loaded_reviews[0].case_id == "CASE-DEMO-001"


def test_full_pipeline_with_edited_review(tmp_path) -> None:
    """A second pass where the human corrects the AI diagnosis."""
    case_id = "CASE-DEMO-002"
    ai_json = json.dumps({
        "diagnosis": {
            "root_cause": "Gateway mismatch on PC3.",
            "issue_type": "GATEWAY", "osi_layer": "Layer 3",
            "confidence": 70, "severity": "high",
        },
        "evidence": [],
        "next_command": {"command": "ipconfig", "purpose": "Check PC3 gateway."},
        "fix_steps": ["Correct the default gateway."],
        "uncertainties": ["Exact intended subnet was not confirmed."],
    })
    ai_diagnosis = validate_ai_response(ai_json)

    rule_result = run_rules(
        symptom="PC3 cannot reach the internet.",
        topology_notes="PC3 should use gateway 10.0.0.1.",
        show_output="PC3> ipconfig\nDefault Gateway......: 10.0.0.254",
    )
    comparison = compare_ai_and_python(ai_diagnosis, rule_result)

    corrected = ai_diagnosis.model_copy(
        update={
            "diagnosis": ai_diagnosis.diagnosis.model_copy(
                update={"root_cause": "PC3's gateway is 10.0.0.254 instead of 10.0.0.1."}
            )
        }
    )
    review = submit_review(
        review_id="PENDING", case_id=case_id, ai_diagnosis=ai_diagnosis,
        decision=ReviewDecision.EDITED, human_final_diagnosis=corrected,
        review_comment="Corrected the specific gateway value.",
    )
    assert review.human_decision.value == "edited"
    assert review.human_final_diagnosis.diagnosis.root_cause != ai_diagnosis.diagnosis.root_cause

    verification = Verification(status=VerificationStatus.NOT_ATTEMPTED, evidence="")

    log_file = tmp_path / "reviews.json"
    logger = ReviewLogger(log_file)
    logger.save_review(
        case_id=case_id, ai_diagnosis=ai_diagnosis, python_findings=rule_result.findings,
        comparison=comparison, review=review, verification=verification,
    )
    loaded = logger.get_all_reviews()
    assert len(loaded) == 1
    assert loaded[0].human_decision.human_decision.value == "edited"