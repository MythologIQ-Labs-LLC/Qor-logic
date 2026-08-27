# Build Roadmap: Qor Roadmap

**Date:** 2026-08-27
**Status:** Design topology resolved enough for adversarial audit
**Architecture decision:** `docs/ADR_QOR_ROADMAP.md`
**Research provenance:** `docs/Lessons-Learned/2026-08-27-matt-pocock-skills-design-patterns.md`

This document intentionally uses the proposed Roadmap model to plan Roadmap itself. The purpose is to prove that the abstraction produces a clearer implementation strategy before we encode it as a skill.

## Objective

Deliver a Qor-native `/qor-roadmap` capability that can take a large, ambiguous, dependency-rich, or multi-session objective and make it implementation-ready without pretending unresolved decisions are implementation tasks and without bypassing S.H.I.E.L.D.

### Success conditions

1. A fresh session can reconstruct the objective, resolved decisions, unresolved nodes, dependencies, leases, and current actionable frontier from repository-local state.
2. Facts are researched by agents where lawful access exists; authority-scoped decisions are surfaced to the correct actor.
3. Independent frontier work can continue while unrelated nodes are blocked.
4. Historical decisions are not silently rewritten; supersession is explicit and downstream effects are recomputed.
5. Interrupted claims cannot permanently hide work from the frontier.
6. External trackers are optional projections rather than canonical state.
7. Production implementation is never performed by Roadmap; ready implementation work hands to `/qor-plan` and the existing lifecycle.
8. The base capability is host-neutral and can later be consumed by enterprise orchestration without a second state model.
9. Prompt and tool cost are measurable enough to compare Roadmap-assisted work against the current flow.

## Explicit exclusions

- Roadmap is not a replacement for GitHub Projects, Linear, or another project-management product.
- Roadmap is not a new mandatory S.H.I.E.L.D. phase.
- Roadmap does not manage deployment or release execution.
- Roadmap does not implement application code.
- The first release does not require network access or an external issue tracker.
- The first release does not attempt an ML-based priority score.
- The first release does not refactor the entire Qor prompt corpus in the same change.

## Resolved decisions

| ID | Decision | Resolution |
|---|---|---|
| D1 | Capability identity | Name it `/qor-roadmap`; do not reuse an external skill identity. |
| D2 | Lifecycle placement | Situational pre-S.H.I.E.L.D. on-ramp; not a mandatory phase. |
| D3 | Planning boundary | Roadmap resolves what must be known/decided; `/qor-plan` defines how resolved work will be implemented. |
| D4 | Canonical state | Repository-local append-only event history under `.qor/roadmaps/<id>/events.jsonl`. |
| D5 | Derived state | `state.json` is deterministic and rebuildable; it is not a second mutable authority. |
| D6 | Tracker boundary | External trackers and human-readable map views are projections only. |
| D7 | Decision history | Append-only with explicit `superseded_by` semantics. |
| D8 | Claim model | Session-aware work lease, not permanent assignee ownership. |
| D9 | Frontier order | Deterministic leverage-first lexicographic ranking; creation order only breaks final ties. |
| D10 | Research routing | Deduplicated, capability- and cost-aware fanout. |
| D11 | Production code | Never modified by Roadmap itself; implementation nodes hand to `/qor-plan`. |
| D12 | Enterprise boundary | Base Qor owns the contract; enterprise layers consume it after stabilization. |
| D13 | Delivery shape | Tracer-bullet waves with independently verifiable end-to-end behavior. |

## Unresolved space

These items are intentionally not blocking the first implementation slice because their correct shape depends on evidence from the core state engine.

### U1: External tracker projection protocol

Need evidence from the stable base schema before choosing the minimum projection contract for issue trackers. Avoid designing adapters around fields that may change during the first slice.

### U2: Cross-repository roadmap federation

Potentially valuable for enterprise programs, but base Roadmap should first prove one repository-local authority. Federation before stable identity and event semantics would multiply failure modes.

### U3: Long-term lease expiry policy

The data model must carry explicit timestamps and release state immediately. The default expiry duration, automatic reaping policy, and remote actor heartbeats can be chosen after real interruption tests.

### U4: General decision-supercession service

Roadmap should implement explicit supersession locally first. Generalizing it into a Qor-wide decision primitive is a later architectural decision once at least two real consumers exist.

### U5: Generalized experiment harness

The existing A/B skill is specialized. Roadmap evaluation needs a broader experiment surface, but the exact reusable abstraction should be designed from the first concrete Roadmap benchmarks rather than guessed up front.

## Dependency topology

