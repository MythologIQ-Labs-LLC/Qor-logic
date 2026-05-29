# Plan: Phase 113 - Shadow Genome causal-graph layer (#139)

**change_class**: feature

**doc_tier**: system

**terms_introduced**:
- term: Shadow Genome Graph
  home: qor/references/doctrine-shadow-genome-graph.md
- term: Causal Chain
  home: qor/references/doctrine-shadow-genome-graph.md

**boundaries**:
- limitations: V1 ships a Python causal-graph layer (typed nodes + typed edges + trace_chain / snapshot / query over append-only JSONL) usable by operators and skills for root-cause traceback. It is a library + CLI; it does not auto-instrument existing gate writes.
- non_goals: The proposal's governance dashboard API, CBT/KBT/IBT trust-level transitions, and cross-module federation gossip are DECLINED for qor-logic (not deferred): they realize their advantage in a consuming product/UI, which qor-logic's Python governance tooling does not have. See Locked Decisions for the fit assessment.
- exclusions: No mutation/amendment of nodes (strictly append-only). No retention/pruning automation in V1 (documented as a known unbounded-growth caveat).

## Open Questions

None. The proposal's three open questions are resolved by the fit assessment + convention (strictly append-only; retention is a documented caveat not automated in V1; federation is declined for qor-logic).

## Locked Decisions (fit assessment per operator guidance)

- **LD1 (build the core)**: the causal-graph SHAPE translates cleanly to Python over qor-logic's existing append-only shadow-event model. Typed nodes (`checkpoint`/`state`/`failure`/`governance`), typed edges (`produced`/`occurred_during`/`triggered_by`/`applies_to`), `trace_chain`, `snapshot`, `query`, append-only JSONL. Delivers operator + `/qor-debug` + `/qor-remediate` root-cause traceback. Worth building.
- **LD2 (decline the consumer-stack vision)**: the governance dashboard API (`/api/qor/governance-dashboard`), CBT/KBT/IBT trust-level transitions, and federation gossip are DECLINED for qor-logic. Their advantage is realized by a consuming product/UI; in qor-logic they would be infrastructure without a consumer. This is the honest "may not deliver the advantages within the Python framework" outcome the operator authorized accepting — scoped precisely to those three surfaces, while the core causal layer is retained because it does deliver.
- **LD3 (determinism)**: node/edge IDs are deterministic sequence ids (`n0`, `n1`, ... / `e0`, ...) persisted in the JSONL; no wall-clock or randomness in id derivation, so the graph is reproducible and testable. Persistence path defaults to `.qor/genome.jsonl`, overridable via `QOR_GENOME_PATH`.

## Context

#139 proposes upgrading the flat shadow-event log into a causal graph for root-cause traceback / audit replay / drift snapshots. The TypeScript PoC (`evidence/shadow-genome.ts`, 22 tests) targets a consuming dashboard. This phase ports the fitting core to Python and declines the consumer-specific surfaces.

## Feature Inventory Touches

Empty. Governance tooling + doctrine; no `src/` user-touchable product feature surface.
`feature_inventory_touches`: `[]`.

## Phase 1: Shadow Genome Graph library

### Affected Files

- `tests/test_shadow_genome_graph.py` - NEW. Behavioral tests: node/edge creation, multi-hop + branching + depth-limited trace_chain, cycle safety, snapshot counts, query filters, JSONL persistence round-trip.
- `qor/scripts/shadow_genome_graph.py` - NEW. `GenomeNodeType` / `GenomeEdgeType` enums; `ShadowGenomeGraph` with `add_node`, `add_edge`, `trace_chain`, `snapshot`, `query`; append-only JSONL load/save with an in-memory inbound/outbound adjacency index.

### Changes

`ShadowGenomeGraph(path)` loads append-only JSONL ops (one `{"op":"node"|"edge", ...}` per line) and rebuilds adjacency. `add_node(type, label, metadata) -> id` and `add_edge(src, tgt, type, metadata) -> id` append a line and update the index; ids are deterministic sequence ids (LD3). `trace_chain(node_id, max_depth=None) -> list[list[str]]` walks INBOUND edges to root(s), cycle-safe, depth-limited, returning causal paths. `snapshot() -> dict` returns node/edge counts + per-type distribution. `query(node_type=None, label_contains=None) -> list[node]`. CLI: `python -m qor.scripts.shadow_genome_graph --path <p> {snapshot|trace <id>|query --type <t>}`.

