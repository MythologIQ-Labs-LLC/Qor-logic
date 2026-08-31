# ADR: Qor Roadmap as a Governed Decision-Topology Meta Capability

**Status:** Proposed, amended after pre-implementation adversarial review; formal `/qor-audit` still required
**Date:** 2026-08-27
**Scope:** Qor-logic base capability
**Adversarial review:** `docs/adversarial-review-qor-roadmap-2026-08-27.md`

## Context

Qor already has strong single-purpose phases for framing intent, researching facts, planning implementation, auditing plans, implementing, substantiating, validating, and remediating process failures.

A remaining gap appears when one objective is too large, dependency-rich, uncertain, or long-lived to become a trustworthy implementation plan in one pass. In that class of work, future decisions may not yet be specifiable, independent factual branches may proceed at different rates, and a new agent context may need to resume without re-asking settled questions.

The new capability must not solve that gap by creating a second ideation, research, or planning system.

## Decision

Add a Qor-native meta capability named `/qor-roadmap`.

`/qor-roadmap` owns durable decision topology and routing for genuinely long-horizon work. It records what remains unresolved, what depends on what, what is currently actionable, and which existing Qor skill or authority actor legally resolves each item.

It is not an SDLC phase.

It is not a workflow bundle with a fixed phase sequence.

It does not perform production implementation.

It does not replace `/qor-ideate`, `/qor-research`, or `/qor-plan`.

The semantic boundary is:

> Roadmap determines what remains to become known, decided, or unblocked before a defined scope may enter planning.
>
> Existing Qor skills perform the work that resolves those items.
>
> Plan determines how a sufficiently resolved scope will be implemented.

## v1 admission boundary

Roadmap is intentionally narrow in v1.

It is operator-invoked only and experimental until controlled evaluation demonstrates enough benefit to justify automatic routing.

Use it only when at least one strong long-horizon condition exists:

- the objective is expected to require multiple agent contexts before an implementation plan is trustworthy;
- future work cannot yet be specified because independent prerequisite decisions or facts block it;
- several independent resolution branches must be preserved across context changes;
- one objective is expected to yield more than one governed implementation plan over time and needs a shared decision substrate.

Do not invoke Roadmap merely because a feature is complex. `/qor-plan` already owns complex and multi-phase implementation planning. Do not invoke Roadmap merely because a concept is fuzzy. `/qor-ideate` already owns problem framing, assumptions, options, scope, and readiness.

## Placement

Roadmap is a program-level meta capability. The implementation plan should place the canonical skill under the existing meta skill surface, subject to live-tree verification.

Roadmap must not declare `phase: roadmap` or become a new gate in `qor/gates/chain.md` in v1.

## Ownership boundary

Roadmap owns only:

1. roadmap and objective identity;
2. durable node state and history;
3. dependency edges;
4. unresolved-space metadata;
5. actionable-frontier derivation;
6. evidence and decision pointers;
7. resolver/routing metadata;
8. plan-handoff readiness and handoff pointers.

Roadmap does not own the resolution process for another Qor skill's domain.

Examples:

- factual discovery requiring investigation routes to `/qor-research`;
- missing problem framing routes to `/qor-ideate`;
- implementation design routes to `/qor-plan`;
- production code changes route through the existing S.H.I.E.L.D. chain;
- authority-scoped decisions are surfaced to the actor holding sufficient authority.

The delegation table remains the single source of truth for cross-skill handoffs.

## Relationship to the existing lifecycle

```text
long-horizon objective
        |
        v
  /qor-roadmap
        |
  existing framing present?
    | yes       | no
    |           v
    |      /qor-ideate
    |           |
    +-----------+
        |
        v
 durable prerequisite graph
        |
 actionable frontier
    /          \
 fact          decision
  |               |
/qor-research   authority
    \          /
     record result
        |
 recompute frontier
        |
 no unresolved blockers
 for a named planning scope
        |
        v
    /qor-plan
        |
 existing S.H.I.E.L.D.
```

Roadmap never bypasses `/qor-plan`'s existing prior-artifact rules. Before handoff, it verifies that a legal ideation or research predecessor exists for the current Qor session. If one is missing, Roadmap routes to that predecessor instead of manufacturing a gate override.

A Roadmap-specific gate predecessor is outside v1 and requires a separate architecture decision.

## Working domain model

### Objective

The long-horizon outcome the Roadmap exists to make plannable over time. It carries success conditions and explicit exclusions.

### Roadmap Node

A stable-identity unresolved or resolved prerequisite.

v1 node kinds:

- `fact`: evidence the agent can lawfully establish, normally through `/qor-research` when investigation is required;
- `decision`: a consequential choice with explicit authority requirement;
- `prerequisite`: a non-production condition or setup state that must become true before a planning scope is ready.

Roadmap does not model implementation tasks in v1.

