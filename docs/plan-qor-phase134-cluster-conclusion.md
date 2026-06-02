# Plan: Cluster conclusion — Shadow Genome graph export + roadmap decision (#164) + qor-compliance determination (#151)

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Concludes the last two #147 follow-ons. **#164**: of the five declined production-hardening capabilities, **export** is the one cheap + aligned with "Qor-logic proper", so it ships now — `ShadowGenomeGraph.to_dict/to_json/to_dot` + an `export` CLI subcommand; the other four (dashboard/query-API surface, trust-transition modeling, cross-workspace federation, retention/pruning) are evaluated and **deferred post-1.0** with rationale in a roadmap doc (they are SaaS-grade surfaces a governance-skills package does not need to be 1.0-complete). **#151**: records the determination (Option c) that `qor-compliance` is a FailSafe-owned artifact absent from Qor-logic — not retire/fix here; `qor-governance-compliance` is the in-repo compliance skill (already provenance-fixed Phase 81); no duplicate is created.
- non_goals: Building the four deferred #164 capabilities (documented roadmap, not implemented — they remain post-1.0); creating a `qor-compliance` skill (would duplicate `qor-governance-compliance`, violating #151's no-duplicate guarantee); spawning new open issues (the deferrals are a roadmap doc, not new trackers, so the cluster closes).
- exclusions: No change to FailSafe's bundled `qor-compliance` (not this repo's artifact).

## Open Questions

None. #164 export is the implementable subset; the heavier four are documented roadmap (operator can re-prioritize post-1.0). #151 resolved Option (c) per operator decision (2026-06-02) + the existing research brief + grep evidence.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Touches `qor/scripts` + docs + tests.)

- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_genome_graph_export.py` · test_descriptor: `ShadowGenomeGraph.to_dict/to_json/to_dot export the built nodes+edges (valid JSON round-trips node/edge counts; DOT contains a digraph + each node and edge), and the export CLI subcommand prints the chosen format; the roadmap doc records a decision for all five #164 capabilities + the #151 determination`

## Phase 1: Graph export (#164 accepted capability) — `qor/scripts/shadow_genome_graph.py`

### Affected Files

- `tests/test_genome_graph_export.py` - NEW. Behavioral export tests (see Unit Tests). Written first; red before the methods exist.
- `qor/scripts/shadow_genome_graph.py` - add `to_dict`, `to_json`, `to_dot` to `ShadowGenomeGraph`; add an `export` subcommand to `main` (`--format json|dot`).

### Changes

```python
def to_dict(self) -> dict:
    """{'nodes': [{id,type,label,metadata}...], 'edges': [{id,source,target,type,metadata}...]}"""
def to_json(self, indent: int = 2) -> str:
    """json.dumps(self.to_dict(), indent=indent)"""
def to_dot(self) -> str:
    """Graphviz: digraph { "<id>" [label="<label>"]; "<src>" -> "<tgt>" [label="<type>"]; }"""
# main: add subparser `export` with --format {json,dot} (default json); prints to stdout.
```

De-complecting: `to_dict` is the single source; `to_json`/`to_dot` render from it. Pure (no I/O beyond the existing load).

### Unit Tests

- `tests/test_genome_graph_export.py::test_to_dict_has_nodes_and_edges` - build a graph (2 nodes + 1 edge via the existing add_node/add_edge API); `to_dict()` has `len(nodes)==2`, `len(edges)==1`, with the id/type/label fields.
- `::test_to_json_roundtrips` - `json.loads(g.to_json())` equals `g.to_dict()` (valid JSON; counts preserved).
- `::test_to_dot_contains_digraph_and_elements` - `to_dot()` starts a `digraph`, contains each node id and a `->` edge line.
- `::test_export_cli_json` / `::test_export_cli_dot` - `main(["--path", <jsonl>, "export", "--format", "json"|"dot"])` returns 0 and prints the format (capsys).
- `::test_export_empty_graph` - export of an empty graph yields `{"nodes": [], "edges": []}` / an empty `digraph` (no crash).

## Phase 2: Roadmap decision (#164) + qor-compliance determination (#151)

### Affected Files

- `tests/test_genome_graph_export.py` - add the roadmap/determination doc-contract tests.
- `docs/shadow-genome-graph-roadmap.md` - NEW. Records the decision for each of the five #164 capabilities: `export` = SHIPPED (Phase 134); `dashboard/query-API`, `trust-transition modeling`, `cross-workspace federation`, `retention/pruning` = DEFERRED post-1.0, each with a one-paragraph rationale (why a governance-skills package does not need it to be 1.0-complete + what would trigger revisiting). Also records the #151 determination.
- `docs/research-brief-qor-compliance-provenance-2026-05-29.md` - append a `## Decision (GH #151 closed, 2026-06-02)` section finalizing Option (c): qor-compliance is FailSafe-owned/absent from Qor-logic; `qor-governance-compliance` is the canonical in-repo compliance skill; no duplicate created; F244/FX359 belongs to FailSafe's bundle.

### Changes

The roadmap doc is the durable #164 artifact (decision, not deferral-to-a-new-issue, so the cluster closes). The research-brief decision section finalizes #151. Both are documentary; the seal entry records both closures.

### Unit Tests

- `tests/test_genome_graph_export.py::test_roadmap_covers_all_five_capabilities` - read `shadow-genome-graph-roadmap.md`; assert it names all five (`export`, `dashboard`, `trust`, `federation`, `retention`) and marks `export` shipped.
- `::test_qor_compliance_determination_recorded` - read the research brief; assert it contains the `## Decision (GH #151 closed` section naming Option (c) / `qor-governance-compliance`.

## Definition of Done

### Deliverable: cluster conclusion

- **D1**: the Shadow Genome graph can be exported (json/dot) via API + CLI; the four heavier capabilities have a documented post-1.0 roadmap decision; the qor-compliance question has a recorded Option-(c) determination.
- **D2**: `to_dict`/`to_json`/`to_dot` + `export` CLI in `shadow_genome_graph.py`; `docs/shadow-genome-graph-roadmap.md`; the research-brief decision section.
- **D3**: META_LEDGER seal entry recording both #164 + #151 closures; version bump.
- **D4**: `tests/test_genome_graph_export.py::test_to_json_roundtrips` + `::test_to_dot_contains_digraph_and_elements` + `::test_roadmap_covers_all_five_capabilities` + `::test_qor_compliance_determination_recorded`.

## CI Commands

- `python -m pytest tests/test_genome_graph_export.py tests/test_shadow_genome_graph.py -q` — export + existing graph tests (no regression).
- `python -m qor.cli scripts shadow_genome_graph export --format json` — exports the live genome graph (advisory).
- `python -m pytest -q` — full suite green before substantiate.
