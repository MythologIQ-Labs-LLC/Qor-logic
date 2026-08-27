# ADR: Qor Roadmap as a Governed Decision-Topology On-Ramp

**Status:** Proposed, operator-approved for planning; implementation remains subject to `/qor-audit` PASS
**Date:** 2026-08-27
**Scope:** Qor-logic base capability

## Context

Qor's existing lifecycle is strong once work is sufficiently defined to research, plan, audit, implement, substantiate, validate, and remediate. It is less explicit about a different class of problem: objectives that are too large, uncertain, dependency-rich, or multi-session to become a trustworthy implementation plan in one pass.

For that class of work, forcing uncertainty directly into `/qor-plan` creates predictable failure modes:

- premature implementation decomposition;
- hidden factual prerequisites;
- repeated operator questions across sessions;
- stale decisions that remain indistinguishable from current ones;
- duplicated research;
- no explicit representation of work that is not yet specifiable;
- no durable, low-resolution view of what can legally happen next.

The capability must complement S.H.I.E.L.D., not replace it. It must also remain host-neutral and tracker-neutral because Qor compiles into multiple agent environments.

## Decision

Add a Qor-native capability named `/qor-roadmap`.

`/qor-roadmap` is a situational pre-S.H.I.E.L.D. orchestrator for large, ambiguous, dependency-rich, or multi-session objectives. It models the work as a governed decision topology, resolves only the currently actionable frontier, persists decision history and prerequisites across sessions, and hands implementation-ready work to existing Qor skills.

It is not a new mandatory SDLC phase.

It does not implement production code.

It does not replace `/qor-plan`.

The semantic boundary is:

> Roadmap determines what must become known, decided, or unblocked before an objective is ready to execute.
>
> Plan determines how to implement the work after those prerequisites are sufficiently resolved.

## Relationship to the Qor lifecycle

```text
large / ambiguous / multi-session objective
                 |
                 v
           /qor-roadmap
                 |
       governed decision topology
        /        |          \
     facts    decisions   prerequisites
       |          |            |
       v          v            v
 /qor-research  authority   delegated Qor work
       \          |            /
        \         |           /
          actionable frontier
                 |
          roadmap ready
                 |
                 v
             /qor-plan
                 |
                 v
         existing S.H.I.E.L.D.
```

A roadmap may delegate to existing skills according to the delegation table. It must never reproduce those skills' process inline.

## Working domain model

These names are design vocabulary for this proposed capability. Canonical glossary entries land with the implementation slice that makes each concept executable.

### Objective

The outcome the roadmap exists to make implementation-ready. The objective includes success conditions and explicit exclusions.

### Roadmap Node

A stable-identity unit in the decision topology. A node represents one unresolved or resolved prerequisite, not an arbitrary implementation chunk.

Initial node kinds:

- `fact`: evidence the agent can establish;
- `decision`: a consequential choice requiring declared authority;
- `prerequisite`: non-production work or external setup that must become true;
- `implementation`: a handoff marker for work that is ready to enter `/qor-plan`, never production execution inside Roadmap itself.

### Dependency Edge

A directed blocking relation. Node B cannot become actionable while an unresolved dependency edge from A blocks it.

### Unresolved Space

A named area of uncertainty whose concrete nodes cannot yet be stated responsibly. It is distinct from out-of-scope work. As upstream uncertainty resolves, unresolved space either graduates into explicit nodes or disappears as irrelevant.

### Actionable Frontier

The set of open nodes whose blocking dependencies are resolved and whose authority or execution prerequisites allow work now.

### Decision Record

The immutable historical record of a resolved decision, including rationale, evidence pointers, authority, and downstream dependencies.

A later decision does not silently rewrite an earlier one. It supersedes it with an explicit relationship.

### Work Lease

A bounded claim on a node by an actor/session. A lease records actor identity, session identity, claim time, scope, and release or expiry state. Interrupted work must not leave a node permanently unavailable.

