# Plan: Phase 73 - Feature Inventory artifact + per-feature TDD (doctrine + skill prose V1)

**change_class**: feature

**doc_tier**: standard

**originating_remediation**: GH #40 (FEATURE_INDEX seal-time gate) + GH #41 (plan/audit/implement upstream gates).

**terms_introduced**:
- term: Feature Inventory
  home: qor/references/doctrine-feature-inventory.md
- term: Feature Inventory Touches
  home: qor/references/doctrine-feature-tdd.md
- term: per-feature TDD
  home: qor/references/doctrine-feature-tdd.md
- term: feature-test-undeclared
  home: qor/references/doctrine-feature-tdd.md

**boundaries**:
- limitations:
  - V1 ships doctrine + skill prose + plan schema field. Operator-discipline enforcement only; no runtime parser/verifier in this phase.
  - Schema field is OPTIONAL (`feature_inventory_touches` may be absent for plans that touch only docs/governance). The required-when-touching-src/ enforcement lives in operator discipline + qor-plan prose; mechanical enforcement deferred.
  - The FEATURE_INDEX.md format is described in doctrine prose; no JSON-schema mirror this phase.
- non_goals:
  - No runtime helper `qor/scripts/feature_inventory.py` (defer to follow-on phase).
  - No worked-example FEATURE_INDEX.md (consumer projects will author their own; doctrine documents the format).
  - No /qor-substantiate Step 6 regression-blocking helper (Step 6 gains prose surface only; ABORT semantics deferred until runtime helper exists).
- exclusions:
  - No changes to `/qor-debug`, `/qor-refactor`, `/qor-remediate`.
  - No new CI workflows.

## Open Questions

None. Issues #40 + #41 specify the lifecycle hooks in detail; V1 lands the doctrine + prose surface; V2 phases will wire the runtime helper, FEATURE_INDEX.md schema, and ABORT-on-regression semantics.

## Phase 1: Doctrines (P1 + P2)

### Affected Files

- `qor/references/doctrine-feature-inventory.md` - NEW. Documents the FEATURE_INDEX.md artifact format, lifecycle hooks (qor-implement + qor-substantiate), and seal-time regression semantics (prose; ABORT-helper deferred to V2).
- `qor/references/doctrine-feature-tdd.md` - NEW. Documents per-unit vs per-feature TDD layering, acceptance question for feature-level tests ("If the feature were silently broken but the test artifact still existed, would this assertion fail?"), and the three upstream gates (qor-plan declaration / qor-audit Feature Test Coverage Pass / qor-implement Step 5 expansion).
- `tests/test_doctrine_feature_inventory.py` - NEW. 2 tests asserting doctrine contents.
- `tests/test_doctrine_feature_tdd.py` - NEW. 2 tests asserting doctrine contents.

### Changes

Doctrine 1 (`doctrine-feature-inventory.md`) covers:
- The FEATURE_INDEX.md artifact (one row per feature; columns `ID | Name | Source file:line | Doc citation | Test path | Verification status`).
- Status enum: `verified` / `unverified` / `n/a` (with operator-justified rationale for `n/a`).
- Section grouping by surface category (commands, routes, UI surfaces, services, etc.).
- Lifecycle hooks: `/qor-implement` Step 12.5 appends/updates entries; `/qor-substantiate` Step 6 verifies + surfaces counts in seal entry.
- Append-only vs mutable: V1 documents append-only-with-deprecation-markers as the recommended convention (Merkle-friendly).
- Originating incident: a sibling product's v5 2026-05-06 sealed-but-not-verified Phase 1 monitor surface; 264 features eventually backfilled across 80+ test files.

Doctrine 2 (`doctrine-feature-tdd.md`) covers:
- Definition: per-unit TDD (existing TDD-Light contract) vs per-feature TDD (new contract).
- Acceptance question for feature tests: "If the feature were silently broken but the test artifact still existed, would this assertion fail?" -- inherits SG-035 form.
- Three upstream gates (Gate 1: /qor-plan `Feature Inventory Touches` declaration; Gate 2: /qor-audit Feature Test Coverage Pass; Gate 3: /qor-implement Step 5 per-feature failing-test-first).
- VETO category: `feature-test-undeclared` (consumed by `/qor-audit`).
- Why all three gates are needed (without any single one the regression class survives).
- Cross-reference to `doctrine-feature-inventory.md`.

### Unit Tests

- `tests/test_doctrine_feature_inventory.py::test_documents_index_columns` - reads doctrine, asserts the six index columns (`ID`, `Name`, `Source`, `Doc citation`, `Test path`, `Verification status`) are named with proximity to the artifact heading.
- `tests/test_doctrine_feature_inventory.py::test_documents_lifecycle_hooks` - asserts both `/qor-implement` Step 12.5 and `/qor-substantiate` Step 6 lifecycle hooks are named with append/verify semantics.
- `tests/test_doctrine_feature_tdd.py::test_documents_three_upstream_gates` - asserts the doctrine names all three gates (plan / audit / implement) with their respective enforcement points.
- `tests/test_doctrine_feature_tdd.py::test_documents_acceptance_question` - asserts the acceptance question form ("If the feature were silently broken... would this assertion fail?") matches SG-035 inheritance.

## Phase 2: Plan schema field (P1 partial)

### Affected Files

