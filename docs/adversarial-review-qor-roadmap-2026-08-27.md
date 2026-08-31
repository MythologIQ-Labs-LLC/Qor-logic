# Adversarial Review: Qor Roadmap and Design-Lessons Program

**Date:** 2026-08-27
**Scope:** `docs/ADR_QOR_ROADMAP.md`, `docs/roadmap-qor-roadmap-build-2026-08-27.md`, GH #373, GH #374
**Review type:** pre-implementation red-team pass, not a formal `/qor-audit` gate artifact
**Initial posture:** assume the proposals are duplicative, architecturally indulgent, and over-influenced by an external design corpus until Qor-specific evidence proves otherwise.

## Verdict

**Roadmap concept:** SURVIVES WITH MATERIAL REVISION.

**Current Roadmap implementation design:** VETO.

**Broad design-lessons program:** SURVIVES AS A RESEARCH UMBRELLA ONLY. Direct implementation from the umbrella is VETO.

The Roadmap solves a real gap only if it remains narrower than `/qor-ideate`, `/qor-research`, and `/qor-plan`. The current draft crosses that boundary in several places and front-loads infrastructure that has not earned its cost. The corrected v1 should be an operator-invoked, single-writer meta capability that owns only durable decision topology, frontier visibility, and legal handoff routing.

## Evidence baseline from current Qor

The review is grounded in existing Qor behavior rather than treating the proposed design as a blank slate.

- `/qor-ideate` already owns problem framing, assumptions, options, boundaries, readiness, and routing to research or planning.
- `/qor-plan` already requires project-context inspection, 2-3 alternative approaches, trade-off discussion, collaborative validation, and incremental implementation phases.
- `qor/gates/delegation-table.md` makes cross-skill delegation the single source of truth and explicitly forbids inline reinvention.
- `qor/references/doctrine-execution-continuity.md` already defines durable identity, claims, checkpoints, continuation, live-writer conflicts, and forbidden authority for execution continuity.
- `qor/scripts/shadow_process.py` already contains a cross-platform atomic JSONL append pattern with locking and validation.
- `/qor-process-review-cycle` already runs `corpus_consolidation_report`, `skill_size_budget_lint`, and `progressive_disclosure_lint` to counter prompt-corpus growth.
- `/qor-debug` already requires evidence-based root-cause analysis and a failing test before a fix, although it does not yet require a tight red-capable reproduction before hypothesis work.

Those existing mechanisms are the burden-of-proof baseline. A new Roadmap behavior must hide complexity that otherwise reappears across those surfaces, not merely rename existing work.

---

## Roadmap findings

### VETO R-A1: Roadmap currently owns work that Qor already delegates

The ADR currently says Roadmap may perform research, evidence gathering, design exploration, operator questioning, issue/environment inspection, and non-production prerequisites.

That is too much ownership for a meta-orchestrator. It conflicts with Qor's delegation rule: a skill that detects another skill's domain names and invokes that skill instead of reproducing its process.

**Failure mode:** Roadmap becomes a second `/qor-ideate` + `/qor-research` + partial `/qor-plan` under one durable wrapper.

**Mandated correction:**

Roadmap owns only:

1. objective and topology identity;
2. durable unresolved/resolved state;
3. dependency edges;
4. actionable-frontier derivation;
5. evidence and decision pointers;
6. routing to the legal Qor skill or authority actor;
7. plan-handoff readiness.

Fact resolution delegates to `/qor-research` when research is needed. Problem framing and option generation remain `/qor-ideate` or `/qor-plan` responsibilities. Roadmap records results and pointers; it does not reproduce their process.

**Disposition:** VETO until ADR ownership language is narrowed.

### VETO R-A2: The proposed build is horizontal, not a tracer bullet

The build roadmap labels delivery as tracer-bullet waves, but its current dependency chain is:

`schema -> reducer -> frontier engine -> resume/leases -> skill journey -> delegation`.

The first user-visible behavior appears only after several infrastructure layers exist. That is a horizontal platform build.