## Authority rule

Roadmap separates facts from decisions.

- Factual prerequisites are agent obligations when the agent has lawful access to establish them.
- Consequential choices are resolved only by an actor with sufficient authority.
- Missing facts should not be converted into questions for the operator merely because asking is easier than investigating.
- One blocked decision does not block independent frontier work.

This produces breadth-first progress across the ready frontier rather than serial dialogue through unrelated questions.

## Persistence model

Roadmap state must be reconstructible and must not depend on one mutable prose artifact.

The base implementation will use a repository-local append-only event stream as the canonical state source:

```text
.qor/roadmaps/<roadmap-id>/
├── events.jsonl       # authoritative append-only history
└── state.json         # derived, rebuildable projection
```

The event stream records topology and lifecycle changes. `state.json` is a cache/projection and may be regenerated deterministically from the event history.

Initial event families:

- roadmap created or objective amended;
- node added or classified;
- dependency added or removed with rationale;
- node resolved;
- decision superseded;
- unresolved space added, graduated, or retired;
- lease acquired, released, or expired;
- roadmap declared implementation-ready.

A human-readable roadmap view and external issue trackers are projections, not canonical state. This prevents platform body-size limits, child-item limits, label drift, or assignment semantics from corrupting the underlying decision model.

## Stable identity and reconstruction

Every roadmap and node receives a stable Qor identifier independent of tracker identifiers. Projections may store tracker backreferences, but membership and dependency reconstruction must remain possible from Qor state alone.

A fresh session should be able to:

1. load the objective and compact derived state;
2. identify the current frontier without loading every historical detail;
3. inspect only the selected node and its dependency/evidence neighborhood;
4. continue without re-asking settled decisions.

## Decision supersession

Resolved decisions are append-only historical facts.

When new evidence invalidates a prior decision:

```text
Decision A
status: superseded
superseded_by: Decision G
reason: <new evidence or changed constraint>
```

Downstream nodes that depended on the superseded decision are re-evaluated deterministically. The historical record remains visible.

This model should be reusable by other long-lived Qor decision surfaces after Roadmap proves it.

## Claim and interruption semantics

A claim is a lease, not permanent assignment.

Minimum lease fields:

```text
actor
session_id
claimed_at
scope
status
released_at or expires_at
```

An incomplete or interrupted session releases its lease when that state can be observed. Expiry/staleness handling must be deterministic and visible rather than silently hiding the node from the frontier forever.

External tracker assignment may mirror a lease, but it cannot define the lease.

## Frontier selection

Creation order is only a final tie-breaker. Roadmap should prefer nodes that most reduce uncertainty or unlock useful downstream work.

The first deterministic ranking contract is lexicographic, not an opaque learned score:

1. higher number of blocked downstream nodes;
2. higher unresolved-space reduction potential;
3. higher risk-reduction value;
4. closer dependency distance to implementation readiness;
5. lower estimated execution cost;
6. older creation sequence.

Where values are unknown, Roadmap records `unknown` rather than inventing precision. Ranking inputs and the resulting order must be inspectable.

## Research economy

Research fanout is capability- and cost-aware.

Recommended routing:

```text
recon / search             -> economical qualified model
source synthesis           -> medium reasoning tier
architecture inference     -> strong reasoning tier
consequential judgment     -> highest qualified tier
```

Before parallel research is dispatched, Roadmap checks whether branches overlap materially and deduplicates shared evidence needs. A parent agent should pass the minimum sufficient brief rather than cloning its entire context into every subagent.

## Implementation boundary

Roadmap may perform or delegate:

- research;
- evidence gathering;
- design exploration;
- operator questioning for authority-scoped decisions;
- non-production prerequisites;
- issue or environment inspection;
- state persistence and topology maintenance.

Roadmap may not make production implementation changes merely because an implementation node becomes actionable.

