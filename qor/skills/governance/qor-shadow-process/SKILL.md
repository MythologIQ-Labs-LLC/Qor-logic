---
name: qor-shadow-process
description: Append-only process failure log; threshold-triggered GitHub issue creation; cross-repo aggregation.
user-invocable: true
category: governance
requires: []
enhances_with: []
gate_reads: []
gate_writes: docs/PROCESS_SHADOW_GENOME.md (append-only)
---

# /qor-shadow-process — Process Shadow Genome Recorder

<skill>
  <trigger>/qor-shadow-process</trigger>
  <phase>GOVERNANCE (cross-cutting; invoked by other skills and auto-triggers)</phase>
  <persona>Judge</persona>
  <output>Appended event in docs/PROCESS_SHADOW_GENOME.md (JSONL)</output>
</skill>

## Purpose

Record **process-level** failures (distinct from `docs/SHADOW_GENOME.md` which records **audit-verdict** failures). Analogous to the Shadow Genome concept but at the meta-process layer — failures of how we work, not failures in the artifact itself.

Events flow into a threshold-gated GitHub issue pipeline (see `qor/scripts/check_shadow_threshold.py` and `create_shadow_issue.py` — deferred).

## Event Schema

```json
{
  "ts": "ISO-8601 UTC",
  "skill": "qor-<name>",
  "session_id": "<UTC-ISO-MIN>-<6hex>",
  "event_type": "gate_override | regression | hallucination | degradation | capability_shortfall | aged_high_severity_unremediated",
  "severity": 1-5,
  "details": {},
  "addressed": false,
  "issue_url": null,
  "addressed_ts": null,
  "addressed_reason": null,
  "source_entry_id": null
}
```

**Severity rubric**: gate_override=1, capability_shortfall=2, regression=3, hallucination=4, degradation=5.

**`addressed` state machine**:
- `false → true (issue_created)` — any severity; threshold trips (sum ≥ 10)
- `false → true (resolved_without_issue)` — any severity; operator action via `/qor-remediate`
- `false → true (stale_expired)` — severity 1–2 only; 90 days unaddressed
- Severity ≥ 3 never stale-expires
- Reverse transitions forbidden (re-opening requires a new event)

## Execution Protocol (record-only, minimal)

1. Accept event payload matching schema.
2. Validate severity, event_type, timestamp.
3. Append as single-line JSON to `docs/PROCESS_SHADOW_GENOME.md`.
4. Atomic write via `os.replace()` (Windows-safe).
5. Return event id (SHA256 of first 7 fields).

## Constraints

- **NEVER** modify existing events (append-only)
- **NEVER** delete events (use addressed=true to close)
- **ALWAYS** use atomic write primitive (`os.replace`)
- **ALWAYS** validate schema before append

## Status

**STUB (minimal)** — threshold automation, issue creation, cross-repo aggregation, self-escalation idempotence all deferred to `plan-qor-tooling-deferred.md`. This file exists so the skill registry is complete and gate_override events have a named recorder.