```text
R1 Contract + schema
 |\
 | \-> R2 Event reducer + deterministic state
 |          |\
 |          | \-> R3 Frontier engine
 |          |          |
 |          |          v
 |          |      R5 Canonical skill journey
 |          |          |
 |          v          v
 |      R4 Resume + lease semantics
 |          |          |
 |          +----------+
 |                     |
 +----> R6 Delegation + /qor-plan handoff
                       |
                       v
                 R7 First-slice evaluation
                       |
          +------------+-------------+
          |                          |
          v                          v
     R8 Hardening                R9 Prompt mechanics
          |                          |
          v                          v
   R10 Tracker projection       R11 Planning/ideation integration
          \                          /
           \                        /
            +----> R12 Enterprise consumption
```

## Roadmap nodes

### R1: Contract and schema

**Kind:** prerequisite
**Blocked by:** none
**Status:** actionable

Define versioned schemas and pure domain types for:

- roadmap identity and objective;
- node identity, kind, status, authority requirement, and evidence pointers;
- dependency edges;
- unresolved-space entries;
- decision records and supersession;
- lease events;
- roadmap readiness.

**Completion evidence:** schema fixtures validate; invalid cycles, unknown node references, invalid state transitions, and malformed event payloads fail visibly.

### R2: Append-only reducer and derived state

**Kind:** implementation handoff
**Blocked by:** R1
**Status:** blocked

Build a pure reducer that consumes `events.jsonl` and produces deterministic Roadmap state. File I/O is kept behind a small adapter so tests exercise the same reducer used by the skill.

**Completion evidence:** identical event history always yields byte-stable canonical state; rebuilding `state.json` from events produces no semantic drift.

### R3: Actionable frontier engine

**Kind:** implementation handoff
**Blocked by:** R2
**Status:** blocked

Compute open, unblocked, legally actionable nodes and order them by the ADR's inspectable ranking contract.

The engine must expose why each node is or is not on the frontier.

**Completion evidence:** table-driven dependency graphs prove blocking, independent parallel readiness, tie-breaking, unknown ranking inputs, and reordering after a node resolves.

### R4: Resume and work-lease semantics

**Kind:** implementation handoff
**Blocked by:** R2
**Status:** blocked

Implement stable resumption and lease acquisition/release without making external assignment canonical.

**Completion evidence:** a simulated interrupted session leaves enough data for a fresh session to either resume or recover the lease according to explicit policy; no node disappears silently.

### R5: Canonical `/qor-roadmap` skill journey

**Kind:** implementation handoff
**Blocked by:** R3, R4
**Status:** blocked

Implement the smallest user-visible end-to-end journey:

1. initialize objective;
2. identify initial facts, decisions, prerequisites, unresolved space, and dependencies;
3. compute frontier;
4. resolve one ready node through the legal delegated skill or authority path;
5. persist the event;
6. reload compact state;
7. recompute frontier;
8. stop at implementation handoff.

The skill body orchestrates and delegates. It does not duplicate research, planning, audit, implementation, or persistence logic inline.

**Completion evidence:** an integration fixture can start a roadmap, resolve nodes across two simulated sessions, and finish with a `/qor-plan` handoff while proving no production implementation path exists.

### R6: Delegation table and planning boundary

**Kind:** prerequisite
**Blocked by:** R1, R5
**Status:** blocked

Update the delegation table before wiring cross-skill handoffs. Define when Roadmap may call research/ideation and when it must hand to `/qor-plan`.

Add canonical glossary entries in the same implementation phase as their first executable consumers.

**Completion evidence:** delegation lints and skill consistency tests prove Roadmap names legal successors instead of reinventing them.

### R7: First-slice evaluation

**Kind:** fact
**Blocked by:** R5, R6
**Status:** blocked

Run controlled scenarios comparing current Qor flow against Roadmap-assisted flow.

Initial scenarios:

1. large greenfield architecture decision with several independent research branches;
2. interrupted and resumed multi-session feature;
3. mixed factual uncertainty and human authority decisions.

Collect:

- operator questions asked;
- facts needlessly delegated to the operator;
- unresolved assumptions at `/qor-plan` handoff;
- duplicate research;
- frontier correctness;
- resume fidelity;
- abandoned/stale claims;
- contradicted decisions without supersession;
- context/token use;
- time to implementation-ready state;
- any S.H.I.E.L.D. bypass attempt.

**Completion evidence:** a reproducible evidence bundle shows where Roadmap improves or regresses the baseline.

### R8: State hardening

**Kind:** implementation handoff
**Blocked by:** R7
**Status:** blocked

Use first-slice evidence to harden:

