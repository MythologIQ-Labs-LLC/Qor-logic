# /qor-ideate dialogue protocol

Operator-facing prompts for each of the 10 ideation-artifact sections. The skill body invokes these prompts; the operator authors the responses. Phase 59 v1: operator-driven prose; LLM-assisted authoring is out of scope.

## Section 1 — Spark Record

**Prompt operator with**:
1. "What sparked this concept? Describe the originating observation, friction, or pattern in 1-3 sentences."
2. "What initial question did this raise that you couldn't immediately answer?"
3. "Why now? What recurrence, deadline, or strategic charge makes this signal worth preserving today rather than parking it?"

Required fields: `spark.observation`, `spark.initial_question`, `spark.why_now`.

## Section 2 — Problem Frame

**Prompt operator with** (multi-step):
1. "Who or what is affected? List actors (operators, end users, integrators, downstream systems, etc.)."
2. "What is the failure mode? Describe what happens when the problem manifests, WITHOUT prescribing a fix."
3. "What is the cost of leaving this unsolved? Quantify if possible (operator hours/incident, lost session work, etc.)."

Required fields: `problem_frame.affected_actors`, `problem_frame.failure_mode`, `problem_frame.cost_of_failure`.

**Anti-pattern guard**: skill REFUSES to advance to Section 4 until problem_frame is fully populated. Premature solutioning is the canonical failure pattern (`SG-PrematureSolutioning-A`).

## Section 3 — Transformation Statement

**Prompt operator with**:
"Phrase the desired change as: `[Actor] moves from [current state] to [desired state] without [unacceptable cost or failure mode]`. Single sentence."

Required field: `transformation_statement` (string, ≥10 chars).

## Section 4 — Assumption Ledger (optional, encouraged)

**For each assumption**, operator authors:
- statement (text)
- category — multiple-choice: user / market / technical / workflow / governance / operational / security / compliance
- confidence — multiple-choice: low / medium / high
- impact_if_wrong — multiple-choice: low / medium / high
- validation_method (text — how operator would test this assumption)
- blocking (bool — does this block downstream progression?)

**Anti-pattern guard**: assumption_laundering — tentative belief becomes requirement without evidence. The ledger forces explicit confidence + validation_method.

## Section 5 — Scope Boundary Record

**Prompt operator with**:
1. "What is this concept NOT? List non-goals."
2. "What limitations apply? (read-only access, no breaking-change tolerance, etc.)"
3. "What is explicitly excluded from scope? (out-of-band features, related-but-separate concerns)"
4. "Are there forbidden interpretations? (semantic drift the team must guard against)"

Required: `boundaries.non_goals[]`, `boundaries.limitations[]`, `boundaries.exclusions[]`. Optional: `boundaries.forbidden_interpretations[]`.

## Section 6 — Concept Brief (synthesized)

The skill synthesizes from sections 1–5 into a brief shown for operator confirmation. No new fields beyond `concept_name` (top-level required string).

## Section 7 — Options Matrix

**Anti-pattern guard**: skill REFUSES to advance to Section 8 until ≥2 options are recorded. Operator must compare alternatives.

**For each option**, operator authors:
- name (short identifier)
- summary (1-2 sentences)
- selected (bool — is this the chosen approach?)
- rejection_reason (text — required when selected=false)

## Section 8 — Governance Profile

**Prompt operator with** (multiple-choice where possible):
1. "Risk grade? L1 (no production traffic) / L2 (operator-visible behavior change) / L3 (security-relevant or production-traffic) / L4 (system-wide architectural shift)."
2. "What evidence will be required at audit time? (list)"
3. "What triggers should escalate this concept? (list — e.g., 3rd recurrence, contradiction with existing doctrine)"

Required: `governance_profile.risk_grade`, `governance_profile.evidence_required[]`. Optional: `governance_profile.escalation_triggers[]`.

## Section 9 — Failure Remediation Plan

**For each anticipated failure class**, operator authors:
- failure_class (text)
- detection_signal (text — how would you know it's happening?)
- containment_action (text — what stops bleeding?)
- return_phase — multiple-choice: ideation / research / plan / audit / implement / remediate / substantiate

**Anti-pattern guard**: failure_blindness. Plans that assume success and treat failure as an implementation detail are the most expensive class. Capturing return_phase forces operator to pre-decide where each failure class re-enters the SDLC chain.

## Section 10 — Readiness Scoring + Routing

**Prompt operator with**:
1. "Readiness status? Multiple-choice: ready / blocked / research_required / planning_advisory_only."
2. "If blocked: list blocking_reasons."
3. "Recommended next phase? Multiple-choice: research / plan / hold."

Required: `readiness.status`, `readiness.recommended_next_phase`.

**Routing decision matrix**:

| status | recommended_next_phase | Skill behavior |
|---|---|---|
| `ready` | `research` | Hand off to `/qor-research` |
| `ready` | `plan` | Hand off to `/qor-plan` |
| `research_required` | `research` | Hand off to `/qor-research` (overrides if mismatched) |
| `blocked` | `hold` | Remain in ideation; surface `blocking_reasons` |
| `planning_advisory_only` | `plan` | Hand off to `/qor-plan` with advisory flag in plan-gate payload |
