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

## Scope boundary (qor-logic fit assessment; #139)

The originating proposal targets a consuming product with a governance
dashboard. For qor-logic, only the **core causal layer** above is in scope. The
following are **DECLINED for qor-logic** — they realize their advantage in a
consuming product/UI that this repo does not have, so building them here would
be infrastructure without a consumer:

- Governance dashboard API (`/api/qor/governance-dashboard`).
- CBT/KBT/IBT trust-level transitions.
- Cross-module federation gossip / centralized graph store.

This is a deliberate, honest scope decision (not a deferral with intent): the
causal-traceback shape translates to Python and is retained; the dashboard /
trust-level / federation vision belongs to a consumer.

## Caveats

- **Strictly append-only**: nodes/edges are immutable once written; corrections
  are new nodes/edges, never mutations or deletions.
- **Unbounded growth**: full history grows without bound. V1 ships no automated
  retention/pruning; a retention policy is future work.

Maps to NIST AI RMF MAP-3.1 (trust anchor integrity) and EU AI Act Art. 12
(record-keeping integrity). Originating proposal: GH #139.
