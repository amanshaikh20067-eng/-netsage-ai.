"""M10 integration tests: input reaches backend, results display.

Uses streamlit.testing.v1.AppTest and mocks the AI call so no live
OpenAI request is ever made.
"""
from __future__ import annotations

import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from ai.diagnosis import RawDiagnosisResponse

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")

VALID_AI_JSON = json.dumps({
    "diagnosis": {
        "root_cause": "VLAN 20 is missing from Switch1.",
        "issue_type": "VLAN", "osi_layer": "Layer 2",
        "confidence": 85, "severity": "medium",
    },
    "evidence": [{"source": "show_output", "observation": "show vlan brief lacks VLAN 20."}],
    "next_command": {"command": "show vlan brief", "purpose": "Confirm VLAN 20 exists."},
    "fix_steps": ["Create VLAN 20."], "uncertainties": [],
})


def _fake_request_diagnosis(self, symptom, topology_notes, show_output, python_findings=None):
    return RawDiagnosisResponse(content=VALID_AI_JSON, model="fake-model")


def test_app_starts_and_shows_input_form() -> None:
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()
    assert not at.exception
    assert "NetSage AI" in [t.value for t in at.title]


def test_missing_api_key_shows_error(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("NETSAGE_REVIEWS_PATH", str(tmp_path / "reviews.json"))
    monkeypatch.setattr("config.settings.is_openai_configured", lambda: False)

    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()
    at.text_area(key="symptom_input").input("PC2 cannot reach PC1.")
    at.text_area(key="topology_input").input("PC2 is on VLAN 20, which does not exist yet.")
    at.text_area(key="show_output_input").input("show vlan brief\n1 default active")
    at.button(key="analyze_submit").click().run()

    assert not at.exception
    assert any("not configured" in e.value for e in at.error)
    assert any("Python Deterministic Findings" in m.value for m in at.subheader)


def test_full_pipeline_with_mocked_ai(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("NETSAGE_REVIEWS_PATH", str(tmp_path / "reviews.json"))
    monkeypatch.setattr("config.settings.is_openai_configured", lambda: True)
    monkeypatch.setattr(
        "ai.diagnosis.DiagnosisService.request_diagnosis", _fake_request_diagnosis,
    )

    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()
    at.text_area(key="symptom_input").input("PC2 cannot reach PC1.")
    at.text_area(key="topology_input").input("PC2 is on VLAN 20, which does not exist yet.")
    at.text_area(key="show_output_input").input("show vlan brief\n1 default active")
    at.button(key="analyze_submit").click().run()

    assert not at.exception
    assert any("VLAN 20 is missing from Switch1." in m.value for m in at.markdown)
    assert any("Comparison" in m.value for m in at.subheader)

    at.radio(key="review_decision_radio").set_value("Accept")
    at.button(key="submit_review_button").click().run()
    assert not at.exception
    assert any("Review recorded: accepted" in a.value for a in at.success)

    at.radio(key="verification_status_radio").set_value("Verified")
    at.button(key="save_verification_button").click().run()
    assert not at.exception
    assert any("has been logged as REV-" in i.value for i in at.info)