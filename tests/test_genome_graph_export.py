"""Behavioral tests for Phase 134 (GH #164 export + #151 determination)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts import shadow_genome_graph as sgg


def _graph(tmp_path: Path) -> sgg.ShadowGenomeGraph:
    g = sgg.ShadowGenomeGraph(tmp_path / "genome.jsonl")
    a = g.add_node(sgg.GenomeNodeType.CHECKPOINT, "checkpoint-1")
    b = g.add_node(sgg.GenomeNodeType.FAILURE, "failure-1")
    g.add_edge(a, b, sgg.GenomeEdgeType.TRIGGERED_BY)
    return g


def test_to_dict_has_nodes_and_edges(tmp_path: Path) -> None:
    d = _graph(tmp_path).to_dict()
    assert len(d["nodes"]) == 2
    assert len(d["edges"]) == 1
    assert {n["label"] for n in d["nodes"]} == {"checkpoint-1", "failure-1"}
    assert d["edges"][0]["type"] == "triggered_by"


def test_to_json_roundtrips(tmp_path: Path) -> None:
    g = _graph(tmp_path)
    assert json.loads(g.to_json()) == g.to_dict()


def test_to_dot_contains_digraph_and_elements(tmp_path: Path) -> None:
    g = _graph(tmp_path)
    dot = g.to_dot()
    assert dot.lstrip().startswith("digraph")
    assert "->" in dot
    assert "checkpoint-1" in dot and "failure-1" in dot


def test_export_empty_graph(tmp_path: Path) -> None:
    g = sgg.ShadowGenomeGraph(tmp_path / "empty.jsonl")
    assert g.to_dict() == {"nodes": [], "edges": []}
    assert "digraph" in g.to_dot()  # valid empty digraph, no crash


def test_export_cli_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _graph(tmp_path)
    rc = sgg.main(["--path", str(tmp_path / "genome.jsonl"), "export", "--format", "json"])
    out = capsys.readouterr().out
    assert rc == 0
    assert json.loads(out)["nodes"]


def test_export_cli_dot(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _graph(tmp_path)
    rc = sgg.main(["--path", str(tmp_path / "genome.jsonl"), "export", "--format", "dot"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "digraph" in out


def test_roadmap_covers_all_five_capabilities() -> None:
    doc = Path("docs/shadow-genome-graph-roadmap.md").read_text(encoding="utf-8").lower()
    for cap in ("export", "dashboard", "trust", "federation", "retention"):
        assert cap in doc, f"roadmap missing capability decision: {cap}"
    assert "shipped" in doc  # export is marked shipped


def test_qor_compliance_determination_recorded() -> None:
    doc = Path("docs/research-brief-qor-compliance-provenance-2026-05-29.md").read_text(encoding="utf-8")
    assert "## Decision (GH #151 closed" in doc
    assert "qor-governance-compliance" in doc