**Failure mode:** Qor spends multiple governed changes constructing an abstract state engine before proving that Roadmap improves one real workflow.

**Mandated correction:**

The first implementation unit must be one releaseable vertical pilot that includes only the minimum contract necessary to prove:

1. initialize one objective;
2. persist a few prerequisite nodes and edges;
3. derive an actionable frontier;
4. resolve one node through a legal delegate or authority path;
5. resume in a fresh agent context;
6. emit a legal `/qor-plan` handoff;
7. never implement production code.

The schema, reducer, store, skill body, and handoff behavior are internal parts of that single governed pilot, not separately released foundation projects.

**Disposition:** VETO on current R1-R6 sequencing.

### VETO R-A3: Work leases are unproven and duplicate existing continuity semantics

The v1 design introduces actor/session leases, expiry, release, stale-claim recovery, and claim visibility.

No v1 requirement demonstrates multiple independent canonical writers to one Roadmap. A single Roadmap orchestrator can remain single-writer while subagents return research results to the parent. With no canonical concurrent writers, a lease solves a problem the first release does not have.

Qor also already owns durable claim and live-writer semantics under execution continuity. Inventing a Roadmap-specific lease model risks a second claim vocabulary.

**Mandated correction:**

- v1 is single-writer;
- no work-lease schema in the first slice;
- interrupted work never hides a node because no claim removes it from the frontier;
- if multi-writer Roadmap operation is later demonstrated as necessary, evaluate reuse or extension of execution-continuity claim semantics before creating a second model.

**Disposition:** VETO for v1; EXPERIMENT FIRST for later concurrency.

### VETO R-A4: `state.json` is a cache without evidence that a cache is needed

The event history is already proposed as canonical. `state.json` adds a second persisted artifact plus stale/corrupt/rebuild semantics before event-volume evidence exists.

**Failure mode:** cache invalidation becomes implementation and test burden before Roadmap has enough events for reduction cost to matter.

**Mandated correction:**

v1 persists only the versioned append-only event history. State is reduced in memory on load. Add a materialized projection only after measured reconstruction cost justifies it.

**Disposition:** VETO for first slice; performance-triggered follow-up only.

### VETO R-A5: Supersession cannot deterministically re-decide downstream work

The current design says downstream nodes are re-evaluated deterministically when a decision is superseded.

A graph can deterministically identify affected descendants. It cannot deterministically decide whether their prior conclusions remain valid unless the validity rule is itself encoded as deterministic data. Most design decisions require reasoning or authority.

**Mandated correction:**

Supersession performs deterministic **invalidation propagation**:

- prior decision remains historical;
- replacement relation is explicit;
- descendants that depended on the superseded decision become `needs_review` or equivalent;
- re-resolution routes through the node's lawful resolver.

Do not claim automatic semantic re-evaluation.

**Disposition:** VETO on current wording and tests.

### VETO R-A6: Frontier ranking invents precision the state does not contain

The draft ranking includes unresolved-space reduction potential, risk-reduction value, distance to readiness, and estimated execution cost.

Several of those values would be LLM estimates. Recording `unknown` avoids fabrication but does not make the remaining numeric comparison meaningful. A deterministic algorithm over subjective inputs is still subjective.

**Mandated correction:**

v1 computes the **frontier set**, not an authoritative priority order.

It may expose graph-derived annotations such as:

- directly blocked dependent count;
- transitive dependent count;
- distance to an explicitly declared handoff condition;
- explicit operator priority if one was declared.

Automatic node selection or leverage ranking is deferred until controlled evaluation shows that it beats operator choice or simple graph-derived ordering.

**Disposition:** VETO for v1 ranking; EXPERIMENT FIRST later.

### VETO R-A7: The proposed `sdlc/qor-roadmap` placement contradicts the architecture

The ADR repeatedly says Roadmap is not an SDLC phase. The build roadmap nevertheless predicts `qor/skills/sdlc/qor-roadmap/SKILL.md`.

That path tells maintainers and tooling the opposite of the semantic decision.

**Mandated correction:**

