# Doctrine: Shadow Genome Graph

> A causal graph over governance events: any outcome can be traced back to its
> root cause through typed nodes and edges.

## Shadow Genome Graph

The **Shadow Genome Graph** (`qor.scripts.shadow_genome_graph`) is a Python
causal-graph layer over qor-logic's append-only shadow-event model. It persists
as append-only JSONL (one `{"op": "node"|"edge", ...}` line per operation) with
deterministic sequence ids (`n0`, `e0`, ...) so the graph is reproducible and
testable. Persistence path defaults to `.qor/genome.jsonl`, overridable via
`QOR_GENOME_PATH`.

### Node types

| Type | Purpose |
|------|---------|
| `checkpoint` | governance checkpoint (plan-complete, audit-pass, substantiation-gate) |
| `state` | workcell or module state change |
| `failure` | governance denial, audit failure, or error |
| `governance` | policy application or rule enforcement |
| `trust` | a CBT/KBT/IBT trust-level transition event (#213) |

### Edge types

| Type | Semantics |
|------|-----------|
| `produced` | source produced target |
| `occurred_during` | target happened during source's scope |
| `triggered_by` | target was triggered by source |
| `applies_to` | a governance decision applies to a target |

## Causal Chain

A **Causal Chain** is a path returned by `trace_chain(node_id)`, walking inbound
edges from a node back to its root(s). It is cycle-safe (a node already on the
current path is not revisited) and depth-limited via `max_depth`. `snapshot()`
returns node/edge counts + per-type distribution; `query()` filters nodes by
type and label. These give operators and `/qor-debug` / `/qor-remediate`
root-cause traceback over governance events.

## Scope boundary (qor-logic fit assessment; #139 -> #213)

The originating proposal (#139) targeted a consuming product with a governance
dashboard, so the trust-level / federation / maturity surfaces were originally
**declined** for qor-logic as infrastructure without a consumer. That premise
changed at #213: FailSafe (#196, shipped) is now the consumer, so those surfaces
are back in scope under an **emitter-API + derive** model -- qor-logic owns the
canonical schema + recorder methods and surfaces them in `to_dict`; it derives
failure-node maturity from its own data; trust-transitions + federation-peer
status are fed by the consumer's adapter through the API. The
`/api/qor/governance-dashboard` endpoint remains a consumer concern (qor-logic
ships data, not a web UI).

### Producer surfaces (#213, emitter-API + derive)

| Surface | API | `to_dict` key |
|---|---|---|
| Trust transitions | `record_trust_transition(from_level, to_level, *, triggering_evidence, governance_node_id, at)` | `trust_transitions` |
| Federation peers | `set_federation_peer(peer_id, *, name, state, last_sync, origin)` | `federation_peers` |
| Failure maturity | `annotate_failure_maturity(failure_node_id, *, classified, constraint_id, detector_id, enforced_by, verified_window)` + `derive_maturity_stage(...)` | `maturity` (on failure nodes) |

`TrustLevel` (CBT/KBT/IBT), `PeerState` (synced/syncing/stale/degraded/
incompatible/unauthorized/offline), and `MaturityStage` (observed -> classified
-> constraint_extracted -> detectable -> enforced -> verified) are closed enums.
All three remain strictly append-only: trust transitions are `trust` nodes with
edges; peer status and maturity are append-only ops with latest-wins derivation.

## Caveats

- **Strictly append-only**: nodes/edges are immutable once written; corrections
  are new nodes/edges, never mutations or deletions.
- **Unbounded growth**: full history grows without bound. V1 ships no automated
  retention/pruning; a retention policy is future work.

Maps to NIST AI RMF MAP-3.1 (trust anchor integrity) and EU AI Act Art. 12
(record-keeping integrity). Originating proposal: GH #139.
