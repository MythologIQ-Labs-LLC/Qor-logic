# Plan: Phase 289 - Governed Attention Resolver V1

**Issue:** GH #501, child of GH #497
**change_class**: feature
**Status:** plan prepared; formal `/qor-audit` required before implementation

## Problem contract

Qor has many governance sources but no canonical, inspectable mechanism that determines which sources participate in a particular operation. Global injection creates ceremony and context burden; unconstrained retrieval risks silently creating apparent authority from relevance.

GH #501 passed architecture review for a bounded V1 on 2026-09-22 with four mandatory constraints: typed authority-bearing inputs, pure applicability resolution, fail-visible ambiguity for unresolved canonical conflicts, and negative evidence for considered exclusions.

## Objective

Implement a stdlib-only pure resolver over typed synthetic inputs that produces a deterministic, explainable minimum governance packet without creating policy, authority, obligations, or repository mutations.

## Authorized changes

1. Add a small resolver module under `qor/scripts/` or a more appropriate existing runtime package identified during implementation recon.
2. Add focused behavioral tests for the resolver contract and three representative workflow pilots.
3. Add only the minimum schema/types necessary for deterministic resolution.
4. Update documentation required by procedural-fidelity and governance-index rules.

## Locked decisions

### LD-1: authority-bearing fields are explicit

V1 consumes an `OperationDescriptor`. Authority ceiling, lifecycle state, change/risk class, mutation posture, external visibility, and environment relevance are explicit caller/canonical-state inputs. V1 does not infer these fields from prose similarity.

### LD-2: resolution is pure

Given an operation descriptor and governance-source metadata, resolution returns dispositions and rationale. It does not mutate governance state, waive gates, create obligations, or perform arbitrary retrieval.

### LD-3: dispositions are bounded

V1 supports: `required`, `advisory`, `optional`, `excluded`, `stale`, `superseded`, and `ambiguous`.

### LD-4: ambiguity fails visibly

Conflicting current canonical sources at equal effective precedence with no accepted supersession produce `ambiguous`. The resolver does not invent a tie-breaker.

### LD-5: exclusions are evidence

The output packet records considered-but-excluded sources with stable reason/rule identifiers so minimum context is distinguishable from accidental omission.

### LD-6: deterministic ordering

Equivalent inputs produce equivalent ordered output independent of input collection ordering.

### LD-7: authority ordering is closed and mechanically decidable

V1 must not derive authority ordering from strings, source-list position, retrieval rank, semantic similarity, or implementation accident. Implementation recon must first bind `authority_class` to an existing canonical repository ordering if one exists. If no such ordering exists, V1 introduces the smallest closed ordered enum needed by the three pilots and documents that enum as part of the resolver contract.

The same comparison function must be used for both authority-ceiling enforcement and equal-precedence conflict detection. An unknown, unsupported, or otherwise incomparable authority class is not coerced into the ordering: its resolution is fail-visible `ambiguous` and requires escalation/canonical-state repair before it can contribute required authority.

A governance source whose authority class exceeds the operation's explicit authority ceiling cannot resolve to `required`, regardless of relevance or applicability matches. This rule is mechanically testable and is not a prose-only expectation.

## Candidate contracts

- `OperationDescriptor`: operation type, lifecycle state, artifact/subsystem, change/risk class, environment relevance, authority ceiling, mutation class, external visibility.
- `GovernanceSource`: stable id, source class, canonical authority class, applicability predicates, freshness/supersession state, required/advisory posture.
- `Resolution`: disposition, matched rule ids, rationale, authority class.
- `GovernancePacket`: operation identity, required/advisory/optional sources, exclusions, stale/superseded records, unresolved ambiguity.

Exact Python representation is implementation detail subject to audit and repository convention recon, except that authority ordering must satisfy LD-7.

## Pilot workflows

1. **Ordinary implementation change**: implementation obligations surface; deployment/runtime-only sources are explicitly excluded.
2. **Deployment-sensitive change**: environment/release obligations surface without granting deployment authority.
3. **Governance/documentation change**: doctrine/governance freshness surfaces while unrelated runtime ceremony is excluded.

## Evidence strategy

Behavioral tests must prove:

- no source can raise the operation authority ceiling;
- authority comparison uses the canonical/closed ordering rather than lexical or input-order comparison;
- unknown or incomparable authority classes become `ambiguous`, never silently coerced;
- equal-precedence conflict detection uses the same authority comparison semantics as ceiling enforcement;
- semantic/relevance labels alone cannot create `required` status;
- exclusions retain stable rationale;
- stale and superseded sources cannot masquerade as current required context;
- equal-precedence unresolved conflicts become `ambiguous`;
- output is deterministic across shuffled input order;
- all three pilots produce bounded packets with both positive and negative evidence.

## CI Commands

```bash
python -m pytest tests/ -v
python -m ruff check qor/ tests/
python -m qor.scripts.seal_artifacts --check --skip-tests --repo-root .
python -m qor.scripts.publication_boundary_lint --repo-root .
```

Formal `/qor-audit` remains required before implementation.

## Acceptance criteria

- [x] Bounded V1 architecture survives adversarial review on GH #501.
- [x] Minimal typed operation/source/output contracts are specified for audit.
- [x] Authority-preservation and ambiguity behavior are locked.
- [x] Authority ordering/comparison is mechanically decidable and fail-visible for unknown classes.
- [x] Negative-evidence/exclusion behavior is locked.
- [x] Three representative pilots are specified.
- [ ] Formal `/qor-audit` PASS on this implementation plan.
- [ ] Resolver implementation is behaviorally tested.
- [ ] Three pilots pass without context explosion or authority creation.
- [ ] Documentation/governance surfaces are reconciled.

## Explicit non-goals

- Shadow Spectrum metadata wiring from #499;
- #498 evidence-envelope integration;
- #500 automated freshness/supersession ingestion;
- semantic/vector retrieval as an authority mechanism;
- changing lifecycle gates;
- introducing a new skill;
- Qortara Logic migration.

## Promotion rule

Do not implement until this plan receives formal `/qor-audit` PASS. After implementation, normal substantiation and repository gates still apply; this plan does not authorize merge by itself.