Treat Roadmap as a program-level/meta capability. The implementation plan should evaluate `qor/skills/meta/qor-roadmap/` or the closest existing meta seam. It must not declare a new `phase: roadmap` gate stage in v1.

**Disposition:** VETO on SDLC placement.

### VETO R-A8: The plan-handoff contract is underspecified

`/qor-plan` already has prior-artifact checks. The current design says Roadmap hands to `/qor-plan` but does not state whether Roadmap becomes a legal prior gate artifact, whether it reuses ideation/research artifacts, or whether every handoff produces an override.

**Failure mode:** a supposedly governed on-ramp ends by creating systematic gate overrides.

**Mandated correction:**

For v1, Roadmap does not become a new gate phase. It must preserve the existing chain:

- if problem framing is absent, delegate to `/qor-ideate`;
- if factual research is required, delegate to `/qor-research`;
- Roadmap records pointers to those artifacts;
- before plan handoff, Roadmap verifies that the current Qor session has a legal ideation or research predecessor accepted by `/qor-plan`;
- if not, it stops and routes to the missing legal predecessor instead of creating an override.

A future Roadmap-specific predecessor contract requires a separate architecture decision.

**Disposition:** VETO until explicit.

### VETO R-A9: “Hard enforcement” of no implementation is stronger than the cross-host architecture can prove

A prompt can prohibit production writes. A generic Bash or Write tool can still perform them. Not every supported host offers command-level policy enforcement.

Qor should not state a cross-host hard guarantee it cannot mechanically verify.

**Mandated correction:**

Use a layered claim:

- canonical Roadmap procedure contains no production implementation step;
- Roadmap state mutation goes through the narrowest available deterministic Qor helper/CLI;
- canonical tool declarations omit production-edit tools where the host can enforce that distinction;
- tests prove no Roadmap instruction or helper performs production implementation;
- hosts with reliable pre-tool enforcement may add a stronger mechanical boundary;
- hosts without such a seam receive a disclosed structural, not absolute, guarantee.

**Disposition:** VETO on the word “hard” as a universal guarantee.

### REVISE R-A10: `implementation` is the wrong node kind

An `implementation` Roadmap node invites the Roadmap to become an implementation backlog and compete with `/qor-plan`.

**Mandated correction:**

Do not model implementation tasks in v1. A Roadmap reaches a **plan handoff** when a defined scope has no unresolved blocking prerequisites. The handoff is an output/pointer containing settled constraints and evidence, not a production task node.

If partial handoffs become necessary later, model them as named scopes or handoff records, not as implementation decomposition inside Roadmap.

**Disposition:** REVISE.

### REVISE R-A11: Model-tier routing does not belong in the Roadmap architecture

The ADR currently maps recon, synthesis, inference, and consequential judgment to model-cost tiers.

Roadmap should declare the required capability and delegate research. Existing Qor host/model capability routing owns model selection policy. Embedding tier advice in the Roadmap ADR creates drift as model economics change.

**Disposition:** remove the table from the architectural contract; retain “cost-aware, deduplicated research” as a delegated requirement.

### REVISE R-A12: Future tracker, prompt, and enterprise work is over-connected to #373

The current topology includes prompt-mechanics, tracker projection, `/qor-plan`/`/qor-ideate` integration, and enterprise consumption as downstream Roadmap nodes.

Those are separate programs. Keeping them in one Roadmap makes #373 effectively unfinishable and lets successful v1 delivery create implied commitments that have not passed their own burden of proof.

**Mandated correction:**

#373 closes when the evaluated base Roadmap pilot is complete. Tracker projection, automatic routing, enterprise consumption, and broad prompt mechanics become separate follow-up issues only if the pilot creates evidence for them.

**Disposition:** REVISE.

### SURVIVES R-S1: Append-only Roadmap history

The append-only history remains justified. Large cross-session decision work needs reconstructible history and explicit correction. A mutable tracker body is not sufficient authority.