### Dependency Edge

A directed blocking relation between Roadmap nodes. The v1 graph is acyclic. A node cannot be actionable while any blocking predecessor is unresolved or marked for review.

### Unresolved Space

Lightweight metadata naming uncertainty that cannot yet be decomposed responsibly into nodes. It is distinct from out-of-scope work.

Unresolved Space does not receive model-invented scores in v1. It either graduates into explicit nodes, is retired with rationale, or remains visible.

### Actionable Frontier

The set of unresolved nodes whose blocking dependencies are resolved and whose resolver is legally available now.

v1 returns the frontier set plus inspectable graph-derived annotations. It does not automatically choose the next node.

Permitted annotations include:

- direct dependent count;
- transitive dependent count;
- graph distance to an explicitly declared planning-scope condition;
- explicit operator priority when one was actually declared.

No model-estimated leverage, risk-reduction, uncertainty-reduction, or execution-cost score is authoritative in v1.

### Decision Record

The immutable historical record of a resolved authority decision, including rationale, evidence pointers, authority, and dependency references.

A later decision does not rewrite the prior record. It supersedes it explicitly.

### Plan Handoff

A Roadmap output, not a Roadmap node.

A Plan Handoff states that a named scope has no unresolved Roadmap prerequisites and carries pointers to the objective, settled decisions, factual evidence, limitations, and exclusions required by `/qor-plan`.

It contains no implementation decomposition or production task list.

## Persistence model

v1 uses one repository-local versioned append-only event history as canonical Roadmap state:

```text
.qor/roadmaps/<roadmap-id>/events.jsonl
```

No `state.json` materialized cache ships in v1. Current state is reduced in memory from the event history on load. A persistent projection may be added later only if measured reconstruction cost justifies it.

The first event declares the Roadmap contract version. Unsupported future versions fail visibly rather than being partially interpreted.

Initial event families are limited to behavior required by the vertical pilot:

- roadmap created;
- objective amended with rationale;
- node added;
- dependency added or removed with rationale;
- unresolved space added, graduated, or retired;
- fact resolved with evidence pointer;
- decision resolved with authority and rationale;
- prerequisite resolved;
- decision superseded;
- descendant invalidated for review;
- plan handoff emitted.

Atomic append semantics must be explicit. The implementation plan should reuse or generalize proven Qor atomic JSONL behavior where doing so does not create disproportionate blast radius.

## Single-writer v1

v1 has one canonical Roadmap writer per invocation. Parallel subagents may investigate facts, but they return results to the Roadmap orchestrator rather than mutating canonical Roadmap state independently.

Therefore v1 has no Roadmap-specific work leases, claim expiry, heartbeat, or stale-assignee model.

If real multi-writer demand appears later, the design must first evaluate the durable claim and live-writer semantics Qor already owns under execution continuity. A second independent claim vocabulary is not admitted by default.

## Fact and decision authority rule

Roadmap separates discoverable facts from authority-scoped decisions.

- Facts the agent can lawfully establish are agent obligations.
- Consequential choices remain authority-scoped decisions.
- Missing facts should not be converted into operator questions merely because asking is easier than investigating.
- One blocked decision does not block independent actionable nodes.
- Roadmap records resolution evidence and authority. It does not silently infer authority.

## Supersession semantics

Resolved decisions are historical facts and remain visible.

When a prior decision is superseded:

1. append the replacement decision relation;
2. deterministically identify graph descendants that depended on the superseded decision;
3. mark those descendants `needs_review` or equivalent;
4. remove affected unresolved descendants from the actionable frontier until reviewed;
5. route each review through its lawful resolver.

Qor does not claim that semantic validity can be recomputed automatically merely because graph impact can be computed deterministically.

Generalizing supersession beyond Roadmap is deferred until at least one additional real consumer exists.

## Research economy

Roadmap may deduplicate identical factual needs before delegating research and should pass the minimum sufficient brief to each research invocation.

Roadmap does not define model brands or fixed cost tiers. Existing Qor capability and host policies own model selection.

## Plan-handoff boundary

A Plan Handoff is legal only when:

- the named scope has no unresolved blocking nodes;
- no blocking descendant is `needs_review`;
- required evidence pointers exist;
- every required authority decision is recorded;
- the current Qor session has a legal predecessor artifact accepted by `/qor-plan`.

If the last condition is false, Roadmap routes to `/qor-ideate` or `/qor-research` as appropriate and does not create an override merely to proceed.

The handoff references settled artifacts by pointer. It does not copy a second mutable version of their contents.

## Production-implementation boundary

Roadmap contains no production implementation step.

The enforceable guarantee is layered rather than overstated:

