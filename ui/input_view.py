"""Case input UI section. Pure display; no business logic."""
from __future__ import annotations

import streamlit as st


def render_input_form() -> dict[str, str] | None:
    """Render the case input fields. Returns raw text fields on submit, else None."""
    st.subheader("1. Case Input")
    symptom = st.text_area(
        "Symptom", height=100, key="symptom_input",
        help="What is the observed problem?",
    )
    topology_notes = st.text_area(
        "Topology notes", height=150, key="topology_input",
        help="Relevant topology / design information.",
    )
    show_output = st.text_area(
        "Show-command output", height=200, key="show_output_input",
        help="Paste raw Packet Tracer / IOS command output.",
    )
    submitted = st.button("Analyze", key="analyze_submit")

    if not submitted:
        return None
    return {
        "symptom": symptom,
        "topology_notes": topology_notes,
        "show_output": show_output,
    }
