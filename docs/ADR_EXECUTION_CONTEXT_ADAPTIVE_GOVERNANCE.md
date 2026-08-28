# ADR: Execution-Context Adaptive Governance

**Status:** Accepted for Phase 240 implementation

**Issue:** GH #379

**Date:** 2026-08-28

## Context

Qor's Phase 55 model-pinning mechanism encoded a valid early lesson: different AI models can require different instruction structure, wording, repetition, and control tactics. The original implementation expressed that lesson through named-model allowlists and a vendor-specific capability ladder.

That representation no longer scales. Model names change quickly, stable aliases can change behavior, hosts can route a nominal session to another responder, reasoning modes alter behavior within one model family, and host/tool/system-prompt context materially affects execution. Qor's own later research already identified declared-model/responder skew.

The original metadata was also declarative and WARN-only. It was never a reliable authority boundary. Keeping those fields physically present in live executable skills after declaring them non-authoritative creates a second problem: humans and downstream tooling can still reasonably interpret them as eligibility controls. The migration therefore must remove the ambiguous live surface, not merely reinterpret it.

## Decision

Qor will govern **execution context**, not model identity, as the primary adaptation surface.

Model identity remains provenance and evaluation evidence. It does not by itself grant or deny authority to execute a governance skill.

The architecture separates four concerns:

1. **Invariant governance contract** — semantic obligations, authority, gate meanings, evidence requirements, ABORT/PASS/VETO semantics, and safety constraints.
2. **Skill execution requirements** — observable runtime capabilities required to perform the work plus advisory quality expectations.
3. **Runtime execution context** — host, declared model family, responder model family when known, reasoning mode, and published runtime capabilities.
4. **Bounded rendering recipe** — a deterministic allowlisted presentation strategy that may change wording/order/redundancy but cannot change semantics.

## Invariant versus adaptive boundary

The following are model- and host-invariant:

- gate authority and legal predecessor rules;
- PASS/VETO/ABORT semantics;
- evidence and provenance requirements;
- negative constraints and fabrication protections;
- required tests and validation behavior;
- security and authority boundaries;
- production-write permissions and prohibitions.

The following may adapt within an admitted recipe:

- outcome-first versus procedure-first presentation;
- checklist versus prose formatting;
- explanatory repetition;
- amount of non-binding example material;
- ordering of semantically independent explanatory sections.

An adaptive recipe may never remove, weaken, reinterpret, or synthesize a governance obligation.

## Runtime evidence precedence

When Qor chooses presentation behavior, evidence is ordered:

1. invariant Qor contract;
2. observable host/runtime facts;
3. versioned empirical qualification evidence, when available;
4. vendor/host guidance, when explicitly encoded by a governed change;
5. model-supplied rendering hint constrained to an allowlist;
6. conservative default.

A model may select among legal rendering recipes. It may not self-certify capability, authority, or qualification.

## Execution-context contract

Scoped skills may declare:

```yaml
hard_execution_requirements: [repo-read, repo-search]
advisory_quality_requirements: [high-reasoning, high-instruction-fidelity]
rendering_recipes: [conservative, outcome-first, explicit-checklist]
default_rendering_recipe: conservative
```

`hard_execution_requirements` are only binding when the runtime publishes a complete capability inventory. If capability reporting is incomplete, unmet requirements are reported as **unverified**, not falsely treated as absent.

`advisory_quality_requirements` are never used as mechanical admission criteria without separate empirical qualification evidence.

## Bounded rendering recipes

Phase 240 admits exactly three recipe identifiers:

- `conservative` — preserve source ordering and explicit constraints; no compression of required steps.
- `outcome-first` — foreground objective and success condition, then execute the unchanged required checks.
- `explicit-checklist` — present required checks as an explicit checklist while preserving every obligation.

Recipe selection is deterministic. A runtime/model hint is honored only when it names a recipe already admitted by the skill.

## Retirement of live model pinning

`model_compatibility` and `min_model_capability` are retired from active executable skill frontmatter as part of Phase 240.

The compatibility module name may remain temporarily for historical callers and for its independent fabrication-risk doctrine scan, but named-model metadata is not a supported steady-state execution contract.

Phase 240 therefore requires:

- removal of named-model allowlists and vendor-tier minimums from live skills;
- replacement of model-specific eligibility language with execution-context/capability language;
- a regression test that rejects reintroduction of the retired fields into active skills;
- no runtime path that derives authority from a former model tier.

Historical research, changelog, sealed evidence, and ADR material may describe the retired mechanism where doing so is necessary to explain provenance. That history is not executable authority.

## Negative constraints

The NR-001/NR-002 protections remain independent of model identity. The distribution compiler may continue to inject those protections into cross-host variants, but the rationale is **cross-host high-risk execution**, not an asserted model tier.

## Unknown models and hosts

Unknown model families are not rejected. They receive the skill's conservative default rendering unless a valid bounded hint or observable reasoning-mode rule selects another admitted recipe.

Unknown runtime capabilities are surfaced explicitly as unverified. Qor must not turn missing telemetry into a fabricated capability verdict.

## Alternatives rejected

### Maintain a named-model registry

Rejected because model proliferation, aliases, routing, and host-specific behavior make the registry stale faster than Qor can govern it.

### Leave model pins physically present but declare them inert

Rejected because live executable metadata that appears to restrict model eligibility remains an authority ambiguity for operators, hosts, compilers, and future tooling. A governance control should not require oral tradition to explain that its visible restriction is supposedly meaningless.

### Let the model freely optimize its own prompt

Rejected because the executing model would effectively gain authority to rewrite its controls.

### Build a large qualitative capability taxonomy

Rejected for v1 because labels such as "premature implementation tendency" or "adversarial strength" are subjective until backed by repeatable evaluations.

### Reject unknown models

Rejected because it converts incomplete telemetry into an authority decision and recreates vendor lock-in.

## Consequences

Positive:

- Qor becomes vendor-neutral at the governance layer;
- model identity remains observable without becoming authority;
- adaptation can evolve without duplicating skill semantics;
- model/host self-knowledge is useful but bounded;
- execution limitations become explicit and truthfully scoped;
- executable skill metadata no longer contradicts the portability contract.

Costs:

- host adapters need to publish richer capability context over time;
- quality qualification remains advisory until empirical suites exist;
- the live skill corpus and tests must be migrated in this phase rather than deferred;
- historical model-pinning documentation remains provenance and should not be rewritten to pretend the old design never existed.

## Phase 240 scope

Phase 240 implements the execution-context inspector, bounded recipe selection, live skill-corpus removal of named-model admission metadata, `/qor-plan` preflight wiring, `/qor-audit` context inspection, compatibility behavior for the old module name where necessary, focused tests, and the minimum documentation correction needed to describe the new authority boundary.

It does **not** build an empirical model-qualification layer, remote model registry, benchmark service, or per-model recipe database.