- the canonical Roadmap procedure never instructs production-code mutation;
- Roadmap state mutations use the narrowest available deterministic Qor helper or CLI;
- canonical tool declarations omit production-edit capabilities where a host can enforce that distinction;
- tests verify that Roadmap helpers write only within the Roadmap state surface and that Roadmap emits a `/qor-plan` handoff rather than an implementation action;
- hosts with reliable pre-tool enforcement may add stronger mechanical controls;
- hosts without such a seam receive a disclosed structural boundary, not a false universal hard guarantee.

## v1 implementation strategy

Do not ship schema, reducer, frontier, persistence, and skill prose as separately released foundation layers.

The first implementation target is one vertical experimental pilot that proves the entire narrow journey:

1. initialize one Roadmap;
2. append a few nodes and edges;
3. reconstruct state from disk;
4. compute the frontier set;
5. resolve one fact or decision through the legal resolver;
6. resume from a fresh agent context;
7. determine that a named scope is ready;
8. verify the legal predecessor for `/qor-plan`;
9. emit a compact Plan Handoff;
10. stop before production implementation.

Internal modules and test phases may be separated inside the governed implementation plan, but the capability is not considered delivered until the vertical journey is green.

## Experimental routing posture

v1 is explicitly operator-invoked only.

Automatic routing into Roadmap is deferred until controlled evaluation against the current Qor baseline demonstrates a material improvement in at least some of:

- repeated operator questions;
- facts unnecessarily asked of the operator;
- unresolved assumptions at plan entry;
- duplicate research;
- resume fidelity;
- frontier correctness;
- context/tool cost;
- time to an audit-ready plan;
- gate overrides introduced by the new flow.

A later routing decision must name the signals that justify invocation and the false-positive cost of routing ordinary complex work into Roadmap.

## Enterprise and tracker boundaries

External tracker projection, cross-repository federation, enterprise orchestration, and automatic multi-writer claims are not part of the v1 implementation issue.

They may become separate follow-up issues only after the base pilot is evaluated and the contract is stable enough to consume without forking a second state model.

## Consequences

### Positive

- long-horizon uncertainty can remain explicit without turning `/qor-plan` into persistent project memory;
- cross-context resumption becomes durable;
- operator attention is reserved for real decisions rather than discoverable facts;
- existing Qor skills remain authoritative for their own domains;
- tracker platforms remain optional projections;
- historical decisions can be corrected without silent mutation;
- the first implementation is small enough to evaluate before broader adoption.

### Costs

- Qor gains one new persistent state family under `.qor/`;
- event contracts require schema/version discipline;
- a meta skill adds discoverability pressure even when user-invoked only;
- Roadmap creates value only for a subset of work, so admission discipline matters;
- formal evaluation is required before automatic routing or concurrency features are justified.

## Rejected alternatives

### Extend `/qor-plan` into a persistent long-horizon workspace

Rejected. `/qor-plan` already owns implementation design and should consume resolved context, not retain every unresolved future branch across governed changes.

### Extend `/qor-ideate` into a persistent dependency graph

Rejected for v1. Ideate owns concept framing and readiness. Turning it into long-lived graph state would complect a single-session framing artifact with multi-context program navigation.

### Add Roadmap as a mandatory lifecycle phase

Rejected. Most work does not need it.

### Use an external issue tracker as canonical Roadmap state

Rejected. Tracker limits and platform semantics must not become correctness constraints.

### Add Roadmap-specific work leases in v1

Rejected. Single-writer v1 has no demonstrated canonical claim conflict, and Qor already has continuity claim semantics that must be considered before another model is introduced.

### Persist a derived `state.json` cache in v1

Rejected. Reconstruction cost has not demonstrated a need for a cache.

### Automatically rank the frontier with model-estimated values

Rejected for v1. Determinism over subjective estimates does not create objective priority.

### Represent implementation work as Roadmap nodes

Rejected. That would pull implementation decomposition into a surface whose purpose is to decide when work is ready for `/qor-plan`.

### Allow Roadmap to resolve another skill's domain inline

Rejected. The delegation table remains authoritative.

## Admission criteria for the vertical pilot

Implementation planning may begin only when:

1. this amended ADR and the amended build roadmap have undergone formal `/qor-audit`;
2. the implementation plan treats the first release as one vertical pilot, not a sequence of separately shipped platform layers;
3. the v1 schema excludes leases, cache state, automatic ranking, and implementation task nodes;
4. atomic append and unsupported-version behavior have explicit tests;
5. fresh-context resumption is tested from repository state only;
6. the Plan Handoff preserves `/qor-plan`'s legal prior-artifact contract without a routine override;
7. the delegation table is updated before any Roadmap-to-skill routing is wired;
8. no external tracker, external repository, or enterprise extension is required by the base test suite;
9. research provenance remains documentation only and creates no runtime dependency.

The associated build strategy is `docs/roadmap-qor-roadmap-build-2026-08-27.md`.