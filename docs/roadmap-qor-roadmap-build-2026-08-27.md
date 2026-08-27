# Build Roadmap: Qor Roadmap

**Date:** 2026-08-27
**Status:** Amended after pre-implementation adversarial review; formal `/qor-audit` required before implementation
**Architecture decision:** `docs/ADR_QOR_ROADMAP.md`
**Adversarial review:** `docs/adversarial-review-qor-roadmap-2026-08-27.md`
**Research provenance:** `docs/Lessons-Learned/2026-08-27-matt-pocock-skills-design-patterns.md`

## Why this roadmap changed

The original build topology proposed schema, reducer, frontier, lease/resume behavior, skill wiring, and delegation as sequential prerequisites. The adversarial pass rejected that structure because it front-loaded a platform before proving one useful Roadmap journey.

This amended roadmap treats the first release as one vertical experimental pilot. Internal code may still have a schema, reducer, store, and skill surface, but those are implementation details of one governed delivery, not separate releases or independent roadmap milestones.

## Objective

Prove that a narrow, Qor-native `/qor-roadmap` meta capability can preserve decision topology across agent contexts and produce a cleaner legal `/qor-plan` handoff than the current flow for genuinely long-horizon work.

The pilot must prove value without becoming a second ideation, research, planning, implementation, tracker, or execution-continuity system.

## v1 constraints locked by adversarial review

1. `/qor-roadmap` is a meta capability, not an SDLC phase.
2. v1 is operator-invoked only.
3. Roadmap owns topology, durable state, frontier derivation, pointers, and routing only.
4. Resolution work delegates to existing Qor skills or the correct authority actor.
5. v1 is single-writer.
6. Canonical state is one versioned append-only event history.
7. No materialized `state.json` cache ships in v1.
8. No Roadmap-specific leases, expiry, heartbeat, or assignment semantics ship in v1.
9. The frontier is a set with graph-derived annotations, not an automatically selected priority order.
10. Supersession propagates deterministic invalidation, not automatic semantic re-decision.
11. Roadmap has no implementation-task node type.
12. A Plan Handoff is an output boundary containing pointers to settled context, not an implementation plan.
13. Roadmap never manufactures a routine gate override to reach `/qor-plan`.
14. External tracker projection, enterprise consumption, broad prompt mechanics, and multi-writer claims are outside #373.
15. Automatic routing is not considered until evaluation proves benefit.

## Resolved design decisions

| ID | Decision | Resolution |
|---|---|---|
| D1 | Capability identity | `/qor-roadmap` |
| D2 | Classification | program-level meta capability |
| D3 | Invocation v1 | explicit operator invocation only |
| D4 | Core ownership | topology/state/frontier/routing only |
| D5 | Canonical state | `.qor/roadmaps/<id>/events.jsonl` |
| D6 | Writer model | single canonical writer in v1 |
| D7 | Derived state | in-memory reduction on load |
| D8 | Node kinds | `fact`, `decision`, `prerequisite` |
| D9 | Unknown future shape | lightweight unresolved-space metadata |
| D10 | Frontier | all legally actionable nodes, graph-derived explanation |
| D11 | Correction | append-only supersession + descendant `needs_review` invalidation |
| D12 | Planning transition | Plan Handoff output to `/qor-plan`; no implementation decomposition |
| D13 | Gate continuity | Roadmap preserves existing ideation/research predecessor requirements |
| D14 | Delivery | one vertical experimental pilot before hardening |

## Deferred questions that do not block the pilot

These are explicitly not v1 schema obligations.

### F1: Automatic routing

Does Roadmap produce enough benefit, with a low enough false-positive rate, to be auto-selected for some requests?

Decision waits for evaluation.

### F2: Frontier prioritization

Does graph-derived leverage ranking outperform presenting the frontier set to the operator/caller?

Decision waits for evaluation.

### F3: Multi-writer concurrency

Do real Roadmaps need multiple canonical writers rather than one orchestrator collecting subagent results?

If yes, evaluate existing execution-continuity claim semantics before designing a Roadmap-specific claim model.

### F4: Materialized projection cache

Does event reduction become expensive enough to justify a persisted `state.json` or other projection?

Decision requires measured reconstruction cost.

### F5: External tracker projection

Which subset of stable Roadmap state is useful to project into GitHub, Linear, or another tracker?

Decision waits for a stable base contract.

### F6: Enterprise consumption

Which base signals are actually needed by higher-tier orchestration?

Decision waits until the base pilot is stable and evaluated.

### F7: Partial plan handoffs

Does one active Roadmap need to emit several independent Plan Handoffs while the larger objective remains unresolved?

