# Plan: Phase 67 - plan_text_consistency_lint wiring + qor-audit unchanged-plan short-circuit

**change_class**: hotfix

**doc_tier**: standard

**originating_remediation**: GH #42 (Adopt plan_text_consistency_lint upstream + wire into qor-plan Step 5 + qor-audit Step 0.6) and GH #45 (qor-audit: detect unchanged-plan re-invocation; short-circuit instead of re-auditing identical content).

**terms_introduced**: none. Both fixes operate on existing surfaces (qor-plan / qor-audit / plan_text_consistency_lint already on main since Phase 55).

**boundaries**:
- limitations:
  - V1 wires the existing `qor/scripts/plan_text_consistency_lint.py` into qor-plan Step 5 + qor-audit Step 0.6 alongside existing pre-audit lints. No changes to the lint's detection logic.
  - V1 short-circuit uses content-hash comparison against the prior audit gate artifact's `target_content_hash` field. When prior artifact is absent, behavior unchanged.
- non_goals:
  - Replacing or extending the lint's detection rules (those live in a sibling consumer workspace's source script imported at Phase 55).
  - Cross-session short-circuit (V1 looks only at current session's audit.json).
- exclusions:
  - No changes to /qor-implement or /qor-substantiate gates.
  - No new CLI flags on `qor-logic` commands.

## Open Questions

None. Both issues specify exact wiring locations and expected behavior; this plan implements them.

## Phase 1: plan_text_consistency_lint wiring (GH #42)

### Affected Files

- `tests/test_plan_text_consistency_lint_audit_wiring.py` - NEW. 3 tests asserting qor-audit Step 0.6 invokes plan_text_consistency_lint alongside existing lints, and qor-plan Step 5 names the lint as a discipline-verification step.
- `qor/skills/governance/qor-audit/SKILL.md` - Step 0.6 gains a third lint invocation: the module `qor.scripts.plan_text_consistency_lint` with `--check` against the resolved plan path, alongside the existing two lint invocations and matching their WARN-only (trailing `|| true`) posture.
- `qor/skills/sdlc/qor-plan/SKILL.md` - Step 5 review checklist gains: "Plan asserts the same command, dependency, or filesystem path identically at every site where it appears" plus tooling instruction `python -m qor.scripts.plan_text_consistency_lint --check <plan-path>`.
- `qor/references/doctrine-shadow-genome-countermeasures.md` - new SG entry `SG-PlanTextDrift-A`: prose-boundary precision drift in plan markdown (same operation specified differently at multiple sites). Countermeasure: pre-audit lint at qor-plan Step 5 + qor-audit Step 0.6.

### Changes

Three surgical edits + one SG entry. The existing `plan_text_consistency_lint.py` script (sealed at Phase 55) is already callable; this phase wires it into the operator-visible audit + plan flow. Doctrine entry catalogs the cross-iteration recurrence pattern (3-VETO cycle in a sibling consumer workspace) for future operator reference.

### Unit Tests

- `tests/test_plan_text_consistency_lint_audit_wiring.py::test_qor_audit_step_0_6_invokes_plan_text_consistency_lint` - reads `qor/skills/governance/qor-audit/SKILL.md`, locates Step 0.6 body, asserts it contains `python -m qor.scripts.plan_text_consistency_lint` invocation alongside the existing plan_test_lint and plan_grep_lint calls.
- `tests/test_plan_text_consistency_lint_audit_wiring.py::test_qor_plan_step_5_names_consistency_lint_discipline` - reads `qor/skills/sdlc/qor-plan/SKILL.md`, locates Step 5 review checklist, asserts it includes both the discipline statement ("identically at every site") AND the tooling reference to `plan_text_consistency_lint`.
- `tests/test_plan_text_consistency_lint_audit_wiring.py::test_doctrine_sg_plan_text_drift_a_documented` - reads `qor/references/doctrine-shadow-genome-countermeasures.md`, asserts the `SG-PlanTextDrift-A` entry exists with the canonical pattern description (cites originating a sibling consumer workspace 3-VETO cycle).

## Phase 2: qor-audit unchanged-plan short-circuit (GH #45)

### Affected Files

- `tests/test_qor_audit_unchanged_plan_short_circuit.py` - NEW. 4 tests covering content-hash matching, divergent-content full-rerun, missing prior-audit gracefully proceeds, short-circuit verdict carries forward.
- `qor/scripts/qor_audit_runtime.py` - extend with `check_unchanged_plan_short_circuit(plan_path, session_id)` returning `(should_skip: bool, prior_verdict: str | None)`.
- `qor/skills/governance/qor-audit/SKILL.md` - Step 0 (Gate Check) gains a sub-step documenting the short-circuit behavior; references the new helper.
- `qor/gates/schema/audit.schema.json` - extend with optional `target_content_hash` field (Phase 45 schema already declared it per the issue body; verify presence and amend if absent).

### Changes

The new helper computes the SHA-256 of the current plan file, reads the prior audit gate artifact for the same session via `gate_chain.read_phase_artifact`, and returns whether the recorded `target_content_hash` matches. If yes, the skill prose instructs the operator to skip re-audit and return to `/qor-plan` for amendment.

Backward compatibility: prior audit artifacts without `target_content_hash` are treated as "no short-circuit available" (proceed with full audit). Future audits write the field on every gate artifact emission.

### Unit Tests

- `tests/test_qor_audit_unchanged_plan_short_circuit.py::test_short_circuit_when_plan_content_hash_matches_prior_audit` - constructs a fixture session with a prior audit.json containing `target_content_hash` matching the test plan's SHA-256; invokes `check_unchanged_plan_short_circuit`; asserts `should_skip=True` and the prior verdict is returned.
- `tests/test_qor_audit_unchanged_plan_short_circuit.py::test_no_short_circuit_when_plan_content_diverges` - constructs a session where prior audit's hash differs from current plan; asserts `should_skip=False`.
- `tests/test_qor_audit_unchanged_plan_short_circuit.py::test_no_short_circuit_when_no_prior_audit_exists` - empty session; asserts `should_skip=False` (graceful fallback).
- `tests/test_qor_audit_unchanged_plan_short_circuit.py::test_skill_prose_documents_short_circuit_behavior` - reads `qor/skills/governance/qor-audit/SKILL.md` Step 0 region; asserts it documents the unchanged-plan short-circuit path.

## CI Commands

- `python -m pytest tests/test_plan_text_consistency_lint_audit_wiring.py tests/test_qor_audit_unchanged_plan_short_circuit.py -v` - validates the new Phase 67 tests.
- `python -m qor.scripts.dist_compile` - regenerates dist variants (qor-audit + qor-plan SKILL.md changes propagate).
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase67-plan-lint-wiring-and-audit-short-circuit.md` - self-application: lint this plan with the newly-wired discipline.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` - full suite.
