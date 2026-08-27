# Plan: Phase 238 — Experimental `/qor-roadmap` Vertical Pilot

**change_class**: feature

**doc_tier**: standard

**originating_issue**: GH #373

**design_authorities**:
- `docs/ADR_QOR_ROADMAP.md`
- `docs/adversarial-review-qor-roadmap-2026-08-27.md`
- `docs/roadmap-qor-roadmap-build-2026-08-27.md`

**governance_note**: The pre-implementation adversarial pass materially amended the design. This execution environment could not run the repository's executable `/qor-audit` lint ladder before implementation because it had no network path to obtain a local checkout. The operator explicitly authorized an experimental implementation pass. This branch therefore requires repository CI evidence and remains a prototype/pilot until a legal audited promotion path is satisfied; it does not fabricate a formal audit PASS.

**post-implementation correction**: Integration review caught one P2 capability, decision supersession, that had leaked into the P1 implementation despite the adversarial review explicitly deferring it until after pilot evaluation. The P1 contract was trimmed before closeout so the schema, reducer, CLI, skill, and tests expose no supersession behavior.

**boundaries**:
- limitations:
  - v1 is single-writer and operator-invoked only.
  - state is reconstructed in memory from one append-only event log.
  - frontier ordering exposes only graph-derived facts; it does not choose the next node.
- non_goals:
  - no Roadmap-specific leases, heartbeats, or concurrent writers.
  - no persisted `state.json` cache.
  - no tracker projection, automatic routing, enterprise integration, or model-tier routing.
  - no implementation-task nodes and no production implementation from Roadmap.
  - no decision supersession or descendant invalidation in P1.
- exclusions:
  - no new top-level CLI family; use existing `qor-logic scripts <module>` dispatch.
  - no canonical glossary promotion for experimental Roadmap vocabulary until the pilot evaluation earns it.

## Open Questions

None block the P1 pilot. Supersession, automatic invocation, multi-writer operation, tracker projection, and enterprise consumption remain evidence-gated follow-ups.

## Phase 1: Contract, state engine, and safe persistence

### Affected Files

- `qor/gates/schema/roadmap_event.schema.json` — versioned P1 event contract.
- `qor/scripts/roadmap_model.py` — P1 domain state and schema validation.
- `qor/scripts/roadmap_state.py` — pure reducer and dependency-cycle rejection.
- `qor/scripts/roadmap_store.py` — canonical `.qor/roadmaps/<id>/events.jsonl` storage with path confinement and atomic replacement.
- `qor/scripts/roadmap_view.py` — frontier derivation and plan-handoff readiness.
- `qor/scripts/roadmap_cli.py` — experimental operator surface through existing module dispatch.

### Changes

Implement one append-only Roadmap history with event kinds for Roadmap creation, nodes, dependencies, node resolution, unresolved-space state, and planning scopes.

The reducer MUST fail visibly on unsupported contract versions, malformed events, unknown references, duplicate identifiers, sequence gaps, dependency cycles, and illegal authority use.

The frontier returns the complete actionable set plus blockers, authority requirements, resolver metadata, and graph-derived dependent counts. It does not auto-select a winner.

Decision supersession is not part of P1. If evaluation earns it, it belongs to a later governed slice with its own contract and tests.

### Unit Tests

- `tests/test_roadmap_state.py` — event validation, cycle rejection, authority, frontier, and scope readiness.
- `tests/test_roadmap_store.py` — path confinement, malformed JSONL, reconstruction, interrupted atomic write.

## Phase 2: Delegation-first skill integration

### Affected Files

- `qor/gates/delegation-table.md` — declare Roadmap routing before skill wiring.
- `qor/skills/meta/qor-roadmap/SKILL.md` — thin meta skill that records topology and delegates resolution.
- `qor/skills/meta/qor-help/SKILL.md` — catalog entry.
- `docs/SKILL_REGISTRY.md` — registry entry.
- `tests/test_roadmap_skill_contract.py` — structural contract tying skill routing to the delegation table.

### Changes

Roadmap owns topology and routing only.

- missing problem framing → `/qor-ideate`;
- factual investigation → `/qor-research`;
- ready named planning scope → `/qor-plan`;
- production implementation is never a Roadmap action.

The skill invokes `qor-logic scripts roadmap_cli` for state operations. It does not inline another skill's process.

### Unit Tests

- Delegation rows exist before skill routing is admitted.
- The skill is `phase: meta`, user-invocable, and contains no implementation execution step.
- The skill routes facts, framing, and planning to their existing owners.

## Phase 3: End-to-end pilot and feature inventory

### Affected Files

- `tests/test_roadmap_cli.py` — two-context behavioral journey.
- `docs/FEATURE_INDEX.md` — experimental Roadmap surface, verified only after behavioral coverage exists.
- `qor/gates/SCHEMA_REGISTRY.json` — event schema registration.

### Changes

Prove one vertical journey:

1. initialize objective;
2. add fact + decision + prerequisite topology;
3. derive initial frontier;
4. resolve a fact with evidence;
5. expose an authority decision only when the required authority is available;
6. reconstruct state from disk in a fresh load;
7. create a named planning scope;
8. fail handoff while blockers remain;
9. accept a valid `research.json` or `ideation.json` predecessor;
10. emit a compact `/qor-plan` handoff containing settled-context pointers and no implementation task list.

### Unit Tests

- `tests/test_roadmap_cli.py::test_vertical_pilot_across_fresh_loads`
- `tests/test_roadmap_cli.py::test_handoff_fails_without_legal_predecessor`
- `tests/test_roadmap_cli.py::test_handoff_fails_while_scope_blocked`

## Feature Inventory Touches

| FEATURE_INDEX entry | Operation | Test descriptor |
|---|---|---|
| FX026 `qor-logic scripts roadmap_cli` | NEW | `tests/test_roadmap_cli.py`: persisted topology survives fresh loads, derives the correct frontier, and emits only a legal `/qor-plan` handoff after prerequisites resolve. |

## Definition of Done

### Deliverable: Roadmap P1 vertical pilot

- **D1**: Operator can preserve long-horizon prerequisite topology and resume it without conversation history.
- **D2**: Versioned JSONL contract, pure reducer, safe store, module-dispatch CLI, and meta skill exist behind current Qor seams.
- **D3**: Delegation remains authoritative; Roadmap cannot become a second research/planning/implementation owner.
- **D4**: Behavioral tests prove cycle rejection, authority gating, fresh-load reconstruction, frontier correctness, and legal plan handoff.
- **D5**: P2 supersession remains absent until evaluation evidence admits it.

## CI Commands

- `python -m pytest tests/test_roadmap_state.py tests/test_roadmap_store.py tests/test_roadmap_cli.py tests/test_roadmap_skill_contract.py -q` — Roadmap pilot behavior.
- `python -m pytest -q` — repository regression suite.
- `python -m ruff check qor tests` — Pyflakes gate.
- `python qor/scripts/check_variant_drift.py` — canonical/compiled host parity.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` — ledger integrity.

## Implementation stop condition

Phase 238 stops after the narrow vertical pilot is green in CI. It does not proceed into supersession, ranking, caching, leases, trackers, automatic routing, or enterprise consumption. Those require evaluation evidence and separate admission.
