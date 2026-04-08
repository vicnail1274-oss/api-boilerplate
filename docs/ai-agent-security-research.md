# AI Agent Security Research: Snort / Sigma / YARA

## Scope

This document summarizes how Snort, Sigma, and YARA style detections can be adapted for AI Agent behavior monitoring.

## Why all three are useful together

- **Snort-style** detections are strong for network and protocol-level indicators (for example suspicious outbound destinations or C2-like traffic patterns).
- **Sigma-style** detections are strong for log-event correlations (for example a prompt-injection signal followed by dangerous command execution).
- **YARA-style** detections are strong for content signatures (for example token patterns that indicate prompt injection, secrets exfiltration intent, or malware-like payloads).

Combining the three helps detect both isolated indicators and multi-step attack chains.

## AI Agent scenario mapping

| AI Agent Risk Scenario | Snort-style | Sigma-style | YARA-style |
|---|---|---|---|
| Tool abuse / command execution escalation | N/A (mostly host/log signal) | Sequence: privilege request -> shell execution | Pattern match on risky shell command templates |
| Prompt injection leading to policy bypass | N/A | Sequence: injection marker -> restricted action | Pattern match on "ignore previous instructions", "reveal secrets", "bypass policy" |
| Exfiltration via outbound requests | Destination/domain/IP anomaly, unusual protocol | Sequence: sensitive read -> outbound request | Payload signatures for secret-like material (tokens, key blocks) |
| Autonomous lateral movement behavior | Internal scanning traffic patterns | Sequence: discovery commands -> credential access -> remote action | Pattern fragments that indicate reconnaissance command bundles |

## Practical detection design for this repo

1. **Snort-inspired rules**
   - Flag outbound requests to domains outside the trusted allow-list.
   - Flag direct-IP destinations and known suspicious tunneling or paste domains.

2. **Sigma-inspired rules**
   - Correlate events over time windows.
   - Example: `prompt_injection_detected` followed by `command_execute` with high-risk payload within 5 minutes.

3. **YARA-inspired rules**
   - Signature-based matching over command/prompt payload strings.
   - Match common injection phrases and high-risk shell patterns.

## Non-breaking integration plan

- Keep implementation in standalone Python modules:
  - `security_scan_logic_script.py`
  - `system_guardian.py`
- Do not change existing Node/TypeScript runtime paths.
- Expose pure functions/classes so integration is additive and opt-in.

## Limitations and next hardening steps

- Signature-based detections can generate false positives without environment tuning.
- Domain allow-lists should be environment-specific.
- Correlation windows and thresholds should be calibrated with real workload telemetry.
- For production, add signed rule packs and immutable audit logging for detection outputs.