**Constraint:** version the event contract from the first record and fail visibly on unsupported future versions. Use atomic append semantics proven elsewhere in Qor rather than casual file appends.

### SURVIVES R-S2: Stable Qor identity independent of tracker identity

This is necessary if trackers remain replaceable projections.

### SURVIVES R-S3: Facts and authority decisions are different node classes

This is a meaningful Qor distinction. The agent should establish lawful facts itself and surface only consequential decisions to the correct authority.

### SURVIVES R-S4: Explicit unresolved space

The distinction between “not yet specifiable” and “out of scope” is useful. In v1 it should remain lightweight metadata and must not receive fabricated priority scores.

### SURVIVES R-S5: Tracker independence

External trackers remain optional projections. No base correctness test may require a tracker or network service.

### SURVIVES R-S6: Roadmap must not implement production code

The boundary remains essential. The guarantee must be phrased at the level Qor can actually enforce per host.

---

## Corrected Roadmap v1 shape

```text
operator selects /qor-roadmap for genuinely long-horizon work
                    |
                    v
        existing ideation context present?
             | yes            | no
             |                v
             |           /qor-ideate
             |                |
             +----------------+
                    |
                    v
          Roadmap event history
        objective + prerequisite graph
                    |
             actionable frontier
              /             \
          fact                decision
           |                     |
     /qor-research          authority actor
              \             /
               \           /
                record result
                    |
           recompute frontier
                    |
          no blocking prereqs
          for plan-handoff scope
                    |
                    v
             /qor-plan
                    |
              existing SHIELD
```

v1 properties:

- operator-invoked only;
- meta capability, not SDLC phase;
- single canonical writer;
- append-only versioned event history only;
- no state cache;
- no leases;
- no external tracker;
- no automatic frontier ranking;
- deterministic graph impact, not semantic re-decision;
- no implementation task nodes;
- no automatic routing until evaluation.

---

## Corrected first implementation strategy

The current “R1 schema first” frontier is rejected. The first legal build target is one **vertical pilot**.

### Pilot P1: minimum viable Roadmap journey

One governed `/qor-plan -> /qor-audit -> /qor-implement -> /qor-substantiate` change should deliver the complete narrow journey.

Internal implementation phases may separate tests and code, but the capability is not considered shipped until the whole path works.

**Required behavior:**

1. Create a Roadmap with stable id and objective.
2. Append a small set of `fact`, `decision`, and `prerequisite` records plus dependency edges.
3. Rebuild current state deterministically from the event history.
4. Return all actionable nodes with graph-derived explanation.
5. Resolve one fact through a referenced research result or one decision through an authority record.
6. Start a fresh agent context and reconstruct the same current state from disk.
7. Determine that a named scope has no unresolved blockers.
8. Verify the legal ideation/research predecessor required by `/qor-plan` exists.
9. Emit a compact plan-handoff record containing pointers to settled decisions/evidence.
10. Stop and route to `/qor-plan`.

**Explicitly absent from P1:**

- work leases;
- concurrent canonical writers;
- `state.json` cache;
- external tracker projection;
- automatic frontier ranking;
- automatic model routing;
- automatic Roadmap invocation;
- enterprise integration;
- generalized supersession framework;
- broad prompt refactoring.

### Pilot P2: correction semantics

Only after P1 evaluation, add explicit decision supersession plus deterministic descendant invalidation to `needs_review`. Re-resolution remains delegated.

### Evaluation E1

Compare P1 against the current Qor baseline on fixed scenarios. Until E1 shows material benefit, Roadmap remains explicitly operator-invoked and experimental.

Minimum metrics:

- repeated operator questions;
- facts unnecessarily asked of the operator;
- unresolved assumptions at plan entry;
- duplicate research;
- resume fidelity;
- incorrect or missing frontier nodes;
- context/tool cost;
- time to an audit-ready `/qor-plan`;
- gate overrides caused by Roadmap;
- production-write attempts from Roadmap.

Only E1 may admit automatic routing, ranking, concurrency claims, tracker projection, or enterprise consumption into follow-up work.

---

## #374 design-lessons program findings

