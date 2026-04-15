---
name: qor-remediate
description: Process-level remediation for repeated failures, gate violations, and regression patterns. Absorbs qor-course-correct.
user-invocable: true
category: sdlc
requires: []
enhances_with:
  - codex-plugin: adversarial review of proposed remediation
  - agent-teams: parallel specialist consultation for cross-cutting fixes
gate_reads:
  - .qor/gates/<session_id>/substantiate.json (if present)
  - docs/PROCESS_SHADOW_GENOME.md
gate_writes: .qor/gates/<session_id>/remediate.json
phase: remediate
---
# /qor-remediate — Process Remediation

<skill>
  <trigger>/qor-remediate</trigger>
  <phase>REMEDIATE (post-substantiate or threshold-auto-triggered)</phase>
  <persona>Governor</persona>
  <output>Remediation proposal + shadow-process events addressed</output>
</skill>

## Purpose

Handle **process-level** failures distinct from code failures:

- Repeated gate overrides
- Threshold breach in Process Shadow Genome (severity sum ≥ 10)
- Regression pattern detected across multiple implement/substantiate cycles
- Capability shortfalls compounding (Codex absent, Agent Teams unavailable)

For **code-level** failures (runtime errors, test failures, broken behavior), use `/qor-debug` instead.

## Execution Protocol

### Step 1 — Read context

- Parse `docs/PROCESS_SHADOW_GENOME.md` (JSONL) filtering `addressed=false`.
- Identify pattern: cluster events by `event_type`, `skill`, `session_id`.
- Read latest substantiate gate artifact if present.

### Step 2 — Pattern match

Categorize the failure pattern:

- **Gate-loop**: repeated overrides on same gate (plan-audit, audit-implement). Root cause likely plan-quality or audit-calibration.
- **Regression**: implement-substantiate cycle producing worse state than prior cycle.
- **Hallucination**: unverified mechanism naming caught at substantiate.
- **Capability-shortfall aggregation**: ≥3 capability_shortfall events in one session.
- **Aged-high-severity**: sev ≥ 3 event unaddressed > 90 days (auto-escalated).

### Step 3 — Propose process change

Not a code change — a **skill / agent / gate / doctrine** change.

Examples:
- Add a grounding check to `qor-plan` Step 2b for a specific mechanism class
- Tighten `qor-audit` rubric to catch a specific violation class
- Add a reference file under a skill's `references/` capturing a recurring anti-pattern
- Escalate a severity level in the shadow rubric
- Retire a skill that consistently produces low-quality output

### Step 4 — Mark events addressed

For every event the proposal addresses, update `docs/PROCESS_SHADOW_GENOME.md`:
- `addressed: true`, `addressed_ts: <ISO-8601>`, `addressed_reason: "remediated by /qor-remediate session <id>"`.

### Step 5 — Emit remediate gate artifact

Write `.qor/gates/<session_id>/remediate.json` with the proposal for downstream audit.

## Constraints

- **NEVER** propose code changes — that is `/qor-debug`'s domain
- **NEVER** mark events addressed without a concrete remediation paired to each
- **ALWAYS** cite shadow events by `id` in the remediation proposal
- **ALWAYS** write the gate artifact; remediation that doesn't pass downstream audit is advisory-only until reviewed

## Status

**STUB (minimal)** — Full behavior deferred to `plan-qor-tooling-deferred.md`. This file exists so the skill registry is complete and the category structure is stable.
