"""Analysis display sections: AI diagnosis, Python findings, comparison.

Pure display. No networking, comparison, or validation logic lives here.
"""
from __future__ import annotations

import streamlit as st

from models.comparison import ComparisonResult
from models.diagnosis import AIDiagnosis
from models.rules import PythonFinding


def render_ai_diagnosis(diagnosis: AIDiagnosis | None, error: str | None) -> None:
    st.subheader("2. AI Analysis")
    if error:
        st.error(error)
        return
    if diagnosis is None:
        st.info("No AI analysis yet.")
        return

    d = diagnosis.diagnosis
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Root cause:** {d.root_cause}")
        st.markdown(f"**Issue type:** {d.issue_type.value}")
        st.markdown(f"**OSI layer:** {d.osi_layer}")
    with col2:
        st.markdown(f"**Confidence:** {d.confidence}/100")
        st.markdown(f"**Severity:** {d.severity.value}")

    st.markdown("**Evidence:**")
    if diagnosis.evidence:
        for item in diagnosis.evidence:
            st.markdown(f"- [{item.source.value}] {item.observation}")
    else:
        st.caption("None reported.")

    st.markdown(
        f"**Next command:** `{diagnosis.next_command.command}` — "
        f"{diagnosis.next_command.purpose}"
    )

    if diagnosis.fix_steps:
        st.markdown("**Fix steps:**")
        for i, step in enumerate(diagnosis.fix_steps, start=1):
            st.markdown(f"{i}. {step}")

    if diagnosis.uncertainties:
        st.markdown("**Uncertainties:**")
        for u in diagnosis.uncertainties:
            st.markdown(f"- {u}")


def render_python_findings(findings: list[PythonFinding]) -> None:
    st.subheader("3. Python Deterministic Findings")
    if not findings:
        st.info("No Python findings available.")
        return
    for f in findings:
        label = f"{f.rule_id.value} — {f.status.value}"
        if f.status.value == "detected":
            st.warning(label)
        elif f.status.value == "not_detected":
            st.success(label)
        else:
            st.info(label)
        for e in f.evidence:
            st.caption(f"• {e}")


def render_comparison(comparison: ComparisonResult | None) -> None:
    st.subheader("4. Comparison")
    if comparison is None:
        st.info("No comparison available yet.")
        return
    st.markdown(f"**Status:** {comparison.status.value}")
    st.markdown(f"**Reason:** {comparison.reason}")