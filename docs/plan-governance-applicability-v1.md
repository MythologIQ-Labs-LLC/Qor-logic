# Plan: Governed Attention / Applicability Resolver V1

**Issue:** GH #501 under umbrella GH #497
**change_class**: feature
**Status:** bounded V1 implementation prepared for current-base audit and CI

## Objective

Implement the smallest deterministic control plane that can decide which explicitly supplied governance sources apply to a typed operation without semantic retrieval, authority invention, global context injection, or Shadow Spectrum coupling.

This is the bounded V1 already admitted by the architecture review on #501.

## Authorized implementation

1. Add a pure stdlib resolver in `qor/scripts/governance_applicability.py`.
2. Define typed operation facts, applicability rules, governance-source metadata, per-source resolutions, and a deterministic governance packet.
3. Support explicit result states: `required | advisory | optional | excluded | stale | superseded | ambiguous`.
4. Preserve negative evidence for considered-but-excluded sources.
5. Fail visibly when current same-precedence sources declare conflicting decisions in the same rule domain.
6. Consume freshness/supersession status only as caller-supplied metadata; do not duplicate #500's freshness owner.
7. Exercise the resolver with ordinary implementation, deployment-sensitive, and governance/documentation pilot cases.

## Locked decisions

### LD-1: typed inputs only

`OperationDescriptor` is caller-supplied canonical context. V1 does not infer lifecycle state, authority ceiling, risk/change class, environment relevance, mutation posture, or visibility from prose similarity.

### LD-2: explicit applicability rules

A source participates only through declared exact-match `ApplicabilityRule` metadata. Empty rule fields are unconstrained, but a source with no rules is excluded as unclassified rather than silently treated as global.

### LD-3: resolver is pure with respect to authority

The resolver may preserve a source's declared `required`, `advisory`, or `optional` posture. It may exclude, flag stale/superseded state, or return ambiguity. It cannot upgrade authority, waive gates, mutate governance state, fetch arbitrary material, or create obligations from retrieval similarity.

### LD-4: negative evidence is durable output

Every considered source receives a resolution. Excluded sources carry a machine-readable reason such as no rule match or lower-precedence shadowing. Context minimization is therefore distinguishable from accidental omission.

### LD-5: precedence is explicit and local

Precedence is source metadata and applies only inside an explicit `rule_key`. Higher numeric precedence may shadow lower precedence in that rule domain. Additive sources with no `rule_key` are not globally rank-ordered.

### LD-6: conflict is fail-visible

A conflict-ranked source must declare a `decision_token`. If multiple current applicable sources at the same highest precedence for the same `rule_key` declare different decision tokens, all winners resolve `ambiguous`. V1 does not invent a tie-breaker.

### LD-7: freshness remains owned by #500

V1 only consumes `current | stale | superseded` metadata. It does not calculate document currency, supersession graphs, or ADR status. Those remain #500 responsibilities.

### LD-8: no Shadow or retrieval wiring yet

V1 has no embeddings, semantic search, repository retrieval, Shadow Spectrum metadata, #498 evidence-envelope integration, external service dependency, or runtime mutation.

## Pilot cases

1. **Ordinary implementation:** implementation doctrine is surfaced while production-only material is explicitly excluded.
2. **Deployment-sensitive change:** promotion/release authority and operational evidence surface when environment relevance is production.
3. **Governance/documentation change:** governance freshness obligations surface while unrelated runtime recovery ceremony is excluded.

## Verification

Required exact-head evidence:

```bash
python -m pytest tests/test_governance_applicability.py -v
python -m pytest tests/ -q
python -m ruff check qor/ tests/
```

CI remains authoritative for execution evidence. This plan does not claim those commands passed until the exact branch revision runs them.

## Acceptance criteria

- [x] typed operation descriptor exists;
- [x] authority-bearing fields are inputs, never semantic inference outputs;
- [x] applicability rules are explicit and deterministic;
- [x] missing applicability metadata does not create global context;
- [x] resolver preserves declared source posture rather than upgrading it;
- [x] required/advisory/optional/excluded/stale/superseded/ambiguous are explicit;
- [x] negative evidence records why considered sources were excluded;
- [x] freshness/supersession is consumed without duplicating #500 ownership;
- [x] same-precedence conflicts fail visibly as ambiguous;
- [x] incomplete conflict metadata fails closed;
- [x] output ordering is deterministic;
- [x] ordinary implementation pilot covered;
- [x] deployment-sensitive pilot covered;
- [x] governance/documentation pilot covered;
- [ ] exact-head CI/test/lint evidence passes;
- [ ] independent/current-base review accepts the implementation;
- [ ] #501 acceptance criteria are reconciled after merge rather than inferred from PR existence.

## Non-goals

- no semantic search or embeddings;
- no arbitrary repository retrieval;
- no automatic source discovery;
- no independent policy authority;
- no #498 evidence-envelope enforcement;
- no #499 Shadow Spectrum wiring;
- no #500 freshness computation;
- no lifecycle/gate mutation;
- no Qortara Logic migration.

## Follow-on only after V1 proves stable

- connect #500-produced freshness/supersession metadata;
- expose adopted #498 evidence/current-fitness metadata proportionally;
- pilot Shadow Spectrum metadata only after #499 is adopted;
- measure false positives, false negatives, ambiguity rate, and context burden before any retrieval expansion.
