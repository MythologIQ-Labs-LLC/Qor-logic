from __future__ import annotations

import json

import pytest

from qor.scripts import roadmap_state, roadmap_store


def test_store_rejects_path_escape(tmp_path) -> None:
    with pytest.raises(roadmap_state.InvalidHistoryError, match="invalid roadmap id"):
        roadmap_store.events_path(tmp_path, "../outside")


def test_store_reconstructs_and_rejects_malformed_jsonl(tmp_path) -> None:
    roadmap_store.create_roadmap(tmp_path, "demo", title="Objective")
    roadmap_store.append_payload(
        tmp_path,
        "demo",
        event_type="node_added",
        payload={"node": {
            "id": "fact", "kind": "fact", "title": "Fact",
            "resolver": "/qor-research", "authority_required": None,
        }},
    )
    state = roadmap_store.load_state(tmp_path, "demo")
    assert state.roadmap_id == "demo"
    assert "fact" in state.nodes

    path = roadmap_store.events_path(tmp_path, "demo")
    path.write_text(path.read_text(encoding="utf-8") + "{broken\n", encoding="utf-8")
    with pytest.raises(roadmap_state.InvalidHistoryError, match="malformed roadmap JSONL"):
        roadmap_store.load_events(tmp_path, "demo")


def test_atomic_failure_preserves_prior_history(tmp_path, monkeypatch) -> None:
    roadmap_store.create_roadmap(tmp_path, "demo", title="Objective")
    path = roadmap_store.events_path(tmp_path, "demo")
    before = path.read_text(encoding="utf-8")

    def fail_replace(_src, _dst):
        raise OSError("simulated interruption")

    monkeypatch.setattr(roadmap_store.os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated interruption"):
        roadmap_store.append_payload(
            tmp_path,
            "demo",
            event_type="node_added",
            payload={"node": {
                "id": "fact", "kind": "fact", "title": "Fact",
                "resolver": "/qor-research", "authority_required": None,
            }},
        )
    assert path.read_text(encoding="utf-8") == before


def test_event_lines_are_canonical_json_objects(tmp_path) -> None:
    roadmap_store.create_roadmap(tmp_path, "demo", title="Objective")
    lines = roadmap_store.events_path(tmp_path, "demo").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["type"] == "roadmap_created"
