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
7. Live executable skill metadata must not grant or imply authority through a named model, model allowlist, or vendor capability tier; fabrication-risk guards remain binding and independent.
8. Phase 240 creates no model registry, empirical learner, benchmark service, or remote dependency.
9. Historical research, changelog, and ADR material may describe former model-pinning behavior as provenance. Active skill contracts and runtime admission logic may not retain it as an operative or ambiguous control surface.

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

No model name appears in recipe-selection or admission logic.

## Phase 2 — Live skill migration

Remove named-model admission metadata from the live executable skill corpus in this phase.

Required migration:

- remove `model_compatibility` from active `qor/skills/**/SKILL.md` frontmatter;
- remove `min_model_capability` from active `qor/skills/**/SKILL.md` frontmatter;
- replace any model-specific eligibility wording in active skill descriptions with execution-context/capability language;
- do not derive hard capability requirements from former model tiers;
- preserve historical discussion of the retired mechanism only in non-executable provenance/documentation surfaces;
- add a corpus test that fails if either legacy admission field reappears in a live skill.

This is a completion requirement, not deferred cleanup. Leaving inert-looking named-model restrictions in executable skills creates an authority ambiguity for humans, hosts, and future tooling.

## Phase 3 — Wire real consumers

### `/qor-plan`

Keep the existing Step 0.3 command name only where compatibility requires it. `model_pinning_lint` becomes a transition shim that:

- never grants or denies authority from model-family identity;
- surfaces the new execution-context scan;
- remains WARN-only;
- preserves the independent fabrication-risk guard;
- treats any remaining live model-pinning fields as migration debt rather than a supported steady state.

A later rename of the compatibility command may occur without changing gate semantics.

### `/qor-audit`

Wire execution-context inspection through `qor_audit_runtime.check_prior_artifact()`, the existing Step 0 runtime seam. The inspection:

- reports the selected rendering recipe;
- records declared and responder model identity separately;
- treats model identity as provenance only;
- reports incomplete capability telemetry as `unverified`;
- blocks only when an explicit execution contract has a hard requirement and the runtime declares a complete capability inventory proving that requirement absent.

`/qor-audit` itself must contain no named-model eligibility field.

### `/qor-substantiate` and other live skills

The same authority rule applies across the executable corpus. No governance phase may become unreachable merely because the current model family is absent from a named allowlist or a vendor-specific quality tier.

## Phase 4 — Compatibility and safety

### `qor/scripts/model_pinning_lint.py`

Retain the module name temporarily for backwards compatibility and fabrication-risk scanning, but remove vendor-specific authority semantics.

- no model-family mismatch may become an execution denial;
- no vendor-specific capability ladder is an authority source;
- compatibility parsing, if temporarily retained for historical callers, is explicitly non-authoritative and must not be required by live skill frontmatter;
- existing fabrication-risk doctrine pointer checks remain intact.

### Compiler safety

NR-001/NR-002 injection behavior is not changed in this slice. Its protection remains binding regardless of model identity. Current compiler prose and tests must not imply that those protections exist only for a named model tier.

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
9. active skills contain no `model_compatibility` or `min_model_capability` admission fields;
10. non-vendor-specific/unknown model identity does not block `/qor-audit` entry;
11. `/qor-audit` blocks only a proven missing hard capability;
12. the compatibility shim never warns or fails because a model family is absent from a former allowlist;
13. fabrication-risk guards remain active;
14. full repository variant drift remains clean.

## Non-goals

- empirical qualification database;
- automated vendor documentation ingestion;
- runtime benchmarking;
- per-model prompt templates;
- self-certifying model capabilities;
- changing Qor gate semantics;
- erasing historical research or changelog provenance that documents the retired mechanism.

## Definition of Done

- ADR and code agree on the invariant/adaptive boundary.
- Active executable skills contain no named-model admission fields or vendor-tier eligibility constraints.
- Model identity has no execution-authority effect in the shared runtime seam.
- `/qor-audit` can enter under an unknown/non-vendor-specific declared model when no proven hard capability is missing.
- Execution-context behavior is deterministic and unit-tested.
- Qor truthfully distinguishes missing capability from unknown telemetry.
- Bounded rendering hints cannot change governance semantics.
- Negative constraints remain active independently of model identity.
- A regression test prevents reintroduction of live model pinning.
- Full CI and variant drift pass on the final Phase 240 head.

## CI Commands

- `python -m pytest tests/test_execution_context.py tests/test_model_pinning_frontmatter.py tests/test_qor_audit_execution_context.py -q` — focused Phase 240 contract tests.
- `python -m pytest tests/ -q` — full repository regression suite.
- `python qor/scripts/check_variant_drift.py` — generated-host variant consistency.
- `python -m ruff check qor tests` — static lint over implementation and tests.
