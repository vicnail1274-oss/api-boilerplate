"""System guardian patrol integration for AI agent scans."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from security_scan_logic_script import run_security_scan


@dataclass(slots=True)
class PatrolResult:
    status: str
    total_findings: int
    findings_by_severity: dict[str, int]
    frameworks_triggered: list[str]
    findings: list[dict[str, Any]]


def _derive_status(findings_by_severity: dict[str, int]) -> str:
    if findings_by_severity.get("critical", 0) > 0:
        return "critical"
    if findings_by_severity.get("high", 0) > 0:
        return "alert"
    if findings_by_severity.get("medium", 0) > 0:
        return "warning"
    return "ok"


def patrol(
    raw_events: list[dict[str, Any]],
    trusted_domains: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Run security patrol and return a stable integration payload."""
    scan_output = run_security_scan(raw_events, trusted_domains=trusted_domains)
    summary = scan_output["summary"]
    findings = scan_output["findings"]
    findings_by_severity = summary["findings_by_severity"]

    result = PatrolResult(
        status=_derive_status(findings_by_severity),
        total_findings=summary["total_findings"],
        findings_by_severity=findings_by_severity,
        frameworks_triggered=summary["frameworks_triggered"],
        findings=findings,
    )
    return {
        "status": result.status,
        "total_findings": result.total_findings,
        "findings_by_severity": result.findings_by_severity,
        "frameworks_triggered": result.frameworks_triggered,
        "findings": result.findings,
    }