### Unit Tests

- `test_shadow_genome_graph.py::test_add_node_returns_deterministic_id` - two graphs built with the same op sequence yield identical ids.
- `::test_trace_chain_multi_hop` - A produced B produced C; `trace_chain(C)` returns a path back to A.
- `::test_trace_chain_branching` - C has two inbound roots; trace returns both chains.
- `::test_trace_chain_depth_limited` - `max_depth=1` truncates the path.
- `::test_trace_chain_cycle_safe` - an A<->B cycle terminates (no infinite loop) and returns a bounded path.
- `::test_snapshot_counts_by_type` - snapshot returns correct node/edge totals + per-type counts.
- `::test_query_filters_by_type_and_label` - query returns only matching nodes.
- `::test_jsonl_persistence_round_trip` - a graph reloaded from its JSONL has identical nodes/edges/adjacency.

## Phase 2: doctrine + glossary

### Affected Files

- `tests/test_shadow_genome_graph_doctrine.py` - NEW. Asserts the doctrine defines the node/edge type registries + the causal-chain contract + the explicit qor-logic scope boundary (declined surfaces), and the glossary carries the two terms.
- `qor/references/doctrine-shadow-genome-graph.md` - NEW. The causal-graph model (node/edge types, trace semantics, append-only + deterministic-id contract) AND the fit-assessment scope boundary: dashboard / trust-levels / federation declined for qor-logic with rationale; retention-growth caveat.
- `qor/references/glossary.md` - AMENDED. Add `Shadow Genome Graph`, `Causal Chain`.

### Unit Tests

- `test_shadow_genome_graph_doctrine.py::test_doctrine_defines_types_and_scope_boundary` - parser asserts all four node types + four edge types are named AND the declined-surfaces scope boundary is stated.
- `::test_glossary_has_graph_terms` - the two terms exist with `home` set to the doctrine.

## Definition of Done

### Deliverable D-113.1: causal-graph library
- **D1**: A Python causal-graph layer gives root-cause traceback over typed governance nodes/edges.
- **D2**: `qor/scripts/shadow_genome_graph.py` with the enums + `add_node`/`add_edge`/`trace_chain`/`snapshot`/`query` + CLI; append-only JSONL; deterministic ids.
- **D3**: Append-only + deterministic-id contract documented.
- **D4**: `tests/test_shadow_genome_graph.py` passes all eight cases.

### Deliverable D-113.2: doctrine + honest scope boundary
- **D1**: Doctrine defines the model and explicitly declines the dashboard / trust-level / federation surfaces for qor-logic with rationale.
- **D2**: `doctrine-shadow-genome-graph.md` NEW; two glossary terms added.
- **D3**: Retention-growth caveat stated.
- **D4**: `tests/test_shadow_genome_graph_doctrine.py` passes.

## CI Commands

- `python -m pytest tests/test_shadow_genome_graph.py -q` - causal-graph library.
- `python -m pytest tests/test_shadow_genome_graph_doctrine.py -q` - doctrine + glossary.
- `python -m pytest tests/ -q` - full regression.
- `python -m qor.scripts.plan_text_consistency_lint --check docs/plan-qor-phase113-shadow-genome-graph.md` - plan-internal consistency.
- `python -m qor.scripts.dod_check --plan docs/plan-qor-phase113-shadow-genome-graph.md` - Definition of Done declaration check.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - ledger chain integrity.

## CI Coverage Exemptions

- `test_packaging_install` - packaging integration smoke; orthogonal.
- `gate_chain_completeness` - sealed-phase chain audit; runs every PR.
- `dependency_admission_lint` - dependency cooling-period check; no dependency changes here.
- `check_variant_drift` - no source-skill prompt changes in this phase; variants unaffected.