#374 contains useful ideas, but several overlap current Qor mechanisms. It must remain an umbrella for experiments, not an implementation issue.

| Candidate | Adversarial disposition | Reason |
|---|---|---|
| Prompt/context budgeting | **ABSORB + EXPERIMENT FIRST** | Process review already runs corpus size and progressive-disclosure tooling. Measure gaps before adding another program. |
| Verify before questioning | **SURVIVES** | Strong sequencing rule; pilot in Roadmap and planning without a new skill. |
| Facts vs decision authority | **SURVIVES** | Useful general rule, but generalize only after Roadmap proves the distinction in practice. |
| Multi-agent design divergence | **EXPERIMENT FIRST** | `/qor-plan` already proposes 2-3 approaches. Test whether independent agents materially improve diversity/quality enough to justify cost. |
| Deep-module/deletion-test lens | **EXPERIMENT FIRST** | Useful review heuristic; do not canonize new vocabulary or abstractions until it finds real shallow Qor modules. |
| Active domain-model discipline | **ABSORB** | Qor already has glossary integrity and `/qor-ideate`. Add only demonstrated missing behaviors, not a parallel domain-modeling skill. |
| Tight red-capable debug loop | **SURVIVES WITH REVISION** | `/qor-debug` already requires evidence and failing tests, but can be strengthened by requiring a red-capable reproduction before causal theory. Keep proactive QA concerns separate from GH #166. |
| Durable handoffs by pointer | **EXPERIMENT FIRST** | Measure resume fidelity and repeated-question reduction before doctrine. |
| Environment-focused retrospective | **ABSORB** | Extend `/qor-process-review-cycle`; do not create a second retrospective system. |
| Tracer-bullet / expand-contract planning | **EXPERIMENT FIRST** | `/qor-plan` already requires incremental phases. Compare vertical-slice guidance against current planning before changing doctrine. |
| Question-driven prototypes | **EXPERIMENT FIRST** | Useful when a real design question needs executable evidence; not enough evidence for a first-class skill. |
| Phase-boundary context transitions | **EXPERIMENT FIRST** | Context loss is host-sensitive. Measure resume fidelity before adding cross-host rules. |
| Mechanical authority enforcement | **ABSORB / HOST-SPECIFIC** | Qor already has authority/continuity semantics. Add host-specific enforcement only where a real tool-boundary seam exists. |

## #374 admission rule

No code or doctrine change is implemented directly from #374.

For each candidate, create a dedicated follow-up only when all are present:

1. named current-Qor behavior deficit;
2. baseline evidence;
3. smallest intervention that could fix it;
4. measurable target behavior;
5. overlap check against existing skills/scripts/doctrines;
6. experiment or deterministic test plan;
7. adversarial review.

This turns the external design corpus into hypotheses rather than authority.

---

## Required amendments before formal `/qor-audit`

- [ ] Narrow Roadmap ownership to topology/state/routing only.
- [ ] Move proposed skill placement out of `sdlc/`.
- [ ] Mark v1 operator-invoked only.
- [ ] Replace R1-R6 horizontal program with one vertical P1 pilot.
- [ ] Remove v1 work leases and concurrent-writer semantics.
- [ ] Remove v1 `state.json` cache.
- [ ] Remove model-estimated frontier ranking from v1.
- [ ] Replace semantic “re-evaluation” with deterministic descendant invalidation.
- [ ] Replace `implementation` node kind with a plan-handoff output boundary.
- [ ] Specify how Roadmap reaches `/qor-plan` without creating gate overrides.
- [ ] Downgrade universal “hard enforcement” claims to enforceable per-host properties.
- [ ] Remove model-tier selection from the Roadmap architectural contract.
- [ ] Remove #374 prompt work, tracker projection, and enterprise consumption from #373's blocking topology.
- [ ] Make #374 explicitly research-only with child issues admitted by evidence.

After those amendments, the design package is suitable for formal `/qor-plan` and `/qor-audit` against the implementation pilot. This document itself does not substitute for that gate.