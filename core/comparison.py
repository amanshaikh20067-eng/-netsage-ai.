"""AI vs Python deterministic comparison engine.

Pure, deterministic comparison logic. Never calls OpenAI. Never modifies
the AI diagnosis or Python findings it is given — it only reads them and
returns a ComparisonResult.

Design note on rule-to-issue-type mapping:
The six Python rules do not map one-to-one onto the nine AIDiagnosis
issue types. Each rule is assigned a "primary" issue type (the domain it
most directly targets) and zero or more "related" issue types (domains
where the same underlying evidence could plausibly manifest). This
mapping is a deliberate design choice, not something specified by the
implementation plan, and is documented here so it can be revisited.
"""
from __future__ import annotations

from models.case import IssueType
from models.comparison import ComparisonResult, ComparisonStatus
from models.diagnosis import AIDiagnosis
from models.rules import PythonFinding, RuleEngineResult, RuleId, RuleStatus

RULE_PRIMARY_ISSUE_TYPE: dict[RuleId, IssueType] = {
    RuleId.DUPLICATE_IP: IssueType.OTHER,
    RuleId.WRONG_SUBNET_MASK: IssueType.GATEWAY,
    RuleId.GATEWAY_MISMATCH: IssueType.GATEWAY,
    RuleId.INTERFACE_DOWN: IssueType.OTHER,
    RuleId.MISSING_VLAN: IssueType.VLAN,
    RuleId.MISSING_ROUTE: IssueType.ROUTING,
}

RULE_RELATED_ISSUE_TYPES: dict[RuleId, frozenset[IssueType]] = {
    RuleId.DUPLICATE_IP: frozenset({IssueType.DHCP, IssueType.GATEWAY}),
    RuleId.WRONG_SUBNET_MASK: frozenset({IssueType.OTHER}),
    RuleId.GATEWAY_MISMATCH: frozenset({IssueType.DHCP}),
    RuleId.INTERFACE_DOWN: frozenset({IssueType.VLAN, IssueType.ROUTING, IssueType.WIRELESS}),
    RuleId.MISSING_VLAN: frozenset({IssueType.WIRELESS}),
    RuleId.MISSING_ROUTE: frozenset({IssueType.GATEWAY}),
}


def _normalize_findings(python_findings: list[PythonFinding] | RuleEngineResult | None) -> list[PythonFinding]:
    if python_findings is None:
        return []
    if isinstance(python_findings, RuleEngineResult):
        return list(python_findings.findings)
    return list(python_findings)


def compare_ai_and_python(
    ai_diagnosis: AIDiagnosis,
    python_findings: list[PythonFinding] | RuleEngineResult | None,
) -> ComparisonResult:
    """Compare a validated AI diagnosis against deterministic Python findings.

    Does not assume that an absence of a Python finding means the AI is
    wrong: NO_DETERMINISTIC_RESULT is returned whenever Python could not
    reach any conclusion, rather than treating that as agreement,
    disagreement, or evidence of anything about the AI's diagnosis.
    """
    findings = _normalize_findings(python_findings)

    if not findings:
        return ComparisonResult(
            status=ComparisonStatus.NO_DETERMINISTIC_RESULT,
            reason="No Python findings were supplied.",
        )

    detected = [f for f in findings if f.status == RuleStatus.DETECTED]
    not_detected = [f for f in findings if f.status == RuleStatus.NOT_DETECTED]

    if not detected and not not_detected:
        return ComparisonResult(
            status=ComparisonStatus.NO_DETERMINISTIC_RESULT,
            reason=(
                "Python's deterministic rules could not reach a conclusion "
                "from the available evidence."
            ),
        )

    issue_type = ai_diagnosis.diagnosis.issue_type

    primary_finding = next(
        (f for f in findings if RULE_PRIMARY_ISSUE_TYPE.get(f.rule_id) == issue_type),
        None,
    )
    related_finding = next(
        (
            f
            for f in findings
            if f is not primary_finding
            and issue_type in RULE_RELATED_ISSUE_TYPES.get(f.rule_id, frozenset())
        ),
        None,
    )
    other_detected = [f for f in detected if f is not primary_finding and f is not related_finding]

    if primary_finding is not None and primary_finding.status == RuleStatus.DETECTED:
        if other_detected:
            extra = ", ".join(f.rule_id.value for f in other_detected)
            return ComparisonResult(
                status=ComparisonStatus.PARTIAL_AGREEMENT,
                reason=(
                    f"AI and Python agree that {issue_type.value} is a problem "
                    f"({primary_finding.rule_id.value}), but Python also detected "
                    f"additional issues the AI diagnosis did not address: {extra}."
                ),
            )
        return ComparisonResult(
            status=ComparisonStatus.AGREEMENT,
            reason=(
                f"AI diagnosis ({issue_type.value}) matches Python's deterministic "
                f"finding {primary_finding.rule_id.value}."
            ),
        )

    if related_finding is not None and related_finding.status == RuleStatus.DETECTED:
        return ComparisonResult(
            status=ComparisonStatus.PARTIAL_AGREEMENT,
            reason=(
                f"AI diagnosis ({issue_type.value}) is related to, but not identical "
                f"to, Python's deterministic finding {related_finding.rule_id.value}."
            ),
        )

    if primary_finding is not None and primary_finding.status == RuleStatus.NOT_DETECTED:
        return ComparisonResult(
            status=ComparisonStatus.CONFLICT,
            reason=(
                f"AI diagnosed {issue_type.value} as the root cause, but Python's "
                f"deterministic check ({primary_finding.rule_id.value}) found no "
                f"supporting evidence for that specific condition."
            ),
        )

    if detected:
        found = ", ".join(f.rule_id.value for f in detected)
        return ComparisonResult(
            status=ComparisonStatus.PYTHON_ONLY,
            reason=(
                f"Python detected {found}, which the AI diagnosis "
                f"({issue_type.value}) did not identify."
            ),
        )

    return ComparisonResult(
        status=ComparisonStatus.AI_ONLY,
        reason=(
            f"AI diagnosed {issue_type.value}, which falls outside what Python's "
            f"deterministic rules currently check, and no deterministic problems "
            f"were detected."
        ),
    )