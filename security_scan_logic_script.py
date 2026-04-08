"""Security scan logic for AI Agent behavior anomaly detection.

This module is standalone by design so it can be consumed by automation
workflows without impacting existing runtime services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import re
from typing import Any, Iterable
from urllib.parse import urlparse


SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass(slots=True)
class AgentEvent:
    timestamp: datetime
    agent_id: str
    event_type: str
    payload: str = ""
    target: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DetectionFinding:
    rule_id: str
    framework: str
    severity: str
    title: str
    description: str
    event_index: int
    event_time: str
    agent_id: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScanReport:
    findings: list[DetectionFinding]
    findings_by_severity: dict[str, int]
    frameworks_triggered: list[str]


class AgentBehaviorAnomalyDetector:
    """Combines Snort/Sigma/YARA-inspired logic over agent telemetry."""

    # YARA-inspired content signatures
    _PROMPT_INJECTION_MARKERS = [
        "ignore previous instructions",
        "bypass policy",
        "disregard safety",
        "reveal system prompt",
        "exfiltrate",
        "do not follow your rules",
        "developer mode override",
    ]

    _HIGH_RISK_COMMAND_PATTERNS = [
        re.compile(r"\brm\s+-rf\s+/", re.IGNORECASE),
        re.compile(r"\bcurl\b.+\|\s*(bash|sh)\b", re.IGNORECASE),
        re.compile(r"\bwget\b.+\|\s*(bash|sh)\b", re.IGNORECASE),
        re.compile(r"\bchmod\s+777\b", re.IGNORECASE),
        re.compile(r"\b(base64|python)\b.+\beval\b", re.IGNORECASE),
        re.compile(r"\b(nc|netcat)\b.+\s-e\s+", re.IGNORECASE),
    ]

    # Snort-inspired network indicators
    _SUSPICIOUS_HOST_PATTERNS = [
        re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$"),  # direct IPv4 destination
        re.compile(r".*\.ngrok-free\.app$", re.IGNORECASE),
        re.compile(r".*\.trycloudflare\.com$", re.IGNORECASE),
        re.compile(r".*pastebin\.com$", re.IGNORECASE),
    ]

    def __init__(
        self,
        trusted_domains: Iterable[str] | None = None,
        tool_call_burst_threshold: int = 25,
        burst_window_seconds: int = 60,
        sigma_correlation_window_minutes: int = 5,
    ) -> None:
        self.trusted_domains = {
            d.lower()
            for d in (
                trusted_domains
                or {
                    "api.openai.com",
                    "raw.githubusercontent.com",
                    "github.com",
                    "registry.npmjs.org",
                }
            )
        }
        self.tool_call_burst_threshold = tool_call_burst_threshold
        self.burst_window = timedelta(seconds=burst_window_seconds)
        self.sigma_window = timedelta(minutes=sigma_correlation_window_minutes)

    def scan(self, events: list[AgentEvent]) -> ScanReport:
        findings: list[DetectionFinding] = []
        normalized = sorted(events, key=lambda event: event.timestamp)

        findings.extend(self._detect_yara_signatures(normalized))
        findings.extend(self._detect_snort_network_anomalies(normalized))
        findings.extend(self._detect_tool_burst(normalized))
        findings.extend(self._detect_sigma_correlations(normalized))

        severity_counts = {level: 0 for level in ("low", "medium", "high", "critical")}
        frameworks: set[str] = set()
        for finding in findings:
            severity_counts[finding.severity] += 1
            frameworks.add(finding.framework)

        findings.sort(
            key=lambda item: (
                -SEVERITY_ORDER.get(item.severity, 0),
                item.event_time,
                item.rule_id,
            )
        )
        return ScanReport(
            findings=findings,
            findings_by_severity=severity_counts,
            frameworks_triggered=sorted(frameworks),
        )

    def _detect_yara_signatures(self, events: list[AgentEvent]) -> list[DetectionFinding]:
        findings: list[DetectionFinding] = []
        for idx, event in enumerate(events):
            payload = event.payload.lower()
            for marker in self._PROMPT_INJECTION_MARKERS:
                if marker in payload:
                    findings.append(
                        self._build_finding(
                            idx,
                            event,
                            rule_id="YARA-AI-001",
                            framework="YARA",
                            severity="high",
                            title="Prompt injection marker detected",
                            description="Detected content signature commonly used in prompt injection attempts.",
                            evidence={"matched_marker": marker},
                        )
                    )

            if event.event_type in {"command_execute", "shell_command"}:
                for pattern in self._HIGH_RISK_COMMAND_PATTERNS:
                    if pattern.search(event.payload):
                        findings.append(
                            self._build_finding(
                                idx,
                                event,
                                rule_id="YARA-AI-002",
                                framework="YARA",
                                severity="critical",
                                title="High-risk command signature detected",
                                description="Command payload matched a high-risk execution signature.",
                                evidence={"matched_regex": pattern.pattern},
                            )
                        )
        return findings

    def _detect_snort_network_anomalies(self, events: list[AgentEvent]) -> list[DetectionFinding]:
        findings: list[DetectionFinding] = []
        for idx, event in enumerate(events):
            if event.event_type not in {"outbound_request", "network_call", "http_request"}:
                continue

            destination = (event.target or event.metadata.get("destination") or "").strip()
            if not destination:
                continue

            hostname = self._extract_hostname(destination)
            if not hostname:
                continue

            if hostname not in self.trusted_domains and not hostname.endswith(".githubusercontent.com"):
                findings.append(
                    self._build_finding(
                        idx,
                        event,
                        rule_id="SNORT-AI-001",
                        framework="Snort",
                        severity="medium",
                        title="Outbound request to untrusted destination",
                        description="Outbound request was sent to a domain not present in trusted allow-list.",
                        evidence={"destination": destination, "hostname": hostname},
                    )
                )

            for pattern in self._SUSPICIOUS_HOST_PATTERNS:
                if pattern.match(hostname):
                    findings.append(
                        self._build_finding(
                            idx,
                            event,
                            rule_id="SNORT-AI-002",
                            framework="Snort",
                            severity="high",
                            title="Suspicious outbound destination pattern",
                            description="Destination hostname matched suspicious network indicator pattern.",
                            evidence={
                                "destination": destination,
                                "hostname": hostname,
                                "matched_regex": pattern.pattern,
                            },
                        )
                    )
        return findings

    def _detect_tool_burst(self, events: list[AgentEvent]) -> list[DetectionFinding]:
        findings: list[DetectionFinding] = []
        tool_events = [
            (idx, event)
            for idx, event in enumerate(events)
            if event.event_type in {"tool_call", "command_execute", "shell_command"}
        ]
        start = 0
        for end, (event_idx, current) in enumerate(tool_events):
            while current.timestamp - tool_events[start][1].timestamp > self.burst_window:
                start += 1
            window_count = end - start + 1
            if window_count > self.tool_call_burst_threshold:
                findings.append(
                    self._build_finding(
                        event_idx,
                        current,
                        rule_id="SIGMA-AI-001",
                        framework="Sigma",
                        severity="medium",
                        title="Tool invocation burst anomaly",
                        description="Tool/command activity exceeded expected burst threshold.",
                        evidence={
                            "window_seconds": int(self.burst_window.total_seconds()),
                            "window_count": window_count,
                            "threshold": self.tool_call_burst_threshold,
                        },
                    )
                )
                break
        return findings

    def _detect_sigma_correlations(self, events: list[AgentEvent]) -> list[DetectionFinding]:
        findings: list[DetectionFinding] = []
        prompt_injection_indices = [
            idx for idx, event in enumerate(events) if self._has_injection_marker(event.payload)
        ]
        for injection_idx in prompt_injection_indices:
            injection_event = events[injection_idx]
            for follow_idx in range(injection_idx + 1, len(events)):
                candidate = events[follow_idx]
                if candidate.timestamp - injection_event.timestamp > self.sigma_window:
                    break
                if candidate.event_type not in {"command_execute", "shell_command"}:
                    continue
                if self._matches_high_risk_command(candidate.payload):
                    findings.append(
                        self._build_finding(
                            follow_idx,
                            candidate,
                            rule_id="SIGMA-AI-002",
                            framework="Sigma",
                            severity="critical",
                            title="Prompt-injection to command-execution chain",
                            description="Correlated potential prompt injection followed by high-risk command execution.",
                            evidence={
                                "injection_event_index": injection_idx,
                                "injection_event_time": injection_event.timestamp.isoformat(),
                                "correlation_window_minutes": int(self.sigma_window.total_seconds() // 60),
                            },
                        )
                    )
                    break
        return findings

    def _build_finding(
        self,
        event_index: int,
        event: AgentEvent,
        *,
        rule_id: str,
        framework: str,
        severity: str,
        title: str,
        description: str,
        evidence: dict[str, Any],
    ) -> DetectionFinding:
        return DetectionFinding(
            rule_id=rule_id,
            framework=framework,
            severity=severity,
            title=title,
            description=description,
            event_index=event_index,
            event_time=event.timestamp.isoformat(),
            agent_id=event.agent_id,
            evidence=evidence,
        )

    @staticmethod
    def _extract_hostname(destination: str) -> str:
        parsed = urlparse(destination)
        if parsed.scheme and parsed.hostname:
            return parsed.hostname.lower()
        if "://" not in destination and "/" not in destination:
            return destination.lower()
        return ""

    def _has_injection_marker(self, payload: str) -> bool:
        lowered = payload.lower()
        return any(marker in lowered for marker in self._PROMPT_INJECTION_MARKERS)

    def _matches_high_risk_command(self, payload: str) -> bool:
        return any(pattern.search(payload) for pattern in self._HIGH_RISK_COMMAND_PATTERNS)


def parse_event(raw_event: dict[str, Any]) -> AgentEvent:
    """Parse event dictionaries while tolerating schema variation."""
    timestamp_value = raw_event.get("timestamp")
    if isinstance(timestamp_value, datetime):
        timestamp = timestamp_value
    elif isinstance(timestamp_value, str):
        timestamp = datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
    else:
        timestamp = datetime.now(timezone.utc)

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return AgentEvent(
        timestamp=timestamp,
        agent_id=str(raw_event.get("agent_id", "unknown-agent")),
        event_type=str(raw_event.get("event_type", "unknown")),
        payload=str(raw_event.get("payload", "")),
        target=raw_event.get("target"),
        metadata=dict(raw_event.get("metadata", {})),
    )


def run_security_scan(raw_events: list[dict[str, Any]], trusted_domains: Iterable[str] | None = None) -> dict[str, Any]:
    """High-level API used by patrol workflows."""
    detector = AgentBehaviorAnomalyDetector(trusted_domains=trusted_domains)
    events = [parse_event(event) for event in raw_events]
    report = detector.scan(events)
    return {
        "findings": [
            {
                "rule_id": finding.rule_id,
                "framework": finding.framework,
                "severity": finding.severity,
                "title": finding.title,
                "description": finding.description,
                "event_index": finding.event_index,
                "event_time": finding.event_time,
                "agent_id": finding.agent_id,
                "evidence": finding.evidence,
            }
            for finding in report.findings
        ],
        "summary": {
            "findings_by_severity": report.findings_by_severity,
            "frameworks_triggered": report.frameworks_triggered,
            "total_findings": len(report.findings),
        },
    }
