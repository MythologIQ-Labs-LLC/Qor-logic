"""Phase 152 (GH #213): Shadow Genome federation-peer status emitter.

An adapter-level peer model fed by the consumer: append-only status events,
latest-wins per peer, surfaced as federation_peers in to_dict.
"""
from __future__ import annotations

import pytest

from qor.scripts.shadow_genome_graph import PeerState, ShadowGenomeGraph


def _g(tmp_path):
    return ShadowGenomeGraph(tmp_path / "genome.jsonl")


def test_set_peer_surfaces_in_to_dict(tmp_path):
    g = _g(tmp_path)
    g.set_federation_peer("p1", name="alpha", state=PeerState.SYNCED,
                          last_sync="2026-06-10T00:00:00Z", origin="gossip")
    peers = {p["id"]: p for p in g.to_dict()["federation_peers"]}
    assert peers["p1"] == {
        "id": "p1", "name": "alpha", "state": "synced",
        "last_sync": "2026-06-10T00:00:00Z", "origin": "gossip",
    }


def test_latest_state_wins(tmp_path):
    g = _g(tmp_path)
    g.set_federation_peer("p1", name="alpha", state=PeerState.SYNCING)
    g.set_federation_peer("p1", name="alpha", state=PeerState.STALE)
    peers = {p["id"]: p for p in g.to_dict()["federation_peers"]}
    assert peers["p1"]["state"] == "stale"


def test_peer_persists_across_reload(tmp_path):
    g = _g(tmp_path)
    g.set_federation_peer("p1", name="alpha", state=PeerState.DEGRADED)
    g2 = _g(tmp_path)  # reopen from the same JSONL
    peers = {p["id"]: p for p in g2.to_dict()["federation_peers"]}
    assert peers["p1"]["state"] == "degraded"


def test_invalid_peer_state_rejected(tmp_path):
    g = _g(tmp_path)
    with pytest.raises(ValueError):
        g.set_federation_peer("p1", name="alpha", state="bogus")
