# Plan: Phase 71 - qor-implement Step 8.5 Documentation Sync

**change_class**: hotfix

**doc_tier**: standard

**originating_remediation**: GH #52 (qor-implement: no documentation update step -- documentation lifecycle backloaded to substantiation).

**terms_introduced**: none. Builds on existing `doc_tier` machinery from Phase 28.

**boundaries**:
- limitations:
  - V1 adds the operator-facing checklist + doc_tier-conditional guidance. The lift is operator-discipline, not automated detection. Phase 64's procedural-fidelity check at substantiate Step 4.6.6 remains the post-hoc verification.
  - The checklist is doc-surface-specific (file tree, architecture, operations, schema); other doc surfaces (CHANGELOG, README, policies) remain owned by `/qor-substantiate` Steps 6.5 + 7.6.
- non_goals:
  - Automated doc-update detection (the operator reads their diff and updates).
  - Replacing substantiate Step 4.6.6 procedural-fidelity check (which catches gaps post-hoc).
- exclusions:
  - No changes to qor-substantiate skill prose.
  - No new CLI tooling.

## Open Questions

None. Issue #52 specifies the exact placement (between Step 8 and Step 9) and checklist contents.

## Phase 1: qor-implement Step 8.5 prose + doctrine cross-reference

### Affected Files

- `tests/test_qor_implement_step_8_5_documentation_sync.py` - NEW. 4 tests asserting Step 8.5 exists, names the 4 documentation surfaces, declares doc_tier-conditional semantics, and references the substantiate verification gates.
- `qor/skills/sdlc/qor-implement/SKILL.md` - new Step 8.5 between Step 8 (Post-Build Cleanup) and Step 9 (Complexity Self-Check). Per Issue #52 spec.
- `qor/references/doctrine-documentation-integrity.md` - add an "Implement-time authoring" subsection cross-referencing the new Step 8.5 + the substantiate-time verification gates (Steps 4.7, 6, 6.5, 4.6.6).

### Changes

Step 8.5 prose follows Issue #52's proposed text verbatim plus minor wiring to match the surrounding skill's style. The checklist enumerates four documentation surfaces operators reassess against the implement diff:

1. `ARCHITECTURE_PLAN.md` file tree — add new files, remove deleted files.
2. Architecture docs (`docs/architecture.md` + schema docs) — update interface contracts, data flows, dependency tables for new tables/functions/env vars/cron jobs.
3. Operations docs (`docs/operations.md`) — document new scripts, env vars, deployment steps.
4. Schema docs — document new migrations, RLS policies, function signatures.

doc_tier semantics:
- `minimal`: skip with WARN (matches existing minimal-tier semantics).
- `standard` / `system`: at least the file tree + relevant architecture doc section get updated.
- `legacy`: bypass (matches existing legacy escape hatch).

Doctrine subsection in `doctrine-documentation-integrity.md` documents the implement-time authoring discipline: the implementing agent has fullest context for accurate doc updates; substantiate verifies but should not be the primary authoring phase.

### Unit Tests

- `tests/test_qor_implement_step_8_5_documentation_sync.py::test_step_8_5_documentation_sync_exists` - reads `qor/skills/sdlc/qor-implement/SKILL.md`, locates `### Step 8.5: Documentation Sync` heading, asserts the section body is non-empty.
- `tests/test_qor_implement_step_8_5_documentation_sync.py::test_step_8_5_names_four_doc_surfaces` - asserts the section body names all four documentation surfaces (`ARCHITECTURE_PLAN`, `architecture`, `operations`, `schema`).
- `tests/test_qor_implement_step_8_5_documentation_sync.py::test_step_8_5_doc_tier_conditional_semantics` - asserts the section body references `doc_tier` and distinguishes `minimal` (WARN-skip) from `standard`/`system` (required updates).
- `tests/test_qor_implement_step_8_5_documentation_sync.py::test_step_8_5_precedes_step_9_complexity_self_check` - asserts byte offset of `### Step 8.5:` precedes `### Step 9:` byte offset (placement correctness per Issue #52 spec).

## CI Commands

- `python -m pytest tests/test_qor_implement_step_8_5_documentation_sync.py -v` - validates Phase 71 tests.
- `python -m qor.scripts.dist_compile` - regenerates dist variants for qor-implement prose change.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase71-qor-implement-step-8-5-documentation-sync.md` - self-application with Phase 67's wired discipline.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` - full suite.
