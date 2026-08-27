"""Post-fix verification controls. Pure display."""
from __future__ import annotations

import streamlit as st

from models.verification import Verification, VerificationStatus


def render_verification_form() -> Verification | None:
    st.subheader("6. Verification")
    st.caption("After applying the fix in Packet Tracer, record whether it resolved the issue.")

    status_label = st.radio(
        "Verification status",
        options=["Verified", "Not verified", "Not attempted"],
        horizontal=True, key="verification_status_radio",
    )
    evidence = st.text_area(
        "Verification evidence",
        placeholder="e.g. show vlan brief now lists VLAN 20; ping succeeded.",
        key="verification_evidence",
    )

    if not st.button("Save verification", key="save_verification_button"):
        return None

    status_map = {
        "Verified": VerificationStatus.VERIFIED,
        "Not verified": VerificationStatus.NOT_VERIFIED,
        "Not attempted": VerificationStatus.NOT_ATTEMPTED,
    }
    verification = Verification(status=status_map[status_label], evidence=evidence)
    st.success(f"Verification recorded: {verification.status.value}")
    return verification