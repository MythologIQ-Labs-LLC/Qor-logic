# Plan: Phase 240 — Execution-Context Adaptive Governance

**change_class**: governance-feature

**doc_tier**: system

**originating_issue**: GH #379

**adr**: `docs/ADR_EXECUTION_CONTEXT_ADAPTIVE_GOVERNANCE.md`

## Locked Decisions

1. Governance semantics remain invariant across models and hosts.
2. Model identity is provenance/evaluation evidence, not execution authority.
3. Runtime adaptation is keyed by execution context and an allowlisted rendering recipe.
4. Model self-preference may choose only among recipes the skill already admits.
5. Unknown model identity falls back conservatively rather than blocking execution.
6. Hard capability requirements only become mechanically missing when the runtime explicitly declares its capability inventory complete.
7. Legacy model pinning remains a compatibility/deprecation surface; fabrication-risk guards remain binding and independent.
8. Phase 240 creates no model registry, empirical learner, benchmark service, or remote dependency.

## Phase 1 — Execution-context seam

### New file

- `qor/scripts/execution_context.py`

### Behavior

Provide deterministic library + CLI behavior for:

- host detection through existing `qor_platform` state;
- declared model from `QOR_MODEL_FAMILY`;
- optional actual responder from `QOR_RESPONDER_MODEL_FAMILY`;
- reasoning mode from `QOR_REASONING_MODE`;
- explicit runtime capabilities from `QOR_EXECUTION_CAPABILITIES`;
- completeness signal from `QOR_EXECUTION_CAPABILITIES_COMPLETE`;
- bounded rendering hint from `QOR_RENDERING_HINT`;
- skill contract parsing from YAML frontmatter;
- deterministic recipe selection;
- complete/missing/unverified hard-requirement reporting;
- corpus scan and single-skill inspection.

Allowed recipes are exactly `conservative`, `outcome-first`, and `explicit-checklist`.

No model name appears in recipe-selection logic.

## Phase 2 — Migrate live model-pinned skills

Replace live `model_compatibility` / `min_model_capability` frontmatter on every currently pinned skill, including `/qor-ideate`, with:

- `hard_execution_requirements`;
- `advisory_quality_requirements`;
- `rendering_recipes`;
- `default_rendering_recipe`.

Use capability requirements that reflect the skill's existing permitted tool surface without claiming host enforcement Qor cannot observe.

Risk/governance skills default to `conservative`; planning/ideation/research may admit `outcome-first`; all scoped skills may admit `explicit-checklist` where it changes presentation only.

## Phase 3 — Wire real consumers

### `/qor-plan`

Replace Step 0.3 model-pinning lint with execution-context scan. The scan is advisory at planning time and reports unknown/unverified context rather than inventing a capability verdict.

### `/qor-audit`

Add execution-context inspection before substantive audit passes. The inspection:

- records the selected rendering recipe;
- explicitly states that the recipe may not alter PASS/VETO/ABORT, authority, or evidence requirements;
- treats named model compatibility as non-authoritative;
- may ABORT only when a runtime has declared a complete capability inventory and an admitted hard requirement is actually absent.

## Phase 4 — Compatibility and safety cleanup

### `qor/scripts/model_pinning_lint.py`

Retain the module for backwards compatibility and fabrication-risk scanning.

- Legacy model pins become deprecation warnings only.
- Unknown/new model families never become an execution denial.
- Existing fabrication-risk doctrine pointer checks remain intact.

### `qor/scripts/dist_compile.py`

Preserve NR-001/NR-002 injection for the existing cross-host variants but remove the stale claim that injection represents a lower model tier. Safety protections remain model-invariant.

## Phase 5 — Tests

Add focused tests proving:

1. unknown model families do not block inspection;
2. responder identity is distinct from declared model identity;
3. incomplete capability telemetry yields `unverified`, not `missing`;
4. complete telemetry with a real absent requirement yields `missing`;
5. a valid model/runtime rendering hint selects only an admitted recipe;
6. an unadmitted hint falls back deterministically;
7. reasoning mode may select `outcome-first` only when the skill admits it;
8. no recipe contains permission to alter semantic obligations;
9. all live formerly pinned skills declare execution-context metadata and no longer carry named-model authority fields;
10. `/qor-plan` invokes execution-context scan;
11. `/qor-audit` invokes execution-context inspection;
12. legacy model-pinning consumers still return WARN-only and fabrication-risk guards remain active;
13. variant compilation still injects NR-001/NR-002 in the same host variants;
14. full repository variant drift remains clean.

## Non-goals

- empirical qualification database;
- automated vendor documentation ingestion;
- runtime benchmarking;
- per-model prompt templates;
- self-certifying model capabilities;
- changing Qor gate semantics;
- changing existing platform profiles in this slice.

## Definition of Done

- ADR and code agree on the invariant/adaptive boundary.
- No live skill depends on a vendor model name for execution authority.
- Execution-context behavior is deterministic and fully unit-tested.
- Qor can truthfully distinguish missing capability from unknown telemetry.
- Bounded rendering hints cannot change governance semantics.
- Negative constraints remain active independently of model identity.
- Full CI and variant drift pass on the Phase 240 branch.
