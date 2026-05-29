"""Phase 113 (#139): Shadow Genome causal-graph library behavioral tests."""
from __future__ import annotations

from qor.scripts.shadow_genome_graph import (
    GenomeEdgeType,
    GenomeNodeType,
    ShadowGenomeGraph,
)


def _g(tmp_path, name="genome.jsonl"):
    return ShadowGenomeGraph(tmp_path / name)


def test_add_node_returns_deterministic_id(tmp_path):
    g1 = _g(tmp_path, "a.jsonl")
    g2 = _g(tmp_path, "b.jsonl")
    id1 = g1.add_node(GenomeNodeType.CHECKPOINT, "plan-complete")
    id2 = g2.add_node(GenomeNodeType.CHECKPOINT, "plan-complete")
    assert id1 == id2 == "n0"


def test_trace_chain_multi_hop(tmp_path):
    g = _g(tmp_path)
    a = g.add_node(GenomeNodeType.CHECKPOINT, "A")
    b = g.add_node(GenomeNodeType.STATE, "B")
    c = g.add_node(GenomeNodeType.STATE, "C")
    g.add_edge(a, b, GenomeEdgeType.PRODUCED)
    g.add_edge(b, c, GenomeEdgeType.PRODUCED)
    assert g.trace_chain(c) == [[a, b, c]]


def test_trace_chain_branching(tmp_path):
    g = _g(tmp_path)
    a = g.add_node(GenomeNodeType.CHECKPOINT, "A")
    b = g.add_node(GenomeNodeType.CHECKPOINT, "B")
    c = g.add_node(GenomeNodeType.FAILURE, "C")
    g.add_edge(a, c, GenomeEdgeType.TRIGGERED_BY)
    g.add_edge(b, c, GenomeEdgeType.TRIGGERED_BY)
    chains = g.trace_chain(c)
    assert [a, c] in chains and [b, c] in chains
    assert len(chains) == 2


def test_trace_chain_depth_limited(tmp_path):
    g = _g(tmp_path)
    a = g.add_node(GenomeNodeType.CHECKPOINT, "A")
    b = g.add_node(GenomeNodeType.STATE, "B")
    c = g.add_node(GenomeNodeType.STATE, "C")
    g.add_edge(a, b, GenomeEdgeType.PRODUCED)
    g.add_edge(b, c, GenomeEdgeType.PRODUCED)
    # depth 1 from C reaches B but not A
    assert g.trace_chain(c, max_depth=1) == [[b, c]]


def test_trace_chain_cycle_safe(tmp_path):
    g = _g(tmp_path)
    a = g.add_node(GenomeNodeType.STATE, "A")
    b = g.add_node(GenomeNodeType.STATE, "B")
    g.add_edge(a, b, GenomeEdgeType.PRODUCED)
    g.add_edge(b, a, GenomeEdgeType.PRODUCED)  # cycle
    chains = g.trace_chain(b)  # must terminate
    assert chains == [[a, b]]


def test_snapshot_counts_by_type(tmp_path):
    g = _g(tmp_path)
    a = g.add_node(GenomeNodeType.CHECKPOINT, "A")
    b = g.add_node(GenomeNodeType.FAILURE, "B")
    g.add_edge(a, b, GenomeEdgeType.TRIGGERED_BY)
    snap = g.snapshot()
    assert snap["nodes"] == 2 and snap["edges"] == 1
    assert snap["node_types"] == {"checkpoint": 1, "failure": 1}
    assert snap["edge_types"] == {"triggered_by": 1}


def test_query_filters_by_type_and_label(tmp_path):
    g = _g(tmp_path)
    g.add_node(GenomeNodeType.GOVERNANCE, "gate-block-plan")
    g.add_node(GenomeNodeType.GOVERNANCE, "gate-allow-implement")
    g.add_node(GenomeNodeType.STATE, "gate-state")
    gov = g.query(node_type=GenomeNodeType.GOVERNANCE)
    assert len(gov) == 2
    blocks = g.query(node_type=GenomeNodeType.GOVERNANCE, label_contains="block")
    assert len(blocks) == 1 and blocks[0].label == "gate-block-plan"


def test_jsonl_persistence_round_trip(tmp_path):
    g = _g(tmp_path)
    a = g.add_node(GenomeNodeType.CHECKPOINT, "A", {"phase": "plan"})
    b = g.add_node(GenomeNodeType.STATE, "B")
    g.add_edge(a, b, GenomeEdgeType.PRODUCED, {"why": "test"})
    reloaded = ShadowGenomeGraph(g.path)
    assert set(reloaded.nodes) == {a, b}
    assert len(reloaded.edges) == 1
    assert reloaded.trace_chain(b) == [[a, b]]
    assert reloaded.nodes[a].metadata == {"phase": "plan"}
