"""Phase 152 (GH #213): Shadow Genome trust-transition emitter.

Records CBT/KBT/IBT trust-level transitions as append-only `trust` nodes linked
to their triggering evidence + governance node, surfaced in to_dict for the
downstream (FailSafe) dashboard.
"""
from __future__ import annotations

import pytest

from qor.scripts.shadow_genome_graph import (
    GenomeNodeType,
    ShadowGenomeGraph,
    TrustLevel,
)


def _g(tmp_path):
    return ShadowGenomeGraph(tmp_path / "genome.jsonl")


def test_record_promotion_sets_direction(tmp_path):
    g = _g(tmp_path)
    up = g.record_trust_transition(TrustLevel.CBT, TrustLevel.KBT)
    down = g.record_trust_transition(TrustLevel.IBT, TrustLevel.KBT)
    by_id = {t["id"]: t for t in g.to_dict()["trust_transitions"]}
    assert by_id[up]["direction"] == "promotion"
    assert by_id[down]["direction"] == "demotion"


def test_transition_links_evidence_and_governance(tmp_path):
    g = _g(tmp_path)
    ev = g.add_node(GenomeNodeType.FAILURE, "audit-veto")
    gov = g.add_node(GenomeNodeType.GOVERNANCE, "rule-x")
    tid = g.record_trust_transition(
        TrustLevel.KBT, TrustLevel.IBT, triggering_evidence=[ev], governance_node_id=gov
    )
    # causal edges exist: evidence triggered the transition; it applies to governance
    edges = g.to_dict()["edges"]
    assert any(e["source"] == ev and e["target"] == tid and e["type"] == "triggered_by" for e in edges)
    assert any(e["source"] == tid and e["target"] == gov and e["type"] == "applies_to" for e in edges)


def test_to_dict_surfaces_trust_transitions(tmp_path):
    g = _g(tmp_path)
    ev = g.add_node(GenomeNodeType.FAILURE, "f")
    gov = g.add_node(GenomeNodeType.GOVERNANCE, "g")
    tid = g.record_trust_transition(
        TrustLevel.CBT, TrustLevel.IBT, triggering_evidence=[ev], governance_node_id=gov, at="2026-06-10T00:00:00Z"
    )
    t = {x["id"]: x for x in g.to_dict()["trust_transitions"]}[tid]
    assert t["from_level"] == "CBT" and t["to_level"] == "IBT" and t["direction"] == "promotion"
    assert t["triggering_evidence"] == [ev]
    assert t["governance_node_id"] == gov
    assert t["at"] == "2026-06-10T00:00:00Z"


def test_invalid_trust_level_rejected(tmp_path):
    g = _g(tmp_path)
    with pytest.raises(ValueError):
        g.record_trust_transition("ZZZ", TrustLevel.KBT)
