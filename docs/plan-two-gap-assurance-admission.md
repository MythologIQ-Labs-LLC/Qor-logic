# Plan: Two-Gap Assurance ADR Admission

**Issue:** GH #498 under umbrella GH #497
**change_class**: feature
**Status:** bounded documentation/admission slice; formal `/qor-audit` required before ADR adoption

## Objective

Resolve the known bounded defects in `docs/ADR_TWO_GAP_ASSURANCE_BOUNDARY.md` so the two-gap assurance model can receive a meaningful formal adoption review without yet implementing runtime enforcement.

## Authorized changes

1. Clarify that inner/outer loop arrows represent assurance relationships and claim progression, not a mandatory universal runtime order.
2. Separate acceptance from promotability/promotion authority.
3. Define a mandatory minimum evidence envelope for claims that advance lifecycle authority.
4. Define a minimum current-fitness invalidation contract.
5. Define explicit recovery/containment/rollback authority separately from remediation authority.
6. Define a vendor-neutral outer-loop evidence handoff contract.
7. Preserve historical PASS truth while making unknown current-fitness state fail visibly as `UNESTABLISHED`.

## Locked decisions

### LD-1: authority-bearing envelopes are mandatory

A claim used to advance lifecycle authority must bind to the exact revision/artifact, governing contract, evaluator/check set, relevant evaluated environment/model, evidence, freshness, exclusions/N/A state, and responsible authority where applicable.

Profiles may add fields. They may not silently erase relevant core fields.

### LD-2: acceptance does not authorize promotion

Acceptance is an assurance decision. Merge, release, publish, deploy, and activate remain separately authorized actions.

### LD-3: fitness invalidation has a minimum enforceable vocabulary

At minimum, consumers must account for revision/base drift, contract drift, evaluator drift, environment-model drift, dependency/external-contract drift, authority drift, freshness expiry, and contradictory operational evidence.

Unknown material invalidation state means current fitness is unestablished, not implicitly valid.

### LD-4: containment and remediation are separate authority domains

Containment/rollback may precede complete causal classification when immediate risk requires it, but only under pre-existing recovery authority. Containment does not grant root-cause mutation authority and remediation does not prove recovery.

### LD-5: no runtime enforcement in this slice

This branch only repairs the proposed ADR and records the adoption plan. It does not change schemas, skills, gates, runtime state, QA enforcement, Shadow Spectrum writers, or Qortara Logic.

## Evidence strategy

Formal review should challenge at least:

- whether the evidence-envelope minimum is sufficient without becoming universal ceremony;
- whether acceptance and promotion authority are cleanly separated;
- whether the invalidation trigger set is minimal but complete enough to fail safely;
- whether historical validity remains distinct from current fitness;
- whether containment authority can act rapidly without becoming silent remediation authority;
- whether outer-loop handoff remains vendor-neutral and non-mutating by default;
- whether the ADR duplicates or contradicts Phase 294 lifecycle/QA doctrine;
- whether Shadow Genome integration remains downstream of applicability/authority resolution.

## Acceptance criteria

- [x] Evidence envelope is mandatory for authority-bearing transitions.
- [x] Profile-specific omission requires explicit N/A/rationale rather than silence.
- [x] Acceptance is separated from promotability and promotion actions.
- [x] Minimum current-fitness invalidation classes are explicit.
- [x] Unknown material invalidation state maps to `UNESTABLISHED`.
- [x] Recovery/containment/rollback authority is separate from remediation authority.
- [x] Outer-loop handoff contract is explicit and vendor-neutral.
- [x] Historical evidence remains immutable truth even when current fitness expires.
- [x] No runtime enforcement is introduced by this slice.
- [ ] Formal `/qor-audit` PASS on the current revision.
- [ ] ADR adoption status updated only after that review permits it.
- [ ] Implementation plan for enforceable envelope/invalidation behavior follows adoption.

## Explicit non-goals

- no runtime schema implementation;
- no automatic fitness invalidation engine;
- no deployment or observability integration;
- no new acceptance skill;
- no Shadow Spectrum runtime wiring;
- no Qortara Logic migration;
- no broad #497 documentation rewrite.

## Follow-on after adoption

1. implement the smallest enforceable evidence-envelope/current-fitness contract;
2. expose the resulting metadata to #501 applicability resolution;
3. reconcile #500 freshness/supersession enforcement;
4. allow #499 Shadow Spectrum to consume typed divergence only after applicability/authority boundaries are settled;
5. integrate #502 human-QA evidence as another bounded evidence source rather than a universal gate.