When an implementation node is ready, the legal next action is a Qor handoff, normally `/qor-plan`, followed by the existing S.H.I.E.L.D. chain.

## Skill invocation boundary

Roadmap is situational, not an always-required gate.

It should be directly invokable by the operator and routable by Qor when the request exhibits one or more strong signals:

- cannot responsibly fit in one planning session;
- material unresolved architecture or product decisions;
- multiple independent research branches;
- dependencies that make future work not yet specifiable;
- likely interruption or cross-session continuation;
- multiple implementation streams that require a shared decision substrate.

Host-specific invocation metadata is a compiler concern. The canonical Qor skill defines behavior and triggers without hardcoding one host's invocation mechanism.

## First implementation strategy

The implementation should be built as tracer-bullet waves rather than horizontal layers.

The first slice must prove one narrow end-to-end journey:

1. initialize a roadmap from an objective;
2. append nodes and blocking edges;
3. derive deterministic state from events;
4. compute an actionable frontier;
5. resolve a fact or decision node;
6. resume from a fresh process/session using only persisted state;
7. declare an implementation node ready;
8. emit the legal `/qor-plan` handoff without executing implementation.

Only after that path is green should the implementation deepen leases, supersession propagation, external projections, planning integration, and enterprise consumption.

## Enterprise extension boundary

The canonical Roadmap contract belongs in base Qor-logic.

Higher-tier enterprise orchestration may consume:

- roadmap readiness;
- frontier state;
- authority requirements;
- work leases;
- decision provenance;
- evidence pointers.

It must not fork a second Roadmap state model. Enterprise work-claim and governance machinery should adapt to the base contract once that contract is stable.

## Consequences

### Positive

- large work can remain honest about uncertainty without becoming plan-shaped fiction;
- cross-session resumption becomes a first-class behavior;
- operator attention is spent on decisions rather than discoverable facts;
- existing Qor skills remain single-purpose and composable;
- implementation cannot bypass S.H.I.E.L.D.;
- tracker integration becomes replaceable projection logic;
- decision history can support explicit supersession instead of silent mutation;
- deterministic state reduction creates a strong CI and evidence surface.

### Costs

- Qor gains a new persistent state family under `.qor/`;
- node and dependency schemas require versioning discipline;
- resumption, lease expiry, and supersession create non-trivial state-machine tests;
- host and tracker projections need careful separation from canonical state;
- the skill catalog gains another situational entry point, increasing discoverability pressure unless routing remains precise.

## Rejected alternatives

### Extend `/qor-plan` until it handles this use case

Rejected. It would complect decision discovery, long-horizon state navigation, and implementation planning. `/qor-plan` should consume sufficiently resolved decisions, not become the persistent workspace for every unresolved branch.

### Add Roadmap as a mandatory lifecycle phase

Rejected. Most work does not need it. Mandatory invocation would impose context and ceremony on changes that are already implementation-ready.

### Use the issue tracker as canonical Roadmap state

Rejected. Tracker limits and platform-specific semantics would become correctness constraints. Trackers are useful projections and collaboration surfaces, not the Qor state authority.

### Represent claims only as assignees

Rejected. Assignment does not encode session identity, interruption, expiry, or stale-claim recovery.

### Allow implementation directly from Roadmap

Rejected. It creates a second implementation path around the governance chain and weakens test, audit, and evidence guarantees.

### Select frontier nodes by creation order

Rejected. Creation time is not decision value. It remains only a deterministic tie-breaker.

## Admission criteria for implementation

Implementation may begin only when:

1. this ADR and the associated build roadmap have passed `/qor-audit`;
2. the first slice has explicit tests for event reduction, frontier calculation, resumption, and no-implementation handoff;
3. new canonical terms are added to the glossary in the same implementation phase as their executable consumers;
4. the delegation table is updated before skill-to-skill handoffs are wired;
5. no external tracker or repository is required for the base test suite;
6. the public-safe research provenance remains isolated to the permitted lessons-learned record.