The architecture permits later named handoff scopes, but the first pilot proves one objective-to-one-handoff journey only.

## Corrected dependency topology

```text
A0 Amended design package
        |
        v
A1 Formal /qor-audit
        |
      PASS
        |
        v
P1 Vertical Roadmap pilot
        |
        v
E1 Baseline evaluation
        |
   +----+-------------------+
   |                        |
 material benefit       no material benefit
   |                        |
   v                        v
H1 correction hardening   simplify / stop
   |
   +------------------------------+
                                  |
                      evidence-admitted follow-ups only
```

There is deliberately no R1-R12 platform chain. Tracker, enterprise, prompt mechanics, ranking, concurrency, and cache work do not block or extend #373.

## Current actionable frontier

The current actionable item is **A1: formal `/qor-audit` of the amended design package**.

No production implementation node is actionable until that gate passes.

The pre-implementation red-team document is not a formal audit artifact and must not be used as one.

## P1: Minimum viable Roadmap journey

**Kind:** governed implementation plan after A1 PASS
**Goal:** prove one complete useful journey in one releaseable change

The implementing `/qor-plan` should use the next available phase number at execution time and structure its internal phases around tests-first delivery. It should not create separate governed releases for schema, reducer, store, and skill prose.

### User-visible behavior

An operator can explicitly invoke Roadmap for one long-horizon objective, preserve a small prerequisite graph across a fresh agent context, resolve one fact or decision through the correct Qor path, inspect what is actionable, and receive a legal `/qor-plan` handoff when all blockers for the pilot scope are resolved.

### Required end-to-end journey

1. **Initialize**
   - Create stable Roadmap identity.
   - Record objective, success conditions, exclusions, contract version.

2. **Map a minimal topology**
   - Add several `fact`, `decision`, and `prerequisite` nodes.
   - Add directed dependency edges.
   - Reject unknown references and cycles visibly.
   - Record one unresolved-space entry if the fixture needs it.

3. **Reconstruct**
   - Load events from disk.
   - Deterministically rebuild current state in memory.
   - Do not rely on a mutable cache.

4. **Derive frontier**
   - Return every unresolved node with all blockers resolved.
   - Explain blockers for nodes outside the frontier.
   - Surface graph-derived dependent counts as information only.
   - Do not auto-select a node.

5. **Resolve legally**
   - A factual node references a `/qor-research` result or other lawful evidence.
   - An authority decision records actor, decision, rationale, and evidence pointers.
   - A prerequisite records observable completion evidence.
   - The Roadmap writes only the resulting state event/pointer.

6. **Resume**
   - Start a fresh simulated agent context against the same repository state.
   - Load the same Roadmap without conversation history.
   - Recover objective, node status, dependencies, unresolved space, and frontier.
   - Do not re-ask a settled decision.

7. **Prepare Plan Handoff**
   - Determine that the pilot planning scope has no unresolved blockers.
   - Verify a legal ideation/research predecessor accepted by `/qor-plan` exists for the current Qor session.
   - If not, stop and route to the missing predecessor.
   - If yes, emit a compact handoff record with pointers to settled facts, decisions, constraints, evidence, and exclusions.

8. **Stop**
   - Name `/qor-plan` as the legal next action.
   - Do not modify production code.
   - Do not create implementation tasks inside Roadmap.

## P1 minimum persistence contract

```text
.qor/roadmaps/<roadmap-id>/events.jsonl
```

Required properties:

- append-only through the canonical Roadmap writer;
- first event declares contract version;
- unsupported future versions fail visibly;
- malformed events fail visibly;
- partial trailing/corrupt writes have explicit handling;
- writes use an atomic/locked pattern suitable for supported platforms;
- stable Roadmap and node ids do not depend on tracker ids;
- a replay over identical event history yields equivalent current state.

The implementation plan must inspect existing Qor atomic JSONL behavior before designing a second persistence primitive. Reuse or extraction is preferred only when it does not inflate the pilot's blast radius disproportionately.

## P1 expected implementation surfaces

These are hypotheses, not locked paths until `/qor-plan` verifies the live tree:

- `qor/skills/meta/qor-roadmap/SKILL.md` or the nearest valid meta location;
- a small pure Roadmap domain/reducer module;
- a narrowly scoped Roadmap store/CLI surface;
- one versioned Roadmap event schema or equivalent executable validator;
- `qor/gates/delegation-table.md` updates before routing is wired;
- `qor/references/glossary.md` entries only for terms with live consumers;
- help/catalog/compiler surfaces required by existing Qor checks;
- focused unit and integration tests.

The plan should not add a new Roadmap gate phase or require network/tracker access.

