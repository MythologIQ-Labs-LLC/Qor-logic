# Plan: Phase 240 — Execution-Context Adaptive Governance

**change_class**: governance

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
9. Live skill-corpus metadata cleanup is deferred until the shared authority seam is proven; legacy model fields may remain physically present but have no execution-authority effect.

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
- conservative migration of existing legacy-pinned skills;
- deterministic recipe selection;
- complete/missing/unverified hard-requirement reporting;
- corpus scan and single-skill inspection.

Allowed recipes are exactly `conservative`, `outcome-first`, and `explicit-checklist`.

No model name appears in recipe-selection logic.

## Phase 2 — Legacy migration behavior

Do **not** mass-edit the skill corpus merely to delete existing model-pinning lines.

Instead:

- explicit execution-context frontmatter is authoritative when a skill adopts it;
- a skill that still carries legacy `model_compatibility` / `min_model_capability` metadata receives a conservative migration contract;
- the migration contract has no hard capability requirement derived from the old model tier;
- legacy model identity remains provenance only;
- a later corpus cleanup may remove the inert fields after this shared seam is proven.

This preserves historical readability while removing named-model authority at one deterministic owner.

## Phase 3 — Wire real consumers

### `/qor-plan`

Keep the existing Step 0.3 command name for compatibility. `model_pinning_lint` becomes a shim that:

- no longer emits authority warnings from model-family mismatch;
- surfaces the new execution-context scan;
- remains WARN-only;
- preserves the independent fabrication-risk guard.

A later prose cleanup may rename Step 0.3 after the implementation is proven; behavior changes now, wording cleanup does not need its own risk surface.

### `/qor-audit`

Wire execution-context inspection through `qor_audit_runtime.check_prior_artifact()`, the existing Step 0 runtime seam. The inspection:

- reports the selected rendering recipe;
- records declared and responder model identity separately;
- treats named model compatibility as non-authoritative;
- reports incomplete capability telemetry as `unverified`;
- blocks only when a future explicit execution contract has a hard requirement and the runtime declares a complete capability inventory proving that requirement absent.

## Phase 4 — Compatibility and safety

### `qor/scripts/model_pinning_lint.py`

Retain the module for backwards compatibility and fabrication-risk scanning.

- Legacy model pins are advisory provenance only.
- Unknown/new model families never become an execution denial.
- Existing `extract_capability_tier` and `_CAPABILITY_ORDER` exports remain for historical callers but are explicitly non-authoritative.
- Existing fabrication-risk doctrine pointer checks remain intact.

### Compiler safety

NR-001/NR-002 injection behavior is not changed in this slice. Its protection remains binding regardless of model identity. Renaming historical "weak-tier" prose is documentation cleanup, not a prerequisite for changing authority semantics.

## Phase 5 — Tests

Add focused tests proving:

1. unknown model families do not block inspection;
2. responder identity is distinct from declared model identity;
3. incomplete capability telemetry yields `unverified`, not `missing`;
4. complete telemetry with a real absent requirement yields `missing`;
5. a valid model/runtime rendering hint selects only an admitted recipe;
6. an unadmitted hint falls back deterministically;
7. reasoning mode may select `outcome-first` only when the skill admits it;
8. rendering recipes explicitly preserve semantic obligations;
9. legacy pinned skills receive a conservative non-authoritative migration contract;
10. non-Claude identity does not block `/qor-audit` entry;
11. `/qor-audit` blocks only a proven missing hard capability;
12. legacy model-pinning checks no longer warn on family mismatch;
13. fabrication-risk guards remain active;
14. full repository variant drift remains clean.

## Non-goals

- mass skill-frontmatter cleanup;
- empirical qualification database;
- automated vendor documentation ingestion;
- runtime benchmarking;
- per-model prompt templates;
- self-certifying model capabilities;
- changing Qor gate semantics;
- changing existing platform profiles in this slice.

## Definition of Done

- ADR and code agree on the invariant/adaptive boundary.
- Named-model metadata has no execution-authority effect in the shared runtime seam.
- `/qor-audit` can enter under a non-Claude declared model when no proven hard capability is missing.
- Execution-context behavior is deterministic and unit-tested.
- Qor truthfully distinguishes missing capability from unknown telemetry.
- Bounded rendering hints cannot change governance semantics.
- Negative constraints remain active independently of model identity.
- Full CI and variant drift pass on the Phase 240 branch.

## CI Commands

- `python -m pytest tests/test_execution_context.py tests/test_model_pinning_frontmatter.py tests/test_qor_audit_execution_context.py -q` — focused Phase 240 contract tests.
- `python -m pytest tests/ -q` — full repository regression suite.
- `python qor/scripts/check_variant_drift.py` — generated-host variant consistency.
- `python -m ruff check qor tests` — static lint over implementation and tests.
