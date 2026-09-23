# Plan: Phase 295 - Two-Gap Assurance ADR Bounded Amendment

**Issue:** GH #498 under umbrella GH #497
**change_class**: governance
**Status:** prepared; blocked on Phase 294 lifecycle/QA doctrine admission before formal audit/promotion

## Problem contract

The proposed `docs/ADR_TWO_GAP_ASSURANCE_BOUNDARY.md` correctly separates requirement gap from model gap and historical PASS from current fitness, but repeated pre-audit review identified bounded authority/evidence ambiguities that prevent adoption:

1. authority-bearing evidence envelopes were advisory rather than mandatory;
2. acceptance and promotion were compressed into one transition;
3. current-fitness invalidation lacked a canonical minimum trigger vocabulary;
4. invalidation lacked an explicit blocking state that preserves historical PASS truth.

## Objective

Amend the existing proposed ADR only enough to resolve those bounded findings without introducing runtime schemas, new skills, deployment adapters, Shadow Spectrum wiring, or a second evidence registry.

## Dependency gate

Phase 294 (`GH #497` / `GH #502`) establishes the lifecycle and QA semantic foundation that this ADR consumes. Phase 295 may be prepared in parallel for review efficiency, but it MUST NOT be adopted or treated as implementation authority before the Phase 294 doctrine foundation is admitted.

## Authorized changes

1. Amend `docs/ADR_TWO_GAP_ASSURANCE_BOUNDARY.md`.
2. Preserve `Status: Proposed` until formal `/qor-audit` PASS and governed adoption.
3. Encode a mandatory minimum evidence envelope for authority-bearing transitions.
4. Separate acceptance from promotion authorization/action.
5. Define the core current-fitness invalidation vocabulary.
6. Define `CURRENT_FITNESS_NOT_ESTABLISHED` as a blocking assurance state that does not rewrite historical PASS truth.
7. Clarify #499, #500, and #502 as downstream/cross-cutting consumers rather than substitutes for #498 adoption.

## Locked decisions

### LD-1: mandatory core envelope

Authority-bearing transitions MUST bind to subject revision, governing contract, evaluator/check set or explicit `not_applicable`, evaluated environment/conditions or explicit `not_applicable`, supporting evidence, freshness, limitations/exclusions, and authority basis where required.

Profiles may enrich the envelope but may not silently omit required dimensions.

### LD-2: acceptance does not grant promotion authority

Acceptance is a claim about suitability for intended use. Promotion is a separately authorized action family. Merge, release, publish, deploy, and activate do not inherit authority from acceptance or from each other.

### LD-3: minimum invalidation vocabulary

Core classes:

- `REVISION_DRIFT`
- `CONTRACT_DRIFT`
- `EVALUATOR_DRIFT`
- `ENVIRONMENT_DRIFT`
- `DEPENDENCY_DRIFT`
- `AUTHORITY_DRIFT`
- `FRESHNESS_EXPIRED`
- `CONTRADICTORY_EVIDENCE`

Profiles may add classes but may not erase the core meanings.

### LD-4: explicit not-established state

An applicable unresolved invalidation moves current fitness to `CURRENT_FITNESS_NOT_ESTABLISHED`. That state blocks dependent advancement requiring current fitness but does not retroactively convert a historically truthful PASS into FAIL.

Unknown applicability does not collapse to current-fit.

## Evidence strategy

Formal audit must verify:

- no contradiction with Phase 294 lifecycle/QA doctrine once admitted;
- no implicit authority inheritance between acceptance and promotion;
- no universal heavyweight schema is accidentally mandated;
- `not_applicable` cannot be used as silent omission;
- invalidation classes are semantically distinct enough to implement deterministically;
- historical evidence remains immutable/truthful;
- #499 Shadow classification cannot create mutation or promotion authority;
- #500 freshness and #502 QA consume/enforce the contract rather than redefine it;
- vendor-neutral production boundary remains intact.

## CI Commands

```bash
python -m pytest tests/test_plan_schema_ci_commands.py -v
python -m pytest tests/ -v
python -m ruff check qor/ tests/
python -m qor.scripts.publication_boundary_lint --repo-root .
```

Mechanical CI is necessary but not sufficient. Formal `/qor-audit` remains required.

## Acceptance criteria

- [x] Mandatory authority-bearing evidence-envelope core defined.
- [x] Explicit `not_applicable` semantics prevent silent omission.
- [x] Acceptance and promotion authority are separated.
- [x] Merge/release/publish/deploy/activate authority is non-inherited.
- [x] Core invalidation vocabulary is defined.
- [x] `CURRENT_FITNESS_NOT_ESTABLISHED` blocks dependent advancement without rewriting historical PASS.
- [x] Unknown/inconclusive invalidation cannot become current-fit by default.
- [x] #499 remains downstream of authority/applicability boundaries.
- [x] #500 and #502 are consumers/enforcers, not substitutes for #498 adoption.
- [x] No runtime implementation or Qortara Logic migration is introduced.
- [ ] Phase 294 lifecycle/QA foundation admitted.
- [ ] Formal `/qor-audit` PASS on this amended ADR/plan.
- [ ] Governed adoption recorded before implementation planning begins.

## Explicit non-goals

- runtime state machine implementation;
- evidence-envelope JSON schema implementation;
- deployment/observability adapter implementation;
- Shadow Spectrum schema wiring;
- Governance Index lifecycle implementation;
- human-QA runtime schema changes;
- Qortara Logic migration.

## Promotion boundary

This phase amends architecture only. It does not close GH #498. GH #498 remains open until the ADR is formally audited/adopted and its acceptance criteria are implemented in later governed slices.