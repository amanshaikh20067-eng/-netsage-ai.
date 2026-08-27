"""Dashboard data aggregation and display.

Metric calculation is a pure function (compute_dashboard_metrics) so it
can be tested without Streamlit or a live review log file. Nothing here
hardcodes counts or percentages -- everything is derived from the
reviews actually supplied.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import streamlit as st

from core.review_logger import ReviewLog, ReviewLogger


@dataclass(frozen=True)
class DashboardMetrics:
    total_reviews: int
    issue_type_counts: dict[str, int]
    severity_counts: dict[str, int]
    decision_counts: dict[str, int]

    @property
    def agreement_rate(self) -> float | None:
        """Fraction of reviews where the human accepted the AI diagnosis as-is.

        None when there is no data, so callers never divide by zero.
        """
        if self.total_reviews == 0:
            return None
        return self.decision_counts.get("accepted", 0) / self.total_reviews


def compute_dashboard_metrics(reviews: list[ReviewLog]) -> DashboardMetrics:
    """Derive dashboard statistics from stored review records.

    Safe to call with an empty list -- returns zeroed-out metrics rather
    than raising.
    """
    issue_types: Counter[str] = Counter()
    severities: Counter[str] = Counter()
    decisions: Counter[str] = Counter({"accepted": 0, "edited": 0, "rejected": 0})

    for review in reviews:
        issue_types[review.ai_diagnosis.diagnosis.issue_type.value] += 1
        severities[review.ai_diagnosis.diagnosis.severity.value] += 1
        decisions[review.human_decision.human_decision.value] += 1

    return DashboardMetrics(
        total_reviews=len(reviews),
        issue_type_counts=dict(issue_types),
        severity_counts=dict(severities),
        decision_counts=dict(decisions),
    )


def render_dashboard(logger: ReviewLogger) -> None:
    st.subheader("Dashboard")
    reviews = logger.get_all_reviews()
    metrics = compute_dashboard_metrics(reviews)

    if metrics.total_reviews == 0:
        st.info("No reviews have been logged yet. Analyze and review a case to populate the dashboard.")
        return

    st.metric("Total reviews", metrics.total_reviews)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Issue types**")
        st.bar_chart(metrics.issue_type_counts)
    with col2:
        st.markdown("**Severity**")
        st.bar_chart(metrics.severity_counts)
    with col3:
        st.markdown("**AI vs human decision**")
        st.bar_chart(metrics.decision_counts)

    if metrics.agreement_rate is not None:
        st.metric("Acceptance rate", f"{metrics.agreement_rate:.0%}")