## P1 red-test inventory required before code

At minimum, the plan must bind these observable failures before implementation:

### Contract and storage

- malformed event rejected;
- unsupported future contract version rejected visibly;
- unknown node reference rejected;
- cycle-forming dependency rejected;
- atomic append preserves a valid prior history under simulated interrupted write behavior.

### Reduction and frontier

- identical event history produces equivalent state;
- unresolved blocker removes dependent from frontier;
- independent ready nodes remain simultaneously actionable;
- resolved node leaves the frontier;
- outside-frontier explanation names the actual unresolved blocker;
- no model-estimated field is required to compute frontier membership.

### Delegation and authority

- fact resolution records evidence pointer and does not substitute an operator answer when lawful research is required;
- authority decision cannot be recorded without required authority metadata;
- Roadmap routing names existing skills through the delegation table rather than reproducing their processes.

### Resume

- fresh simulated context reconstructs the same objective/topology/frontier from repository state;
- settled decisions are not re-requested;
- no conversation transcript is required for correctness.

### Plan handoff

- handoff fails closed when blocking nodes remain;
- handoff stops and routes to ideation/research if `/qor-plan`'s legal predecessor is absent;
- valid handoff contains pointers to settled context rather than a duplicated implementation plan;
- Roadmap helper/state writer cannot target a path outside its declared Roadmap state root;
- canonical Roadmap procedure terminates at `/qor-plan` and contains no production implementation step.

### Host/compiler compatibility

- canonical skill compiles/installs under supported hosts at the declared capability level;
- any host that cannot mechanically enforce a production-write restriction reports the weaker structural guarantee rather than claiming a hard boundary.

## P1 definition of done

The pilot is complete only when all are true:

- **D1:** one long-horizon objective can be resumed in a fresh agent context without reconstructing settled decisions from conversation history;
- **D2:** frontier membership is computed from explicit dependency state and is explainable;
- **D3:** resolution work delegates to existing Qor skills/authority rather than becoming inline Roadmap process;
- **D4:** a legal Plan Handoff reaches `/qor-plan` without a routine gate override and without production mutation;
- **D5:** the base suite requires no external tracker, external repository, or enterprise extension;
- **D6:** no work leases, materialized state cache, automatic ranking, automatic invocation, or implementation-task nodes have leaked into v1.

## E1: Baseline evaluation

P1 is experimental until compared against the current Qor path.

### Baseline

Use the existing Qor sequence appropriate to the fixture, normally:

```text
/qor-ideate -> /qor-research -> /qor-plan
```

Do not weaken the baseline by omitting capabilities Qor already has.

### Fixed scenarios

Use at least:

1. a large architecture objective with multiple independent factual branches;
2. a deliberately interrupted and resumed objective;
3. a mixed factual/authority objective in which one decision is blocked while another branch can proceed.

### Metrics

Collect:

- operator questions asked;
- questions whose answers were discoverable facts;
- unresolved assumptions at plan entry;
- duplicate evidence gathering;
- fresh-context resume fidelity;
- incorrectly included/excluded frontier nodes;
- gate overrides caused by the flow;
- context/token/tool cost;
- elapsed interaction steps to audit-ready plan;
- production-write attempts or illegal handoffs.

### Decision after E1

Classify each proposed follow-up independently:

- **SURVIVES:** evidence shows a meaningful Roadmap advantage;
- **REVISE:** benefit exists but implementation shape is wrong;
- **EXPERIMENT FIRST:** evidence insufficient;
- **REJECT:** cost/complexity exceeds demonstrated value.

E1 does not automatically admit all deferred features.

## H1: Correction hardening

Only if P1/E1 justify continued investment, add explicit decision supersession and deterministic descendant invalidation.

Required semantic:

```text
old decision remains historical
        |
        v
replacement relation appended
        |
        v
graph descendants identified
        |
        v
needs_review applied
        |
        v
lawful resolver re-evaluates
```

The graph determines impact. It does not claim to re-decide semantic validity.

## Follow-up admission policy

Automatic routing, ranking, multi-writer claims, projection cache, tracker projection, partial handoffs, and enterprise consumption each require a separate follow-up issue with:

1. evidence from P1/E1;
2. named current limitation;
3. smallest proposed intervention;
4. overlap check against existing Qor mechanisms;
5. measurable acceptance criteria;
6. adversarial review.

The broader design-lessons program remains GH #374 and is not in this build's blocking topology.

## Formal next action

The amended ADR and this roadmap should now enter formal `/qor-audit`.

A PASS admits a single `/qor-plan` for P1.

A VETO returns the design package for amendment. No implementation should begin from this document alone.