- `qor/gates/schema/plan.schema.json` - extend with optional `feature_inventory_touches` array field. Items have `entry_id`, `operation` (enum: `NEW` / `MODIFIED` / `n/a-justified`), `test_path`, `test_descriptor`.
- `tests/test_plan_schema_feature_inventory_touches.py` - NEW. 3 tests: optional field present + well-formed; operation enum rejects invalid values; field absent is acceptable.

### Changes

Schema gains the optional field. No `if-then` required-when-touching-src/ rule yet (would require static analysis at validation time; defer to V2 runtime helper).

### Unit Tests

- `tests/test_plan_schema_feature_inventory_touches.py::test_optional_field_validates` - synthetic plan with valid `feature_inventory_touches` passes schema validation.
- `tests/test_plan_schema_feature_inventory_touches.py::test_operation_enum_rejects_invalid` - synthetic plan with `operation: "FROBNICATE"` fails schema validation with message naming the enum.
- `tests/test_plan_schema_feature_inventory_touches.py::test_field_absent_is_valid` - existing-style plan without the field still passes schema validation.

## Phase 3: SKILL prose updates (P3 + P4 + P5 + P6)

### Affected Files

- `qor/skills/sdlc/qor-plan/SKILL.md` - extend Step 5 (Plan Output) with `Feature Inventory Touches` declaration requirement; reference doctrine-feature-tdd.md.
- `qor/skills/governance/qor-audit/SKILL.md` - add Feature Test Coverage Pass under Step 3 (between Test Functionality Pass and Infrastructure Alignment Pass) with VETO category `feature-test-undeclared`.
- `qor/skills/sdlc/qor-implement/SKILL.md` - extend Step 5 (TDD-Light) with per-feature scope expansion; Step 12.5 (Reality vs Blueprint) names FEATURE_INDEX.md update obligation.
- `qor/skills/governance/qor-substantiate/SKILL.md` - extend Step 6 (Sync System State) with FEATURE_INDEX verification pass + ledger surface (counts of verified/unverified/n/a; list newly unverified entries; ABORT-helper deferred to V2).
- `qor/gates/schema/audit.schema.json` - extend `findings_categories` enum with `feature-test-undeclared` (so audit gate artifacts can record the new category).
- `tests/test_qor_plan_feature_inventory_touches_prose.py` - NEW. 2 tests asserting plan SKILL.md prose surface.
- `tests/test_qor_audit_feature_test_coverage_pass_prose.py` - NEW. 2 tests asserting audit SKILL.md prose surface (pass name + VETO category).
- `tests/test_qor_implement_per_feature_tdd_prose.py` - NEW. 2 tests asserting implement SKILL.md prose surface (Step 5 expansion + Step 12.5 FEATURE_INDEX obligation).
- `tests/test_qor_substantiate_feature_inventory_prose.py` - NEW. 2 tests asserting substantiate SKILL.md prose surface (Step 6 verification + ledger surface).

### Changes

Each SKILL.md gains a "Phase 73 wiring" sub-section in the appropriate Step. Prose-only; no executable code blocks reference V2-deferred runtime helper.

### Unit Tests

- `tests/test_qor_plan_feature_inventory_touches_prose.py::test_step_5_names_feature_inventory_touches` - asserts qor-plan Step 5 region names the section header.
- `tests/test_qor_plan_feature_inventory_touches_prose.py::test_step_5_links_doctrine_feature_tdd` - asserts the region cites `doctrine-feature-tdd.md`.
- `tests/test_qor_audit_feature_test_coverage_pass_prose.py::test_step_3_names_feature_test_coverage_pass` - asserts Step 3 region names "Feature Test Coverage Pass".
- `tests/test_qor_audit_feature_test_coverage_pass_prose.py::test_step_3_ties_veto_to_feature_test_undeclared` - asserts the VETO category `feature-test-undeclared` appears with VETO context.
- `tests/test_qor_implement_per_feature_tdd_prose.py::test_step_5_expands_to_per_feature_scope` - asserts Step 5 prose names per-feature failing-test-first scope.
- `tests/test_qor_implement_per_feature_tdd_prose.py::test_step_12_5_names_feature_index_update_obligation` - asserts Step 12.5 names FEATURE_INDEX update obligation.
- `tests/test_qor_substantiate_feature_inventory_prose.py::test_step_6_verification_pass` - asserts Step 6 names FEATURE_INDEX verification pass.
- `tests/test_qor_substantiate_feature_inventory_prose.py::test_step_6_names_ledger_counts_surface` - asserts ledger seal entry counts surface (`Total / verified / unverified / n/a`).

## CI Commands

- `python -m pytest tests/test_doctrine_feature_inventory.py tests/test_doctrine_feature_tdd.py tests/test_plan_schema_feature_inventory_touches.py tests/test_qor_plan_feature_inventory_touches_prose.py tests/test_qor_audit_feature_test_coverage_pass_prose.py tests/test_qor_implement_per_feature_tdd_prose.py tests/test_qor_substantiate_feature_inventory_prose.py -v` - validates Phase 73 tests.
- `python -m qor.scripts.dist_compile` - regenerates dist variants.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase73-feature-inventory-tdd.md` - self-application.
- `python -m pytest --deselect tests/test_changelog_tag_coverage.py` - full suite.
