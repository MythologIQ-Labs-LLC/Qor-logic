"""Phase 152 (GH #213): Shadow Genome failure-node learning maturity.

Append-only maturity annotations on failure nodes + a pure stage-derivation
(Observed -> Classified -> Constraint extracted -> Detectable -> Enforced ->
Verified), surfaced on failure nodes in to_dict.
"""
from __future__ import annotations

import pytest

from qor.scripts.shadow_genome_graph import (
    GenomeNodeType,
    MaturityStage,
    ShadowGenomeGraph,
    derive_maturity_stage,
)


def _g(tmp_path):
    return ShadowGenomeGraph(tmp_path / "genome.jsonl")


def test_derive_stage_ladder():
    assert derive_maturity_stage({}) == MaturityStage.OBSERVED
    assert derive_maturity_stage({"classified": True}) == MaturityStage.CLASSIFIED
    assert derive_maturity_stage({"classified": True, "constraint_id": "c1"}) == MaturityStage.CONSTRAINT_EXTRACTED
    assert derive_maturity_stage({"constraint_id": "c1", "detector_id": "d1"}) == MaturityStage.DETECTABLE
    assert derive_maturity_stage({"detector_id": "d1", "enforced_by": "gate-x"}) == MaturityStage.ENFORCED
    assert derive_maturity_stage({"enforced_by": "gate-x", "verified_window": "7d"}) == MaturityStage.VERIFIED


def test_unannotated_failure_is_observed(tmp_path):
    g = _g(tmp_path)
    f = g.add_node(GenomeNodeType.FAILURE, "boom")
    node = {n["id"]: n for n in g.to_dict()["nodes"]}[f]
    assert node["maturity"]["stage"] == "observed"


def test_annotation_surfaces_on_failure_node(tmp_path):
    g = _g(tmp_path)
    f = g.add_node(GenomeNodeType.FAILURE, "boom")
    chk = g.add_node(GenomeNodeType.CHECKPOINT, "ok")
    g.annotate_failure_maturity(f, classified=True, constraint_id="SG-x", detector_id="lint-y",
                                enforced_by="gate-z", verified_window="14d")
    nodes = {n["id"]: n for n in g.to_dict()["nodes"]}
    assert nodes[f]["maturity"]["stage"] == "verified"
    assert nodes[f]["maturity"]["constraint_id"] == "SG-x"
    # non-failure nodes carry no maturity field
    assert "maturity" not in nodes[chk]


def test_annotate_non_failure_rejected(tmp_path):
    g = _g(tmp_path)
    chk = g.add_node(GenomeNodeType.CHECKPOINT, "ok")
    with pytest.raises(ValueError):
        g.annotate_failure_maturity(chk, classified=True)
