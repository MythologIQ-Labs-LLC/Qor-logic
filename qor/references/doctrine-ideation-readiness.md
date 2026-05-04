# Ideation readiness phase (Phase 59)

Phase 59 introduces `/qor-ideate` as an optional pre-research SDLC phase. Closes Issue #20 (governed ideation readiness): converts a raw concept into a structured artifact before research and planning, capturing intent and assumptions before they become inferred. Codifies `SG-PrematureSolutioning-A` countermeasure.

## Applicability

Optional advisory-gate posture matching Phase 8: `/qor-research` and `/qor-plan` accept either ideation OR research as their prior artifact via `gate_chain.check_prior_artifact` extension. Hotfixes MAY skip ideation. The skill writes `.qor/gates/<sid>/ideation.json` validated against `qor/gates/schema/ideation.schema.json`.

## The 10 ideation artifact sections

The skill structures dialogue across 10 sections that map to schema fields:

### 1. Spark Record

`spark.observation` + `spark.initial_question` + `spark.why_now`. Captures the originating signal before it becomes over-compressed into requirements language. The `why_now` field guards against silently parking signals that become drift-inducing requirements months later.

### 2. Problem Frame

`problem_frame.affected_actors` + `problem_frame.failure_mode` + `problem_frame.cost_of_failure`. Defines the actual failure mode WITHOUT prescribing a solution. Skill REFUSES to advance to Section 3 until populated. This is the canonical anti-pattern guard for `SG-PrematureSolutioning-A`.

### 3. Transformation Statement

`transformation_statement` (single sentence). Form: "[Actor] moves from [current state] to [desired state] without [unacceptable cost]."

### 4. Assumption Ledger

`assumptions[]` (optional). Each entry: statement, category (user/market/technical/workflow/governance/operational/security/compliance), confidence (low/medium/high), impact_if_wrong, validation_method, blocking. Anti-pattern guard for assumption-laundering.

### 5. Scope Boundary Record

`boundaries.non_goals` + `boundaries.limitations` + `boundaries.exclusions` + optional `boundaries.forbidden_interpretations`. Anti-pattern guard for scope-seepage.

### 6. Concept Brief

`concept_name` (top-level). Synthesized from sections 1-5; operator confirms before advancing.

### 7. Options Matrix

`options[]`. Skill REFUSES to advance until ≥2 options recorded. Each: name, summary, selected (bool), rejection_reason (required when not selected). Anti-pattern guard for premature-decomposition.

### 8. Governance Profile

`governance_profile.risk_grade` (L1/L2/L3/L4) + `governance_profile.evidence_required[]` + optional `governance_profile.escalation_triggers[]`.

### 9. Failure Remediation Plan

`failure_remediation[]` (optional). Each: failure_class, detection_signal, containment_action, return_phase (ideation/research/plan/audit/implement/remediate/substantiate). Anti-pattern guard for failure-blindness.

### 10. Readiness Scoring + Routing

`readiness.status` + `readiness.recommended_next_phase` + optional `readiness.blocking_reasons[]`.

### Required envelope fields

In addition to the 10 sections, the gate artifact carries the standard envelope: `phase` (= `"ideation"`), `ts` (ISO-8601), `session_id`, `concept_name`, and `ai_provenance` (per Phase 54 doctrine; built via `qor.scripts.ai_provenance.build_manifest`).

## Readiness scoring model

The `readiness.status` enum encodes the routing decision:

| status | Meaning | Routing |
|---|---|---|
| `ready` | Concept is fully framed; safe to plan or research | Hand off per `recommended_next_phase` |
| `blocked` | Concept has hard blockers (missing actor, contradictory assumptions, etc.) | Remain in ideation; surface `blocking_reasons` |
| `research_required` | High-impact assumptions need validation | Route to `/qor-research` |
| `planning_advisory_only` | Allow prototype-level planning; block production implementation | Route to `/qor-plan` with advisory flag |

## Routing decision matrix

| status | recommended_next_phase | Hand off |
|---|---|---|
| `ready` | `research` | `/qor-research` |
| `ready` | `plan` | `/qor-plan` |
| `research_required` | `research` | `/qor-research` (overrides recommended_next_phase if mismatched) |
| `blocked` | `hold` | Remain in `/qor-ideate`; do not advance |
| `planning_advisory_only` | `plan` | `/qor-plan` with advisory flag |