- supersession propagation;
- stale-lease recovery;
- cycle handling;
- unresolved-space graduation;
- version migration;
- corrupt or partially written event handling;
- deterministic reconstruction checks.

**Completion evidence:** adversarial state-machine tests cover interrupted writes, stale projections, superseded prerequisites, and malformed histories.

### R9: Prompt-mechanics program

**Kind:** implementation handoff
**Blocked by:** R7
**Status:** blocked

Apply the broader design-corpus findings without tying them unnecessarily to Roadmap code.

Candidate work:

- context-pointer and progressive-disclosure audit;
- always-loaded description budget;
- observable completion criteria;
- verify-before-question sequencing;
- active-versus-passive domain-model discipline;
- design-divergence option for consequential architecture;
- deletion-test review for shallow wrapper skills;
- environment-focused process retrospective;
- fact/decision ownership rule.

This should be its own governed change stream rather than a side effect of Roadmap implementation.

### R10: External tracker projection

**Kind:** implementation handoff
**Blocked by:** R8, U1 resolution
**Status:** blocked

Add an adapter that can mirror selected state into a configured tracker while preserving Qor identity and reconstructibility.

A tracker outage, body limit, child-item limit, label drift, or assignment change must not corrupt canonical Roadmap state.

### R11: `/qor-plan` and `/qor-ideate` integration

**Kind:** implementation handoff
**Blocked by:** R7, R9
**Status:** blocked

Consume resolved Roadmap decisions without re-interviewing the operator. Where beneficial, adopt breadth-first questioning of independent ready decisions and design-divergence for consequential choices.

Do not turn `/qor-plan` into a second Roadmap state engine.

### R12: Enterprise consumption

**Kind:** implementation handoff
**Blocked by:** R8 and stable base contract
**Status:** blocked

In the enterprise extension repository, teach orchestration to consume Roadmap frontier, authority, lease, and readiness signals through the base contract.

No forked Roadmap implementation is permitted.

## Current actionable frontier

Only **R1: Contract and schema** is intentionally actionable for implementation.

That is the preferred first move because every later behavior depends on stable identities and legal state transitions. Starting with the skill prose, issue-tracker adapter, or enterprise integration would create interfaces before the state authority exists.

R1 should be executed through the normal Qor flow after this design package passes audit:

```text
/qor-plan
  -> /qor-audit
  -> /qor-implement
  -> /qor-substantiate
```

The implementing `/qor-plan` should use the next available phase number at execution time rather than reserving a chain of future phase numbers now.

## First tracer-bullet delivery wave

Although R1 is the first actionable node, the first **releaseable capability** should combine R1 through R6 as a narrow vertical slice after each prerequisite lands green.

### User-visible behavior

An operator can start a Roadmap for an objective, record a small dependency graph, resolve ready fact/decision nodes across sessions, inspect the current frontier, and receive a governed `/qor-plan` handoff when implementation becomes ready.

### Minimal implementation surfaces

Expected surfaces, subject to `/qor-plan` verification against the live tree:

- `qor/skills/sdlc/qor-roadmap/SKILL.md`
- `qor/scripts/roadmap_state.py` or equivalent pure state module
- `qor/scripts/roadmap_store.py` or equivalent I/O adapter
- schema under `qor/gates/schema/` or another existing canonical schema location selected by the implementation plan
- `qor/gates/delegation-table.md`
- `qor/references/glossary.md`
- skill catalog / feature inventory surfaces required by existing repository checks
- tests for schema, reducer, frontier, resumption, delegation, compilation/install parity, and implementation-boundary enforcement

Specific paths are hypotheses until `/qor-plan` verifies the current architecture. The plan should prefer existing seams over creating new ones.

## Build-wave policy

Each implementation wave must:

1. fit in a fresh context window where practical;
2. leave the repository green on its own;
3. have a concrete external behavior or deterministic contract that can be verified;
4. declare blocking relationships explicitly;
5. use expand-contract rather than forced vertical slicing for any wide compatibility migration;
6. update the delegation table before new cross-skill routing;
7. add glossary terms only with real consumers;
8. produce evidence sufficient to resume from a fresh session;
9. stop rather than silently implementing the next blocked node.

## Definition of Roadmap-ready for `/qor-plan`

This design program is ready to enter implementation planning when:

- the ADR is audited and not vetoed;
- R1 has no unresolved authority decision;
- no open question changes the identity or canonical-state model;
- the first red tests can be named before implementation begins;
- external tracker integration remains outside the first slice;
- the no-production-implementation boundary is testable;
- the lessons-learned research remains provenance, not runtime coupling.

At the time of this document, those conditions are satisfied except the required `/qor-audit` verdict.