## Failure-mode catalog (8 unraveling points)

Pre-Phase-59, ad-hoc ideation accumulated 8 canonical failure modes. The skill structurally guards against each:

### Premature Solutioning

The spark becomes a solution before the problem is fully understood. **Guard**: skill REFUSES to advance to Section 3 (Transformation) until Section 2 (Problem Frame) is populated. Codified as `SG-PrematureSolutioning-A`.

### Language Drift

Terms (governance, memory, runtime, evidence, audit, agent) mean different things across artifacts. **Guard**: glossary entries with `home:` field tied to ideation artifact's `terms_introduced` (carried forward to `/qor-plan` schema's `terms_introduced` per Phase 28).

### Assumption Laundering

A tentative belief becomes a requirement without new evidence. **Guard**: assumption ledger structure forces explicit confidence + validation_method per assumption.

### Scope Seepage

A focused concept expands into a platform, framework, runtime, agent system, and doctrine all at once. **Guard**: scope boundary record (non_goals + limitations + exclusions + forbidden_interpretations) blocks expansion unless explicitly justified.

### Research Asymmetry

Technical research is completed but user/workflow/governance/risk research isn't. **Guard**: Section 4 assumption category enum (user, market, technical, workflow, governance, operational, security, compliance) forces breadth-of-domain coverage.

### Failure Blindness

The plan assumes success and treats failure recovery as an implementation detail. **Guard**: failure_remediation[] structure forces operator to pre-decide failure-class → return_phase mapping.

### Premature Decomposition

The concept is split into implementation tasks before system-level intent is stable. **Guard**: skill REFUSES to advance to Section 8 until ≥2 options compared.

### Validation Collapse

Success becomes defined as code-existing, tests-passing, plan-completed. **Guard**: transformation_statement (Section 3) is the success definition; downstream verification refers back to it.

## Hotfix exemption

`change_class: hotfix` plans MAY skip `/qor-ideate`. Operator declares this in the plan frontmatter (existing `change_class:` field per `qor/gates/schema/plan.schema.json`); no schema change required. Future phase may add an explicit `ideation_skipped: true` flag for audit traceability.

## Relationship to qor-research and qor-plan

### `/qor-research`

Continues to be responsible for grounding external facts, APIs, source-code interfaces, dependencies, and verified findings. `/qor-ideate` identifies WHAT research is needed (via assumption ledger validation_method); `/qor-research` performs the verification.

### `/qor-plan`

Continues to be responsible for creating implementation plans. `/qor-ideate` ensures the concept is stable enough to plan (readiness.status = ready). The plan inherits `concept_name`, `boundaries`, and `governance_profile.risk_grade` from the ideation artifact when present.

### `/qor-remediate`

Future phase will extend `qor-remediate` to consume ideation artifacts when repeated failures suggest the original concept was malformed. Phase 59 v1: out of scope.

## Phase 59 changes vs. ad-hoc operator review

Pre-Phase-59, ideation was implicit. Operators wrote plans directly from a hunch; assumptions, problem frames, and failure remediation routes were either inferred at plan time or omitted entirely. The 8 unraveling points above were caught only on adversarial audit (`/qor-audit` Section-4 Razor + Test Functionality + Macro-Architecture passes), often requiring a re-plan cycle.

Phase 59 surfaces intent at the structural level. The procedural-fidelity check from Phase 58 (`SG-DocSurfaceUncovered-A`) and the prompt-injection canary from Phase 53 (`SG-PromptInjection-A`) are runtime governance enforcement; this doctrine adds front-of-chain governance enforcement.

## References

- `qor/skills/sdlc/qor-ideate/SKILL.md` — skill body.
- `qor/skills/sdlc/qor-ideate/references/dialogue-protocol.md` — section-by-section operator prompts.
- `qor/gates/schema/ideation.schema.json` — gate artifact schema.
- `qor/scripts/gate_chain.py:_check_ideation_predecessor` — predecessor recognition extension.
- `qor/references/doctrine-shadow-genome-countermeasures.md` `SG-PrematureSolutioning-A` — codified failure pattern.
- Issue #20 — operator request that prompted this phase.
- META_LEDGER Entry #188 — Phase 58-slot audit PASS (substantively the same content).
